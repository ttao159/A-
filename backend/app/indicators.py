"""技术指标计算：基于日线 DataFrame（date/open/high/low/close/volume）。

纯 Python 实现，供个股 AI 诊断与条件选股复用。
"""

import math

import pandas as pd


def _sma(values: list, period: int) -> list:
    """简单移动平均，长度不足返回空列表（从 period-1 开始）。"""
    out = []
    s = 0.0
    for i, v in enumerate(values):
        s += v
        if i >= period:
            s -= values[i - period]
        if i >= period - 1:
            out.append(s / period)
    return out


def _ema(values: list, period: int) -> list:
    out = []
    k = 2.0 / (period + 1)
    prev = None
    for v in values:
        if prev is None:
            prev = v
        else:
            prev = v * k + prev * (1 - k)
        out.append(prev)
    return out


def _rsi(values: list, period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    gains, losses = 0.0, 0.0
    for i in range(1, period + 1):
        diff = values[i] - values[i - 1]
        if diff >= 0:
            gains += diff
        else:
            losses -= diff
    if losses == 0:
        return 100.0
    avg_g, avg_l = gains / period, losses / period
    for i in range(period + 1, len(values)):
        diff = values[i] - values[i - 1]
        g, l = (diff, 0.0) if diff >= 0 else (0.0, -diff)
        avg_g = (avg_g * (period - 1) + g) / period
        avg_l = (avg_l * (period - 1) + l) / period
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return 100.0 - 100.0 / (1.0 + rs)


def compute_indicators(df) -> dict:
    """计算一组常用技术指标，返回供诊断使用的结构化快照。

    df: pandas DataFrame，列含 open/high/low/close/volume，按日期升序。
    """
    closes = [float(x) for x in df["close"].tolist()]
    if len(closes) < 30:
        return {}

    last = closes[-1]
    prev = closes[-2] if len(closes) > 1 else last
    change_pct = (last - prev) / prev * 100.0 if prev else 0.0

    def ma(period: int) -> float | None:
        if len(closes) < period:
            return None
        return round(sum(closes[-period:]) / period, 3)

    ma5, ma10, ma20, ma60 = ma(5), ma(10), ma(20), ma(60)

    # MACD(12,26,9)
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    dif = [a - b for a, b in zip(ema12, ema26)]
    dea = _ema(dif, 9)
    macd_bar = (dif[-1] - dea[-1]) * 2.0
    macd_golden = len(dif) >= 2 and dif[-1] > dea[-1] and dif[-2] <= dea[-2]
    macd_dead = len(dif) >= 2 and dif[-1] < dea[-1] and dif[-2] >= dea[-2]

    # KDJ(9,3,3)
    low9 = [float(x) for x in df["low"].tail(9).tolist()]
    high9 = [float(x) for x in df["high"].tail(9).tolist()]
    low_min, high_max = min(low9), max(high9)
    rsv = (last - low_min) / (high_max - low_min) * 100.0 if high_max > low_min else 50.0
    k = (2.0 / 3) * 50.0 + rsv / 3.0
    d = (2.0 / 3) * 50.0 + k / 3.0
    j = 3 * k - 2 * d

    # BOLL(20,2)
    if len(closes) >= 20:
        ma20v = sum(closes[-20:]) / 20.0
        variance = sum((x - ma20v) ** 2 for x in closes[-20:]) / 20.0
        std = math.sqrt(variance)
        boll_up = ma20v + 2 * std
        boll_low = ma20v - 2 * std
        boll_width = (boll_up - boll_low) / ma20v * 100.0 if ma20v else 0.0
        boll_pos = (last - boll_low) / (boll_up - boll_low) if boll_up > boll_low else 0.5
    else:
        boll_up = boll_low = ma20v = boll_width = boll_pos = None

    # 量能
    volumes = [float(x) for x in df["volume"].tolist()]
    vol_now = volumes[-1]
    vol_avg5 = sum(volumes[-6:-1]) / 5.0 if len(volumes) >= 6 else vol_now
    vol_ratio = vol_now / vol_avg5 if vol_avg5 else 1.0

    # 波动率（20 日年化/日化，取日化百分比）
    rets = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
    ret20 = rets[-20:]
    mean = sum(ret20) / len(ret20)
    var = sum((x - mean) ** 2 for x in ret20) / len(ret20)
    vol_pct = math.sqrt(var) * 100.0 if var > 0 else 0.0

    # 区间统计
    tail20 = closes[-20:]
    recent_high = max(float(x) for x in df["high"].tail(20).tolist())
    recent_low = min(float(x) for x in df["low"].tail(20).tolist())
    ret_20 = (last / closes[-21] - 1) * 100.0 if len(closes) > 21 else 0.0
    ret_60 = (last / closes[-61] - 1) * 100.0 if len(closes) > 61 else None

    trend = "多头" if (ma5 and ma10 and ma20 and ma5 > ma10 > ma20) else (
        "空头" if (ma5 and ma10 and ma20 and ma5 < ma10 < ma20) else "震荡")

    return {
        "price": round(last, 3),
        "change_pct": round(change_pct, 2),
        "ma5": ma5, "ma10": ma10, "ma20": ma20, "ma60": ma60,
        "macd_dif": round(dif[-1], 4), "macd_dea": round(dea[-1], 4),
        "macd_bar": round(macd_bar, 4),
        "macd_golden": macd_golden, "macd_dead": macd_dead,
        "kdj_k": round(k, 2), "kdj_d": round(d, 2), "kdj_j": round(j, 2),
        "rsi14": round(rsi, 2) if (rsi := _rsi(closes)) is not None else None,
        "boll_up": round(boll_up, 3) if boll_up is not None else None,
        "boll_low": round(boll_low, 3) if boll_low is not None else None,
        "boll_width": round(boll_width, 2) if boll_width is not None else None,
        "boll_pos": round(boll_pos, 3) if boll_pos is not None else None,
        "vol_ratio": round(vol_ratio, 2),
        "vol_pct": round(vol_pct, 2),
        "recent_high": round(recent_high, 3),
        "recent_low": round(recent_low, 3),
        "ret_20": round(ret_20, 2),
        "ret_60": round(ret_60, 2) if ret_60 is not None else None,
        "trend": trend,
    }


def ma(values, period: int) -> pd.Series:
    """简单移动平均，返回与输入等长的 Series，前 period-1 个为 NaN。"""
    return values.rolling(period).mean()


def highest(values, period: int) -> pd.Series:
    """滚动最高价，返回与输入等长的 Series，前 period-1 个为 NaN。"""
    return values.rolling(period).max()


def volume_ma(values, period: int) -> pd.Series:
    """成交量均线，返回与输入等长的 Series，前 period-1 个为 NaN。"""
    return values.rolling(period).mean()


def macd(close, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD，返回 (dif, dea) 两个与输入等长的 Series。"""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    return dif, dea


def rsi(close, period: int = 14) -> pd.Series:
    """RSI（Wilder 平滑），返回与输入等长的 Series。"""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1.0)
    out = 100.0 - 100.0 / (1.0 + rs)
    return out.where(avg_loss != 0, 100.0)


def bollinger(close, period: int = 20, num_std: float = 2.0):
    """布林带，返回 (mid, upper, lower) 三个与输入等长的 Series。"""
    mid = close.rolling(period).mean()
    std = close.rolling(period).std(ddof=0)
    upper = mid + num_std * std
    lower = mid - num_std * std
    return mid, upper, lower


def kdj(high, low, close, n: int = 9):
    """KDJ，返回 (k, d, j) 三个与输入等长的 Series。"""
    low_n = low.rolling(n).min()
    high_n = high.rolling(n).max()
    rsv = (close - low_n) / (high_n - low_n).replace(0, 1.0) * 100.0
    rsv = rsv.where(high_n != low_n, 50.0)
    k = rsv.ewm(alpha=1.0 / 3, adjust=False).mean()
    d = k.ewm(alpha=1.0 / 3, adjust=False).mean()
    j = 3.0 * k - 2.0 * d
    return k, d, j
