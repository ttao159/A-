"""行情服务：全系统统一使用公开数据 API，禁用 akshare 与合成数据。

MarketDataService 继承 PublicDataService（腾讯 K 线 / 新浪股票列表），
并增加内存 TTL 缓存与并发预取，避免全市场扫描与多次回测时重复请求公开接口。
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from .public_data import DataUnavailableError, PublicDataService

PREFETCH_WORKERS = 16


class MarketDataService(PublicDataService):
    """全系统统一行情服务：真实公开数据 + TTL 缓存 + 并发预取。"""

    KLINE_TTL = 600    # 日线缓存 10 分钟
    LIST_TTL = 3600    # 股票列表缓存 1 小时

    def __init__(self):
        self._kline_cache = {}
        self._list_cache = None
        self._list_ts = 0.0
        self._lock = threading.Lock()

    def get_stock_list(self):
        now = time.time()
        if self._list_cache and now - self._list_ts < self.LIST_TTL:
            return self._list_cache
        result = super().get_stock_list()
        self._list_cache = result
        self._list_ts = now
        return result

    def get_daily_bars(self, code: str, start: str, end: str):
        key = (code, start, end)
        now = time.time()
        with self._lock:
            hit = self._kline_cache.get(key)
            if hit and now - hit[0] < self.KLINE_TTL:
                return hit[1]
        df = super().get_daily_bars(code, start, end)
        with self._lock:
            self._kline_cache[key] = (now, df)
        return df

    def prefetch_daily_bars(self, codes: list, start: str, end: str) -> None:
        """并发预取日线行情填充缓存，单只失败自动跳过。"""
        with ThreadPoolExecutor(max_workers=PREFETCH_WORKERS) as ex:
            list(ex.map(lambda code: self._fetch_and_cache(code, start, end), codes))

    def _fetch_and_cache(self, code: str, start: str, end: str) -> None:
        key = (code, start, end)
        with self._lock:
            hit = self._kline_cache.get(key)
            if hit and time.time() - hit[0] < self.KLINE_TTL:
                return
        try:
            df = super().get_daily_bars(code, start, end)
        except DataUnavailableError:
            return
        with self._lock:
            self._kline_cache[key] = (time.time(), df)
