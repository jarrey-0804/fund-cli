"""
AI 分析增强模块.

提供基金数据的智能分析和自然语言摘要生成。
支持多种AI后端（OpenAI/本地模型/规则引擎）。
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from fund_cli.core.ai_validator import AIOutputValidator

logger = logging.getLogger(__name__)


class AIBackend(str, Enum):
    """AI后端类型."""

    RULE_BASED = "rule_based"  # 规则引擎（默认，无需API）
    OPENAI = "openai"  # OpenAI API
    LOCAL = "local"  # 本地模型


@dataclass
class AnalysisResult:
    """分析结果."""

    summary: str = ""  # 总体摘要
    risk_warning: str = ""  # 风险提示
    investment_advice: str = ""  # 投资建议
    performance_comment: str = ""  # 业绩评价
    highlights: list[str] = field(default_factory=list)  # 亮点
    concerns: list[str] = field(default_factory=list)  # 风险点
    confidence: float = 0.0  # 置信度 0-1
    data_source: str = ""  # 数据来源
    analysis_date: str = ""  # 分析日期


class AIBackendInterface(ABC):
    """AI后端接口."""

    @abstractmethod
    def analyze(self, context: str, instruction: str) -> str:
        """生成分析文本."""
        pass


class RuleBasedBackend(AIBackendInterface):
    """基于规则的分析引擎（无需外部API）."""

    def analyze(self, context: str, instruction: str) -> str:
        """基于规则生成分析文本."""
        # 简单的关键词匹配和模板生成
        # 实际实现中会解析context中的数据并生成结构化分析
        return self._generate_rule_based_analysis(context, instruction)

    def _generate_rule_based_analysis(self, context: str, instruction: str) -> str:
        """规则引擎分析."""
        # 基于instruction类型选择分析模板
        if "摘要" in instruction or "summary" in instruction.lower():
            return self._generate_summary(context)
        elif "风险" in instruction or "risk" in instruction.lower():
            return self._generate_risk_analysis(context)
        elif "建议" in instruction or "advice" in instruction.lower():
            return self._generate_advice(context)
        else:
            return self._generate_general_analysis(context)

    def _generate_summary(self, context: str) -> str:
        """生成摘要."""
        return f"基于当前数据分析，该基金表现{self._extract_performance(context)}。"

    def _generate_risk_analysis(self, context: str) -> str:
        """生成风险分析."""
        return "该基金存在一定的市场风险和流动性风险，建议关注市场波动对基金净值的影响。"

    def _generate_advice(self, context: str) -> str:
        """生成投资建议."""
        return "建议投资者根据自身风险承受能力和投资目标，合理配置该基金。"

    def _generate_general_analysis(self, context: str) -> str:
        """生成通用分析."""
        return (
            f"综合分析：{self._generate_summary(context)} {self._generate_risk_analysis(context)}"
        )

    def _extract_performance(self, context: str) -> str:
        """从上下文提取业绩描述."""
        # 简单实现：基于关键词判断
        positive_words = ["优秀", "良好", "增长", "正收益"]
        negative_words = ["亏损", "下降", "回撤", "负收益"]

        positive_count = sum(1 for w in positive_words if w in context)
        negative_count = sum(1 for w in negative_words if w in context)

        if positive_count > negative_count:
            return "较为优秀"
        elif negative_count > positive_count:
            return "欠佳，需关注风险"
        else:
            return "平稳"


class OpenAIBackend(AIBackendInterface):
    """OpenAI API后端."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self._api_key = api_key
        self._model = model
        self._client = None

    def _ensure_client(self) -> None:
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self._api_key)
            except ImportError as exc:
                raise RuntimeError("openai 包未安装，请运行: pip install openai") from exc

    def analyze(self, context: str, instruction: str) -> str:
        """使用OpenAI生成分析."""
        self._ensure_client()
        if self._client is None:
            return ""  # Should not happen
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位专业的基金分析师，请基于提供的数据进行专业分析。",
                },
                {"role": "user", "content": f"{instruction}\n\n数据：{context}"},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content or ""


class AIAnalyzer:
    """AI分析器."""

    def __init__(self, backend: AIBackend = AIBackend.RULE_BASED, **kwargs):
        self._backend = self._create_backend(backend, **kwargs)
        # 带TTL和大小限制的分析缓存
        self._analysis_cache: dict[str, tuple[datetime, Any]] = {}
        self._cache_ttl = 3600  # 1小时过期
        self._cache_max_size = 200  # 最大缓存条目数

    def _get_cache_key(self, fund_code: str, metrics: dict[str, Any]) -> str:
        """生成分析缓存键.

        基于基金代码和部分关键指标生成缓存键
        """
        # 选取关键指标进行缓存
        key_metrics = {
            k: metrics.get(k)
            for k in ["total_return", "sharpe_ratio", "max_drawdown"]
            if k in metrics
        }
        return f"{fund_code}:{hash(str(sorted(key_metrics.items())))}"

    def _create_backend(self, backend: AIBackend, **kwargs) -> AIBackendInterface:
        if backend == AIBackend.RULE_BASED:
            return RuleBasedBackend()
        elif backend == AIBackend.OPENAI:
            return OpenAIBackend(**kwargs)
        else:
            raise ValueError(f"不支持的AI后端: {backend}")

    def analyze_fund(
        self,
        fund_code: str,
        fund_name: str,
        metrics: dict[str, Any],
        holdings: list[dict[str, Any]] | None = None,
        asset_allocation: dict[str, float] | None = None,
        use_cache: bool = True,
    ) -> AnalysisResult:
        """分析单只基金.

        Args:
            fund_code: 基金代码
            fund_name: 基金名称
            metrics: 基金指标
            holdings: 持仓数据
            asset_allocation: 资产配置
            use_cache: 是否使用缓存
        """
        # 检查缓存
        if use_cache:
            cache_key = self._get_cache_key(fund_code, metrics)
            if cache_key in self._analysis_cache:
                ts, cached_result = self._analysis_cache[cache_key]
                if datetime.now() - ts < timedelta(seconds=self._cache_ttl):
                    return cached_result
                else:
                    del self._analysis_cache[cache_key]

        context = self._build_fund_context(
            fund_code, fund_name, metrics, holdings, asset_allocation
        )

        summary = self._backend.analyze(context, "请生成该基金的总体摘要")
        risk = self._backend.analyze(context, "请分析该基金的风险")
        advice = self._backend.analyze(context, "请给出投资建议")
        performance = self._backend.analyze(context, "请评价该基金的业绩表现")

        highlights = self._extract_highlights(metrics)
        concerns = self._extract_concerns(metrics)

        result = AnalysisResult(
            summary=summary,
            risk_warning=risk,
            investment_advice=advice,
            performance_comment=performance,
            highlights=highlights,
            concerns=concerns,
            confidence=0.7 if isinstance(self._backend, RuleBasedBackend) else 0.9,
            data_source=fund_code,
            analysis_date=date.today().strftime("%Y-%m-%d"),
        )

        # Validate AI output
        validator = AIOutputValidator()
        validation = validator.validate(result.summary, metrics)
        if not validation.passed:
            logger.warning("AI输出验证警告: %s", validation.issues)
            result.confidence *= validation.confidence_score

        # 存入缓存（带大小限制）
        if use_cache:
            cache_key = self._get_cache_key(fund_code, metrics)
            # LRU 淘汰
            if len(self._analysis_cache) >= self._cache_max_size:
                oldest_key = next(iter(self._analysis_cache))
                del self._analysis_cache[oldest_key]
            self._analysis_cache[cache_key] = (datetime.now(), result)

        return result

    def clear_cache(self) -> None:
        """清空分析缓存."""
        self._analysis_cache.clear()

    def analyze_portfolio(
        self,
        funds: list[dict[str, Any]],
        portfolio_metrics: dict[str, Any],
    ) -> AnalysisResult:
        """分析投资组合."""
        context = f"组合包含{len(funds)}只基金，组合指标：{portfolio_metrics}"

        summary = self._backend.analyze(context, "请生成该投资组合的总体摘要")
        risk = self._backend.analyze(context, "请分析该投资组合的风险")

        return AnalysisResult(
            summary=summary,
            risk_warning=risk,
            confidence=0.7 if isinstance(self._backend, RuleBasedBackend) else 0.9,
            analysis_date=date.today().strftime("%Y-%m-%d"),
        )

    def _build_fund_context(self, fund_code, fund_name, metrics, holdings, asset_allocation) -> str:
        """构建分析上下文."""
        parts = [f"基金{fund_name}({fund_code})"]
        parts.append(f"核心指标: {metrics}")
        if holdings:
            parts.append(f"前十大重仓: {holdings[:5]}")
        if asset_allocation:
            parts.append(f"资产配置: {asset_allocation}")
        return "\n".join(parts)

    def _extract_highlights(self, metrics: dict) -> list[str]:
        """提取亮点."""
        highlights = []
        total_return = metrics.get("total_return", 0)
        sharpe = metrics.get("sharpe_ratio", 0)
        max_dd = metrics.get("max_drawdown", 0)

        if total_return and total_return > 0.1:
            highlights.append(f"总收益率 {total_return:.2%}，表现优异")
        if sharpe and sharpe > 1.5:
            highlights.append(f"夏普比率 {sharpe:.2f}，风险调整收益优秀")
        if max_dd and max_dd > -0.1:
            highlights.append(f"最大回撤仅 {max_dd:.2%}，风控良好")
        return highlights or ["基金运作平稳"]

    def _extract_concerns(self, metrics: dict) -> list[str]:
        """提取风险点."""
        concerns = []
        max_dd = metrics.get("max_drawdown", 0)
        vol = metrics.get("volatility", 0)
        sharpe = metrics.get("sharpe_ratio", 0)

        if max_dd and max_dd < -0.2:
            concerns.append(f"最大回撤 {max_dd:.2%}，回撤较大")
        if vol and vol > 0.25:
            concerns.append(f"波动率 {vol:.2%}，波动较高")
        if sharpe is not None and sharpe < 0.5:
            concerns.append(f"夏普比率 {sharpe:.2f}，风险收益比不佳")
        return concerns or ["暂无显著风险点"]
