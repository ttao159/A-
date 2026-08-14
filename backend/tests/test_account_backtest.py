import pytest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import backtest
from app.account import AccountService, Portfolio, check_risk
from app.database import Base
from app.market import MarketDataService
from app.models import Account, Position
from app.schemas import default_config


def make_state(**overrides):
    state = {
        "initial_capital": 1_000_000.0,
        "cash": 1_000_000.0,
        "positions": {},
        "high_water": 1_000_000.0,
    }
    state.update(overrides)
    return state


# ===== 风控 =====
def test_risk_max_holdings():
    positions = {f"c{i}": {"code": f"c{i}", "qty": 100, "avg_cost": 10.0} for i in range(10)}
    cfg = {"risk": {"maxHoldings": 10, "maxPositionPercent": 20}}
    ok, reason = check_risk(make_state(positions=positions), cfg, 10.0, 100, {})
    assert ok is False
    assert "持仓" in reason


def test_risk_max_position_percent():
    cfg = {"risk": {"maxHoldings": 10, "maxPositionPercent": 20}}
    # 单只 30 万 > 100 万 * 20%
    ok, _ = check_risk(make_state(), cfg, 100.0, 3000, {})
    assert ok is False


def test_risk_total_stop_loss():
    state = make_state(cash=750_000.0)  # 已亏 25%，触发 20% 止损线
    cfg = {"risk": {"totalStopLoss": 20, "maxHoldings": 10, "maxPositionPercent": 20}}
    ok, _ = check_risk(state, cfg, 10.0, 100, {})
    assert ok is False


def test_risk_ok():
    cfg = {"risk": {"maxHoldings": 10, "maxPositionPercent": 20, "totalStopLoss": 20, "maxDrawdown": 25}}
    ok, _ = check_risk(make_state(), cfg, 10.0, 1000, {})
    assert ok is True


# ===== Portfolio =====
def test_portfolio_buy_updates_cash():
    pf = Portfolio(1_000_000.0)
    qty = pf.buy("600000", "测试", 10.0, 1000, "2026-01-01")
    assert qty == 1000
    assert pf.cash < 1_000_000.0
    assert "600000" in pf.positions
    assert pf.positions["600000"]["qty"] == 1000


def test_portfolio_sell_realizes_pnl():
    pf = Portfolio(1_000_000.0)
    pf.buy("600000", "测试", 10.0, 1000, "2026-01-01")
    pf.sell("600000", 12.0, 1000, "2026-01-02")
    assert "600000" not in pf.positions
    assert pf.total_realized_pnl > 0


# ===== 回测 =====
def test_backtest_returns_structure():
    market = MarketDataService()
    cfg = default_config()
    result = backtest.run_backtest(cfg, market, "2025-01-01", "2026-01-01")
    assert set(result.keys()) == {"metrics", "equity_curve", "trades"}
    assert "total_return_pct" in result["metrics"]
    assert "max_drawdown_pct" in result["metrics"]
    assert len(result["equity_curve"]) > 0


def test_compute_metrics_basic():
    pf = Portfolio(1_000_000.0)
    pf.trades.append({"direction": "sell", "pnl": 1000.0})
    pf.trades.append({"direction": "sell", "pnl": -500.0})
    curve = [{"date": "2026-01-01", "equity": 1_000_000.0},
             {"date": "2026-01-02", "equity": 1_050_000.0}]
    m = backtest.compute_metrics(curve, pf)
    assert m["total_return_pct"] == pytest.approx(5.0)
    assert m["win_rate_pct"] == pytest.approx(50.0)


def test_roll_daily_increments_hold_days_once_per_day():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    acct = Account(initial_capital=1_000_000.0, available_cash=1_000_000.0)
    db.add(acct)
    db.commit()

    yesterday = datetime.utcnow() - timedelta(days=1)
    db.add(Position(account_id=acct.id, code="600000", name="测试", qty=100,
                    avg_cost=10.0, hold_days=0, high_since_buy=10.0, updated_at=yesterday))
    db.commit()

    svc = AccountService()
    svc.roll_daily(db)
    p = db.query(Position).first()
    assert p.hold_days == 1

    # 同一天重复 roll 不应再次 +1
    svc.roll_daily(db)
    db.refresh(p)
    assert p.hold_days == 1
    db.close()
