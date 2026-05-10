"""
AI 分析器测试.

测试 fund_cli.ai.analyzer 模块。
"""

import pytest
from unittest.mock import MagicMock, patch

from fund_cli.ai.analyzer import AIAnalyzer


@pytest.fixture
def mock_provider():
    """创建模拟 LLM 提供商."""
    provider = MagicMock()
    provider.generate.return_value = "AI 生成的分析结果"
    return provider


@pytest.fixture
def analyzer(mock_provider):
    """创建 AIAnalyzer 实例."""
    return AIAnalyzer(provider=mock_provider)


class TestAIAnalyzerInit:
    """测试 AIAnalyzer 初始化."""

    def test_init_with_provider(self, mock_provider):
        """测试使用自定义 provider 初始化."""
        analyzer = AIAnalyzer(provider=mock_provider)
        assert analyzer.provider is mock_provider

    @patch("fund_cli.ai.analyzer.get_provider")
    def test_init_with_default_provider(self, mock_get_provider):
        """测试使用默认 provider 初始化."""
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        analyzer = AIAnalyzer()

        assert analyzer.provider is mock_provider


class TestSummarizeFund:
    """测试 summarize_fund 方法."""

    def test_summarize_fund_success(self, analyzer, mock_provider):
        """测试生成基金摘要成功."""
        fund_data = {
            "info": {
                "name": "测试基金",
                "type": "混合型",
                "manager": "张三"
            },
            "metrics": {
                "total_return": 0.15,
                "cagr": 0.12,
                "sharpe_ratio": 1.2,
                "max_drawdown": -0.08,
                "volatility": 0.18
            }
        }

        result = analyzer.summarize_fund("000001", fund_data)

        assert result == "AI 生成的分析结果"
        mock_provider.generate.assert_called_once()

    def test_summarize_fund_with_missing_data(self, analyzer, mock_provider):
        """测试缺失数据时的摘要生成."""
        fund_data = {
            "info": {},
            "metrics": {}
        }

        result = analyzer.summarize_fund("000001", fund_data)

        assert result == "AI 生成的分析结果"
        mock_provider.generate.assert_called_once()

    def test_summarize_fund_empty_data(self, analyzer, mock_provider):
        """测试空数据时的摘要生成."""
        fund_data = {}

        result = analyzer.summarize_fund("000001", fund_data)

        assert result == "AI 生成的分析结果"
        mock_provider.generate.assert_called_once()


class TestCompareFunds:
    """测试 compare_funds 方法."""

    def test_compare_funds_success(self, analyzer, mock_provider):
        """测试对比分析成功."""
        fund_codes = ["000001", "000002"]
        funds_data = [
            {
                "info": {"name": "基金A", "type": "股票型"},
                "metrics": {"cagr": 0.15, "sharpe_ratio": 1.2, "max_drawdown": -0.08, "volatility": 0.18}
            },
            {
                "info": {"name": "基金B", "type": "债券型"},
                "metrics": {"cagr": 0.08, "sharpe_ratio": 0.8, "max_drawdown": -0.03, "volatility": 0.05}
            }
        ]

        result = analyzer.compare_funds(fund_codes, funds_data)

        assert result == "AI 生成的分析结果"
        mock_provider.generate.assert_called_once()

    def test_compare_funds_empty_list(self, analyzer, mock_provider):
        """测试空列表对比."""
        result = analyzer.compare_funds([], [])

        assert result == "AI 生成的分析结果"
        mock_provider.generate.assert_called_once()

    def test_compare_funds_single_fund(self, analyzer, mock_provider):
        """测试单只基金对比."""
        fund_codes = ["000001"]
        funds_data = [
            {"info": {"name": "基金A"}, "metrics": {"cagr": 0.15}}
        ]

        result = analyzer.compare_funds(fund_codes, funds_data)

        assert result == "AI 生成的分析结果"


class TestInvestmentAdvice:
    """测试 investment_advice 方法."""

    def test_investment_advice_success(self, analyzer, mock_provider):
        """测试投资建议生成成功."""
        mock_provider.generate.return_value = """
        {
            "suitability": "适合",
            "allocation": "20%",
            "risk_warning": "注意波动风险",
            "holding_period": "建议长期持有"
        }
        """

        fund_data = {
            "info": {"name": "测试基金"},
            "metrics": {"sharpe_ratio": 1.2, "max_drawdown": -0.08}
        }

        result = analyzer.investment_advice("000001", fund_data, "moderate")

        assert "suitability" in result
        assert "allocation" in result

    def test_investment_advice_invalid_json(self, analyzer, mock_provider):
        """测试返回无效 JSON 时的处理."""
        mock_provider.generate.return_value = "无效 JSON 文本"

        fund_data = {"info": {}, "metrics": {}}

        result = analyzer.investment_advice("000001", fund_data, "conservative")

        # 应该返回包含默认值的字典
        assert isinstance(result, dict)

    def test_investment_advice_different_risk_profiles(self, analyzer, mock_provider):
        """测试不同风险偏好."""
        mock_provider.generate.return_value = '{"suitability": "适合"}'

        fund_data = {"info": {}, "metrics": {}}

        for profile in ["conservative", "moderate", "aggressive"]:
            result = analyzer.investment_advice("000001", fund_data, profile)
            assert isinstance(result, dict)


class TestRiskAssessment:
    """测试 risk_assessment 方法."""

    def test_risk_assessment_success(self, analyzer, mock_provider):
        """测试风险评估成功."""
        mock_provider.generate.return_value = """
        {
            "overall_risk": "中等",
            "risk_factors": ["波动率较高", "回撤较大"],
            "suggestions": ["分散投资"]
        }
        """

        fund_data = {
            "info": {"name": "测试基金"},
            "nav": []
        }

        result = analyzer.risk_assessment("000001", fund_data)

        assert isinstance(result, dict)

    def test_risk_assessment_invalid_response(self, analyzer, mock_provider):
        """测试无效响应处理."""
        mock_provider.generate.return_value = "不是 JSON"

        fund_data = {"info": {}, "nav": []}

        result = analyzer.risk_assessment("000001", fund_data)

        assert isinstance(result, dict)


class TestMarketInsight:
    """测试 market_insight 方法."""

    def test_market_insight_success(self, analyzer, mock_provider):
        """测试市场解读成功."""
        fund_data = {
            "info": {"name": "测试基金", "type": "股票型"},
            "metrics": {"total_return": 0.15}
        }

        result = analyzer.market_insight("000001", fund_data)

        assert result == "AI 生成的分析结果"
        mock_provider.generate.assert_called_once()


class TestPortfolioReview:
    """测试 portfolio_review 方法."""

    def test_portfolio_review_success(self, analyzer, mock_provider):
        """测试组合评价成功."""
        mock_provider.generate.return_value = """
        {
            "overall_assessment": "组合配置合理",
            "recommendations": ["增加债券配置"],
            "risk_analysis": "风险适中"
        }
        """

        portfolio_data = {
            "funds": [
                {"code": "000001", "weight": 0.6},
                {"code": "000002", "weight": 0.4}
            ]
        }

        result = analyzer.portfolio_review(portfolio_data)

        assert "overall_assessment" in result

    def test_portfolio_review_empty_portfolio(self, analyzer, mock_provider):
        """测试空组合评价."""
        mock_provider.generate.return_value = '{}'

        portfolio_data = {"funds": []}

        result = analyzer.portfolio_review(portfolio_data)

        assert isinstance(result, dict)
