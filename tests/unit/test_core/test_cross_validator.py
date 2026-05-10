"""交叉验证器单元测试."""

import pytest
from fund_cli.core.cross_validator import CrossValidator, CrossValidationResult


class TestCrossValidator:
    """CrossValidator 测试."""

    def setup_method(self):
        self.validator = CrossValidator()

    def test_validate_identical_metrics(self):
        """测试相同指标验证通过."""
        perf = {"volatility": 0.15, "max_drawdown": -0.10, "sharpe_ratio": 1.5}
        risk = {"volatility": 0.15, "max_drawdown": -0.10, "sharpe_ratio": 1.5}
        results = self.validator.validate(perf, risk)
        summary = self.validator.get_summary(results)
        # validate checks all 5 CROSS_CHECK_METRICS; the 3 provided match, the other 2 are both None -> pass
        assert summary["passed"] == 5
        assert summary["failed"] == 0

    def test_validate_different_metrics(self):
        """测试差异指标验证失败."""
        perf = {"volatility": 0.20, "max_drawdown": -0.15}
        risk = {"volatility": 0.10, "max_drawdown": -0.05}
        results = self.validator.validate(perf, risk)
        summary = self.validator.get_summary(results)
        assert summary["failed"] == 2

    def test_validate_none_values(self):
        """测试None值处理."""
        perf = {"volatility": None, "max_drawdown": -0.10}
        risk = {"volatility": None, "max_drawdown": -0.10}
        results = self.validator.validate(perf, risk)
        summary = self.validator.get_summary(results)
        # Both None should pass
        assert summary["passed"] >= 1

    def test_validate_one_none(self):
        """测试单侧None值."""
        perf = {"volatility": 0.15}
        risk = {"volatility": None}
        results = self.validator.validate(perf, risk)
        summary = self.validator.get_summary(results)
        assert summary["failed"] == 1

    def test_validate_within_tolerance(self):
        """测试在容忍度范围内的差异."""
        perf = {"volatility": 0.1501}
        risk = {"volatility": 0.1500}
        results = self.validator.validate(perf, risk)
        assert all(r.passed for r in results)

    def test_custom_tolerance(self):
        """测试自定义容忍度."""
        validator = CrossValidator(custom_tolerance={"volatility": 0.001})
        perf = {"volatility": 0.151}
        risk = {"volatility": 0.150}
        results = validator.validate(perf, risk)
        assert not results[0].passed

    def test_get_summary(self):
        """测试摘要生成."""
        perf = {"volatility": 0.15, "max_drawdown": -0.10, "sharpe_ratio": 1.5}
        risk = {"volatility": 0.15, "max_drawdown": -0.10, "sharpe_ratio": 1.5}
        results = self.validator.validate(perf, risk)
        summary = self.validator.get_summary(results)
        assert summary["total"] == 5
        assert summary["pass_rate"] == 1.0
        assert len(summary["failed_metrics"]) == 0

    def test_result_dataclass(self):
        """测试结果数据类."""
        result = CrossValidationResult(
            metric_name="test",
            perf_value=1.0,
            risk_value=1.0,
            diff=0.0,
            diff_percent=0.0,
            passed=True,
            tolerance=0.01
        )
        assert result.passed is True
        assert result.metric_name == "test"

    def test_validate_all_cross_check_metrics(self):
        """测试所有CROSS_CHECK_METRICS指标都参与验证."""
        perf = {"volatility": 0.15, "max_drawdown": -0.10, "var_95": -0.05,
                "beta": 1.0, "sharpe_ratio": 1.5}
        risk = {"volatility": 0.15, "max_drawdown": -0.10, "var_95": -0.05,
                "beta": 1.0, "sharpe_ratio": 1.5}
        results = self.validator.validate(perf, risk)
        summary = self.validator.get_summary(results)
        assert summary["total"] == 5
        assert summary["passed"] == 5

    def test_get_summary_empty_results(self):
        """测试空结果列表的摘要."""
        summary = self.validator.get_summary([])
        assert summary["total"] == 0
        assert summary["pass_rate"] == 0

    def test_validate_zero_values(self):
        """测试零值处理."""
        perf = {"volatility": 0.0}
        risk = {"volatility": 0.0}
        results = self.validator.validate(perf, risk)
        assert all(r.passed for r in results)
