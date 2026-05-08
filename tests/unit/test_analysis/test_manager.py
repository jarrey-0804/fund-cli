"""基金经理分析引擎测试"""

from datetime import date

import pytest

from fund_cli.analysis.manager import ManagerAnalyzer


@pytest.fixture
def analyzer():
    return ManagerAnalyzer()


@pytest.fixture
def sample_manager_data():
    return {
        "name": "张三",
        "fund_code": "000001",
        "fund_name": "华夏成长混合",
        "company": "华夏基金",
        "start_date": date(2020, 1, 15),
        "tenure_days": 1600,
        "total_return": 25.5,
        "annual_return": 8.2,
    }


@pytest.fixture
def multi_fund_manager_data():
    return {
        "name": "李四",
        "fund_code": "000002",
        "fund_name": "华夏回报混合",
        "company": "华夏基金",
        "start_date": date(2018, 6, 1),
        "tenure_days": 2500,
        "funds": [
            {"fund_name": "华夏回报混合", "total_return": 30.0},
            {"fund_name": "华夏优势混合", "total_return": 15.0},
            {"fund_name": "华夏精选混合", "total_return": 45.0},
        ],
    }


class TestManagerInfo:
    def test_normal_data(self, analyzer, sample_manager_data):
        result = analyzer.manager_info(sample_manager_data)
        assert result["name"] == "张三"
        assert result["fund_code"] == "000001"
        assert result["company"] == "华夏基金"

    def test_missing_fields(self, analyzer):
        result = analyzer.manager_info({})
        assert result["name"] == ""
        assert result["tenure_days"] == 0


class TestPerformanceStats:
    def test_single_fund(self, analyzer, sample_manager_data):
        result = analyzer.performance_stats(sample_manager_data)
        assert result["total_funds"] == 1
        assert result["avg_return"] == 8.2
        assert result["best_fund"] == "华夏成长混合"

    def test_multi_fund(self, analyzer, multi_fund_manager_data):
        result = analyzer.performance_stats(multi_fund_manager_data)
        assert result["total_funds"] == 3
        assert result["avg_return"] == pytest.approx(30.0, abs=0.01)
        assert result["best_fund"] == "华夏精选混合"
        assert result["best_return"] == 45.0

    def test_empty_data(self, analyzer):
        result = analyzer.performance_stats({})
        assert result["total_funds"] == 1
        assert result["avg_return"] == 0


class TestStabilityAnalysis:
    def test_long_tenure(self, analyzer, multi_fund_manager_data):
        result = analyzer.stability_analysis(multi_fund_manager_data)
        assert result["tenure_years"] > 5
        assert result["stability_level"] == "非常稳定"
        assert result["stability_score"] == 5

    def test_medium_tenure(self, analyzer, sample_manager_data):
        result = analyzer.stability_analysis(sample_manager_data)
        assert result["tenure_years"] > 3
        assert result["stability_level"] == "稳定"
        assert result["stability_score"] == 4

    def test_short_tenure(self, analyzer):
        data = {"tenure_days": 730}
        result = analyzer.stability_analysis(data)
        assert result["stability_level"] == "一般"
        assert result["stability_score"] == 3

    def test_very_short_tenure(self, analyzer):
        data = {"tenure_days": 100}
        result = analyzer.stability_analysis(data)
        assert result["stability_level"] == "较新"
        assert result["stability_score"] == 2

    def test_multi_fund_flag(self, analyzer, multi_fund_manager_data):
        result = analyzer.stability_analysis(multi_fund_manager_data)
        assert result["multi_fund_manager"] is True
        assert result["managed_fund_count"] == 3


class TestAnalyze:
    def test_full_analysis(self, analyzer, sample_manager_data):
        result = analyzer.analyze(sample_manager_data)
        assert "info" in result
        assert "performance" in result
        assert "stability" in result


class TestGetMetrics:
    def test_metrics_list(self, analyzer):
        metrics = analyzer.get_metrics()
        assert "manager_info" in metrics
        assert "performance_stats" in metrics
        assert "stability_analysis" in metrics
