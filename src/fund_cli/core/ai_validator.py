"""
AI分析输出验证器.

验证AI生成的分析内容是否与输入数据一致，防止幻觉和误导。
"""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AIValidationResult:
    """AI输出验证结果."""

    passed: bool
    issues: list[str] = field(default_factory=list)
    confidence_score: float = 1.0  # 0-1


class AIOutputValidator:
    """
    AI分析输出验证器.

    检查AI生成的文本是否与原始数据一致。
    """

    def __init__(self):
        self._metrics_patterns = {
            "total_return": r"总收益率?\s*[:：]\s*([+-]?\d+\.?\d*)%?",
            "sharpe_ratio": r"夏普比率?\s*[:：]\s*([+-]?\d+\.?\d*)",
            "max_drawdown": r"最大回撤?\s*[:：]\s*([+-]?\d+\.?\d*)%?",
            "volatility": r"(?:年化)?波动率?\s*[:：]\s*([+-]?\d+\.?\d*)%?",
            "beta": r"[Bb]eta\s*[:：]\s*([+-]?\d+\.?\d*)",
            "alpha": r"[Aa]lpha\s*[:：]\s*([+-]?\d+\.?\d*)",
        }

    def validate(
        self, ai_text: str, source_metrics: dict[str, float], tolerance: float = 0.05
    ) -> AIValidationResult:
        """
        验证AI输出是否与源数据一致.

        Args:
            ai_text: AI生成的文本
            source_metrics: 原始指标数据
            tolerance: 数值差异容忍度（默认5%）

        Returns:
            验证结果
        """
        issues = []

        # 检查数值一致性
        for metric_name, pattern in self._metrics_patterns.items():
            if metric_name not in source_metrics:
                continue

            source_value = source_metrics[metric_name]
            if source_value is None:
                continue

            # 在文本中查找该指标
            matches = re.findall(pattern, ai_text)
            if not matches:
                continue  # AI没有提到这个指标，不算错误

            # 检查数值是否一致
            for match in matches:
                try:
                    ai_value = float(match)
                    # 处理百分比
                    if abs(source_value) < 1 and abs(ai_value) > 1:
                        ai_value = ai_value / 100
                    elif abs(source_value) > 1 and abs(ai_value) < 1:
                        ai_value = ai_value * 100

                    # 检查差异
                    if source_value != 0:
                        diff_ratio = abs(ai_value - source_value) / abs(source_value)
                    else:
                        diff_ratio = abs(ai_value)

                    if diff_ratio > tolerance:
                        issues.append(
                            f"{metric_name}数值不一致: "
                            f"AI输出{ai_value:.4f} vs 实际{source_value:.4f} "
                            f"(差异{diff_ratio:.1%})"
                        )
                except ValueError:
                    continue

        # 检查矛盾表述
        contradiction_patterns = [
            (r"夏普比率.*大于.*1.*", r"夏普比率.*小于.*0\.5", "sharpe_ratio"),
            (r"最大回撤.*小于.*10%", r"最大回撤.*大于.*20%", "max_drawdown"),
        ]

        for pos_pattern, neg_pattern, metric in contradiction_patterns:
            pos_match = bool(re.search(pos_pattern, ai_text))
            neg_match = bool(re.search(neg_pattern, ai_text))
            if pos_match and neg_match:
                issues.append(f"文本中存在关于{metric}的矛盾表述")

        # 计算置信度
        confidence = max(0.0, 1.0 - len(issues) * 0.2)

        return AIValidationResult(
            passed=len(issues) == 0, issues=issues, confidence_score=confidence
        )

    def validate_summary_consistency(
        self, summary: str, metrics: dict[str, float]
    ) -> AIValidationResult:
        """验证摘要与指标的一致性."""
        issues = []

        # 检查正面/负面描述与数据是否一致
        total_return = metrics.get("total_return", 0)
        sharpe = metrics.get("sharpe_ratio", 0)

        positive_words = ["优秀", "良好", "优异", "出色", "强劲"]
        negative_words = ["较差", "不佳", "欠佳", "疲软", "亏损"]

        has_positive = any(w in summary for w in positive_words)
        has_negative = any(w in summary for w in negative_words)

        # 如果收益率为负但描述为优秀
        if total_return < 0 and has_positive and not has_negative:
            issues.append(f"总收益率为负({total_return:.2%})但描述为正面")

        # 如果夏普比率低但描述为优秀
        if sharpe is not None and sharpe < 0.5 and has_positive:
            issues.append(f"夏普比率较低({sharpe:.2f})但描述为优秀")

        confidence = max(0.0, 1.0 - len(issues) * 0.3)

        return AIValidationResult(
            passed=len(issues) == 0, issues=issues, confidence_score=confidence
        )
