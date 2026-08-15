import pandas as pd
from unittest import mock

from app import strategy_engine as se
from app.schemas import default_config


def make_bars(closes, highs=None):
    n = len(closes)
    highs = highs if highs is not None else list(closes)
    return pd.DataFrame({
        "open": list(closes),
        "high": list(highs),
        "low": list(closes),
        "close": list(closes),
        "volume": [10000] * n,
    })


def buy_config(**enabled):
    keys = ["maCross", "macdCross", "breakHigh", "volumeBreak"]
    buy = {k: {"enabled": False, "shortPeriod": 5, "longPeriod": 20,
               "fast": 12, "slow": 26, "signal": 9, "days": 20,
               "multiple": 1.5, "avgDays": 5} for k in keys}
    for k in enabled:
        buy[k]["enabled"] = True
    sell = {"takeProfit": {"enabled": False, "percent": 10},
            "stopLoss": {"enabled": False, "percent": 5}}
    return {"buy": buy, "sell": sell, "risk": {}}


def sell_config(**enabled):
    sell = {
        "takeProfit": {"enabled": False, "percent": 10},
        "stopLoss": {"enabled": False, "percent": 5},
        "trailingStop": {"enabled": False, "drawdown": 8},
        "maDeathCross": {"enabled": False, "shortPeriod": 5, "longPeriod": 20},
        "macdDeathCross": {"enabled": False},
        "belowMA": {"enabled": False, "period": 20},
        "maxHoldDays": {"enabled": False, "days": 20},
    }
    for k in enabled:
        sell[k]["enabled"] = True
    return {"buy": {}, "sell": sell, "risk": {}}


def position(avg_cost=10.0, hold_days=3, high=10.5):
    return {"code": "600000", "name": "测试", "qty": 100,
            "avg_cost": avg_cost, "hold_days": hold_days, "high_since_buy": high}


# ===== 买入信号 =====
def test_buy_no_signal_returns_false():
    bars = make_bars([10.0] * 30)
    assert se.evaluate_buy(buy_config(), bars) is False


def test_buy_breakout_triggers():
    closes = [10.0] * 21 + [11.0]
    highs = [10.5] * 21 + [11.0]
    bars = make_bars(closes, highs)
    assert se.evaluate_buy(buy_config(breakHigh=True), bars) is True


def test_buy_breakout_not_triggered():
    closes = [10.0] * 22
    highs = [10.5] * 22
    bars = make_bars(closes, highs)
    assert se.evaluate_buy(buy_config(breakHigh=True), bars) is False


# ===== 卖出信号 =====
def test_sell_take_profit():
    bars = make_bars([10.0, 10.5, 11.0])  # 最新价 11，成本 10，盈利 10%
    assert se.evaluate_sell(sell_config(takeProfit=True), position(avg_cost=10.0), bars) == "takeProfit"


def test_sell_stop_loss():
    bars = make_bars([10.0, 9.8, 9.5])  # 最新价 9.5，成本 10，亏损 5%
    assert se.evaluate_sell(sell_config(stopLoss=True), position(avg_cost=10.0), bars) == "stopLoss"


def test_sell_no_signal():
    bars = make_bars([10.0, 10.1, 10.2])
    assert se.evaluate_sell(sell_config(takeProfit=True, stopLoss=True),
                            position(avg_cost=10.0), bars) is None


def test_sell_max_hold_days():
    bars = make_bars([10.0] * 5)
    assert se.evaluate_sell(sell_config(maxHoldDays=True),
                            position(avg_cost=10.0, hold_days=20), bars) == "maxHoldDays"


def test_sell_t1_blocks_same_day():
    bars = make_bars([10.0, 9.0, 8.0])  # 大跌本应触发止损
    pos = position(avg_cost=10.0, hold_days=0)
    assert se.evaluate_sell(sell_config(stopLoss=True), pos, bars) is None


def test_sell_max_single_loss():
    cfg = {"buy": {}, "sell": {"takeProfit": {"enabled": False}},
           "risk": {"maxSingleLoss": 15}}
    bars = make_bars([10.0, 9.0, 8.0])  # 亏损 20%，超过 15% 阈值
    pos = position(avg_cost=10.0, hold_days=5)
    assert se.evaluate_sell(cfg, pos, bars) == "maxSingleLoss"


def cfg_only(buy_key=None, sell_key=None):
    """基于默认配置，仅启用指定信号，其余全部关闭。"""
    cfg = default_config()
    for v in cfg["buy"].values():
        v["enabled"] = False
    for v in cfg["sell"].values():
        v["enabled"] = False
    if buy_key:
        cfg["buy"][buy_key]["enabled"] = True
    if sell_key:
        cfg["sell"][sell_key]["enabled"] = True
    return cfg


# ===== 新增买入信号 =====
def test_buy_rsi_oversold_triggers():
    bars = make_bars([10.0] * 20)
    rsi = pd.Series([50.0] * 18 + [25.0, 32.0])
    with mock.patch("app.strategy_engine.ind.rsi", return_value=rsi):
        assert se.evaluate_buy(cfg_only(buy_key="rsiOversold"), bars) is True


def test_buy_rsi_oversold_not_triggered():
    bars = make_bars([10.0] * 20)
    rsi = pd.Series([50.0] * 18 + [25.0, 28.0])  # 未上穿阈值
    with mock.patch("app.strategy_engine.ind.rsi", return_value=rsi):
        assert se.evaluate_buy(cfg_only(buy_key="rsiOversold"), bars) is False


def test_buy_kdj_golden_cross_triggers():
    bars = make_bars([10.0] * 20)
    k = pd.Series([40.0] * 18 + [30.0, 45.0])
    d = pd.Series([40.0] * 18 + [35.0, 40.0])
    j = pd.Series([40.0] * 20)
    with mock.patch("app.strategy_engine.ind.kdj", return_value=(k, d, j)):
        assert se.evaluate_buy(cfg_only(buy_key="kdjGoldenCross"), bars) is True


def test_buy_kdj_golden_cross_high_zone_skipped():
    bars = make_bars([10.0] * 20)
    k = pd.Series([70.0] * 18 + [60.0, 75.0])
    d = pd.Series([70.0] * 18 + [65.0, 70.0])
    j = pd.Series([70.0] * 20)
    with mock.patch("app.strategy_engine.ind.kdj", return_value=(k, d, j)):
        # D > 50（高位区），不满足低位金叉
        assert se.evaluate_buy(cfg_only(buy_key="kdjGoldenCross"), bars) is False


def test_buy_boll_lower_rebound_triggers():
    closes = [10.0] * 19 + [9.4, 10.0]
    bars = make_bars(closes)
    mid = pd.Series([10.0] * 21)
    upper = pd.Series([11.0] * 21)
    lower = pd.Series([9.5] * 19 + [9.5, 9.6])
    with mock.patch("app.strategy_engine.ind.bollinger", return_value=(mid, upper, lower)):
        assert se.evaluate_buy(cfg_only(buy_key="bollLowerRebound"), bars) is True


# ===== 新增卖出信号 =====
def test_sell_rsi_overbought_triggers():
    bars = make_bars([10.0] * 20)
    rsi = pd.Series([50.0] * 18 + [75.0, 68.0])
    with mock.patch("app.strategy_engine.ind.rsi", return_value=rsi):
        assert se.evaluate_sell(cfg_only(sell_key="rsiOverbought"), position(), bars) == "rsiOverbought"


def test_sell_kdj_death_cross_triggers():
    bars = make_bars([10.0] * 20)
    k = pd.Series([60.0] * 18 + [80.0, 60.0])
    d = pd.Series([60.0] * 18 + [70.0, 65.0])
    j = pd.Series([60.0] * 20)
    with mock.patch("app.strategy_engine.ind.kdj", return_value=(k, d, j)):
        assert se.evaluate_sell(cfg_only(sell_key="kdjDeathCross"), position(), bars) == "kdjDeathCross"


def test_sell_boll_below_mid_triggers():
    closes = [10.0] * 19 + [10.0, 9.4]
    bars = make_bars(closes)
    mid = pd.Series([10.0] * 21)
    upper = pd.Series([11.0] * 21)
    lower = pd.Series([9.0] * 21)
    with mock.patch("app.strategy_engine.ind.bollinger", return_value=(mid, upper, lower)):
        assert se.evaluate_sell(cfg_only(sell_key="bollBelowMid"), position(), bars) == "bollBelowMid"


# ===== 向量化买入信号与逐 bar 一致性 =====
def test_buy_signal_mask_matches_evaluate_buy():
    import numpy as np
    closes = [10.0] * 20 + [11.0, 10.5, 10.8, 11.2]
    highs = [10.5] * 20 + [11.0, 10.6, 10.9, 11.3]
    bars = make_bars(closes, highs)
    for key in ["breakHigh", "maCross", "macdCross", "volumeBreak",
                "rsiOversold", "kdjGoldenCross", "bollLowerRebound"]:
        cfg = cfg_only(buy_key=key)
        mask = se.buy_signal_mask(cfg, bars)
        assert mask is not None, f"{key} 未向量化"
        ref = np.array([se.evaluate_buy(cfg, bars.iloc[:i + 1]) for i in range(len(bars))])
        assert np.array_equal(mask, ref), f"{key} 向量化与逐 bar 不一致"


def test_buy_signal_mask_returns_none_for_patterns():
    cfg = cfg_only(buy_key="hammer")
    bars = make_bars([10.0] * 30)
    assert se.buy_signal_mask(cfg, bars) is None
