# -*- coding: utf-8 -*-
"""
数据源适配器基类测试

测试覆盖：
- DataSourceAdapter 基类
- 异常类
- DataCache 类方法
"""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from fund_cli.data.base import (
    DataNotFoundError,
    DataSourceAdapter,
    DataSourceError,
    NetworkError,
)


# =============================================================================
# 异常类测试
# =============================================================================


class TestExceptions:
    """测试异常类"""

    def test_data_source_error_message(self):
        """测试 DataSourceError 消息"""
        error = DataSourceError("测试错误")
        assert str(error) == "测试错误"

    def test_data_source_error_inheritance(self):
        """测试 DataSourceError 继承"""
        error = DataSourceError("错误")
        assert isinstance(error, Exception)

    def test_data_not_found_error_message(self):
        """测试 DataNotFoundError 消息"""
        error = DataNotFoundError("数据未找到")
        assert str(error) == "数据未找到"

    def test_data_not_found_error_inheritance(self):
        """测试 DataNotFoundError 继承"""
        error = DataNotFoundError("错误")
        assert isinstance(error, Exception)

    def test_network_error_message(self):
        """测试 NetworkError 消息"""
        error = NetworkError("网络错误")
        assert str(error) == "网络错误"

    def test_network_error_inheritance(self):
        """测试 NetworkError 继承"""
        error = NetworkError("错误")
        assert isinstance(error, Exception)

    def test_raise_data_source_error(self):
        """测试抛出 DataSourceError"""
        with pytest.raises(DataSourceError, match="测试错误"):
            raise DataSourceError("测试错误")

    def test_raise_data_not_found_error(self):
        """测试抛出 DataNotFoundError"""
        with pytest.raises(DataNotFoundError, match="数据不存在"):
            raise DataNotFoundError("数据不存在")

    def test_raise_network_error(self):
        """测试抛出 NetworkError"""
        with pytest.raises(NetworkError, match="连接失败"):
            raise NetworkError("连接失败")

    def test_catch_data_source_error(self):
        """测试捕获 DataSourceError"""
        try:
            raise DataSourceError("错误")
        except DataSourceError as e:
            assert str(e) == "错误"

    def test_catch_data_not_found_as_data_source_error(self):
        """测试 DataNotFoundError 可以作为 Exception 捕获"""
        try:
            raise DataNotFoundError("未找到")
        except Exception as e:
            assert isinstance(e, DataNotFoundError)


# =============================================================================
# DataSourceAdapter 基类测试
# =============================================================================


class TestDataSourceAdapterBase:
    """测试 DataSourceAdapter 基类"""

    def test_cannot_instantiate_abstract_class(self):
        """测试不能直接实例化抽象类"""
        with pytest.raises(TypeError):
            DataSourceAdapter("test")

    def test_subclass_must_implement_is_available(self):
        """测试子类必须实现 is_available 方法"""

        class IncompleteAdapter(DataSourceAdapter):
            def is_available(self):
                pass  # 只实现一个方法

        # 仍然不能实例化，因为还有很多抽象方法未实现
        with pytest.raises(TypeError):
            IncompleteAdapter("test")

    def test_adapter_name_property(self):
        """测试适配器 name 属性"""

        class TestAdapter(DataSourceAdapter):
            def is_available(self):
                return True

            # 实现所有抽象方法
            def get_fund_info(self, fund_code):
                return {}

            def get_all_fund_names(self):
                return pd.DataFrame()

            def get_fund_info_ths(self, fund_code):
                return {}

            def get_index_fund_info(self, category="全部", indicator="全部"):
                return pd.DataFrame()

            def get_fund_overview(self, fund_code):
                return {}

            def get_fund_purchase_status(self):
                return pd.DataFrame()

            def get_fund_nav(self, fund_code, start_date=None, end_date=None):
                return pd.DataFrame()

            def get_fund_daily_nav(self):
                return pd.DataFrame()

            def get_etf_spot(self):
                return pd.DataFrame()

            def get_fund_category_spot(self, category="", date=None):
                return pd.DataFrame()

            def get_etf_spot_ths(self, date=None):
                return pd.DataFrame()

            def get_lof_spot(self):
                return pd.DataFrame()

            def get_etf_hist(self, fund_code, period="daily", start_date=None, end_date=None):
                return pd.DataFrame()

            def get_lof_hist(self, fund_code, period="daily", start_date=None, end_date=None):
                return pd.DataFrame()

            def get_etf_minute(self, fund_code, period="1", start_date=None, end_date=None):
                return pd.DataFrame()

            def get_lof_minute(self, fund_code, period="1", start_date=None, end_date=None):
                return pd.DataFrame()

            def get_fund_holdings(self, fund_code, report_date=None):
                return pd.DataFrame()

            def get_fund_bond_holdings(self, fund_code, year=None):
                return pd.DataFrame()

            def get_fund_industry_allocation(self, fund_code, year=None):
                return pd.DataFrame()

            def get_fund_portfolio_change(self, fund_code, indicator="累计买入", year=None):
                return pd.DataFrame()

            def get_all_fund_managers(self):
                return pd.DataFrame()

            def search_funds(self, fund_type=None, company=None, min_scale=None, max_scale=None, keyword=None, limit=100):
                return pd.DataFrame()

            def get_fund_list(self, fund_type=None):
                return pd.DataFrame()

            def get_benchmark_nav(self, benchmark_code, start_date=None, end_date=None):
                return pd.DataFrame()

            def get_fund_fee(self, fund_code):
                return {}

            def get_fund_company_aum(self):
                return pd.DataFrame()

            def get_fund_aum_trend(self):
                return pd.DataFrame()

            def get_fund_company_aum_history(self, year=None):
                return pd.DataFrame()

            def get_fund_scale_change(self):
                return pd.DataFrame()

            def get_fund_holder_structure(self):
                return pd.DataFrame()

            def get_fund_ratings(self):
                return pd.DataFrame()

            def get_fund_rating_sh(self, date=None):
                return pd.DataFrame()

            def get_fund_rating_zs(self, date=None):
                return pd.DataFrame()

            def get_fund_rating_ja(self, date=None):
                return pd.DataFrame()

            def get_fund_dividends(self, year=None, fund_type="", page=-1):
                return pd.DataFrame()

            def get_fund_splits(self, year=None, fund_type="", page=-1):
                return pd.DataFrame()

            def get_fund_dividend_rank(self):
                return pd.DataFrame()

            def get_fund_rank_by_type(self, fund_type="全部"):
                return pd.DataFrame()

            def get_exchange_fund_rank(self):
                return pd.DataFrame()

            def get_money_fund_rank(self):
                return pd.DataFrame()

            def get_lcx_fund_rank(self):
                return pd.DataFrame()

            def get_hk_fund_rank(self):
                return pd.DataFrame()

            def get_fund_achievement(self, fund_code):
                return pd.DataFrame()

            def get_fund_risk_analysis(self, fund_code):
                return pd.DataFrame()

            def get_fund_profit_probability(self, fund_code):
                return pd.DataFrame()

            def get_fund_asset_allocation(self, fund_code, date=None):
                return pd.DataFrame()

            def get_index_spot_em(self, category="沪深重要指数"):
                return pd.DataFrame()

            def get_index_spot_sina(self):
                return pd.DataFrame()

            def get_index_daily_tx(self, code, start=None, end=None):
                return pd.DataFrame()

            def get_index_daily_em(self, code, start=None, end=None):
                return pd.DataFrame()

            def get_index_hist(self, code, period="daily", start=None, end=None):
                return pd.DataFrame()

            def get_index_minute(self, code, period="1", start=None, end=None):
                return pd.DataFrame()

            def get_macro_leverage_ratio(self):
                return pd.DataFrame()

            def get_enterprise_price_index(self):
                return pd.DataFrame()

            def get_fdi_data(self):
                return pd.DataFrame()

            def get_lpr_data(self):
                return pd.DataFrame()

            def get_urban_unemployment(self):
                return pd.DataFrame()

            def get_social_financing(self):
                return pd.DataFrame()

            def get_gdp_yearly(self):
                return pd.DataFrame()

            def get_gdp_quarterly(self):
                return pd.DataFrame()

            def get_cpi_yearly(self):
                return pd.DataFrame()

            def get_cpi_monthly(self):
                return pd.DataFrame()

            def get_ppi_yearly(self):
                return pd.DataFrame()

            def get_ppi_monthly(self):
                return pd.DataFrame()

            def get_exports_yearly(self):
                return pd.DataFrame()

            def get_imports_yearly(self):
                return pd.DataFrame()

            def get_trade_balance(self):
                return pd.DataFrame()

            def get_industrial_production(self):
                return pd.DataFrame()

            def get_pmi_official(self):
                return pd.DataFrame()

            def get_pmi_caixin(self):
                return pd.DataFrame()

            def get_services_pmi(self):
                return pd.DataFrame()

            def get_non_manufacturing_pmi(self):
                return pd.DataFrame()

            def get_m2_yearly(self):
                return pd.DataFrame()

            def get_new_loan(self):
                return pd.DataFrame()

            def get_china_interest_rate(self):
                return pd.DataFrame()

            def get_usa_interest_rate(self):
                return pd.DataFrame()

            def get_euro_interest_rate(self):
                return pd.DataFrame()

            def get_japan_interest_rate(self):
                return pd.DataFrame()

            def get_uk_interest_rate(self):
                return pd.DataFrame()

            def get_shibor(self):
                return pd.DataFrame()

            def get_shibor_lpr(self):
                return pd.DataFrame()

            def get_hibor(self):
                return pd.DataFrame()

            def get_industry_boards(self):
                return pd.DataFrame()

            def get_industry_board_hist(self, code, period="daily", start=None, end=None):
                return pd.DataFrame()

            def get_concept_boards(self):
                return pd.DataFrame()

            def get_concept_board_hist(self, code, period="daily", start=None, end=None):
                return pd.DataFrame()

            def get_sector_fund_flow(self, period="今日"):
                return pd.DataFrame()

            def get_china_us_bond_yield(self):
                return pd.DataFrame()

            def get_bond_yield_curve(self, bond_type="国债", period="daily", start_date=None, end_date=None):
                return pd.DataFrame()

            def get_bond_spot_quote(self):
                return pd.DataFrame()

            def get_convertible_bonds(self):
                return pd.DataFrame()

            def get_convertible_bond_detail(self, code):
                return {}

            def get_bond_spot(self, code):
                return pd.DataFrame()

            def get_bond_hist(self, code, period="daily", start_date=None, end_date=None):
                return pd.DataFrame()

            def get_a_share_valuation(self):
                return pd.DataFrame()

            def get_stock_valuation_lg(self, code):
                return pd.DataFrame()

            def get_index_valuation(self, code, indicator="pe"):
                return pd.DataFrame()

            def get_market_pe_lg(self, code):
                return pd.DataFrame()

            def get_market_pb_lg(self, code):
                return pd.DataFrame()

            def get_market_fund_flow(self):
                return pd.DataFrame()

            def get_stock_fund_flow(self, code, market="sh"):
                return pd.DataFrame()

            def get_north_fund_flow(self, market="北向资金"):
                return pd.DataFrame()

            def get_retail_sales_yearly(self):
                return pd.DataFrame()

            def get_fixed_asset_investment(self):
                return pd.DataFrame()

            def get_fund_manager(self, fund_code):
                return {}

            def get_fund_rating(self, fund_code):
                return None

            def batch_get_fund_nav(self, fund_codes, start_date=None, end_date=None):
                return {}

        adapter = TestAdapter("test_adapter")
        assert adapter.name == "test_adapter"

    def test_adapter_repr(self):
        """测试适配器 __repr__ 方法"""

        class TestAdapter(DataSourceAdapter):
            def is_available(self):
                return True

            # 省略其他抽象方法的实现...
            def get_fund_info(self, fund_code):
                return {}

            def get_all_fund_names(self):
                return pd.DataFrame()

            def get_fund_info_ths(self, fund_code):
                return {}

            def get_index_fund_info(self, category="全部", indicator="全部"):
                return pd.DataFrame()

            def get_fund_overview(self, fund_code):
                return {}

            def get_fund_purchase_status(self):
                return pd.DataFrame()

            def get_fund_nav(self, fund_code, start_date=None, end_date=None):
                return pd.DataFrame()

            def get_fund_daily_nav(self):
                return pd.DataFrame()

            def get_etf_spot(self):
                return pd.DataFrame()

            def get_fund_category_spot(self, category="", date=None):
                return pd.DataFrame()

            def get_etf_spot_ths(self, date=None):
                return pd.DataFrame()

            def get_lof_spot(self):
                return pd.DataFrame()

            def get_etf_hist(self, fund_code, period="daily", start_date=None, end_date=None):
                return pd.DataFrame()

            def get_lof_hist(self, fund_code, period="daily", start_date=None, end_date=None):
                return pd.DataFrame()

            def get_etf_minute(self, fund_code, period="1", start_date=None, end_date=None):
                return pd.DataFrame()

            def get_lof_minute(self, fund_code, period="1", start_date=None, end_date=None):
                return pd.DataFrame()

            def get_fund_holdings(self, fund_code, report_date=None):
                return pd.DataFrame()

            def get_fund_bond_holdings(self, fund_code, year=None):
                return pd.DataFrame()

            def get_fund_industry_allocation(self, fund_code, year=None):
                return pd.DataFrame()

            def get_fund_portfolio_change(self, fund_code, indicator="累计买入", year=None):
                return pd.DataFrame()

            def get_all_fund_managers(self):
                return pd.DataFrame()

            def search_funds(self, fund_type=None, company=None, min_scale=None, max_scale=None, keyword=None, limit=100):
                return pd.DataFrame()

            def get_fund_list(self, fund_type=None):
                return pd.DataFrame()

            def get_benchmark_nav(self, benchmark_code, start_date=None, end_date=None):
                return pd.DataFrame()

            def get_fund_fee(self, fund_code):
                return {}

            def get_fund_company_aum(self):
                return pd.DataFrame()

            def get_fund_aum_trend(self):
                return pd.DataFrame()

            def get_fund_company_aum_history(self, year=None):
                return pd.DataFrame()

            def get_fund_scale_change(self):
                return pd.DataFrame()

            def get_fund_holder_structure(self):
                return pd.DataFrame()

            def get_fund_ratings(self):
                return pd.DataFrame()

            def get_fund_rating_sh(self, date=None):
                return pd.DataFrame()

            def get_fund_rating_zs(self, date=None):
                return pd.DataFrame()

            def get_fund_rating_ja(self, date=None):
                return pd.DataFrame()

            def get_fund_dividends(self, year=None, fund_type="", page=-1):
                return pd.DataFrame()

            def get_fund_splits(self, year=None, fund_type="", page=-1):
                return pd.DataFrame()

            def get_fund_dividend_rank(self):
                return pd.DataFrame()

            def get_fund_rank_by_type(self, fund_type="全部"):
                return pd.DataFrame()

            def get_exchange_fund_rank(self):
                return pd.DataFrame()

            def get_money_fund_rank(self):
                return pd.DataFrame()

            def get_lcx_fund_rank(self):
                return pd.DataFrame()

            def get_hk_fund_rank(self):
                return pd.DataFrame()

            def get_fund_achievement(self, fund_code):
                return pd.DataFrame()

            def get_fund_risk_analysis(self, fund_code):
                return pd.DataFrame()

            def get_fund_profit_probability(self, fund_code):
                return pd.DataFrame()

            def get_fund_asset_allocation(self, fund_code, date=None):
                return pd.DataFrame()

            def get_index_spot_em(self, category="沪深重要指数"):
                return pd.DataFrame()

            def get_index_spot_sina(self):
                return pd.DataFrame()

            def get_index_daily_tx(self, code, start=None, end=None):
                return pd.DataFrame()

            def get_index_daily_em(self, code, start=None, end=None):
                return pd.DataFrame()

            def get_index_hist(self, code, period="daily", start=None, end=None):
                return pd.DataFrame()

            def get_index_minute(self, code, period="1", start=None, end=None):
                return pd.DataFrame()

            def get_macro_leverage_ratio(self):
                return pd.DataFrame()

            def get_enterprise_price_index(self):
                return pd.DataFrame()

            def get_fdi_data(self):
                return pd.DataFrame()

            def get_lpr_data(self):
                return pd.DataFrame()

            def get_urban_unemployment(self):
                return pd.DataFrame()

            def get_social_financing(self):
                return pd.DataFrame()

            def get_gdp_yearly(self):
                return pd.DataFrame()

            def get_gdp_quarterly(self):
                return pd.DataFrame()

            def get_cpi_yearly(self):
                return pd.DataFrame()

            def get_cpi_monthly(self):
                return pd.DataFrame()

            def get_ppi_yearly(self):
                return pd.DataFrame()

            def get_ppi_monthly(self):
                return pd.DataFrame()

            def get_exports_yearly(self):
                return pd.DataFrame()

            def get_imports_yearly(self):
                return pd.DataFrame()

            def get_trade_balance(self):
                return pd.DataFrame()

            def get_industrial_production(self):
                return pd.DataFrame()

            def get_pmi_official(self):
                return pd.DataFrame()

            def get_pmi_caixin(self):
                return pd.DataFrame()

            def get_services_pmi(self):
                return pd.DataFrame()

            def get_non_manufacturing_pmi(self):
                return pd.DataFrame()

            def get_m2_yearly(self):
                return pd.DataFrame()

            def get_new_loan(self):
                return pd.DataFrame()

            def get_china_interest_rate(self):
                return pd.DataFrame()

            def get_usa_interest_rate(self):
                return pd.DataFrame()

            def get_euro_interest_rate(self):
                return pd.DataFrame()

            def get_japan_interest_rate(self):
                return pd.DataFrame()

            def get_uk_interest_rate(self):
                return pd.DataFrame()

            def get_shibor(self):
                return pd.DataFrame()

            def get_shibor_lpr(self):
                return pd.DataFrame()

            def get_hibor(self):
                return pd.DataFrame()

            def get_industry_boards(self):
                return pd.DataFrame()

            def get_industry_board_hist(self, code, period="daily", start=None, end=None):
                return pd.DataFrame()

            def get_concept_boards(self):
                return pd.DataFrame()

            def get_concept_board_hist(self, code, period="daily", start=None, end=None):
                return pd.DataFrame()

            def get_sector_fund_flow(self, period="今日"):
                return pd.DataFrame()

            def get_china_us_bond_yield(self):
                return pd.DataFrame()

            def get_bond_yield_curve(self, bond_type="国债", period="daily", start_date=None, end_date=None):
                return pd.DataFrame()

            def get_bond_spot_quote(self):
                return pd.DataFrame()

            def get_convertible_bonds(self):
                return pd.DataFrame()

            def get_convertible_bond_detail(self, code):
                return {}

            def get_bond_spot(self, code):
                return pd.DataFrame()

            def get_bond_hist(self, code, period="daily", start_date=None, end_date=None):
                return pd.DataFrame()

            def get_a_share_valuation(self):
                return pd.DataFrame()

            def get_stock_valuation_lg(self, code):
                return pd.DataFrame()

            def get_index_valuation(self, code, indicator="pe"):
                return pd.DataFrame()

            def get_market_pe_lg(self, code):
                return pd.DataFrame()

            def get_market_pb_lg(self, code):
                return pd.DataFrame()

            def get_market_fund_flow(self):
                return pd.DataFrame()

            def get_stock_fund_flow(self, code, market="sh"):
                return pd.DataFrame()

            def get_north_fund_flow(self, market="北向资金"):
                return pd.DataFrame()

            def get_retail_sales_yearly(self):
                return pd.DataFrame()

            def get_fixed_asset_investment(self):
                return pd.DataFrame()

            def get_fund_manager(self, fund_code):
                return {}

            def get_fund_rating(self, fund_code):
                return None

            def batch_get_fund_nav(self, fund_codes, start_date=None, end_date=None):
                return {}

        adapter = TestAdapter("my_adapter")
        result = repr(adapter)
        assert "TestAdapter" in result
        assert "my_adapter" in result


# =============================================================================
# DataCache 类测试
# =============================================================================


class TestDataCache:
    """测试 DataCache 类"""

    def test_cache_init(self, tmp_path):
        """测试缓存初始化"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"), default_ttl=3600)
        assert cache.default_ttl == 3600
        assert cache.cache_dir.exists()

    def test_cache_set_and_get(self, tmp_path):
        """测试缓存设置和获取"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"))
        cache.set("test_key", {"data": "test_value"})

        result = cache.get("test_key")
        assert result == {"data": "test_value"}

    def test_cache_get_nonexistent(self, tmp_path):
        """测试获取不存在的缓存"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"))
        result = cache.get("nonexistent_key")
        assert result is None

    def test_cache_delete(self, tmp_path):
        """测试缓存删除"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"))
        cache.set("test_key", "test_value")
        cache.delete("test_key")

        result = cache.get("test_key")
        assert result is None

    def test_cache_exists(self, tmp_path):
        """测试缓存存在检查"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"))
        assert not cache.exists("test_key")

        cache.set("test_key", "test_value")
        assert cache.exists("test_key")

    def test_cache_clear(self, tmp_path):
        """测试缓存清空"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"))
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        assert not cache.exists("key1")
        assert not cache.exists("key2")

    def test_cache_get_stats(self, tmp_path):
        """测试缓存统计"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"))
        cache.set("key1", "value1")

        stats = cache.get_stats()
        assert "size" in stats
        assert "directory" in stats

    def test_cache_fund_info(self, tmp_path):
        """测试基金信息缓存便捷方法"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"))
        info = {"code": "000001", "name": "测试基金"}
        cache.set_fund_info("000001", info)

        result = cache.get_fund_info("000001")
        assert result == info

    def test_cache_fund_holdings(self, tmp_path):
        """测试持仓数据缓存便捷方法"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"))
        df = pd.DataFrame({"stock_code": ["600519"], "stock_name": ["贵州茅台"]})
        cache.set_fund_holdings("000001", "2024Q2", df)

        result = cache.get_fund_holdings("000001", "2024Q2")
        assert result.equals(df)

    def test_cache_fund_manager(self, tmp_path):
        """测试基金经理信息缓存便捷方法"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"))
        info = {"name": "张三", "company": "华夏基金"}
        cache.set_fund_manager("000001", info)

        result = cache.get_fund_manager("000001")
        assert result == info

    def test_cache_context_manager(self, tmp_path):
        """测试缓存上下文管理器"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"))
        with cache as c:
            c.set("test_key", "test_value")
            assert c.get("test_key") == "test_value"

    def test_cache_repr(self, tmp_path):
        """测试缓存字符串表示"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"))
        result = repr(cache)
        assert "DataCache" in result

    def test_cache_generate_key(self, tmp_path):
        """测试缓存键生成"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"))
        key1 = cache._generate_key("prefix", "arg1", "arg2", kwarg1="value1")
        key2 = cache._generate_key("prefix", "arg1", "arg2", kwarg1="value1")

        assert key1 == key2  # 相同参数生成相同键
        assert key1.startswith("prefix:")

    def test_cache_ttl(self, tmp_path):
        """测试缓存过期时间"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(tmp_path / "cache"), default_ttl=3600)
        cache.set("test_key", "test_value", ttl=7200)

        # 验证值存在
        assert cache.get("test_key") == "test_value"
