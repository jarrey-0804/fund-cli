"""
单元测试 - 归因分析与组合分析
"""

import numpy as np
import pandas as pd
import pytest

from fund_cli.analysis.attribution import AttributionAnalyzer
from fund_cli.analysis.portfolio import PortfolioAnalyzer


class TestAttributionAnalyzer:
    """归因分析器测试"""

    @pytest.fixture
    def analyzer(self):
        return AttributionAnalyzer()

    @pytest.fixture
    def multi_asset_returns(self):
        """多资产收益率数据"""
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=252, freq="B")
        return pd.DataFrame(
            {
                "asset_a": np.random.normal(0.001, 0.02, 252),
                "asset_b": np.random.normal(0.0008, 0.015, 252),
                "asset_c": np.random.normal(0.0005, 0.01, 252),
            },
            index=dates,
        )

    def test_simple_decomposition(self, analyzer, multi_asset_returns):
        """测试简单收益率分解"""
        result = analyzer.analyze(multi_asset_returns)

        assert "asset_a" in result
        assert "asset_b" in result
        assert "asset_c" in result

        for asset_data in result.values():
            assert "total_return" in asset_data
            assert "annualized_return" in asset_data
            assert "volatility" in asset_data

    def test_brinson_attribution(self, analyzer, multi_asset_returns):
        """测试 Brinson 归因分析"""
        benchmark_weights = {"asset_a": 0.5, "asset_b": 0.3, "asset_c": 0.2}
        portfolio_weights = {"asset_a": 0.4, "asset_b": 0.4, "asset_c": 0.2}

        result = analyzer.analyze(
            multi_asset_returns,
            benchmark_weights=benchmark_weights,
            portfolio_weights=portfolio_weights,
        )

        assert "allocation_effect" in result
        assert "selection_effect" in result
        assert "interaction_effect" in result
        assert "total_active_return" in result

    def test_get_metrics(self, analyzer):
        """测试获取指标列表"""
        metrics = analyzer.get_metrics()
        assert "allocation_effect" in metrics
        assert "total_active_return" in metrics


class TestPortfolioAnalyzer:
    """组合分析器测试"""

    @pytest.fixture
    def analyzer(self):
        return PortfolioAnalyzer()

    @pytest.fixture
    def multi_asset_returns(self):
        """多资产收益率数据"""
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=252, freq="B")
        return pd.DataFrame(
            {
                "asset_a": np.random.normal(0.001, 0.02, 252),
                "asset_b": np.random.normal(0.0008, 0.015, 252),
                "asset_c": np.random.normal(0.0005, 0.01, 252),
            },
            index=dates,
        )

    def test_equal_weight_portfolio(self, analyzer, multi_asset_returns):
        """测试等权组合分析"""
        result = analyzer.analyze(multi_asset_returns)

        assert "portfolio_return" in result
        assert "portfolio_volatility" in result
        assert "portfolio_sharpe" in result
        assert "diversification_ratio" in result
        assert "average_correlation" in result
        assert result["asset_count"] == 3

    def test_custom_weights(self, analyzer, multi_asset_returns):
        """测试自定义权重"""
        weights = {"asset_a": 0.6, "asset_b": 0.3, "asset_c": 0.1}
        result = analyzer.analyze(multi_asset_returns, weights=weights)

        assert result["weights"] == weights
        assert result["asset_count"] == 3

    def test_diversification_ratio(self, analyzer, multi_asset_returns):
        """测试风险分散度"""
        result = analyzer.analyze(multi_asset_returns)

        # DR 应该 > 1（分散化有效）
        assert result["diversification_ratio"] >= 1.0

    def test_contribution_analysis(self, analyzer, multi_asset_returns):
        """测试收益贡献分析"""
        weights = {"asset_a": 0.5, "asset_b": 0.3, "asset_c": 0.2}
        result = analyzer.analyze(multi_asset_returns, weights=weights)

        contribution = result["contribution"]
        assert "asset_a" in contribution
        assert "asset_b" in contribution
        assert "asset_c" in contribution

        for asset_contrib in contribution.values():
            assert "weight" in asset_contrib
            assert "return" in asset_contrib
            assert "contribution" in asset_contrib

    def test_get_metrics(self, analyzer):
        """测试获取指标列表"""
        metrics = analyzer.get_metrics()
        assert "portfolio_return" in metrics
        assert "diversification_ratio" in metrics
