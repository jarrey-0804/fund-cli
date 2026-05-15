"""
智能选基助手

基于自然语言理解和多因子模型的智能基金推荐系统。
帮助用户从数千只基金中快速找到符合需求的基金。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import pandas as pd

from fund_cli.core.ai_validator import AIOutputValidator
from fund_cli.core.data_manager import DataManager
from fund_cli.data.models import FundFilter, FundType

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """风险等级"""

    CONSERVATIVE = "保守型"
    MODERATE = "稳健型"
    AGGRESSIVE = "激进型"


class InvestmentStyle(str, Enum):
    """投资风格"""

    VALUE = "价值"
    GROWTH = "成长"
    BALANCED = "平衡"


@dataclass
class InvestmentNeed:
    """投资需求解析结果"""

    # 基金类型
    fund_type: FundType | None = None
    # 收益目标
    min_return: float | None = None
    max_return: float | None = None
    # 风险约束
    max_drawdown: float | None = None
    max_volatility: float | None = None
    min_sharpe: float | None = None
    # 规模约束
    min_scale: float | None = None
    max_scale: float | None = None
    # 风险偏好
    risk_level: RiskLevel | None = None
    # 投资风格
    style: InvestmentStyle | None = None
    # 其他关键词
    keywords: list[str] = field(default_factory=list)
    # 原始需求文本
    raw_text: str = ""


@dataclass
class FundRecommendation:
    """基金推荐结果"""

    fund_code: str
    fund_name: str
    fund_type: str
    score: float
    rank: int
    recommendation_reason: str
    risk_warning: str
    key_metrics: dict[str, Any] = field(default_factory=dict)


class NeedParser:
    """
    投资需求解析器

    将用户的自然语言描述转换为结构化的筛选条件。
    """

    # 类型关键词映射
    TYPE_KEYWORDS = {
        FundType.EQUITY: ["股票型", "股票", "权益", "偏股"],
        FundType.BOND: ["债券型", "债券", "债基", "纯债"],
        FundType.MIXED: ["混合型", "混合", "偏债混合", "偏股混合"],
        FundType.INDEX: ["指数型", "指数", "ETF", "被动"],
        FundType.QDII: ["QDII", "海外", "港股", "美股"],
        FundType.MONEY: ["货币型", "货币", "现金管理"],
    }

    # 风险等级关键词映射
    RISK_KEYWORDS = {
        RiskLevel.CONSERVATIVE: ["保守", "稳健", "低风险", "保本", "安全"],
        RiskLevel.MODERATE: ["稳健", "平衡", "中等风险", "适中"],
        RiskLevel.AGGRESSIVE: ["激进", "进取", "高风险", "成长"],
    }

    # 风格关键词映射
    STYLE_KEYWORDS = {
        InvestmentStyle.VALUE: ["价值", "蓝筹", "红利", "低估值"],
        InvestmentStyle.GROWTH: ["成长", "新兴", "科技", "创新"],
        InvestmentStyle.BALANCED: ["平衡", "均衡", "混合"],
    }

    def parse(self, text: str) -> InvestmentNeed:
        """
        解析用户的自然语言需求

        Args:
            text: 用户输入的自然语言描述

        Returns:
            结构化的投资需求对象
        """
        need = InvestmentNeed(raw_text=text)

        # 解析基金类型
        need.fund_type = self._parse_fund_type(text)

        # 解析收益目标
        need.min_return, need.max_return = self._parse_return_target(text)

        # 解析风险约束
        need.max_drawdown = self._parse_max_drawdown(text)
        need.min_sharpe = self._parse_sharpe(text)

        # 解析规模约束
        need.min_scale, need.max_scale = self._parse_scale(text)

        # 解析风险偏好
        need.risk_level = self._parse_risk_level(text)

        # 解析投资风格
        need.style = self._parse_style(text)

        # 提取其他关键词
        need.keywords = self._extract_keywords(text)

        return need

    def _parse_fund_type(self, text: str) -> FundType | None:
        """解析基金类型"""
        for fund_type, keywords in self.TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return fund_type
        return None

    def _parse_return_target(self, text: str) -> tuple[float | None, float | None]:
        """解析收益目标"""
        min_return = None
        max_return = None

        # 匹配 "年化收益X%以上" 或 "收益X%以上"
        pattern = r"年化收益(\d+(?:\.\d+)?)%?以上"
        match = re.search(pattern, text)
        if match:
            min_return = float(match.group(1))

        # 匹配 "收益X%左右"
        pattern = r"收益(\d+(?:\.\d+)?)%?左右"
        match = re.search(pattern, text)
        if match:
            target = float(match.group(1))
            min_return = target - 5
            max_return = target + 5

        return min_return, max_return

    def _parse_max_drawdown(self, text: str) -> float | None:
        """解析最大回撤约束"""
        # 匹配 "最大回撤不超过X%" 或 "回撤X%以内"
        patterns = [
            r"最大回撤不超过(\d+(?:\.\d+)?)%?",
            r"回撤(\d+(?:\.\d+)?)%?以内",
            r"回撤不超过(\d+(?:\.\d+)?)%?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return -float(match.group(1))  # 回撤为负值
        return None

    def _parse_sharpe(self, text: str) -> float | None:
        """解析夏普比率要求"""
        pattern = r"夏普比率(\d+(?:\.\d+)?)以上"
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
        return None

    def _parse_scale(self, text: str) -> tuple[float | None, float | None]:
        """解析规模约束"""
        min_scale = None
        max_scale = None

        # 匹配 "规模X亿以上"
        pattern = r"规模(\d+(?:\.\d+)?)亿以上"
        match = re.search(pattern, text)
        if match:
            min_scale = float(match.group(1))

        # 匹配 "规模X亿以下"
        pattern = r"规模(\d+(?:\.\d+)?)亿以下"
        match = re.search(pattern, text)
        if match:
            max_scale = float(match.group(1))

        return min_scale, max_scale

    def _parse_risk_level(self, text: str) -> RiskLevel | None:
        """解析风险偏好"""
        for level, keywords in self.RISK_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return level
        return None

    def _parse_style(self, text: str) -> InvestmentStyle | None:
        """解析投资风格"""
        for style, keywords in self.STYLE_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return style
        return None

    def _extract_keywords(self, text: str) -> list[str]:
        """提取其他关键词"""
        # 移除已解析的关键词
        parsed_words = set()
        for keywords in self.TYPE_KEYWORDS.values():
            parsed_words.update(keywords)
        for keywords in self.RISK_KEYWORDS.values():
            parsed_words.update(keywords)
        for keywords in self.STYLE_KEYWORDS.values():
            parsed_words.update(keywords)

        # 提取剩余的关键词
        words = re.findall(r"[\u4e00-\u9fa5]{2,}", text)
        return [w for w in words if w not in parsed_words]


class FundScorer:
    """
    基金评分引擎

    基于多因子模型对基金进行综合评分。
    """

    # 因子权重（可根据风险偏好调整）
    DEFAULT_WEIGHTS = {
        "return": 0.30,  # 收益因子
        "risk": 0.25,  # 风险因子
        "sharpe": 0.20,  # 风险调整收益因子
        "scale": 0.10,  # 规模因子
        "stability": 0.15,  # 稳定性因子
    }

    def score(
        self,
        df: pd.DataFrame,
        need: InvestmentNeed,
        custom_weights: dict[str, float] | None = None,
    ) -> pd.DataFrame:
        """
        对基金进行综合评分

        Args:
            df: 基金数据 DataFrame
            need: 投资需求
            custom_weights: 自定义因子权重

        Returns:
            包含评分的 DataFrame
        """
        if df.empty:
            return df

        weights = custom_weights or self.DEFAULT_WEIGHTS.copy()

        # 根据风险偏好调整权重
        if need.risk_level == RiskLevel.CONSERVATIVE:
            weights = {"return": 0.20, "risk": 0.35, "sharpe": 0.25, "scale": 0.10, "stability": 0.10}
        elif need.risk_level == RiskLevel.AGGRESSIVE:
            weights = {"return": 0.40, "risk": 0.15, "sharpe": 0.20, "scale": 0.10, "stability": 0.15}

        # 计算各因子得分
        scores = pd.DataFrame(index=df.index)

        # 收益因子（使用近1年收益率）
        if "return_1y" in df.columns:
            scores["return_score"] = self._normalize(df["return_1y"])
        else:
            scores["return_score"] = 0.5

        # 风险因子（使用最大回撤，越小越好）
        if "max_drawdown" in df.columns:
            scores["risk_score"] = self._normalize(-df["max_drawdown"])
        else:
            scores["risk_score"] = 0.5

        # 夏普比率因子
        if "sharpe_ratio" in df.columns:
            scores["sharpe_score"] = self._normalize(df["sharpe_ratio"])
        else:
            scores["sharpe_score"] = 0.5

        # 规模因子（适中规模得分较高）
        if "scale" in df.columns:
            scores["scale_score"] = self._scale_score(df["scale"])
        else:
            scores["scale_score"] = 0.5

        # 稳定性因子（使用波动率，越小越好）
        if "volatility" in df.columns:
            scores["stability_score"] = self._normalize(-df["volatility"])
        else:
            scores["stability_score"] = 0.5

        # 计算综合得分
        df["score"] = (
            scores["return_score"] * weights["return"]
            + scores["risk_score"] * weights["risk"]
            + scores["sharpe_score"] * weights["sharpe"]
            + scores["scale_score"] * weights["scale"]
            + scores["stability_score"] * weights["stability"]
        )

        return df

    def _normalize(self, series: pd.Series) -> pd.Series:
        """归一化到 0-1"""
        if series.std() == 0:
            return pd.Series([0.5] * len(series), index=series.index)
        return (series - series.min()) / (series.max() - series.min())

    def _scale_score(self, scale: pd.Series) -> pd.Series:
        """规模评分（适中规模得分较高）"""
        # 理想规模范围：20-100亿
        optimal_min, optimal_max = 20, 100
        score = pd.Series(0.5, index=scale.index)

        # 规模在理想范围内
        in_range = (scale >= optimal_min) & (scale <= optimal_max)
        score[in_range] = 1.0

        # 规模过小
        too_small = scale < optimal_min
        score[too_small] = scale[too_small] / optimal_min * 0.8

        # 规模过大
        too_large = scale > optimal_max
        # 使用 clip 确保值在合理范围内
        large_score = 1.0 - (scale[too_large] - optimal_max) / optimal_max * 0.2
        score[too_large] = large_score.clip(lower=0.6)

        return score


class RecommendationGenerator:
    """
    推荐理由生成器

    为每只推荐基金生成个性化的推荐理由。
    """

    def generate(
        self,
        fund_info: dict[str, Any],
        need: InvestmentNeed,
        score: float,
        rank: int,
    ) -> tuple[str, str]:
        """
        生成推荐理由和风险提示

        Args:
            fund_info: 基金信息
            need: 投资需求
            score: 综合得分
            rank: 排名

        Returns:
            (推荐理由, 风险提示)
        """
        reasons = []
        warnings = []

        fund_info.get("name", "该基金")
        fund_info.get("type", "未知类型")

        # 基于排名的推荐
        if rank <= 3:
            reasons.append(f"综合评分排名第{rank}位，表现优异")
        elif rank <= 10:
            reasons.append(f"综合评分排名第{rank}位，表现良好")

        # 基于收益的推荐
        return_1y = fund_info.get("return_1y")
        if return_1y is not None:
            if return_1y > 20:
                reasons.append(f"近一年收益率{return_1y:.1f}%，收益表现突出")
            elif return_1y > 10:
                reasons.append(f"近一年收益率{return_1y:.1f}%，收益稳健")
            elif return_1y < 0:
                warnings.append("近一年收益为负，需关注市场风险")

        # 基于风险的推荐
        max_dd = fund_info.get("max_drawdown")
        if max_dd is not None:
            if max_dd > -10:
                reasons.append(f"最大回撤{abs(max_dd):.1f}%，风险控制优秀")
            elif max_dd < -30:
                warnings.append(f"最大回撤{abs(max_dd):.1f}%，波动较大")

        # 基于夏普比率的推荐
        sharpe = fund_info.get("sharpe_ratio")
        if sharpe is not None:
            if sharpe > 2:
                reasons.append(f"夏普比率{sharpe:.2f}，风险调整收益优秀")
            elif sharpe > 1:
                reasons.append(f"夏普比率{sharpe:.2f}，风险调整收益良好")

        # 基于规模的推荐
        scale = fund_info.get("scale")
        if scale is not None:
            if 20 <= scale <= 100:
                reasons.append(f"规模{scale:.1f}亿，适中规模便于管理")
            elif scale < 5:
                warnings.append("规模较小，可能面临清盘风险")

        # 基于匹配度的推荐
        if need.fund_type:
            reasons.append(f"符合您对{need.fund_type.value}的需求")

        if need.risk_level:
            reasons.append(f"适合{need.risk_level.value}投资者")

        # 默认推荐理由
        if not reasons:
            reasons.append("综合表现符合筛选条件")

        # 默认风险提示
        if not warnings:
            warnings.append("基金投资有风险，请根据自身风险承受能力谨慎投资")

        return "；".join(reasons), "；".join(warnings)


class FundSelector:
    """
    智能选基助手

    整合需求解析、基金筛选、评分排序、推荐理由生成等功能。
    """

    def __init__(self, data_manager: DataManager | None = None):
        """
        初始化智能选基助手

        Args:
            data_manager: 数据管理器实例
        """
        self._dm = data_manager or DataManager()
        self._parser = NeedParser()
        self._scorer = FundScorer()
        self._generator = RecommendationGenerator()
        self._validator = AIOutputValidator()

    def select(
        self,
        query: str,
        top_n: int = 10,
        custom_weights: dict[str, float] | None = None,
    ) -> list[FundRecommendation]:
        """
        基于自然语言查询智能选基

        Args:
            query: 用户的自然语言需求描述
            top_n: 返回的推荐数量
            custom_weights: 自定义因子权重

        Returns:
            推荐基金列表
        """
        # 1. 解析需求
        need = self._parser.parse(query)
        logger.info(f"解析需求: {need}")

        # 2. 构建筛选条件
        filter_obj = self._build_filter(need)

        # 3. 执行筛选
        df = self._dm.search_funds(
            fund_type=filter_obj.fund_type.value if filter_obj.fund_type else None,
            min_scale=filter_obj.min_scale,
            max_scale=filter_obj.max_scale,
            limit=500,  # 先获取较多候选
        )

        if df.empty:
            logger.warning("未找到符合条件的基金")
            return []

        # 4. 应用额外筛选条件
        df = self._apply_additional_filters(df, need)

        # 5. 评分排序
        df = self._scorer.score(df, need, custom_weights)
        df = df.sort_values("score", ascending=False).head(top_n)

        # 6. 生成推荐结果
        recommendations = []
        for rank, (_idx, row) in enumerate(df.iterrows(), 1):
            fund_info = row.to_dict()
            reason, warning = self._generator.generate(fund_info, need, row["score"], rank)

            rec = FundRecommendation(
                fund_code=str(row.get("code", row.get("fund_code", ""))),
                fund_name=str(row.get("name", row.get("fund_name", ""))),
                fund_type=str(row.get("type", fund_info.get("fund_type", "未知"))),
                score=float(row["score"]),
                rank=rank,
                recommendation_reason=reason,
                risk_warning=warning,
                key_metrics={
                    "return_1y": row.get("return_1y"),
                    "max_drawdown": row.get("max_drawdown"),
                    "sharpe_ratio": row.get("sharpe_ratio"),
                    "scale": row.get("scale"),
                },
            )
            recommendations.append(rec)

        return recommendations

    def _build_filter(self, need: InvestmentNeed) -> FundFilter:
        """构建筛选条件对象"""
        return FundFilter(
            fund_type=need.fund_type,
            min_scale=need.min_scale,
            max_scale=need.max_scale,
            min_return_1y=need.min_return,
            max_return_1y=need.max_return,
            max_drawdown=need.max_drawdown,
            min_sharpe=need.min_sharpe,
        )

    def _apply_additional_filters(self, df: pd.DataFrame, need: InvestmentNeed) -> pd.DataFrame:
        """应用额外的筛选条件"""
        if df.empty:
            return df

        # 收益筛选
        if need.min_return is not None and "return_1y" in df.columns:
            df = df[df["return_1y"] >= need.min_return]
        if need.max_return is not None and "return_1y" in df.columns:
            df = df[df["return_1y"] <= need.max_return]

        # 风险筛选
        if need.max_drawdown is not None and "max_drawdown" in df.columns:
            df = df[df["max_drawdown"] >= need.max_drawdown]

        # 夏普比率筛选
        if need.min_sharpe is not None and "sharpe_ratio" in df.columns:
            df = df[df["sharpe_ratio"] >= need.min_sharpe]

        return df

    def format_recommendations(self, recommendations: list[FundRecommendation]) -> str:
        """
        格式化推荐结果为可读文本

        Args:
            recommendations: 推荐基金列表

        Returns:
            格式化的推荐文本
        """
        if not recommendations:
            return "未找到符合条件的基金，请尝试调整筛选条件。"

        lines = ["# 智能选基推荐结果\n"]
        lines.append(f"共找到 {len(recommendations)} 只符合条件的基金：\n")

        for rec in recommendations:
            lines.append(f"## {rec.rank}. {rec.fund_name} ({rec.fund_code})")
            lines.append(f"- 基金类型: {rec.fund_type}")
            lines.append(f"- 综合评分: {rec.score:.2f}")
            lines.append(f"- 推荐理由: {rec.recommendation_reason}")
            lines.append(f"- 风险提示: {rec.risk_warning}")

            if rec.key_metrics:
                lines.append("- 关键指标:")
                if rec.key_metrics.get("return_1y") is not None:
                    lines.append(f"  - 近一年收益: {rec.key_metrics['return_1y']:.2f}%")
                if rec.key_metrics.get("max_drawdown") is not None:
                    lines.append(f"  - 最大回撤: {abs(rec.key_metrics['max_drawdown']):.2f}%")
                if rec.key_metrics.get("sharpe_ratio") is not None:
                    lines.append(f"  - 夏普比率: {rec.key_metrics['sharpe_ratio']:.2f}")
                if rec.key_metrics.get("scale") is not None:
                    lines.append(f"  - 基金规模: {rec.key_metrics['scale']:.1f}亿")
            lines.append("")

        return "\n".join(lines)


def select_funds(
    query: str,
    top_n: int = 10,
    data_manager: DataManager | None = None,
) -> list[FundRecommendation]:
    """
    智能选基便捷函数

    Args:
        query: 用户的自然语言需求描述
        top_n: 返回的推荐数量
        data_manager: 数据管理器实例

    Returns:
        推荐基金列表
    """
    selector = FundSelector(data_manager)
    return selector.select(query, top_n)
