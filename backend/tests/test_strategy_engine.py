import pandas as pd

from app import strategy_engine as se


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
