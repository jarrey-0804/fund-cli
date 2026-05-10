"""合规风控报告生成器单元测试."""

import pytest
import pandas as pd
import numpy as np
from datetime import date
from unittest.mock import MagicMock, patch

from fund_cli.core.reporters.risk_control_reporter import RiskControlReporter


class TestRiskControlReporter:
    """RiskControlReporter 测试."""

    def setup_method(self):
        self.reporter = RiskControlReporter()

    def test_generate_basic(self):
        """测试基本报告生成."""
        metrics = {
            "volatility": 0.15,
            "max_drawdown": -0.10,
            "sharpe_ratio": 1.2,
            "beta": 1.0,
            "var_95": -0.05,
        }
        nav_df = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=100, freq="B"),
            "unit_nav": 1.0 + np.arange(100) * 0.001,
        })

        content = self.reporter.generate(
            fund_code="000001",
            metrics=metrics,
            nav_data=nav_df,
        )

        assert content is not None
        assert "<!DOCTYPE html>" in content or "html" in content.lower()

    def test_build_risk_overview_normal(self):
        """测试风险概览正常指标."""
        metrics = {
            "volatility": 0.15,
            "max_drawdown": -0.10,
            "sharpe_ratio": 1.5,
            "beta": 1.0,
            "var_95": -0.05,
        }

        result = self.reporter._build_risk_overview(metrics)

        assert len(result) == 5
        assert all(item["status"] == "正常" for item in result)

    def test_build_risk_overview_warning(self):
        """测试风险概览警告指标."""
        metrics = {
            "volatility": 0.35,
            "max_drawdown": -0.25,
            "sharpe_ratio": -0.3,
            "beta": 1.5,
            "var_95": -0.15,
        }

        result = self.reporter._build_risk_overview(metrics)

        assert any(item["status"] == "警告" for item in result)

    def test_build_risk_overview_extreme(self):
        """测试风险概览极端指标."""
        metrics = {
            "volatility": 0.60,
            "max_drawdown": -0.50,
            "sharpe_ratio": -2.0,
            "beta": 3.0,
            "var_95": -0.30,
        }

        result = self.reporter._build_risk_overview(metrics)

        assert any(item["status"] == "异常" for item in result)

    def test_build_risk_overview_missing_metrics(self):
        """测试风险概览缺失指标."""
        metrics = {}

        result = self.reporter._build_risk_overview(metrics)

        assert len(result) == 0

    def test_build_concentration(self):
        """测试集中度分析."""
        metrics = {"stock_ratio": 0.6}

        result = self.reporter._build_concentration(metrics)

        assert len(result) == 3
        assert all("name" in item for item in result)
        assert all("value" in item for item in result)
        assert all("threshold" in item for item in result)

    def test_build_concentration_high_stock_ratio(self):
        """测试高股票仓位警告."""
        metrics = {"stock_ratio": 0.9}

        result = self.reporter._build_concentration(metrics)

        stock_item = next((item for item in result if item["name"] == "股票仓位"), None)
        assert stock_item is not None
        assert stock_item["status"] == "警告"

    def test_build_compliance_checks_complete(self):
        """测试合规检查完整数据."""
        nav_df = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=100, freq="B"),
            "unit_nav": 1.0 + np.arange(100) * 0.001,
        })
        metrics = {
            "volatility": 0.15,
            "max_drawdown": -0.10,
            "sharpe_ratio": 1.5,
        }

        result = self.reporter._build_compliance_checks(metrics, nav_df)

        assert len(result) == 5
        assert all("name" in item for item in result)
        assert all("passed" in item for item in result)

    def test_build_compliance_checks_empty_nav(self):
        """测试合规检查空净值数据."""
        metrics = {
            "volatility": 0.15,
            "max_drawdown": -0.10,
            "sharpe_ratio": 1.5,
        }

        result = self.reporter._build_compliance_checks(metrics, None)

        assert len(result) == 5
        data_complete = next((item for item in result if item["name"] == "数据完整性"), None)
        assert data_complete is not None
        assert data_complete["passed"] is False

    def test_build_compliance_checks_stale_data(self):
        """测试合规检查过期数据."""
        # 使用一年前的数据
        old_dates = pd.date_range("2023-01-01", periods=100, freq="B")
        nav_df = pd.DataFrame({
            "nav_date": old_dates,
            "unit_nav": 1.0 + np.arange(100) * 0.001,
        })
        metrics = {
            "volatility": 0.15,
            "max_drawdown": -0.10,
            "sharpe_ratio": 1.5,
        }

        result = self.reporter._build_compliance_checks(metrics, nav_df)

        timeliness = next((item for item in result if item["name"] == "数据时效性"), None)
        assert timeliness is not None
        assert timeliness["passed"] is False

    def test_build_compliance_checks_high_volatility(self):
        """测试合规检查高波动率."""
        nav_df = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=100, freq="B"),
            "unit_nav": 1.0 + np.arange(100) * 0.001,
        })
        metrics = {
            "volatility": 0.60,
            "max_drawdown": -0.10,
            "sharpe_ratio": 1.5,
        }

        result = self.reporter._build_compliance_checks(metrics, nav_df)

        vol_check = next((item for item in result if item["name"] == "波动率合规"), None)
        assert vol_check is not None
        assert vol_check["passed"] is False

    def test_build_compliance_checks_extreme_drawdown(self):
        """测试合规检查极端回撤."""
        nav_df = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=100, freq="B"),
            "unit_nav": 1.0 + np.arange(100) * 0.001,
        })
        metrics = {
            "volatility": 0.15,
            "max_drawdown": -0.50,
            "sharpe_ratio": 1.5,
        }

        result = self.reporter._build_compliance_checks(metrics, nav_df)

        mdd_check = next((item for item in result if item["name"] == "最大回撤合规"), None)
        assert mdd_check is not None
        assert mdd_check["passed"] is False

    def test_build_compliance_checks_missing_metrics(self):
        """测试合规检查缺失指标."""
        nav_df = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=100, freq="B"),
            "unit_nav": 1.0 + np.arange(100) * 0.001,
        })
        metrics = {}

        result = self.reporter._build_compliance_checks(metrics, nav_df)

        # 缺失指标的检查应该标记为失败
        assert any(not item["passed"] for item in result)

    def test_save(self, tmp_path):
        """测试保存报告."""
        content = "<html>Test Report</html>"
        output_path = str(tmp_path / "test_report.html")

        self.reporter.save(content, output_path)

        import os
        assert os.path.exists(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_get_formats(self):
        """测试获取支持的格式."""
        formats = self.reporter.get_formats()

        assert "html" in formats

    def test_generate_with_template(self):
        """测试使用自定义模板生成."""
        metrics = {
            "volatility": 0.15,
            "max_drawdown": -0.10,
            "sharpe_ratio": 1.2,
        }
        nav_df = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=100, freq="B"),
            "unit_nav": 1.0 + np.arange(100) * 0.001,
        })

        # 测试不使用自定义模板
        content = self.reporter.generate(
            fund_code="000001",
            metrics=metrics,
            nav_data=nav_df,
            template_path=None,
        )

        assert content is not None
        assert "<!DOCTYPE html>" in content or "html" in content.lower()
