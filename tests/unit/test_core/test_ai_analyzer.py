"""
AI分析器单元测试
"""
import pytest

from fund_cli.core.ai_analyzer import (
    AIAnalyzer,
    AIBackend,
    AnalysisResult,
    OpenAIBackend,
    RuleBasedBackend,
)


class TestRuleBasedBackend:
    """测试规则引擎后端"""

    def test_init(self):
        backend = RuleBasedBackend()
        assert backend is not None

    def test_analyze_summary(self):
        backend = RuleBasedBackend()
        result = backend.analyze("基金收益率15%", "请生成该基金的总体摘要")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_analyze_risk(self):
        backend = RuleBasedBackend()
        result = backend.analyze("基金波动率20%", "请分析该基金的风险")
        assert "风险" in result

    def test_analyze_advice(self):
        backend = RuleBasedBackend()
        result = backend.analyze("基金数据", "请给出投资建议")
        assert "建议" in result

    def test_analyze_general(self):
        backend = RuleBasedBackend()
        result = backend.analyze("基金数据", "请分析该基金")
        assert isinstance(result, str)

    def test_positive_performance(self):
        backend = RuleBasedBackend()
        result = backend._extract_performance("该基金增长良好，正收益优秀")
        assert "优秀" in result

    def test_negative_performance(self):
        backend = RuleBasedBackend()
        result = backend._extract_performance("基金亏损下降回撤")
        assert "欠佳" in result


class TestAIAnalyzer:
    """测试AI分析器"""

    def test_init_default(self):
        analyzer = AIAnalyzer()
        assert analyzer is not None

    def test_init_with_backend(self):
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        assert analyzer is not None

    def test_analyze_fund(self):
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            fund_code="000001",
            fund_name="华夏成长混合",
            metrics={"total_return": 0.15, "sharpe_ratio": 1.5, "max_drawdown": -0.08},
        )
        assert isinstance(result, AnalysisResult)
        assert result.summary != ""
        assert result.risk_warning != ""
        assert result.analysis_date != ""

    def test_analyze_fund_with_holdings(self):
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            fund_code="000001",
            fund_name="华夏成长混合",
            metrics={"total_return": 0.15},
            holdings=[{"code": "600519", "name": "贵州茅台", "proportion": 0.05}],
        )
        assert isinstance(result, AnalysisResult)

    def test_analyze_portfolio(self):
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_portfolio(
            funds=[{"code": "000001", "name": "华夏成长"}],
            portfolio_metrics={"total_return": 0.12},
        )
        assert isinstance(result, AnalysisResult)

    def test_extract_highlights_good(self):
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        highlights = analyzer._extract_highlights({
            "total_return": 0.15, "sharpe_ratio": 1.8, "max_drawdown": -0.05
        })
        assert len(highlights) >= 2

    def test_extract_concerns_bad(self):
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        concerns = analyzer._extract_concerns({
            "max_drawdown": -0.25, "volatility": 0.30, "sharpe_ratio": 0.3
        })
        assert len(concerns) >= 2

    def test_extract_highlights_neutral(self):
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        highlights = analyzer._extract_highlights({"total_return": 0.01})
        assert len(highlights) >= 1

    def test_confidence_rule_based(self):
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund("000001", "测试", {})
        assert result.confidence == 0.7

    def test_unsupported_backend(self):
        with pytest.raises(ValueError):
            AIAnalyzer(backend="unsupported")


class TestOpenAIBackend:
    """测试OpenAI后端"""

    def test_init_without_api_key(self):
        backend = OpenAIBackend()
        assert backend._model == "gpt-4o-mini"

    def test_missing_openai_package(self):
        backend = OpenAIBackend()
        # 不安装openai时调用analyze应该抛出RuntimeError
        try:
            import openai  # noqa: F401
        except ImportError:
            with pytest.raises(RuntimeError, match="openai 包未安装"):
                backend.analyze("test", "test")
