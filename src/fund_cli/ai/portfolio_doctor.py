"""
投资组合诊断模块

帮助用户评估现有组合的健康状况，发现潜在风险，并提供优化建议。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

from fund_cli.analysis.performance import PerformanceAnalyzer
from fund_cli.analysis.risk import RiskAnalyzer
from fund_cli.core.cross_validator import CrossValidator
from fund_cli.core.data_manager import DataManager

logger = logging.getLogger(__name__)


class HealthLevel(str, Enum):
    """健康等级"""

    EXCELLENT = "优秀"
    GOOD = "良好"
    MODERATE = "一般"
    POOR = "较差"
    CRITICAL = "危险"


class DiagnosisCategory(str, Enum):
    """诊断类别"""

    DIVERSIFICATION = "分散度"
    CONCENTRATION = "集中度"
    STYLE_DRIFT = "风格漂移"
    RISK_EXPOSURE = "风险敞口"
    PERFORMANCE = "业绩表现"
    CORRELATION = "相关性"


@dataclass
class DiagnosisItem:
    """单项诊断结果"""

    category: DiagnosisCategory
    level: HealthLevel
    score: float  # 0-100
    description: str
    details: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class PortfolioDiagnosis:
    """组合诊断报告"""

    # 整体健康评分
    overall_score: float
    overall_level: HealthLevel
    # 各项诊断结果
    diagnoses: list[DiagnosisItem]
    # 风险提示
    risk_warnings: list[str]
    # 优化建议
    optimization_suggestions: list[str]
    # 组合统计
    portfolio_stats: dict[str, Any] = field(default_factory=dict)


class DiversificationAnalyzer:
    """分散度分析器"""

    def analyze(self, weights: dict[str, float], correlations: pd.DataFrame | None = None) -> DiagnosisItem:
        """
        分析组合分散度

        Args:
            weights: 各基金权重
            correlations: 相关性矩阵（可选）

        Returns:
            分散度诊断结果
        """
        if not weights:
            return DiagnosisItem(
                category=DiagnosisCategory.DIVERSIFICATION,
                level=HealthLevel.CRITICAL,
                score=0,
                description="组合为空，无法分析",
            )

        # 计算有效持仓数量（Effective Number of Holdings）
        weights_arr = np.array(list(weights.values()))
        weights_arr = weights_arr[weights_arr > 0]

        if len(weights_arr) == 0:
            return DiagnosisItem(
                category=DiagnosisCategory.DIVERSIFICATION,
                level=HealthLevel.CRITICAL,
                score=0,
                description="组合为空，无法分析",
            )

        # Herfindahl-Hirschman Index (HHI)
        hhi = np.sum(weights_arr**2)

        # 有效持仓数量
        effective_n = 1 / hhi if hhi > 0 else 1

        # 分散度评分（有效持仓越多越好）
        if effective_n >= 5:
            level = HealthLevel.EXCELLENT
            score = 90
            description = f"组合分散度优秀，有效持仓{effective_n:.1f}只"
        elif effective_n >= 3:
            level = HealthLevel.GOOD
            score = 75
            description = f"组合分散度良好，有效持仓{effective_n:.1f}只"
        elif effective_n >= 2:
            level = HealthLevel.MODERATE
            score = 60
            description = f"组合分散度一般，有效持仓{effective_n:.1f}只"
        else:
            level = HealthLevel.POOR
            score = 40
            description = f"组合分散度较差，有效持仓仅{effective_n:.1f}只"

        suggestions = []
        if effective_n < 3:
            suggestions.append("建议增加持仓数量，降低单一资产风险")
        if hhi > 0.5:
            suggestions.append("建议降低单一持仓权重，实现更均衡的配置")

        return DiagnosisItem(
            category=DiagnosisCategory.DIVERSIFICATION,
            level=level,
            score=score,
            description=description,
            details={
                "effective_n": round(effective_n, 2),
                "hhi": round(hhi, 4),
                "actual_n": len(weights_arr),
            },
            suggestions=suggestions,
        )


class ConcentrationAnalyzer:
    """集中度分析器"""

    def analyze(self, weights: dict[str, float], threshold: float = 0.3) -> DiagnosisItem:
        """
        分析组合集中度

        Args:
            weights: 各基金权重
            threshold: 集中度阈值

        Returns:
            集中度诊断结果
        """
        if not weights:
            return DiagnosisItem(
                category=DiagnosisCategory.CONCENTRATION,
                level=HealthLevel.CRITICAL,
                score=0,
                description="组合为空，无法分析",
            )

        weights_arr = np.array(list(weights.values()))

        # Top1 持仓权重
        top1_weight = np.max(weights_arr)

        # Top3 持仓权重
        sorted_weights = np.sort(weights_arr)[::-1]
        top3_weight = np.sum(sorted_weights[:3]) if len(sorted_weights) >= 3 else np.sum(sorted_weights)

        # Top5 持仓权重
        top5_weight = np.sum(sorted_weights[:5]) if len(sorted_weights) >= 5 else np.sum(sorted_weights)

        # 评分
        if top1_weight <= 0.2:
            level = HealthLevel.EXCELLENT
            score = 90
            description = f"集中度控制优秀，最大持仓{top1_weight*100:.1f}%"
        elif top1_weight <= 0.3:
            level = HealthLevel.GOOD
            score = 75
            description = f"集中度控制良好，最大持仓{top1_weight*100:.1f}%"
        elif top1_weight <= 0.5:
            level = HealthLevel.MODERATE
            score = 60
            description = f"集中度偏高，最大持仓{top1_weight*100:.1f}%"
        else:
            level = HealthLevel.POOR
            score = 40
            description = f"集中度过高，最大持仓{top1_weight*100:.1f}%"

        suggestions = []
        if top1_weight > threshold:
            suggestions.append(f"最大持仓权重{top1_weight*100:.1f}%超过{threshold*100}%阈值，建议降低")
        if top3_weight > 0.6:
            suggestions.append("前三大持仓占比过高，建议分散配置")

        return DiagnosisItem(
            category=DiagnosisCategory.CONCENTRATION,
            level=level,
            score=score,
            description=description,
            details={
                "top1_weight": round(top1_weight, 4),
                "top3_weight": round(top3_weight, 4),
                "top5_weight": round(top5_weight, 4),
            },
            suggestions=suggestions,
        )


class CorrelationAnalyzer:
    """相关性分析器"""

    def analyze(
        self,
        returns_data: pd.DataFrame | None = None,
        correlations: pd.DataFrame | None = None,
    ) -> DiagnosisItem:
        """
        分析组合内资产相关性

        Args:
            returns_data: 收益率数据
            correlations: 相关性矩阵（可选，如已计算）

        Returns:
            相关性诊断结果
        """
        if correlations is None:
            if returns_data is None or returns_data.empty:
                return DiagnosisItem(
                    category=DiagnosisCategory.CORRELATION,
                    level=HealthLevel.MODERATE,
                    score=60,
                    description="无相关性数据，无法分析",
                )
            correlations = returns_data.corr()

        # 计算平均相关系数（排除对角线）
        n = len(correlations)
        if n < 2:
            return DiagnosisItem(
                category=DiagnosisCategory.CORRELATION,
                level=HealthLevel.MODERATE,
                score=60,
                description="持仓数量不足，无法分析相关性",
            )

        # 提取上三角矩阵（排除对角线）
        upper_tri = correlations.values[np.triu_indices(n, k=1)]
        avg_corr = np.mean(np.abs(upper_tri))
        max_corr = np.max(np.abs(upper_tri))

        # 评分
        if avg_corr <= 0.3:
            level = HealthLevel.EXCELLENT
            score = 90
            description = f"相关性低，平均相关系数{avg_corr:.2f}"
        elif avg_corr <= 0.5:
            level = HealthLevel.GOOD
            score = 75
            description = f"相关性适中，平均相关系数{avg_corr:.2f}"
        elif avg_corr <= 0.7:
            level = HealthLevel.MODERATE
            score = 60
            description = f"相关性偏高，平均相关系数{avg_corr:.2f}"
        else:
            level = HealthLevel.POOR
            score = 40
            description = f"相关性过高，平均相关系数{avg_corr:.2f}"

        suggestions = []
        if avg_corr > 0.6:
            suggestions.append("组合内资产相关性较高，分散效果有限")
        if max_corr > 0.9:
            suggestions.append("存在高度相关资产，建议替换其一")

        return DiagnosisItem(
            category=DiagnosisCategory.CORRELATION,
            level=level,
            score=score,
            description=description,
            details={
                "avg_correlation": round(avg_corr, 4),
                "max_correlation": round(max_corr, 4),
            },
            suggestions=suggestions,
        )


class RiskExposureAnalyzer:
    """风险敞口分析器"""

    def analyze(
        self,
        weights: dict[str, float],
        fund_risks: dict[str, float] | None = None,
    ) -> DiagnosisItem:
        """
        分析组合风险敞口

        Args:
            weights: 各基金权重
            fund_risks: 各基金风险指标（如波动率）

        Returns:
            风险敞口诊断结果
        """
        if not weights:
            return DiagnosisItem(
                category=DiagnosisCategory.RISK_EXPOSURE,
                level=HealthLevel.CRITICAL,
                score=0,
                description="组合为空，无法分析",
            )

        if fund_risks is None:
            return DiagnosisItem(
                category=DiagnosisCategory.RISK_EXPOSURE,
                level=HealthLevel.MODERATE,
                score=60,
                description="无风险数据，无法分析风险敞口",
            )

        # 计算加权风险
        total_risk = 0.0
        for fund_code, weight in weights.items():
            risk = fund_risks.get(fund_code, 0)
            total_risk += weight * risk

        # 风险贡献分析
        risk_contributions = {}
        for fund_code, weight in weights.items():
            risk = fund_risks.get(fund_code, 0)
            contribution = weight * risk / total_risk if total_risk > 0 else 0
            risk_contributions[fund_code] = contribution

        # 找出风险贡献最大的资产
        max_contributor = max(risk_contributions, key=risk_contributions.get)
        max_contribution = risk_contributions[max_contributor]

        # 评分
        if max_contribution <= 0.3:
            level = HealthLevel.EXCELLENT
            score = 90
            description = f"风险敞口分散，最大风险贡献{max_contribution*100:.1f}%"
        elif max_contribution <= 0.5:
            level = HealthLevel.GOOD
            score = 75
            description = f"风险敞口适中，最大风险贡献{max_contribution*100:.1f}%"
        elif max_contribution <= 0.7:
            level = HealthLevel.MODERATE
            score = 60
            description = f"风险敞口偏高，最大风险贡献{max_contribution*100:.1f}%"
        else:
            level = HealthLevel.POOR
            score = 40
            description = f"风险敞口集中，最大风险贡献{max_contribution*100:.1f}%"

        suggestions = []
        if max_contribution > 0.5:
            suggestions.append(f"基金{max_contributor}贡献了{max_contribution*100:.1f}%的风险，建议降低权重")

        return DiagnosisItem(
            category=DiagnosisCategory.RISK_EXPOSURE,
            level=level,
            score=score,
            description=description,
            details={
                "total_risk": round(total_risk, 4),
                "max_contributor": max_contributor,
                "max_contribution": round(max_contribution, 4),
                "risk_contributions": {k: round(v, 4) for k, v in risk_contributions.items()},
            },
            suggestions=suggestions,
        )


class PortfolioDoctor:
    """
    投资组合诊断器

    整合多项诊断功能，生成完整的组合诊断报告。
    """

    def __init__(self, data_manager: DataManager | None = None):
        """
        初始化组合诊断器

        Args:
            data_manager: 数据管理器实例
        """
        self._dm = data_manager or DataManager()
        self._diversification_analyzer = DiversificationAnalyzer()
        self._concentration_analyzer = ConcentrationAnalyzer()
        self._correlation_analyzer = CorrelationAnalyzer()
        self._risk_exposure_analyzer = RiskExposureAnalyzer()
        self._performance_analyzer = PerformanceAnalyzer()
        self._risk_analyzer = RiskAnalyzer()

    def diagnose(
        self,
        funds: list[str],
        weights: list[float] | None = None,
        returns_data: pd.DataFrame | None = None,
        fund_info: dict[str, dict] | None = None,
    ) -> PortfolioDiagnosis:
        """
        执行组合诊断

        Args:
            funds: 基金代码列表
            weights: 权重列表（如为 None 则等权）
            returns_data: 收益率数据（可选）
            fund_info: 基金信息字典（可选）

        Returns:
            组合诊断报告
        """
        # 处理空组合
        if not funds:
            return PortfolioDiagnosis(
                overall_score=0,
                overall_level=HealthLevel.CRITICAL,
                diagnoses=[
                    DiagnosisItem(
                        category=DiagnosisCategory.DIVERSIFICATION,
                        level=HealthLevel.CRITICAL,
                        score=0,
                        description="组合为空，无法分析",
                    )
                ],
                risk_warnings=["组合为空"],
                optimization_suggestions=["请添加基金到组合中"],
                portfolio_stats={"fund_count": 0},
            )

        # 构建权重字典
        if weights is None:
            weights = [1.0 / len(funds)] * len(funds)
        weights_dict = dict(zip(funds, weights))

        diagnoses = []

        # 1. 分散度分析
        correlations = None
        if returns_data is not None and not returns_data.empty:
            correlations = returns_data.corr()

        div_diagnosis = self._diversification_analyzer.analyze(weights_dict, correlations)
        diagnoses.append(div_diagnosis)

        # 2. 集中度分析
        conc_diagnosis = self._concentration_analyzer.analyze(weights_dict)
        diagnoses.append(conc_diagnosis)

        # 3. 相关性分析
        corr_diagnosis = self._correlation_analyzer.analyze(returns_data, correlations)
        diagnoses.append(corr_diagnosis)

        # 4. 风险敞口分析
        fund_risks = None
        if fund_info:
            fund_risks = {
                code: info.get("volatility", info.get("risk", 0))
                for code, info in fund_info.items()
            }
        risk_diagnosis = self._risk_exposure_analyzer.analyze(weights_dict, fund_risks)
        diagnoses.append(risk_diagnosis)

        # 5. 计算整体评分
        scores = [d.score for d in diagnoses]
        overall_score = np.mean(scores)

        if overall_score >= 80:
            overall_level = HealthLevel.EXCELLENT
        elif overall_score >= 65:
            overall_level = HealthLevel.GOOD
        elif overall_score >= 50:
            overall_level = HealthLevel.MODERATE
        elif overall_score >= 35:
            overall_level = HealthLevel.POOR
        else:
            overall_level = HealthLevel.CRITICAL

        # 6. 汇总风险提示
        risk_warnings = []
        for d in diagnoses:
            if d.level in [HealthLevel.POOR, HealthLevel.CRITICAL]:
                risk_warnings.append(f"【{d.category.value}】{d.description}")

        # 7. 汇总优化建议
        optimization_suggestions = []
        for d in diagnoses:
            optimization_suggestions.extend(d.suggestions)

        # 去重
        optimization_suggestions = list(dict.fromkeys(optimization_suggestions))

        # 8. 组合统计
        portfolio_stats = {
            "fund_count": len(funds),
            "total_weight": round(sum(weights), 4),
            "max_weight": round(max(weights), 4),
            "min_weight": round(min(weights), 4),
        }

        return PortfolioDiagnosis(
            overall_score=round(overall_score, 2),
            overall_level=overall_level,
            diagnoses=diagnoses,
            risk_warnings=risk_warnings,
            optimization_suggestions=optimization_suggestions,
            portfolio_stats=portfolio_stats,
        )

    def format_diagnosis(self, diagnosis: PortfolioDiagnosis) -> str:
        """
        格式化诊断报告为可读文本

        Args:
            diagnosis: 组合诊断报告

        Returns:
            格式化的诊断文本
        """
        lines = ["# 投资组合诊断报告\n"]

        # 整体评估
        lines.append("## 整体评估")
        lines.append(f"- 健康评分: {diagnosis.overall_score}/100")
        lines.append(f"- 健康等级: {diagnosis.overall_level.value}")
        lines.append("")

        # 各项诊断
        lines.append("## 详细诊断")
        for d in diagnosis.diagnoses:
            lines.append(f"### {d.category.value}")
            lines.append(f"- 状态: {d.level.value}")
            lines.append(f"- 评分: {d.score}/100")
            lines.append(f"- 说明: {d.description}")
            if d.details:
                lines.append("- 详情:")
                for k, v in d.details.items():
                    if isinstance(v, dict):
                        lines.append(f"  - {k}:")
                        for kk, vv in v.items():
                            lines.append(f"    - {kk}: {vv}")
                    else:
                        lines.append(f"  - {k}: {v}")
            if d.suggestions:
                lines.append("- 建议:")
                for s in d.suggestions:
                    lines.append(f"  - {s}")
            lines.append("")

        # 风险提示
        if diagnosis.risk_warnings:
            lines.append("## ⚠️ 风险提示")
            for w in diagnosis.risk_warnings:
                lines.append(f"- {w}")
            lines.append("")

        # 优化建议
        if diagnosis.optimization_suggestions:
            lines.append("## 💡 优化建议")
            for s in diagnosis.optimization_suggestions:
                lines.append(f"- {s}")
            lines.append("")

        # 组合统计
        lines.append("## 组合统计")
        for k, v in diagnosis.portfolio_stats.items():
            lines.append(f"- {k}: {v}")

        return "\n".join(lines)


def diagnose_portfolio(
    funds: list[str],
    weights: list[float] | None = None,
    data_manager: DataManager | None = None,
) -> PortfolioDiagnosis:
    """
    组合诊断便捷函数

    Args:
        funds: 基金代码列表
        weights: 权重列表
        data_manager: 数据管理器实例

    Returns:
        组合诊断报告
    """
    doctor = PortfolioDoctor(data_manager)
    return doctor.diagnose(funds, weights)
