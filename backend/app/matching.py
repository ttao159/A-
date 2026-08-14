"""撮合引擎：模拟成交与费用计算。"""

import pandas as pd

from . import config

# 涨跌停判断阈值（主板 ±10%，留少量容差）
LIMIT_RATIO = 0.098


def calc_fees(direction: str, price: float, qty: int):
    """返回 (commission, tax, transfer_fee)。"""
    amount = price * qty
    commission = max(amount * config.COMMISSION_RATE, config.COMMISSION_MIN)
    tax = amount * config.STAMP_TAX_RATE if direction == "sell" else 0.0
    transfer_fee = amount * config.TRANSFER_FEE_RATE
    return commission, tax, transfer_fee


def match_fill(direction: str, prev_close: float, next_bar: pd.Series):
    """按下一交易日开盘价撮合。

    返回 (fill_price, reject_reason)。fill_price 为 None 表示拒单。
    """
    open_price = next_bar.get("open")
    volume = next_bar.get("volume", 0)

    if open_price is None or pd.isna(open_price) or volume == 0:
        return None, "停牌无成交"
    if prev_close and prev_close > 0:
        chg = (open_price - prev_close) / prev_close
        if direction == "buy" and chg >= LIMIT_RATIO:
            return None, "涨停无法买入"
        if direction == "sell" and chg <= -LIMIT_RATIO:
            return None, "跌停无法卖出"
    return float(open_price), None


def round_lot(qty: int) -> int:
    """向下取整到 100 股整数倍。"""
    return (qty // 100) * 100
