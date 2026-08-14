"""自动扫描交易：基于最新行情运行策略并自动下单。"""

import json
from datetime import date, timedelta

from . import config, matching
from .account import AccountService, check_risk
from .models import Position, ScanReport, Strategy
from .public_data import DataUnavailableError
from .strategy_engine import evaluate_buy, evaluate_sell

LOOKBACK_DAYS = 120


def _position_dict(p: Position) -> dict:
    return {
        "code": p.code,
        "name": p.name,
        "qty": p.qty,
        "avg_cost": p.avg_cost,
        "hold_days": p.hold_days or 0,
        "high_since_buy": p.high_since_buy or p.avg_cost,
    }


def scan_and_trade(db, market, accounts: AccountService = None) -> dict:
    """执行一次全市场扫描并自动交易，返回扫描报告。"""
    accounts = accounts or AccountService()
    strategies = db.query(Strategy).filter(Strategy.enabled == 1).all()
    if not strategies:
        return {"error": "无启用的策略", "buys": [], "sells": [], "rejected": []}

    acct = accounts.ensure_account(db, config.DEFAULT_INITIAL_CAPITAL)
    accounts.roll_daily(db)

    end = date.today().isoformat()
    start = (date.today() - timedelta(days=LOOKBACK_DAYS)).isoformat()

    # 并发预取全市场日线，填充缓存，随后各策略循环命中缓存
    stock_list = market.get_stock_list()
    prefetch = getattr(market, "prefetch_daily_bars", None)
    if prefetch:
        prefetch([c for c, _ in stock_list], start, end)

    report = {"buys": [], "sells": [], "rejected": [], "strategy_count": len(strategies)}

    for strategy in strategies:
        cfg = json.loads(strategy.config_json)
        positions = db.query(Position).filter(Position.account_id == acct.id).all()
        held = {p.code: p for p in positions}

        # 组合状态（用于风控与持仓市值）
        state = {
            "initial_capital": acct.initial_capital,
            "cash": acct.available_cash,
            "positions": {p.code: _position_dict(p) for p in positions},
            "high_water": acct.initial_capital,
        }
        equity = acct.available_cash + sum(p.qty * p.avg_cost for p in positions)
        state["high_water"] = max(acct.initial_capital, equity)

        for code, name in market.get_stock_list():
            try:
                bars = market.get_daily_bars(code, start, end)
            except DataUnavailableError:
                continue
            if bars is None or len(bars) < 3:
                continue
            price = float(bars["close"].iloc[-1])

            if code in held:
                p = held[code]
                reason = evaluate_sell(cfg, _position_dict(p), bars)
                if reason:
                    order = accounts.place_order(db, acct, code, name, "sell", price, p.qty, reason)
                    if order.status == "filled":
                        report["sells"].append({
                            "code": code, "name": name, "price": round(price, 3),
                            "qty": p.qty, "reason": reason,
                        })
            else:
                if not evaluate_buy(cfg, bars):
                    continue
                max_pos_pct = float(cfg.get("risk", {}).get("maxPositionPercent", 20))
                total = equity
                qty = matching.round_lot(int(total * max_pos_pct / 100.0 / price))
                if qty < 100:
                    continue
                ok, why = check_risk(state, cfg, price, qty, {p.code: p.avg_cost for p in positions})
                if not ok:
                    report["rejected"].append({"code": code, "name": name, "reason": why})
                    continue
                order = accounts.place_order(db, acct, code, name, "buy", price, qty, "buy_signal")
                if order.status == "filled":
                    report["buys"].append({
                        "code": code, "name": name, "price": round(price, 3),
                        "qty": qty, "reason": "buy_signal",
                    })
                    positions = db.query(Position).filter(Position.account_id == acct.id).all()
                    held = {p.code: p for p in positions}
                    state["positions"] = {p.code: _position_dict(p) for p in positions}
                    state["cash"] = acct.available_cash
                    equity = acct.available_cash + sum(p.qty * p.avg_cost for p in positions)
                    state["high_water"] = max(state["high_water"], equity)

    db.add(ScanReport(
        strategy_count=len(strategies),
        buy_count=len(report["buys"]),
        sell_count=len(report["sells"]),
        reject_count=len(report["rejected"]),
        report_json=json.dumps(report, ensure_ascii=False),
    ))
    db.commit()

    return report
