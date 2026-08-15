"""技术指标计算（纯 pandas 实现）。"""

import pandas as pd


def ma(series: pd.Series, period: int) -> pd.Series:
    """移动平均线。"""
    return series.rolling(window=period).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """返回 (dif, dea) 两个 Series。"""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    return dif, dea


def highest(series: pd.Series, period: int) -> pd.Series:
    """近 period 日最高价（含当日）。"""
    return series.rolling(window=period).max()


def volume_ma(volume: pd.Series, period: int) -> pd.Series:
    """成交量均线。"""
    return volume.rolling(window=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """相对强弱指标（Wilder 平滑），返回 0~100 的 Series。"""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, float("nan"))
    out = 100.0 - 100.0 / (1.0 + rs)
    return out.fillna(100.0)


def bollinger(close: pd.Series, period: int = 20, num_std: float = 2.0):
    """布林带，返回 (mid, upper, lower) 三个 Series。"""
    mid = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return mid, upper, lower


def kdj(high: pd.Series, low: pd.Series, close: pd.Series,
        n: int = 9, k_period: int = 3, d_period: int = 3):
    """KDJ 指标，返回 (k, d, j) 三个 Series。"""
    lowest_low = low.rolling(window=n).min()
    highest_high = high.rolling(window=n).max()
    denom = (highest_high - lowest_low).replace(0.0, float("nan"))
    rsv = ((close - lowest_low) / denom * 100.0).fillna(50.0)
    k = rsv.ewm(alpha=1.0 / k_period, adjust=False).mean()
    d = k.ewm(alpha=1.0 / d_period, adjust=False).mean()
    j = 3.0 * k - 2.0 * d
    return k, d, j
