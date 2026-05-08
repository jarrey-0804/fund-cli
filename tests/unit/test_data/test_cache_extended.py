"""扩展缓存功能测试"""

import pandas as pd

from fund_cli.data.cache import DataCache


class TestHoldingsCache:
    def test_set_and_get_holdings(self, temp_cache_dir):
        cache = DataCache(cache_dir=str(temp_cache_dir))
        df = pd.DataFrame({"stock_code": ["600519"], "weight": [9.5]})
        cache.set_fund_holdings("000001", "2024-06-30", df)
        result = cache.get_fund_holdings("000001", "2024-06-30")
        assert result is not None
        assert len(result) == 1

    def test_holdings_cache_miss(self, temp_cache_dir):
        cache = DataCache(cache_dir=str(temp_cache_dir))
        result = cache.get_fund_holdings("000001", "2024-06-30")
        assert result is None


class TestManagerCache:
    def test_set_and_get_manager(self, temp_cache_dir):
        cache = DataCache(cache_dir=str(temp_cache_dir))
        info = {"name": "张三", "fund_code": "000001"}
        cache.set_fund_manager("000001", info)
        result = cache.get_fund_manager("000001")
        assert result is not None
        assert result["name"] == "张三"

    def test_manager_cache_miss(self, temp_cache_dir):
        cache = DataCache(cache_dir=str(temp_cache_dir))
        result = cache.get_fund_manager("999999")
        assert result is None
