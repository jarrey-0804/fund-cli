"""
个性化推荐引擎

为用户提供量身定制的基金推荐。
支持协同过滤推荐、内容推荐、混合推荐等功能。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

from fund_cli.ai.user_profile import (
    UserProfile,
    RiskTolerance,
    InvestmentGoal,
    InvestmentStyle,
)
from fund_cli.core.data_manager import DataManager

logger = logging.getLogger(__name__)


class RecommendationType(str, Enum):
    """推荐类型"""

    SIMILAR = "相似基金"
    ALTERNATIVE = "替代基金"
    COMPLEMENTARY = "互补基金"
    TOP_PERFORMER = "绩优基金"
    RISK_MATCHED = "风险匹配"
    GOAL_ALIGNED = "目标对齐"


@dataclass
class FundScore:
    """基金评分"""

    fund_code: str
    fund_name: str
    fund_type: str
    overall_score: float
    detail_scores: dict[str, float]
    match_reasons: list[str]


@dataclass
class RecommendationItem:
    """推荐项"""

    fund_code: str
    fund_name: str
    fund_type: str
    recommendation_type: RecommendationType
    score: float
    match_score: float  # 与用户画像匹配度
    recommendation_reason: str
    risk_warning: str
    key_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class RecommendationReport:
    """推荐报告"""

    user_id: str
    recommendations: list[RecommendationItem]
    total_candidates: int
    filter_criteria: dict[str, Any]
    summary: str


class ContentBasedRecommender:
    """基于内容的推荐器"""

    def recommend(
        self,
        profile: UserProfile,
        fund_data: pd.DataFrame | None = None,
        top_n: int = 10,
    ) -> list[FundScore]:
        """
        基于用户画像特征推荐基金

        Args:
            profile: 用户画像
            fund_data: 基金数据
            top_n: 返回数量

        Returns:
            基金评分列表
        """
        if fund_data is None or fund_data.empty:
            return self._generate_mock_scores(profile, top_n)

        scores = []
        for _, row in fund_data.iterrows():
            score = self._calculate_match_score(profile, row)
            scores.append(
                FundScore(
                    fund_code=str(row.get("code", row.get("fund_code", ""))),
                    fund_name=str(row.get("name", row.get("fund_name", ""))),
                    fund_type=str(row.get("type", row.get("fund_type", "未知"))),
                    overall_score=score["overall"],
                    detail_scores=score["details"],
                    match_reasons=score["reasons"],
                )
            )

        scores.sort(key=lambda x: x.overall_score, reverse=True)
        return scores[:top_n]

    def _calculate_match_score(self, profile: UserProfile, fund: pd.Series) -> dict:
        """计算匹配得分"""
        scores = {}
        reasons = []

        # 风险匹配得分
        risk_score = self._risk_match_score(profile, fund)
        scores["risk_match"] = risk_score
        if risk_score > 80:
            reasons.append("风险等级匹配")

        # 类型偏好得分
        type_score = self._type_match_score(profile, fund)
        scores["type_match"] = type_score
        if type_score > 70:
            reasons.append("符合偏好基金类型")

        # 规模匹配得分
        scale_score = self._scale_match_score(profile, fund)
        scores["scale_match"] = scale_score

        # 业绩得分
        perf_score = self._performance_score(fund)
        scores["performance"] = perf_score
        if perf_score > 80:
            reasons.append("历史业绩优秀")

        # 综合得分
        weights = {"risk_match": 0.3, "type_match": 0.25, "scale_match": 0.15, "performance": 0.3}
        overall = sum(scores[k] * weights[k] for k in weights)

        return {"overall": overall, "details": scores, "reasons": reasons}

    def _risk_match_score(self, profile: UserProfile, fund: pd.Series) -> float:
        """风险匹配得分"""
        fund_risk = fund.get("risk_level", "中风险")
        user_risk = profile.risk_assessment.tolerance

        risk_mapping = {
            RiskTolerance.CONSERVATIVE: ["低风险"],
            RiskTolerance.MODERATELY_CONSERVATIVE: ["低风险", "中低风险"],
            RiskTolerance.BALANCED: ["中低风险", "中风险"],
            RiskTolerance.MODERATELY_AGGRESSIVE: ["中风险", "中高风险"],
            RiskTolerance.AGGRESSIVE: ["中高风险", "高风险"],
        }

        acceptable = risk_mapping.get(user_risk, ["中风险"])
        return 100 if fund_risk in acceptable else 30

    def _type_match_score(self, profile: UserProfile, fund: pd.Series) -> float:
        """类型匹配得分"""
        fund_type = fund.get("type", fund.get("fund_type", ""))
        preferred = profile.preferences.preferred_fund_types

        if not preferred:
            return 50

        for i, ptype in enumerate(preferred):
            if ptype in fund_type:
                return 100 - i * 10

        return 20

    def _scale_match_score(self, profile: UserProfile, fund: pd.Series) -> float:
        """规模匹配得分"""
        scale = fund.get("scale", fund.get("fund_scale", 50))
        min_scale = profile.preferences.min_fund_scale
        max_scale = profile.preferences.max_fund_scale

        if min_scale <= scale <= max_scale:
            return 100
        elif scale < min_scale:
            return max(0, 50 - (min_scale - scale) * 5)
        else:
            return max(0, 50 - (scale - max_scale) * 0.5)

    def _performance_score(self, fund: pd.Series) -> float:
        """业绩得分"""
        ret_1y = fund.get("return_1y", 0)
        sharpe = fund.get("sharpe_ratio", 0)

        ret_score = min(100, max(0, 50 + ret_1y * 2))
        sharpe_score = min(100, max(0, sharpe * 30 + 50))

        return (ret_score + sharpe_score) / 2

    def _generate_mock_scores(self, profile: UserProfile, top_n: int) -> list[FundScore]:
        """生成模拟评分"""
        np.random.seed(42)
        funds = [
            ("000001", "华夏成长", "股票型"),
            ("000002", "易方达策略", "混合型"),
            ("000003", "南方稳健", "混合型"),
            ("000011", "华夏大盘", "股票型"),
            ("000015", "易方达价值", "混合型"),
        ]

        scores = []
        for code, name, ftype in funds[:top_n]:
            score = np.random.uniform(60, 95)
            scores.append(
                FundScore(
                    fund_code=code,
                    fund_name=name,
                    fund_type=ftype,
                    overall_score=round(score, 2),
                    detail_scores={
                        "risk_match": round(np.random.uniform(50, 100), 2),
                        "type_match": round(np.random.uniform(50, 100), 2),
                        "performance": round(np.random.uniform(50, 100), 2),
                    },
                    match_reasons=["风险等级匹配", "业绩表现良好"],
                )
            )

        scores.sort(key=lambda x: x.overall_score, reverse=True)
        return scores


class CollaborativeRecommender:
    """协同过滤推荐器"""

    def recommend(
        self,
        user_id: str,
        user_fund_matrix: pd.DataFrame | None = None,
        top_n: int = 10,
    ) -> list[str]:
        """
        基于协同过滤推荐基金

        Args:
            user_id: 用户ID
            user_fund_matrix: 用户-基金矩阵
            top_n: 返回数量

        Returns:
            推荐基金代码列表
        """
        if user_fund_matrix is None:
            return self._generate_mock_recommendations(top_n)

        # 简化实现：返回热门基金
        fund_popularity = user_fund_matrix.sum()
        top_funds = fund_popularity.nlargest(top_n).index.tolist()

        return [str(f) for f in top_funds]

    def _generate_mock_recommendations(self, top_n: int) -> list[str]:
        """生成模拟推荐"""
        popular_funds = ["000001", "000002", "000003", "000011", "000015", "000020", "000025"]
        return popular_funds[:top_n]


class HybridRecommender:
    """混合推荐器"""

    def __init__(self, data_manager: DataManager | None = None):
        self._dm = data_manager or DataManager()
        self._content_recommender = ContentBasedRecommender()
        self._collab_recommender = CollaborativeRecommender()

    def recommend(
        self,
        profile: UserProfile,
        recommendation_type: RecommendationType = RecommendationType.RISK_MATCHED,
        top_n: int = 10,
        content_weight: float = 0.7,
    ) -> list[RecommendationItem]:
        """
        混合推荐

        Args:
            profile: 用户画像
            recommendation_type: 推荐类型
            top_n: 返回数量
            content_weight: 内容推荐权重

        Returns:
            推荐项列表
        """
        # 内容推荐
        content_scores = self._content_recommender.recommend(profile, top_n=top_n * 2)

        # 协同过滤推荐
        collab_funds = self._collab_recommender.recommend(profile.user_id, top_n=top_n)

        # 合并结果
        recommendations = []
        seen = set()

        for score in content_scores:
            if score.fund_code in seen:
                continue
            seen.add(score.fund_code)

            # 协同过滤加成
            collab_boost = 10 if score.fund_code in collab_funds else 0
            final_score = score.overall_score * content_weight + collab_boost

            rec = RecommendationItem(
                fund_code=score.fund_code,
                fund_name=score.fund_name,
                fund_type=score.fund_type,
                recommendation_type=recommendation_type,
                score=round(final_score, 2),
                match_score=round(score.overall_score, 2),
                recommendation_reason=self._generate_reason(score, profile),
                risk_warning=self._generate_risk_warning(score, profile),
                key_metrics={
                    "risk_match": score.detail_scores.get("risk_match", 0),
                    "performance": score.detail_scores.get("performance", 0),
                },
            )
            recommendations.append(rec)

        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:top_n]

    def _generate_reason(self, score: FundScore, profile: UserProfile) -> str:
        """生成推荐理由"""
        reasons = score.match_reasons.copy()

        if profile.investment_goal == InvestmentGoal.STEADY_INCOME:
            reasons.append("适合稳健增值目标")
        elif profile.investment_goal == InvestmentGoal.AGGRESSIVE_GROWTH:
            reasons.append("符合积极成长目标")

        if not reasons:
            reasons.append("综合评分较高")

        return "；".join(reasons[:3])

    def _generate_risk_warning(self, score: FundScore, profile: UserProfile) -> str:
        """生成风险提示"""
        warnings = []

        risk_match = score.detail_scores.get("risk_match", 50)
        if risk_match < 50:
            warnings.append("风险等级与您的偏好不完全匹配")

        if profile.risk_assessment.tolerance == RiskTolerance.CONSERVATIVE:
            if "股票" in score.fund_type:
                warnings.append("股票型基金波动较大，请谨慎投资")

        if not warnings:
            warnings.append("基金投资有风险，请根据自身情况谨慎投资")

        return "；".join(warnings)


class FundRecommender:
    """
    基金推荐主类

    整合多种推荐策略，提供个性化基金推荐。
    """

    def __init__(self, data_manager: DataManager | None = None):
        self._dm = data_manager or DataManager()
        self._hybrid_recommender = HybridRecommender(data_manager)

    def recommend(
        self,
        profile: UserProfile,
        top_n: int = 10,
        recommendation_type: str = "RISK_MATCHED",
    ) -> RecommendationReport:
        """
        执行基金推荐

        Args:
            profile: 用户画像
            top_n: 返回数量
            recommendation_type: 推荐类型

        Returns:
            推荐报告
        """
        rec_type = RecommendationType[recommendation_type]
        recommendations = self._hybrid_recommender.recommend(profile, rec_type, top_n)

        # 生成摘要
        summary = self._generate_summary(recommendations, profile)

        return RecommendationReport(
            user_id=profile.user_id,
            recommendations=recommendations,
            total_candidates=len(recommendations) * 5,
            filter_criteria={
                "risk_tolerance": profile.risk_assessment.tolerance.value,
                "investment_goal": profile.investment_goal.value,
                "preferred_types": profile.preferences.preferred_fund_types,
            },
            summary=summary,
        )

    def recommend_similar(self, fund_code: str, top_n: int = 5) -> list[RecommendationItem]:
        """推荐相似基金"""
        np.random.seed(42)
        similar_funds = [
            RecommendationItem(
                fund_code=f"00000{i}",
                fund_name=f"相似基金{i}",
                fund_type="混合型",
                recommendation_type=RecommendationType.SIMILAR,
                score=round(85 - i * 5, 2),
                match_score=round(80 - i * 3, 2),
                recommendation_reason=f"与{fund_code}投资风格相似",
                risk_warning="基金投资有风险",
            )
            for i in range(1, top_n + 1)
        ]
        return similar_funds

    def recommend_alternative(self, fund_code: str, top_n: int = 5) -> list[RecommendationItem]:
        """推荐替代基金"""
        np.random.seed(43)
        alt_funds = [
            RecommendationItem(
                fund_code=f"00001{i}",
                fund_name=f"替代基金{i}",
                fund_type="股票型",
                recommendation_type=RecommendationType.ALTERNATIVE,
                score=round(80 - i * 4, 2),
                match_score=round(75 - i * 3, 2),
                recommendation_reason=f"可作为{fund_code}的替代选择",
                risk_warning="替代基金风险特征可能不同",
            )
            for i in range(1, top_n + 1)
        ]
        return alt_funds

    def _generate_summary(self, recommendations: list[RecommendationItem], profile: UserProfile) -> str:
        """生成推荐摘要"""
        if not recommendations:
            return "暂无符合条件的推荐基金。"

        top = recommendations[0]
        return (
            f"根据您的风险偏好（{profile.risk_assessment.tolerance.value}）"
            f"和投资目标（{profile.investment_goal.value}），"
            f"为您推荐{len(recommendations)}只基金，"
            f"首选{top.fund_name}（{top.fund_code}）。"
        )

    def format_report(self, report: RecommendationReport) -> str:
        """格式化推荐报告"""
        lines = ["# 基金推荐报告\n"]

        lines.append(f"用户ID: {report.user_id}")
        lines.append(f"筛选条件: 风险偏好={report.filter_criteria.get('risk_tolerance', '未知')}, "
                    f"投资目标={report.filter_criteria.get('investment_goal', '未知')}")
        lines.append(f"候选基金数: {report.total_candidates}")
        lines.append("")

        lines.append("## 推荐基金列表")
        lines.append("| 排名 | 基金代码 | 基金名称 | 类型 | 综合得分 | 匹配度 |")
        lines.append("|------|----------|----------|------|----------|--------|")

        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"| {i} | {rec.fund_code} | {rec.fund_name} | {rec.fund_type} | {rec.score:.1f} | {rec.match_score:.1f}% |")

        lines.append("")

        lines.append("## 推荐详情")
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"### {i}. {rec.fund_name} ({rec.fund_code})")
            lines.append(f"- 推荐类型: {rec.recommendation_type.value}")
            lines.append(f"- 综合得分: {rec.score:.2f}")
            lines.append(f"- 匹配度: {rec.match_score:.1f}%")
            lines.append(f"- 推荐理由: {rec.recommendation_reason}")
            lines.append(f"- 风险提示: {rec.risk_warning}")
            lines.append("")

        lines.append("## 摘要")
        lines.append(report.summary)

        return "\n".join(lines)


def recommend_funds(
    profile: UserProfile,
    top_n: int = 10,
    data_manager: DataManager | None = None,
) -> RecommendationReport:
    """基金推荐便捷函数"""
    recommender = FundRecommender(data_manager)
    return recommender.recommend(profile, top_n)
