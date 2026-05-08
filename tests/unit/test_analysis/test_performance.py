"""
单元测试 - 分析模块
"""

import numpy as np
import pandas as pd
import pytest

from fund_cli.analysis.performance import PerformanceAnalyzer
from fund_cli.analysis.risk import RiskAnalyzer


class TestPerformanceAnalyzer:
    """业绩分析器测试"""

    @pytest.fixture
    def analyzer(self):
        return PerformanceAnalyzer(risk_free_rate=0.03)

    def test_analyze_basic_metrics(self, analyzer, sample_returns):
        """测试基础指标计算"""
        metrics = analyzer.analyze(sample_returns)

        # 检查必要指标存在
        assert "total_return" in metrics
        assert "cagr" in metrics
        assert "sharpe" in metrics
        assert "max_drawdown" in metrics
        assert "volatility" in metrics

    def test_analyze_with_benchmark(
        self,
        analyzer,
        sample_returns,
        sample_benchmark_returns,
    ):
        """测试带基准的分析"""
        metrics = analyzer.analyze(
            sample_returns,
            benchmark=sample_benchmark_returns,
        )

        assert "alpha" in metrics
        assert "beta" in metrics
        assert "tracking_error" in metrics
        assert "information_ratio" in metrics

    def test_get_metrics(self, analyzer):
        """测试获取指标列表"""
        metrics = analyzer.get_metrics()

        assert "total_return" in metrics
        assert "sharpe" in metrics
        assert "max_drawdown" in metrics

    def test_calculate_returns(self, analyzer, sample_nav_data):
        """测试收益率计算"""
        returns = analyzer.calculate_returns(sample_nav_data)

        assert isinstance(returns, pd.Series)
        assert len(returns) > 0

    def test_calculate_cumulative_return(self, analyzer, sample_returns):
        """测试累计收益率计算"""
        cum_return = analyzer.calculate_cumulative_return(sample_returns)

        assert isinstance(cum_return, pd.Series)
        assert len(cum_return) == len(sample_returns)

    def test_calculate_drawdown(self, analyzer, sample_returns):
        """测试回撤计算"""
        drawdown = analyzer.calculate_drawdown(sample_returns)

        assert isinstance(drawdown, pd.Series)
        # 回撤应该都是非正数
        assert (drawdown <= 0).all()


class TestRiskAnalyzer:
    """风险分析器测试"""

    @pytest.fixture
    def analyzer(self):
        return RiskAnalyzer()

    def test_analyze_basic_metrics(self, analyzer, sample_returns):
        """测试基础风险指标"""
        metrics = analyzer.analyze(sample_returns)

        assert "volatility_annual" in metrics
        assert "max_drawdown" in metrics
        assert "var_95" in metrics
        assert "skewness" in metrics
        assert "kurtosis" in metrics

    def test_max_drawdown_calculation(self, analyzer, sample_returns):
        """测试最大回撤计算"""
        max_dd = analyzer.max_drawdown(sample_returns)

        # 最大回撤应该是负数或零
        assert max_dd <= 0

    def test_var_calculation(self, analyzer, sample_returns):
        """测试 VaR 计算"""
        var_95 = analyzer.var(sample_returns, 0.95)
        var_99 = analyzer.var(sample_returns, 0.99)

        # VaR(99%) 应该比 VaR(95%) 更极端（更小）
        assert var_99 <= var_95

    def test_cvar_calculation(self, analyzer, sample_returns):
        """测试 CVaR 计算"""
        cvar_95 = analyzer.cvar(sample_returns, 0.95)
        var_95 = analyzer.var(sample_returns, 0.95)

        # CVaR 应该比 VaR 更极端（更小或相等）
        assert cvar_95 <= var_95

    def test_beta_calculation(
        self,
        analyzer,
        sample_returns,
        sample_benchmark_returns,
    ):
        """测试 Beta 计算"""
        beta = analyzer.beta(sample_returns, sample_benchmark_returns)

        # Beta 应该是有限数值
        assert np.isfinite(beta)

    def test_tracking_error(
        self,
        analyzer,
        sample_returns,
        sample_benchmark_returns,
    ):
        """测试跟踪误差计算"""
        te = analyzer.tracking_error(sample_returns, sample_benchmark_returns)

        # 跟踪误差应该是正数
        assert te >= 0

    def test_empty_returns(self, analyzer):
        """测试空数据处理"""
        empty_returns = pd.Series([], dtype=float)

        # 应该返回 0 或处理空数据
        max_dd = analyzer.max_drawdown(empty_returns)
        assert max_dd == 0.0
