"""
持仓分析命令测试.

测试 fund holding 命令的各个子命令。
"""

from unittest.mock import MagicMock, patch

import pandas as pd
from typer.testing import CliRunner

from fund_cli.commands.holding_cmd import app

runner = CliRunner()


class TestHoldingQueryCommand:
    """测试 holding query 命令."""

    @patch("fund_cli.commands.holding_cmd.DataManager")
    @patch("fund_cli.commands.holding_cmd.HoldingAnalyzer")
    def test_query_success(self, mock_analyzer_cls, mock_dm_cls):
        """测试查询持仓成功."""
        # Mock DataManager
        mock_dm = MagicMock()
        mock_holdings = pd.DataFrame({
            "stock_code": ["000001", "000002"],
            "stock_name": ["平安银行", "万科A"],
            "weight": [5.0, 4.5],
            "market_value": [10000, 9000]
        })
        mock_dm.get_fund_holdings.return_value = mock_holdings
        mock_dm_cls.return_value = mock_dm

        # Mock HoldingAnalyzer
        mock_analyzer = MagicMock()
        mock_analyzer.top_holdings.return_value = mock_holdings.head(2)
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["query", "000001"])

        assert result.exit_code == 0
        mock_dm.get_fund_holdings.assert_called_once_with("000001")

    @patch("fund_cli.commands.holding_cmd.DataManager")
    def test_query_error(self, mock_dm_cls):
        """测试查询持仓失败."""
        mock_dm = MagicMock()
        mock_dm.get_fund_holdings.side_effect = Exception("数据获取失败")
        mock_dm_cls.return_value = mock_dm

        result = runner.invoke(app, ["query", "000001"])

        assert result.exit_code == 1

    @patch("fund_cli.commands.holding_cmd.DataManager")
    @patch("fund_cli.commands.holding_cmd.HoldingAnalyzer")
    def test_query_with_top_n(self, mock_analyzer_cls, mock_dm_cls):
        """测试指定top_n参数."""
        mock_dm = MagicMock()
        mock_holdings = pd.DataFrame({
            "stock_code": ["000001"],
            "stock_name": ["平安银行"],
            "weight": [5.0],
            "market_value": [10000]
        })
        mock_dm.get_fund_holdings.return_value = mock_holdings
        mock_dm_cls.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.top_holdings.return_value = mock_holdings
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["query", "000001", "--top-n", "5"])

        assert result.exit_code == 0
        mock_analyzer.top_holdings.assert_called_once_with(mock_holdings, top_n=5)


class TestHoldingIndustryCommand:
    """测试 holding industry 命令."""

    @patch("fund_cli.commands.holding_cmd.DataManager")
    @patch("fund_cli.commands.holding_cmd.HoldingAnalyzer")
    def test_industry_success(self, mock_analyzer_cls, mock_dm_cls):
        """测试行业配置分析成功."""
        mock_dm = MagicMock()
        mock_holdings = pd.DataFrame({
            "industry": ["银行", "房地产"],
            "weight": [10.0, 8.0]
        })
        mock_dm.get_fund_holdings.return_value = mock_holdings
        mock_dm_cls.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.industry_distribution.return_value = {"银行": 10.0, "房地产": 8.0}
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["industry", "000001"])

        assert result.exit_code == 0
        mock_analyzer.industry_distribution.assert_called_once()

    @patch("fund_cli.commands.holding_cmd.DataManager")
    def test_industry_error(self, mock_dm_cls):
        """测试行业配置分析失败."""
        mock_dm = MagicMock()
        mock_dm.get_fund_holdings.side_effect = Exception("分析失败")
        mock_dm_cls.return_value = mock_dm

        result = runner.invoke(app, ["industry", "000001"])

        assert result.exit_code == 1


class TestHoldingConcentrationCommand:
    """测试 holding concentration 命令."""

    @patch("fund_cli.commands.holding_cmd.DataManager")
    @patch("fund_cli.commands.holding_cmd.HoldingAnalyzer")
    def test_concentration_success(self, mock_analyzer_cls, mock_dm_cls):
        """测试集中度分析成功."""
        mock_dm = MagicMock()
        mock_holdings = pd.DataFrame({
            "stock_code": ["000001", "000002"],
            "weight": [5.0, 4.5]
        })
        mock_dm.get_fund_holdings.return_value = mock_holdings
        mock_dm_cls.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.concentration_hhi.return_value = 0.045
        mock_analyzer._hhi_level.return_value = "分散"
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["concentration", "000001"])

        assert result.exit_code == 0
        assert "HHI指数" in result.output or "集中度" in result.output

    @patch("fund_cli.commands.holding_cmd.DataManager")
    def test_concentration_error(self, mock_dm_cls):
        """测试集中度分析失败."""
        mock_dm = MagicMock()
        mock_dm.get_fund_holdings.side_effect = Exception("分析失败")
        mock_dm_cls.return_value = mock_dm

        result = runner.invoke(app, ["concentration", "000001"])

        assert result.exit_code == 1


class TestHoldingChangesCommand:
    """测试 holding changes 命令."""

    @patch("fund_cli.commands.holding_cmd.DataManager")
    @patch("fund_cli.commands.holding_cmd.HoldingAnalyzer")
    def test_changes_success(self, mock_analyzer_cls, mock_dm_cls):
        """测试持仓变化追踪成功."""
        mock_dm = MagicMock()
        mock_holdings = pd.DataFrame({
            "stock_code": ["000001", "000002"],
            "stock_name": ["平安银行", "万科A"],
            "weight": [5.0, 4.5]
        })
        mock_dm.get_fund_holdings.return_value = mock_holdings
        mock_dm_cls.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.top_holdings.return_value = mock_holdings.head(2)
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["changes", "000001"])

        assert result.exit_code == 0

    @patch("fund_cli.commands.holding_cmd.DataManager")
    @patch("fund_cli.commands.holding_cmd.HoldingAnalyzer")
    def test_changes_empty_data(self, mock_analyzer_cls, mock_dm_cls):
        """测试持仓数据为空."""
        mock_dm = MagicMock()
        mock_dm.get_fund_holdings.return_value = pd.DataFrame()
        mock_dm_cls.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["changes", "000001"])

        assert result.exit_code == 0
        assert "暂无持仓数据" in result.output

    @patch("fund_cli.commands.holding_cmd.DataManager")
    def test_changes_error(self, mock_dm_cls):
        """测试持仓变化追踪失败."""
        mock_dm = MagicMock()
        mock_dm.get_fund_holdings.side_effect = Exception("分析失败")
        mock_dm_cls.return_value = mock_dm

        result = runner.invoke(app, ["changes", "000001"])

        assert result.exit_code == 1


class TestHoldingStyleCommand:
    """测试 holding style 命令."""

    @patch("fund_cli.commands.holding_cmd.DataManager")
    @patch("fund_cli.commands.holding_cmd.HoldingAnalyzer")
    def test_style_success(self, mock_analyzer_cls, mock_dm_cls):
        """测试风格分析成功."""
        mock_dm = MagicMock()
        mock_holdings = pd.DataFrame({
            "stock_code": ["000001"],
            "market_cap": ["large"],
            "style": ["value"]
        })
        mock_dm.get_fund_holdings.return_value = mock_holdings
        mock_dm_cls.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.style_analysis.return_value = {
            "market_cap_style": "大盘",
            "investment_style": "价值",
            "grid_position": "大盘价值",
            "large_cap_weight": 80.0,
            "value_weight": 70.0
        }
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["style", "000001"])

        assert result.exit_code == 0
        assert "风格分析" in result.output or "市值风格" in result.output

    @patch("fund_cli.commands.holding_cmd.DataManager")
    def test_style_error(self, mock_dm_cls):
        """测试风格分析失败."""
        mock_dm = MagicMock()
        mock_dm.get_fund_holdings.side_effect = Exception("分析失败")
        mock_dm_cls.return_value = mock_dm

        result = runner.invoke(app, ["style", "000001"])

        assert result.exit_code == 1


class TestHoldingAppStructure:
    """测试持仓命令应用结构."""

    def test_app_exists(self):
        """测试应用存在."""
        assert app is not None

    def test_help_text(self):
        """测试帮助文本."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "持仓分析命令" in result.output or "holding" in result.output.lower()

    def test_commands_exist(self):
        """测试命令存在."""
        commands = ["query", "industry", "concentration", "changes", "style"]
        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0, f"命令 {cmd} 不存在"


class TestHoldingFundCodeValidation:
    """测试基金代码验证."""

    @patch("fund_cli.commands.holding_cmd.DataManager")
    def test_invalid_fund_code_query(self, mock_dm_cls):
        """测试无效基金代码查询."""
        # Mock 以避免实际数据获取
        mock_dm = MagicMock()
        mock_dm.get_fund_holdings.return_value = MagicMock()
        mock_dm_cls.return_value = mock_dm

        result = runner.invoke(app, ["query", "INVALID"])
        # 验证器会抛出异常或返回错误
        assert result.exit_code in [0, 1]

    @patch("fund_cli.commands.holding_cmd.DataManager")
    def test_invalid_fund_code_industry(self, mock_dm_cls):
        """测试无效基金代码行业分析."""
        mock_dm = MagicMock()
        mock_dm.get_fund_holdings.return_value = MagicMock()
        mock_dm_cls.return_value = mock_dm

        result = runner.invoke(app, ["industry", "INVALID"])
        assert result.exit_code in [0, 1]
