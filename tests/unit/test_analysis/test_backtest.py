"""组合回测引擎测试"""

import numpy as np
import pandas as pd
import pytest

from fund_cli.analysis.backtest import BacktestAnalyzer


@pytest.fixture
def analyzer():
    return BacktestAnalyzer()


@pytest.fixture
def sample_returns():
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=252, freq="B")
    return pd.DataFrame(
        {
            "fund_a": np.random.normal(0.001, 0.02, 252),
            "fund_b": np.random.normal(0.0008, 0.015, 252),
        },
        index=dates,
    )


class TestBacktestAnalyzer:
    def test_equal_weight(self, analyzer, sample_returns):
        result = analyzer.run_backtest(sample_returns)
        assert "total_return" in result
        assert "annual_return" in result
        assert "sharpe_ratio" in result
        assert "max_drawdown" in result
        assert "win_rate" in result

    def test_custom_weights(self, analyzer, sample_returns):
        weights = {"fund_a": 0.6, "fund_b": 0.4}
        result = analyzer.run_backtest(sample_returns, weights=weights)
        assert result["total_return"] is not None

    def test_weights_sum_validation(self, analyzer, sample_returns):
        weights = {"fund_a": 0.7, "fund_b": 0.3}
        result = analyzer.run_backtest(sample_returns, weights=weights)
        assert isinstance(result["total_return"], float)

    def test_win_rate_range(self, analyzer, sample_returns):
        result = analyzer.run_backtest(sample_returns)
        assert 0 <= result["win_rate"] <= 100

    def test_max_drawdown_negative(self, analyzer, sample_returns):
        result = analyzer.run_backtest(sample_returns)
        assert result["max_drawdown"] <= 0

    def test_trading_days(self, analyzer, sample_returns):
        result = analyzer.run_backtest(sample_returns)
        assert result["trading_days"] == 252

    def test_get_metrics(self, analyzer):
        metrics = analyzer.get_metrics()
        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
