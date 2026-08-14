"""公开数据服务单元测试：使用录制的真实 API 响应样本，禁用真实网络请求。"""

import json
import sys
from unittest import mock

import pandas as pd
import pytest

sys.path.insert(0, "..")  # noqa: E402

from app.market import MarketDataService
from app.public_data import DataUnavailableError, PublicDataService, is_main_board

# 腾讯 K 线接口真实响应样本（600519 qfq 日线，行格式 date/open/close/high/low/volume）
TENCENT_KLINE_SAMPLE = {
    "code": 0,
    "msg": "",
    "data": {
        "sh600519": {
            "qfqday": [
                ["2024-11-20", "1439.537", "1441.347", "1450.507", "1427.837", "21345.000"],
                ["2024-11-21", "1440.407", "1441.667", "1445.527", "1428.537", "18262.000"],
                ["2024-11-22", "1437.687", "1404.357", "1444.307", "1404.357", "33436.000"],
            ]
        }
    },
}

# 新浪股票列表真实响应样本
SINA_LIST_SAMPLE = [
    {"symbol": "sh600000", "code": "600000", "name": "浦发银行"},
    {"symbol": "sz000001", "code": "000001", "name": "平安银行"},
    {"symbol": "sz300750", "code": "300750", "name": "宁德时代"},
    {"symbol": "sh688981", "code": "688981", "name": "中芯国际"},
    {"symbol": "bj920000", "code": "920000", "name": "安徽凤凰"},
]

# 腾讯实时行情真实响应样本（GBK 编码的名称字段）
TENCENT_QUOTE_GBK = (
    'v_sh600519="1~贵州茅台~600519~1341.99~1355.29";'
    'v_sz000001="51~平安银行~000001~11.11~11.25";'
)


class TestIsMainBoard:
    def test_sh_main_board(self):
        assert is_main_board("600519") is True
        assert is_main_board("601318") is True

    def test_sz_main_board(self):
        assert is_main_board("000001") is True
        assert is_main_board("002594") is True

    def test_growth_board_excluded(self):
        assert is_main_board("300750") is False
        assert is_main_board("301236") is False

    def test_star_board_excluded(self):
        assert is_main_board("688981") is False
        assert is_main_board("689009") is False

    def test_beijing_board_excluded(self):
        assert is_main_board("920000") is False
        assert is_main_board("430047") is False

    def test_invalid_code(self):
        assert is_main_board("60051") is False
        assert is_main_board("abc") is False


class TestGetDailyBars:
    def test_parses_tencent_kline(self):
        with mock.patch("app.public_data._http_get_json", return_value=TENCENT_KLINE_SAMPLE):
            df = PublicDataService().get_daily_bars("600519", "2024-11-20", "2024-12-31")
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]
        assert len(df) == 3
        assert df.iloc[0]["date"] == "2024-11-20"
        assert df.iloc[0]["open"] == 1439.537
        assert df.iloc[0]["close"] == 1441.347
        assert df.iloc[0]["high"] == 1450.507
        assert df.iloc[0]["low"] == 1427.837
        assert df.iloc[0]["volume"] == 21345.0

    def test_empty_data_raises(self):
        with mock.patch("app.public_data._http_get_json", return_value={"data": {}}):
            with pytest.raises(DataUnavailableError):
                PublicDataService().get_daily_bars("600519", "2024-01-01", "2024-12-31")

    def test_no_kline_rows_raises(self):
        with mock.patch("app.public_data._http_get_json",
                        return_value={"data": {"sh600519": {"qfqday": []}}}):
            with pytest.raises(DataUnavailableError):
                PublicDataService().get_daily_bars("600519", "2024-01-01", "2024-12-31")

    def test_growth_board_code_rejected(self):
        with pytest.raises(DataUnavailableError):
            PublicDataService().get_daily_bars("300750", "2024-01-01", "2024-12-31")

    def test_bars_filtered_by_start_date(self):
        with mock.patch("app.public_data._http_get_json", return_value=TENCENT_KLINE_SAMPLE):
            df = PublicDataService().get_daily_bars("600519", "2024-11-21", "2024-12-31")
        assert df["date"].iloc[0] == "2024-11-21"


class TestGetStockList:
    def test_filters_to_main_board(self):
        with mock.patch("app.public_data._http_get_json", return_value=SINA_LIST_SAMPLE):
            stocks = PublicDataService().get_stock_list()
        assert stocks == [("600000", "浦发银行"), ("000001", "平安银行")]

    def test_empty_list_raises(self):
        with mock.patch("app.public_data._http_get_json", return_value=[]):
            with pytest.raises(DataUnavailableError):
                PublicDataService().get_stock_list()

    def test_pagination_pages_until_short_page(self):
        def fake_fetch(url):
            if "page=1" in url:
                return SINA_LIST_SAMPLE
            return []

        with mock.patch("app.public_data._http_get_json", side_effect=fake_fetch):
            stocks = PublicDataService().get_stock_list()
        assert ("600000", "浦发银行") in stocks


class TestGetStockNames:
    def test_parses_gbk_quote(self):
        class FakeResp:
            status = 200

            def read(self):
                return TENCENT_QUOTE_GBK.encode("gbk")

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        with mock.patch("app.public_data.urllib.request.urlopen", return_value=FakeResp()):
            names = PublicDataService().get_stock_names(["600519", "000001"])
        assert names == {"600519": "贵州茅台", "000001": "平安银行"}

    def test_empty_codes(self):
        assert PublicDataService().get_stock_names([]) == {}

    def test_failure_falls_back_to_empty(self):
        with mock.patch("app.public_data.urllib.request.urlopen", side_effect=Exception("net")):
            assert PublicDataService().get_stock_names(["600519"]) == {}


class TestMarketDataServiceCache:
    def test_daily_bars_cached_within_ttl(self):
        svc = MarketDataService()
        with mock.patch.object(PublicDataService, "get_daily_bars",
                               return_value=pd.DataFrame()) as spy:
            svc.get_daily_bars("600519", "2024-01-01", "2024-12-31")
            svc.get_daily_bars("600519", "2024-01-01", "2024-12-31")
            assert spy.call_count == 1

    def test_daily_bars_not_cached_across_dates(self):
        svc = MarketDataService()
        with mock.patch.object(PublicDataService, "get_daily_bars",
                               return_value=pd.DataFrame()) as spy:
            svc.get_daily_bars("600519", "2024-01-01", "2024-12-31")
            svc.get_daily_bars("600519", "2023-01-01", "2023-12-31")
            assert spy.call_count == 2

    def test_cache_expires_after_ttl(self):
        svc = MarketDataService()
        svc.KLINE_TTL = 0
        with mock.patch.object(PublicDataService, "get_daily_bars",
                               return_value=pd.DataFrame()) as spy:
            svc.get_daily_bars("600519", "2024-01-01", "2024-12-31")
            svc.get_daily_bars("600519", "2024-01-01", "2024-12-31")
            assert spy.call_count == 2

    def test_stock_list_cached(self):
        svc = MarketDataService()
        with mock.patch.object(PublicDataService, "get_stock_list",
                               return_value=[("600519", "贵州茅台")]) as spy:
            svc.get_stock_list()
            svc.get_stock_list()
            assert spy.call_count == 1
