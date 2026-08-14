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
                          *patterns.BUY_PATTERNS) if _enabled(buy, k)]
    if not active:
        return False
    if len(bars) < 3:
        return False

    close = bars["close"]
    high = bars["high"]
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
                          *patterns.SELL_PATTERNS) if _enabled(sell, k)]
    if not active:
        return None

    high = bars["high"]
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
        elif key in patterns.SELL_PATTERNS:
            if patterns.detect(bars, key):
                return key
    return None
