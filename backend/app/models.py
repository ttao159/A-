"""ORM 数据模型。"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from .database import Base


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    enabled = Column(Integer, default=1)
    config_json = Column(Text, nullable=False)
    initial_capital = Column(Float, default=0.0)
    available_cash = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    initial_capital = Column(Float, nullable=False)
    available_cash = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)
    code = Column(String(20), nullable=False)
    name = Column(String(50), nullable=False)
    qty = Column(Integer, nullable=False)
    avg_cost = Column(Float, nullable=False)
    hold_days = Column(Integer, default=0)
    high_since_buy = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(50), nullable=False)
    direction = Column(String(10), nullable=False)  # buy / sell
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)
    status = Column(String(20), nullable=False)  # filled / rejected
    reason = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)
    code = Column(String(20), nullable=False)
    name = Column(String(50), nullable=False)
    direction = Column(String(10), nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    transfer_fee = Column(Float, default=0.0)
    pnl = Column(Float, default=0.0)
    traded_at = Column(DateTime, default=datetime.utcnow)


class Backtest(Base):
    __tablename__ = "backtests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    start_date = Column(String(20), nullable=False)
    end_date = Column(String(20), nullable=False)
    metrics_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EquityPoint(Base):
    __tablename__ = "equity_curve"

    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=False)
    date = Column(String(20), nullable=False)
    equity = Column(Float, nullable=False)


class ScanReport(Base):
    __tablename__ = "scan_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_count = Column(Integer, default=0)
    buy_count = Column(Integer, default=0)
    sell_count = Column(Integer, default=0)
    reject_count = Column(Integer, default=0)
    source = Column(String(10), default="manual")  # manual / auto
    report_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyBarCache(Base):
    __tablename__ = "daily_bar_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    period = Column(String(10), nullable=False, default="day")
    adjust = Column(String(10), nullable=False, default="qfq")
    data_json = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("code", "period", "adjust", name="uq_bar_cache"),)


class GenerationReport(Base):
    __tablename__ = "generation_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_json = Column(Text, nullable=False)
    report_json = Column(Text, nullable=False)
    recommended_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
