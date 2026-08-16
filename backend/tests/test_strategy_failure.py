from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Account, Alert, Strategy, Trade
from app.scanner import _detect_strategy_failure


def _make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    acct = Account(initial_capital=1_000_000.0, available_cash=1_000_000.0)
    db.add(acct)
    db.commit()
    return db, acct


def _add_sell(db, acct, strategy_id, pnl):
    db.add(Trade(order_id=1, account_id=acct.id, strategy_id=strategy_id, code="600000",
                 name="测试", direction="sell", qty=100, price=10.0, pnl=pnl))
    db.commit()


def test_failure_consecutive_sell_losses():
    db, acct = _make_db()
    s = Strategy(name="亏损策略", enabled=1, config_json="{}",
                 initial_capital=1_000_000.0, available_cash=1_000_000.0)
    db.add(s)
    db.commit()
    for _ in range(5):
        _add_sell(db, acct, s.id, -100.0)

    failed = _detect_strategy_failure(db, acct, s, {}, equity=1_000_000.0)
    assert failed is True
    db.refresh(s)
    assert s.enabled == 0
    assert db.query(Alert).filter(Alert.alert_type == "strategy_failed").first() is not None
    db.close()


def test_failure_drawdown():
    db, acct = _make_db()
    s = Strategy(name="回撤策略", enabled=1, config_json="{}",
                 initial_capital=1_000_000.0, available_cash=800_000.0)
    db.add(s)
    db.commit()

    failed = _detect_strategy_failure(db, acct, s, {}, equity=800_000.0)
    assert failed is True
    db.refresh(s)
    assert s.enabled == 0
    db.close()


def test_no_failure_with_profit():
    db, acct = _make_db()
    s = Strategy(name="盈利策略", enabled=1, config_json="{}",
                 initial_capital=1_000_000.0, available_cash=1_100_000.0)
    db.add(s)
    db.commit()
    _add_sell(db, acct, s.id, 50.0)

    failed = _detect_strategy_failure(db, acct, s, {}, equity=1_100_000.0)
    assert failed is False
    db.refresh(s)
    assert s.enabled == 1
    db.close()


def test_no_failure_when_sells_below_threshold():
    db, acct = _make_db()
    s = Strategy(name="正常策略", enabled=1, config_json="{}",
                 initial_capital=1_000_000.0, available_cash=1_000_000.0)
    db.add(s)
    db.commit()
    for _ in range(3):
        _add_sell(db, acct, s.id, -100.0)

    failed = _detect_strategy_failure(db, acct, s, {}, equity=1_000_000.0)
    assert failed is False
    db.close()


def test_thresholds_configurable():
    db, acct = _make_db()
    s = Strategy(name="低阈值策略", enabled=1, config_json="{}",
                 initial_capital=1_000_000.0, available_cash=1_000_000.0)
    db.add(s)
    db.commit()
    for _ in range(2):
        _add_sell(db, acct, s.id, -100.0)

    cfg = {"risk": {"maxConsecutiveLosses": 2}}
    failed = _detect_strategy_failure(db, acct, s, cfg, equity=1_000_000.0)
    assert failed is True
    db.close()
