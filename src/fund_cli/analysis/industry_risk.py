"""
行业集中度风险分析器

检测行业配置集中度风险并生成预警提示。
"""

from __future__ import annotations

import logging
from typing import Any

from fund_cli.core.analyzer import Analyzer

logger = logging.getLogger(__name__)


class IndustryRiskAnalyzer:
    """
    行业集中度风险分析器

    功能：
    - 计算行业 HHI 指数
    - 识别高集中度行业
    - 生成风险提示
    - 行业景气度判断
    """

    # 默认阈值
    DEFAULT_THRESHOLD_HIGH = 0.40
    DEFAULT_THRESHOLD_MEDIUM = 0.30

    # 行业景气度关键词（正面）
    BOOM_KEYWORDS = ["新能源", "半导体", "人工智能", "AI", "医药", "消费"]

    def analyze_concentration_risk(
        self,
        industry_exposure: dict[str, float],
        threshold_high: float | None = None,
        threshold_medium: float | None = None,
    ) -> dict[str, Any]:
        """
        行业集中度风险提示

        Args:
            industry_exposure: {行业名称: 占比}
            threshold_high: 高风险阈值，默认 0.40
            threshold_medium: 中风险阈值，默认 0.30

        Returns:
            {高集中度行业, 风险提示列表, HHI指数, 集中度评价}
        """
        if threshold_high is None:
            threshold_high = self.DEFAULT_THRESHOLD_HIGH
        if threshold_medium is None:
            threshold_medium = self.DEFAULT_THRESHOLD_MEDIUM

        # 计算 HHI
        hhi = sum(v ** 2 for v in industry_exposure.values())

        # 识别高集中度行业
        high_concentration = {
            k: v for k, v in industry_exposure.items() if v > threshold_medium
        }

        # 生成风险提示
        alerts = []
        for industry, ratio in sorted(high_concentration.items(), key=lambda x: x[1], reverse=True):
            risk_level = "高" if ratio > threshold_high else "中"
            alerts.append({
                "行业": industry,
                "占比": f"{ratio:.2%}",
                "风险等级": risk_level,
                "提示": self._generate_risk_message(industry, ratio, risk_level),
            })

        # 集中度评价
        if hhi < 0.10:
            concentration_verdict = "分散度良好"
        elif hhi < 0.15:
            concentration_verdict = "适度集中"
        elif hhi < 0.25:
            concentration_verdict = "集中度偏高"
        else:
            concentration_verdict = "高度集中"

        return {
            "高集中度行业": high_concentration,
            "风险提示": alerts,
            "HHI指数": round(hhi, 4),
            "集中度评价": concentration_verdict,
        }

    def analyze_boom_bust(
        self,
        industry_exposure: dict[str, float],
    ) -> dict[str, Any]:
        """
        行业景气度分析

        Args:
            industry_exposure: {行业名称: 占比}

        Returns:
            {景气行业, 风险行业, 景气度评价}
        """
        boom_industries = []
        for industry, ratio in industry_exposure.items():
            if any(kw in industry for kw in self.BOOM_KEYWORDS):
                boom_industries.append({"行业": industry, "占比": f"{ratio:.2%}"})

        return {
            "景气行业": boom_industries,
            "风险行业": [],  # 可扩展
            "景气度评价": self._generate_boom_evaluation(boom_industries),
        }

    def _generate_risk_message(
        self,
        industry: str,
        ratio: float,
        risk_level: str,
    ) -> str:
        """生成风险提示消息"""
        if risk_level == "高":
            return f"在{industry}行业的集中度偏高（{ratio:.2%}），可能导致组合波动增大，建议适当分散"
        else:
            return f"在{industry}行业有一定集中度（{ratio:.2%}），需关注行业轮动风险"

    def _generate_boom_evaluation(
        self,
        boom_industries: list[dict[str, str]],
    ) -> str:
        """生成景气度评价"""
        if not boom_industries:
            return "持仓行业分布均衡，无明显景气集中"

        names = "、".join(item["行业"] for item in boom_industries[:3])
        return f"持仓偏向{names}等景气行业，需关注估值水平和轮动风险"
