# -*- coding: utf-8 -*-
"""
基金分析命令测试

测试 analyze_cmd 模块的所有命令功能。
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from typer.testing import CliRunner

from fund_cli.commands.analyze_cmd import app

runner = CliRunner()


@pytest.fixture
def mock_data_manager():
    """Mock 数据管理器"""
    mock_dm = MagicMock()

    # 模拟基金信息
    mock_dm.get_fund_info.return_value = {
        "code": "000001",
        "name": "华夏成长混合",
        "type": "混合型",
        "establish_date": "2005-01-12",
        "manager": "张三",
        "company": "华夏基金",
        "scale": 50.5,
    }

    # 模拟净值数据
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=252, freq="B")
    nav_values = 1.0 + np.cumsum(np.random.normal(0.001, 0.02, 252))
    daily_returns = np.random.normal(0.001, 0.02, 252) * 100

    nav_df = pd.DataFrame(
        {
            "nav_date": dates,
            "unit_nav": nav_values,
            "accumulated_nav": nav_values * 1.5,
            "daily_return": daily_returns,
        }
    )
    mock_dm.get_fund_nav.return_value = nav_df

    # 模拟基准数据
    benchmark_df = pd.DataFrame(
        {
            "nav_date": dates,
            "unit_nav": 1.0 + np.cumsum(np.random.normal(0.0005, 0.015, 252)),
        }
    )
    mock_dm.get_benchmark_nav.return_value = benchmark_df

    return mock_dm


@pytest.fixture
def mock_performance_analyzer():
    """Mock 业绩分析器"""
    mock_analyzer = MagicMock()
    mock_analyzer.analyze.return_value = {
        "total_return": 15.5,
        "cagr": 12.3,
        "volatility": 18.5,
        "max_drawdown": -12.5,
        "sharpe": 1.25,
        "sortino": 1.45,
        "var_95": -2.5,
        "alpha": 2.3,
        "beta": 0.85,
        "information_ratio": 0.45,
        "tracking_error": 3.2,
    }
    mock_analyzer.rolling_performance.return_value = pd.DataFrame(
        {
            "rolling_return": np.random.normal(10, 5, 10),
            "rolling_sharpe": np.random.normal(1.0, 0.3, 10),
            "rolling_volatility": np.random.normal(15, 3, 10),
        },
        index=pd.date_range("2024-01-01", periods=10, freq="B"),
    )
    mock_analyzer.monthly_return_distribution.return_value = {
        "total_months": 12,
        "positive_months": 8,
        "negative_months": 4,
        "win_rate": 66.7,
        "avg_monthly_return": 1.2,
        "max_month": 5.5,
        "min_month": -3.2,
    }
    mock_analyzer.scenario_analysis.return_value = {
        "乐观": {
            "annual_return": 20.0,
            "simulated_total_return": 25.0,
            "simulated_volatility": 15.0,
        },
        "中性": {
            "annual_return": 10.0,
            "simulated_total_return": 12.0,
            "simulated_volatility": 18.0,
        },
        "悲观": {
            "annual_return": -5.0,
            "simulated_total_return": -8.0,
            "simulated_volatility": 22.0,
        },
    }
    mock_analyzer.performance_persistence.return_value = {
        "persistence_score": 75,
        "rank_correlation": 0.65,
        "monthly_win_rate": 58.3,
        "max_positive_streak": 5,
        "max_negative_streak": 2,
    }
    return mock_analyzer


@pytest.fixture
def mock_risk_analyzer():
    """Mock 风险分析器"""
    mock_analyzer = MagicMock()
    mock_analyzer.analyze.return_value = {
        "volatility_annual": 18.5,
        "max_drawdown": -12.5,
        "var_95": -2.5,
        "beta": 0.85,
        "tracking_error": 3.2,
    }
    return mock_analyzer


@pytest.fixture
def mock_reporter():
    """Mock 报告生成器"""
    mock_rep = MagicMock()
    mock_rep.generate.return_value = "<html>Test Report</html>"
    mock_rep.save.return_value = None
    return mock_rep


class TestAnalyzeInfoCommand:
    """基金信息命令测试"""

    def test_info_help(self):
        """测试基金信息命令帮助"""
        result = runner.invoke(app, ["info", "--help"])
        assert result.exit_code == 0
        assert "基金代码" in result.output

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_info_success(self, mock_get_dm, mock_data_manager):
        """测试成功获取基金信息"""
        mock_get_dm.return_value = mock_data_manager
        result = runner.invoke(app, ["info", "000001"])
        assert result.exit_code == 0
        assert "华夏成长混合" in result.output

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_info_with_error(self, mock_get_dm, mock_data_manager):
        """测试获取基金信息错误处理"""
        mock_get_dm.return_value = mock_data_manager
        mock_data_manager.get_fund_info.side_effect = Exception("测试错误")
        result = runner.invoke(app, ["info", "000001"])
        assert result.exit_code == 1


class TestAnalyzeNavCommand:
    """净值历史命令测试"""

    def test_nav_help(self):
        """测试净值历史命令帮助"""
        result = runner.invoke(app, ["nav", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_nav_success(self, mock_get_dm, mock_data_manager):
        """测试成功获取净值历史"""
        mock_get_dm.return_value = mock_data_manager
        result = runner.invoke(app, ["nav", "000001"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_nav_with_date_range(self, mock_get_dm, mock_data_manager):
        """测试指定日期范围获取净值"""
        mock_get_dm.return_value = mock_data_manager
        result = runner.invoke(
            app,
            ["nav", "000001", "--start", "2024-01-01", "--end", "2024-06-30"],
        )
        assert result.exit_code == 0

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_nav_with_limit(self, mock_get_dm, mock_data_manager):
        """测试限制显示条数"""
        mock_get_dm.return_value = mock_data_manager
        result = runner.invoke(app, ["nav", "000001", "--limit", "10"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_nav_no_data(self, mock_get_dm, mock_data_manager):
        """测试无净值数据情况"""
        mock_get_dm.return_value = mock_data_manager
        mock_data_manager.get_fund_nav.return_value = pd.DataFrame()
        result = runner.invoke(app, ["nav", "000001"])
        assert result.exit_code == 0
        assert "未找到" in result.output

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_nav_with_error(self, mock_get_dm, mock_data_manager):
        """测试净值获取错误处理"""
        mock_get_dm.return_value = mock_data_manager
        mock_data_manager.get_fund_nav.side_effect = Exception("测试错误")
        result = runner.invoke(app, ["nav", "000001"])
        assert result.exit_code == 1


class TestAnalyzeMetricsCommand:
    """业绩指标分析命令测试"""

    def test_metrics_help(self):
        """测试业绩指标命令帮助"""
        result = runner.invoke(app, ["metrics", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    @patch("fund_cli.commands.analyze_cmd.PerformanceAnalyzer")
    @patch("fund_cli.commands.analyze_cmd.RiskAnalyzer")
    def test_metrics_success(
        self,
        mock_risk_class,
        mock_perf_class,
        mock_get_dm,
        mock_data_manager,
        mock_performance_analyzer,
        mock_risk_analyzer,
    ):
        """测试成功分析业绩指标"""
        mock_get_dm.return_value = mock_data_manager
        mock_perf_class.return_value = mock_performance_analyzer
        mock_risk_class.return_value = mock_risk_analyzer
        result = runner.invoke(app, ["metrics", "000001"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    @patch("fund_cli.commands.analyze_cmd.PerformanceAnalyzer")
    @patch("fund_cli.commands.analyze_cmd.RiskAnalyzer")
    def test_metrics_with_benchmark(
        self,
        mock_risk_class,
        mock_perf_class,
        mock_get_dm,
        mock_data_manager,
        mock_performance_analyzer,
        mock_risk_analyzer,
    ):
        """测试带基准的业绩指标分析"""
        mock_get_dm.return_value = mock_data_manager
        mock_perf_class.return_value = mock_performance_analyzer
        mock_risk_class.return_value = mock_risk_analyzer
        result = runner.invoke(app, ["metrics", "000001", "--benchmark", "000300"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.analyze_cmd.get_data_manager")
    def test_metrics_no_data(self, mock_get_dm, mock_data_manager):
        """测试无净值数据分析"""
        mock_get_dm.return_value = mock_data_manager
        mock_data_manager.get_fund_nav.return_value = pd.DataFrame()
        result = runner.invoke(app, ["metrics", "000001"])
        assert result.exit_code == 0
        assert "未找到" in result.output


class TestAnalyzeReportCommand:
    """分析报告生成命令测试"""

    def test_report_help(self):
        """测试报告生成命令帮助"""
        result = runner.invoke(app, ["report", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    @patch("fund_cli.core.reporters.html_reporter.HtmlReporter")
    def test_report_html(
        self,
        mock_reporter_class,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_performance_analyzer,
        mock_reporter,
        tmp_path,
    ):
        """测试生成 HTML 报告"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_performance_analyzer
        mock_reporter_class.return_value = mock_reporter
        output_file = tmp_path / "test_report.html"
        result = runner.invoke(
            app,
            ["report", "000001", "--output", str(output_file), "--format", "html"],
        )
        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    @patch("fund_cli.core.reporters.markdown_reporter.MarkdownReporter")
    def test_report_markdown(
        self,
        mock_reporter_class,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_performance_analyzer,
        mock_reporter,
        tmp_path,
    ):
        """测试生成 Markdown 报告"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_performance_analyzer
        mock_reporter_class.return_value = mock_reporter
        output_file = tmp_path / "test_report.md"
        result = runner.invoke(
            app,
            ["report", "000001", "--output", str(output_file), "--format", "markdown"],
        )
        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    def test_report_invalid_format(self, mock_dm_class, mock_data_manager, tmp_path):
        """测试无效报告格式"""
        mock_dm_class.return_value = mock_data_manager
        output_file = tmp_path / "test_report.txt"
        result = runner.invoke(
            app,
            ["report", "000001", "--output", str(output_file), "--format", "txt"],
        )
        assert result.exit_code == 1

    @patch("fund_cli.core.data_manager.DataManager")
    def test_report_no_data(self, mock_dm_class, mock_data_manager):
        """测试无数据生成报告"""
        mock_dm_class.return_value = mock_data_manager
        mock_data_manager.get_fund_nav.return_value = pd.DataFrame()
        result = runner.invoke(app, ["report", "000001"])
        assert result.exit_code == 0
        assert "无净值数据" in result.output


class TestAnalyzeRollingCommand:
    """滚动业绩分析命令测试"""

    def test_rolling_help(self):
        """测试滚动业绩命令帮助"""
        result = runner.invoke(app, ["rolling", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    def test_rolling_success(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_performance_analyzer,
    ):
        """测试成功滚动业绩分析"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_performance_analyzer
        result = runner.invoke(app, ["rolling", "000001"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    def test_rolling_with_window(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_performance_analyzer,
    ):
        """测试指定窗口滚动分析"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_performance_analyzer
        result = runner.invoke(app, ["rolling", "000001", "--window", "30"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    def test_rolling_no_data(self, mock_dm_class, mock_data_manager):
        """测试无数据滚动分析"""
        mock_dm_class.return_value = mock_data_manager
        mock_data_manager.get_fund_nav.return_value = pd.DataFrame()
        result = runner.invoke(app, ["rolling", "000001"])
        assert result.exit_code == 0
        assert "无净值数据" in result.output


class TestAnalyzeMonthlyCommand:
    """月度收益分布命令测试"""

    def test_monthly_help(self):
        """测试月度收益命令帮助"""
        result = runner.invoke(app, ["monthly", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    def test_monthly_success(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_performance_analyzer,
    ):
        """测试成功月度收益分布"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_performance_analyzer
        result = runner.invoke(app, ["monthly", "000001"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    def test_monthly_no_data(self, mock_dm_class, mock_data_manager):
        """测试无数据月度分析"""
        mock_dm_class.return_value = mock_data_manager
        mock_data_manager.get_fund_nav.return_value = pd.DataFrame()
        result = runner.invoke(app, ["monthly", "000001"])
        assert result.exit_code == 0
        assert "无净值数据" in result.output


class TestAnalyzeScenarioCommand:
    """情景分析命令测试"""

    def test_scenario_help(self):
        """测试情景分析命令帮助"""
        result = runner.invoke(app, ["scenario", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    def test_scenario_success(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_performance_analyzer,
    ):
        """测试成功情景分析"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_performance_analyzer
        result = runner.invoke(app, ["scenario", "000001"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    def test_scenario_no_data(self, mock_dm_class, mock_data_manager):
        """测试无数据情景分析"""
        mock_dm_class.return_value = mock_data_manager
        mock_data_manager.get_fund_nav.return_value = pd.DataFrame()
        result = runner.invoke(app, ["scenario", "000001"])
        assert result.exit_code == 0
        assert "无净值数据" in result.output


class TestAnalyzePersistenceCommand:
    """业绩持续性分析命令测试"""

    def test_persistence_help(self):
        """测试业绩持续性命令帮助"""
        result = runner.invoke(app, ["persistence", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    def test_persistence_success(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_performance_analyzer,
    ):
        """测试成功业绩持续性分析"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_performance_analyzer
        result = runner.invoke(app, ["persistence", "000001"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_manager.DataManager")
    def test_persistence_no_data(self, mock_dm_class, mock_data_manager):
        """测试无数据业绩持续性分析"""
        mock_dm_class.return_value = mock_data_manager
        mock_data_manager.get_fund_nav.return_value = pd.DataFrame()
        result = runner.invoke(app, ["persistence", "000001"])
        assert result.exit_code == 0
        assert "无净值数据" in result.output
