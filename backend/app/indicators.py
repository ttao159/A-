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
