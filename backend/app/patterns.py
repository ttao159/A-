"""K 线技术形态识别（基于经典技术分析规则）。

每个检测函数接收包含 open/high/low/close 的 DataFrame，
判断最后一根 bar 是否构成对应形态，返回 bool。
"""

import pandas as pd


def _body(row) -> float:
    return abs(row["close"] - row["open"])


def _upper_shadow(row) -> float:
    return row["high"] - max(row["open"], row["close"])


def _lower_shadow(row) -> float:
    return min(row["open"], row["close"]) - row["low"]


# ===== 看涨（买入）形态 =====

def is_hammer(bars: pd.DataFrame) -> bool:
    """锤子线：下跌末端，实体小、下影线约为实体 2 倍以上、上影线极短。"""
    if len(bars) < 7:
        return False
    if bars["close"].iloc[-6] <= bars["close"].iloc[-1]:
        return False
    last = bars.iloc[-1]
    body = _body(last)
    if body <= 0:
        return False
    return _lower_shadow(last) >= 2 * body and _upper_shadow(last) <= 0.3 * body


def is_bullish_engulfing(bars: pd.DataFrame) -> bool:
    """看涨吞没：前阴后阳，阳线实体完全吞没前一根阴线实体。"""
    if len(bars) < 2:
        return False
    prev, last = bars.iloc[-2], bars.iloc[-1]
    if not (prev["close"] < prev["open"]):
        return False
    if not (last["close"] > last["open"]):
        return False
    return last["open"] <= prev["close"] and last["close"] >= prev["open"]


def is_morning_star(bars: pd.DataFrame) -> bool:
    """早晨之星：大阴线 + 小实体星线 + 大阳线，收盘回补第一根实体。"""
    if len(bars) < 3:
        return False
    a, b, c = bars.iloc[-3], bars.iloc[-2], bars.iloc[-1]
    if not (a["close"] < a["open"]):
        return False
    body_a = _body(a)
    if body_a <= 0:
        return False
    if _body(b) > body_a * 0.5:
        return False
    if not (c["close"] > c["open"]):
        return False
    return c["close"] > (a["open"] + a["close"]) / 2


def is_three_white_soldiers(bars: pd.DataFrame) -> bool:
    """红三兵：连续三根阳线，收盘价逐日抬高，开盘价位于前一根实体内。"""
    if len(bars) < 3:
        return False
    a, b, c = bars.iloc[-3], bars.iloc[-2], bars.iloc[-1]
    if not (a["close"] > a["open"] and b["close"] > b["open"] and c["close"] > c["open"]):
        return False
    if not (c["close"] > b["close"] > a["close"]):
        return False
    return a["open"] < b["open"] < a["close"]


def is_double_bottom(bars: pd.DataFrame, lookback: int = 60,
                     tolerance: float = 0.03, rebound: float = 0.05) -> bool:
    """双底：窗口内两个相近低点、中间反弹，当前收盘价突破颈线。"""
    if len(bars) < lookback:
        return False
    window = bars.iloc[-lookback:]
    lows = window["low"].reset_index(drop=True)
    closes = window["close"].reset_index(drop=True)
    i1 = int(lows.idxmin())
    v1 = lows.iloc[i1]
    if v1 <= 0:
        return False
    i2 = None
    for j in range(i1 + 5, len(lows)):
        if abs(lows.iloc[j] - v1) / v1 <= tolerance:
            i2 = j
            break
    if i2 is None:
        return False
    neck = closes.iloc[i1:i2].max()
    if neck <= 0 or (neck - v1) / v1 < rebound:
        return False
    return closes.iloc[-1] > neck


# ===== 看跌（卖出）形态 =====

def is_hanging_man(bars: pd.DataFrame) -> bool:
    """上吊线：上涨末端，实体小、下影线约为实体 2 倍以上、上影线极短。"""
    if len(bars) < 7:
        return False
    if bars["close"].iloc[-6] >= bars["close"].iloc[-1]:
        return False
    last = bars.iloc[-1]
    body = _body(last)
    if body <= 0:
        return False
    return _lower_shadow(last) >= 2 * body and _upper_shadow(last) <= 0.3 * body


def is_bearish_engulfing(bars: pd.DataFrame) -> bool:
    """看跌吞没：前阳后阴，阴线实体完全吞没前一根阳线实体。"""
    if len(bars) < 2:
        return False
    prev, last = bars.iloc[-2], bars.iloc[-1]
    if not (prev["close"] > prev["open"]):
        return False
    if not (last["close"] < last["open"]):
        return False
    return last["open"] >= prev["close"] and last["close"] <= prev["open"]


def is_evening_star(bars: pd.DataFrame) -> bool:
    """黄昏之星：大阳线 + 小实体星线 + 大阴线，收盘回补第一根实体。"""
    if len(bars) < 3:
        return False
    a, b, c = bars.iloc[-3], bars.iloc[-2], bars.iloc[-1]
    if not (a["close"] > a["open"]):
        return False
    body_a = _body(a)
    if body_a <= 0:
        return False
    if _body(b) > body_a * 0.5:
        return False
    if not (c["close"] < c["open"]):
        return False
    return c["close"] < (a["open"] + a["close"]) / 2


def is_three_black_crows(bars: pd.DataFrame) -> bool:
    """三只乌鸦：连续三根阴线，收盘价逐日走低。"""
    if len(bars) < 3:
        return False
    a, b, c = bars.iloc[-3], bars.iloc[-2], bars.iloc[-1]
    if not (a["close"] < a["open"] and b["close"] < b["open"] and c["close"] < c["open"]):
        return False
    return c["close"] < b["close"] < a["close"]


def is_double_top(bars: pd.DataFrame, lookback: int = 60,
                  tolerance: float = 0.03, rebound: float = 0.05) -> bool:
    """双顶：窗口内两个相近高点、中间回落，当前收盘价跌破颈线。"""
    if len(bars) < lookback:
        return False
    window = bars.iloc[-lookback:]
    highs = window["high"].reset_index(drop=True)
    closes = window["close"].reset_index(drop=True)
    i1 = int(highs.idxmax())
    v1 = highs.iloc[i1]
    if v1 <= 0:
        return False
    i2 = None
    for j in range(i1 + 5, len(highs)):
        if abs(highs.iloc[j] - v1) / v1 <= tolerance:
            i2 = j
            break
    if i2 is None:
        return False
    neck = closes.iloc[i1:i2].min()
    if neck <= 0 or (v1 - neck) / v1 < rebound:
        return False
    return closes.iloc[-1] < neck


_DETECTORS = {
    "hammer": is_hammer,
    "bullishEngulfing": is_bullish_engulfing,
    "morningStar": is_morning_star,
    "threeWhiteSoldiers": is_three_white_soldiers,
    "doubleBottom": is_double_bottom,
    "hangingMan": is_hanging_man,
    "bearishEngulfing": is_bearish_engulfing,
    "eveningStar": is_evening_star,
    "threeBlackCrows": is_three_black_crows,
    "doubleTop": is_double_top,
}

BUY_PATTERNS = ["hammer", "bullishEngulfing", "morningStar", "threeWhiteSoldiers", "doubleBottom"]
SELL_PATTERNS = ["hangingMan", "bearishEngulfing", "eveningStar", "threeBlackCrows", "doubleTop"]


def detect(bars: pd.DataFrame, name: str) -> bool:
    """按形态名检测最后一根 bar 是否构成该形态。"""
    fn = _DETECTORS.get(name)
    if fn is None:
        return False
    return bool(fn(bars))
