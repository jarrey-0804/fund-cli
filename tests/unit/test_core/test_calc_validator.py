"""计算结果验证器单元测试."""

from fund_cli.core.calc_validator import REASONABLE_BOUNDS, CalcValidator


class TestCalcValidator:
    """CalcValidator 测试."""

    def setup_method(self):
        self.validator = CalcValidator()

    def test_validate_normal_sharpe(self):
        """测试正常夏普比率."""
        result = self.validator.validate_metric("sharpe_ratio", 1.5)
        assert result.passed is True

    def test_validate_extreme_sharpe(self):
        """测试极端夏普比率."""
        result = self.validator.validate_metric("sharpe_ratio", 10.0)
        assert result.passed is False
        assert "sharpe_ratio" in result.message

    def test_validate_negative_volatility(self):
        """测试负波动率."""
        result = self.validator.validate_metric("volatility", -0.1)
        assert result.passed is False

    def test_validate_nan_value(self):
        """测试NaN值."""
        result = self.validator.validate_metric("sharpe_ratio", float("nan"))
        assert result.passed is False
        assert "NaN" in result.message

    def test_validate_none_value(self):
        """测试None值."""
        result = self.validator.validate_metric("sharpe_ratio", None)
        assert result.passed is False

    def test_validate_unknown_metric(self):
        """测试未知指标跳过验证."""
        result = self.validator.validate_metric("unknown_metric", 999.0)
        assert result.passed is True
        assert "跳过" in result.message

    def test_validate_metrics_batch(self):
        """测试批量验证."""
        metrics = {
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.10,
            "volatility": 0.15,
            "annualized_return": 0.08,
        }
        results = self.validator.validate_metrics(metrics)
        assert len(results) == 4
        assert all(r.passed for r in results)

    def test_check_nan_ratio_pass(self):
        """测试NaN比例检查通过."""
        metrics = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0, "e": 5.0}
        passed, msg = self.validator.check_nan_ratio(metrics, threshold=0.2)
        assert passed is True

    def test_check_nan_ratio_fail(self):
        """测试NaN比例检查失败."""
        metrics = {"a": None, "b": None, "c": None, "d": None, "e": 5.0}
        passed, msg = self.validator.check_nan_ratio(metrics, threshold=0.2)
        assert passed is False

    def test_get_summary(self):
        """测试验证摘要."""
        metrics = {"sharpe_ratio": 1.5, "max_drawdown": -0.10}
        results = self.validator.validate_metrics(metrics)
        summary = self.validator.get_summary(results)
        assert summary["total"] == 2
        assert summary["passed"] == 2
        assert summary["pass_rate"] == 1.0

    def test_custom_bounds(self):
        """测试自定义边界."""
        validator = CalcValidator(custom_bounds={"sharpe_ratio": (0, 2)})
        result = validator.validate_metric("sharpe_ratio", 2.5)
        assert result.passed is False

    def test_all_bounds_have_valid_range(self):
        """测试所有预定义边界合理性."""
        for name, (lower, upper) in REASONABLE_BOUNDS.items():
            assert lower < upper, f"{name}: lower={lower} >= upper={upper}"

    def test_validate_metrics_batch_skips_none(self):
        """测试批量验证跳过None值."""
        metrics = {
            "sharpe_ratio": 1.5,
            "max_drawdown": None,
            "volatility": 0.15,
        }
        results = self.validator.validate_metrics(metrics)
        # validate_metrics skips None values, so only 2 results
        assert len(results) == 2

    def test_check_nan_ratio_empty(self):
        """测试空指标NaN比例检查."""
        passed, msg = self.validator.check_nan_ratio({})
        assert passed is True

    def test_validate_negative_max_drawdown(self):
        """测试负最大回撤在合理范围内."""
        result = self.validator.validate_metric("max_drawdown", -0.10)
        assert result.passed is True

    def test_validate_positive_max_drawdown(self):
        """测试正最大回撤不在合理范围内."""
        result = self.validator.validate_metric("max_drawdown", 0.10)
        assert result.passed is False

    def test_get_summary_with_failures(self):
        """测试包含失败的验证摘要."""
        metrics = {"sharpe_ratio": 10.0, "max_drawdown": -0.10}
        results = self.validator.validate_metrics(metrics)
        summary = self.validator.get_summary(results)
        assert summary["total"] == 2
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert len(summary["warnings"]) == 1
