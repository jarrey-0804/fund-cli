"""质量门禁单元测试."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from fund_cli.core.quality_gate import QualityGate
from fund_cli.core.data_quality import QualityReport, ExpectationResult


class TestQualityGate:
    """QualityGate 测试."""

    def setup_method(self):
        self.gate = QualityGate()

    def test_check_good_data(self):
        """测试良好数据通过门禁."""
        dates = pd.date_range("2024-01-01", periods=100, freq="B")
        nav_df = pd.DataFrame({
            "nav_date": dates,
            "unit_nav": 1.0 + np.cumsum(np.random.normal(0.001, 0.01, 100)),
            "daily_return": np.random.normal(0.001, 0.02, 100),
        })
        report = self.gate.check("000001", nav_df)
        assert report.score > 0
        assert isinstance(report.results, list)

    def test_check_empty_data(self):
        """测试空数据被拦截."""
        nav_df = pd.DataFrame()
        report = self.gate.check("000001", nav_df)
        assert report.blocked is True
        assert report.score == 0

    def test_check_insufficient_data(self):
        """测试数据量不足."""
        dates = pd.date_range("2024-01-01", periods=5, freq="B")
        nav_df = pd.DataFrame({
            "nav_date": dates,
            "unit_nav": [1.0, 1.01, 1.02, 1.03, 1.04],
            "daily_return": [0.01, 0.01, 0.01, 0.01, 0.01],
        })
        report = self.gate.check("000001", nav_df)
        # Should have error for insufficient data
        assert any(not r.passed and r.severity == "error" for r in report.results)

    def test_check_and_raise_passes(self):
        """测试check_and_raise通过时不抛异常."""
        dates = pd.date_range("2024-01-01", periods=100, freq="B")
        nav_df = pd.DataFrame({
            "nav_date": dates,
            "unit_nav": 1.0 + np.arange(100) * 0.001,
            "daily_return": np.full(100, 0.001),
        })
        # Should not raise
        report = self.gate.check_and_raise("000001", nav_df)
        assert report is not None

    def test_check_and_raise_blocked(self):
        """测试check_and_raise拦截时抛异常."""
        nav_df = pd.DataFrame()
        with pytest.raises(ValueError, match="数据质量检查未通过"):
            self.gate.check_and_raise("000001", nav_df)

    def test_check_with_missing_columns(self):
        """测试缺少必要列."""
        nav_df = pd.DataFrame({"date": ["2024-01-01"], "price": [1.0]})
        report = self.gate.check("000001", nav_df)
        # Should have error for missing required columns
        assert any("必要列" in r.name for r in report.results)

    def test_check_returns_quality_report(self):
        """测试返回QualityReport实例."""
        dates = pd.date_range("2024-01-01", periods=100, freq="B")
        nav_df = pd.DataFrame({
            "nav_date": dates,
            "unit_nav": 1.0 + np.arange(100) * 0.001,
            "daily_return": np.full(100, 0.001),
        })
        report = self.gate.check("000001", nav_df)
        assert isinstance(report, QualityReport)
        assert report.fund_code == "000001"
        assert isinstance(report.results, list)

    def test_check_empty_data_report_properties(self):
        """测试空数据报告属性."""
        nav_df = pd.DataFrame()
        report = self.gate.check("000001", nav_df)
        assert report.level == "poor"
        assert report.blocked is True
        assert report.error_count >= 1
