"""
集成测试 - 数据流
"""

import pytest

from fund_cli.analysis.performance import PerformanceAnalyzer
from fund_cli.analysis.risk import RiskAnalyzer
from fund_cli.core.data_manager import DataManager


@pytest.mark.integration
class TestDataFlow:
    """数据流集成测试"""

    @pytest.fixture
    def data_manager(self, temp_cache_dir):
        """创建数据管理器"""
        from fund_cli.data.cache import DataCache

        cache = DataCache(cache_dir=str(temp_cache_dir))
        return DataManager(cache=cache)

    def test_data_manager_initialization(self, data_manager):
        """测试数据管理器初始化"""
        assert data_manager is not None
        assert data_manager._cache is not None

    def test_cache_stats(self, data_manager):
        """测试缓存统计"""
        stats = data_manager.get_cache_stats()

        assert "size" in stats
        assert "directory" in stats

    def test_cache_clear(self, data_manager):
        """测试清空缓存"""
        data_manager.clear_cache()

        stats = data_manager.get_cache_stats()
        assert stats["size"] == 0


@pytest.mark.integration
class TestAnalysisWorkflow:
    """分析工作流集成测试"""

    def test_full_analysis_workflow(self, sample_nav_data):
        """测试完整分析流程"""
        # 1. 准备数据
        nav_series = sample_nav_data.set_index("nav_date")["unit_nav"]
        returns = nav_series.pct_change().dropna()

        # 2. 业绩分析
        perf_analyzer = PerformanceAnalyzer(risk_free_rate=0.03)
        perf_metrics = perf_analyzer.analyze(returns)

        # 3. 风险分析
        risk_analyzer = RiskAnalyzer()
        risk_metrics = risk_analyzer.analyze(returns)

        # 4. 验证结果
        assert "total_return" in perf_metrics
        assert "sharpe" in perf_metrics
        assert "max_drawdown" in perf_metrics

        assert "volatility_annual" in risk_metrics
        assert "var_95" in risk_metrics

    def test_analysis_with_benchmark(
        self,
        sample_nav_data,
        sample_benchmark_returns,
    ):
        """测试带基准的分析流程"""
        nav_series = sample_nav_data.set_index("nav_date")["unit_nav"]
        returns = nav_series.pct_change().dropna()

        # 对齐日期
        common_dates = returns.index.intersection(sample_benchmark_returns.index)
        returns_aligned = returns.loc[common_dates]
        benchmark_aligned = sample_benchmark_returns.loc[common_dates]

        analyzer = PerformanceAnalyzer()
        metrics = analyzer.analyze(returns_aligned, benchmark=benchmark_aligned)

        # 验证相对指标
        assert "alpha" in metrics
        assert "beta" in metrics
        assert "tracking_error" in metrics
