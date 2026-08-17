"""行业分类服务：从新浪公开接口构建 股票→行业 映射并磁盘缓存。

新浪行业板块列表（newSinaHy.php）给出板块节点与成分股数量，随后按板块
分页拉取成分股，反向构建 {code: industry} 映射。构建在后台线程进行，
未就绪时调用方回退个股级归因。
"""

import json
import threading
import time
import urllib.request
from datetime import datetime, timedelta

from .database import SessionLocal
from .models import IndustryCache
from .public_data import DataUnavailableError, TIMEOUT, UA, is_main_board

SINA_HY_URL = "https://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php"
SINA_NODE_URL = ("https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                 "Market_Center.getHQNodeData")

REBUILD_TTL_SECONDS = 7 * 24 * 3600  # 行业分类 7 天重建一次


def _http_get_text(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        if resp.status != 200:
            raise DataUnavailableError(f"行业接口返回 HTTP {resp.status}")
        return resp.read().decode("utf-8", errors="replace")


def _parse_sina_hy(raw: str) -> dict:
    """解析 newSinaHy.php：返回 {板块节点: (成分股数量, 板块名)}。"""
    idx = raw.find("{")
    end = raw.rfind("}")
    if idx < 0 or end < idx:
        raise DataUnavailableError("行业板块列表解析失败")
    try:
        data = json.loads(raw[idx:end + 1])
    except Exception as exc:
        raise DataUnavailableError(f"行业板块列表 JSON 解析失败: {exc}")
    out = {}
    for node, meta in (data or {}).items():
        parts = str(meta).split(",")
        if len(parts) >= 2:
            try:
                out[node] = (int(parts[0]), parts[1])
            except ValueError:
                continue
    return out


def _fetch_node_stocks(node: str, count: int) -> list:
    """拉取某行业板块成分股 [(code, name)]，返回空列表表示失败。"""
    stocks = []
    page = 1
    while page <= count // 100 + 2:
        url = f"{SINA_NODE_URL}?page={page}&num=100&sort=symbol&asc=1&node={node}"
        try:
            raw = _http_get_text(url)
            data = json.loads(raw) if raw and raw.strip() else []
        except Exception:
            break
        if not isinstance(data, list) or not data:
            break
        for item in data:
            if isinstance(item, dict) and item.get("code"):
                stocks.append((str(item["code"]), str(item.get("name") or "")))
        if len(data) < 100:
            break
        page += 1
    return stocks


class IndustryMapService:
    """股票→行业映射，DB 缓存 + 内存缓存，后台重建。"""

    def __init__(self):
        self._cache: dict = {}
        self._loaded_ts = 0.0
        self._loading = False
        self._lock = threading.Lock()

    def _load_from_db(self) -> dict:
        db = SessionLocal()
        try:
            rows = db.query(IndustryCache).all()
            if not rows:
                return {}
            newest = max((r.updated_at or datetime.utcnow()) for r in rows)
            if datetime.utcnow() - newest > timedelta(seconds=REBUILD_TTL_SECONDS):
                return {}
            return {r.code: r.industry for r in rows}
        finally:
            db.close()

    def _upsert(self, mapping: dict) -> None:
        db = SessionLocal()
        try:
            existing = {r.code: r for r in db.query(IndustryCache).all()}
            now = datetime.utcnow()
            for code, industry in mapping.items():
                row = existing.get(code)
                if row:
                    row.industry = industry
                    row.updated_at = now
                else:
                    db.add(IndustryCache(code=code, industry=industry, updated_at=now))
            db.commit()
        finally:
            db.close()

    def _build(self) -> None:
        try:
            hy = _parse_sina_hy(_http_get_text(SINA_HY_URL))
            mapping: dict = {}
            for node, (count, industry) in hy.items():
                for code, _name in _fetch_node_stocks(node, count):
                    if is_main_board(code):
                        mapping[code] = industry
            if not mapping:
                return
            self._upsert(mapping)
            with self._lock:
                self._cache = mapping
                self._loaded_ts = time.time()
        except Exception:
            # 构建失败保留旧缓存，下次触发时重试
            pass
        finally:
            with self._lock:
                self._loading = False

    def _ensure_build(self) -> None:
        with self._lock:
            if self._loading:
                return
            if self._cache and time.time() - self._loaded_ts < REBUILD_TTL_SECONDS:
                return
            self._loading = True
        threading.Thread(target=self._build, daemon=True).start()

    def get_industry_map(self) -> dict:
        """返回 {code: industry}；首次调用返回空并触发后台构建。"""
        if self._cache:
            self._ensure_build()
            return self._cache
        with self._lock:
            if not self._cache:
                loaded = self._load_from_db()
                if loaded:
                    self._cache = loaded
                    self._loaded_ts = time.time()
        self._ensure_build()
        return self._cache


industry_map = IndustryMapService()
