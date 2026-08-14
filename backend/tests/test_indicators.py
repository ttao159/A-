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
