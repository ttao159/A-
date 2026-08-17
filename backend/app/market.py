"""行情服务：全系统统一使用公开数据 API，禁用 akshare 与合成数据。

MarketDataService 继承 PublicDataService（腾讯 K 线 / 新浪股票列表），
并增加内存 TTL 缓存、磁盘持久化缓存与并发预取，避免全市场扫描与
多次回测时重复请求公开接口。
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime

import pandas as pd

from .public_data import DataUnavailableError, PublicDataService

PREFETCH_WORKERS = 16

FULL_START = "2000-01-01"   # 磁盘缓存拉取的宽区间起点（腾讯接口最多返回 1000 条）


class MarketDataService(PublicDataService):
    """全系统统一行情服务：真实公开数据 + TTL 缓存 + 磁盘缓存 + 并发预取。"""

    KLINE_TTL = 600     # 内存日线缓存 10 分钟
    LIST_TTL = 3600     # 股票列表缓存 1 小时
    PERIOD_TTL = 3600   # 周/月/年 K 线内存缓存 1 小时
    DISK_TTL = 1800     # 磁盘日线缓存 30 分钟
    REALTIME_TTL = 15   # 个股实时行情内存缓存 15 秒

    def __init__(self):
        self._kline_cache = {}
        self._quote_cache = {}
        self._market_cache = None
        self._list_cache = None
        self._list_ts = 0.0
        self._lock = threading.Lock()

    def get_market_quotes(self):
        """全市场实时行情快照，带 15 秒内存缓存。"""
        now = time.time()
        with self._lock:
            hit = self._market_cache
            if hit and now - hit[0] < 15:
                return hit[1]
        result = super().get_market_quotes()
        with self._lock:
            self._market_cache = (now, result)
        return result

    def get_stock_list(self):
        now = time.time()
        if self._list_cache and now - self._list_ts < self.LIST_TTL:
            return self._list_cache
        result = super().get_stock_list()
        self._list_cache = result
        self._list_ts = now
        return result

    # ===== 个股实时行情（短 TTL 缓存） =====
    def get_realtime_quotes(self, codes: list) -> dict:
        """获取个股实时行情，带 15 秒内存缓存；失败时返回空字典（调用方回退日线）。"""
        if not codes:
            return {}
        key = ("realtime", tuple(sorted(codes)))
        now = time.time()
        with self._lock:
            hit = self._quote_cache.get(key)
            if hit and now - hit[0] < self.REALTIME_TTL:
                return hit[1]
        try:
            result = super().get_realtime_quotes(codes)
        except DataUnavailableError:
            result = {}
        with self._lock:
            self._quote_cache[key] = (now, result)
        return result

    # ===== 日线（带磁盘缓存） =====
    def get_daily_bars(self, code: str, start: str, end: str, adjust: str = "qfq"):
        key = (code, start, end, adjust)
        now = time.time()
        with self._lock:
            hit = self._kline_cache.get(key)
            if hit and now - hit[0] < self.KLINE_TTL:
                return hit[1]

        full = self._load_daily_bars(code, adjust)
        if full is None:
            raise DataUnavailableError(f"股票 {code} 无日线数据")
        if len(full) == 0:
            df = full
        else:
            df = full[(full["date"] >= start) & (full["date"] <= end)].reset_index(drop=True)
        with self._lock:
            self._kline_cache[key] = (now, df)
        return df

    def _load_daily_bars(self, code: str, adjust: str):
        """返回完整日线（宽区间），优先磁盘缓存，否则拉取并写磁盘缓存。"""
        df = self._disk_get(code, "day", adjust)
        if df is not None:
            return df
        try:
            df = super().get_daily_bars(code, FULL_START, date.today().isoformat(), adjust)
        except DataUnavailableError:
            return None
        if df is not None and len(df):
            self._disk_put(code, "day", adjust, df)
        return df

    def _disk_get(self, code: str, period: str, adjust: str):
        from io import StringIO

        from .database import SessionLocal
        from .models import DailyBarCache

        db = SessionLocal()
        try:
            row = (db.query(DailyBarCache)
                   .filter_by(code=code, period=period, adjust=adjust).first())
            if not row or not row.updated_at or not row.data_json:
                return None
            if (datetime.utcnow() - row.updated_at).total_seconds() > self.DISK_TTL:
                return None
            df = pd.read_json(StringIO(row.data_json), orient="records", convert_dates=False)
            if df is not None and len(df):
                # 统一为纯日期字符串，避免磁盘缓存读回的 datetime 与实时接口的 str 混用
                df["date"] = df["date"].apply(lambda x: str(x)[:10])
                return df
            return None
        except Exception:
            return None
        finally:
            db.close()

    def _disk_put(self, code: str, period: str, adjust: str, df) -> None:
        from .database import SessionLocal
        from .models import DailyBarCache

        if df is None or len(df) == 0:
            return
        db = SessionLocal()
        try:
            row = (db.query(DailyBarCache)
                   .filter_by(code=code, period=period, adjust=adjust).first())
            payload = df.to_json(orient="records", date_format="iso")
            if row:
                row.data_json = payload
                row.updated_at = datetime.utcnow()
            else:
                db.add(DailyBarCache(code=code, period=period, adjust=adjust,
                                     data_json=payload))
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    # ===== 周期 K 线（周/月/年，仅内存缓存） =====
    def get_kline(self, code: str, period: str, start: str, end: str, adjust: str = "qfq"):
        key = ("kline", period, adjust, code, start, end)
        ttl = self.KLINE_TTL if period == "day" else self.PERIOD_TTL
        now = time.time()
        with self._lock:
            hit = self._kline_cache.get(key)
            if hit and now - hit[0] < ttl:
                return hit[1]
        df = super().get_kline(code, period, start, end, adjust)
        with self._lock:
            self._kline_cache[key] = (now, df)
        return df

    # ===== 并发预取 =====
    def prefetch_daily_bars(self, codes: list, start: str, end: str) -> None:
        """并发预取日线行情填充缓存，单只失败自动跳过。"""
        with ThreadPoolExecutor(max_workers=PREFETCH_WORKERS) as ex:
            list(ex.map(lambda code: self._fetch_and_cache(code, start, end), codes))

    def _fetch_and_cache(self, code: str, start: str, end: str) -> None:
        key = (code, start, end, "qfq")
        with self._lock:
            hit = self._kline_cache.get(key)
            if hit and time.time() - hit[0] < self.KLINE_TTL:
                return
        full = self._load_daily_bars(code, "qfq")
        if full is None or len(full) == 0:
            return
        df = full[(full["date"] >= start) & (full["date"] <= end)].reset_index(drop=True)
        with self._lock:
            self._kline_cache[key] = (time.time(), df)
