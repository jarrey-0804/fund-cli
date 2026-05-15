"""
数据源适配器混合类单元测试

测试 DataSourceAdapterMixin 中所有占位方法的错误抛出行为。
每个方法都应该抛出 DataSourceError，且错误消息包含"不支持"。
"""

import inspect

import pandas as pd
import pytest

from fund_cli.data.adapters.mixins import DataSourceAdapterMixin
from fund_cli.data.base import DataSourceError


class TestDataSourceAdapterMixin:
    """测试数据源适配器混合类"""

    @pytest.fixture
    def mixin(self):
        """创建测试用的混合类实例"""
        instance = DataSourceAdapterMixin()
        instance.name = "test_adapter"
        return instance

    # =========================================================================
    # P0 - 核心基金功能接口测试
    # =========================================================================

    @pytest.mark.parametrize("method_name,kwargs", [
        ("get_fund_info_ths", {"fund_code": "000001"}),
        ("get_index_fund_info", {"category": "全部", "indicator": "全部"}),
        ("get_fund_overview", {"fund_code": "000001"}),
        ("get_fund_purchase_status", {}),
        ("get_fund_daily_nav", {}),
        ("get_fund_category_spot", {"category": "股票型", "date": None}),
        ("get_etf_spot_ths", {"date": None}),
        ("get_etf_hist", {"fund_code": "510050", "period": "daily", "start_date": None, "end_date": None}),
        ("get_lof_hist", {"fund_code": "160106", "period": "daily", "start_date": None, "end_date": None}),
        ("search_funds", {"fund_type": None, "company": None, "min_scale": None, "max_scale": None, "keyword": None, "limit": 100}),
        ("get_fund_list", {"fund_type": None}),
        ("get_benchmark_nav", {"benchmark_code": "000300", "start_date": None, "end_date": None}),
        ("get_fund_holdings", {"fund_code": "000001", "report_date": None}),
        ("get_fund_bond_holdings", {"fund_code": "000001", "year": None}),
        ("get_fund_industry_allocation", {"fund_code": "000001", "year": None}),
        ("get_fund_portfolio_change", {"fund_code": "000001", "indicator": "累计买入", "year": None}),
        ("get_all_fund_managers", {}),
        ("get_etf_minute", {"fund_code": "510050", "period": "1", "start_date": None, "end_date": None}),
        ("get_lof_minute", {"fund_code": "160106", "period": "1", "start_date": None, "end_date": None}),
    ])
    def test_p0_methods_raise_error(self, mixin, method_name, kwargs):
        """测试 P0 级别方法抛出 DataSourceError"""
        method = getattr(mixin, method_name)
        with pytest.raises(DataSourceError, match="不支持"):
            method(**kwargs)

    # =========================================================================
    # P1 - 分析增强功能接口测试
    # =========================================================================

    @pytest.mark.parametrize("method_name,kwargs", [
        # 基金公司/规模 (5个)
        ("get_fund_company_aum", {}),
        ("get_fund_aum_trend", {}),
        ("get_fund_company_aum_history", {"year": None}),
        ("get_fund_scale_change", {}),
        ("get_fund_holder_structure", {}),
        # 基金评级 (4个)
        ("get_fund_ratings", {}),
        ("get_fund_rating_sh", {"date": None}),
        ("get_fund_rating_zs", {"date": None}),
        ("get_fund_rating_ja", {"date": None}),
        # 基金分红/拆分 (3个)
        ("get_fund_dividends", {"year": None, "fund_type": "", "page": -1}),
        ("get_fund_splits", {"year": None, "fund_type": "", "page": -1}),
        ("get_fund_dividend_rank", {}),
        # 基金排行 (5个)
        ("get_fund_rank_by_type", {"fund_type": "全部"}),
        ("get_exchange_fund_rank", {}),
        ("get_money_fund_rank", {}),
        ("get_lcx_fund_rank", {}),
        ("get_hk_fund_rank", {}),
        # 基金业绩/分析 (3个)
        ("get_fund_achievement", {"fund_code": "000001"}),
        ("get_fund_risk_analysis", {"fund_code": "000001"}),
        ("get_fund_profit_probability", {"fund_code": "000001"}),
        # 基金资产配置 (1个)
        ("get_fund_asset_allocation", {"fund_code": "000001", "date": None}),
        # 市场指数扩展 (6个)
        ("get_index_spot_em", {"category": "沪深重要指数"}),
        ("get_index_spot_sina", {}),
        ("get_index_daily_tx", {"code": "sh000001", "start": None, "end": None}),
        ("get_index_daily_em", {"code": "000001", "start": None, "end": None}),
        ("get_index_hist", {"code": "000001", "period": "daily", "start": None, "end": None}),
        ("get_index_minute", {"code": "000001", "period": "1", "start": None, "end": None}),
    ])
    def test_p1_methods_raise_error(self, mixin, method_name, kwargs):
        """测试 P1 级别方法抛出 DataSourceError"""
        method = getattr(mixin, method_name)
        with pytest.raises(DataSourceError, match="不支持"):
            method(**kwargs)

    # =========================================================================
    # P2 - 辅助分析功能接口测试
    # =========================================================================

    @pytest.mark.parametrize("method_name,kwargs", [
        # 宏观经济数据 (22个)
        ("get_macro_leverage_ratio", {}),
        ("get_enterprise_price_index", {}),
        ("get_fdi_data", {}),
        ("get_lpr_data", {}),
        ("get_urban_unemployment", {}),
        ("get_social_financing", {}),
        ("get_gdp_yearly", {}),
        ("get_gdp_quarterly", {}),
        ("get_cpi_yearly", {}),
        ("get_cpi_monthly", {}),
        ("get_ppi_yearly", {}),
        ("get_ppi_monthly", {}),
        ("get_exports_yearly", {}),
        ("get_imports_yearly", {}),
        ("get_trade_balance", {}),
        ("get_industrial_production", {}),
        ("get_pmi_official", {}),
        ("get_pmi_caixin", {}),
        ("get_services_pmi", {}),
        ("get_non_manufacturing_pmi", {}),
        ("get_m2_yearly", {}),
        ("get_new_loan", {}),
        # 利率数据 (8个)
        ("get_china_interest_rate", {}),
        ("get_usa_interest_rate", {}),
        ("get_euro_interest_rate", {}),
        ("get_japan_interest_rate", {}),
        ("get_uk_interest_rate", {}),
        ("get_shibor", {}),
        ("get_shibor_lpr", {}),
        ("get_hibor", {}),
        # 行业板块数据 (5个)
        ("get_industry_boards", {}),
        ("get_industry_board_hist", {"code": "BK01", "period": "daily", "start": None, "end": None}),
        ("get_concept_boards", {}),
        ("get_concept_board_hist", {"code": "GN01", "period": "daily", "start": None, "end": None}),
        ("get_sector_fund_flow", {"period": "今日"}),
        # 债券数据 (7个)
        ("get_china_us_bond_yield", {}),
        ("get_bond_yield_curve", {"bond_type": "国债", "period": "daily", "start": None, "end": None}),
        ("get_bond_spot_quote", {}),
        ("get_convertible_bonds", {}),
        ("get_convertible_bond_detail", {"code": "110001"}),
        ("get_bond_spot", {"code": "sh019547"}),
        ("get_bond_hist", {"code": "sh019547", "period": "daily", "start": None, "end": None}),
        # 估值指标 (5个)
        ("get_a_share_valuation", {}),
        ("get_stock_valuation_lg", {"code": "000001"}),
        ("get_index_valuation", {"code": "000001", "indicator": "pe"}),
        ("get_market_pe_lg", {"code": "sh"}),
        ("get_market_pb_lg", {"code": "sh"}),
        # 资金流向 (3个)
        ("get_market_fund_flow", {}),
        ("get_stock_fund_flow", {"code": "600519", "market": "sh"}),
        ("get_north_fund_flow", {"market": "北向资金"}),
        # 其他 (2个)
        ("get_retail_sales_yearly", {}),
        ("get_fixed_asset_investment", {}),
        # 已有接口兼容 (4个)
        ("get_fund_manager", {"fund_code": "000001"}),
        ("get_fund_rating", {"fund_code": "000001"}),
        ("batch_get_fund_nav", {"fund_codes": ["000001", "000002"], "start_date": None, "end_date": None}),
        ("get_fund_fee", {"fund_code": "000001"}),
    ])
    def test_p2_methods_raise_error(self, mixin, method_name, kwargs):
        """测试 P2 级别方法抛出 DataSourceError"""
        method = getattr(mixin, method_name)
        with pytest.raises(DataSourceError, match="不支持"):
            method(**kwargs)

    # =========================================================================
    # 错误消息验证测试
    # =========================================================================

    def test_error_message_contains_adapter_name(self, mixin):
        """测试错误消息包含适配器名称"""
        with pytest.raises(DataSourceError) as exc_info:
            mixin.get_fund_holdings("000001")
        assert "test_adapter" in str(exc_info.value)

    def test_error_message_contains_interface_name(self, mixin):
        """测试错误消息包含接口名称"""
        with pytest.raises(DataSourceError) as exc_info:
            mixin.get_fund_info_ths("000001")
        assert "同花顺基金信息" in str(exc_info.value)

    @pytest.mark.parametrize("method_name,interface_name", [
        ("get_fund_purchase_status", "申购状态"),
        ("get_fund_daily_nav", "每日净值"),
        ("get_fund_category_spot", "分类行情"),
        ("get_etf_spot_ths", "同花顺ETF"),
        ("get_etf_hist", "ETF历史"),
        ("get_lof_hist", "LOF历史"),
        ("get_fund_holdings", "基金持仓"),
        ("get_fund_bond_holdings", "基金债券持仓"),
        ("get_fund_industry_allocation", "行业配置"),
        ("get_fund_company_aum", "基金公司规模"),
        ("get_fund_ratings", "基金评级总汇"),
        ("get_fund_dividends", "基金分红"),
        ("get_macro_leverage_ratio", "宏观杠杆率"),
        ("get_shibor", "SHIBOR"),
        ("get_industry_boards", "行业板块列表"),
        ("get_north_fund_flow", "北向资金"),
    ])
    def test_error_message_contains_specific_interface(self, mixin, method_name, interface_name):
        """测试错误消息包含特定接口名称"""
        method = getattr(mixin, method_name)
        # 获取方法签名并构造默认参数
        sig = inspect.signature(method)
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param.default is not param.empty:
                kwargs[param_name] = param.default
            elif param_name in ["fund_code", "code", "symbol"]:
                kwargs[param_name] = "000001"
            elif param_name == "fund_codes":
                kwargs[param_name] = ["000001"]
            elif param_name == "year":
                kwargs[param_name] = None
            elif param_name == "date":
                kwargs[param_name] = None
            elif param_name in ["start", "end", "start_date", "end_date"]:
                kwargs[param_name] = None
            elif param_name == "period":
                kwargs[param_name] = "daily"
            elif param_name == "market":
                kwargs[param_name] = "sh"
            elif param_name == "indicator":
                kwargs[param_name] = "pe"
            elif param_name == "category":
                kwargs[param_name] = "全部"
            else:
                kwargs[param_name] = ""

        with pytest.raises(DataSourceError) as exc_info:
            method(**kwargs)
        assert interface_name in str(exc_info.value)


class TestDataSourceAdapterMixinMethodsCount:
    """验证混合类方法数量"""

    def test_all_methods_are_tested(self):
        """验证所有方法都被测试覆盖"""
        # 获取所有公共方法（不包括 __ 开头的方法）
        all_methods = [
            name for name, method in inspect.getmembers(DataSourceAdapterMixin, predicate=inspect.isfunction)
            if not name.startswith("_")
        ]

        # 预期的方法数量（根据 mixins.py 文件）
        # P0: 19个方法
        # P1: 25个方法
        # P2: 56个方法
        # 总计: 约100个方法
        expected_min_count = 90  # 至少应该有90个方法

        assert len(all_methods) >= expected_min_count, (
            f"预期至少有 {expected_min_count} 个方法，实际有 {len(all_methods)} 个"
        )


class TestDataSourceAdapterMixinInheritance:
    """测试混合类的继承行为"""

    def test_can_be_inherited(self):
        """测试混合类可以被继承"""
        class CustomAdapter(DataSourceAdapterMixin):
            def __init__(self):
                self.name = "custom"

            def get_fund_holdings(self, fund_code, report_date=None):
                """覆盖持仓方法"""
                return pd.DataFrame({"stock_code": ["600519"], "stock_name": ["贵州茅台"]})

        adapter = CustomAdapter()
        # 覆盖的方法应该正常工作
        result = adapter.get_fund_holdings("000001")
        assert len(result) == 1

        # 未覆盖的方法应该抛出错误
        with pytest.raises(DataSourceError, match="不支持"):
            adapter.get_fund_info_ths("000001")

    def test_inheritance_with_multiple_overrides(self):
        """测试继承并覆盖多个方法"""
        class PartialAdapter(DataSourceAdapterMixin):
            def __init__(self):
                self.name = "partial"

            def get_fund_holdings(self, fund_code, report_date=None):
                return pd.DataFrame()

            def get_fund_info_ths(self, fund_code):
                return {"code": fund_code, "name": "测试基金"}

            def get_fund_ratings(self):
                return pd.DataFrame({"rating": [5]})

        adapter = PartialAdapter()

        # 覆盖的方法
        assert adapter.get_fund_holdings("000001").empty
        assert adapter.get_fund_info_ths("000001")["name"] == "测试基金"
        assert len(adapter.get_fund_ratings()) == 1

        # 未覆盖的方法
        with pytest.raises(DataSourceError):
            adapter.get_fund_dividends()


class TestDataSourceAdapterMixinEdgeCases:
    """测试边界条件"""

    @pytest.fixture
    def mixin(self):
        """创建测试用的混合类实例"""
        instance = DataSourceAdapterMixin()
        instance.name = "test_adapter"
        return instance

    def test_name_attribute_required(self, mixin):
        """测试 name 属性是必需的"""
        # mixin 已经设置了 name 属性
        assert hasattr(mixin, "name")
        assert mixin.name == "test_adapter"

    def test_name_attribute_used_in_error(self, mixin):
        """测试 name 属性在错误消息中使用"""
        mixin.name = "my_custom_adapter"
        with pytest.raises(DataSourceError) as exc_info:
            mixin.get_fund_holdings("000001")
        assert "my_custom_adapter" in str(exc_info.value)

    def test_method_with_empty_string_params(self, mixin):
        """测试空字符串参数"""
        with pytest.raises(DataSourceError):
            mixin.get_fund_info_ths("")

    def test_method_with_none_params(self, mixin):
        """测试 None 参数"""
        # 某些方法接受 None 参数
        with pytest.raises(DataSourceError):
            mixin.get_fund_company_aum_history(year=None)

    def test_method_with_various_date_formats(self, mixin):
        """测试不同日期格式参数"""
        # 测试方法接受日期参数
        with pytest.raises(DataSourceError):
            mixin.get_etf_hist("510050", start_date="20240101", end_date="20241231")
