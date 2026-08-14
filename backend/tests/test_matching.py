import pandas as pd
import pytest

from app import matching


def test_calc_fees_buy():
    c, tax, tf = matching.calc_fees("buy", 100.0, 1000)
    assert c == pytest.approx(25.0)  # 10万 * 万2.5
    assert tax == 0.0                # 买入无印花税
    assert tf == pytest.approx(1.0)  # 10万 * 万0.1


def test_calc_fees_sell():
    c, tax, tf = matching.calc_fees("sell", 100.0, 1000)
    assert tax == pytest.approx(50.0)  # 卖出印花税 0.05%


def test_commission_minimum():
    c, _, _ = matching.calc_fees("buy", 10.0, 100)  # 成交额 1000，佣金按最低 5 元
    assert c == pytest.approx(5.0)


def test_round_lot():
    assert matching.round_lot(250) == 200
    assert matching.round_lot(99) == 0
    assert matching.round_lot(1000) == 1000


def test_match_normal_buy():
    bar = pd.Series({"open": 10.0, "volume": 10000})
    price, reason = matching.match_fill("buy", 9.8, bar)
    assert price == pytest.approx(10.0)
    assert reason is None


def test_match_limit_up_buy_rejected():
    bar = pd.Series({"open": 11.0, "volume": 10000})
    price, reason = matching.match_fill("buy", 10.0, bar)
    assert price is None
    assert reason == "涨停无法买入"


def test_match_limit_down_sell_rejected():
    bar = pd.Series({"open": 9.0, "volume": 10000})
    price, reason = matching.match_fill("sell", 10.0, bar)
    assert price is None
    assert reason == "跌停无法卖出"


def test_match_suspended():
    bar = pd.Series({"open": 10.0, "volume": 0})
    price, reason = matching.match_fill("buy", 9.8, bar)
    assert price is None
    assert reason == "停牌无成交"
