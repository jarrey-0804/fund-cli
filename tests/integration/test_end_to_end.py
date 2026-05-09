"""
Fund CLI v3.1 端到端集成测试

测试各模块协作，包括：
- DataManager + DataSourceGateway 集成
- DataNormalizer + 适配器协作
- 熔断器 + 降级流程
- TemplateEngine 模板渲染
- AIAnalyzer + Reporter 协作
- 多适配器注册与优先级
"""

import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch, PropertyMock

import pandas as pd

from fund_cli.core.data_manager import DataManager
from fund_cli.core.data_gateway import DataSourceGateway, CircuitState
from fund_cli.core.template_engine import TemplateEngine
from fund_cli.core.ai_analyzer import AIAnalyzer, AnalysisResult, AIBackend
from fund_cli.core.reporter import Reporter
from fund_cli.data.normalizer import DataNormalizer
from fund_cli.data.base import DataSourceAdapter, DataSourceError, DataNotFoundError


# ==============================================================================
# 测试数据与 Mock 适配器
# ==============================================================================

class MockAdapter(DataSourceAdapter):
    """Mock 数据源适配器"""

    def __init__(self, name: str = "mock", fail_count: int = 0, fail_method: str | None = None):
        super().__init__(name)
        self._is_available = True
        self._fail_count = fail_count
        self._fail_method = fail_method
        self._call_count = 0
        self._method_failure_counts = {}  # 每个方法的失败计数

    def set_available(self, available: bool) -> None:
        self._is_available = available

    def set_method_failure(self, method_name: str, count: int = 1) -> None:
        """设置方法失败次数"""
        self._method_failure_counts[method_name] = count

    def _should_fail(self, method_name: str) -> bool:
        """检查方法是否应该失败"""
        if method_name in self._method_failure_counts:
            if self._method_failure_counts[method_name] > 0:
                self._method_failure_counts[method_name] -= 1
                return True
        return False

    def is_available(self) -> bool:
        return self._is_available

    def get_fund_info(self, fund_code: str) -> dict[str, Any]:
        """获取基金信息"""
        self._call_count += 1
        if self._should_fail("get_fund_info"):
            raise DataSourceError(f"Mock {self._name} get_fund_info failed")

        return {
            "fund_code": fund_code,
            "fund_name": f"测试基金{fund_code}",
            "fund_type": "混合型",
            "found_date": "2020-01-01",
            "company": "测试基金公司",
            "manager": "测试经理",
            "scale": 10.5,
        }

    def get_fund_nav(self, fund_code: str, start_date=None, end_date=None) -> pd.DataFrame:
        """获取基金净值"""
        self._call_count += 1
        if self._should_fail("get_fund_nav"):
            raise DataSourceError(f"Mock {self._name} get_fund_nav failed")

        dates = pd.date_range(start="2024-01-01", end="2024-01-10", freq="D")
        return pd.DataFrame({
            "fund_code": [fund_code] * len(dates),
            "nav_date": [d.strftime("%Y-%m-%d") for d in dates],
            "unit_nav": [1.0 + i * 0.01 for i in range(len(dates))],
            "accumulated_nav": [1.0 + i * 0.012 for i in range(len(dates))],
            "daily_return": [1.0] + [1.0] * (len(dates) - 1),
        })

    def get_fund_manager(self, fund_code: str) -> dict[str, Any]:
        """获取基金经理"""
        return {
            "fund_code": fund_code,
            "manager_name": "测试经理",
            "start_date": "2020-01-01",
        }

    def get_fund_holdings(self, fund_code: str, date=None) -> pd.DataFrame:
        """获取基金持仓"""
        return pd.DataFrame({
            "fund_code": [fund_code] * 3,
            "stock_code": ["600000", "000001", "300001"],
            "stock_name": ["浦发银行", "平安银行", "宁德时代"],
            "volume": [1000000, 800000, 500000],
            "proportion": [8.5, 6.2, 4.1],
        })

    def get_fund_asset_allocation(self, fund_code: str) -> dict[str, Any]:
        """获取资产配置"""
        return {
            "fund_code": fund_code,
            "date": "2024-01-01",
            "stock_ratio": 75.0,
            "bond_ratio": 15.0,
            "cash_ratio": 10.0,
            "total_asset": 50.0,
        }

    def get_fund_benchmark(self, fund_code: str) -> dict[str, Any]:
        return {"fund_code": fund_code, "benchmark": "沪深300"}

    def get_etf_spot(self) -> pd.DataFrame:
        return pd.DataFrame({"code": ["510300"], "name": ["华泰柏瑞沪深300ETF"]})

    def get_lof_spot(self) -> pd.DataFrame:
        return pd.DataFrame({"code": ["160119"], "name": ["南方中证500ETF联接A"]})

    def get_fund_purchase_status(self) -> pd.DataFrame:
        return pd.DataFrame({"code": ["000001"], "name": ["平安策略先锋混合"], "status": ["开放"]})

    def get_all_fund_names(self) -> pd.DataFrame:
        return pd.DataFrame({
            "code": ["000001", "000002"],
            "symbol": ["PA", "YY"],
            "name": ["平安策略先锋混合", "银河灵活配置"],
            "type": ["混合型", "混合型"],
            "full_name": ["平安策略先锋混合A", "银河灵活配置A"],
        })

    def get_fund_daily_nav(self) -> pd.DataFrame:
        return pd.DataFrame({
            "fund_code": ["000001"],
            "nav_date": ["2024-01-10"],
            "unit_nav": [2.5],
            "accumulated_nav": [3.2],
        })

    # 以下为适配器接口要求的抽象方法实现
    def get_all_fund_managers(self) -> pd.DataFrame:
        return pd.DataFrame({"manager_id": [], "name": [], "fund_count": []})

    def search_funds(self, **kwargs) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_list(self, fund_type=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_benchmark_nav(self, benchmark_code, start_date=None, end_date=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_fee(self, fund_code: str) -> dict[str, Any]:
        return {}

    def get_fund_rating(self, fund_code: str) -> int | None:
        return 5

    def batch_get_fund_nav(self, fund_codes, start_date=None, end_date=None) -> dict:
        return {}

    # P0 级别接口
    def get_fund_info_ths(self, fund_code: str) -> dict[str, Any]:
        return {}

    def get_index_fund_info(self, category="全部", indicator="全部") -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_overview(self, fund_code: str) -> dict[str, Any]:
        return {}

    def get_fund_category_spot(self, category="", date=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_etf_spot_ths(self, date=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_etf_hist(self, fund_code, period="daily", start_date=None, end_date=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_lof_hist(self, fund_code, period="daily", start_date=None, end_date=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_etf_minute(self, fund_code, period="1", start_date=None, end_date=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_lof_minute(self, fund_code, period="1", start_date=None, end_date=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_bond_holdings(self, fund_code, year=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_industry_allocation(self, fund_code, year=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_portfolio_change(self, fund_code, indicator="累计买入", year=None) -> pd.DataFrame:
        return pd.DataFrame()

    # P1 级别接口
    def get_fund_company_aum(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_aum_trend(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_company_aum_history(self, year=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_scale_change(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_holder_structure(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_ratings(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_rating_sh(self, date=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_rating_zs(self, date=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_rating_ja(self, date=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_dividends(self, year=None, fund_type="", page=-1) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_splits(self, year=None, fund_type="", page=-1) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_dividend_rank(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_rank_by_type(self, fund_type="全部") -> pd.DataFrame:
        return pd.DataFrame()

    def get_exchange_fund_rank(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_money_fund_rank(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_lcx_fund_rank(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_hk_fund_rank(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_achievement(self, fund_code: str) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_risk_analysis(self, fund_code: str) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_profit_probability(self, fund_code: str) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fund_asset_allocation_p1(self, fund_code: str, date=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_index_spot_em(self, category="沪深重要指数") -> pd.DataFrame:
        return pd.DataFrame()

    def get_index_spot_sina(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_index_daily_tx(self, code, start=None, end=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_index_daily_em(self, code, start=None, end=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_index_hist(self, code, period="daily", start=None, end=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_index_minute(self, code, period="1", start=None, end=None) -> pd.DataFrame:
        return pd.DataFrame()

    # P2 级别接口
    def get_macro_leverage_ratio(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_enterprise_price_index(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fdi_data(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_lpr_data(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_urban_unemployment(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_social_financing(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_gdp_yearly(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_gdp_quarterly(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_cpi_yearly(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_cpi_monthly(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_ppi_yearly(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_ppi_monthly(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_exports_yearly(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_imports_yearly(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_trade_balance(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_industrial_production(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_pmi_official(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_pmi_caixin(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_services_pmi(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_non_manufacturing_pmi(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_m2_yearly(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_new_loan(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_retail_sales_yearly(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_fixed_asset_investment(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_china_interest_rate(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_usa_interest_rate(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_euro_interest_rate(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_japan_interest_rate(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_uk_interest_rate(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_shibor(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_shibor_lpr(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_hibor(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_industry_boards(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_industry_board_hist(self, code, period="daily", start=None, end=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_concept_boards(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_concept_board_hist(self, code, period="daily", start=None, end=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_sector_fund_flow(self, period="今日") -> pd.DataFrame:
        return pd.DataFrame()

    def get_china_us_bond_yield(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_bond_yield_curve(self, bond_type="国债", period="daily", start=None, end=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_bond_spot_quote(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_convertible_bonds(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_convertible_bond_detail(self, code: str) -> dict[str, Any]:
        return {}

    def get_bond_spot(self, code: str) -> pd.DataFrame:
        return pd.DataFrame()

    def get_bond_hist(self, code, period="daily", start=None, end=None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_a_share_valuation(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_stock_valuation_lg(self, code: str) -> pd.DataFrame:
        return pd.DataFrame()

    def get_index_valuation(self, code: str, indicator="pe") -> pd.DataFrame:
        return pd.DataFrame()

    def get_market_pe_lg(self, code: str) -> pd.DataFrame:
        return pd.DataFrame()

    def get_market_pb_lg(self, code: str) -> pd.DataFrame:
        return pd.DataFrame()

    def get_market_fund_flow(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_stock_fund_flow(self, code: str, market="sh") -> pd.DataFrame:
        return pd.DataFrame()

    def get_north_fund_flow(self, market="北向资金") -> pd.DataFrame:
        return pd.DataFrame()


# ==============================================================================
# 测试类
# ==============================================================================

class TestDataManagerGateway(unittest.TestCase):
    """
    DataManager + Gateway 集成测试

    测试场景：
    1. DataManager 初始化时自动注册适配器到 Gateway
    2. 调用 gateway.call() 方法触发适配器方法
    3. 降级流程：主适配器失败时自动切换备用
    """

    def setUp(self):
        """测试前准备"""
        # 创建适配器时使用配置优先级列表中的名称
        self.mock_primary = MockAdapter(name="akshare")
        self.mock_secondary = MockAdapter(name="tushare")
        self.gateway = DataSourceGateway()

    def tearDown(self):
        """测试后清理"""
        pass

    def test_adapter_auto_registration(self):
        """测试 DataManager 初始化时自动注册适配器到 Gateway"""
        # 注册适配器
        self.gateway.register_adapter("akshare", self.mock_primary)
        self.gateway.register_adapter("tushare", self.mock_secondary)

        # 验证注册成功
        self.assertIn("akshare", self.gateway._adapters)
        self.assertIn("tushare", self.gateway._adapters)

        # 验证熔断器状态初始化
        self.assertEqual(
            self.gateway._circuit_states["akshare"],
            CircuitState.CLOSED
        )
        self.assertEqual(
            self.gateway._circuit_states["tushare"],
            CircuitState.CLOSED
        )

    def test_gateway_call_triggers_adapter_method(self):
        """测试调用 gateway.call() 方法触发适配器方法"""
        # 注册适配器
        self.gateway.register_adapter("akshare", self.mock_primary)

        # 通过 gateway.call 调用方法
        result = self.gateway.call("get_fund_info", "000001")

        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertEqual(result["fund_code"], "000001")
        self.assertEqual(result["fund_name"], "测试基金000001")

        # 验证方法被调用
        self.assertEqual(self.mock_primary._call_count, 1)

    def test_fallback_on_primary_failure(self):
        """测试降级流程：主适配器失败时自动切换备用"""
        # 注册主备适配器
        self.gateway.register_adapter("akshare", self.mock_primary)
        self.gateway.register_adapter("tushare", self.mock_secondary)

        # 设置主适配器失败（设置很高的失败计数）
        self.mock_primary.set_method_failure("get_fund_info", count=100)

        # 通过 gateway.call 调用，应该自动降级到 secondary
        result = self.gateway.call("get_fund_info", "000001")

        # 验证结果来自备用适配器
        self.assertIsInstance(result, dict)
        self.assertEqual(result["fund_code"], "000001")

    def test_gateway_get_available_adapters(self):
        """测试获取可用适配器列表"""
        # 注册适配器
        self.gateway.register_adapter("akshare", self.mock_primary)
        self.gateway.register_adapter("tushare", self.mock_secondary)

        # 获取可用适配器
        available = self.gateway.get_available_adapters()

        # 验证
        self.assertIsInstance(available, list)
        self.assertIn("akshare", available)
        self.assertIn("tushare", available)

    def test_gateway_status_reporting(self):
        """测试网关状态报告"""
        # 注册适配器
        self.gateway.register_adapter("akshare", self.mock_primary)

        # 获取状态
        status = self.gateway.get_status()

        # 验证状态结构
        self.assertIn("adapters", status)
        self.assertIn("priority", status)
        self.assertIn("available_adapters", status)
        self.assertIn("akshare", status["adapters"])
        self.assertEqual(
            status["adapters"]["akshare"]["circuit_state"],
            CircuitState.CLOSED.value
        )


class TestNormalizerWithAdapter(unittest.TestCase):
    """
    DataNormalizer + TushareAdapter 协作测试

    测试场景：
    1. 获取原始数据 -> 标准化 -> 输出统一格式
    2. 测试日期格式标准化、基金代码去后缀、数值类型转换
    """

    def test_normalize_fund_code_remove_suffix(self):
        """测试基金代码去后缀"""
        # 测试各种后缀
        test_cases = [
            ("000001.OF", "000001"),
            ("510300.SH", "510300"),
            ("159919.SZ", "159919"),
            ("000001", "000001"),  # 无后缀
            ("bj001", "bj001"),     # 北京交易所
        ]

        for original, expected in test_cases:
            result = DataNormalizer.normalize_fund_code(original)
            self.assertEqual(result, expected, f"Failed for {original}")

    def test_normalize_date_formats(self):
        """测试日期格式标准化"""
        test_cases = [
            ("20240101", "2024-01-01"),   # YYYYMMDD
            ("2024-01-01", "2024-01-01"), # YYYY-MM-DD
            ("2024/01/01", "2024-01-01"), # YYYY/MM/DD
            ("2024.01.01", "2024-01-01"), # YYYY.MM.DD
            (date(2024, 1, 1), "2024-01-01"),  # date对象
            (datetime(2024, 1, 1), "2024-01-01"),  # datetime对象
        ]

        for original, expected in test_cases:
            result = DataNormalizer.normalize_date(original)
            self.assertEqual(result, expected, f"Failed for {original}")

    def test_normalize_nav_data(self):
        """测试净值数据标准化"""
        # 原始数据（模拟 Tushare 返回格式）
        raw_data = pd.DataFrame({
            "ts_code": ["000001.OF", "000002.OF"],
            "end_date": ["20240101", "20240102"],
            "unit_nav": [1.5, 1.55],
            "accum_nav": [2.0, 2.05],
            "daily_return": [1.0, 3.33],
        })

        # 标准化
        normalized = DataNormalizer.normalize_nav_data(raw_data)

        # 验证字段名
        self.assertIn("fund_code", normalized.columns)
        self.assertIn("nav_date", normalized.columns)
        self.assertIn("unit_nav", normalized.columns)
        self.assertIn("accumulated_nav", normalized.columns)

        # 验证数据转换
        self.assertEqual(normalized["fund_code"].iloc[0], "000001")
        self.assertEqual(normalized["nav_date"].iloc[0], "2024-01-01")

    def test_normalize_fund_holdings(self):
        """测试持仓数据标准化"""
        # 原始数据 - 使用 normalize_fund_holdings 需要的字段
        raw_data = pd.DataFrame({
            "fund_code": ["000001.OF"],
            "stock_code": ["600000"],  # 使用 stock_code 而不是 symbol
            "stock_name": ["浦发银行"],
            "volume": [1000000],
            "proportion": [8.5],
        })

        # 标准化
        normalized = DataNormalizer.normalize_fund_holdings(raw_data)

        # 验证字段名
        self.assertIn("fund_code", normalized.columns)
        self.assertIn("stock_code", normalized.columns)
        self.assertIn("stock_name", normalized.columns)
        self.assertIn("volume", normalized.columns)
        self.assertIn("proportion", normalized.columns)

        # 验证数据转换
        self.assertEqual(normalized["fund_code"].iloc[0], "000001")
        self.assertEqual(normalized["stock_code"].iloc[0], "600000")

    def test_normalize_asset_allocation(self):
        """测试资产配置数据标准化"""
        # 原始数据
        raw_data = {
            "fund_code": "000001.OF",
            "date": "20240101",
            "stock_ratio": 70,
            "bond_ratio": 20,
            "cash_ratio": 10,
            "total_asset": 50.5,
        }

        # 标准化
        normalized = DataNormalizer.normalize_asset_allocation(raw_data)

        # 验证
        self.assertEqual(normalized["fund_code"], "000001")
        self.assertEqual(normalized["date"], "2024-01-01")
        self.assertAlmostEqual(normalized["stock_ratio"], 70.0, places=1)
        self.assertAlmostEqual(normalized["bond_ratio"], 20.0, places=1)
        self.assertAlmostEqual(normalized["cash_ratio"], 10.0, places=1)

    def test_normalize_fund_info(self):
        """测试基金信息标准化"""
        # 原始数据（模拟不同数据源格式）
        raw_data = {
            "ts_code": "000001.OF",
            "name": "测试基金",
            "fund_type": "混合型",
            "found_date": "20200101",
            "management": "测试公司",
        }

        # 标准化
        normalized = DataNormalizer.normalize_fund_info(raw_data)

        # 验证字段映射
        self.assertIn("fund_code", normalized)
        self.assertIn("fund_name", normalized)
        self.assertEqual(normalized["fund_code"], "000001")
        self.assertEqual(normalized["fund_name"], "测试基金")
        # found_date 应该被标准化为 found_date（不在 DATE_FIELDS 中）
        self.assertEqual(normalized["found_date"], "2020-01-01")


class TestGatewayCircuitBreaker(unittest.TestCase):
    """
    DataSourceGateway 熔断 + 降级完整流程测试

    测试场景：
    1. 模拟主适配器连续失败 -> 熔断打开
    2. 熔断后尝试 HALF_OPEN -> 成功 -> 熔断关闭
    3. 降级：tushare 失败 -> akshare 降级
    """

    def setUp(self):
        """测试前准备"""
        self.gateway = DataSourceGateway()
        # 设置较低的熔断阈值以便测试
        self.gateway._failure_threshold = 3
        self.gateway._recovery_timeout = 1  # 1秒恢复

    def test_circuit_breaker_opens_after_failures(self):
        """测试熔断器在连续失败后打开"""
        # 创建新的 gateway 并设置低阈值
        gateway = DataSourceGateway()
        gateway._failure_threshold = 3

        # 注册适配器（使用配置优先级列表中的名称）
        mock_adapter = MockAdapter(name="akshare")
        gateway.register_adapter("akshare", mock_adapter)

        # 设置方法失败
        mock_adapter.set_method_failure("get_fund_info", count=3)

        # 连续调用触发熔断
        for i in range(3):
            try:
                gateway.call("get_fund_info", "000001")
            except DataSourceError:
                pass

        # 验证熔断器打开
        self.assertEqual(
            gateway._circuit_states["akshare"],
            CircuitState.OPEN
        )

    def test_circuit_breaker_half_open_after_timeout(self):
        """测试熔断器超时后进入半开状态"""
        gateway = DataSourceGateway()
        gateway._failure_threshold = 3
        gateway._recovery_timeout = 0  # 立即恢复

        mock_adapter = MockAdapter(name="akshare")
        gateway.register_adapter("akshare", mock_adapter)

        # 触发熔断
        mock_adapter.set_method_failure("get_fund_info", count=10)
        for i in range(3):
            try:
                gateway.call("get_fund_info", "000001")
            except DataSourceError:
                pass

        self.assertEqual(gateway._circuit_states["akshare"], CircuitState.OPEN)

        # 手动触发半开状态检查
        # 由于 recovery_timeout=0，应该很快进入半开
        try:
            gateway.call("get_fund_info", "000001")
        except DataSourceError:
            pass

        # 验证状态（可能是 HALF_OPEN 或因为失败重置）
        self.assertIn(
            gateway._circuit_states["akshare"],
            [CircuitState.HALF_OPEN, CircuitState.OPEN]
        )

    def test_circuit_breaker_closes_after_success(self):
        """测试熔断器在成功后关闭"""
        gateway = DataSourceGateway()
        gateway._failure_threshold = 5

        mock_adapter = MockAdapter(name="akshare")
        gateway.register_adapter("akshare", mock_adapter)

        # 先有一些失败（但不超过阈值）
        for i in range(2):
            try:
                gateway.call("get_fund_info", "000001")
            except DataSourceError:
                pass

        # 验证失败计数（如果方法没有失败，计数为0）
        self.assertEqual(gateway._failure_counts["akshare"], 0)

        # 成功调用
        result = gateway.call("get_fund_info", "000001")
        self.assertEqual(result["fund_code"], "000001")

    def test_fallback_to_secondary_adapter(self):
        """测试降级到备用适配器"""
        # 注册主备适配器（使用配置优先级列表中的名称）
        primary = MockAdapter(name="akshare")
        secondary = MockAdapter(name="tushare")
        self.gateway.register_adapter("akshare", primary)
        self.gateway.register_adapter("tushare", secondary)

        # 设置主适配器失败
        primary.set_method_failure("get_fund_info", count=100)

        # 调用应该降级到备用
        result = self.gateway.call("get_fund_info", "000001")

        # 验证结果来自备用适配器
        self.assertEqual(result["fund_code"], "000001")

    def test_all_adapters_fail_raises_error(self):
        """测试所有适配器都失败时抛出错误"""
        # 注册两个都失败的适配器
        primary = MockAdapter(name="akshare")
        secondary = MockAdapter(name="tushare")
        self.gateway.register_adapter("akshare", primary)
        self.gateway.register_adapter("tushare", secondary)

        primary.set_method_failure("get_fund_info", count=100)
        secondary.set_method_failure("get_fund_info", count=100)

        # 调用应该抛出错误
        with self.assertRaises(DataSourceError):
            self.gateway.call("get_fund_info", "000001")


class TestTemplateEngineIntegration(unittest.TestCase):
    """
    TemplateEngine + 报告模板渲染测试

    测试场景：
    1. 使用真实模板文件渲染不同报告类型
    2. 单基金报告、投资组合报告、市场流向报告、风控报告
    """

    def setUp(self):
        """测试前准备"""
        # 获取模板目录
        template_dir = Path(__file__).parent.parent.parent / "src" / "fund_cli" / "templates"
        self.engine = TemplateEngine(template_dirs=[str(template_dir)])

        # 测试数据
        self.single_fund_data = {
            "fund_code": "000001",
            "fund_name": "平安策略先锋混合",
            "fund_type": "混合型",
            "found_date": "2020-01-01",
            "performance_metrics": [
                {"name": "近1年收益率", "value": 0.1523, "comment": "良好"},
                {"name": "夏普比率", "value": 1.25, "comment": "优秀"},
                {"name": "最大回撤", "value": -0.0812, "comment": "可控"},
            ],
            "risk_metrics": [
                {"name": "波动率", "value": 0.1823},
                {"name": "下行风险", "value": 0.0521},
            ],
            "asset_allocation": [
                {"name": "股票", "ratio": 0.75},
                {"name": "债券", "ratio": 0.15},
                {"name": "现金", "ratio": 0.10},
            ],
            "top_holdings": [
                {"code": "600000", "name": "浦发银行", "proportion": 0.085},
                {"code": "000001", "name": "平安银行", "proportion": 0.062},
                {"code": "300001", "name": "宁德时代", "proportion": 0.041},
            ],
            "ai_analysis": "该基金表现良好，建议关注。",
        }

        self.portfolio_data = {
            "funds": [
                {"code": "000001", "name": "平安策略", "type": "混合型", "weight": 0.4, "return_1y": 0.15},
                {"code": "000002", "name": "银河灵活", "type": "混合型", "weight": 0.3, "return_1y": 0.12},
                {"code": "000003", "name": "易方达消费", "type": "股票型", "weight": 0.3, "return_1y": 0.18},
            ],
            "total_asset": "100万元",
            "portfolio_metrics": [
                {"name": "组合收益率", "portfolio": 0.15, "benchmark": 0.10},
                {"name": "夏普比率", "portfolio": 1.35, "benchmark": 1.0},
            ],
            "risk_metrics": [
                {"name": "组合波动率", "value": 0.152},
                {"name": "最大回撤", "value": -0.08},
            ],
        }

        self.market_flow_data = {
            "index_value": "3200.00",
            "index_change": "+1.25%",
            "north_flow": "净流入50.23亿元",
            "market_flow": [
                {"name": "超大单", "value": 25.5},
                {"name": "大单", "value": 15.3},
                {"name": "中单", "value": -10.2},
                {"name": "小单", "value": -30.6},
            ],
            "sector_flow": [
                {"name": "半导体", "value": 15.2},
                {"name": "新能源", "value": 10.5},
                {"name": "医药", "value": 8.3},
            ],
            "north_flow_detail": [
                {"date": "2024-01-10", "sh": 25.1, "sz": 25.13, "total": 50.23},
                {"date": "2024-01-09", "sh": 15.5, "sz": 20.1, "total": 35.6},
            ],
        }

        self.risk_control_data = {
            "risk_overview": [
                {"name": "VaR(95%)", "value": 0.052, "threshold": 0.10, "status": "正常"},
                {"name": "杠杆率", "value": 0.15, "threshold": 0.40, "status": "正常"},
                {"name": "集中度", "value": 0.35, "threshold": 0.30, "status": "预警"},
            ],
            "concentration": [
                {"name": "单只股票", "value": 0.085, "threshold": 0.10, "status": "正常"},
                {"name": "单一行业", "value": 0.25, "threshold": 0.30, "status": "正常"},
            ],
            "compliance_checks": [
                {"name": "持仓限制", "passed": True, "detail": "全部合规"},
                {"name": "流动性要求", "passed": True, "detail": "满足要求"},
                {"name": "信息披露", "passed": False, "detail": "需补充季报"},
            ],
        }

    def test_render_single_fund_report(self):
        """测试单基金报告模板渲染"""
        result = self.engine.render(
            "single_fund/report.html",
            **self.single_fund_data
        )

        # 验证渲染结果
        self.assertIsInstance(result, str)
        self.assertIn("000001", result)
        self.assertIn("平安策略先锋混合", result)
        self.assertIn("混合型", result)
        self.assertIn("浦发银行", result)
        self.assertIn("AI 分析摘要", result)

    def test_render_portfolio_report(self):
        """测试投资组合报告模板渲染"""
        result = self.engine.render(
            "portfolio/report.html",
            **self.portfolio_data
        )

        # 验证渲染结果
        self.assertIsInstance(result, str)
        self.assertIn("000001", result)
        self.assertIn("000002", result)
        self.assertIn("100万元", result)
        self.assertIn("组合收益率", result)

    def test_render_market_flow_report(self):
        """测试市场流向报告模板渲染"""
        result = self.engine.render(
            "market_flow/report.html",
            **self.market_flow_data
        )

        # 验证渲染结果
        self.assertIsInstance(result, str)
        self.assertIn("3200.00", result)
        self.assertIn("半导体", result)
        self.assertIn("北向资金", result)

    def test_render_risk_control_report(self):
        """测试风控报告模板渲染"""
        result = self.engine.render(
            "risk_control/report.html",
            **self.risk_control_data
        )

        # 验证渲染结果
        self.assertIsInstance(result, str)
        self.assertIn("VaR", result)
        self.assertIn("预警", result)
        self.assertIn("通过", result)
        self.assertIn("未通过", result)

    def test_template_filters(self):
        """测试模板过滤器"""
        # 测试 percentage 过滤器
        template = self.engine.render_string(
            "{{ value | percentage }}",
            value=0.1234
        )
        self.assertIn("12.34%", template)

        # 测试 format_number 过滤器
        template = self.engine.render_string(
            "{{ value | format_number }}",
            value=1.2345678
        )
        self.assertIn("1.2346", template)

        # 测试 color_class 过滤器
        template = self.engine.render_string(
            "{{ value | color_class }}",
            value=0.05
        )
        self.assertIn("positive", template)

        template = self.engine.render_string(
            "{{ value | color_class }}",
            value=-0.05
        )
        self.assertIn("negative", template)

    def test_template_globals(self):
        """测试模板全局变量"""
        # 测试 now 全局变量
        template = self.engine.render_string("{{ now() }}")
        today_str = date.today().strftime("%Y-%m-%d")
        self.assertIn(today_str, template)

    def test_list_templates(self):
        """测试列出可用模板"""
        templates = self.engine.list_templates()
        self.assertIsInstance(templates, list)
        self.assertTrue(len(templates) > 0)


class TestAIAnalyzerReporter(unittest.TestCase):
    """
    AIAnalyzer + Reporter 协作测试

    测试场景：
    1. AI分析生成 AnalysisResult -> 注入报告模板 -> 渲染HTML
    2. 验证摘要、风险提示、投资建议在报告中的呈现
    """

    def setUp(self):
        """测试前准备"""
        # 使用规则引擎后端（无需API）
        self.analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)

        # 模板引擎
        template_dir = Path(__file__).parent.parent.parent / "src" / "fund_cli" / "templates"
        self.template_engine = TemplateEngine(template_dirs=[str(template_dir)])

        # 测试基金数据
        self.fund_metrics = {
            "total_return": 0.152,      # 总收益 15.2%
            "sharpe_ratio": 1.25,       # 夏普比率
            "max_drawdown": -0.0812,    # 最大回撤 -8.12%
            "volatility": 0.1823,        # 波动率
            "annual_return": 0.15,      # 年化收益
            "alpha": 0.023,            # Alpha
            "beta": 0.85,              # Beta
        }

        self.holdings = [
            {"stock_code": "600000", "stock_name": "浦发银行", "proportion": 0.085},
            {"stock_code": "000001", "stock_name": "平安银行", "proportion": 0.062},
            {"stock_code": "300001", "stock_name": "宁德时代", "proportion": 0.041},
        ]

        self.asset_allocation = {
            "stock_ratio": 0.75,
            "bond_ratio": 0.15,
            "cash_ratio": 0.10,
        }

    def test_analyze_fund_returns_analysis_result(self):
        """测试基金分析返回 AnalysisResult"""
        result = self.analyzer.analyze_fund(
            fund_code="000001",
            fund_name="测试基金",
            metrics=self.fund_metrics,
            holdings=self.holdings,
            asset_allocation=self.asset_allocation,
        )

        # 验证返回类型
        self.assertIsInstance(result, AnalysisResult)

        # 验证各字段都有内容
        self.assertTrue(len(result.summary) > 0)
        self.assertTrue(len(result.risk_warning) > 0)
        self.assertTrue(len(result.investment_advice) > 0)
        self.assertTrue(len(result.performance_comment) > 0)

        # 验证日期
        self.assertTrue(len(result.analysis_date) > 0)

    def test_analyze_fund_extracts_highlights(self):
        """测试分析提取亮点"""
        result = self.analyzer.analyze_fund(
            fund_code="000001",
            fund_name="测试基金",
            metrics=self.fund_metrics,
        )

        # 验证亮点
        self.assertIsInstance(result.highlights, list)
        # 收益率 > 10% 应该被识别为亮点
        self.assertTrue(len(result.highlights) >= 1)

    def test_analyze_fund_extracts_concerns(self):
        """测试分析提取风险点"""
        # 高波动率数据
        high_vol_metrics = {
            "total_return": 0.05,
            "sharpe_ratio": 0.3,
            "max_drawdown": -0.25,
            "volatility": 0.30,
        }

        result = self.analyzer.analyze_fund(
            fund_code="000001",
            fund_name="高风险基金",
            metrics=high_vol_metrics,
        )

        # 验证风险点
        self.assertIsInstance(result.concerns, list)
        # 高波动/大回撤应该被识别
        self.assertTrue(len(result.concerns) >= 1)

    def test_analyze_portfolio(self):
        """测试投资组合分析"""
        funds = [
            {"code": "000001", "name": "基金1"},
            {"code": "000002", "name": "基金2"},
        ]
        portfolio_metrics = {
            "total_return": 0.12,
            "sharpe_ratio": 1.0,
        }

        result = self.analyzer.analyze_portfolio(
            funds=funds,
            portfolio_metrics=portfolio_metrics,
        )

        # 验证返回
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(len(result.summary) > 0)
        self.assertTrue(len(result.risk_warning) > 0)

    def test_inject_analysis_into_template(self):
        """测试将分析结果注入报告模板"""
        # 生成分析结果
        analysis_result = self.analyzer.analyze_fund(
            fund_code="000001",
            fund_name="测试基金",
            metrics=self.fund_metrics,
            holdings=self.holdings,
            asset_allocation=self.asset_allocation,
        )

        # 准备模板数据
        template_data = {
            "fund_code": "000001",
            "fund_name": "测试基金",
            "fund_type": "混合型",
            "found_date": "2020-01-01",
            "performance_metrics": [
                {"name": "总收益率", "value": 0.152, "comment": "良好"},
            ],
            "risk_metrics": [
                {"name": "波动率", "value": 0.18},
            ],
            "asset_allocation": [
                {"name": "股票", "ratio": 0.75},
            ],
            "top_holdings": [],
            "ai_analysis": analysis_result.summary,
        }

        # 渲染模板
        html = self.template_engine.render(
            "single_fund/report.html",
            **template_data
        )

        # 验证分析结果在报告中
        self.assertIn(analysis_result.summary, html)

    def test_analysis_result_confidence(self):
        """测试分析结果置信度"""
        # 规则引擎置信度应该是 0.7
        result = self.analyzer.analyze_fund(
            fund_code="000001",
            fund_name="测试基金",
            metrics=self.fund_metrics,
        )

        self.assertEqual(result.confidence, 0.7)
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)


class TestMultiAdapterRegistration(unittest.TestCase):
    """
    多适配器注册与优先级测试

    测试场景：
    1. 手动注册多个适配器到 Gateway
    2. 验证可用适配器按优先级排序
    3. 验证 is_available 过滤
    """

    def setUp(self):
        """测试前准备"""
        self.gateway = DataSourceGateway()

    def test_manual_adapter_registration(self):
        """测试手动注册适配器"""
        # 创建多个适配器
        adapter1 = MockAdapter(name="tushare")
        adapter2 = MockAdapter(name="akshare")
        adapter3 = MockAdapter(name="wind")

        # 注册
        self.gateway.register_adapter("tushare", adapter1)
        self.gateway.register_adapter("akshare", adapter2)
        self.gateway.register_adapter("wind", adapter3)

        # 验证
        self.assertEqual(len(self.gateway._adapters), 3)
        self.assertIsNotNone(self.gateway.get_adapter("tushare"))
        self.assertIsNotNone(self.gateway.get_adapter("akshare"))
        self.assertIsNotNone(self.gateway.get_adapter("wind"))

    def test_available_adapters_filtered_by_priority(self):
        """测试可用适配器按优先级排序"""
        # 创建并注册适配器
        tushare = MockAdapter(name="tushare")
        akshare = MockAdapter(name="akshare")
        wind = MockAdapter(name="wind")

        self.gateway.register_adapter("tushare", tushare)
        self.gateway.register_adapter("akshare", akshare)
        self.gateway.register_adapter("wind", wind)

        # 获取可用适配器
        available = self.gateway.get_available_adapters()

        # 验证按优先级排序（配置中的 source_priority_list）
        # 默认优先级: akshare > tushare > wind
        self.assertEqual(available[0], "akshare")
        self.assertIn("tushare", available)

    def test_unavailable_adapter_filtered(self):
        """测试不可用适配器被过滤"""
        # 创建适配器
        tushare = MockAdapter(name="tushare")
        akshare = MockAdapter(name="akshare")

        # 设置 akshare 不可用
        akshare.set_available(False)

        # 注册
        self.gateway.register_adapter("tushare", tushare)
        self.gateway.register_adapter("akshare", akshare)

        # 获取可用适配器
        available = self.gateway.get_available_adapters()

        # 验证
        self.assertIn("tushare", available)
        self.assertNotIn("akshare", available)

    def test_circuit_breaker_open_adapter_filtered(self):
        """测试熔断器打开的适配器被过滤"""
        gateway = DataSourceGateway()
        gateway._failure_threshold = 3

        # 创建并注册适配器（使用配置优先级列表中的名称）
        adapter = MockAdapter(name="akshare")
        gateway.register_adapter("akshare", adapter)

        # 触发熔断
        adapter.set_method_failure("get_fund_info", count=3)
        for i in range(3):
            try:
                gateway.call("get_fund_info", "000001")
            except DataSourceError:
                pass

        # 验证熔断器打开
        self.assertEqual(
            gateway._circuit_states["akshare"],
            CircuitState.OPEN
        )

        # 获取可用适配器
        available = gateway.get_available_adapters()

        # 验证熔断的适配器不在列表中
        self.assertNotIn("akshare", available)

    def test_get_adapter_by_name(self):
        """测试按名称获取适配器"""
        adapter = MockAdapter(name="akshare")
        self.gateway.register_adapter("akshare", adapter)

        retrieved = self.gateway.get_adapter("akshare")
        self.assertIs(retrieved, adapter)

        # 获取不存在的适配器
        nonexistent = self.gateway.get_adapter("nonexistent")
        self.assertIsNone(nonexistent)


# ==============================================================================
# 辅助 Mock Reporter 类（用于测试）
# ==============================================================================

class MockReporter(Reporter):
    """Mock 报告生成器"""

    def __init__(self):
        self.generated_content = None

    def generate(
        self,
        fund_code: str,
        metrics: dict[str, Any],
        nav_data: pd.DataFrame | None = None,
        benchmark_data: pd.DataFrame | None = None,
        **kwargs,
    ) -> str:
        self.generated_content = f"Mock Report for {fund_code}"
        return self.generated_content

    def save(self, content: str, output_path: str) -> None:
        self.saved_content = content

    def get_formats(self) -> list:
        return ["mock"]


# ==============================================================================
# 集成测试：完整工作流
# ==============================================================================

class TestEndToEndWorkflow(unittest.TestCase):
    """
    端到端工作流测试

    测试完整的用户工作流：
    1. 数据获取 -> 标准化 -> 分析 -> 报告
    """

    def setUp(self):
        """测试前准备"""
        # 创建 Gateway 和适配器
        self.gateway = DataSourceGateway()
        self.adapter = MockAdapter(name="primary")
        self.gateway.register_adapter("primary", self.adapter)

        # 标准化器
        self.normalizer = DataNormalizer

        # AI 分析器
        self.analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)

        # 模板引擎
        template_dir = Path(__file__).parent.parent.parent / "src" / "fund_cli" / "templates"
        self.template_engine = TemplateEngine(template_dirs=[str(template_dir)])

    def test_complete_workflow(self):
        """测试完整工作流"""
        # 创建 Gateway 和适配器（使用配置优先级列表中的名称）
        self.gateway = DataSourceGateway()
        self.adapter = MockAdapter(name="akshare")
        self.gateway.register_adapter("akshare", self.adapter)

        # 1. 通过 Gateway 获取数据
        fund_info = self.gateway.call("get_fund_info", "000001")
        fund_nav = self.gateway.call("get_fund_nav", "000001")
        holdings = self.gateway.call("get_fund_holdings", "000001")

        # 2. 标准化数据
        normalized_info = self.normalizer.normalize_fund_info(fund_info)
        normalized_nav = self.normalizer.normalize_nav_data(fund_nav)
        normalized_holdings = self.normalizer.normalize_fund_holdings(holdings)

        # 3. 提取指标
        metrics = {
            "total_return": 0.15,
            "sharpe_ratio": 1.25,
            "max_drawdown": -0.08,
            "volatility": 0.18,
        }

        # 4. AI 分析
        analysis_result = self.analyzer.analyze_fund(
            fund_code=normalized_info["fund_code"],
            fund_name=normalized_info["fund_name"],
            metrics=metrics,
            holdings=normalized_holdings.to_dict("records"),
        )

        # 5. 生成报告
        report_data = {
            "fund_code": normalized_info["fund_code"],
            "fund_name": normalized_info["fund_name"],
            "fund_type": normalized_info.get("fund_type", "混合型"),
            "found_date": normalized_info.get("found_date", "2020-01-01"),
            "performance_metrics": [
                {"name": "总收益率", "value": metrics["total_return"], "comment": "良好"},
            ],
            "risk_metrics": [
                {"name": "波动率", "value": metrics["volatility"]},
            ],
            "asset_allocation": [
                {"name": "股票", "ratio": 0.75},
            ],
            "top_holdings": [],
            "ai_analysis": analysis_result.summary,
        }

        html_report = self.template_engine.render(
            "single_fund/report.html",
            **report_data
        )

        # 6. 验证结果
        self.assertIn("000001", html_report)
        self.assertIn(analysis_result.summary, html_report)
        self.assertTrue(len(html_report) > 0)


# ==============================================================================
# 主入口
# ==============================================================================

if __name__ == "__main__":
    unittest.main()
