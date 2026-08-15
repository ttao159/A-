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
            "rsiOversold": {"enabled": False, "period": 14, "threshold": 30},
            "kdjGoldenCross": {"enabled": False, "n": 9, "lowZone": 50},
            "bollLowerRebound": {"enabled": False, "period": 20, "numStd": 2},
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
            "rsiOverbought": {"enabled": False, "period": 14, "threshold": 70},
            "kdjDeathCross": {"enabled": False, "n": 9, "highZone": 50},
            "bollBelowMid": {"enabled": False, "period": 20, "numStd": 2},
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


class TargetsInput(BaseModel):
    scope: str = Field(description="single/custom/market")
    codes: list[str] = Field(default_factory=list, description="股票代码列表")


class GeneratorRequest(BaseModel):
    targets: TargetsInput
    start_date: str = Field(description="YYYY-MM-DD")
    end_date: str = Field(description="YYYY-MM-DD")
    risk_profile: str = Field(description="conservative/balanced/aggressive")
    count: int = Field(ge=1, le=10, description="生成策略数量")
    target_annual_return: float = Field(default=0.0, ge=0, description="目标年化收益率（%）")
    analysis_depth: Optional[str] = Field(default="standard", description="quick/standard/deep")
