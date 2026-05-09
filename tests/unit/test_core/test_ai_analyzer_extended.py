# -*- coding: utf-8 -*-
"""
AI 分析器扩展单元测试

测试覆盖：
- analyze_fund 完整流程（metrics + holdings + asset_allocation）
- analyze_portfolio 多基金分析
- 缓存机制（命中 / 未命中 / 清空）
- 边界情况（空 metrics、None 值、异常数据）
- _build_fund_context 上下文构建
- AnalysisResult 数据类完整性
- OpenAI 后端 mock 测试
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from fund_cli.core.ai_analyzer import (
    AIBackend,
    AIAnalyzer,
    AnalysisResult,
    OpenAIBackend,
    RuleBasedBackend,
)


# =============================================================================
# 测试类：analyze_fund 完整流程
# =============================================================================


class TestAnalyzeFundComplete:
    """测试 analyze_fund 完整数据分析流程"""

    def test_analyze_fund_complete_data(self):
        """测试传入完整 metrics + holdings + asset_allocation"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            fund_code="110011",
            fund_name="易方达中小盘混合",
            metrics={
                "total_return": 0.25,
                "annualized_return": 0.18,
                "volatility": 0.15,
                "sharpe_ratio": 1.8,
                "max_drawdown": -0.12,
                "alpha": 0.03,
                "beta": 0.85,
            },
            holdings=[
                {"code": "600519", "name": "贵州茅台", "proportion": 0.08},
                {"code": "000858", "name": "五粮液", "proportion": 0.05},
            ],
            asset_allocation={"stock": 0.65, "bond": 0.25, "cash": 0.10},
        )
        assert isinstance(result, AnalysisResult)
        assert result.summary != ""
        assert result.risk_warning != ""
        assert result.investment_advice != ""
        assert result.performance_comment != ""
        assert len(result.highlights) >= 2
        assert result.analysis_date != ""

    def test_analyze_fund_with_holdings_only(self):
        """测试仅传入 holdings"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            fund_code="000001",
            fund_name="测试基金",
            metrics={"total_return": 0.10},
            holdings=[
                {"code": "600519", "name": "贵州茅台", "proportion": 0.10},
            ],
        )
        assert isinstance(result, AnalysisResult)
        assert result.summary != ""

    def test_analyze_fund_with_asset_allocation_only(self):
        """测试仅传入资产配置"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            fund_code="000001",
            fund_name="测试基金",
            metrics={"total_return": 0.10},
            asset_allocation={"stock": 0.80, "bond": 0.15, "cash": 0.05},
        )
        assert isinstance(result, AnalysisResult)
        assert result.summary != ""

    def test_analyze_fund_result_data_source(self):
        """测试分析结果包含正确的数据来源"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund("110011", "测试", {"total_return": 0.10})
        assert result.data_source == "110011"

    def test_analyze_fund_result_confidence(self):
        """测试规则引擎后端置信度为 0.7"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund("000001", "测试", {"total_return": 0.10})
        assert result.confidence == 0.7

    def test_analyze_fund_result_date_format(self):
        """测试分析日期格式为 YYYY-MM-DD"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund("000001", "测试", {"total_return": 0.10})
        today_str = date.today().strftime("%Y-%m-%d")
        assert result.analysis_date == today_str


# =============================================================================
# 测试类：analyze_portfolio 多基金分析
# =============================================================================


class TestAnalyzePortfolio:
    """测试 analyze_portfolio 投资组合分析"""

    def test_analyze_portfolio_single_fund(self):
        """测试单只基金组合分析"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_portfolio(
            funds=[{"code": "000001", "name": "华夏成长"}],
            portfolio_metrics={"total_return": 0.12},
        )
        assert isinstance(result, AnalysisResult)
        assert result.summary != ""
        assert result.risk_warning != ""

    def test_analyze_portfolio_multiple_funds(self):
        """测试多只基金组合分析"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_portfolio(
            funds=[
                {"code": "000001", "name": "华夏成长"},
                {"code": "000002", "name": "华夏回报"},
                {"code": "110011", "name": "易方达中小盘"},
            ],
            portfolio_metrics={
                "total_return": 0.15,
                "sharpe_ratio": 1.6,
                "max_drawdown": -0.10,
            },
        )
        assert isinstance(result, AnalysisResult)
        assert result.summary != ""

    def test_analyze_portfolio_empty_funds(self):
        """测试空基金列表"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_portfolio(
            funds=[],
            portfolio_metrics={"total_return": 0.0},
        )
        assert isinstance(result, AnalysisResult)
        assert result.summary != ""

    def test_analyze_portfolio_confidence(self):
        """测试组合分析置信度"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_portfolio(
            funds=[{"code": "000001", "name": "华夏成长"}],
            portfolio_metrics={},
        )
        assert result.confidence == 0.7


# =============================================================================
# 测试类：缓存机制
# =============================================================================


class TestAnalyzerCache:
    """测试分析器缓存机制"""

    def test_analyze_fund_cache_hit(self):
        """测试连续分析相同基金命中缓存"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        metrics = {"total_return": 0.15, "sharpe_ratio": 1.2, "max_drawdown": -0.08}
        result1 = analyzer.analyze_fund("000001", "测试基金", metrics, use_cache=True)
        result2 = analyzer.analyze_fund("000001", "测试基金", metrics, use_cache=True)
        assert result1.summary == result2.summary
        assert result1.risk_warning == result2.risk_warning
        assert result1.investment_advice == result2.investment_advice
        assert result1 is result2  # 应该是同一个对象

    def test_analyze_fund_cache_different_metrics(self):
        """测试不同 metrics 不命中缓存"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result1 = analyzer.analyze_fund("000001", "测试基金", {"total_return": 0.15})
        result2 = analyzer.analyze_fund("000001", "测试基金", {"total_return": 0.25})
        # 不同指标，结果可能不同（至少不是同一个对象）
        assert result1 is not result2

    def test_analyze_fund_cache_different_fund(self):
        """测试不同基金代码不命中缓存"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        metrics = {"total_return": 0.15, "sharpe_ratio": 1.2}
        result1 = analyzer.analyze_fund("000001", "测试基金A", metrics)
        result2 = analyzer.analyze_fund("000002", "测试基金B", metrics)
        assert result1 is not result2

    def test_analyze_fund_no_cache(self):
        """测试禁用缓存时每次都重新分析"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        metrics = {"total_return": 0.15, "sharpe_ratio": 1.2}
        result1 = analyzer.analyze_fund("000001", "测试基金", metrics, use_cache=False)
        result2 = analyzer.analyze_fund("000001", "测试基金", metrics, use_cache=False)
        # 禁用缓存时，每次都创建新对象
        assert result1 is not result2

    def test_clear_cache(self):
        """测试清空缓存"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        analyzer.analyze_fund("000001", "测试", {"total_return": 0.1})
        assert len(analyzer._analysis_cache) > 0
        analyzer.clear_cache()
        assert len(analyzer._analysis_cache) == 0

    def test_clear_cache_then_reanalyze(self):
        """测试清空缓存后重新分析产生新结果"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        metrics = {"total_return": 0.15, "sharpe_ratio": 1.2}
        result1 = analyzer.analyze_fund("000001", "测试基金", metrics)
        analyzer.clear_cache()
        result2 = analyzer.analyze_fund("000001", "测试基金", metrics)
        # 清空缓存后重新分析，应该是新对象
        assert result1 is not result2
        # 但内容应该相同
        assert result1.summary == result2.summary


# =============================================================================
# 测试类：边界情况
# =============================================================================


class TestAnalyzerEdgeCases:
    """测试分析器边界情况"""

    def test_analyze_fund_empty_metrics(self):
        """测试空 metrics"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund("000001", "测试基金", {})
        assert isinstance(result, AnalysisResult)
        assert "基金运作平稳" in result.highlights

    def test_analyze_fund_zero_metrics(self):
        """测试所有指标为零"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            "000001",
            "测试基金",
            {"total_return": 0, "sharpe_ratio": 0, "max_drawdown": 0, "volatility": 0},
        )
        assert isinstance(result, AnalysisResult)
        assert result.summary != ""

    def test_analyze_fund_negative_return(self):
        """测试负收益"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            "000001",
            "测试基金",
            {"total_return": -0.20, "sharpe_ratio": 0.3, "max_drawdown": -0.35},
        )
        assert isinstance(result, AnalysisResult)
        assert len(result.concerns) >= 1

    def test_analyze_fund_high_volatility(self):
        """测试高波动率"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            "000001",
            "测试基金",
            {"total_return": 0.10, "volatility": 0.30},
        )
        assert isinstance(result, AnalysisResult)
        concerns_text = " ".join(result.concerns)
        assert "波动" in concerns_text

    def test_analyze_fund_large_drawdown(self):
        """测试大回撤"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            "000001",
            "测试基金",
            {"total_return": 0.05, "max_drawdown": -0.30},
        )
        assert isinstance(result, AnalysisResult)
        concerns_text = " ".join(result.concerns)
        assert "回撤" in concerns_text

    def test_analyze_fund_none_holdings(self):
        """测试 holdings 为 None"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            "000001",
            "测试基金",
            {"total_return": 0.10},
            holdings=None,
        )
        assert isinstance(result, AnalysisResult)

    def test_analyze_fund_none_asset_allocation(self):
        """测试 asset_allocation 为 None"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            "000001",
            "测试基金",
            {"total_return": 0.10},
            asset_allocation=None,
        )
        assert isinstance(result, AnalysisResult)

    def test_analyze_fund_all_none_optional(self):
        """测试所有可选参数为 None"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            "000001",
            "测试基金",
            {"total_return": 0.10},
            holdings=None,
            asset_allocation=None,
        )
        assert isinstance(result, AnalysisResult)
        assert result.summary != ""

    def test_analyze_fund_very_high_sharpe(self):
        """测试极高夏普比率"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            "000001",
            "测试基金",
            {"total_return": 0.30, "sharpe_ratio": 3.5, "max_drawdown": -0.05},
        )
        assert isinstance(result, AnalysisResult)
        assert len(result.highlights) >= 2

    def test_analyze_fund_low_sharpe(self):
        """测试低夏普比率"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        result = analyzer.analyze_fund(
            "000001",
            "测试基金",
            {"total_return": 0.02, "sharpe_ratio": 0.2},
        )
        assert isinstance(result, AnalysisResult)
        concerns_text = " ".join(result.concerns)
        assert "夏普" in concerns_text


# =============================================================================
# 测试类：_build_fund_context 上下文构建
# =============================================================================


class TestBuildFundContext:
    """测试 _build_fund_context 上下文构建"""

    def test_context_contains_fund_name_and_code(self):
        """测试上下文包含基金名称和代码"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        context = analyzer._build_fund_context("000001", "华夏成长", {}, None, None)
        assert "华夏成长" in context
        assert "000001" in context

    def test_context_contains_metrics(self):
        """测试上下文包含指标数据"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        context = analyzer._build_fund_context(
            "000001", "测试", {"total_return": 0.15}, None, None
        )
        assert "核心指标" in context
        assert "total_return" in context

    def test_context_contains_holdings(self):
        """测试上下文包含持仓数据"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        holdings = [{"code": "600519", "name": "贵州茅台", "proportion": 0.08}]
        context = analyzer._build_fund_context(
            "000001", "测试", {}, holdings, None
        )
        assert "重仓" in context
        assert "600519" in context

    def test_context_holdings_limited_to_5(self):
        """测试持仓数据限制为前5条"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        holdings = [{"code": f"60000{i}", "name": f"股票{i}", "proportion": 0.05} for i in range(10)]
        context = analyzer._build_fund_context(
            "000001", "测试", {}, holdings, None
        )
        # 应只包含前5条
        assert "600009" not in context
        assert "600004" in context

    def test_context_contains_asset_allocation(self):
        """测试上下文包含资产配置"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        context = analyzer._build_fund_context(
            "000001", "测试", {}, None, {"stock": 0.80, "bond": 0.15, "cash": 0.05}
        )
        assert "资产配置" in context

    def test_context_without_optional_data(self):
        """测试无可选数据时的上下文"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        context = analyzer._build_fund_context("000001", "测试", {}, None, None)
        assert "测试" in context
        assert "000001" in context
        assert "重仓" not in context
        assert "资产配置" not in context

    def test_context_empty_holdings_omitted(self):
        """测试空持仓列表不出现在上下文中"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        context = analyzer._build_fund_context("000001", "测试", {}, [], None)
        assert "重仓" not in context


# =============================================================================
# 测试类：AnalysisResult 数据类
# =============================================================================


class TestAnalysisResult:
    """测试 AnalysisResult 数据类完整性"""

    def test_default_values(self):
        """测试默认值"""
        result = AnalysisResult()
        assert result.summary == ""
        assert result.risk_warning == ""
        assert result.investment_advice == ""
        assert result.performance_comment == ""
        assert result.highlights == []
        assert result.concerns == []
        assert result.confidence == 0.0
        assert result.data_source == ""
        assert result.analysis_date == ""

    def test_custom_values(self):
        """测试自定义值"""
        result = AnalysisResult(
            summary="测试摘要",
            risk_warning="测试风险",
            investment_advice="测试建议",
            performance_comment="测试业绩",
            highlights=["亮点1", "亮点2"],
            concerns=["风险1"],
            confidence=0.85,
            data_source="000001",
            analysis_date="2024-01-01",
        )
        assert result.summary == "测试摘要"
        assert result.risk_warning == "测试风险"
        assert result.investment_advice == "测试建议"
        assert result.performance_comment == "测试业绩"
        assert result.highlights == ["亮点1", "亮点2"]
        assert result.concerns == ["风险1"]
        assert result.confidence == 0.85
        assert result.data_source == "000001"
        assert result.analysis_date == "2024-01-01"

    def test_highlights_mutable_default(self):
        """测试 highlights 列表默认值独立"""
        result1 = AnalysisResult()
        result2 = AnalysisResult()
        result1.highlights.append("新亮点")
        assert "新亮点" not in result2.highlights

    def test_concerns_mutable_default(self):
        """测试 concerns 列表默认值独立"""
        result1 = AnalysisResult()
        result2 = AnalysisResult()
        result1.concerns.append("新风险")
        assert "新风险" not in result2.concerns


# =============================================================================
# 测试类：OpenAI 后端 mock 测试
# =============================================================================


class TestOpenAIBackendMock:
    """测试 OpenAI 后端（使用 mock，不实际调用 API）"""

    def test_openai_backend_analyze(self):
        """测试 OpenAI 后端分析调用"""
        backend = OpenAIBackend(api_key="test-key")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="这是AI生成的分析结果。"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        backend._client = mock_client

        result = backend.analyze("基金数据", "请分析该基金")
        assert result == "这是AI生成的分析结果。"
        mock_client.chat.completions.create.assert_called_once()

    def test_openai_backend_analyze_empty_response(self):
        """测试 OpenAI 后端返回空内容"""
        backend = OpenAIBackend(api_key="test-key")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]
        mock_client.chat.completions.create.return_value = mock_response
        backend._client = mock_client

        result = backend.analyze("基金数据", "请分析该基金")
        assert result == ""

    def test_openai_backend_model_parameter(self):
        """测试 OpenAI 后端使用指定模型"""
        backend = OpenAIBackend(api_key="test-key", model="gpt-4")
        assert backend._model == "gpt-4"

    def test_openai_backend_ensure_client(self):
        """测试 _ensure_client 懒加载"""
        backend = OpenAIBackend(api_key="test-key")
        assert backend._client is None
        # 模拟 openai 包已安装，补丁延迟导入的 OpenAI 类
        with patch("openai.OpenAI") as MockOpenAI:
            mock_client = MagicMock()
            MockOpenAI.return_value = mock_client
            backend._ensure_client()
            MockOpenAI.assert_called_once_with(api_key="test-key")
            assert backend._client is mock_client

    def test_openai_backend_missing_package_raises(self):
        """测试 openai 包未安装时抛出 RuntimeError"""
        backend = OpenAIBackend(api_key="test-key")
        with patch("builtins.__import__", side_effect=ImportError("No module")):
            with pytest.raises(RuntimeError, match="openai 包未安装"):
                backend._ensure_client()

    def test_analyzer_with_openai_backend(self):
        """测试使用 OpenAI 后端的分析器"""
        analyzer = AIAnalyzer(backend=AIBackend.OPENAI, api_key="test-key")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="AI分析结果"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        analyzer._backend._client = mock_client

        result = analyzer.analyze_fund("000001", "测试基金", {"total_return": 0.15})
        assert isinstance(result, AnalysisResult)
        assert result.confidence == 0.9  # OpenAI 后端置信度 0.9

    def test_openai_backend_call_parameters(self):
        """测试 OpenAI 后端调用参数正确"""
        backend = OpenAIBackend(api_key="test-key", model="gpt-4o-mini")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="结果"))]
        mock_client.chat.completions.create.return_value = mock_response
        backend._client = mock_client

        backend.analyze("基金上下文数据", "请分析该基金的风险")

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4o-mini"
        assert call_args.kwargs["temperature"] == 0.3
        assert call_args.kwargs["max_tokens"] == 1000
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert "基金分析师" in messages[0]["content"]
        assert messages[1]["role"] == "user"


# =============================================================================
# 测试类：_extract_highlights 和 _extract_concerns
# =============================================================================


class TestExtractHighlightsAndConcerns:
    """测试亮点和风险点提取"""

    def test_highlights_all_good(self):
        """测试所有指标优秀时提取多个亮点"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        highlights = analyzer._extract_highlights({
            "total_return": 0.25,
            "sharpe_ratio": 2.0,
            "max_drawdown": -0.05,
        })
        assert len(highlights) == 3

    def test_highlights_no_good(self):
        """测试无优秀指标时返回默认"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        highlights = analyzer._extract_highlights({
            "total_return": 0.01,
            "sharpe_ratio": 0.5,
            "max_drawdown": -0.15,
        })
        assert highlights == ["基金运作平稳"]

    def test_concerns_all_bad(self):
        """测试所有指标差时提取多个风险点"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        concerns = analyzer._extract_concerns({
            "max_drawdown": -0.30,
            "volatility": 0.30,
            "sharpe_ratio": 0.2,
        })
        assert len(concerns) == 3

    def test_concerns_no_bad(self):
        """测试无风险指标时返回默认"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        concerns = analyzer._extract_concerns({
            "max_drawdown": -0.05,
            "volatility": 0.10,
            "sharpe_ratio": 1.5,
        })
        assert concerns == ["暂无显著风险点"]

    def test_concerns_zero_sharpe(self):
        """测试夏普比率为零"""
        analyzer = AIAnalyzer(backend=AIBackend.RULE_BASED)
        concerns = analyzer._extract_concerns({"sharpe_ratio": 0})
        assert len(concerns) >= 1
        assert "夏普" in " ".join(concerns)
