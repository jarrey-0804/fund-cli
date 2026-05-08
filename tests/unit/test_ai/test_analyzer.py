"""
AI分析器单元测试
"""

import pytest

from fund_cli.ai.analyzer import AIAnalyzer
from fund_cli.ai.providers import LLMProvider


class MockLLMProvider(LLMProvider):
    """测试用Mock提供商"""

    def __init__(self):
        # 不调用父类初始化，避免配置依赖
        self.mock_response = "Mock AI response"

    def generate(self, prompt, **kwargs):
        return self.mock_response

    def is_available(self):
        return True

    def validate_config(self):
        return True


@pytest.fixture
def mock_provider():
    """Mock LLM提供商"""
    return MockLLMProvider()


@pytest.fixture
def sample_fund_data():
    """示例基金数据"""
    return {
        "info": {
            "name": "测试基金",
            "type": "股票型",
            "manager": "张三",
        },
        "metrics": {
            "total_return": 15.5,
            "cagr": 12.3,
            "sharpe_ratio": 1.2,
            "max_drawdown": -8.5,
            "volatility": 18.2,
        },
    }


@pytest.fixture
def sample_funds_data():
    """示例多只基金数据"""
    return [
        {
            "code": "000001",
            "info": {"name": "基金A", "type": "股票型"},
            "metrics": {
                "cagr": 12.0,
                "sharpe_ratio": 1.1,
                "max_drawdown": -10.0,
                "volatility": 20.0,
            },
        },
        {
            "code": "000002",
            "info": {"name": "基金B", "type": "债券型"},
            "metrics": {"cagr": 6.0, "sharpe_ratio": 0.8, "max_drawdown": -3.0, "volatility": 5.0},
        },
    ]


class TestAIAnalyzer:
    """AIAnalyzer测试"""

    def test_init_with_provider(self, mock_provider):
        """测试使用提供商初始化"""
        analyzer = AIAnalyzer(mock_provider)
        assert analyzer.provider == mock_provider

    def test_summarize_fund(self, mock_provider, sample_fund_data):
        """测试基金摘要生成"""
        analyzer = AIAnalyzer(mock_provider)
        result = analyzer.summarize_fund("000001", sample_fund_data)

        assert result == "Mock AI response"

    def test_compare_funds(self, mock_provider, sample_funds_data):
        """测试基金对比分析"""
        analyzer = AIAnalyzer(mock_provider)
        codes = ["000001", "000002"]
        result = analyzer.compare_funds(codes, sample_funds_data)

        assert result == "Mock AI response"

    def test_investment_advice(self, mock_provider, sample_fund_data):
        """测试投资建议生成"""
        mock_provider.mock_response = '{"suitability": "是", "allocation": "20%", "risk_warning": "中等风险", "holding_period": "长期"}'

        analyzer = AIAnalyzer(mock_provider)
        result = analyzer.investment_advice("000001", sample_fund_data, "moderate")

        assert result["suitability"] == "是"
        assert result["allocation"] == "20%"

    def test_investment_advice_invalid_json(self, mock_provider, sample_fund_data):
        """测试投资建议返回非JSON时的处理"""
        mock_provider.mock_response = "Plain text response"

        analyzer = AIAnalyzer(mock_provider)
        result = analyzer.investment_advice("000001", sample_fund_data, "moderate")

        assert "raw_response" in result
        assert result["raw_response"] == "Plain text response"

    def test_risk_assessment(self, mock_provider, sample_fund_data):
        """测试风险评估"""
        mock_provider.mock_response = '{"risk_level": "中", "main_risks": "市场波动", "warnings": "注意回撤", "control_suggestions": "分散投资"}'

        analyzer = AIAnalyzer(mock_provider)
        result = analyzer.risk_assessment("000001", sample_fund_data)

        assert result["risk_level"] == "中"
        assert result["main_risks"] == "市场波动"

    def test_market_insight(self, mock_provider, sample_fund_data):
        """测试市场解读"""
        analyzer = AIAnalyzer(mock_provider)
        result = analyzer.market_insight("000001", sample_fund_data, "市场震荡")

        assert result == "Mock AI response"

    def test_portfolio_review(self, mock_provider):
        """测试组合分析"""
        mock_provider.mock_response = '{"overall_assessment": "组合良好", "optimization_suggestions": "增加债券比例", "diversification": "分散度适中"}'

        portfolio_data = {
            "funds": [
                {"code": "000001", "metrics": {"cagr": 10.0, "sharpe_ratio": 1.0}},
                {"code": "000002", "metrics": {"cagr": 5.0, "sharpe_ratio": 0.8}},
            ],
            "weights": [0.6, 0.4],
        }

        analyzer = AIAnalyzer(mock_provider)
        result = analyzer.portfolio_review(portfolio_data)

        assert result["overall_assessment"] == "组合良好"

    def test_generate_report(self, mock_provider, sample_fund_data):
        """测试生成报告"""
        analyzer = AIAnalyzer(mock_provider)
        result = analyzer.generate_report(
            "000001", sample_fund_data["info"], sample_fund_data["metrics"]
        )

        assert result == "Mock AI response"


class TestAIAnalyzerCalculations:
    """AIAnalyzer计算功能测试"""

    def test_calculate_risk_metrics_with_data(self):
        """测试风险指标计算-有数据"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        nav_data = [1.0, 1.05, 1.03, 1.08, 1.06, 1.10]
        result = analyzer._calculate_risk_metrics(nav_data)

        assert "max_drawdown" in result
        assert "volatility" in result
        assert "downside_deviation" in result
        assert "sortino_ratio" in result
        assert "beta" in result

    def test_calculate_risk_metrics_empty(self):
        """测试风险指标计算-空数据"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        result = analyzer._calculate_risk_metrics([])

        assert result["max_drawdown"] == 0
        assert result["volatility"] == 0

    def test_calculate_portfolio_metrics(self):
        """测试组合指标计算"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        portfolio_data = {
            "funds": [
                {"metrics": {"cagr": 10.0, "sharpe_ratio": 1.0}},
                {"metrics": {"cagr": 5.0, "sharpe_ratio": 0.8}},
            ],
            "weights": [0.6, 0.4],
        }

        result = analyzer._calculate_portfolio_metrics(portfolio_data)

        assert result["expected_return"] == 8.0  # 10*0.6 + 5*0.4
        assert result["expected_volatility"] == 10.0
        assert result["portfolio_sharpe"] == 0.92  # 1.0*0.6 + 0.8*0.4

    def test_parse_json_response_valid(self):
        """测试JSON响应解析-有效"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        response = '{"key": "value", "number": 123}'
        result = analyzer._parse_json_response(response)

        assert result["key"] == "value"
        assert result["number"] == 123

    def test_parse_json_response_invalid(self):
        """测试JSON响应解析-无效"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        response = "Not a JSON response"
        result = analyzer._parse_json_response(response)

        assert "raw_response" in result
        assert result["raw_response"] == "Not a JSON response"

    def test_parse_json_response_with_markdown(self):
        """测试JSON响应解析-包含markdown代码块"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        response = 'Some text before {\n  "key": "value"\n} some text after'
        result = analyzer._parse_json_response(response)

        assert result["key"] == "value"
