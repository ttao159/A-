"""策略生成引擎：启发式生成候选策略，回测对比并输出报告。"""

import re

from . import backtest
from .public_data import DataUnavailableError
from .schemas import default_config

RISK_PROFILES = {
    "conservative": {
        "maxPositionPercent": 10, "maxHoldings": 5,
        "maxSingleLoss": 8, "totalStopLoss": 15, "maxDrawdown": 15,
    },
    "balanced": {
        "maxPositionPercent": 20, "maxHoldings": 8,
        "maxSingleLoss": 12, "totalStopLoss": 20, "maxDrawdown": 20,
    },
    "aggressive": {
        "maxPositionPercent": 30, "maxHoldings": 12,
        "maxSingleLoss": 18, "totalStopLoss": 25, "maxDrawdown": 25,
    },
}

# 信号模板库：每项含买入/卖出信号组合与可扰动参数（多个取值按轮次选取）
SIGNAL_TEMPLATES = [
    {
        "name": "均线金叉趋势",
        "buy": {"maCross": {"shortPeriod": [5, 10, 5], "longPeriod": [20, 30, 60]}},
        "sell": {"takeProfit": {"percent": [10, 15, 20]},
                 "stopLoss": {"percent": [5, 6, 8]}},
    },
    {
        "name": "N日突破",
        "buy": {"breakHigh": {"days": [20, 40, 60]}},
        "sell": {"takeProfit": {"percent": [10, 15]},
                 "stopLoss": {"percent": [6, 8]}},
    },
    {
        "name": "MACD金叉",
        "buy": {"macdCross": {}},
        "sell": {"takeProfit": {"percent": [10, 15]},
                 "stopLoss": {"percent": [5, 7]}},
    },
    {
        "name": "放量突破",
        "buy": {"volumeBreak": {"multiple": [1.5, 2.0], "avgDays": [5, 10]},
                "breakHigh": {"days": [20, 30]}},
        "sell": {"trailingStop": {"drawdown": [8, 12]},
                 "stopLoss": {"percent": [5, 7]}},
    },
    {
        "name": "均线金叉+均线死叉",
        "buy": {"maCross": {"shortPeriod": [5, 10], "longPeriod": [20, 30]}},
        "sell": {"maDeathCross": {"shortPeriod": [5, 10], "longPeriod": [20, 30]},
                 "stopLoss": {"percent": [6, 8]}},
    },
    {
        "name": "早晨之星",
        "buy": {"morningStar": {}},
        "sell": {"takeProfit": {"percent": [10, 15]},
                 "stopLoss": {"percent": [5, 8]}},
    },
    {
        "name": "锤子线反弹",
        "buy": {"hammer": {}},
        "sell": {"trailingStop": {"drawdown": [10, 15]},
                 "stopLoss": {"percent": [5, 6]}},
    },
    {
        "name": "看涨吞没",
        "buy": {"bullishEngulfing": {}},
        "sell": {"takeProfit": {"percent": [12, 18]},
                 "stopLoss": {"percent": [5, 7]}},
    },
    {
        "name": "红三兵",
        "buy": {"threeWhiteSoldiers": {}},
        "sell": {"takeProfit": {"percent": [10, 15]},
                 "stopLoss": {"percent": [5, 8]}},
    },
    {
        "name": "MACD金叉+均线死叉",
        "buy": {"macdCross": {}},
        "sell": {"maDeathCross": {"shortPeriod": [5, 10], "longPeriod": [20, 30]},
                 "stopLoss": {"percent": [6, 8]}},
    },
]


def validate_params(payload: dict) -> None:
    """校验生成请求参数，非法时抛 ValueError。"""
    if payload.get("risk_profile") not in RISK_PROFILES:
        raise ValueError("risk_profile 必须是 conservative/balanced/aggressive 之一")
    count = payload.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 10:
        raise ValueError("count 必须是 1~10 的整数")
    start = str(payload.get("start_date") or "")
    end = str(payload.get("end_date") or "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", start):
        raise ValueError("start_date 格式必须为 YYYY-MM-DD")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", end):
        raise ValueError("end_date 格式必须为 YYYY-MM-DD")
    if end < start:
        raise ValueError("end_date 不能早于 start_date")
    target = payload.get("target_annual_return", 0.0)
    if target is None:
        target = 0.0
    if not isinstance(target, (int, float)) or isinstance(target, bool) or target < 0:
        raise ValueError("target_annual_return 必须是非负数值")
    targets = payload.get("targets") or {}
    scope = targets.get("scope")
    if scope not in ("single", "custom", "market"):
        raise ValueError("targets.scope 必须是 single/custom/market 之一")
    codes = targets.get("codes") or []
    if not isinstance(codes, list):
        raise ValueError("targets.codes 必须是数组")
    if scope in ("single", "custom"):
        if not codes:
            raise ValueError("single/custom 模式必须提供股票代码")
        for c in codes:
            if not re.fullmatch(r"\d{6}", str(c)):
                raise ValueError(f"无效股票代码: {c}")


def _build_config(tpl: dict, variant: int, risk: dict) -> dict:
    """依据模板与轮次变体构建完整策略配置。"""
    cfg = default_config()
    for key, entry in cfg["buy"].items():
        entry["enabled"] = False
    for key, entry in cfg["sell"].items():
        entry["enabled"] = False
    for key, params in tpl["buy"].items():
        entry = cfg["buy"][key]
        entry["enabled"] = True
        for pname, pvals in params.items():
            entry[pname] = pvals[variant % len(pvals)]
    for key, params in tpl["sell"].items():
        entry = cfg["sell"][key]
        entry["enabled"] = True
        for pname, pvals in params.items():
            entry[pname] = pvals[variant % len(pvals)]
    cfg["risk"] = dict(risk)
    return cfg


def generate_strategies(count: int, risk_profile: str) -> list:
    """生成 count 个候选策略配置，保证信号组合两两存在差异。"""
    risk = RISK_PROFILES[risk_profile]
    strategies = []
    for i in range(count):
        tpl = SIGNAL_TEMPLATES[i % len(SIGNAL_TEMPLATES)]
        variant = i // len(SIGNAL_TEMPLATES)
        strategies.append(_build_config(tpl, variant, risk))
    return strategies


def score_strategy(metrics: dict, target_annual_return: float = 0.0) -> float:
    """综合评分：年化 + 目标接近度 + 低回撤 + 胜率 + 盈亏比。"""
    if not metrics or metrics.get("trade_count", 0) == 0:
        return -100.0
    annual = metrics.get("annual_return_pct", 0.0)
    dd = metrics.get("max_drawdown_pct", 0.0)
    win = metrics.get("win_rate_pct", 0.0)
    plr = metrics.get("profit_loss_ratio", 0.0)
    denom = max(abs(target_annual_return), 1.0)
    proximity = max(0.0, 1.0 - abs(annual - target_annual_return) / denom)
    return round(annual + 0.4 * proximity - 0.5 * dd + 0.2 * win + 0.1 * plr, 2)


def _signal_summary(config: dict) -> dict:
    """提取启用的买卖信号名称列表，用于前端展示。"""
    buy_keys = [k for k, v in (config.get("buy") or {}).items() if v.get("enabled")]
    sell_keys = [k for k, v in (config.get("sell") or {}).items() if v.get("enabled")]
    return {"buy": buy_keys, "sell": sell_keys}


def build_report(payload: dict, results: list, scores: dict, ranking: list) -> dict:
    return {
        "request": {
            "targets": payload["targets"],
            "start_date": payload["start_date"],
            "end_date": payload["end_date"],
            "risk_profile": payload["risk_profile"],
            "count": payload["count"],
            "target_annual_return": payload.get("target_annual_return", 0.0),
        },
        "strategies": [
            {
                "index": r["index"],
                "signals": _signal_summary(r["config"]),
                "config": r["config"],
                "metrics": r.get("metrics", {}),
                "equity_curve": r.get("equity_curve", []),
                "trades": r.get("trades", []),
            }
            for r in results
        ],
        "ranking": [{"index": r["index"], "score": scores[r["index"]]} for r in ranking],
        "recommended_index": ranking[0]["index"] if ranking else None,
    }


class _CachedMarket:
    """内存行情包装：复用预取的日线数据，避免重复请求公开接口。"""

    def __init__(self, stock_list: list, bars_map: dict):
        self._stock_list = stock_list
        self._bars_map = bars_map

    def get_stock_list(self):
        return self._stock_list

    def get_daily_bars(self, code, start, end):
        return self._bars_map.get(code)


def run_generation(payload: dict, market) -> dict:
    """完整生成流程：校验 → 取标的与行情 → 生成策略 → 回测 → 评分排序 → 报告。"""
    validate_params(payload)
    start, end = payload["start_date"], payload["end_date"]
    scope = payload["targets"]["scope"]
    codes = [str(c) for c in (payload["targets"].get("codes") or [])]

    if scope == "market":
        stock_list = market.get_stock_list()
    else:
        if scope == "single":
            codes = codes[:1]
        names = market.get_stock_names(codes)
        stock_list = [(c, names.get(c, c)) for c in codes]
    if not stock_list:
        raise DataUnavailableError("标的池为空")

    bars_map = {}
    for code, name in stock_list:
        try:
            df = market.get_daily_bars(code, start, end)
            if df is not None and len(df):
                bars_map[code] = df
        except DataUnavailableError:
            continue
    if not bars_map:
        raise DataUnavailableError(f"区间 {start}~{end} 内无可用真实行情数据")

    all_dates = sorted(set().union(*[set(df["date"]) for df in bars_map.values()]))
    if len(all_dates) < 60:
        raise ValueError(f"回测区间可用交易日不足 60 天（实际 {len(all_dates)} 天）")

    strategies = generate_strategies(payload["count"], payload["risk_profile"])
    cached = _CachedMarket(stock_list, bars_map)
    target = float(payload.get("target_annual_return", 0.0) or 0.0)

    results = []
    for idx, cfg in enumerate(strategies):
        result = backtest.run_backtest(cfg, cached, start, end)
        results.append({"index": idx, "config": cfg, **result})

    scores = {r["index"]: score_strategy(r.get("metrics", {}), target) for r in results}
    ranking = sorted(results, key=lambda r: scores[r["index"]], reverse=True)
    return build_report(payload, results, scores, ranking)
