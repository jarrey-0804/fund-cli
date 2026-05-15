"""
压力测试模块测试
"""


import pytest

from fund_cli.analysis.stress_test import (
    HISTORICAL_SCENARIOS,
    CustomScenarioEngine,
    HistoricalScenarioEngine,
    StressScenario,
    StressTester,
    StressTestReport,
    StressTestResult,
    run_stress_test,
)


class TestHistoricalScenarioEngine:
    """历史情景引擎测试"""

    def setup_method(self):
        self.engine = HistoricalScenarioEngine()

    def test_run_crisis_2008(self):
        """测试2008金融危机情景"""
        result = self.engine.run(StressScenario.CRISIS_2008, beta=1.0)

        assert isinstance(result, StressTestResult)
        assert result.scenario_type == StressScenario.CRISIS_2008
        assert result.portfolio_loss < 0  # 应该是损失

    def test_run_with_high_beta(self):
        """测试高Beta基金"""
        result = self.engine.run(StressScenario.CRISIS_2008, beta=1.5)

        # 高Beta应该有更大的损失
        assert result.portfolio_loss < -40

    def test_run_with_low_beta(self):
        """测试低Beta基金"""
        result = self.engine.run(StressScenario.CRISIS_2008, beta=0.5)

        # 低Beta应该有较小的损失
        assert result.portfolio_loss > -30

    def test_var_breach_detection(self):
        """测试VaR突破检测"""
        # 高Beta可能导致VaR突破
        result = self.engine.run(StressScenario.CRISIS_2008, beta=1.5)
        # 检查VaR突破字段存在
        assert hasattr(result, "var_breach")

    def test_custom_scenario_raises_error(self):
        """测试自定义情景应该抛出错误"""
        with pytest.raises(ValueError):
            self.engine.run(StressScenario.CUSTOM)


class TestCustomScenarioEngine:
    """自定义情景引擎测试"""

    def setup_method(self):
        self.engine = CustomScenarioEngine()

    def test_run_market_shock(self):
        """测试市场冲击"""
        result = self.engine.run(shock_percent=-30.0, beta=1.0)

        assert isinstance(result, StressTestResult)
        assert result.scenario_type == StressScenario.CUSTOM
        assert result.portfolio_loss == pytest.approx(-30.0, rel=0.1)

    def test_run_with_beta(self):
        """测试带Beta的自定义冲击"""
        result = self.engine.run(shock_percent=-20.0, beta=1.5)

        # Beta放大冲击
        assert result.portfolio_loss < -20.0

    def test_run_sector_shock(self):
        """测试行业冲击"""
        result = self.engine.run(shock_percent=-15.0, beta=1.0, shock_type="sector")

        assert isinstance(result, StressTestResult)
        assert "行业" in result.scenario_name or "sector" in result.scenario_name.lower()

    def test_run_rate_shock(self):
        """测试利率冲击"""
        result = self.engine.run(shock_percent=-10.0, beta=1.0, shock_type="rate")

        assert isinstance(result, StressTestResult)


class TestStressTester:
    """压力测试主类测试"""

    def setup_method(self):
        self.tester = StressTester()

    def test_run_single_scenario(self):
        """测试单一情景"""
        result = self.tester.run_single(StressScenario.PANDEMIC_2020, beta=1.0)

        assert isinstance(result, StressTestResult)
        assert result.scenario_type == StressScenario.PANDEMIC_2020

    def test_run_all_scenarios(self):
        """测试所有情景"""
        results = self.tester.run_all(beta=1.0)

        assert isinstance(results, list)
        assert len(results) >= 5  # 至少5个预设情景

    def test_generate_report(self):
        """测试生成报告"""
        report = self.tester.generate_report(
            fund_code="000001",
            fund_name="测试基金",
            beta=1.0,
        )

        assert isinstance(report, StressTestReport)
        assert report.fund_code == "000001"
        assert len(report.results) > 0
        assert report.worst_case is not None

    def test_format_report(self):
        """测试格式化报告"""
        report = self.tester.generate_report("000001", "测试基金", beta=1.0)
        formatted = self.tester.format_report(report)

        assert "压力测试报告" in formatted
        assert "综合评估" in formatted


class TestStressScenario:
    """压力情景枚举测试"""

    def test_scenario_values(self):
        """测试情景枚举值"""
        assert StressScenario.CRISIS_2008.value == "2008金融危机"
        assert StressScenario.CRASH_2015.value == "2015股灾"
        assert StressScenario.PANDEMIC_2020.value == "2020疫情"
        assert StressScenario.CUSTOM.value == "自定义"


class TestHistoricalScenarios:
    """历史情景数据库测试"""

    def test_scenarios_exist(self):
        """测试情景数据存在"""
        assert StressScenario.CRISIS_2008 in HISTORICAL_SCENARIOS
        assert StressScenario.CRASH_2015 in HISTORICAL_SCENARIOS
        assert StressScenario.PANDEMIC_2020 in HISTORICAL_SCENARIOS

    def test_scenario_details(self):
        """测试情景详情"""
        scenario = HISTORICAL_SCENARIOS[StressScenario.CRISIS_2008]
        assert scenario.market_shock < 0
        assert len(scenario.affected_sectors) > 0
        assert scenario.recovery_days > 0


class TestStressTestResult:
    """压力测试结果测试"""

    def test_result_creation(self):
        """测试结果创建"""
        result = StressTestResult(
            scenario_name="测试情景",
            scenario_type=StressScenario.CUSTOM,
            portfolio_loss=-25.0,
            portfolio_recovery_days=180,
            var_breach=True,
            max_drawdown=-25.0,
            sensitivity={"市场敏感度": 1.2},
            risk_warning="高风险",
            hedging_suggestion="建议对冲",
        )

        assert result.scenario_name == "测试情景"
        assert result.portfolio_loss == -25.0
        assert result.var_breach is True


def test_run_stress_test_convenience():
    """测试便捷函数"""
    result = run_stress_test("000001", scenario="2008金融危机", beta=1.0)
    assert isinstance(result, StressTestResult)


def test_run_stress_test_all():
    """测试运行所有情景"""
    report = run_stress_test("000001", scenario="all", beta=1.0)
    assert isinstance(report, StressTestReport)
