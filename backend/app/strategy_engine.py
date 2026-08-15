"""策略引擎：根据策略配置与行情判断买卖信号。"""

from typing import Optional

import pandas as pd

from . import indicators as ind
from . import patterns


def _enabled(cfg: dict, key: str) -> bool:
    return bool(cfg.get(key, {}).get("enabled", False))


def _col(bars: pd.DataFrame, name: str):
    """若 bars 已预计算该指标列则返回，否则返回 None。"""
    return bars[name] if name in bars.columns else None


def attach_indicators(config: dict, bars: pd.DataFrame) -> pd.DataFrame:
    """为启用的信号一次性预计算指标列，返回追加新列的 DataFrame 副本。

    回测中先把指标算在完整历史上，随后仅对尾部窗口切片读取，
    避免每个交易日重复做 rolling/ewm 重算。
    """
    bars = bars.copy()
    buy = config.get("buy", {})
    sell = config.get("sell", {})
    close = bars["close"]
    high = bars["high"]
    low = bars["low"]
    volume = bars["volume"]

    if _enabled(buy, "maCross"):
        p = buy["maCross"]
        bars["_b_ma_s"] = ind.ma(close, int(p.get("shortPeriod", 5)))
        bars["_b_ma_l"] = ind.ma(close, int(p.get("longPeriod", 20)))
    if _enabled(buy, "macdCross"):
        dif, dea = ind.macd(close)
        bars["_b_dif"], bars["_b_dea"] = dif, dea
    if _enabled(buy, "volumeBreak"):
        bars["_b_vma"] = ind.volume_ma(volume, int(buy["volumeBreak"].get("avgDays", 5)))
    if _enabled(buy, "rsiOversold"):
        bars["_b_rsi"] = ind.rsi(close, int(buy["rsiOversold"].get("period", 14)))
    if _enabled(buy, "kdjGoldenCross"):
        k, d, _ = ind.kdj(high, low, close, int(buy["kdjGoldenCross"].get("n", 9)))
        bars["_b_k"], bars["_b_d"] = k, d
    if _enabled(buy, "bollLowerRebound"):
        p = buy["bollLowerRebound"]
        mid, upper, lower = ind.bollinger(close, int(p.get("period", 20)), float(p.get("numStd", 2)))
        bars["_b_boll_mid"], bars["_b_boll_upper"], bars["_b_boll_lower"] = mid, upper, lower

    if _enabled(sell, "maDeathCross"):
        p = sell["maDeathCross"]
        bars["_s_ma_s"] = ind.ma(close, int(p.get("shortPeriod", 5)))
        bars["_s_ma_l"] = ind.ma(close, int(p.get("longPeriod", 20)))
    if _enabled(sell, "macdDeathCross"):
        dif, dea = ind.macd(close)
        bars["_s_dif"], bars["_s_dea"] = dif, dea
    if _enabled(sell, "belowMA"):
        bars["_s_below_ma"] = ind.ma(close, int(sell["belowMA"].get("period", 20)))
    if _enabled(sell, "rsiOverbought"):
        bars["_s_rsi"] = ind.rsi(close, int(sell["rsiOverbought"].get("period", 14)))
    if _enabled(sell, "kdjDeathCross"):
        k, d, _ = ind.kdj(high, low, close, int(sell["kdjDeathCross"].get("n", 9)))
        bars["_s_k"], bars["_s_d"] = k, d
    if _enabled(sell, "bollBelowMid"):
        p = sell["bollBelowMid"]
        mid, _, _ = ind.bollinger(close, int(p.get("period", 20)), float(p.get("numStd", 2)))
        bars["_s_boll_mid"] = mid

    return bars


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
            ms, ml = _col(bars, "_b_ma_s"), _col(bars, "_b_ma_l")
            if ms is None:
                ms = ind.ma(close, s)
            if ml is None:
                ml = ind.ma(close, l)
            if not (ms.iloc[-2] < ml.iloc[-2] and ms.iloc[-1] >= ml.iloc[-1]):
                return False
        elif key == "macdCross":
            dif, dea = _col(bars, "_b_dif"), _col(bars, "_b_dea")
            if dif is None:
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
            vma = _col(bars, "_b_vma")
            if vma is None:
                vma = ind.volume_ma(volume, n)
            if not volume.iloc[-1] > vma.iloc[-1] * mult:
                return False
        elif key == "rsiOversold":
            period = int(buy["rsiOversold"].get("period", 14))
            threshold = float(buy["rsiOversold"].get("threshold", 30))
            rsi = _col(bars, "_b_rsi")
            if rsi is None:
                rsi = ind.rsi(close, period)
            if len(bars) < period + 1:
                return False
            if not (rsi.iloc[-2] < threshold <= rsi.iloc[-1]):
                return False
        elif key == "kdjGoldenCross":
            n = int(buy["kdjGoldenCross"].get("n", 9))
            low_zone = float(buy["kdjGoldenCross"].get("lowZone", 50))
            k, d = _col(bars, "_b_k"), _col(bars, "_b_d")
            if k is None:
                k, d, _ = ind.kdj(high, low, close, n)
            if len(bars) < n + 1:
                return False
            if not (k.iloc[-2] < d.iloc[-2] and k.iloc[-1] >= d.iloc[-1] and d.iloc[-1] < low_zone):
                return False
        elif key == "bollLowerRebound":
            period = int(buy["bollLowerRebound"].get("period", 20))
            num_std = float(buy["bollLowerRebound"].get("numStd", 2))
            lower = _col(bars, "_b_boll_lower")
            if lower is None:
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
                ms, ml = _col(bars, "_s_ma_s"), _col(bars, "_s_ma_l")
                if ms is None:
                    ms = ind.ma(close, s)
                if ml is None:
                    ml = ind.ma(close, l)
                if ms.iloc[-2] > ml.iloc[-2] and ms.iloc[-1] <= ml.iloc[-1]:
                    return "maDeathCross"
        elif key == "macdDeathCross":
            dif, dea = _col(bars, "_s_dif"), _col(bars, "_s_dea")
            if dif is None:
                dif, dea = ind.macd(close)
            if dif.iloc[-2] > dea.iloc[-2] and dif.iloc[-1] <= dea.iloc[-1]:
                return "macdDeathCross"
        elif key == "belowMA":
            period = int(sell["belowMA"].get("period", 20))
            if len(bars) >= period:
                ma = _col(bars, "_s_below_ma")
                if ma is None:
                    ma = ind.ma(close, period)
                if price < ma.iloc[-1]:
                    return "belowMA"
        elif key == "maxHoldDays":
            days = int(sell["maxHoldDays"].get("days", 20))
            if hold_days >= days:
                return "maxHoldDays"
        elif key == "rsiOverbought":
            period = int(sell["rsiOverbought"].get("period", 14))
            threshold = float(sell["rsiOverbought"].get("threshold", 70))
            rsi = _col(bars, "_s_rsi")
            if rsi is None:
                rsi = ind.rsi(close, period)
            if len(bars) < period + 1:
                continue
            if rsi.iloc[-2] > threshold >= rsi.iloc[-1]:
                return "rsiOverbought"
        elif key == "kdjDeathCross":
            n = int(sell["kdjDeathCross"].get("n", 9))
            high_zone = float(sell["kdjDeathCross"].get("highZone", 50))
            k, d = _col(bars, "_s_k"), _col(bars, "_s_d")
            if k is None:
                k, d, _ = ind.kdj(high, low, close, n)
            if len(bars) < n + 1:
                continue
            if k.iloc[-2] > d.iloc[-2] and k.iloc[-1] <= d.iloc[-1] and d.iloc[-1] > high_zone:
                return "kdjDeathCross"
        elif key == "bollBelowMid":
            period = int(sell["bollBelowMid"].get("period", 20))
            num_std = float(sell["bollBelowMid"].get("numStd", 2))
            mid = _col(bars, "_s_boll_mid")
            if mid is None:
                mid, _, _ = ind.bollinger(close, period, num_std)
            if len(bars) < period + 1:
                continue
            if close.iloc[-2] >= mid.iloc[-2] and close.iloc[-1] < mid.iloc[-1]:
                return "bollBelowMid"
        elif key in patterns.SELL_PATTERNS:
            if patterns.detect(bars, key):
                return key
    return None


_VECTORIZABLE_BUY = ("maCross", "macdCross", "breakHigh", "volumeBreak",
                     "rsiOversold", "kdjGoldenCross", "bollLowerRebound")


def buy_signal_mask(config: dict, bars: pd.DataFrame):
    """向量化计算每交易日买入信号布尔序列，供回测 O(1) 查询。

    仅支持可向量化的技术指标信号；若启用形态信号（patterns）或无信号则
    返回 None，调用方需回退到逐 bar evaluate_buy。返回长度等于 len(bars)
    的 numpy bool 数组，第 i 个元素表示第 i 根 bar 收盘时是否触发买入。
    """
    buy = config.get("buy", {})
    active = [k for k in _VECTORIZABLE_BUY if _enabled(buy, k)]
    if not active:
        return None
    if any(_enabled(buy, k) for k in patterns.BUY_PATTERNS):
        return None
    if len(bars) < 3:
        return None

    close = bars["close"]
    high = bars["high"]
    low = bars["low"]
    volume = bars["volume"]
    masks = []
    min_len = 2  # 外层 len(bars) < 3 即 idx < 2 返回 False

    for key in active:
        if key == "maCross":
            p = buy["maCross"]
            s, l = int(p.get("shortPeriod", 5)), int(p.get("longPeriod", 20))
            ms, ml = ind.ma(close, s), ind.ma(close, l)
            masks.append((ms.shift(1) < ml.shift(1)) & (ms >= ml))
            min_len = max(min_len, l)
        elif key == "macdCross":
            dif, dea = ind.macd(close)
            masks.append((dif.shift(1) < dea.shift(1)) & (dif >= dea))
        elif key == "breakHigh":
            n = int(buy["breakHigh"].get("days", 20))
            prev_high = high.rolling(n).max().shift(1)
            masks.append(close > prev_high)
            min_len = max(min_len, n)
        elif key == "volumeBreak":
            mult = float(buy["volumeBreak"].get("multiple", 1.5))
            n = int(buy["volumeBreak"].get("avgDays", 5))
            masks.append(volume > ind.volume_ma(volume, n) * mult)
            min_len = max(min_len, n)
        elif key == "rsiOversold":
            period = int(buy["rsiOversold"].get("period", 14))
            threshold = float(buy["rsiOversold"].get("threshold", 30))
            rsi = ind.rsi(close, period)
            masks.append((rsi.shift(1) < threshold) & (rsi >= threshold))
            min_len = max(min_len, period)
        elif key == "kdjGoldenCross":
            n = int(buy["kdjGoldenCross"].get("n", 9))
            low_zone = float(buy["kdjGoldenCross"].get("lowZone", 50))
            k, d, _ = ind.kdj(high, low, close, n)
            masks.append((k.shift(1) < d.shift(1)) & (k >= d) & (d < low_zone))
            min_len = max(min_len, n)
        elif key == "bollLowerRebound":
            period = int(buy["bollLowerRebound"].get("period", 20))
            num_std = float(buy["bollLowerRebound"].get("numStd", 2))
            _, _, lower = ind.bollinger(close, period, num_std)
            masks.append((close.shift(1) <= lower.shift(1)) & (close > lower))
            min_len = max(min_len, period)

    result = masks[0]
    for m in masks[1:]:
        result = result & m
    arr = result.fillna(False).values
    if min_len > 0:
        arr[:min_len] = False
    return arr
