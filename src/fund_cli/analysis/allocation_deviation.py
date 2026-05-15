"""
配置偏离度分析器

计算当前资产配置与目标配置之间的偏离程度。
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AllocationDeviationAnalyzer:
    """
    配置偏离度分析器

    功能：
    - 计算各类资产的配置偏离度
    - 计算总偏离度
    - 生成配置评价和建议
    """

    # 默认目标配置（基于用户画像或经典60/40配置）
    DEFAULT_TARGET: dict[str, float] = {
        "权益": 0.70,
        "固收": 0.15,
        "现金": 0.10,
        "其他": 0.05,
    }

    # 偏离度阈值
    THRESHOLD_GOOD = 0.10  # 总偏离度 < 10%: 配置合理
    THRESHOLD_WARN = 0.20  # 总偏离度 < 20%: 轻微偏离
    # 总偏离度 >= 20%: 偏离较大

    def __init__(self, data_manager=None):
        """
        初始化配置偏离度分析器

        Args:
            data_manager: 数据管理器
        """
        from fund_cli.core.data_manager import get_data_manager

        self._dm = data_manager or get_data_manager()

    def compute_deviation(
        self,
        current: dict[str, float],
        target: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """
        计算配置偏离度

        Args:
            current: 当前配置 {'权益': 0.88, '固收': 0.01, '现金': 0.12}
            target: 目标配置，默认使用 DEFAULT_TARGET

        Returns:
            {各资产偏离, 总偏离度, 评价, 建议}
        """
        if target is None:
            target = self.DEFAULT_TARGET

        # 计算各类资产偏离
        deviation: dict[str, float] = {}
        for asset_class in target:
            current_val = current.get(asset_class, 0.0)
            deviation[asset_class] = round(current_val - target[asset_class], 4)

        # 总偏离度（绝对值之和）
        total_deviation = round(sum(abs(v) for v in deviation.values()), 4)

        # 评价
        if total_deviation < self.THRESHOLD_GOOD:
            verdict = "配置合理"
            suggestion = "当前配置与目标配置偏差较小，建议维持现有配置。"
        elif total_deviation < self.THRESHOLD_WARN:
            verdict = "轻微偏离"
            suggestion = self._generate_adjustment_suggestion(deviation, target)
        else:
            verdict = "偏离较大，建议调整"
            suggestion = self._generate_adjustment_suggestion(deviation, target)

        return {
            "当前配置": current,
            "目标配置": target,
            "各资产偏离": deviation,
            "总偏离度": total_deviation,
            "评价": verdict,
            "建议": suggestion,
        }

    def parse_target_string(self, target_str: str) -> dict[str, float]:
        """
        解析目标配置字符串

        Args:
            target_str: 格式 "权益:0.7,固收:0.15,现金:0.15"

        Returns:
            {资产类: 权重}
        """
        target = {}
        for item in target_str.split(","):
            item = item.strip()
            if ":" in item:
                key, val = item.split(":", 1)
                target[key.strip()] = float(val.strip())
        return target

    def _generate_adjustment_suggestion(
        self,
        deviation: dict[str, float],
        target: dict[str, float],
    ) -> str:
        """
        生成调仓建议

        Args:
            deviation: 各资产偏离度
            target: 目标配置

        Returns:
            调仓建议文本
        """
        suggestions = []
        for asset_class, dev in deviation.items():
            if abs(dev) > 0.05:  # 偏离超过5%才提建议
                target_val = target.get(asset_class, 0)
                if dev > 0:
                    suggestions.append(f"建议降低{asset_class}配置（当前超配{dev:.2%}，目标{target_val:.2%}）")
                else:
                    suggestions.append(f"建议增加{asset_class}配置（当前低配{abs(dev):.2%}，目标{target_val:.2%}）")

        return "；".join(suggestions) if suggestions else "配置基本合理，可维持现有配置。"


def compute_allocation_deviation(
    current: dict[str, float],
    target: dict[str, float] | None = None,
) -> dict[str, Any]:
    """便捷函数：计算配置偏离度"""
    analyzer = AllocationDeviationAnalyzer()
    return analyzer.compute_deviation(current, target)
