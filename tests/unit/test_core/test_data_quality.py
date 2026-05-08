"""数据质量检查器测试"""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from fund_cli.core.data_quality import DataQualityChecker


@pytest.fixture
def sample_nav_data():
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=200, freq="B")
    nav = 1.0 + np.cumsum(np.random.normal(0.001, 0.01, 200))
    return pd.DataFrame(
        {
            "fund_code": "000001",
            "nav_date": dates,
            "unit_nav": nav,
            "accumulated_nav": nav * 1.5,
            "daily_return": np.random.normal(0.05, 1.5, 200),
        }
    )


@pytest.fixture
def nav_with_missing():
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    nav = pd.DataFrame(
        {
            "nav_date": dates,
            "unit_nav": np.random.uniform(0.8, 1.5, 100),
            "daily_return": np.random.normal(0, 1, 100),
        }
    )
    nav.loc[10:15, "daily_return"] = np.nan
    return nav


@pytest.fixture
def nav_with_anomalies():
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    nav = np.random.uniform(1.0, 1.5, 100)
    nav[50] = 50.0  # 异常值
    nav[80] = 0.001  # 异常值
    return pd.DataFrame({"nav_date": dates, "unit_nav": nav})


class TestCompleteness:
    def test_normal_data(self, sample_nav_data):
        checker = DataQualityChecker()
        result = checker.check_completeness(sample_nav_data)
        assert result["score"] > 80
        assert result["total_rows"] == 200

    def test_missing_values(self, nav_with_missing):
        checker = DataQualityChecker()
        result = checker.check_completeness(nav_with_missing)
        assert result["missing_values"]["daily_return"] == 6

    def test_empty_data(self):
        checker = DataQualityChecker()
        result = checker.check_completeness(pd.DataFrame())
        assert result["score"] == 0


class TestAccuracy:
    def test_normal_data(self, sample_nav_data):
        checker = DataQualityChecker()
        result = checker.check_accuracy(sample_nav_data)
        assert result["score"] > 80

    def test_anomalies_detected(self, nav_with_anomalies):
        checker = DataQualityChecker()
        result = checker.check_accuracy(nav_with_anomalies)
        assert result["anomaly_count"] >= 1

    def test_empty_data(self):
        checker = DataQualityChecker()
        result = checker.check_accuracy(pd.DataFrame())
        assert result["score"] == 100


class TestTimeliness:
    def test_recent_data(self, sample_nav_data):
        checker = DataQualityChecker()
        result = checker.check_timeliness(sample_nav_data)
        assert result["status"] in ("current", "recent", "outdated")

    def test_empty_data(self):
        checker = DataQualityChecker()
        result = checker.check_timeliness(pd.DataFrame())
        assert result["status"] == "unknown"


class TestBatchDownload:
    def test_batch_with_mock(self):
        class MockDM:
            def get_fund_nav(self, code, **kwargs):
                if code == "000001":
                    return pd.DataFrame({"nav_date": [date.today()]})
                raise Exception("not found")

        checker = DataQualityChecker.__new__(DataQualityChecker)
        checker._dm = MockDM()
        result = checker.batch_download(["000001", "999999"])
        assert result["total"] == 2
        assert result["success"] == 1
        assert result["failed"] == 1
