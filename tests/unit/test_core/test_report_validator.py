"""报告验证器单元测试."""

import pytest
from fund_cli.core.report_validator import ReportValidator, ReportValidationResult


class TestReportValidator:
    """ReportValidator 测试."""

    def setup_method(self):
        self.validator = ReportValidator()

    def test_validate_complete_metrics(self):
        """测试完整指标验证通过."""
        metrics = {
            "total_return": 10.0,
            "annualized_return": 8.0,
            "volatility": 15.0,
            "max_drawdown": -5.0,
            "sharpe_ratio": 1.2,
        }
        result = self.validator.validate_metrics(metrics)
        assert result.passed is True
        assert result.compliance_status == "pass"

    def test_validate_missing_metrics(self):
        """测试缺失指标验证失败."""
        metrics = {"total_return": 10.0}
        result = self.validator.validate_metrics(metrics)
        assert result.passed is False
        assert len(result.missing_fields) > 0

    def test_validate_none_metrics(self):
        """测试None值指标验证失败."""
        metrics = {
            "total_return": None,
            "annualized_return": None,
            "volatility": None,
            "max_drawdown": None,
            "sharpe_ratio": None,
        }
        result = self.validator.validate_metrics(metrics)
        assert result.passed is False

    def test_validate_high_nan_ratio(self):
        """测试高NaN比例产生警告."""
        metrics = {
            "total_return": 10.0,
            "annualized_return": None,
            "volatility": None,
            "max_drawdown": None,
            "sharpe_ratio": None,
            "extra1": None,
            "extra2": None,
            "extra3": None,
        }
        result = self.validator.validate_metrics(metrics)
        assert len(result.warnings) > 0

    def test_validate_template_data_complete(self):
        """测试完整模板数据."""
        data = {
            "fund_code": "000001",
            "report_date": "2026-01-01",
            "risk_overview": [{"name": "test"}],
        }
        result = self.validator.validate_template_data(data)
        assert result.passed is True

    def test_validate_template_data_missing(self):
        """测试缺失模板数据."""
        data = {}
        result = self.validator.validate_template_data(data)
        assert result.passed is False
        assert "fund_code" in result.missing_fields

    def test_check_disclaimer(self):
        """测试免责声明检查."""
        assert self.validator.check_disclaimer("仅供参考，不构成投资建议") is True
        assert self.validator.check_disclaimer("投资有风险") is True
        assert self.validator.check_disclaimer("这是一份报告") is False

    def test_validate_portfolio_type(self):
        """测试投资组合报告类型."""
        metrics = {
            "total_return": 10.0,
            "annualized_return": 8.0,
            "volatility": 15.0,
            "max_drawdown": -5.0,
            "sharpe_ratio": 1.2,
        }
        result = self.validator.validate_metrics(metrics, report_type="portfolio")
        assert result.passed is True

    def test_validate_template_data_empty_fund_code(self):
        """测试空基金代码."""
        data = {"fund_code": "", "report_date": "2026-01-01"}
        result = self.validator.validate_template_data(data)
        assert result.passed is False
        assert "fund_code" in result.missing_fields

    def test_validate_template_data_empty_risk_overview(self):
        """测试空risk_overview产生警告."""
        data = {
            "fund_code": "000001",
            "report_date": "2026-01-01",
            "risk_overview": [],
        }
        result = self.validator.validate_template_data(data)
        assert result.passed is True
        assert any("risk_overview" in w for w in result.warnings)

    def test_check_disclaimer_english(self):
        """测试英文免责声明."""
        assert self.validator.check_disclaimer("past performance is not indicative") is True

    def test_validate_missing_all_required(self):
        """测试所有必需指标缺失."""
        result = self.validator.validate_metrics({})
        assert result.passed is False
        assert len(result.missing_fields) == 5

    def test_validate_partial_missing(self):
        """测试部分指标缺失."""
        metrics = {"total_return": 10.0, "annualized_return": 8.0}
        result = self.validator.validate_metrics(metrics)
        assert result.passed is False
        assert "volatility" in result.missing_fields
        assert "max_drawdown" in result.missing_fields
        assert "sharpe_ratio" in result.missing_fields
