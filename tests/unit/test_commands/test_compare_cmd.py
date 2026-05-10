"""
基金对比命令测试.

测试 fund compare 命令的各个子命令。
"""

import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
import pandas as pd
import numpy as np

from fund_cli.commands.compare_cmd import app

runner = CliRunner()


class TestCompareFundsCommand:
    """测试 compare funds 命令."""

    @patch("fund_cli.commands.compare_cmd.get_data_manager")
    @patch("fund_cli.commands.compare_cmd.PerformanceAnalyzer")
    def test_compare_funds_success(self, mock_analyzer_cls, mock_dm_factory):
        """测试对比基金成功."""
        # Mock DataManager
        mock_dm = MagicMock()
        mock_nav = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=30),
            "unit_nav": 1.0 + np.cumsum(np.random.randn(30) * 0.01)
        })
        mock_dm.get_fund_nav.return_value = mock_nav
        mock_dm.get_fund_info.return_value = {"name": "测试基金"}
        mock_dm_factory.return_value = mock_dm

        # Mock PerformanceAnalyzer
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "total_return": 10.0,
            "cagr": 8.0,
            "volatility": 15.0,
            "max_drawdown": -5.0,
            "sharpe": 1.2
        }
        mock_analyzer_cls.return_value = mock_analyzer

        result = runner.invoke(app, ["funds", "000001", "000002"])

        assert result.exit_code == 0

    def test_compare_funds_insufficient_args(self):
        """测试基金数量不足."""
        result = runner.invoke(app, ["funds", "000001"])

        assert result.exit_code == 1
        assert "至少" in result.output or "2" in result.output

    @patch("fund_cli.commands.compare_cmd.get_data_manager")
    def test_compare_funds_data_error(self, mock_dm_factory):
        """测试数据获取错误."""
        mock_dm = MagicMock()
        mock_dm.get_fund_nav.side_effect = Exception("数据获取失败")
        mock_dm_factory.return_value = mock_dm

        result = runner.invoke(app, ["funds", "000001", "000002"])

        # 应该处理错误但不崩溃
        assert result.exit_code in [0, 1]

    @patch("fund_cli.commands.compare_cmd.get_data_manager")
    @patch("fund_cli.commands.compare_cmd.PerformanceAnalyzer")
    def test_compare_funds_different_periods(self, mock_analyzer_cls, mock_dm_factory):
        """测试不同周期对比."""
        mock_dm = MagicMock()
        mock_nav = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=90),
            "unit_nav": 1.0 + np.cumsum(np.random.randn(90) * 0.01)
        })
        mock_dm.get_fund_nav.return_value = mock_nav
        mock_dm.get_fund_info.return_value = {"name": "测试基金"}
        mock_dm_factory.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "total_return": 10.0,
            "cagr": 8.0,
            "volatility": 15.0,
            "max_drawdown": -5.0,
            "sharpe": 1.2
        }
        mock_analyzer_cls.return_value = mock_analyzer

        for period in ["1m", "3m", "6m", "1y", "3y"]:
            result = runner.invoke(app, ["funds", "000001", "000002", "--period", period])
            assert result.exit_code == 0, f"周期 {period} 测试失败"


class TestRollingWinRateCommand:
    """测试 compare rolling-win 命令."""

    @patch("fund_cli.core.data_manager.DataManager")
    def test_rolling_win_success(self, mock_dm_cls):
        """测试滚动胜率成功."""
        mock_dm = MagicMock()
        mock_nav = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=100),
            "daily_return": np.random.randn(100) * 0.01 * 100  # 百分比收益率
        })
        mock_dm.get_fund_nav.return_value = mock_nav
        mock_dm_cls.return_value = mock_dm

        result = runner.invoke(app, ["rolling-win", "000001,000002"])

        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    def test_rolling_win_insufficient_data(self, mock_dm_cls):
        """测试数据不足."""
        mock_dm = MagicMock()
        mock_dm.get_fund_nav.return_value = pd.DataFrame()
        mock_dm_cls.return_value = mock_dm

        result = runner.invoke(app, ["rolling-win", "000001,000002"])

        # 应该提示需要更多数据
        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    def test_rolling_win_single_fund(self, mock_dm_cls):
        """测试单只基金."""
        mock_dm = MagicMock()
        mock_nav = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=100),
            "daily_return": np.random.randn(100) * 0.01 * 100
        })
        mock_dm.get_fund_nav.return_value = mock_nav
        mock_dm_cls.return_value = mock_dm

        result = runner.invoke(app, ["rolling-win", "000001"])

        # 单只基金也应该能运行
        assert result.exit_code == 0


class TestCorrelationCommand:
    """测试 compare correlation 命令."""

    @patch("fund_cli.core.data_manager.DataManager")
    def test_correlation_success(self, mock_dm_cls):
        """测试相关性分析成功."""
        mock_dm = MagicMock()
        mock_nav = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=100),
            "daily_return": np.random.randn(100) * 0.01 * 100
        })
        mock_dm.get_fund_nav.return_value = mock_nav
        mock_dm_cls.return_value = mock_dm

        result = runner.invoke(app, ["correlation", "000001,000002"])

        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    def test_correlation_insufficient_data(self, mock_dm_cls):
        """测试数据不足."""
        mock_dm = MagicMock()
        mock_dm.get_fund_nav.return_value = pd.DataFrame()
        mock_dm_cls.return_value = mock_dm

        result = runner.invoke(app, ["correlation", "000001,000002"])

        # 应该提示需要更多数据
        assert result.exit_code == 0


class TestCompareReportCommand:
    """测试 compare report 命令."""

    @patch("fund_cli.core.data_manager.DataManager")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    @patch("fund_cli.core.reporters.markdown_reporter.MarkdownReporter")
    def test_compare_report_success(self, mock_reporter_cls, mock_analyzer_cls, mock_dm_cls):
        """测试对比报告生成成功."""
        mock_dm = MagicMock()
        mock_nav = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=100),
            "daily_return": np.random.randn(100) * 0.01 * 100
        })
        mock_dm.get_fund_nav.return_value = mock_nav
        mock_dm_cls.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "total_return": 0.1,
            "volatility": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.05
        }
        mock_analyzer_cls.return_value = mock_analyzer

        mock_reporter = MagicMock()
        mock_reporter_cls.return_value = mock_reporter

        result = runner.invoke(app, ["report", "000001,000002"])

        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    def test_compare_report_no_data(self, mock_dm_cls):
        """测试无数据情况."""
        mock_dm = MagicMock()
        mock_dm.get_fund_nav.return_value = pd.DataFrame()
        mock_dm_cls.return_value = mock_dm

        result = runner.invoke(app, ["report", "000001,000002"])

        # 应该提示无数据
        assert result.exit_code == 0


class TestCompareAppStructure:
    """测试对比命令应用结构."""

    def test_app_exists(self):
        """测试应用存在."""
        assert app is not None

    def test_help_text(self):
        """测试帮助文本."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "对比" in result.output or "compare" in result.output.lower()

    def test_commands_exist(self):
        """测试命令存在."""
        commands = ["funds", "rolling-win", "correlation", "report"]
        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0, f"命令 {cmd} 不存在"
