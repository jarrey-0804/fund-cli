"""AI输出验证器单元测试."""

from fund_cli.core.ai_validator import AIOutputValidator, AIValidationResult


class TestAIOutputValidator:
    """AIOutputValidator 测试."""

    def setup_method(self):
        self.validator = AIOutputValidator()

    def test_validate_consistent_text(self):
        """测试一致文本验证通过."""
        text = "该基金总收益率：10.5%，夏普比率：1.2，最大回撤：-5.3%"
        metrics = {"total_return": 10.5, "sharpe_ratio": 1.2, "max_drawdown": -5.3}
        result = self.validator.validate(text, metrics)
        assert result.passed is True
        assert result.confidence_score == 1.0

    def test_validate_inconsistent_values(self):
        """测试不一致数值验证失败."""
        text = "该基金总收益率：50.0%"
        metrics = {"total_return": 10.0}
        result = self.validator.validate(text, metrics)
        assert result.passed is False
        assert len(result.issues) > 0

    def test_validate_missing_metrics_in_text(self):
        """测试文本中未提到指标不算错误."""
        text = "该基金表现良好"
        metrics = {"total_return": 10.0}
        result = self.validator.validate(text, metrics)
        assert result.passed is True

    def test_validate_summary_positive_with_negative_return(self):
        """测试负面收益但正面描述."""
        summary = "该基金表现优秀，收益稳健"
        metrics = {"total_return": -15.0, "sharpe_ratio": 0.3}
        result = self.validator.validate_summary_consistency(summary, metrics)
        assert result.passed is False

    def test_validate_summary_negative_with_positive_return(self):
        """测试正面收益正面描述."""
        summary = "该基金表现良好"
        metrics = {"total_return": 20.0, "sharpe_ratio": 1.5}
        result = self.validator.validate_summary_consistency(summary, metrics)
        assert result.passed is True

    def test_validate_empty_text(self):
        """测试空文本."""
        result = self.validator.validate("", {"total_return": 10.0})
        assert result.passed is True

    def test_validate_none_metrics(self):
        """测试None指标值."""
        text = "该基金总收益率：10%"
        metrics = {"total_return": None}
        result = self.validator.validate(text, metrics)
        assert result.passed is True

    def test_confidence_decreases_with_issues(self):
        """测试置信度随问题数降低."""
        text = "总收益率：50%，夏普比率：100"
        metrics = {"total_return": 10.0, "sharpe_ratio": 1.0}
        result = self.validator.validate(text, metrics)
        assert result.confidence_score < 1.0

    def test_validate_colon_format(self):
        """测试英文冒号格式."""
        text = "该基金总收益率:10.5%"
        metrics = {"total_return": 10.5}
        result = self.validator.validate(text, metrics)
        assert result.passed is True

    def test_validate_volatility(self):
        """测试波动率验证."""
        text = "该基金波动率：15.0%"
        metrics = {"volatility": 15.0}
        result = self.validator.validate(text, metrics)
        assert result.passed is True

    def test_validate_beta(self):
        """测试Beta验证."""
        text = "该基金beta：1.2"
        metrics = {"beta": 1.2}
        result = self.validator.validate(text, metrics)
        assert result.passed is True

    def test_result_dataclass_defaults(self):
        """测试结果数据类默认值."""
        result = AIValidationResult(passed=True)
        assert result.passed is True
        assert result.issues == []
        assert result.confidence_score == 1.0

    def test_validate_summary_low_sharpe(self):
        """测试低夏普比率但正面描述."""
        summary = "该基金表现优秀"
        metrics = {"total_return": 5.0, "sharpe_ratio": 0.3}
        result = self.validator.validate_summary_consistency(summary, metrics)
        assert result.passed is False
        assert any("夏普比率" in issue for issue in result.issues)
