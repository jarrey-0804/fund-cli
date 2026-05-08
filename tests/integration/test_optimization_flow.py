"""组合优化集成测试"""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def multi_fund_returns():
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=252, freq="B")
    return pd.DataFrame(
        {
            "000001": np.random.normal(0.001, 0.02, 252),
            "000002": np.random.normal(0.0008, 0.015, 252),
            "000003": np.random.normal(0.0012, 0.025, 252),
            "000005": np.random.normal(0.0005, 0.012, 252),
            "000010": np.random.normal(0.0009, 0.018, 252),
        },
        index=dates,
    )


class TestOptimizationFlow:
    def test_mean_variance_flow(self, multi_fund_returns):
        """完整均值方差优化流程"""
        from fund_cli.core.optimizers.mean_variance import MeanVarianceOptimizer
        from fund_cli.data.models import OptimizationConstraint

        opt = MeanVarianceOptimizer(risk_free_rate=0.03)
        constraints = OptimizationConstraint(min_weight=0.05, max_weight=0.5)
        result = opt.optimize(multi_fund_returns, constraints)

        assert "weights" in result
        assert len(result["weights"]) == 5
        total = sum(result["weights"].values())
        assert total == pytest.approx(1.0, abs=0.05)

    def test_multi_method_comparison(self, multi_fund_returns):
        """多方法对比"""
        from fund_cli.core.optimizers.max_sharpe import MaxSharpeOptimizer
        from fund_cli.core.optimizers.mean_variance import MeanVarianceOptimizer
        from fund_cli.core.optimizers.risk_parity import RiskParityOptimizer

        mv = MeanVarianceOptimizer()
        ms = MaxSharpeOptimizer()
        rp = RiskParityOptimizer()

        r_mv = mv.optimize(multi_fund_returns)
        r_ms = ms.optimize(multi_fund_returns)
        r_rp = rp.optimize(multi_fund_returns)

        for r in [r_mv, r_ms, r_rp]:
            assert "weights" in r
            assert "sharpe_ratio" in r

    def test_efficient_frontier_flow(self, multi_fund_returns):
        """有效前沿计算流程"""
        from fund_cli.core.optimizers.efficient_frontier import EfficientFrontierCalculator

        calc = EfficientFrontierCalculator()
        result = calc.calculate(multi_fund_returns, n_points=20)

        assert result["n_points"] > 0
        assert len(result["frontier_returns"]) == len(result["frontier_volatilities"])

    def test_backtest_flow(self, multi_fund_returns):
        """回测流程"""
        from fund_cli.analysis.backtest import BacktestAnalyzer

        analyzer = BacktestAnalyzer()
        weights = {
            "000001": 0.3,
            "000002": 0.2,
            "000003": 0.2,
            "000005": 0.15,
            "000010": 0.15,
        }
        result = analyzer.run_backtest(multi_fund_returns, weights=weights)

        assert "total_return" in result
        assert "sharpe_ratio" in result
        assert "max_drawdown" in result
        assert result["max_drawdown"] <= 0

    def test_backtest_equal_weight(self, multi_fund_returns):
        """等权回测"""
        from fund_cli.analysis.backtest import BacktestAnalyzer

        analyzer = BacktestAnalyzer()
        result = analyzer.run_backtest(multi_fund_returns)

        assert result["trading_days"] == 252
        assert 0 <= result["win_rate"] <= 100
