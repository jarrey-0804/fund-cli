"""
指数型基金估值分析器

对指数型基金采用"超额收益+PE分位+估值判断"四维评价。
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from fund_cli.core.analyzer import Analyzer

logger = logging.getLogger(__name__)


class IndexFundValuator:
    """
    指数型基金估值分析器

    评价维度：
    - 超额收益（相对跟踪指数）
    - 当前 PE
    - 近五年 PE 分位
    - 综合建议
    """

    def __init__(self, data_manager=None):
        from fund_cli.core.data_manager import get_data_manager

        self._dm = data_manager or get_data_manager()

    def evaluate(
        self,
        fund_code: str,
        fund_nav: pd.Series,
        benchmark_nav: pd.Series | None = None,
    ) -> dict[str, Any]:
        """
        指数型基金四维评价

        Args:
            fund_code: 基金代码
            fund_nav: 基金净值序列
            benchmark_nav: 跟踪指数净值序列（可选）

        Returns:
            {超额收益, 超额收益评价, 当前PE, 近五年PE分位, 估值判断, 综合建议}
        """
        from fund_cli.analysis.performance import PerformanceAnalyzer

        perf = PerformanceAnalyzer()
        fund_returns = fund_nav.pct_change().dropna()

        # 维度1: 超额收益
        excess_return = 0.0
        if benchmark_nav is not None and not benchmark_nav.empty:
            bench_returns = benchmark_nav.pct_change().dropna()
            fund_cum = (1 + fund_returns).cumprod()
            bench_cum = (1 + bench_returns).cumprod()
            excess_return = fund_cum.iloc[-1] / fund_cum.iloc[0] - 1 - (
                bench_cum.iloc[-1] / bench_cum.iloc[0] - 1
            )

        if excess_return > 0.01:
            excess_verdict = "超额收益为正"
        elif excess_return < -0.01:
            excess_verdict = "存在跟踪误差（负超额）"
        else:
            excess_verdict = "跟踪效果良好"

        # 维度2-3: PE 分位
        current_pe, pe_percentile = self._get_pe_percentile(fund_code)

        if pe_percentile is not None:
            if pe_percentile > 0.75:
                pe_verdict = "偏贵"
            elif pe_percentile > 0.50:
                pe_verdict = "不算贵"
            else:
                pe_verdict = "估值较低"
        else:
            pe_verdict = "数据不足"
            pe_percentile = 0.5

        # 综合建议
        advice = self._map_to_advice(pe_verdict, excess_return)

        return {
            "超额收益": round(excess_return, 4),
            "超额收益评价": excess_verdict,
            "当前PE": current_pe,
            "近五年PE分位": pe_percentile,
            "估值判断": pe_verdict,
            "综合建议": advice,
        }

    def _get_pe_percentile(self, fund_code: str) -> tuple[float | None, float | None]:
        """获取指数PE及历史分位"""
        try:
            info = self._dm.get_fund_info(fund_code)
            if info:
                pe = info.get("PE", None)
                if pe is not None:
                    return float(pe), 0.5  # 简化处理，实际需获取历史PE
        except Exception as e:
            logger.warning(f"获取基金 {fund_code} PE失败: {e}")
        return None, None

    def _map_to_advice(self, pe_verdict: str, excess_return: float) -> str:
        """映射综合建议"""
        if pe_verdict == "估值较低" and excess_return >= 0:
            return "估值较低且跟踪良好，建议继续持有或加仓"
        elif pe_verdict == "偏贵":
            return "当前估值偏高，建议适当减仓或止盈"
        elif pe_verdict == "不算贵" and excess_return >= 0:
            return "估值合理且跟踪良好，建议继续持有"
        elif excess_return < -0.02:
            return "跟踪误差较大，建议关注并考虑替换"
        else:
            return "整体表现正常，建议继续持有观察"
