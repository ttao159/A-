"""券商接口抽象层：统一订单与账户操作，屏蔽模拟盘与实盘差异。"""

from abc import ABC, abstractmethod

from . import config
from .account import AccountService
from .models import Order, Position, Strategy, Trade

BROKER_PAPER = "paper"
BROKER_LIVE = "live"


class BrokerAdapter(ABC):
    """券商适配器抽象基类。

    模拟盘（PaperBroker）与实盘（LiveBroker）均实现此接口，
    业务层（扫描交易、账户查询）通过该接口统一下单与查询。
    """

    broker_type = BROKER_PAPER

    @abstractmethod
    def place_order(self, db, code, name, direction, price, qty, reason="", strategy=None):
        """下单并返回 Order 对象。"""

    @abstractmethod
    def cancel_order(self, db, order_id):
        """撤单并返回 Order 对象。"""

    @abstractmethod
    def get_account(self, db):
        """查询账户快照，返回 dict。"""

    @abstractmethod
    def get_positions(self, db):
        """查询持仓列表。"""

    @abstractmethod
    def get_orders(self, db):
        """查询委托列表。"""

    @abstractmethod
    def get_trades(self, db):
        """查询成交列表。"""

    @abstractmethod
    def reconcile(self, db):
        """对账，返回 dict。"""


class PaperBroker(BrokerAdapter):
    """模拟券商：复用 AccountService 完成模拟撮合与费用计算。"""

    broker_type = BROKER_PAPER

    def __init__(self, accounts: AccountService = None):
        self._accounts = accounts or AccountService()

    def place_order(self, db, code, name, direction, price, qty, reason="", strategy=None):
        acct = self._accounts.ensure_account(db, config.DEFAULT_INITIAL_CAPITAL)
        order = self._accounts.place_order(
            db, acct, code, name, direction, price, qty, reason, strategy)
        order.broker_type = self.broker_type
        db.commit()
        db.refresh(order)
        return order

    def cancel_order(self, db, order_id):
        order = db.query(Order).filter(Order.id == order_id).first()
        if order is None:
            raise ValueError("订单不存在")
        if order.status == "filled":
            raise ValueError("订单已成交，无法撤单")
        raise ValueError("订单已拒绝，无法撤单")

    def get_account(self, db):
        acct, _, _ = self._accounts.get_snapshot(db)
        return {
            "broker_type": self.broker_type,
            "account_id": acct.id,
            "initial_capital": round(acct.initial_capital or 0.0, 2),
            "available_cash": round(acct.available_cash or 0.0, 2),
        }

    def get_positions(self, db):
        _, positions, _ = self._accounts.get_snapshot(db)
        return [self._position_out(p) for p in positions]

    def get_orders(self, db):
        acct = self._accounts.ensure_account(db, config.DEFAULT_INITIAL_CAPITAL)
        orders = db.query(Order).filter(Order.account_id == acct.id).order_by(Order.id.desc()).all()
        return [self._order_out(o) for o in orders]

    def get_trades(self, db):
        _, _, trades = self._accounts.get_snapshot(db)
        return [self._trade_out(t) for t in trades]

    def reconcile(self, db):
        """对账：校验各策略资金守恒（现金 + 持仓成本 = 本金 + 已实现盈亏）。"""
        strategies = db.query(Strategy).all()
        items = []
        for s in strategies:
            positions = db.query(Position).filter(Position.strategy_id == s.id).all()
            invested = sum((p.avg_cost or 0.0) * p.qty for p in positions)
            realized = sum(
                t.pnl or 0.0 for t in db.query(Trade).filter(
                    Trade.strategy_id == s.id, Trade.direction == "sell").all())
            actual = (s.available_cash or 0.0) + invested
            expected = (s.initial_capital or 0.0) + realized
            items.append({
                "strategy_id": s.id,
                "name": s.name,
                "initial_capital": round(s.initial_capital or 0.0, 2),
                "available_cash": round(s.available_cash or 0.0, 2),
                "invested": round(invested, 2),
                "realized_pnl": round(realized, 2),
                "actual_equity": round(actual, 2),
                "expected_equity": round(expected, 2),
                "balanced": abs(actual - expected) < 0.01,
            })
        return {"broker_type": self.broker_type, "strategies": items}

    @staticmethod
    def _position_out(p):
        return {
            "code": p.code, "name": p.name, "qty": p.qty,
            "avg_cost": round(p.avg_cost or 0.0, 3),
            "hold_days": p.hold_days or 0,
            "strategy_id": p.strategy_id,
        }

    @staticmethod
    def _order_out(o):
        return {
            "id": o.id, "code": o.code, "name": o.name,
            "direction": o.direction, "qty": o.qty, "price": o.price,
            "status": o.status, "reason": o.reason,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }

    @staticmethod
    def _trade_out(t):
        return {
            "id": t.id, "code": t.code, "name": t.name,
            "direction": t.direction, "qty": t.qty, "price": t.price,
            "commission": round(t.commission or 0.0, 2),
            "tax": round(t.tax or 0.0, 2),
            "transfer_fee": round(t.transfer_fee or 0.0, 2),
            "pnl": round(t.pnl or 0.0, 2),
            "strategy_id": t.strategy_id,
            "traded_at": t.traded_at.isoformat() if t.traded_at else None,
        }


class LiveBroker(BrokerAdapter):
    """实盘券商占位：本期未接入真实券商，各方法返回明确错误。"""

    broker_type = BROKER_LIVE

    def _unavailable(self):
        raise ValueError("实盘券商未接入")

    def place_order(self, db, code, name, direction, price, qty, reason="", strategy=None):
        self._unavailable()

    def cancel_order(self, db, order_id):
        self._unavailable()

    def get_account(self, db):
        self._unavailable()

    def get_positions(self, db):
        self._unavailable()

    def get_orders(self, db):
        self._unavailable()

    def get_trades(self, db):
        self._unavailable()

    def reconcile(self, db):
        self._unavailable()


def get_broker(broker_type: str = BROKER_PAPER) -> BrokerAdapter:
    """按券商类型返回适配器实例，缺省为模拟盘。"""
    if broker_type == BROKER_LIVE:
        return LiveBroker()
    return PaperBroker()
