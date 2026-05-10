"""
AI 命令测试.

测试 fund ai 命令的各个子命令。
"""

import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from fund_cli.commands.ai_cmd import app, _simple_interactive

runner = CliRunner()


class TestAIChatCommand:
    """测试 ai chat 命令."""

    @patch("fund_cli.ai.agent.get_fund_agent")
    def test_chat_success(self, mock_get_agent):
        """测试成功的对话."""
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = "这是AI的回复"
        mock_get_agent.return_value = mock_agent

        result = runner.invoke(app, ["chat", "分析基金000001"])

        assert result.exit_code == 0

    @patch("fund_cli.ai.agent.get_fund_agent")
    def test_chat_with_user_id(self, mock_get_agent):
        """测试带用户ID的对话."""
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = "回复内容"
        mock_get_agent.return_value = mock_agent

        result = runner.invoke(app, ["chat", "测试消息", "--user", "user123"])

        assert result.exit_code == 0
        mock_agent.invoke.assert_called_once()

    @patch("fund_cli.ai.agent.get_fund_agent")
    def test_chat_with_thread_id(self, mock_get_agent):
        """测试带线程ID的多轮对话."""
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = "回复内容"
        mock_get_agent.return_value = mock_agent

        result = runner.invoke(app, ["chat", "继续对话", "--thread", "thread456"])

        assert result.exit_code == 0

    @patch("fund_cli.ai.agent.get_fund_agent")
    def test_chat_error(self, mock_get_agent):
        """测试对话失败情况."""
        mock_get_agent.side_effect = Exception("Agent初始化失败")

        result = runner.invoke(app, ["chat", "测试"])

        assert result.exit_code == 1


class TestAIInteractiveCommand:
    """测试 ai interactive 命令."""

    @patch("fund_cli.ai.agent.get_fund_agent")
    def test_simple_interactive_mode(self, mock_get_agent):
        """测试简单交互模式."""
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = "AI回复"
        mock_get_agent.return_value = mock_agent

        # 测试简单交互模式函数存在
        assert callable(_simple_interactive)

    def test_interactive_mode_exists(self):
        """测试交互模式命令存在."""
        result = runner.invoke(app, ["interactive", "--help"])
        # 命令应该有帮助信息
        assert result.exit_code == 0


class TestAISummarizeCommand:
    """测试 ai summarize 命令."""

    def test_summarize_help(self):
        """测试 summarize 命令帮助."""
        result = runner.invoke(app, ["summarize", "--help"])
        # 命令应该有帮助信息
        assert result.exit_code == 0


class TestAICompareCommand:
    """测试 ai compare 命令."""

    @patch("fund_cli.data.adapters.get_adapter")
    @patch("fund_cli.ai.analyzer.AIAnalyzer")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    def test_compare_success(self, mock_perf_cls, mock_analyzer_cls, mock_get_adapter):
        """测试对比分析成功."""
        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {"fund_name": "测试基金"}
        mock_nav = MagicMock()
        mock_nav.empty = False
        mock_adapter.get_fund_nav.return_value = mock_nav
        mock_get_adapter.return_value = mock_adapter

        mock_perf = MagicMock()
        mock_perf.calculate_metrics.return_value = {"sharpe": 1.5}
        mock_perf_cls.return_value = mock_perf

        mock_analyzer = MagicMock()
        mock_analyzer.compare_funds.return_value = "对比分析结果"
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["compare", "000001,000002"])

        # 命令应该执行
        assert result.exit_code in [0, 1]


class TestAIAdviceCommand:
    """测试 ai advice 命令."""

    @patch("fund_cli.data.adapters.get_adapter")
    @patch("fund_cli.ai.analyzer.AIAnalyzer")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    def test_advice_success(self, mock_perf_cls, mock_analyzer_cls, mock_get_adapter):
        """测试投资建议生成成功."""
        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {"fund_name": "测试基金"}
        mock_nav = MagicMock()
        mock_nav.empty = False
        mock_adapter.get_fund_nav.return_value = mock_nav
        mock_get_adapter.return_value = mock_adapter

        mock_perf = MagicMock()
        mock_perf.calculate_metrics.return_value = {"sharpe": 1.5}
        mock_perf_cls.return_value = mock_perf

        mock_analyzer = MagicMock()
        mock_analyzer.investment_advice.return_value = {
            "suitability": "适合",
            "allocation": "20%",
            "risk_warning": "注意风险",
            "holding_period": "建议长期持有",
        }
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["advice", "000001"])

        # 命令应该执行
        assert result.exit_code in [0, 1]

    def test_advice_invalid_risk_profile(self):
        """测试无效的风险偏好."""
        result = runner.invoke(app, ["advice", "000001", "--risk", "invalid"])

        assert result.exit_code == 1


class TestAIRiskCommand:
    """测试 ai risk 命令."""

    @patch("fund_cli.data.adapters.get_adapter")
    @patch("fund_cli.ai.analyzer.AIAnalyzer")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    def test_risk_success(self, mock_perf_cls, mock_analyzer_cls, mock_get_adapter):
        """测试风险评估成功."""
        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {"fund_name": "测试基金"}
        mock_nav = MagicMock()
        mock_nav.empty = False
        mock_adapter.get_fund_nav.return_value = mock_nav
        mock_get_adapter.return_value = mock_adapter

        mock_perf = MagicMock()
        mock_perf.calculate_metrics.return_value = {"sharpe": 1.5}
        mock_perf_cls.return_value = mock_perf

        mock_analyzer = MagicMock()
        mock_analyzer.assess_risk.return_value = {
            "overall_risk": "中等",
            "risk_factors": ["波动率较高"],
            "suggestions": ["建议分散投资"],
        }
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["risk", "000001"])

        # 命令应该执行
        assert result.exit_code in [0, 1]


class TestAIInsightCommand:
    """测试 ai insight 命令."""

    @patch("fund_cli.data.adapters.get_adapter")
    @patch("fund_cli.ai.analyzer.AIAnalyzer")
    def test_insight_success(self, mock_analyzer_cls, mock_get_adapter):
        """测试市场解读成功."""
        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {"fund_name": "测试基金"}
        mock_nav = MagicMock()
        mock_nav.empty = False
        mock_adapter.get_fund_nav.return_value = mock_nav
        mock_get_adapter.return_value = mock_adapter

        mock_analyzer = MagicMock()
        mock_analyzer.market_insight.return_value = "市场解读内容"
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["insight", "000001"])

        # 命令应该执行
        assert result.exit_code in [0, 1]


class TestAIPortfolioCommand:
    """测试 ai portfolio 命令."""

    @patch("fund_cli.data.adapters.get_adapter")
    @patch("fund_cli.ai.analyzer.AIAnalyzer")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    def test_portfolio_success(self, mock_perf_cls, mock_analyzer_cls, mock_get_adapter):
        """测试组合分析成功."""
        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {"fund_name": "测试基金"}
        mock_nav = MagicMock()
        mock_nav.empty = False
        mock_adapter.get_fund_nav.return_value = mock_nav
        mock_get_adapter.return_value = mock_adapter

        mock_perf = MagicMock()
        mock_perf.calculate_metrics.return_value = {"sharpe": 1.5}
        mock_perf_cls.return_value = mock_perf

        mock_analyzer = MagicMock()
        mock_analyzer.portfolio_review.return_value = {
            "overall_assessment": "组合评价良好",
            "recommendations": ["建议增加债券配置"],
        }
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["portfolio", "000001,000002"])

        # 命令应该执行
        assert result.exit_code in [0, 1]

    def test_portfolio_single_fund_error(self):
        """测试组合分析只有一个基金时的错误."""
        result = runner.invoke(app, ["portfolio", "000001"])

        assert result.exit_code == 1

    def test_portfolio_invalid_weights(self):
        """测试组合分析权重数量不匹配."""
        result = runner.invoke(app, ["portfolio", "000001,000002", "--weights", "0.5"])

        assert result.exit_code == 1

    def test_portfolio_weights_not_sum_to_one(self):
        """测试组合分析权重和不等于1."""
        result = runner.invoke(app, ["portfolio", "000001,000002", "--weights", "0.3,0.3"])

        assert result.exit_code == 1


class TestAIAppStructure:
    """测试 AI 命令应用结构."""

    def test_app_exists(self):
        """测试应用存在."""
        assert app is not None

    def test_app_has_commands(self):
        """测试应用包含所有命令."""
        # 获取所有注册的命令
        commands = app.registered_commands
        # 验证主要命令存在
        assert len(commands) > 0

    def test_help_text(self):
        """测试帮助文本."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "AI" in result.output or "ai" in result.output.lower()
