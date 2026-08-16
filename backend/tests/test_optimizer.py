import pytest
import pandas as pd

from app import optimizer


class _FakeMarket:
    """固定行情，避免真实网络请求。"""

    def get_stock_list(self):
        return [("600519", "贵州茅台"), ("600036", "招商银行")]

    def get_daily_bars(self, code, start, end):
        n = 200
        dates = pd.bdate_range("2025-01-01", periods=n).strftime("%Y-%m-%d").tolist()
        close = [10.0 * (1 + i * 0.02) for i in range(n)]
        return pd.DataFrame({
            "date": dates, "open": close, "high": [c * 1.005 for c in close],
            "low": [c * 0.995 for c in close], "close": close, "volume": [1e6] * n,
        })


def _cfg():
    return {
        "buy": {"breakHigh": {"enabled": True, "days": 20}},
        "sell": {},
        "risk": {"maxPositionPercent": 20, "maxHoldings": 10},
    }


def test_optimize_returns_sorted_results():
    market = _FakeMarket()
    results, sample = optimizer.optimize(_cfg(), market, "2025-01-01", "2026-01-01",
                                         {"buy.breakHigh.days": [10, 20, 30]})
    assert len(results) == 3
    assert sample["total_stocks"] == 2
    returns = [r["metrics"]["total_return_pct"] for r in results]
    assert returns == sorted(returns, reverse=True)


def test_optimize_sets_params():
    market = _FakeMarket()
    results, _ = optimizer.optimize(_cfg(), market, "2025-01-01", "2026-01-01",
                                    {"buy.breakHigh.days": [10, 20]})
    days = sorted(r["params"]["buy.breakHigh.days"] for r in results)
    assert days == [10, 20]


def test_optimize_rejects_too_many_combos():
    market = _FakeMarket()
    grid = {"risk.maxPositionPercent": list(range(100))}
    with pytest.raises(ValueError):
        optimizer.optimize(_cfg(), market, "2025-01-01", "2026-01-01", grid)
