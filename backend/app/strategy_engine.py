"""策略引擎：根据策略配置与行情判断买卖信号。"""

from typing import Optional

import pandas as pd

from . import indicators as ind
from . import patterns


def _enabled(cfg: dict, key: str) -> bool:
    return bool(cfg.get(key, {}).get("enabled", False))


def evaluate_buy(config: dict, bars: pd.DataFrame) -> bool:
    """判断最后一根 bar 是否满足全部启用的买入信号。"""
    buy = config.get("buy", {})
    active = [k for k in ("maCross", "macdCross", "breakHigh", "volumeBreak",
                          "rsiOversold", "kdjGoldenCross", "bollLowerRebound",
                          *patterns.BUY_PATTERNS) if _enabled(buy, k)]
    if not active:
        return False
    if len(bars) < 3:
        return False

    close = bars["close"]
    high = bars["high"]
    low = bars["low"]
    volume = bars["volume"]

    for key in active:
        if key == "maCross":
            p = buy["maCross"]
            s, l = int(p.get("shortPeriod", 5)), int(p.get("longPeriod", 20))
            if len(bars) < l + 1:
                return False
            ms, ml = ind.ma(close, s), ind.ma(close, l)
            if not (ms.iloc[-2] < ml.iloc[-2] and ms.iloc[-1] >= ml.iloc[-1]):
                return False
        elif key == "macdCross":
            dif, dea = ind.macd(close)
            if not (dif.iloc[-2] < dea.iloc[-2] and dif.iloc[-1] >= dea.iloc[-1]):
                return False
        elif key == "breakHigh":
            n = int(buy["breakHigh"].get("days", 20))
            if len(bars) < n + 1:
                return False
            prev_high = high.iloc[-n - 1:-1].max()
            if not close.iloc[-1] > prev_high:
                return False
        elif key == "volumeBreak":
            mult = float(buy["volumeBreak"].get("multiple", 1.5))
            n = int(buy["volumeBreak"].get("avgDays", 5))
            if len(bars) < n + 1:
                return False
            if not volume.iloc[-1] > ind.volume_ma(volume, n).iloc[-1] * mult:
                return False
        elif key == "rsiOversold":
            period = int(buy["rsiOversold"].get("period", 14))
            threshold = float(buy["rsiOversold"].get("threshold", 30))
            rsi = ind.rsi(close, period)
            if len(bars) < period + 1:
                return False
            if not (rsi.iloc[-2] < threshold <= rsi.iloc[-1]):
                return False
        elif key == "kdjGoldenCross":
            n = int(buy["kdjGoldenCross"].get("n", 9))
            low_zone = float(buy["kdjGoldenCross"].get("lowZone", 50))
            k, d, _ = ind.kdj(high, low, close, n)
            if len(bars) < n + 1:
                return False
            if not (k.iloc[-2] < d.iloc[-2] and k.iloc[-1] >= d.iloc[-1] and d.iloc[-1] < low_zone):
                return False
        elif key == "bollLowerRebound":
            period = int(buy["bollLowerRebound"].get("period", 20))
            num_std = float(buy["bollLowerRebound"].get("numStd", 2))
            _, _, lower = ind.bollinger(close, period, num_std)
            if len(bars) < period + 1:
                return False
            if not (close.iloc[-2] <= lower.iloc[-2] and close.iloc[-1] > lower.iloc[-1]):
                return False
        elif key in patterns.BUY_PATTERNS:
            if not patterns.detect(bars, key):
                return False
    return True


def evaluate_sell(config: dict, position: dict, bars: pd.DataFrame) -> Optional[str]:
    """判断是否触发任一启用的卖出信号，返回卖出原因；未触发返回 None。"""
    close = bars["close"]
    price = close.iloc[-1]
    avg_cost = position["avg_cost"]
    pnl_pct = (price - avg_cost) / avg_cost * 100.0 if avg_cost else 0.0
    hold_days = position.get("hold_days", 0)

    # T+1：买入当日不可卖
    if hold_days < 1:
        return None

    # 风控：单只最大亏损（独立于卖出信号，配置 > 0 即强制生效）
    max_single_loss = float(config.get("risk", {}).get("maxSingleLoss", 0) or 0)
    if max_single_loss > 0 and pnl_pct <= -max_single_loss:
        return "maxSingleLoss"

    sell = config.get("sell", {})
    active = [k for k in ("takeProfit", "stopLoss", "trailingStop", "maDeathCross",
                          "macdDeathCross", "belowMA", "maxHoldDays",
                          "rsiOverbought", "kdjDeathCross", "bollBelowMid",
                          *patterns.SELL_PATTERNS) if _enabled(sell, k)]
    if not active:
        return None

    high = bars["high"]
    low = bars["low"]
    high_since_buy = position.get("high_since_buy", price)

    for key in active:
        if key == "takeProfit":
            if pnl_pct >= float(sell["takeProfit"].get("percent", 10)):
                return "takeProfit"
        elif key == "stopLoss":
            if pnl_pct <= -float(sell["stopLoss"].get("percent", 5)):
                return "stopLoss"
        elif key == "trailingStop":
            dd = float(sell["trailingStop"].get("drawdown", 8))
            if high_since_buy > 0 and price <= high_since_buy * (1 - dd / 100.0):
                return "trailingStop"
        elif key == "maDeathCross":
            p = sell["maDeathCross"]
            s, l = int(p.get("shortPeriod", 5)), int(p.get("longPeriod", 20))
            if len(bars) >= l + 1:
                ms, ml = ind.ma(close, s), ind.ma(close, l)
                if ms.iloc[-2] > ml.iloc[-2] and ms.iloc[-1] <= ml.iloc[-1]:
                    return "maDeathCross"
        elif key == "macdDeathCross":
            dif, dea = ind.macd(close)
            if dif.iloc[-2] > dea.iloc[-2] and dif.iloc[-1] <= dea.iloc[-1]:
                return "macdDeathCross"
        elif key == "belowMA":
            period = int(sell["belowMA"].get("period", 20))
            if len(bars) >= period:
                if price < ind.ma(close, period).iloc[-1]:
                    return "belowMA"
        elif key == "maxHoldDays":
            days = int(sell["maxHoldDays"].get("days", 20))
            if hold_days >= days:
                return "maxHoldDays"
        elif key == "rsiOverbought":
            period = int(sell["rsiOverbought"].get("period", 14))
            threshold = float(sell["rsiOverbought"].get("threshold", 70))
            rsi = ind.rsi(close, period)
            if len(bars) < period + 1:
                continue
            if rsi.iloc[-2] > threshold >= rsi.iloc[-1]:
                return "rsiOverbought"
        elif key == "kdjDeathCross":
            n = int(sell["kdjDeathCross"].get("n", 9))
            high_zone = float(sell["kdjDeathCross"].get("highZone", 50))
            k, d, _ = ind.kdj(high, low, close, n)
            if len(bars) < n + 1:
                continue
            if k.iloc[-2] > d.iloc[-2] and k.iloc[-1] <= d.iloc[-1] and d.iloc[-1] > high_zone:
                return "kdjDeathCross"
        elif key == "bollBelowMid":
            period = int(sell["bollBelowMid"].get("period", 20))
            num_std = float(sell["bollBelowMid"].get("numStd", 2))
            mid, _, _ = ind.bollinger(close, period, num_std)
            if len(bars) < period + 1:
                continue
            if close.iloc[-2] >= mid.iloc[-2] and close.iloc[-1] < mid.iloc[-1]:
                return "bollBelowMid"
        elif key in patterns.SELL_PATTERNS:
            if patterns.detect(bars, key):
                return key
    return None
