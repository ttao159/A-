"""公开数据服务：仅通过公开 HTTP API 获取真实行情，禁用合成数据。

- 日线行情：腾讯 ifzq K 线接口（前复权）
- 全市场股票列表：新浪行情接口
- 股票名称：腾讯实时行情接口（批量查询）
"""

import json
import re
import urllib.request

import pandas as pd

TIMEOUT = 10

TENCENT_KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
TENCENT_QUOTE_URL = "https://qt.gtimg.cn/q="
SINA_LIST_URL = ("https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                 "Market_Center.getHQNodeData")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


class DataUnavailableError(Exception):
    """行情数据源不可用或返回空数据。"""


def _http_get_text(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            if resp.status != 200:
                raise DataUnavailableError(f"公开行情接口返回 HTTP {resp.status}")
            return resp.read().decode("utf-8", errors="replace")
    except DataUnavailableError:
        raise
    except Exception as exc:
        raise DataUnavailableError(f"请求公开行情接口失败: {exc}") from exc


def _http_get_json(url: str):
    raw = _http_get_text(url)
    if not raw or not raw.strip():
        raise DataUnavailableError("公开行情接口返回空响应")
    try:
        return json.loads(raw)
    except Exception as exc:
        raise DataUnavailableError(f"公开行情接口响应解析失败: {exc}") from exc


def _tencent_symbol(code: str) -> str:
    """股票代码转腾讯格式（sh/sz 前缀），仅支持沪深主板。"""
    if not re.fullmatch(r"\d{6}", code or ""):
        raise DataUnavailableError(f"无效的股票代码: {code}")
    if code.startswith("6"):
        return "sh" + code
    if code.startswith("0"):
        return "sz" + code
    raise DataUnavailableError(f"不支持的股票代码（仅沪深主板）: {code}")


def is_main_board(code: str) -> bool:
    """判断是否沪深主板（排除创业板 300/301、科创板 688/689、北交所）。"""
    if re.fullmatch(r"\d{6}", code or "") is None:
        return False
    return code.startswith(("60", "00"))


class PublicDataService:
    """公开数据服务：真实行情，任何失败路径抛 DataUnavailableError。"""

    def get_stock_list(self) -> list:
        """返回沪深主板 [(code, name)]，分页拉取新浪全 A 列表并过滤。"""
        result = []
        page = 1
        while page <= 200:
            url = (f"{SINA_LIST_URL}?page={page}&num=100&sort=symbol&asc=1&node=hs_a")
            data = _http_get_json(url)
            if not isinstance(data, list) or not data:
                break
            for item in data:
                if not isinstance(item, dict):
                    continue
                code = str(item.get("code") or "")
                name = str(item.get("name") or "")
                if is_main_board(code):
                    result.append((code, name))
            if len(data) < 100:
                break
            page += 1
        if not result:
            raise DataUnavailableError("未从公开接口获取到有效的沪深主板股票列表")
        return result

    def get_stock_names(self, codes: list) -> dict:
        """批量查询股票真实名称，返回 {code: name}；失败时回退为代码本身。"""
        if not codes:
            return {}
        names = {}
        for i in range(0, len(codes), 50):
            batch = codes[i:i + 50]
            syms = ",".join(_tencent_symbol(c) for c in batch)
            try:
                req = urllib.request.Request(TENCENT_QUOTE_URL + syms, headers=UA)
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    if resp.status != 200:
                        continue
                    raw = resp.read().decode("gbk", errors="replace")
            except Exception:
                continue
            for line in raw.split(";"):
                line = line.strip()
                if not line.startswith("v_"):
                    continue
                m = re.search(r'="([^"]*)"', line)
                if not m:
                    continue
                fields = m.group(1).split("~")
                if len(fields) < 3:
                    continue
                code = fields[2]
                names[code] = fields[1]
        return names

    def get_daily_bars(self, code: str, start: str, end: str) -> pd.DataFrame:
        """返回真实前复权日线：date/open/high/low/close/volume，按日期升序。"""
        sym = _tencent_symbol(code)
        url = (f"{TENCENT_KLINE_URL}?param={sym},day,{start},{end},1000,qfq")
        data = _http_get_json(url)
        stock = data.get("data", {}).get(sym, {}) if isinstance(data, dict) else {}
        rows = stock.get("qfqday") or stock.get("day")
        if not isinstance(rows, list) or not rows:
            raise DataUnavailableError(f"股票 {code} 无日线数据（{start}~{end}）")

        parsed = []
        for row in rows:
            if not isinstance(row, list) or len(row) < 6:
                continue
            parsed.append({
                "date": str(row[0]),
                "open": float(row[1]),
                "close": float(row[2]),
                "high": float(row[3]),
                "low": float(row[4]),
                "volume": float(row[5]),
            })
        if not parsed:
            raise DataUnavailableError(f"股票 {code} 日线数据解析失败")

        df = pd.DataFrame(parsed, columns=["date", "open", "high", "low", "close", "volume"])
        df = df[df["date"] >= start].reset_index(drop=True)
        return df.sort_values("date").reset_index(drop=True)
