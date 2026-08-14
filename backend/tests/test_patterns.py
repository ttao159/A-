import pandas as pd

from app import patterns as pat


def make_bars(rows):
    return pd.DataFrame(rows)


def flat(rows, n, o=10.0, h=10.2, l=9.8, c=10.0):
    for _ in range(n):
        rows.append({"open": o, "high": h, "low": l, "close": c})
    return rows


# ===== 看涨（买入）形态 =====
def test_hammer():
    rows = []
    flat(rows, 6, o=11.0, h=11.1, l=10.8, c=10.9)  # 前期下跌后
    rows.append({"open": 10.0, "high": 10.1, "low": 9.7, "close": 10.1})
    assert pat.detect(make_bars(rows), "hammer")


def test_hammer_rejects_uptrend():
    rows = []
    flat(rows, 6, o=9.0, h=9.2, l=8.9, c=9.1)  # 前期上涨（收盘更低为下跌）
    rows.append({"open": 10.0, "high": 10.1, "low": 9.7, "close": 10.1})
    assert not pat.detect(make_bars(rows), "hammer")


def test_bullish_engulfing():
    rows = [
        {"open": 10.0, "high": 10.2, "low": 8.9, "close": 9.0},
        {"open": 8.8, "high": 10.6, "low": 8.7, "close": 10.5},
    ]
    assert pat.detect(make_bars(rows), "bullishEngulfing")


def test_morning_star():
    rows = [
        {"open": 10.0, "high": 10.1, "low": 8.9, "close": 9.0},
        {"open": 8.9, "high": 9.0, "low": 8.8, "close": 9.0},
        {"open": 9.0, "high": 9.9, "low": 8.9, "close": 9.8},
    ]
    assert pat.detect(make_bars(rows), "morningStar")


def test_three_white_soldiers():
    rows = [
        {"open": 10.0, "high": 10.6, "low": 9.9, "close": 10.5},
        {"open": 10.3, "high": 10.9, "low": 10.2, "close": 10.8},
        {"open": 10.6, "high": 11.3, "low": 10.5, "close": 11.2},
    ]
    assert pat.detect(make_bars(rows), "threeWhiteSoldiers")


def test_double_bottom():
    rows = []
    flat(rows, 30)
    rows.append({"open": 9.5, "high": 9.6, "low": 9.0, "close": 9.2})       # 第一低点
    flat(rows, 9, o=10.0, h=11.1, l=9.9, c=10.8)                              # 反弹
    rows.append({"open": 9.8, "high": 9.9, "low": 9.1, "close": 9.4})       # 第二低点
    flat(rows, 19, o=10.5, h=11.6, l=10.4, c=11.4)                            # 突破颈线
    assert len(rows) == 60
    assert pat.detect(make_bars(rows), "doubleBottom")


# ===== 看跌（卖出）形态 =====
def test_hanging_man():
    rows = []
    flat(rows, 6, o=9.0, h=9.2, l=8.9, c=9.1)  # 前期上涨
    rows.append({"open": 10.0, "high": 10.1, "low": 9.7, "close": 10.1})
    assert pat.detect(make_bars(rows), "hangingMan")


def test_bearish_engulfing():
    rows = [
        {"open": 9.0, "high": 10.3, "low": 8.9, "close": 10.2},
        {"open": 10.4, "high": 10.5, "low": 8.8, "close": 8.9},
    ]
    assert pat.detect(make_bars(rows), "bearishEngulfing")


def test_evening_star():
    rows = [
        {"open": 9.0, "high": 10.2, "low": 8.9, "close": 10.1},
        {"open": 10.2, "high": 10.3, "low": 10.1, "close": 10.2},
        {"open": 10.1, "high": 10.2, "low": 9.0, "close": 9.1},
    ]
    assert pat.detect(make_bars(rows), "eveningStar")


def test_three_black_crows():
    rows = [
        {"open": 11.0, "high": 11.1, "low": 10.4, "close": 10.5},
        {"open": 10.4, "high": 10.5, "low": 9.9, "close": 10.0},
        {"open": 9.9, "high": 10.0, "low": 9.3, "close": 9.4},
    ]
    assert pat.detect(make_bars(rows), "threeBlackCrows")


def test_double_top():
    rows = []
    flat(rows, 30, o=10.0, h=10.2, l=9.8, c=10.0)
    rows.append({"open": 10.5, "high": 11.0, "low": 10.4, "close": 10.8})   # 第一高点
    flat(rows, 9, o=9.5, h=9.6, l=9.0, c=9.1)                                # 回落
    rows.append({"open": 10.2, "high": 10.9, "low": 10.1, "close": 10.6})   # 第二高点
    flat(rows, 19, o=9.0, h=9.1, l=8.6, c=8.8)                                # 跌破颈线
    assert len(rows) == 60
    assert pat.detect(make_bars(rows), "doubleTop")


def test_detect_unknown_returns_false():
    rows = []
    flat(rows, 10)
    assert pat.detect(make_bars(rows), "noSuchPattern") is False
