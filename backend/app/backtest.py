"""回测引擎：历史行情重放，产出权益曲线与统计指标。"""

import pandas as pd

from . import matching
from .account import Portfolio, check_risk
from .public_data import DataUnavailableError
from .strategy_engine import attach_indicators, buy_signal_mask, evaluate_buy, evaluate_sell

# 信号判断所需的尾部窗口大小（覆盖 doubleBottom/doubleTop 的 60 日 lookback 及各类指标周期）
_WINDOW = 128


def compute_metrics(equity_curve, pf: Portfolio) -> dict:
    if not equity_curve:
        return {}
    initial = pf.initial_capital
    final = equity_curve[-1]["equity"]
    total_return = (final - initial) / initial * 100.0
    n_days = max(len(equity_curve), 1)
    annual_return = ((final / initial) ** (252.0 / n_days) - 1) * 100.0 if final > 0 else -100.0

    peak = float("-inf")
    max_dd = 0.0
    for p in equity_curve:
        eq = p["equity"]
        peak = max(peak, eq)
        if peak > 0:
            max_dd = max(max_dd, (peak - eq) / peak * 100.0)

    sell_trades = [t for t in pf.trades if t["direction"] == "sell"]
    wins = [t for t in sell_trades if t["pnl"] > 0]
    losses = [t for t in sell_trades if t["pnl"] < 0]
    win_rate = len(wins) / len(sell_trades) * 100.0 if sell_trades else 0.0
    avg_win = sum(t["pnl"] for t in wins) / len(wins) if wins else 0.0
    avg_loss = abs(sum(t["pnl"] for t in losses) / len(losses)) if losses else 0.0
    profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0.0

    return {
        "initial_capital": initial,
        "final_equity": round(final, 2),
        "total_return_pct": round(total_return, 2),
        "annual_return_pct": round(annual_return, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "win_rate_pct": round(win_rate, 2),
        "profit_loss_ratio": round(profit_loss_ratio, 2),
        "trade_count": len(pf.trades),
        "closed_trades": len(sell_trades),
    }


def run_backtest(config: dict, market, start: str, end: str,
                 initial_capital: float = 1_000_000.0) -> dict:
    """执行回测，返回 metrics/equity_curve/trades。"""
    stock_list = market.get_stock_list()
    prefetch = getattr(market, "prefetch_daily_bars", None)
    if prefetch:
        prefetch([c for c, _ in stock_list], start, end)
    bars_map = {}
    buy_masks = {}
    for code, name in stock_list:
        try:
            df = market.get_daily_bars(code, start, end)
        except DataUnavailableError:
            continue
        if df is not None and len(df):
            df = attach_indicators(config, df.sort_values("date").reset_index(drop=True))
            bars_map[code] = df
            buy_masks[code] = buy_signal_mask(config, df)

    if not bars_map:
        return {"metrics": {}, "equity_curve": [], "trades": []}

    all_dates = sorted(set().union(*[set(df["date"]) for df in bars_map.values()]))
    if len(all_dates) < 3:
        return {"metrics": {}, "equity_curve": [], "trades": []}

    # 预构建 date -> 行索引，供 O(1) 定位，避免逐日布尔切片
    date_idx = {code: {str(d): i for i, d in enumerate(df["date"])}
                for code, df in bars_map.items()}

    pf = Portfolio(initial_capital)
    equity_curve = []
    pending_buy = []   # (code, name, qty)
    pending_sell = []  # (code, reason)
    signal_stats = {"buy": 0, "sell": {}}

    for date in all_dates:
        # 1. 撮合上一交易日产生的订单（当日开盘价）
        for code, name, qty in pending_buy:
            df = bars_map[code]
            idx = date_idx[code].get(date)
            if idx is None:
                continue
            bar = df.iloc[idx]
            prev_close = float(df.iloc[idx - 1]["close"]) if idx > 0 else None
            fill_price, _ = matching.match_fill("buy", prev_close, bar)
            if fill_price:
                pf.buy(code, name, fill_price, qty, date, "buy_signal")
        for code, reason in pending_sell:
            df = bars_map[code]
            idx = date_idx[code].get(date)
            if idx is None:
                continue
            bar = df.iloc[idx]
            prev_close = float(df.iloc[idx - 1]["close"]) if idx > 0 else None
            fill_price, _ = matching.match_fill("sell", prev_close, bar)
            if fill_price:
                pos = pf.positions.get(code)
                if pos:
                    pf.sell(code, fill_price, pos["qty"], date, reason)
        pending_buy = []
        pending_sell = []

        # 2. 当日收盘价
        prices = {}
        for code, df in bars_map.items():
            idx = date_idx[code].get(date)
            if idx is not None:
                prices[code] = float(df.iloc[idx]["close"])

        # 3. 生成信号（用截止当日数据），次日成交
        risk = config.get("risk", {})
        max_pos_pct = float(risk.get("maxPositionPercent", 20))
        for code, name in stock_list:
            df = bars_map.get(code)
            idx = date_idx[code].get(date)
            if df is None or idx is None:
                continue
            if code in pf.positions:
                start = idx + 1 - _WINDOW
                if start < 0:
                    start = 0
                upto = df.iloc[start: idx + 1]
                reason = evaluate_sell(config, pf.positions[code], upto)
                if reason:
                    signal_stats["sell"][reason] = signal_stats["sell"].get(reason, 0) + 1
                    pending_sell.append((code, reason))
            else:
                mask = buy_masks.get(code)
                if mask is not None:
                    is_buy = bool(mask[idx])
                    close_price = float(df["close"].iloc[idx])
                else:
                    start = idx + 1 - _WINDOW
                    if start < 0:
                        start = 0
                    upto = df.iloc[start: idx + 1]
                    if len(upto) < 3:
                        continue
                    is_buy = evaluate_buy(config, upto)
                    close_price = float(upto["close"].iloc[-1])
                if is_buy:
                    signal_stats["buy"] += 1
                    total = pf.equity(prices)
                    qty = matching.round_lot(int(total * max_pos_pct / 100.0 / close_price))
                    if qty >= 100:
                        ok, why = check_risk(pf.state(), config, close_price, qty, prices)
                        if ok:
                            pending_buy.append((code, name, qty))

        # 4. 更新持仓持有天数与期间最高价
        pf.update_daily(prices)
        equity_curve.append({"date": date, "equity": round(pf.equity(prices), 2)})

    metrics = compute_metrics(equity_curve, pf)
    return {
        "metrics": metrics,
        "equity_curve": equity_curve,
        "trades": pf.trades,
        "signal_stats": signal_stats,
    }
