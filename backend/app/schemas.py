"""Pydantic 请求/响应模型。"""

from typing import Optional

from pydantic import BaseModel, Field


def default_config() -> dict:
    """默认策略配置。"""
    return {
        "buy": {
            "maCross": {"enabled": False, "shortPeriod": 5, "longPeriod": 20},
            "macdCross": {"enabled": False, "fast": 12, "slow": 26, "signal": 9},
            "breakHigh": {"enabled": True, "days": 20},
            "volumeBreak": {"enabled": False, "multiple": 1.5, "avgDays": 5},
            "hammer": {"enabled": False},
            "bullishEngulfing": {"enabled": False},
            "morningStar": {"enabled": False},
            "threeWhiteSoldiers": {"enabled": False},
            "doubleBottom": {"enabled": False},
        },
        "sell": {
            "takeProfit": {"enabled": True, "percent": 10},
            "stopLoss": {"enabled": True, "percent": 5},
            "trailingStop": {"enabled": False, "drawdown": 8},
            "maDeathCross": {"enabled": False, "shortPeriod": 5, "longPeriod": 20},
            "macdDeathCross": {"enabled": False},
            "belowMA": {"enabled": False, "period": 20},
            "maxHoldDays": {"enabled": False, "days": 20},
            "hangingMan": {"enabled": False},
            "bearishEngulfing": {"enabled": False},
            "eveningStar": {"enabled": False},
            "threeBlackCrows": {"enabled": False},
            "doubleTop": {"enabled": False},
        },
        "risk": {
            "maxPositionPercent": 20,
            "maxHoldings": 10,
            "maxSingleLoss": 15,
            "totalStopLoss": 20,
            "maxDrawdown": 25,
        },
    }


class StrategyCreate(BaseModel):
    name: str
    enabled: bool = True
    config: dict = Field(default_factory=default_config)


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[dict] = None


class BacktestRequest(BaseModel):
    start_date: str = Field(default="", description="YYYY-MM-DD，空则默认近一年")
    end_date: str = Field(default="", description="YYYY-MM-DD，空则默认今天")
