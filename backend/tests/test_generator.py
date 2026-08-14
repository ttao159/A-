"""策略生成引擎单元测试。"""

import sys
from unittest import mock

import pandas as pd
import pytest

sys.path.insert(0, "..")  # noqa: E402

from app import generator
from app.generator import (
    RISK_PROFILES,
    SIGNAL_TEMPLATES,
    generate_strategies,
    run_generation,
    score_strategy,
    validate_params,
)
from app.public_data import DataUnavailableError


def _valid_payload(**overrides):
    payload = {
        "targets": {"scope": "single", "codes": ["600519"]},
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "risk_profile": "balanced",
        "count": 3,
        "target_annual_return": 15.0,
    }
    payload.update(overrides)
    return payload


def _fake_bars(n=120):
    dates = pd.bdate_range("2024-01-01", periods=n).strftime("%Y-%m-%d").tolist()
    base = 100.0
    close = [base * (1 + i * 0.001) for i in range(n)]
    return pd.DataFrame({
        "date": dates,
        "open": close, "high": [c * 1.01 for c in close],
        "low": [c * 0.99 for c in close], "close": close,
        "volume": [1e6] * n,
    })


class _FakeMarket:
    """模拟公开数据服务，返回固定行情。"""

    def __init__(self, n=120):
        self.bars = _fake_bars(n)

    def get_stock_list(self):
        return [("600519", "贵州茅台"), ("600036", "招商银行")]

    def get_stock_names(self, codes):
        return {c: f"股票{c}" for c in codes}

    def get_daily_bars(self, code, start, end):
        df = self.bars
        return df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)


class _EmptyMarket(_FakeMarket):
    def get_daily_bars(self, code, start, end):
        return self.bars.iloc[0:0]


class _FailMarket(_FakeMarket):
    def get_daily_bars(self, code, start, end):
        raise DataUnavailableError("数据源不可用")


# ===== validate_params =====
class TestValidateParams:
    def test_valid_payload_passes(self):
        validate_params(_valid_payload())

    def test_invalid_risk_profile_rejected(self):
        with pytest.raises(ValueError):
            validate_params(_valid_payload(risk_profile="super"))

    def test_count_zero_rejected(self):
        with pytest.raises(ValueError):
            validate_params(_valid_payload(count=0))

    def test_count_eleven_rejected(self):
        with pytest.raises(ValueError):
            validate_params(_valid_payload(count=11))

    def test_count_float_rejected(self):
        with pytest.raises(ValueError):
            validate_params(_valid_payload(count=3.5))

    def test_bad_date_format_rejected(self):
        with pytest.raises(ValueError):
            validate_params(_valid_payload(start_date="2024/01/01"))

    def test_end_before_start_rejected(self):
        with pytest.raises(ValueError):
            validate_params(_valid_payload(start_date="2025-01-01", end_date="2024-01-01"))

    def test_negative_target_rejected(self):
        with pytest.raises(ValueError):
            validate_params(_valid_payload(target_annual_return=-5))

    def test_empty_codes_rejected(self):
        with pytest.raises(ValueError):
            validate_params(_valid_payload(targets={"scope": "single", "codes": []}))

    def test_invalid_code_rejected(self):
        with pytest.raises(ValueError):
            validate_params(_valid_payload(targets={"scope": "single", "codes": ["12ab"]}))

    def test_bad_scope_rejected(self):
        with pytest.raises(ValueError):
            validate_params(_valid_payload(targets={"scope": "global", "codes": ["600519"]}))


# ===== generate_strategies =====
class TestGenerateStrategies:
    def test_generates_requested_count(self):
        strategies = generate_strategies(5, "balanced")
        assert len(strategies) == 5

    def test_each_strategy_structure_valid(self):
        for cfg in generate_strategies(3, "balanced"):
            assert set(cfg) == {"buy", "sell", "risk"}
            assert any(v.get("enabled") for v in cfg["buy"].values())
            assert any(v.get("enabled") for v in cfg["sell"].values())

    def test_strategies_differ(self):
        strategies = generate_strategies(4, "balanced")
        serialized = [str(s) for s in strategies]
        assert len(set(serialized)) >= 2

    def test_risk_profile_mapping_applied(self):
        cons = generate_strategies(1, "conservative")[0]["risk"]
        agg = generate_strategies(1, "aggressive")[0]["risk"]
        assert cons["maxPositionPercent"] < agg["maxPositionPercent"]
        assert cons["maxSingleLoss"] < agg["maxSingleLoss"]
        assert cons["maxDrawdown"] < agg["maxDrawdown"]

    def test_risk_profiles_match_mapping_table(self):
        for name, params in RISK_PROFILES.items():
            cfg = generate_strategies(1, name)[0]
            assert cfg["risk"] == params

    def test_templates_reference_existing_signals(self):
        from app.schemas import default_config

        base = default_config()
        for tpl in SIGNAL_TEMPLATES:
            for key in tpl["buy"]:
                assert key in base["buy"], f"未知买入信号: {key}"
            for key in tpl["sell"]:
                assert key in base["sell"], f"未知卖出信号: {key}"


# ===== score_strategy =====
class TestScoreStrategy:
    def test_no_trades_scores_lowest(self):
        assert score_strategy({}, 10) == -100.0
        assert score_strategy({"trade_count": 0}, 10) == -100.0

    def test_higher_annual_scores_higher(self):
        base = {"trade_count": 10, "annual_return_pct": 10, "max_drawdown_pct": 10,
                "win_rate_pct": 50, "profit_loss_ratio": 1.0}
        better = dict(base, annual_return_pct=30)
        assert score_strategy(better) > score_strategy(base)

    def test_lower_drawdown_scores_higher(self):
        base = {"trade_count": 10, "annual_return_pct": 10, "max_drawdown_pct": 25,
                "win_rate_pct": 50, "profit_loss_ratio": 1.0}
        better = dict(base, max_drawdown_pct=5)
        assert score_strategy(better) > score_strategy(base)

    def test_target_proximity_improves_score(self):
        metrics = {"trade_count": 10, "annual_return_pct": 15, "max_drawdown_pct": 10,
                   "win_rate_pct": 50, "profit_loss_ratio": 1.0}
        close = score_strategy(metrics, 15)
        far = score_strategy(metrics, 50)
        assert close > far


# ===== run_generation =====
class TestRunGeneration:
    def test_full_flow_returns_report(self):
        report = run_generation(_valid_payload(count=3), _FakeMarket())
        assert len(report["strategies"]) == 3
        assert len(report["ranking"]) == 3
        assert report["recommended_index"] in {0, 1, 2}
        for s in report["strategies"]:
            assert "equity_curve" in s
            assert "metrics" in s
            assert "signals" in s
            assert s["signals"]["buy"]
            assert s["signals"]["sell"]
        assert report["request"]["count"] == 3

    def test_market_scope_uses_stock_list(self):
        report = run_generation(_valid_payload(targets={"scope": "market", "codes": []}), _FakeMarket())
        assert report["request"]["targets"]["scope"] == "market"
        assert len(report["strategies"]) == 3

    def test_single_scope_uses_first_code(self):
        payload = _valid_payload(targets={"scope": "single", "codes": ["600519", "600036"]})
        with mock.patch("app.generator.backtest.run_backtest",
                        wraps=generator.backtest.run_backtest) as bt:
            run_generation(payload, _FakeMarket())
            _, args, kwargs = bt.mock_calls[0]
            market_arg = kwargs.get("market") if kwargs else None
            if market_arg is None:
                market_arg = args[1]
            stock_list = market_arg.get_stock_list()
            assert len(stock_list) == 1
            assert stock_list[0][0] == "600519"

    def test_empty_bars_raises_data_error(self):
        with pytest.raises(DataUnavailableError):
            run_generation(_valid_payload(), _EmptyMarket())

    def test_data_failure_raises_data_error(self):
        with pytest.raises(DataUnavailableError):
            run_generation(_valid_payload(), _FailMarket())

    def test_insufficient_trading_days_rejected(self):
        with pytest.raises(ValueError):
            run_generation(_valid_payload(), _FakeMarket(n=30))
