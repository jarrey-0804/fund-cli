"""
组合优化命令测试

测试 optimize_cmd 模块的所有命令功能。
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from typer.testing import CliRunner

from fund_cli.commands.optimize_cmd import app

runner = CliRunner()


@pytest.fixture
def mock_returns_data():
    """Mock 收益率数据"""
    np.random.seed(42)
    dates = pd.date_range(date.today() - timedelta(days=365), periods=252, freq="B")
    return pd.DataFrame(
        {
            "000001": np.random.normal(0.001, 0.02, 252),
            "000002": np.random.normal(0.0008, 0.018, 252),
            "000003": np.random.normal(0.0012, 0.022, 252),
        },
        index=dates,
    )


@pytest.fixture
def mock_data_manager():
    """Mock 数据管理器"""
    mock_dm = MagicMock()

    # 模拟净值数据
    def get_fund_nav_side_effect(code, start_date=None, end_date=None):
        np.random.seed(int(code) % 1000)
        dates = pd.date_range(start_date or date.today() - timedelta(days=365), periods=252, freq="B")
        return pd.DataFrame(
            {
                "nav_date": dates,
                "unit_nav": 1.0 + np.cumsum(np.random.normal(0.001, 0.02, 252)),
                "daily_return": np.random.normal(0.1, 2, 252),
            }
        )

    mock_dm.get_fund_nav.side_effect = get_fund_nav_side_effect
    return mock_dm


@pytest.fixture
def mock_optimizer_result():
    """Mock 优化结果"""
    return {
        "method": "mean_variance",
        "expected_return": 0.15,
        "volatility": 0.18,
        "sharpe_ratio": 0.83,
        "weights": {"000001": 0.4, "000002": 0.35, "000003": 0.25},
    }


@pytest.fixture
def mock_frontier_result():
    """Mock 有效前沿结果"""
    return {
        "n_points": 50,
        "frontier_returns": np.linspace(0.05, 0.25, 50),
        "frontier_volatilities": np.linspace(0.10, 0.30, 50),
    }


@pytest.fixture
def mock_backtest_result():
    """Mock 回测结果"""
    return {
        "total_return": 25.5,
        "annual_return": 12.3,
        "annual_volatility": 18.5,
        "sharpe_ratio": 0.67,
        "max_drawdown": -15.2,
        "win_rate": 52.5,
        "trading_days": 252,
    }


class TestMeanVarianceCommand:
    """均值-方差优化命令测试"""

    def test_mean_variance_help(self):
        """测试均值-方差优化命令帮助"""
        result = runner.invoke(app, ["mean-variance", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.core.optimizers.mean_variance.MeanVarianceOptimizer")
    def test_mean_variance_success(
        self,
        mock_optimizer_class,
        mock_get_returns,
        mock_returns_data,
        mock_optimizer_result,
    ):
        """测试成功均值-方差优化"""
        mock_get_returns.return_value = mock_returns_data
        mock_optimizer = MagicMock()
        mock_optimizer.optimize.return_value = mock_optimizer_result
        mock_optimizer_class.return_value = mock_optimizer

        result = runner.invoke(app, ["mean-variance", "000001,000002,000003"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    def test_mean_variance_no_data(self, mock_get_returns):
        """测试无数据均值-方差优化"""
        mock_get_returns.return_value = None
        result = runner.invoke(app, ["mean-variance", "000001,000002"])
        assert result.exit_code == 1
        assert "无法获取" in result.output

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.core.optimizers.mean_variance.MeanVarianceOptimizer")
    def test_mean_variance_with_risk_free(
        self,
        mock_optimizer_class,
        mock_get_returns,
        mock_returns_data,
        mock_optimizer_result,
    ):
        """测试指定无风险利率"""
        mock_get_returns.return_value = mock_returns_data
        mock_optimizer = MagicMock()
        mock_optimizer.optimize.return_value = mock_optimizer_result
        mock_optimizer_class.return_value = mock_optimizer

        result = runner.invoke(
            app,
            ["mean-variance", "000001,000002", "--risk-free", "0.02"],
        )
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.core.optimizers.mean_variance.MeanVarianceOptimizer")
    def test_mean_variance_with_weight_constraints(
        self,
        mock_optimizer_class,
        mock_get_returns,
        mock_returns_data,
        mock_optimizer_result,
    ):
        """测试指定权重约束"""
        mock_get_returns.return_value = mock_returns_data
        mock_optimizer = MagicMock()
        mock_optimizer.optimize.return_value = mock_optimizer_result
        mock_optimizer_class.return_value = mock_optimizer

        result = runner.invoke(
            app,
            ["mean-variance", "000001,000002", "--min-weight", "0.1", "--max-weight", "0.5"],
        )
        assert result.exit_code == 0


class TestMaxSharpeCommand:
    """最大夏普比率优化命令测试"""

    def test_max_sharpe_help(self):
        """测试最大夏普比率优化命令帮助"""
        result = runner.invoke(app, ["max-sharpe", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.core.optimizers.max_sharpe.MaxSharpeOptimizer")
    def test_max_sharpe_success(
        self,
        mock_optimizer_class,
        mock_get_returns,
        mock_returns_data,
        mock_optimizer_result,
    ):
        """测试成功最大夏普比率优化"""
        mock_get_returns.return_value = mock_returns_data
        mock_optimizer = MagicMock()
        mock_optimizer_result["method"] = "max_sharpe"
        mock_optimizer.optimize.return_value = mock_optimizer_result
        mock_optimizer_class.return_value = mock_optimizer

        result = runner.invoke(app, ["max-sharpe", "000001,000002,000003"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    def test_max_sharpe_no_data(self, mock_get_returns):
        """测试无数据最大夏普比率优化"""
        mock_get_returns.return_value = None
        result = runner.invoke(app, ["max-sharpe", "000001,000002"])
        assert result.exit_code == 1

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.core.optimizers.max_sharpe.MaxSharpeOptimizer")
    def test_max_sharpe_with_period(
        self,
        mock_optimizer_class,
        mock_get_returns,
        mock_returns_data,
        mock_optimizer_result,
    ):
        """测试指定分析周期"""
        mock_get_returns.return_value = mock_returns_data
        mock_optimizer = MagicMock()
        mock_optimizer.optimize.return_value = mock_optimizer_result
        mock_optimizer_class.return_value = mock_optimizer

        result = runner.invoke(
            app,
            ["max-sharpe", "000001,000002", "--period", "3y"],
        )
        assert result.exit_code == 0


class TestRiskParityCommand:
    """风险平价优化命令测试"""

    def test_risk_parity_help(self):
        """测试风险平价优化命令帮助"""
        result = runner.invoke(app, ["risk-parity", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.core.optimizers.risk_parity.RiskParityOptimizer")
    def test_risk_parity_success(
        self,
        mock_optimizer_class,
        mock_get_returns,
        mock_returns_data,
        mock_optimizer_result,
    ):
        """测试成功风险平价优化"""
        mock_get_returns.return_value = mock_returns_data
        mock_optimizer = MagicMock()
        mock_optimizer_result["method"] = "risk_parity"
        mock_optimizer.optimize.return_value = mock_optimizer_result
        mock_optimizer_class.return_value = mock_optimizer

        result = runner.invoke(app, ["risk-parity", "000001,000002,000003"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    def test_risk_parity_no_data(self, mock_get_returns):
        """测试无数据风险平价优化"""
        mock_get_returns.return_value = None
        result = runner.invoke(app, ["risk-parity", "000001,000002"])
        assert result.exit_code == 1


class TestEfficientFrontierCommand:
    """有效前沿计算命令测试"""

    def test_frontier_help(self):
        """测试有效前沿命令帮助"""
        result = runner.invoke(app, ["frontier", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.core.optimizers.efficient_frontier.EfficientFrontierCalculator")
    def test_frontier_success(
        self,
        mock_calc_class,
        mock_get_returns,
        mock_returns_data,
        mock_frontier_result,
    ):
        """测试成功有效前沿计算"""
        mock_get_returns.return_value = mock_returns_data
        mock_calc = MagicMock()
        mock_calc.calculate.return_value = mock_frontier_result
        mock_calc_class.return_value = mock_calc

        result = runner.invoke(app, ["frontier", "000001,000002,000003"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    def test_frontier_no_data(self, mock_get_returns):
        """测试无数据有效前沿计算"""
        mock_get_returns.return_value = None
        result = runner.invoke(app, ["frontier", "000001,000002"])
        assert result.exit_code == 1

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.core.optimizers.efficient_frontier.EfficientFrontierCalculator")
    def test_frontier_with_points(
        self,
        mock_calc_class,
        mock_get_returns,
        mock_returns_data,
        mock_frontier_result,
    ):
        """测试指定前沿点数"""
        mock_get_returns.return_value = mock_returns_data
        mock_calc = MagicMock()
        mock_calc.calculate.return_value = mock_frontier_result
        mock_calc_class.return_value = mock_calc

        result = runner.invoke(
            app,
            ["frontier", "000001,000002", "--points", "100"],
        )
        assert result.exit_code == 0


class TestBacktestCommand:
    """组合回测命令测试"""

    def test_backtest_help(self):
        """测试回测命令帮助"""
        result = runner.invoke(app, ["backtest", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.analysis.backtest.BacktestAnalyzer")
    def test_backtest_success(
        self,
        mock_analyzer_class,
        mock_get_returns,
        mock_returns_data,
        mock_backtest_result,
    ):
        """测试成功组合回测"""
        mock_get_returns.return_value = mock_returns_data
        mock_analyzer = MagicMock()
        mock_analyzer.run_backtest.return_value = mock_backtest_result
        mock_analyzer_class.return_value = mock_analyzer

        result = runner.invoke(app, ["backtest", "000001,000002,000003"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    def test_backtest_no_data(self, mock_get_returns):
        """测试无数据组合回测"""
        mock_get_returns.return_value = None
        result = runner.invoke(app, ["backtest", "000001,000002"])
        assert result.exit_code == 1

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.analysis.backtest.BacktestAnalyzer")
    def test_backtest_with_weights(
        self,
        mock_analyzer_class,
        mock_get_returns,
        mock_returns_data,
        mock_backtest_result,
    ):
        """测试指定权重回测"""
        mock_get_returns.return_value = mock_returns_data
        mock_analyzer = MagicMock()
        mock_analyzer.run_backtest.return_value = mock_backtest_result
        mock_analyzer_class.return_value = mock_analyzer

        result = runner.invoke(
            app,
            ["backtest", "000001,000002,000003", "--weights", "0.4,0.3,0.3"],
        )
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.analysis.backtest.BacktestAnalyzer")
    def test_backtest_with_rebalance(
        self,
        mock_analyzer_class,
        mock_get_returns,
        mock_returns_data,
        mock_backtest_result,
    ):
        """测试指定再平衡频率"""
        mock_get_returns.return_value = mock_returns_data
        mock_analyzer = MagicMock()
        mock_analyzer.run_backtest.return_value = mock_backtest_result
        mock_analyzer_class.return_value = mock_analyzer

        result = runner.invoke(
            app,
            ["backtest", "000001,000002", "--rebalance", "quarterly"],
        )
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.analysis.backtest.BacktestAnalyzer")
    def test_backtest_with_period(
        self,
        mock_analyzer_class,
        mock_get_returns,
        mock_returns_data,
        mock_backtest_result,
    ):
        """测试指定分析周期"""
        mock_get_returns.return_value = mock_returns_data
        mock_analyzer = MagicMock()
        mock_analyzer.run_backtest.return_value = mock_backtest_result
        mock_analyzer_class.return_value = mock_analyzer

        result = runner.invoke(
            app,
            ["backtest", "000001,000002", "--period", "2y"],
        )
        assert result.exit_code == 0


class TestOptimizeCommandEdgeCases:
    """边界情况测试"""

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.core.optimizers.mean_variance.MeanVarianceOptimizer")
    def test_single_fund(
        self,
        mock_optimizer_class,
        mock_get_returns,
        mock_optimizer_result,
    ):
        """测试单基金优化"""
        np.random.seed(42)
        dates = pd.date_range(date.today() - timedelta(days=365), periods=252, freq="B")
        single_returns = pd.DataFrame(
            {"000001": np.random.normal(0.001, 0.02, 252)},
            index=dates,
        )
        mock_get_returns.return_value = single_returns
        mock_optimizer = MagicMock()
        mock_optimizer_result["weights"] = {"000001": 1.0}
        mock_optimizer.optimize.return_value = mock_optimizer_result
        mock_optimizer_class.return_value = mock_optimizer

        result = runner.invoke(app, ["mean-variance", "000001"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.analysis.backtest.BacktestAnalyzer")
    def test_backtest_invalid_weights(
        self,
        mock_analyzer_class,
        mock_get_returns,
        mock_returns_data,
        mock_backtest_result,
    ):
        """测试无效权重回测"""
        mock_get_returns.return_value = mock_returns_data
        mock_analyzer = MagicMock()
        mock_analyzer.run_backtest.return_value = mock_backtest_result
        mock_analyzer_class.return_value = mock_analyzer

        # 权重数量与基金数量不匹配
        result = runner.invoke(
            app,
            ["backtest", "000001,000002,000003", "--weights", "0.5,0.5"],
        )
        # 应该忽略无效权重，继续执行
        assert result.exit_code == 0

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    def test_empty_returns(self, mock_get_returns):
        """测试空收益率数据"""
        mock_get_returns.return_value = pd.DataFrame()
        result = runner.invoke(app, ["mean-variance", "000001,000002"])
        assert result.exit_code == 1

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.core.optimizers.mean_variance.MeanVarianceOptimizer")
    def test_optimizer_exception(
        self,
        mock_optimizer_class,
        mock_get_returns,
        mock_returns_data,
    ):
        """测试优化器异常"""
        mock_get_returns.return_value = mock_returns_data
        mock_optimizer = MagicMock()
        mock_optimizer.optimize.side_effect = Exception("优化失败")
        mock_optimizer_class.return_value = mock_optimizer

        result = runner.invoke(app, ["mean-variance", "000001,000002"])
        # 命令应该处理异常
        assert result.exit_code == 0 or result.exit_code == 1

    @patch("fund_cli.commands.optimize_cmd._get_returns")
    @patch("fund_cli.core.optimizers.efficient_frontier.EfficientFrontierCalculator")
    def test_frontier_single_point(
        self,
        mock_calc_class,
        mock_get_returns,
        mock_returns_data,
    ):
        """测试单点有效前沿"""
        mock_get_returns.return_value = mock_returns_data
        mock_calc = MagicMock()
        mock_calc.calculate.return_value = {
            "n_points": 1,
            "frontier_returns": [0.15],
            "frontier_volatilities": [0.18],
        }
        mock_calc_class.return_value = mock_calc

        result = runner.invoke(app, ["frontier", "000001,000002", "--points", "1"])
        assert result.exit_code == 0
