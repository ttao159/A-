import pandas as pd
import pytest

from app import indicators as ind


def test_ma_basic():
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    result = ind.ma(s, 3)
    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert result.iloc[2] == pytest.approx(2.0)
    assert result.iloc[3] == pytest.approx(3.0)
    assert result.iloc[4] == pytest.approx(4.0)


def test_highest():
    s = pd.Series([1.0, 5.0, 3.0, 4.0, 2.0])
    result = ind.highest(s, 3)
    assert result.iloc[2] == pytest.approx(5.0)
    assert result.iloc[4] == pytest.approx(4.0)


def test_volume_ma():
    v = pd.Series([100.0, 200.0, 300.0, 400.0, 500.0])
    result = ind.volume_ma(v, 2)
    assert result.iloc[4] == pytest.approx(450.0)


def test_macd_shapes_and_cross():
    close = pd.Series([10, 10.5, 10.2, 10.8, 11, 11.5, 11.2, 12, 12.5, 13,
                       12.8, 12.5, 12.2, 12.0, 11.8, 12.2, 12.8, 13.2, 14.0, 14.5])
    dif, dea = ind.macd(close)
    assert len(dif) == len(close)
    assert len(dea) == len(close)
    # DIF 是快慢 EMA 之差，rising 段 DIF 应大于 0
    assert dif.iloc[-1] > 0


def test_rsi_range_and_direction():
    close = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24])
    r = ind.rsi(close, 14)
    assert len(r) == len(close)
    # 单边上涨，RSI 应接近 100
    assert r.iloc[-1] > 90


def test_rsi_oversold_low_value():
    close = pd.Series([20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6])
    r = ind.rsi(close, 14)
    assert r.iloc[-1] < 10


def test_bollinger_bands():
    close = pd.Series([10.0] * 20 + [12.0] * 5)
    mid, upper, lower = ind.bollinger(close, 20, 2.0)
    assert upper.iloc[-1] >= mid.iloc[-1] >= lower.iloc[-1]
    assert len(mid) == len(close)


def test_kdj_shape_and_cross():
    n = 20
    high = pd.Series([10 + i * 0.1 for i in range(n)])
    low = pd.Series([9 + i * 0.1 for i in range(n)])
    close = pd.Series([9.5 + i * 0.1 for i in range(n)])
    k, d, j = ind.kdj(high, low, close, 9)
    assert len(k) == n and len(d) == n and len(j) == n
    assert j.iloc[-1] == pytest.approx(3 * k.iloc[-1] - 2 * d.iloc[-1])
