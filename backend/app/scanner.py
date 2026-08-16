"""自动扫描交易：基于最新行情运行策略并自动下单。"""

import json
import threading
from datetime import date, timedelta

from . import config, matching
from .account import AccountService, check_risk
from .broker import PaperBroker
from .models import Alert, Position, ScanReport, Strategy
from .public_data import DataUnavailableError
from .strategy_engine import evaluate_buy, evaluate_sell

LOOKBACK_DAYS = 120

scan_lock = threading.Lock()

RISK_ALERTS = {
    "takeProfit": "止盈",
    "stopLoss": "止损",
    "trailingStop": "移动止盈回撤",
    "maxSingleLoss": "单只最大亏损",
}


def _position_dict(p: Position) -> dict:
    return {
        "code": p.code,
        "name": p.name,
        "qty": p.qty,
        "avg_cost": p.avg_cost,
        "hold_days": p.hold_days or 0,
        "high_since_buy": p.high_since_buy or p.avg_cost,
    }


def _latest_price(market, code: str, start: str, end: str) -> float:
    """获取某股票最新收盘价，失败返回 None。"""
    try:
        bars = market.get_daily_bars(code, start, end)
        if bars is not None and len(bars):
            return float(bars["close"].iloc[-1])
    except DataUnavailableError:
        pass
    return None


def scan_and_trade(db, market, accounts: AccountService = None, broker=None, source: str = "manual", progress=None) -> dict:
    """执行一次全市场扫描并自动交易，返回扫描报告。

    source: manual（手动触发）/ auto（定时任务）。
    broker: 券商适配器，缺省为模拟盘 PaperBroker。
    progress: 可选回调 progress(stage, message, done, total)，用于流式进度上报。
    """
    def emit(stage, message, done, total):
        if progress:
            progress(stage, message, done, total)

    accounts = accounts or AccountService()
    broker = broker or PaperBroker(accounts)
    strategies = db.query(Strategy).filter(Strategy.enabled == 1).all()
    if not strategies:
        return {"error": "无启用的策略", "buys": [], "sells": [], "rejected": []}

    acct = accounts.ensure_account(db, config.DEFAULT_INITIAL_CAPITAL)
    accounts.roll_daily(db)
    accounts.ensure_strategy_capital(db, acct, strategies)

    end = date.today().isoformat()
    start = (date.today() - timedelta(days=LOOKBACK_DAYS)).isoformat()

    # 并发预取全市场日线，填充缓存，随后各策略循环命中缓存
    stock_list = market.get_stock_list()
    total_stocks = len(stock_list) * len(strategies)
    emit("prefetch", f"预取 {len(stock_list)} 只股票日线数据...", 0, total_stocks)
    prefetch = getattr(market, "prefetch_daily_bars", None)
    if prefetch:
        prefetch([c for c, _ in stock_list], start, end)
    emit("prefetch", "日线数据就绪", 1, 1)

    report = {"buys": [], "sells": [], "rejected": [], "strategy_count": len(strategies)}

    processed = 0
    for strategy in strategies:
        cfg = json.loads(strategy.config_json)
        positions = db.query(Position).filter(
            Position.account_id == acct.id, Position.strategy_id == strategy.id).all()
        held = {p.code: p for p in positions}

        # 持仓最新价（用于风控权益计算，缺省回退成本价）
        prices = {p.code: p.avg_cost for p in positions}
        for p in positions:
            latest = _latest_price(market, p.code, start, end)
            if latest is not None:
                prices[p.code] = latest

        # 组合状态（按策略独立资金与持仓）
        state = {
            "initial_capital": strategy.initial_capital,
            "cash": strategy.available_cash,
            "positions": {p.code: _position_dict(p) for p in positions},
            "high_water": strategy.initial_capital,
        }
        equity = strategy.available_cash + sum(p.qty * prices.get(p.code, p.avg_cost)
                                               for p in positions)
        state["high_water"] = max(strategy.initial_capital, equity)

        for code, name in stock_list:
            processed += 1
            if processed % 50 == 0:
                emit("scan", f"{strategy.name} 扫描中 {processed}/{total_stocks}", processed, total_stocks)
            try:
                bars = market.get_daily_bars(code, start, end)
            except DataUnavailableError:
                continue
            if bars is None or len(bars) < 3:
                continue
            price = float(bars["close"].iloc[-1])
            prices[code] = price

            if code in held:
                p = held[code]
                reason = evaluate_sell(cfg, _position_dict(p), bars)
                if reason:
                    order = broker.place_order(db, code, name, "sell", price, p.qty, reason, strategy=strategy)
                    if order.status == "filled":
                        report["sells"].append({
                            "code": code, "name": name, "price": round(price, 3),
                            "qty": p.qty, "reason": reason,
                        })
                        if reason in RISK_ALERTS:
                            db.add(Alert(
                                account_id=acct.id, strategy_id=strategy.id, code=code, name=name,
                                alert_type=reason, price=round(price, 3),
                                message=f"{name}({code}) 触发{RISK_ALERTS[reason]}，现价 {round(price, 2)}",
                            ))
                        # 卖出后同步组合状态，避免后续风控用过期数据
                        positions = db.query(Position).filter(
                            Position.account_id == acct.id, Position.strategy_id == strategy.id).all()
                        held = {p.code: p for p in positions}
                        state["positions"] = {p.code: _position_dict(p) for p in positions}
                        state["cash"] = strategy.available_cash
            else:
                if not evaluate_buy(cfg, bars):
                    continue
                equity = state["cash"] + sum(
                    pp["qty"] * prices.get(pp["code"], pp["avg_cost"])
                    for pp in state["positions"].values()
                )
                max_pos_pct = float(cfg.get("risk", {}).get("maxPositionPercent", 20))
                qty = matching.round_lot(int(equity * max_pos_pct / 100.0 / price))
                if qty < 100:
                    continue
                ok, why = check_risk(state, cfg, price, qty, prices)
                if not ok:
                    report["rejected"].append({"code": code, "name": name, "reason": why})
                    continue
                order = broker.place_order(db, code, name, "buy", price, qty, "buy_signal", strategy=strategy)
                if order.status == "filled":
                    report["buys"].append({
                        "code": code, "name": name, "price": round(price, 3),
                        "qty": qty, "reason": "buy_signal",
                    })
                    positions = db.query(Position).filter(
                        Position.account_id == acct.id, Position.strategy_id == strategy.id).all()
                    held = {p.code: p for p in positions}
                    state["positions"] = {p.code: _position_dict(p) for p in positions}
                    state["cash"] = strategy.available_cash
                    equity = state["cash"] + sum(
                        pp["qty"] * prices.get(pp["code"], pp["avg_cost"])
                        for pp in state["positions"].values()
                    )
                    state["high_water"] = max(state["high_water"], equity)

    emit("scan", "扫描完成，正在写入报告...", total_stocks, total_stocks)
    db.add(ScanReport(
        strategy_count=len(strategies),
        buy_count=len(report["buys"]),
        sell_count=len(report["sells"]),
        reject_count=len(report["rejected"]),
        source=source,
        report_json=json.dumps(report, ensure_ascii=False),
    ))
    db.commit()

    _prune_scan_reports(db, keep=50)

    return report


def _prune_scan_reports(db, keep: int = 50) -> None:
    """清理扫描历史，仅保留最近 `keep` 条，避免数据无限累积。"""
    cutoff = db.query(ScanReport.id).order_by(ScanReport.id.desc()).offset(keep).first()
    if cutoff is not None:
        db.query(ScanReport).filter(ScanReport.id <= cutoff[0]).delete(synchronize_session=False)
        db.commit()
