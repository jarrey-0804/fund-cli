"""
调仓建议生成器

基于组合诊断结果生成调仓方案。
"""

from __future__ import annotations

import logging
from typing import Any

from fund_cli.core.analyzer import Analyzer

logger = logging.getLogger(__name__)


class RebalanceAdvisor:
    """
    调仓建议生成器

    功能：
    - 计算当前资产配置
    - 确定目标配置
    - 生成减仓/加仓建议
    - 调仓后验证
    """

    def __init__(self, data_manager=None):
        from fund_cli.core.data_manager import get_data_manager

        self._dm = data_manager or get_data_manager()

    def generate_rebalance_plan(
        self,
        current_codes: list[str],
        current_weights: list[float],
        current_values: dict[str, float] | None = None,
        target_allocation: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """
        生成完整调仓方案

        Args:
            current_codes: 当前持仓基金代码
            current_weights: 当前持仓权重
            current_values: 当前持仓市值（可选）
            target_allocation: 目标资产配置（可选）

        Returns:
            {当前配置, 目标配置, 减仓建议, 加仓建议, 预期改善}
        """
        if len(current_codes) != len(current_weights):
            raise ValueError("基金数量与权重数量不匹配")

        # 1. 计算当前资产配置
        current_asset = self._compute_asset_allocation(current_codes, current_weights)

        # 2. 确定目标配置
        if target_allocation is None:
            target_allocation = {"权益": 0.70, "固收": 0.15, "现金": 0.15}

        # 3. 计算偏离
        deviation = {}
        for asset_class in target_allocation:
            deviation[asset_class] = current_asset.get(asset_class, 0) - target_allocation[asset_class]

        # 4. 生成减仓建议（超配的资产类别中，评分低的优先减仓）
        reduction = self._generate_reduction_suggestions(current_codes, current_weights, deviation)

        # 5. 生成加仓建议（低配的资产类别）
        addition = self._generate_addition_suggestions(deviation, target_allocation)

        # 6. 预期改善
        improvement = self._estimate_improvement(deviation)

        return {
            "当前配置": current_asset,
            "目标配置": target_allocation,
            "配置偏离": deviation,
            "减仓建议": reduction,
            "加仓建议": addition,
            "预期改善": improvement,
        }

    def _compute_asset_allocation(
        self,
        fund_codes: list[str],
        weights: list[float],
    ) -> dict[str, float]:
        """计算当前资产配置"""
        allocation: dict[str, float] = {"权益": 0, "固收": 0, "现金": 0, "其他": 0}

        for code, weight in zip(fund_codes, weights):
            try:
                info = self._dm.get_fund_info(code)
                fund_type = info.get("type", "") if info else ""

                if "债券" in fund_type or "货币" in fund_type:
                    allocation["固收"] += weight
                elif "股票" in fund_type or "混合" in fund_type or "指数" in fund_type:
                    allocation["权益"] += weight
                elif "QDII" in fund_type:
                    allocation["权益"] += weight
                else:
                    allocation["其他"] += weight
            except Exception:
                allocation["其他"] += weight

        return {k: round(v, 4) for k, v in allocation.items()}

    def _generate_reduction_suggestions(
        self,
        fund_codes: list[str],
        weights: list[float],
        deviation: dict[str, float],
    ) -> list[dict[str, Any]]:
        """生成减仓建议"""
        suggestions = []
        for asset_class, dev in deviation.items():
            if dev > 0.05:  # 超配超过5%
                # 找到该资产类别中权重最大的基金
                candidates = []
                for code, weight in zip(fund_codes, weights):
                    try:
                        info = self._dm.get_fund_info(code)
                        ftype = info.get("type", "") if info else ""
                        if self._belongs_to_asset(ftype, asset_class):
                            candidates.append({"基金代码": code, "基金名称": info.get("name", code), "当前权重": weight})
                    except Exception:
                        pass

                candidates.sort(key=lambda x: x["当前权重"], reverse=True)
                if candidates:
                    top = candidates[0]
                    suggestions.append({
                        "资产类别": asset_class,
                        "超配幅度": f"{dev:.2%}",
                        "建议减仓基金": top["基金名称"],
                        "当前权重": top["当前权重"],
                        "建议操作": f"适当降低{top['基金名称']}的持仓比例",
                    })

        return suggestions

    def _generate_addition_suggestions(
        self,
        deviation: dict[str, float],
        target_allocation: dict[str, float],
    ) -> list[dict[str, Any]]:
        """生成加仓建议"""
        suggestions = []
        for asset_class, dev in deviation.items():
            if dev < -0.05:  # 低配超过5%
                target_weight = target_allocation.get(asset_class, 0)
                suggestions.append({
                    "资产类别": asset_class,
                    "低配幅度": f"{abs(dev):.2%}",
                    "目标权重": f"{target_weight:.2%}",
                    "建议操作": f"适当增加{asset_class}类资产的配置",
                })

        return suggestions

    def _estimate_improvement(self, deviation: dict[str, float]) -> str:
        """估算调仓后预期改善"""
        total_dev = sum(abs(v) for v in deviation.values())
        if total_dev < 0.10:
            return "当前配置接近目标，调仓空间有限"
        elif total_dev < 0.30:
            return "适度调仓可优化组合风险收益比"
        else:
            return "建议进行较大幅度调仓以改善组合配置"

    def _belongs_to_asset(self, fund_type: str, asset_class: str) -> bool:
        """判断基金是否属于某资产类别"""
        mapping = {
            "权益": ["股票", "混合", "指数", "QDII"],
            "固收": ["债券", "货币"],
            "现金": ["货币"],
        }
        keywords = mapping.get(asset_class, [])
        return any(kw in fund_type for kw in keywords)
