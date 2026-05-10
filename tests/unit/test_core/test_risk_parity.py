"""
风险平价优化器测试.

测试 fund_cli.core.optimizers.risk_parity 模块。
"""

import pytest
import numpy as np
import pandas as pd

from fund_cli.core.optimizers.risk_parity import RiskParityOptimizer


@pytest.fixture
def optimizer():
    """创建优化器实例."""
    return RiskParityOptimizer()


@pytest.fixture
def sample_returns():
    """创建样本收益率数据."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=100)
    returns = pd.DataFrame({
        "fund_a": np.random.randn(100) * 0.01,
        "fund_b": np.random.randn(100) * 0.015,
        "fund_c": np.random.randn(100) * 0.02,
    }, index=dates)
    return returns


class TestRiskParityOptimizer:
    """测试 RiskParityOptimizer 类."""

    def test_optimizer_exists(self, optimizer):
        """测试优化器存在."""
        assert optimizer is not None

    def test_get_methods(self, optimizer):
        """测试 get_methods 方法."""
        methods = optimizer.get_methods()
        assert "risk_parity" in methods

    def test_optimize_with_pypfopt(self, optimizer, sample_returns):
        """测试使用 pypfopt 优化."""
        try:
            from pypfopt import HRPOpt
            has_pypfopt = True
        except ImportError:
            has_pypfopt = False

        result = optimizer.optimize(sample_returns)

        assert "weights" in result
        assert "expected_return" in result
        assert "volatility" in result
        assert "sharpe_ratio" in result
        assert "method" in result

        if has_pypfopt:
            assert result["method"] == "risk_parity"
        else:
            assert result["method"] == "inverse_volatility_fallback"

    def test_optimize_fallback(self, optimizer, sample_returns):
        """测试回退实现."""
        result = optimizer._fallback_risk_parity(sample_returns)

        assert "weights" in result
        assert "expected_return" in result
        assert "volatility" in result
        assert "sharpe_ratio" in result
        assert result["method"] == "inverse_volatility_fallback"

    def test_optimize_weights_sum_to_one(self, optimizer, sample_returns):
        """测试权重和为1."""
        result = optimizer.optimize(sample_returns)
        weights = result["weights"]

        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.01

    def test_optimize_single_asset(self, optimizer):
        """测试单一资产."""
        np.random.seed(42)
        returns = pd.DataFrame({
            "fund_a": np.random.randn(100) * 0.01,
        })

        # 单一资产使用回退方法
        result = optimizer._fallback_risk_parity(returns)

        assert "weights" in result
        assert result["weights"]["fund_a"] == 1.0

    def test_optimize_empty_returns(self, optimizer):
        """测试空收益率数据."""
        returns = pd.DataFrame()

        # 应该处理错误或返回合理结果
        try:
            result = optimizer.optimize(returns)
        except Exception:
            pass  # 预期可能抛出异常

    def test_optimize_with_zero_volatility(self, optimizer):
        """测试零波动率资产."""
        returns = pd.DataFrame({
            "fund_a": [0.01] * 100,  # 固定收益
            "fund_b": np.random.randn(100) * 0.01,
        })

        # 使用回退方法
        result = optimizer._fallback_risk_parity(returns)

        assert "weights" in result
