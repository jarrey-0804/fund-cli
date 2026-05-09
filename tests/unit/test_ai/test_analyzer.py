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

    def test_calculate_risk_metrics_single_element(self):
        """测试风险指标计算-单元素数据"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        result = analyzer._calculate_risk_metrics([1.0])

        assert result["max_drawdown"] == 0
        assert result["volatility"] == 0
        assert result["downside_deviation"] == 0
        assert result["sortino_ratio"] == 0
        assert result["beta"] == 0

    def test_calculate_risk_metrics_two_elements(self):
        """测试风险指标计算-两个元素"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        nav_data = [1.0, 1.1]
        result = analyzer._calculate_risk_metrics(nav_data)

        assert "max_drawdown" in result
        assert "volatility" in result
        assert "beta" in result

    def test_calculate_risk_metrics_all_positive_returns(self):
        """测试风险指标计算-全部正收益"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        # 持续上涨的净值序列
        nav_data = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        result = analyzer._calculate_risk_metrics(nav_data)

        assert result["max_drawdown"] >= 0
        assert result["volatility"] >= 0

    def test_calculate_risk_metrics_with_drawdown(self):
        """测试风险指标计算-有回撤"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        # 先涨后跌的净值序列
        nav_data = [1.0, 1.2, 1.1, 0.9, 1.0, 1.1]
        result = analyzer._calculate_risk_metrics(nav_data)

        assert result["max_drawdown"] > 0
        assert result["downside_deviation"] >= 0

    def test_calculate_portfolio_metrics_empty(self):
        """测试组合指标计算-空数据"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        result = analyzer._calculate_portfolio_metrics({})

        assert result["expected_return"] == 0
        assert result["expected_volatility"] == 0
        assert result["portfolio_sharpe"] == 0

    def test_calculate_portfolio_metrics_no_funds(self):
        """测试组合指标计算-无基金"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        result = analyzer._calculate_portfolio_metrics({"funds": [], "weights": []})

        assert result["expected_return"] == 0
        assert result["expected_volatility"] == 0
        assert result["portfolio_sharpe"] == 0

    def test_calculate_portfolio_metrics_no_weights(self):
        """测试组合指标计算-无权重"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        portfolio_data = {
            "funds": [{"metrics": {"cagr": 10.0, "sharpe_ratio": 1.0}}],
            "weights": [],
        }

        result = analyzer._calculate_portfolio_metrics(portfolio_data)

        # 权重不足时，使用 0
        assert result["expected_return"] == 0
        assert result["portfolio_sharpe"] == 0

    def test_calculate_portfolio_metrics_more_funds_than_weights(self):
        """测试组合指标计算-基金多于权重"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        portfolio_data = {
            "funds": [
                {"metrics": {"cagr": 10.0, "sharpe_ratio": 1.0}},
                {"metrics": {"cagr": 5.0, "sharpe_ratio": 0.8}},
                {"metrics": {"cagr": 8.0, "sharpe_ratio": 0.9}},
            ],
            "weights": [0.5, 0.3],  # 只有2个权重
        }

        result = analyzer._calculate_portfolio_metrics(portfolio_data)

        # 第三个基金权重为0
        assert result["expected_return"] == 6.5  # 10*0.5 + 5*0.3 + 8*0
        assert result["portfolio_sharpe"] == 0.74  # 1.0*0.5 + 0.8*0.3 + 0.9*0


class TestAIAnalyzerEdgeCases:
    """AIAnalyzer边界情况测试"""

    def test_summarize_fund_empty_data(self, mock_provider):
        """测试基金摘要生成-空数据"""
        analyzer = AIAnalyzer(mock_provider)
        result = analyzer.summarize_fund("000001", {})

        assert result == "Mock AI response"

    def test_summarize_fund_missing_fields(self, mock_provider):
        """测试基金摘要生成-缺失字段"""
        analyzer = AIAnalyzer(mock_provider)

        fund_data = {"info": {}, "metrics": {}}
        result = analyzer.summarize_fund("000001", fund_data)

        assert result == "Mock AI response"

    def test_summarize_fund_partial_data(self, mock_provider):
        """测试基金摘要生成-部分数据"""
        analyzer = AIAnalyzer(mock_provider)

        fund_data = {
            "info": {"name": "测试基金"},
            # 缺少 metrics
        }
        result = analyzer.summarize_fund("000001", fund_data)

        assert result == "Mock AI response"

    def test_compare_funds_more_codes_than_data(self, mock_provider):
        """测试基金对比-fund_codes多于funds_data"""
        analyzer = AIAnalyzer(mock_provider)

        codes = ["000001", "000002", "000003"]
        funds_data = [
            {"info": {"name": "基金A"}, "metrics": {"cagr": 10.0}},
        ]

        result = analyzer.compare_funds(codes, funds_data)

        assert result == "Mock AI response"

    def test_compare_funds_empty_data(self, mock_provider):
        """测试基金对比-空数据"""
        analyzer = AIAnalyzer(mock_provider)

        result = analyzer.compare_funds([], [])

        assert result == "Mock AI response"

    def test_compare_funds_with_code_in_data(self, mock_provider):
        """测试基金对比-数据中包含code"""
        analyzer = AIAnalyzer(mock_provider)

        funds_data = [
            {"code": "000001", "info": {"name": "基金A"}, "metrics": {"cagr": 10.0}},
        ]

        result = analyzer.compare_funds([], funds_data)

        assert result == "Mock AI response"

    def test_investment_advice_all_risk_profiles(self, mock_provider, sample_fund_data):
        """测试投资建议-所有风险偏好"""
        mock_provider.mock_response = '{"suitability": "是", "allocation": "20%", "risk_warning": "中等风险", "holding_period": "长期"}'

        analyzer = AIAnalyzer(mock_provider)

        for profile in ["conservative", "moderate", "aggressive"]:
            result = analyzer.investment_advice("000001", sample_fund_data, profile)
            assert "suitability" in result

    def test_investment_advice_missing_metrics(self, mock_provider):
        """测试投资建议-缺失指标"""
        mock_provider.mock_response = '{"suitability": "谨慎考虑", "allocation": "10%", "risk_warning": "数据不足", "holding_period": "观望"}'

        analyzer = AIAnalyzer(mock_provider)

        fund_data = {"info": {"name": "测试基金"}}
        result = analyzer.investment_advice("000001", fund_data, "moderate")

        assert "suitability" in result

    def test_risk_assessment_detailed(self, mock_provider, sample_fund_data):
        """测试风险评估-详细模式"""
        mock_provider.mock_response = '{"risk_level": "中", "main_risks": "市场波动", "warnings": "注意回撤", "control_suggestions": "分散投资"}'

        analyzer = AIAnalyzer(mock_provider)
        result = analyzer.risk_assessment("000001", sample_fund_data, detailed=True)

        assert result["risk_level"] == "中"

    def test_risk_assessment_with_nav_data(self, mock_provider):
        """测试风险评估-有净值数据"""
        mock_provider.mock_response = '{"risk_level": "高", "main_risks": "高波动", "warnings": "注意风险", "control_suggestions": "降低仓位"}'

        analyzer = AIAnalyzer(mock_provider)

        fund_data = {
            "info": {"name": "测试基金"},
            "nav": [1.0, 1.1, 1.0, 0.9, 1.0, 1.1, 1.2],
        }
        result = analyzer.risk_assessment("000001", fund_data)

        assert result["risk_level"] == "高"

    def test_risk_assessment_empty_nav(self, mock_provider):
        """测试风险评估-空净值数据"""
        mock_provider.mock_response = '{"risk_level": "未知", "main_risks": "数据不足", "warnings": "无", "control_suggestions": "获取更多数据"}'

        analyzer = AIAnalyzer(mock_provider)

        fund_data = {"info": {"name": "测试基金"}, "nav": []}
        result = analyzer.risk_assessment("000001", fund_data)

        assert "risk_level" in result

    def test_market_insight_without_context(self, mock_provider, sample_fund_data):
        """测试市场解读-无市场环境描述"""
        analyzer = AIAnalyzer(mock_provider)
        result = analyzer.market_insight("000001", sample_fund_data)

        assert result == "Mock AI response"

    def test_market_insight_with_nav_data(self, mock_provider):
        """测试市场解读-有净值数据计算收益"""
        analyzer = AIAnalyzer(mock_provider)

        fund_data = {
            "info": {"name": "测试基金"},
            "nav": [1.0, 1.05, 1.1, 1.08, 1.15],
        }
        result = analyzer.market_insight("000001", fund_data, "牛市行情")

        assert result == "Mock AI response"

    def test_market_insight_single_nav(self, mock_provider):
        """测试市场解读-单条净值数据"""
        analyzer = AIAnalyzer(mock_provider)

        fund_data = {"info": {"name": "测试基金"}, "nav": [1.0]}
        result = analyzer.market_insight("000001", fund_data)

        assert result == "Mock AI response"

    def test_portfolio_review_empty(self, mock_provider):
        """测试组合分析-空数据"""
        mock_provider.mock_response = '{"overall_assessment": "无数据", "optimization_suggestions": "添加基金", "diversification": "无法评估"}'

        analyzer = AIAnalyzer(mock_provider)
        result = analyzer.portfolio_review({})

        assert "overall_assessment" in result

    def test_portfolio_review_no_weights(self, mock_provider):
        """测试组合分析-无权重"""
        mock_provider.mock_response = '{"overall_assessment": "组合良好", "optimization_suggestions": "设置权重", "diversification": "分散度适中"}'

        portfolio_data = {
            "funds": [{"code": "000001", "metrics": {"cagr": 10.0, "sharpe_ratio": 1.0}}],
        }

        analyzer = AIAnalyzer(mock_provider)
        result = analyzer.portfolio_review(portfolio_data)

        assert "overall_assessment" in result

    def test_generate_report_empty_info(self, mock_provider):
        """测试生成报告-空信息"""
        analyzer = AIAnalyzer(mock_provider)
        result = analyzer.generate_report("000001", {}, {})

        assert result == "Mock AI response"

    def test_generate_report_partial_metrics(self, mock_provider):
        """测试生成报告-部分指标"""
        analyzer = AIAnalyzer(mock_provider)

        fund_info = {"name": "测试基金"}
        metrics = {"cagr": 10.0}  # 只有部分指标

        result = analyzer.generate_report("000001", fund_info, metrics)

        assert result == "Mock AI response"


class TestAIAnalyzerJSONParsing:
    """AIAnalyzer JSON解析测试"""

    def test_parse_json_nested(self):
        """测试JSON解析-嵌套结构"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        response = '{"outer": {"inner": "value"}, "array": [1, 2, 3]}'
        result = analyzer._parse_json_response(response)

        assert result["outer"]["inner"] == "value"
        assert result["array"] == [1, 2, 3]

    def test_parse_json_with_special_chars(self):
        """测试JSON解析-特殊字符"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        response = '{"key": "value with \\"quotes\\"", "chinese": "中文"}'
        result = analyzer._parse_json_response(response)

        assert "quotes" in result["key"]
        assert result["chinese"] == "中文"

    def test_parse_json_malformed(self):
        """测试JSON解析-格式错误"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        response = '{"key": "value"'  # 缺少闭合括号
        result = analyzer._parse_json_response(response)

        assert "raw_response" in result

    def test_parse_json_empty_object(self):
        """测试JSON解析-空对象"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        response = '{}'
        result = analyzer._parse_json_response(response)

        assert result == {}

    def test_parse_json_with_numbers(self):
        """测试JSON解析-数字类型"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        response = '{"int": 123, "float": 45.67, "negative": -10}'
        result = analyzer._parse_json_response(response)

        assert result["int"] == 123
        assert result["float"] == 45.67
        assert result["negative"] == -10

    def test_parse_json_with_boolean_null(self):
        """测试JSON解析-布尔和null"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        response = '{"bool_true": true, "bool_false": false, "null_val": null}'
        result = analyzer._parse_json_response(response)

        assert result["bool_true"] is True
        assert result["bool_false"] is False
        assert result["null_val"] is None


class TestAIAnalyzerInitialization:
    """AIAnalyzer初始化测试"""

    def test_init_with_none_provider(self):
        """测试初始化-provider为None时使用默认配置"""
        from unittest.mock import patch

        with patch("fund_cli.ai.analyzer.get_provider") as mock_get_provider:
            mock_provider = MockLLMProvider()
            mock_get_provider.return_value = mock_provider

            analyzer = AIAnalyzer(None)

            mock_get_provider.assert_called_once()
            assert analyzer.provider == mock_provider

    def test_init_prompts_attribute(self, mock_provider):
        """测试初始化-prompts属性"""
        from fund_cli.ai.prompts import PromptTemplates

        analyzer = AIAnalyzer(mock_provider)

        assert hasattr(analyzer, "prompts")
        assert isinstance(analyzer.prompts, PromptTemplates)


class TestAIAnalyzerRiskMetricsCalculation:
    """AIAnalyzer风险指标计算详细测试"""

    def test_calculate_risk_metrics_large_dataset(self):
        """测试风险指标计算-大数据集"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        # 生成100个数据点
        import random
        random.seed(42)
        nav_data = [1.0]
        for _ in range(99):
            change = random.uniform(-0.02, 0.03)
            nav_data.append(nav_data[-1] * (1 + change))

        result = analyzer._calculate_risk_metrics(nav_data)

        assert result["max_drawdown"] >= 0
        assert result["volatility"] >= 0
        assert result["beta"] == 1.0  # 简化计算固定为1.0

    def test_calculate_risk_metrics_declining_prices(self):
        """测试风险指标计算-持续下跌"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        nav_data = [1.0, 0.95, 0.90, 0.85, 0.80, 0.75]
        result = analyzer._calculate_risk_metrics(nav_data)

        assert result["max_drawdown"] > 0
        assert result["downside_deviation"] > 0

    def test_calculate_risk_metrics_volatile(self):
        """测试风险指标计算-高波动"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        # 高波动的净值序列
        nav_data = [1.0, 1.2, 0.9, 1.3, 0.8, 1.4, 0.7, 1.5]
        result = analyzer._calculate_risk_metrics(nav_data)

        assert result["volatility"] > 10  # 高波动
        assert result["max_drawdown"] > 0


class TestAIAnalyzerPortfolioMetricsCalculation:
    """AIAnalyzer组合指标计算详细测试"""

    def test_calculate_portfolio_metrics_many_funds(self):
        """测试组合指标计算-多只基金"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        portfolio_data = {
            "funds": [
                {"metrics": {"cagr": 10.0, "sharpe_ratio": 1.0}},
                {"metrics": {"cagr": 8.0, "sharpe_ratio": 0.9}},
                {"metrics": {"cagr": 6.0, "sharpe_ratio": 0.8}},
                {"metrics": {"cagr": 4.0, "sharpe_ratio": 0.7}},
            ],
            "weights": [0.4, 0.3, 0.2, 0.1],
        }

        result = analyzer._calculate_portfolio_metrics(portfolio_data)

        # 10*0.4 + 8*0.3 + 6*0.2 + 4*0.1 = 4 + 2.4 + 1.2 + 0.4 = 8.0
        assert result["expected_return"] == 8.0
        # 1.0*0.4 + 0.9*0.3 + 0.8*0.2 + 0.7*0.1 = 0.4 + 0.27 + 0.16 + 0.07 = 0.9
        assert result["portfolio_sharpe"] == 0.9

    def test_calculate_portfolio_metrics_missing_metrics_in_fund(self):
        """测试组合指标计算-基金缺少指标"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        portfolio_data = {
            "funds": [
                {"metrics": {"cagr": 10.0, "sharpe_ratio": 1.0}},
                {"metrics": {}},  # 缺少指标
                {"metrics": {"cagr": 5.0}},  # 缺少 sharpe_ratio
            ],
            "weights": [0.5, 0.3, 0.2],
        }

        result = analyzer._calculate_portfolio_metrics(portfolio_data)

        # 10*0.5 + 0*0.3 + 5*0.2 = 5 + 0 + 1 = 6.0
        assert result["expected_return"] == 6.0
        # 1.0*0.5 + 0*0.3 + 0*0.2 = 0.5
        assert result["portfolio_sharpe"] == 0.5

    def test_calculate_portfolio_metrics_zero_weights(self):
        """测试组合指标计算-零权重"""
        provider = MockLLMProvider()
        analyzer = AIAnalyzer(provider)

        portfolio_data = {
            "funds": [
                {"metrics": {"cagr": 10.0, "sharpe_ratio": 1.0}},
                {"metrics": {"cagr": 5.0, "sharpe_ratio": 0.8}},
            ],
            "weights": [0.0, 0.0],
        }

        result = analyzer._calculate_portfolio_metrics(portfolio_data)

        assert result["expected_return"] == 0.0
        assert result["portfolio_sharpe"] == 0.0
