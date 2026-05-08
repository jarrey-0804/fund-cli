"""业绩分析增强测试"""

import numpy as np
import pandas as pd
import pytest

from fund_cli.analysis.performance import PerformanceAnalyzer


@pytest.fixture
def analyzer():
    return PerformanceAnalyzer(risk_free_rate=0.03)


@pytest.fixture
def sample_returns():
    np.random.seed(42)
    dates = pd.date_range("2022-01-01", periods=500, freq="B")
    return pd.Series(np.random.normal(0.001, 0.02, 500), index=dates)


class TestRollingPerformance:
    def test_normal_window(self, analyzer, sample_returns):
        result = analyzer.rolling_performance(sample_returns, window=60)
        assert not result.empty
        assert "rolling_return" in result.columns
        assert "rolling_volatility" in result.columns

    def test_short_data(self, analyzer):
        short = pd.Series(np.random.normal(0.001, 0.02, 30))
        result = analyzer.rolling_performance(short, window=60)
        assert result.empty

    def test_large_window(self, analyzer, sample_returns):
        result = analyzer.rolling_performance(sample_returns, window=252)
        assert not result.empty


class TestMonthlyDistribution:
    def test_normal_data(self, analyzer, sample_returns):
        result = analyzer.monthly_return_distribution(sample_returns)
        assert result["total_months"] > 0
        assert result["positive_months"] + result["negative_months"] <= result["total_months"]
        assert 0 <= result["win_rate"] <= 100

    def test_empty_data(self, analyzer):
        result = analyzer.monthly_return_distribution(pd.Series(dtype=float))
        assert result.get("total_months", 0) == 0


class TestScenarioAnalysis:
    def test_default_scenarios(self, analyzer, sample_returns):
        result = analyzer.scenario_analysis(sample_returns)
        assert "牛市" in result
        assert "熊市" in result
        for _name, data in result.items():
            assert "simulated_total_return" in data

    def test_custom_scenarios(self, analyzer, sample_returns):
        custom = {"custom_up": 0.30, "custom_down": -0.30}
        result = analyzer.scenario_analysis(sample_returns, scenarios=custom)
        assert "custom_up" in result


class TestPerformancePersistence:
    def test_sufficient_data(self, analyzer, sample_returns):
        result = analyzer.performance_persistence(sample_returns)
        assert 0 <= result["persistence_score"] <= 100
        rank_corr = result["rank_correlation"]
        if not pd.isna(rank_corr):
            assert -1 <= rank_corr <= 1

    def test_insufficient_data(self, analyzer):
        short = pd.Series(
            np.random.normal(0.001, 0.02, 10),
            index=pd.date_range("2024-01-01", periods=10, freq="B"),
        )
        result = analyzer.performance_persistence(short)
        assert result["persistence_score"] == 0
