"""
投资组合诊断模块测试
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

from fund_cli.ai.portfolio_doctor import (
    PortfolioDoctor,
    PortfolioDiagnosis,
    DiagnosisItem,
    DiversificationAnalyzer,
    ConcentrationAnalyzer,
    CorrelationAnalyzer,
    RiskExposureAnalyzer,
    HealthLevel,
    DiagnosisCategory,
    diagnose_portfolio,
)


class TestDiversificationAnalyzer:
    """分散度分析器测试"""

    def setup_method(self):
        self.analyzer = DiversificationAnalyzer()

    def test_analyze_empty_weights(self):
        """测试空权重"""
        result = self.analyzer.analyze({})
        assert result.level == HealthLevel.CRITICAL
        assert result.score == 0

    def test_analyze_well_diversified(self):
        """测试良好分散"""
        weights = {"000001": 0.2, "000002": 0.2, "000003": 0.2, "000004": 0.2, "000005": 0.2}
        result = self.analyzer.analyze(weights)
        # 5只等权基金，有效持仓数量为5，应该是优秀或良好
        assert result.level in [HealthLevel.EXCELLENT, HealthLevel.GOOD]
        assert result.score >= 70

    def test_analyze_concentrated(self):
        """测试集中持仓"""
        weights = {"000001": 0.8, "000002": 0.2}
        result = self.analyzer.analyze(weights)
        assert result.level in [HealthLevel.POOR, HealthLevel.MODERATE]
        assert result.score < 80

    def test_analyze_single_fund(self):
        """测试单一持仓"""
        weights = {"000001": 1.0}
        result = self.analyzer.analyze(weights)
        assert result.level == HealthLevel.POOR
        assert result.score < 60


class TestConcentrationAnalyzer:
    """集中度分析器测试"""

    def setup_method(self):
        self.analyzer = ConcentrationAnalyzer()

    def test_analyze_empty_weights(self):
        """测试空权重"""
        result = self.analyzer.analyze({})
        assert result.level == HealthLevel.CRITICAL

    def test_analyze_balanced(self):
        """测试均衡配置"""
        weights = {"000001": 0.2, "000002": 0.2, "000003": 0.2, "000004": 0.2, "000005": 0.2}
        result = self.analyzer.analyze(weights)
        assert result.level == HealthLevel.EXCELLENT
        assert "top1_weight" in result.details

    def test_analyze_concentrated(self):
        """测试高集中度"""
        weights = {"000001": 0.6, "000002": 0.2, "000003": 0.2}
        result = self.analyzer.analyze(weights)
        assert result.level in [HealthLevel.MODERATE, HealthLevel.POOR]

    def test_analyze_highly_concentrated(self):
        """测试极高集中度"""
        weights = {"000001": 0.9, "000002": 0.1}
        result = self.analyzer.analyze(weights)
        assert result.level == HealthLevel.POOR


class TestCorrelationAnalyzer:
    """相关性分析器测试"""

    def setup_method(self):
        self.analyzer = CorrelationAnalyzer()

    def test_analyze_no_data(self):
        """测试无数据情况"""
        result = self.analyzer.analyze()
        assert result.level == HealthLevel.MODERATE

    def test_analyze_low_correlation(self):
        """测试低相关性"""
        # 创建低相关性矩阵
        correlations = pd.DataFrame(
            [[1.0, 0.2, 0.1], [0.2, 1.0, 0.15], [0.1, 0.15, 1.0]],
            columns=["A", "B", "C"],
            index=["A", "B", "C"],
        )
        result = self.analyzer.analyze(correlations=correlations)
        assert result.level == HealthLevel.EXCELLENT
        assert result.details["avg_correlation"] < 0.3

    def test_analyze_high_correlation(self):
        """测试高相关性"""
        # 创建高相关性矩阵
        correlations = pd.DataFrame(
            [[1.0, 0.9, 0.85], [0.9, 1.0, 0.88], [0.85, 0.88, 1.0]],
            columns=["A", "B", "C"],
            index=["A", "B", "C"],
        )
        result = self.analyzer.analyze(correlations=correlations)
        assert result.level in [HealthLevel.POOR, HealthLevel.MODERATE]


class TestRiskExposureAnalyzer:
    """风险敞口分析器测试"""

    def setup_method(self):
        self.analyzer = RiskExposureAnalyzer()

    def test_analyze_empty_weights(self):
        """测试空权重"""
        result = self.analyzer.analyze({})
        assert result.level == HealthLevel.CRITICAL

    def test_analyze_no_risk_data(self):
        """测试无风险数据"""
        weights = {"000001": 0.5, "000002": 0.5}
        result = self.analyzer.analyze(weights)
        assert result.level == HealthLevel.MODERATE

    def test_analyze_balanced_risk(self):
        """测试均衡风险"""
        weights = {"000001": 0.5, "000002": 0.5}
        fund_risks = {"000001": 15.0, "000002": 15.0}
        result = self.analyzer.analyze(weights, fund_risks)
        assert result.level in [HealthLevel.EXCELLENT, HealthLevel.GOOD]

    def test_analyze_concentrated_risk(self):
        """测试风险集中"""
        weights = {"000001": 0.2, "000002": 0.8}
        fund_risks = {"000001": 10.0, "000002": 30.0}
        result = self.analyzer.analyze(weights, fund_risks)
        # 高风险资产权重高，风险贡献集中
        assert "max_contributor" in result.details


class TestPortfolioDoctor:
    """组合诊断器测试"""

    def setup_method(self):
        self.doctor = PortfolioDoctor()

    def test_diagnose_empty_portfolio(self):
        """测试空组合"""
        result = self.doctor.diagnose([])
        assert result.overall_level == HealthLevel.CRITICAL

    def test_diagnose_simple_portfolio(self):
        """测试简单组合"""
        result = self.doctor.diagnose(["000001", "000002"])
        assert isinstance(result, PortfolioDiagnosis)
        assert len(result.diagnoses) >= 3
        assert result.overall_score >= 0

    def test_diagnose_with_weights(self):
        """测试带权重组合"""
        result = self.doctor.diagnose(
            ["000001", "000002", "000003"], weights=[0.5, 0.3, 0.2]
        )
        assert isinstance(result, PortfolioDiagnosis)
        assert result.portfolio_stats["fund_count"] == 3

    def test_format_diagnosis(self):
        """测试格式化诊断报告"""
        result = self.doctor.diagnose(["000001", "000002"])
        formatted = self.doctor.format_diagnosis(result)

        assert "整体评估" in formatted
        assert "健康评分" in formatted
        assert "详细诊断" in formatted


class TestDiagnosisItem:
    """诊断项测试"""

    def test_diagnosis_item_creation(self):
        """测试诊断项创建"""
        item = DiagnosisItem(
            category=DiagnosisCategory.DIVERSIFICATION,
            level=HealthLevel.GOOD,
            score=75,
            description="分散度良好",
            details={"effective_n": 3.5},
            suggestions=["建议增加持仓"],
        )

        assert item.category == DiagnosisCategory.DIVERSIFICATION
        assert item.level == HealthLevel.GOOD
        assert item.score == 75
        assert len(item.suggestions) == 1


class TestPortfolioDiagnosis:
    """组合诊断报告测试"""

    def test_diagnosis_creation(self):
        """测试诊断报告创建"""
        diagnosis = PortfolioDiagnosis(
            overall_score=75.0,
            overall_level=HealthLevel.GOOD,
            diagnoses=[],
            risk_warnings=["风险提示1"],
            optimization_suggestions=["建议1", "建议2"],
            portfolio_stats={"fund_count": 3},
        )

        assert diagnosis.overall_score == 75.0
        assert diagnosis.overall_level == HealthLevel.GOOD
        assert len(diagnosis.optimization_suggestions) == 2


class TestHealthLevel:
    """健康等级测试"""

    def test_health_levels(self):
        """测试健康等级枚举"""
        assert HealthLevel.EXCELLENT.value == "优秀"
        assert HealthLevel.GOOD.value == "良好"
        assert HealthLevel.MODERATE.value == "一般"
        assert HealthLevel.POOR.value == "较差"
        assert HealthLevel.CRITICAL.value == "危险"


def test_diagnose_portfolio_convenience_function():
    """测试便捷函数"""
    result = diagnose_portfolio(["000001", "000002"])
    assert isinstance(result, PortfolioDiagnosis)
