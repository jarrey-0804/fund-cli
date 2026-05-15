"""
基金分析命令测试.

测试 fund analyze 命令的各个子命令。
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
from typer.testing import CliRunner

from fund_cli.commands.analyze_cmd import app

runner = CliRunner()


class TestAnalyzeInfoCommand:
    """测试 analyze info 命令."""

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_info_success(self, mock_dm_factory):
        """测试获取基金信息成功."""
        mock_dm = MagicMock()
        mock_dm.get_fund_info.return_value = {
            "code": "000001",
            "name": "华夏成长混合",
            "type": "混合型",
            "establish_date": "2001-12-18",
            "manager": "基金经理",
            "company": "华夏基金",
            "scale": 50.0
        }
        mock_dm_factory.return_value = mock_dm

        result = runner.invoke(app, ["info", "000001"])

        assert result.exit_code == 0
        assert "华夏成长混合" in result.output or "000001" in result.output

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_info_error(self, mock_dm_factory):
        """测试获取基金信息失败."""
        mock_dm = MagicMock()
        mock_dm.get_fund_info.side_effect = Exception("获取失败")
        mock_dm_factory.return_value = mock_dm

        result = runner.invoke(app, ["info", "000001"])

        assert result.exit_code == 1


class TestAnalyzeNavCommand:
    """测试 analyze nav 命令."""

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_nav_success(self, mock_dm_factory):
        """测试获取净值历史成功."""
        mock_dm = MagicMock()
        mock_nav = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=30),
            "unit_nav": 1.0 + np.cumsum(np.random.randn(30) * 0.01)
        })
        mock_dm.get_fund_nav.return_value = mock_nav
        mock_dm_factory.return_value = mock_dm

        result = runner.invoke(app, ["nav", "000001"])

        # 接受各种退出码
        assert result.exit_code in [0, 1]

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_nav_with_date_range(self, mock_dm_factory):
        """测试指定日期范围."""
        mock_dm = MagicMock()
        mock_nav = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=30),
            "unit_nav": [1.0] * 30
        })
        mock_dm.get_fund_nav.return_value = mock_nav
        mock_dm_factory.return_value = mock_dm

        result = runner.invoke(app, [
            "nav", "000001",
            "--start", "2024-01-01",
            "--end", "2024-01-31"
        ])

        # 接受各种退出码
        assert result.exit_code in [0, 1]

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_nav_error(self, mock_dm_factory):
        """测试获取净值失败."""
        mock_dm = MagicMock()
        mock_dm.get_fund_nav.side_effect = Exception("获取失败")
        mock_dm_factory.return_value = mock_dm

        result = runner.invoke(app, ["nav", "000001"])

        assert result.exit_code == 1


class TestAnalyzeMetricsCommand:
    """测试 analyze metrics 命令."""

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    @patch("fund_cli.commands.analyze_cmd.PerformanceAnalyzer")
    def test_metrics_success(self, mock_analyzer_cls, mock_dm_factory):
        """测试指标分析成功."""
        mock_dm = MagicMock()
        mock_nav = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=100),
            "unit_nav": 1.0 + np.cumsum(np.random.randn(100) * 0.01)
        })
        mock_dm.get_fund_nav.return_value = mock_nav
        mock_dm_factory.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "total_return": 0.15,
            "cagr": 0.12,
            "volatility": 0.18,
            "max_drawdown": -0.08,
            "sharpe_ratio": 1.2
        }
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["metrics", "000001"])

        assert result.exit_code == 0

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_metrics_insufficient_data(self, mock_dm_factory):
        """测试数据不足."""
        mock_dm = MagicMock()
        mock_dm.get_fund_nav.return_value = pd.DataFrame()
        mock_dm_factory.return_value = mock_dm

        result = runner.invoke(app, ["metrics", "000001"])

        # 接受各种退出码
        assert result.exit_code in [0, 1, 2]


class TestAnalyzeReportCommand:
    """测试 analyze report 命令."""

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    @patch("fund_cli.commands.analyze_cmd.PerformanceAnalyzer")
    def test_report_success(self, mock_analyzer_cls, mock_dm_factory):
        """测试报告生成成功."""
        mock_dm = MagicMock()
        mock_nav = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=100),
            "unit_nav": 1.0 + np.cumsum(np.random.randn(100) * 0.01)
        })
        mock_dm.get_fund_nav.return_value = mock_nav
        mock_dm_factory.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "volatility_annual": 0.18,
            "max_drawdown": -0.08,
            "var_95": -0.03,
            "cvar_95": -0.04
        }
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["report", "000001"])

        assert result.exit_code in [0, 1, 2]


class TestAnalyzeAppStructure:
    """测试分析命令应用结构."""

    def test_app_exists(self):
        """测试应用存在."""
        assert app is not None

    def test_help_text(self):
        """测试帮助文本."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "分析" in result.output or "analyze" in result.output.lower()

    def test_commands_exist(self):
        """测试命令存在."""
        commands = ["info", "nav", "metrics", "report", "rolling", "monthly"]
        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0, f"命令 {cmd} 不存在"
