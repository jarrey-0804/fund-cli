"""
风险预算模块测试
"""

import numpy as np
import pandas as pd

from fund_cli.analysis.risk_budget import (
    OptimizationObjective,
    RiskBudgetAnalyzer,
    RiskBudgetOptimizer,
    RiskBudgetReport,
    RiskConcentrationAnalyzer,
    RiskContribution,
    RiskContributionCalculator,
    RiskMeasure,
    TailRiskAnalyzer,
    TailRiskContribution,
    analyze_risk_budget,
    optimize_risk_parity,
)


class TestRiskContributionCalculator:
    """风险贡献计算器测试"""

    def setup_method(self):
        self.calculator = RiskContributionCalculator()

    def test_calculate_empty_weights(self):
        """测试空权重"""
        result = self.calculator.calculate({})
        assert result == []

    def test_calculate_with_weights_only(self):
        """测试仅有权重"""
        weights = {"000001": 0.5, "000002": 0.5}
        result = self.calculator.calculate(weights)

        assert len(result) == 2
        assert all(isinstance(r, RiskContribution) for r in result)

    def test_calculate_with_volatilities(self):
        """测试带波动率计算"""
        weights = {"000001": 0.6, "000002": 0.4}
        volatilities = {"000001": 0.20, "000002": 0.15}

        result = self.calculator.calculate(weights, volatilities=volatilities)

        assert len(result) == 2
        # 波动率高的资产应该有更高的风险贡献
        assert result[0].risk_contribution >= result[1].risk_contribution

    def test_calculate_with_returns(self):
        """测试带收益率数据计算"""
        weights = {"A": 0.5, "B": 0.5}
        returns = pd.DataFrame(
            {
                "A": np.random.randn(100) * 0.01,
                "B": np.random.randn(100) * 0.01,
            }
        )

        result = self.calculator.calculate(weights, returns=returns)

        assert len(result) == 2
        assert all(r.risk_contribution_pct >= 0 for r in result)

    def test_risk_contribution_sum(self):
        """测试风险贡献总和"""
        weights = {"000001": 0.5, "000002": 0.3, "000003": 0.2}
        result = self.calculator.calculate(weights)

        total_pct = sum(r.risk_contribution_pct for r in result)
        assert abs(total_pct - 100) < 1  # 应该接近100%


class TestRiskConcentrationAnalyzer:
    """风险集中度分析器测试"""

    def setup_method(self):
        self.analyzer = RiskConcentrationAnalyzer()

    def test_analyze_empty_contributions(self):
        """测试空贡献"""
        result = self.analyzer.analyze([])
        assert result.portfolio_risk == 0
        assert result.diversification_score == 0

    def test_analyze_balanced_contributions(self):
        """测试均衡贡献"""
        contributions = [
            RiskContribution("A", "A", 0.33, 0.1, 0.033, 33.0),
            RiskContribution("B", "B", 0.33, 0.1, 0.033, 33.0),
            RiskContribution("C", "C", 0.34, 0.1, 0.034, 34.0),
        ]

        result = self.analyzer.analyze(contributions)

        assert result.effective_risk_assets > 2
        # 有效风险资产数为3时，评分应为60（>=3但<4）
        assert result.diversification_score >= 60

    def test_analyze_concentrated_contributions(self):
        """测试集中贡献"""
        contributions = [
            RiskContribution("A", "A", 0.8, 0.15, 0.12, 80.0),
            RiskContribution("B", "B", 0.2, 0.03, 0.03, 20.0),
        ]

        result = self.analyzer.analyze(contributions)

        assert result.risk_concentration > 0.5
        assert result.effective_risk_assets < 2


class TestTailRiskAnalyzer:
    """尾部风险分析器测试"""

    def setup_method(self):
        self.analyzer = TailRiskAnalyzer()

    def test_analyze_empty_weights(self):
        """测试空权重"""
        result = self.analyzer.analyze({})
        assert result == []

    def test_analyze_no_returns(self):
        """测试无收益率数据"""
        result = self.analyzer.analyze({"A": 0.5, "B": 0.5})
        assert result == []

    def test_analyze_with_returns(self):
        """测试带收益率数据"""
        np.random.seed(42)
        weights = {"A": 0.5, "B": 0.5}
        returns = pd.DataFrame(
            {
                "A": np.random.randn(100) * 0.02,
                "B": np.random.randn(100) * 0.02,
            }
        )

        result = self.analyzer.analyze(weights, returns)

        assert isinstance(result, list)
        if result:  # 可能为空如果数据不足
            assert all(isinstance(r, TailRiskContribution) for r in result)


class TestRiskBudgetOptimizer:
    """风险预算优化器测试"""

    def setup_method(self):
        self.optimizer = RiskBudgetOptimizer()

    def test_optimize_empty(self):
        """测试空输入"""
        result = self.optimizer.optimize()
        assert result == {}

    def test_optimize_risk_parity(self):
        """测试风险平价优化"""
        volatilities = {"A": 0.20, "B": 0.10, "C": 0.15}

        result = self.optimizer.optimize(
            volatilities=volatilities,
            objective=OptimizationObjective.RISK_PARITY,
        )

        assert len(result) == 3
        # 波动率低的资产应该有更高的权重
        assert result["B"] > result["A"]

    def test_optimize_min_variance(self):
        """测试最小方差优化"""
        volatilities = {"A": 0.20, "B": 0.10}

        result = self.optimizer.optimize(
            volatilities=volatilities,
            objective=OptimizationObjective.MIN_VARIANCE,
        )

        assert len(result) == 2
        # 权重总和应该为1
        total = sum(result.values())
        assert abs(total - 1.0) < 0.01

    def test_optimize_with_returns(self):
        """测试带收益率数据优化"""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "A": np.random.randn(100) * 0.02,
                "B": np.random.randn(100) * 0.01,
            }
        )

        result = self.optimizer.optimize(returns=returns)

        assert len(result) == 2


class TestRiskBudgetAnalyzer:
    """风险预算分析主类测试"""

    def setup_method(self):
        self.analyzer = RiskBudgetAnalyzer()

    def test_analyze_simple_portfolio(self):
        """测试简单组合"""
        report = self.analyzer.analyze(["000001", "000002"])

        assert isinstance(report, RiskBudgetReport)
        assert len(report.risk_contributions) == 2

    def test_analyze_with_weights(self):
        """测试带权重分析"""
        report = self.analyzer.analyze(
            ["000001", "000002", "000003"],
            weights=[0.5, 0.3, 0.2],
        )

        assert isinstance(report, RiskBudgetReport)
        assert len(report.risk_contributions) == 3

    def test_optimize_weights(self):
        """测试权重优化"""
        result = self.analyzer.optimize_weights(
            ["A", "B", "C"],
            volatilities={"A": 0.20, "B": 0.15, "C": 0.10},
        )

        assert isinstance(result, dict)
        assert len(result) == 3

    def test_format_report(self):
        """测试格式化报告"""
        report = self.analyzer.analyze(["000001", "000002"])
        formatted = self.analyzer.format_report(report)

        assert "风险预算分析报告" in formatted
        assert "风险贡献分析" in formatted


class TestRiskContribution:
    """风险贡献测试"""

    def test_contribution_creation(self):
        """测试贡献创建"""
        contrib = RiskContribution(
            asset_code="000001",
            asset_name="测试基金",
            weight=0.5,
            marginal_risk=0.08,
            risk_contribution=0.04,
            risk_contribution_pct=50.0,
            risk_type="波动率",
        )

        assert contrib.asset_code == "000001"
        assert contrib.weight == 0.5
        assert contrib.risk_contribution_pct == 50.0


class TestTailRiskContribution:
    """尾部风险贡献测试"""

    def test_tail_risk_creation(self):
        """测试尾部风险创建"""
        tail = TailRiskContribution(
            asset_code="000001",
            var_contribution=45.0,
            cvar_contribution=50.0,
            tail_risk_ratio=0.5,
        )

        assert tail.asset_code == "000001"
        assert tail.var_contribution == 45.0


class TestOptimizationObjective:
    """优化目标枚举测试"""

    def test_objective_values(self):
        """测试目标枚举值"""
        assert OptimizationObjective.EQUAL_RISK.value == "等风险贡献"
        assert OptimizationObjective.MIN_VARIANCE.value == "最小方差"
        assert OptimizationObjective.MAX_SHARPE.value == "最大夏普"
        assert OptimizationObjective.RISK_PARITY.value == "风险平价"


class TestRiskMeasure:
    """风险度量枚举测试"""

    def test_measure_values(self):
        """测试度量枚举值"""
        assert RiskMeasure.VOLATILITY.value == "波动率"
        assert RiskMeasure.VAR.value == "VaR"
        assert RiskMeasure.CVAR.value == "CVaR"


def test_analyze_risk_budget_convenience():
    """测试便捷函数"""
    report = analyze_risk_budget(["000001", "000002", "000003"])
    assert isinstance(report, RiskBudgetReport)


def test_optimize_risk_parity_convenience():
    """测试风险平价便捷函数"""
    result = optimize_risk_parity(
        ["A", "B"],
        volatilities={"A": 0.20, "B": 0.10},
    )
    assert isinstance(result, dict)
