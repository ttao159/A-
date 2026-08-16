"""券商接口抽象层：统一订单与账户操作，屏蔽模拟盘与实盘差异。"""

from abc import ABC, abstractmethod

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
