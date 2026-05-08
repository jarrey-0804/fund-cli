"""组合优化器测试"""

import numpy as np
import pandas as pd
import pytest

from fund_cli.core.optimizers.efficient_frontier import EfficientFrontierCalculator
from fund_cli.core.optimizers.max_sharpe import MaxSharpeOptimizer
from fund_cli.core.optimizers.mean_variance import MeanVarianceOptimizer
from fund_cli.core.optimizers.risk_parity import RiskParityOptimizer
from fund_cli.data.models import OptimizationConstraint


@pytest.fixture
def sample_returns():
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=252, freq="B")
    return pd.DataFrame(
        {
            "fund_a": np.random.normal(0.001, 0.02, 252),
            "fund_b": np.random.normal(0.0008, 0.015, 252),
            "fund_c": np.random.normal(0.0012, 0.025, 252),
        },
        index=dates,
    )


class TestMeanVarianceOptimizer:
    def test_optimize_3_assets(self, sample_returns):
        opt = MeanVarianceOptimizer()
        result = opt.optimize(sample_returns)
        assert "weights" in result
        assert len(result["weights"]) == 3
        assert result["method"] in ("mean_variance", "equal_weight_fallback")

    def test_weights_sum_to_one(self, sample_returns):
        opt = MeanVarianceOptimizer()
        result = opt.optimize(sample_returns)
        total = sum(result["weights"].values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_with_constraints(self, sample_returns):
        opt = MeanVarianceOptimizer()
        constraints = OptimizationConstraint(min_weight=0.1, max_weight=0.6)
        result = opt.optimize(sample_returns, constraints)
        for w in result["weights"].values():
            assert 0.1 - 0.01 <= w <= 0.6 + 0.01

    def test_empty_data(self):
        opt = MeanVarianceOptimizer()
        result = opt.optimize(pd.DataFrame())
        assert result["method"] == "equal_weight_fallback"

    def test_get_methods(self):
        opt = MeanVarianceOptimizer()
        assert "mean_variance" in opt.get_methods()


class TestMaxSharpeOptimizer:
    def test_optimize(self, sample_returns):
        opt = MaxSharpeOptimizer()
        result = opt.optimize(sample_returns)
        assert "weights" in result
        assert len(result["weights"]) == 3
        assert result["method"] in ("max_sharpe", "equal_weight_fallback")

    def test_weights_sum_to_one(self, sample_returns):
        opt = MaxSharpeOptimizer()
        result = opt.optimize(sample_returns)
        total = sum(result["weights"].values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_sharpe_positive(self, sample_returns):
        opt = MaxSharpeOptimizer()
        result = opt.optimize(sample_returns)
        assert result["sharpe_ratio"] > 0 or result["method"] == "equal_weight_fallback"

    def test_get_methods(self):
        opt = MaxSharpeOptimizer()
        assert "max_sharpe" in opt.get_methods()


class TestRiskParityOptimizer:
    def test_optimize(self, sample_returns):
        opt = RiskParityOptimizer()
        result = opt.optimize(sample_returns)
        assert "weights" in result
        assert len(result["weights"]) == 3

    def test_weights_sum_to_one(self, sample_returns):
        opt = RiskParityOptimizer()
        result = opt.optimize(sample_returns)
        total = sum(result["weights"].values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_all_weights_positive(self, sample_returns):
        opt = RiskParityOptimizer()
        result = opt.optimize(sample_returns)
        for w in result["weights"].values():
            assert w >= 0

    def test_get_methods(self):
        opt = RiskParityOptimizer()
        assert "risk_parity" in opt.get_methods()


class TestEfficientFrontierCalculator:
    def test_calculate(self, sample_returns):
        calc = EfficientFrontierCalculator()
        result = calc.calculate(sample_returns, n_points=20)
        assert "frontier_returns" in result
        assert "frontier_volatilities" in result
        assert result["n_points"] > 0

    def test_points_count(self, sample_returns):
        calc = EfficientFrontierCalculator()
        result = calc.calculate(sample_returns, n_points=30)
        assert result["n_points"] <= 30

    def test_volatilities_positive(self, sample_returns):
        calc = EfficientFrontierCalculator()
        result = calc.calculate(sample_returns)
        for v in result["frontier_volatilities"]:
            assert v >= 0
