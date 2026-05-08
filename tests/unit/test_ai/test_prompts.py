"""
AI提示词模板单元测试
"""

from fund_cli.ai.prompts import PromptTemplates


class TestPromptTemplates:
    """提示词模板测试"""

    def test_format_summary_prompt(self):
        """测试基金摘要提示词格式化"""
        data = {
            "fund_code": "000001",
            "fund_name": "测试基金",
            "fund_type": "股票型",
            "manager": "张三",
            "total_return": 15.5,
            "cagr": 12.3,
            "sharpe": 1.2,
            "max_drawdown": -8.5,
            "volatility": 18.2,
        }

        result = PromptTemplates.format_summary_prompt(data)

        assert "000001" in result
        assert "测试基金" in result
        assert "股票型" in result
        assert "张三" in result
        assert "15.5" in result
        assert "12.3" in result

    def test_format_compare_prompt(self):
        """测试基金对比提示词格式化"""
        funds_data = "基金1: 000001\n基金2: 000002"

        result = PromptTemplates.format_compare_prompt(funds_data)

        assert "基金1: 000001" in result
        assert "基金2: 000002" in result
        assert "对比分析" in result

    def test_format_risk_prompt(self):
        """测试风险分析提示词格式化"""
        data = {
            "fund_name": "测试基金",
            "fund_code": "000001",
            "volatility": 18.2,
            "max_drawdown": -8.5,
            "var_95": -2.5,
            "var_99": -4.0,
            "skewness": -0.3,
            "kurtosis": 2.1,
        }

        result = PromptTemplates.format_risk_prompt(data)

        assert "测试基金" in result
        assert "000001" in result
        assert "18.2" in result
        assert "-8.5" in result

    def test_format_investment_advice_prompt(self):
        """测试投资建议提示词格式化"""
        fund_data = {
            "name": "测试基金",
            "code": "000001",
            "type": "股票型",
            "cagr": 12.3,
            "sharpe": 1.2,
            "max_drawdown": -8.5,
        }
        risk_profile = "moderate"

        result = PromptTemplates.format_investment_advice_prompt(fund_data, risk_profile)

        assert "测试基金" in result
        assert "000001" in result
        assert "股票型" in result
        assert "12.3" in result
        assert "moderate" in result
        assert "JSON格式" in result

    def test_format_market_insight_prompt(self):
        """测试市场解读提示词格式化"""
        fund_data = {
            "name": "测试基金",
            "code": "000001",
            "recent_return": 5.2,
            "rank_in_category": "前30%",
        }
        market_context = "当前市场处于震荡期"

        result = PromptTemplates.format_market_insight_prompt(fund_data, market_context)

        assert "测试基金" in result
        assert "000001" in result
        assert "5.2" in result
        assert "前30%" in result
        assert "震荡期" in result

    def test_format_market_insight_prompt_default_context(self):
        """测试市场解读提示词格式化-默认市场环境"""
        fund_data = {
            "name": "测试基金",
            "code": "000001",
            "recent_return": 5.2,
            "rank_in_category": "前30%",
        }

        result = PromptTemplates.format_market_insight_prompt(fund_data, None)

        assert "市场环境正常" in result

    def test_format_portfolio_review_prompt(self):
        """测试组合分析提示词格式化"""
        portfolio_data = {
            "funds": [
                {"code": "000001"},
                {"code": "000002"},
            ],
            "weights": [0.6, 0.4],
            "expected_return": 8.5,
            "expected_volatility": 12.0,
            "portfolio_sharpe": 0.9,
        }

        result = PromptTemplates.format_portfolio_review_prompt(portfolio_data)

        assert "000001: 60.0%" in result
        assert "000002: 40.0%" in result
        assert "8.5" in result
        assert "12.0" in result
        assert "0.9" in result
        assert "JSON格式" in result

    def test_format_risk_assessment_prompt(self):
        """测试风险评估提示词格式化"""
        fund_data = {
            "name": "测试基金",
            "code": "000001",
            "max_drawdown": -15.0,
            "volatility": 20.0,
            "downside_deviation": 12.0,
            "sortino_ratio": 0.8,
            "beta": 1.1,
            "risk_events": "2022年3月出现较大回撤",
        }

        result = PromptTemplates.format_risk_assessment_prompt(fund_data, detailed=False)

        assert "测试基金" in result
        assert "000001" in result
        assert "-15.0" in result
        assert "20.0" in result
        assert "2022年3月" in result
        assert "JSON格式" in result

    def test_format_risk_assessment_prompt_detailed(self):
        """测试风险评估提示词格式化-详细模式"""
        fund_data = {
            "name": "测试基金",
            "code": "000001",
            "max_drawdown": -15.0,
            "volatility": 20.0,
            "downside_deviation": 12.0,
            "sortino_ratio": 0.8,
            "beta": 1.1,
            "risk_events": "无",
        }

        result = PromptTemplates.format_risk_assessment_prompt(fund_data, detailed=True)

        assert "详细风险分析报告" in result
        assert "历史风险事件回顾" in result
        assert "压力测试结果" in result

    def test_prompt_length_within_limit(self):
        """测试提示词长度在合理范围内"""
        data = {
            "fund_code": "000001",
            "fund_name": "测试基金",
            "fund_type": "股票型",
            "manager": "张三",
            "total_return": 15.5,
            "cagr": 12.3,
            "sharpe": 1.2,
            "max_drawdown": -8.5,
            "volatility": 18.2,
        }

        result = PromptTemplates.format_summary_prompt(data)

        # 提示词长度应该在合理范围内（不超过4000字符）
        assert len(result) < 4000
        assert len(result) > 100  # 确保不是空或太短

    def test_prompt_templates_constants(self):
        """测试提示词模板常量定义"""
        # 确保所有模板都已定义
        assert hasattr(PromptTemplates, "FUND_SUMMARY")
        assert hasattr(PromptTemplates, "FUND_COMPARE")
        assert hasattr(PromptTemplates, "RISK_ANALYSIS")
        assert hasattr(PromptTemplates, "INVESTMENT_ADVICE")
        assert hasattr(PromptTemplates, "MARKET_INSIGHT")
        assert hasattr(PromptTemplates, "PORTFOLIO_REVIEW")
        assert hasattr(PromptTemplates, "RISK_ASSESSMENT")

        # 确保所有格式化方法都已定义
        assert callable(getattr(PromptTemplates, "format_summary_prompt", None))
        assert callable(getattr(PromptTemplates, "format_compare_prompt", None))
        assert callable(getattr(PromptTemplates, "format_risk_prompt", None))
        assert callable(getattr(PromptTemplates, "format_investment_advice_prompt", None))
        assert callable(getattr(PromptTemplates, "format_market_insight_prompt", None))
        assert callable(getattr(PromptTemplates, "format_portfolio_review_prompt", None))
        assert callable(getattr(PromptTemplates, "format_risk_assessment_prompt", None))
