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
    group_name: str = Field(default="", description="策略分组名称")
    config: dict = Field(default_factory=default_config)
    initial_capital: Optional[float] = Field(default=None, ge=0, description="策略分配本金，缺省为默认 100 万")


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    group_name: Optional[str] = None
    config: Optional[dict] = None
    initial_capital: Optional[float] = Field(default=None, ge=0, description="调整策略分配本金")


class StrategyBatchGroup(BaseModel):
    ids: list[int] = Field(description="策略 ID 列表")
    group_name: str = Field(description="目标分组名称")


class StrategyBatchToggle(BaseModel):
    ids: list[int] = Field(description="策略 ID 列表")
    enabled: bool = Field(description="批量启用/停用")


class StrategyBatchDelete(BaseModel):
    ids: list[int] = Field(description="策略 ID 列表")


class BacktestRequest(BaseModel):
    start_date: str = Field(default="", description="YYYY-MM-DD，空则默认近一年")
    end_date: str = Field(default="", description="YYYY-MM-DD，空则默认今天")


class OptimizeRequest(BaseModel):
    start_date: str = Field(default="", description="YYYY-MM-DD，空则默认近一年")
    end_date: str = Field(default="", description="YYYY-MM-DD，空则默认今天")
    param_grid: dict = Field(description="参数网格，键为点分路径，值为候选列表")
    stock_limit: Optional[int] = Field(default=200, description="抽样股票数量，0 表示全市场")


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


class OrderPrepareRequest(BaseModel):
    code: str = Field(description="股票代码")
    name: str = Field(default="", description="股票名称")
    direction: str = Field(description="buy/sell")
    price: float = Field(gt=0, description="委托价格")
    qty: int = Field(ge=100, description="委托数量（100 股整数倍）")
    strategy_id: Optional[int] = Field(default=None, description="所属策略 ID")
    reason: str = Field(default="", description="下单理由")
