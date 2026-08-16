"""参数优化：对策略参数做网格搜索，返回按历史回测收益排序的最优组合。

参数通过点分路径指定（如 buy.maCross.shortPeriod），对每个组合克隆基础
配置并运行回测，最终按总收益率降序返回。组合数受 MAX_COMBOS 限制。

全市场回测单次约 60 秒，为控制耗时，优化默认在全市场股票列表上按固定
随机种子抽样（stock_limit），抽样行情仍走真实公开数据缓存，不引入合成数据。
"""

import itertools
import json
import random

from . import backtest

MAX_COMBOS = 64
DEFAULT_STOCK_LIMIT = 200
_SAMPLE_SEED = 42


class _SubsetMarket:
    """包装原市场服务，仅覆盖股票列表为抽样子集，行情仍走原服务缓存。"""

    def __init__(self, market, stock_list):
        self._market = market
        self._stock_list = stock_list

    def get_stock_list(self):
        return self._stock_list

    def __getattr__(self, name):
        return getattr(self._market, name)


def _set_param(cfg: dict, path: str, value):
    parts = path.split(".")
    node = cfg
    for p in parts[:-1]:
        node = node[p]
    node[parts[-1]] = value


def _combos(param_grid: dict):
    keys = list(param_grid.keys())
    if not keys:
        return [], []
    value_lists = [param_grid[k] for k in keys]
    combos = list(itertools.product(*value_lists))
    if len(combos) > MAX_COMBOS:
        raise ValueError(f"参数组合数 {len(combos)} 超过上限 {MAX_COMBOS}，请减少候选值")
    return combos, keys


def _sample_market(market, stock_limit: int):
    full_list = market.get_stock_list()
    if stock_limit and stock_limit > 0 and len(full_list) > stock_limit:
        rng = random.Random(_SAMPLE_SEED)
        subset = rng.sample(full_list, stock_limit)
        return _SubsetMarket(market, subset), len(subset), len(full_list)
    return market, len(full_list), len(full_list)


def optimize(base_config: dict, market, start: str, end: str, param_grid: dict,
             initial_capital: float = 1_000_000.0, stock_limit: int = DEFAULT_STOCK_LIMIT,
             progress=None):
    """对 param_grid 做网格搜索，返回 (results, sample_info)。

    results 为 [{params, metrics}]，按总收益率降序；sample_info 记录抽样规模。
    """
    combos, keys = _combos(param_grid)
    sub_market, sampled, total_stocks = _sample_market(market, stock_limit)
    results = []
    for i, combo in enumerate(combos):
        cfg = json.loads(json.dumps(base_config, ensure_ascii=False))
        params = {}
        for k, v in zip(keys, combo):
            _set_param(cfg, k, v)
            params[k] = v
        r = backtest.run_backtest(cfg, sub_market, start, end, initial_capital)
        results.append({"params": params, "metrics": r.get("metrics", {})})
        if progress:
            progress("optimize", f"参数组合 {i + 1}/{len(combos)}", i + 1, len(combos))
    results.sort(
        key=lambda x: x["metrics"].get("total_return_pct", float("-inf")),
        reverse=True,
    )
    sample_info = {"sampled_stocks": sampled, "total_stocks": total_stocks}
    return results, sample_info
