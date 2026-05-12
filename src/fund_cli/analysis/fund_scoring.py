"""
基金综合评分引擎

基于百分位排名计算基金的收益得分、风险得分和综合得分。
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from fund_cli.core.analyzer import Analyzer

logger = logging.getLogger(__name__)


class FundScoringEngine:
    """
    基金综合评分引擎

    评分维度：
    - 收益得分：年化收益在同类基金中的百分位排名
    - 风险得分：最大回撤在同类基金中的百分位排名（越小越好）
    - 综合得分：收益得分 × 0.5 + 风险得分 × 0.5
    """

    def __init__(self, return_weight: float = 0.5, risk_weight: float = 0.5):
        """
        初始化评分引擎

        Args:
            return_weight: 收益维度权重
            risk_weight: 风险维度权重
        """
        if not np.isclose(return_weight + risk_weight, 1.0):
            raise ValueError("收益权重和风险权重之和必须为1")
        self.return_weight = return_weight
        self.risk_weight = risk_weight

    def compute_fund_score(
        self,
        fund_returns: pd.Series,
        peer_returns_list: list[pd.Series],
    ) -> dict[str, float]:
        """
        计算单只基金的收益风险综合得分

        Args:
            fund_returns: 目标基金日收益率序列
            peer_returns_list: 同类基金日收益率列表

        Returns:
            {收益得分, 风险得分, 综合得分}
        """
        from fund_cli.analysis.performance import PerformanceAnalyzer
        from fund_cli.analysis.risk import RiskAnalyzer

        perf = PerformanceAnalyzer()
        risk = RiskAnalyzer()

        # 收益维度：年化收益百分位
        fund_metrics = perf.calculate_metrics(fund_returns)
        fund_ann_ret = fund_metrics.get("年化收益", fund_metrics.get("cagr", 0.0))

        peer_ann_rets = []
        for r in peer_returns_list:
            try:
                m = perf.calculate_metrics(r)
                peer_ann_rets.append(m.get("年化收益", m.get("cagr", 0.0)))
            except Exception:
                continue

        ret_percentile = self._compute_percentile(fund_ann_ret, peer_ann_rets, higher_is_better=True)

        # 风险维度：最大回撤百分位（越小越好）
        fund_mdd = abs(risk.max_drawdown(fund_returns))
        peer_mdds = []
        for r in peer_returns_list:
            try:
                mdd = abs(risk.max_drawdown(r))
                peer_mdds.append(mdd)
            except Exception:
                continue

        mdd_percentile = self._compute_percentile(fund_mdd, peer_mdds, higher_is_better=False)

        composite = ret_percentile * self.return_weight + mdd_percentile * self.risk_weight

        return {
            "收益得分": round(ret_percentile, 4),
            "风险得分": round(mdd_percentile, 4),
            "综合得分": round(composite, 4),
        }

    def compute_portfolio_score(
        self,
        fund_returns_list: list[pd.Series],
        weights: list[float],
        peer_returns_list: list[pd.Series] | None = None,
    ) -> dict[str, Any]:
        """
        计算组合加权综合得分

        Args:
            fund_returns_list: 各基金日收益率列表
            weights: 各基金在组合中的权重
            peer_returns_list: 同类基金日收益率列表（可选）

        Returns:
            {各基金得分, 组合加权得分}
        """
        if len(fund_returns_list) != len(weights):
            raise ValueError("基金数量与权重数量不匹配")

        individual_scores = []
        for returns in fund_returns_list:
            score = self.compute_fund_score(returns, peer_returns_list or [])
            individual_scores.append(score)

        # 加权汇总
        weighted_score = sum(
            s["综合得分"] * w for s, w in zip(individual_scores, weights)
        )

        return {
            "各基金得分": individual_scores,
            "组合加权得分": round(weighted_score, 4),
        }

    def score_to_grade(self, score: float) -> str:
        """
        将百分位得分转换为等级

        Args:
            score: 0-1 之间的得分

        Returns:
            等级: 优秀/良好/一般/较差
        """
        if score >= 0.8:
            return "优秀"
        elif score >= 0.6:
            return "良好"
        elif score >= 0.4:
            return "一般"
        else:
            return "较差"

    def _compute_percentile(
        self,
        value: float,
        peer_values: list[float],
        higher_is_better: bool = True,
    ) -> float:
        """
        计算百分位排名

        Args:
            value: 目标值
            peer_values: 同类值列表
            higher_is_better: 是否越大越好

        Returns:
            百分位 (0-1)
        """
        if not peer_values:
            return 0.5  # 无同类数据时返回中位数

        if higher_is_better:
            rank = sum(1 for v in peer_values if v < value)
        else:
            rank = sum(1 for v in peer_values if v > value)

        return rank / len(peer_values)


def compute_fund_score(
    fund_returns: pd.Series,
    peer_returns_list: list[pd.Series],
) -> dict[str, float]:
    """便捷函数：计算基金综合得分"""
    engine = FundScoringEngine()
    return engine.compute_fund_score(fund_returns, peer_returns_list)
