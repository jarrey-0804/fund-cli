"""
情景分析模块测试
"""


import pytest

from fund_cli.analysis.scenario_analysis import (
    BullBearAnalyzer,
    InvestmentStyle,
    MarketScenario,
    ProbabilityWeightedAnalyzer,
    RateSensitivityAnalyzer,
    ScenarioAnalysisReport,
    ScenarioAnalyzer,
    ScenarioMetrics,
    ScenarioResult,
    StyleRotationAnalyzer,
    analyze_scenarios,
)


class TestBullBearAnalyzer:
    """牛熊市分析器测试"""

    def setup_method(self):
        self.analyzer = BullBearAnalyzer()

    def test_analyze_default(self):
        """测试默认分析"""
        results = self.analyzer.analyze()

        assert MarketScenario.BULL_MARKET in results
        assert MarketScenario.BEAR_MARKET in results
        assert MarketScenario.SIDEWAYS in results

    def test_analyze_with_beta(self):
        """测试带Beta分析"""
        results = self.analyzer.analyze(beta=1.5)

        # 高Beta在牛市应该有更高收益
        bull_metrics = results[MarketScenario.BULL_MARKET]
        assert bull_metrics.expected_return > 30  # 超过市场平均

    def test_analyze_with_alpha(self):
        """测试带Alpha分析"""
        results = self.analyzer.analyze(beta=1.0, alpha=5.0)

        # Alpha增加收益
        bull_metrics = results[MarketScenario.BULL_MARKET]
        assert bull_metrics.expected_return > 30

    def test_metrics_structure(self):
        """测试指标结构"""
        results = self.analyzer.analyze()
        metrics = results[MarketScenario.BULL_MARKET]

        assert hasattr(metrics, "expected_return")
        assert hasattr(metrics, "expected_volatility")
        assert hasattr(metrics, "sharpe_ratio")
        assert hasattr(metrics, "win_rate")


class TestRateSensitivityAnalyzer:
    """利率敏感度分析器测试"""

    def setup_method(self):
        self.analyzer = RateSensitivityAnalyzer()

    def test_analyze_default(self):
        """测试默认分析"""
        results = self.analyzer.analyze()

        assert MarketScenario.RATE_RISE in results
        assert MarketScenario.RATE_FALL in results

    def test_analyze_with_duration(self):
        """测试带久期分析"""
        results = self.analyzer.analyze(duration=7.0)

        # 长久期在利率上行时损失更大
        rise_metrics = results[MarketScenario.RATE_RISE]
        assert rise_metrics.expected_return < -5

    def test_short_duration(self):
        """测试短久期"""
        results = self.analyzer.analyze(duration=2.0)

        rise_metrics = results[MarketScenario.RATE_RISE]
        assert rise_metrics.expected_return > -3  # 损失较小


class TestStyleRotationAnalyzer:
    """风格轮动分析器测试"""

    def setup_method(self):
        self.analyzer = StyleRotationAnalyzer()

    def test_analyze_value_style(self):
        """测试价值风格"""
        results = self.analyzer.analyze(InvestmentStyle.VALUE, market_return=10.0)

        assert "牛市预期收益" in results
        assert "熊市预期收益" in results
        assert "风格优势" in results

    def test_analyze_growth_style(self):
        """测试成长风格"""
        results = self.analyzer.analyze(InvestmentStyle.GROWTH, market_return=10.0)

        # 成长风格在牛市表现更好
        assert results["牛市预期收益"] > 10.0

    def test_analyze_small_cap_style(self):
        """测试小盘风格"""
        results = self.analyzer.analyze(InvestmentStyle.SMALL_CAP, market_return=10.0)

        # 小盘在牛市弹性大
        assert results["牛市预期收益"] > results["熊市预期收益"]


class TestProbabilityWeightedAnalyzer:
    """概率加权分析器测试"""

    def setup_method(self):
        self.analyzer = ProbabilityWeightedAnalyzer()

    def test_analyze_default(self):
        """测试默认分析"""
        scenario_results = {
            MarketScenario.BULL_MARKET: ScenarioMetrics(
                expected_return=30.0,
                expected_volatility=18.0,
                expected_drawdown=-10.0,
                sharpe_ratio=1.5,
                win_rate=70.0,
                probability=35.0,
            ),
            MarketScenario.BEAR_MARKET: ScenarioMetrics(
                expected_return=-25.0,
                expected_volatility=25.0,
                expected_drawdown=-25.0,
                sharpe_ratio=-1.0,
                win_rate=30.0,
                probability=25.0,
            ),
        }

        results = self.analyzer.analyze(scenario_results)

        assert "加权预期收益" in results
        assert "加权预期波动率" in results
        assert "综合夏普比率" in results

    def test_analyze_with_custom_probabilities(self):
        """测试自定义概率"""
        scenario_results = {
            MarketScenario.BULL_MARKET: ScenarioMetrics(
                expected_return=30.0,
                expected_volatility=18.0,
                expected_drawdown=-10.0,
                sharpe_ratio=1.5,
                win_rate=70.0,
                probability=35.0,
            ),
        }
        custom_probs = {MarketScenario.BULL_MARKET: 100.0}

        results = self.analyzer.analyze(scenario_results, custom_probs)

        # 100%牛市概率，收益应该等于牛市收益
        assert results["加权预期收益"] == pytest.approx(30.0, rel=0.1)


class TestScenarioAnalyzer:
    """情景分析主类测试"""

    def setup_method(self):
        self.analyzer = ScenarioAnalyzer()

    def test_analyze_equity_fund(self):
        """测试股票型基金分析"""
        report = self.analyzer.analyze(
            fund_code="000001",
            fund_name="测试基金",
            fund_type="股票型",
            beta=1.2,
        )

        assert isinstance(report, ScenarioAnalysisReport)
        assert report.fund_code == "000001"
        assert len(report.results) > 0

    def test_analyze_bond_fund(self):
        """测试债券型基金分析"""
        report = self.analyzer.analyze(
            fund_code="000002",
            fund_name="债券基金",
            fund_type="债券型",
            duration=5.0,
        )

        assert isinstance(report, ScenarioAnalysisReport)
        # 债券基金应该有利率情景分析
        scenario_types = [r.scenario for r in report.results]
        assert MarketScenario.RATE_RISE in scenario_types or MarketScenario.RATE_FALL in scenario_types

    def test_best_worst_scenario(self):
        """测试最佳最差情景"""
        report = self.analyzer.analyze("000001", fund_type="股票型", beta=1.0)

        assert report.best_scenario is not None
        assert report.worst_scenario is not None

    def test_format_report(self):
        """测试格式化报告"""
        report = self.analyzer.analyze("000001", "测试基金")
        formatted = self.analyzer.format_report(report)

        assert "情景分析报告" in formatted
        assert "综合评估" in formatted


class TestMarketScenario:
    """市场情景枚举测试"""

    def test_scenario_values(self):
        """测试情景枚举值"""
        assert MarketScenario.BULL_MARKET.value == "牛市"
        assert MarketScenario.BEAR_MARKET.value == "熊市"
        assert MarketScenario.SIDEWAYS.value == "震荡市"
        assert MarketScenario.RATE_RISE.value == "利率上行"


class TestInvestmentStyle:
    """投资风格枚举测试"""

    def test_style_values(self):
        """测试风格枚举值"""
        assert InvestmentStyle.VALUE.value == "价值"
        assert InvestmentStyle.GROWTH.value == "成长"
        assert InvestmentStyle.BALANCED.value == "平衡"


class TestScenarioMetrics:
    """情景指标测试"""

    def test_metrics_creation(self):
        """测试指标创建"""
        metrics = ScenarioMetrics(
            expected_return=15.0,
            expected_volatility=20.0,
            expected_drawdown=-12.0,
            sharpe_ratio=0.75,
            win_rate=55.0,
            probability=40.0,
        )

        assert metrics.expected_return == 15.0
        assert metrics.sharpe_ratio == 0.75


class TestScenarioResult:
    """情景分析结果测试"""

    def test_result_creation(self):
        """测试结果创建"""
        metrics = ScenarioMetrics(
            expected_return=20.0,
            expected_volatility=15.0,
            expected_drawdown=-8.0,
            sharpe_ratio=1.2,
            win_rate=65.0,
            probability=35.0,
        )

        result = ScenarioResult(
            scenario=MarketScenario.BULL_MARKET,
            metrics=metrics,
            performance_rank=1,
            style_fit="高度匹配",
            analysis="牛市表现优异",
            suggestions=["可适当增加仓位"],
        )

        assert result.scenario == MarketScenario.BULL_MARKET
        assert result.performance_rank == 1


def test_analyze_scenarios_convenience():
    """测试便捷函数"""
    report = analyze_scenarios("000001", fund_type="股票型", beta=1.0)
    assert isinstance(report, ScenarioAnalysisReport)
