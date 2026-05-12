"""
单只基金双轨评价器

根据基金类型自动选择评价路径：
- 主动型基金：产品评分 + 经理评分 + 百分位排名
- 指数型基金：超额收益 + PE分位 + 估值判断
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from fund_cli.core.analyzer import Analyzer

logger = logging.getLogger(__name__)


class FundEvaluator:
    """
    单只基金双轨评价器

    评价路径：
    - 主动型 → FundScoringEngine + ManagerAnalyzer
    - 指数型 → IndexFundValuator

    输出：
    - 三档建议：继续持有 / 观察 / 替换
    """

    # 指数型基金关键词
    INDEX_KEYWORDS = ["指数", "ETF", "跟踪", "联接", "LOF"]

    def __init__(self, data_manager=None):
        from fund_cli.core.data_manager import get_data_manager

        self._dm = data_manager or get_data_manager()

    def evaluate(
        self,
        fund_code: str,
        fund_info: dict[str, Any] | None = None,
        nav_series: pd.Series | None = None,
        peer_returns_list: list[pd.Series] | None = None,
        benchmark_nav: pd.Series | None = None,
    ) -> dict[str, Any]:
        """
        统一评价入口

        Args:
            fund_code: 基金代码
            fund_info: 基金信息（可选，自动获取）
            nav_series: 净值序列（可选，自动获取）
            peer_returns_list: 同类基金收益率（可选）
            benchmark_nav: 基准净值（可选）

        Returns:
            {基金代码, 基金名称, 基金类型, 评价路径, 评分, 建议}
        """
        # 获取基础信息
        if fund_info is None:
            fund_info = self._dm.get_fund_info(fund_code) or {}

        fund_name = fund_info.get("name", fund_code)
        fund_type = fund_info.get("type", "")

        is_index = self._is_index_fund(fund_type, fund_name)

        if is_index:
            return self._evaluate_index_fund(fund_code, fund_name, fund_type, nav_series, benchmark_nav)
        else:
            return self._evaluate_active_fund(fund_code, fund_name, fund_type, nav_series, peer_returns_list)

    def three_tier_advice(self, composite_score: float) -> str:
        """
        三档操作建议

        Args:
            composite_score: 综合得分 (0-1)

        Returns:
            继续持有 / 观察 / 替换
        """
        if composite_score >= 0.60:
            return "继续持有"
        elif composite_score >= 0.35:
            return "观察"
        else:
            return "替换"

    def _is_index_fund(self, fund_type: str, fund_name: str) -> bool:
        """判断是否为指数型基金"""
        combined = fund_type + fund_name
        return any(kw in combined for kw in self.INDEX_KEYWORDS)

    def _evaluate_active_fund(
        self,
        fund_code: str,
        fund_name: str,
        fund_type: str,
        nav_series: pd.Series | None,
        peer_returns_list: list[pd.Series] | None,
    ) -> dict[str, Any]:
        """主动型基金评价"""
        from fund_cli.analysis.fund_scoring import FundScoringEngine

        score = {"综合得分": 0.5}  # 默认中等

        if nav_series is not None and not nav_series.empty:
            returns = nav_series.pct_change().dropna()
            engine = FundScoringEngine()
            try:
                score = engine.compute_fund_score(returns, peer_returns_list or [])
            except Exception as e:
                logger.warning(f"基金 {fund_code} 评分失败: {e}")

        composite = score.get("综合得分", 0.5)
        grade = FundScoringEngine().score_to_grade(composite)
        advice = self.three_tier_advice(composite)

        return {
            "基金代码": fund_code,
            "基金名称": fund_name,
            "基金类型": fund_type,
            "评价路径": "主动型",
            "收益得分": score.get("收益得分", 0),
            "风险得分": score.get("风险得分", 0),
            "综合得分": composite,
            "等级": grade,
            "建议": advice,
        }

    def _evaluate_index_fund(
        self,
        fund_code: str,
        fund_name: str,
        fund_type: str,
        nav_series: pd.Series | None,
        benchmark_nav: pd.Series | None,
    ) -> dict[str, Any]:
        """指数型基金评价"""
        from fund_cli.analysis.index_valuation import IndexFundValuator

        valuation = {
            "超额收益": 0.0,
            "估值判断": "数据不足",
            "综合建议": "数据不足，建议进一步分析",
        }

        if nav_series is not None and not nav_series.empty:
            valuator = IndexFundValuator(self._dm)
            try:
                valuation = valuator.evaluate(fund_code, nav_series, benchmark_nav)
            except Exception as e:
                logger.warning(f"基金 {fund_code} 估值分析失败: {e}")

        # 将估值判断映射为得分
        pe_verdict = valuation.get("估值判断", "数据不足")
        score_map = {"估值较低": 0.8, "不算贵": 0.6, "偏贵": 0.3, "数据不足": 0.5}
        composite = score_map.get(pe_verdict, 0.5)
        advice = self.three_tier_advice(composite)

        return {
            "基金代码": fund_code,
            "基金名称": fund_name,
            "基金类型": fund_type,
            "评价路径": "指数型",
            "超额收益": valuation.get("超额收益", 0),
            "当前PE": valuation.get("当前PE"),
            "PE分位": valuation.get("近五年PE分位"),
            "估值判断": pe_verdict,
            "综合得分": composite,
            "等级": pe_verdict if pe_verdict in ("估值较低", "不算贵") else ("偏贵" if pe_verdict == "偏贵" else "一般"),
            "建议": advice,
        }
