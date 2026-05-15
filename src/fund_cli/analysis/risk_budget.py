"""
风险预算模块

帮助用户理解组合风险的来源和分配，支持风险贡献分解和风险预算优化。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd

from fund_cli.core.data_manager import DataManager

logger = logging.getLogger(__name__)


class RiskMeasure(str, Enum):
    """风险度量方法"""

    VOLATILITY = "波动率"
    VAR = "VaR"
    CVAR = "CVaR"
    DRAWDOWN = "最大回撤"
    BETA = "Beta"


class OptimizationObjective(str, Enum):
    """优化目标"""

    EQUAL_RISK = "等风险贡献"
    MIN_VARIANCE = "最小方差"
    MAX_SHARPE = "最大夏普"
    RISK_PARITY = "风险平价"


@dataclass
class RiskContribution:
    """风险贡献"""

    asset_code: str
    asset_name: str
    weight: float  # 权重
    marginal_risk: float  # 边际风险
    risk_contribution: float  # 风险贡献（绝对值）
    risk_contribution_pct: float  # 风险贡献占比 (%)
    risk_type: str = "波动率"  # 风险类型


@dataclass
class RiskBudgetResult:
    """风险预算结果"""

    # 各资产风险贡献
    contributions: list[RiskContribution]
    # 组合总风险
    portfolio_risk: float
    # 风险集中度
    risk_concentration: float  # HHI指数
    # 有效风险资产数
    effective_risk_assets: float
    # 风险分散度评分
    diversification_score: float  # 0-100


@dataclass
class TailRiskContribution:
    """尾部风险贡献"""

    asset_code: str
    var_contribution: float  # VaR贡献
    cvar_contribution: float  # CVaR贡献
    tail_risk_ratio: float  # 尾部风险占比


@dataclass
class RiskBudgetReport:
    """风险预算报告"""

    # 基本信息
    portfolio_name: str
    analysis_date: str
    # 风险贡献分析
    risk_contributions: list[RiskContribution]
    # 尾部风险分析
    tail_risk: list[TailRiskContribution]
    # 风险预算结果
    budget_result: RiskBudgetResult
    # 优化建议
    optimization_suggestions: list[str]
    # 风险提示
    risk_warnings: list[str]


class RiskContributionCalculator:
    """风险贡献计算器"""

    def calculate(
        self,
        weights: dict[str, float],
        returns: pd.DataFrame | None = None,
        volatilities: dict[str, float] | None = None,
        correlations: pd.DataFrame | None = None,
    ) -> list[RiskContribution]:
        """
        计算各资产的风险贡献

        Args:
            weights: 各资产权重
            returns: 收益率数据（用于计算协方差矩阵）
            volatilities: 各资产波动率
            correlations: 相关性矩阵

        Returns:
            各资产风险贡献列表
        """
        if not weights:
            return []

        assets = list(weights.keys())
        n = len(assets)
        weights_arr = np.array([weights[a] for a in assets])

        # 获取或计算波动率
        if volatilities is None:
            if returns is not None:
                volatilities = {a: returns[a].std() * np.sqrt(252) for a in assets if a in returns.columns}
            else:
                volatilities = dict.fromkeys(assets, 0.15)  # 默认15%年化波动率

        vols_arr = np.array([volatilities.get(a, 0.15) for a in assets])

        # 获取或计算相关性矩阵
        if correlations is None:
            if returns is not None:
                correlations = returns[assets].corr()
            else:
                correlations = pd.DataFrame(np.eye(n), index=assets, columns=assets)

        # 构建协方差矩阵
        corr_arr = correlations.values[:n, :n]
        cov_matrix = np.outer(vols_arr, vols_arr) * corr_arr

        # 计算组合风险
        portfolio_var = weights_arr @ cov_matrix @ weights_arr
        portfolio_risk = np.sqrt(portfolio_var)

        # 计算边际风险贡献 (MCR)
        # MCR_i = d(sigma_p) / d(w_i) = (Cov * w)_i / sigma_p
        marginal_contrib = cov_matrix @ weights_arr / portfolio_risk if portfolio_risk > 0 else np.zeros(n)

        # 计算风险贡献 (RC)
        # RC_i = w_i * MCR_i
        risk_contrib = weights_arr * marginal_contrib

        # 计算风险贡献占比
        risk_contrib_pct = risk_contrib / portfolio_risk * 100 if portfolio_risk > 0 else np.zeros(n)

        # 构建结果
        contributions = []
        for i, asset in enumerate(assets):
            contributions.append(
                RiskContribution(
                    asset_code=asset,
                    asset_name=asset,  # 可以后续填充名称
                    weight=round(weights_arr[i], 4),
                    marginal_risk=round(marginal_contrib[i], 4),
                    risk_contribution=round(risk_contrib[i], 4),
                    risk_contribution_pct=round(risk_contrib_pct[i], 2),
                    risk_type="波动率",
                )
            )

        return contributions


class RiskConcentrationAnalyzer:
    """风险集中度分析器"""

    def analyze(
        self,
        contributions: list[RiskContribution],
    ) -> RiskBudgetResult:
        """
        分析风险集中度

        Args:
            contributions: 风险贡献列表

        Returns:
            风险预算结果
        """
        if not contributions:
            return RiskBudgetResult(
                contributions=[],
                portfolio_risk=0,
                risk_concentration=0,
                effective_risk_assets=0,
                diversification_score=0,
            )

        # 计算组合总风险
        portfolio_risk = sum(c.risk_contribution for c in contributions)

        # 计算风险贡献占比
        contrib_pcts = [c.risk_contribution_pct / 100 for c in contributions]

        # 计算HHI指数（风险集中度）
        hhi = sum(p**2 for p in contrib_pcts)

        # 计算有效风险资产数
        effective_n = 1 / hhi if hhi > 0 else 0

        # 计算风险分散度评分
        if effective_n >= 4:
            diversification_score = 90
        elif effective_n >= 3:
            diversification_score = 75
        elif effective_n >= 2:
            diversification_score = 60
        else:
            diversification_score = 40

        return RiskBudgetResult(
            contributions=contributions,
            portfolio_risk=round(portfolio_risk, 4),
            risk_concentration=round(hhi, 4),
            effective_risk_assets=round(effective_n, 2),
            diversification_score=diversification_score,
        )


class TailRiskAnalyzer:
    """尾部风险分析器"""

    def analyze(
        self,
        weights: dict[str, float],
        returns: pd.DataFrame | None = None,
        confidence: float = 0.95,
    ) -> list[TailRiskContribution]:
        """
        分析尾部风险贡献

        Args:
            weights: 各资产权重
            returns: 收益率数据
            confidence: 置信水平

        Returns:
            各资产尾部风险贡献
        """
        if not weights or returns is None:
            return []

        assets = list(weights.keys())
        len(assets)

        # 计算组合收益率
        weights_arr = np.array([weights[a] for a in assets])
        available_assets = [a for a in assets if a in returns.columns]

        if not available_assets:
            return []

        portfolio_returns = returns[available_assets] @ weights_arr[: len(available_assets)]

        # 计算VaR和CVaR
        var_threshold = np.percentile(portfolio_returns, (1 - confidence) * 100)
        cvar = portfolio_returns[portfolio_returns <= var_threshold].mean()

        # 计算各资产对尾部风险的贡献（简化方法）
        tail_contributions = []

        for i, asset in enumerate(assets):
            if asset not in returns.columns:
                continue

            # 资产在尾部情景下的表现
            asset_tail_returns = returns[asset][portfolio_returns <= var_threshold]

            # 贡献 = 权重 * 资产尾部收益 / 组合尾部收益
            if cvar != 0:
                var_contrib = weights_arr[i] * asset_tail_returns.mean() / abs(cvar) * 100
                cvar_contrib = var_contrib  # 简化处理
            else:
                var_contrib = 0
                cvar_contrib = 0

            tail_contributions.append(
                TailRiskContribution(
                    asset_code=asset,
                    var_contribution=round(var_contrib, 2),
                    cvar_contribution=round(cvar_contrib, 2),
                    tail_risk_ratio=round(abs(var_contrib), 2),
                )
            )

        return tail_contributions


class RiskBudgetOptimizer:
    """风险预算优化器"""

    def optimize(
        self,
        returns: pd.DataFrame | None = None,
        volatilities: dict[str, float] | None = None,
        correlations: pd.DataFrame | None = None,
        target_risk_budget: dict[str, float] | None = None,
        objective: OptimizationObjective = OptimizationObjective.RISK_PARITY,
    ) -> dict[str, float]:
        """
        基于风险预算优化权重

        Args:
            returns: 收益率数据
            volatilities: 各资产波动率
            correlations: 相关性矩阵
            target_risk_budget: 目标风险预算
            objective: 优化目标

        Returns:
            优化后的权重
        """
        # 确定资产列表
        if volatilities:
            assets = list(volatilities.keys())
        elif returns is not None:
            assets = list(returns.columns)
        else:
            return {}

        n = len(assets)

        if n == 0:
            return {}

        # 获取波动率
        if volatilities is None:
            if returns is not None:
                volatilities = {a: returns[a].std() * np.sqrt(252) for a in assets}
            else:
                volatilities = dict.fromkeys(assets, 0.15)

        vols_arr = np.array([volatilities.get(a, 0.15) for a in assets])

        # 获取相关性
        if correlations is None and returns is not None:
            correlations = returns[assets].corr()

        if correlations is None:
            corr_arr = np.eye(n)
        else:
            corr_arr = correlations.values[:n, :n]

        # 构建协方差矩阵
        cov_matrix = np.outer(vols_arr, vols_arr) * corr_arr

        # 根据优化目标计算权重
        if objective == OptimizationObjective.RISK_PARITY:
            # 风险平价：各资产风险贡献相等
            # 简化解法：权重与波动率成反比
            inv_vols = 1 / vols_arr
            weights_arr = inv_vols / np.sum(inv_vols)

        elif objective == OptimizationObjective.MIN_VARIANCE:
            # 最小方差组合
            # 简化解法：使用逆协方差矩阵
            try:
                inv_cov = np.linalg.inv(cov_matrix)
                ones = np.ones(n)
                weights_arr = inv_cov @ ones / (ones @ inv_cov @ ones)
                weights_arr = np.maximum(weights_arr, 0)  # 不允许做空
                weights_arr = weights_arr / np.sum(weights_arr)
            except np.linalg.LinAlgError:
                weights_arr = np.ones(n) / n

        elif objective == OptimizationObjective.EQUAL_RISK:
            # 等风险贡献
            # 与风险平价类似
            inv_vols = 1 / vols_arr
            weights_arr = inv_vols / np.sum(inv_vols)

        else:
            # 默认等权
            weights_arr = np.ones(n) / n

        # 构建结果
        return {asset: round(weights_arr[i], 4) for i, asset in enumerate(assets)}


class RiskBudgetAnalyzer:
    """
    风险预算分析主类

    整合风险贡献计算、风险集中度分析、尾部风险分析、风险预算优化等功能。
    """

    def __init__(self, data_manager: DataManager | None = None):
        """
        初始化风险预算分析器

        Args:
            data_manager: 数据管理器实例
        """
        self._dm = data_manager or DataManager()
        self._contribution_calculator = RiskContributionCalculator()
        self._concentration_analyzer = RiskConcentrationAnalyzer()
        self._tail_risk_analyzer = TailRiskAnalyzer()
        self._optimizer = RiskBudgetOptimizer()

    def analyze(
        self,
        funds: list[str],
        weights: list[float] | None = None,
        returns: pd.DataFrame | None = None,
        volatilities: dict[str, float] | None = None,
        correlations: pd.DataFrame | None = None,
    ) -> RiskBudgetReport:
        """
        执行风险预算分析

        Args:
            funds: 基金代码列表
            weights: 权重列表
            returns: 收益率数据
            volatilities: 各基金波动率
            correlations: 相关性矩阵

        Returns:
            风险预算报告
        """
        from datetime import datetime

        # 构建权重字典
        if weights is None:
            weights = [1.0 / len(funds)] * len(funds)
        weights_dict = dict(zip(funds, weights, strict=False))

        # 计算风险贡献
        contributions = self._contribution_calculator.calculate(
            weights_dict, returns, volatilities, correlations
        )

        # 分析风险集中度
        budget_result = self._concentration_analyzer.analyze(contributions)

        # 分析尾部风险
        tail_risk = self._tail_risk_analyzer.analyze(weights_dict, returns)

        # 生成优化建议
        optimization_suggestions = self._generate_optimization_suggestions(
            contributions, budget_result
        )

        # 生成风险提示
        risk_warnings = self._generate_risk_warnings(contributions, budget_result)

        return RiskBudgetReport(
            portfolio_name="投资组合",
            analysis_date=datetime.now().strftime("%Y-%m-%d"),
            risk_contributions=contributions,
            tail_risk=tail_risk,
            budget_result=budget_result,
            optimization_suggestions=optimization_suggestions,
            risk_warnings=risk_warnings,
        )

    def optimize_weights(
        self,
        funds: list[str],
        returns: pd.DataFrame | None = None,
        volatilities: dict[str, float] | None = None,
        objective: OptimizationObjective = OptimizationObjective.RISK_PARITY,
    ) -> dict[str, float]:
        """
        优化组合权重

        Args:
            funds: 基金代码列表
            returns: 收益率数据
            volatilities: 各基金波动率
            objective: 优化目标

        Returns:
            优化后的权重
        """
        return self._optimizer.optimize(
            returns=returns,
            volatilities=volatilities,
            objective=objective,
        )

    def _generate_optimization_suggestions(
        self,
        contributions: list[RiskContribution],
        budget_result: RiskBudgetResult,
    ) -> list[str]:
        """生成优化建议"""
        suggestions = []

        # 基于风险集中度
        if budget_result.risk_concentration > 0.4:
            suggestions.append("风险集中度较高，建议降低高风险贡献资产的权重")

        # 基于有效风险资产数
        if budget_result.effective_risk_assets < 2:
            suggestions.append("有效风险资产数较低，建议增加低相关资产以分散风险")

        # 基于各资产风险贡献
        sorted_contrib = sorted(contributions, key=lambda x: x.risk_contribution_pct, reverse=True)
        if sorted_contrib and sorted_contrib[0].risk_contribution_pct > 50:
            suggestions.append(
                f"资产{sorted_contrib[0].asset_code}贡献了{sorted_contrib[0].risk_contribution_pct:.1f}%的风险，建议降低权重"
            )

        if not suggestions:
            suggestions.append("当前风险配置较为均衡，可维持现有配置")

        return suggestions

    def _generate_risk_warnings(
        self,
        contributions: list[RiskContribution],
        budget_result: RiskBudgetResult,
    ) -> list[str]:
        """生成风险提示"""
        warnings = []

        if budget_result.diversification_score < 60:
            warnings.append("⚠️ 风险分散度较低，组合抗风险能力不足")

        for c in contributions:
            if c.risk_contribution_pct > 60:
                warnings.append(f"⚠️ 资产{c.asset_code}风险贡献过高({c.risk_contribution_pct:.1f}%)")

        if not warnings:
            warnings.append("风险水平正常")

        return warnings

    def format_report(self, report: RiskBudgetReport) -> str:
        """
        格式化风险预算报告

        Args:
            report: 风险预算报告

        Returns:
            格式化的报告文本
        """
        lines = ["# 风险预算分析报告\n"]

        lines.append("## 基本信息")
        lines.append(f"- 组合名称: {report.portfolio_name}")
        lines.append(f"- 分析日期: {report.analysis_date}")
        lines.append("")

        lines.append("## 风险贡献分析")
        lines.append(f"- 组合总风险: {report.budget_result.portfolio_risk:.4f}")
        lines.append(f"- 风险集中度(HHI): {report.budget_result.risk_concentration:.4f}")
        lines.append(f"- 有效风险资产数: {report.budget_result.effective_risk_assets:.2f}")
        lines.append(f"- 风险分散度评分: {report.budget_result.diversification_score}/100")
        lines.append("")

        lines.append("### 各资产风险贡献")
        lines.append("| 资产 | 权重 | 风险贡献 | 占比 |")
        lines.append("|------|------|----------|------|")
        for c in report.risk_contributions:
            lines.append(f"| {c.asset_code} | {c.weight:.2%} | {c.risk_contribution:.4f} | {c.risk_contribution_pct:.1f}% |")
        lines.append("")

        if report.tail_risk:
            lines.append("## 尾部风险分析")
            lines.append("| 资产 | VaR贡献 | CVaR贡献 |")
            lines.append("|------|---------|----------|")
            for t in report.tail_risk:
                lines.append(f"| {t.asset_code} | {t.var_contribution:.2f}% | {t.cvar_contribution:.2f}% |")
            lines.append("")

        if report.risk_warnings:
            lines.append("## 风险提示")
            for w in report.risk_warnings:
                lines.append(f"- {w}")
            lines.append("")

        if report.optimization_suggestions:
            lines.append("## 优化建议")
            for s in report.optimization_suggestions:
                lines.append(f"- {s}")

        return "\n".join(lines)


def analyze_risk_budget(
    funds: list[str],
    weights: list[float] | None = None,
    data_manager: DataManager | None = None,
) -> RiskBudgetReport:
    """
    风险预算分析便捷函数

    Args:
        funds: 基金代码列表
        weights: 权重列表
        data_manager: 数据管理器实例

    Returns:
        风险预算报告
    """
    analyzer = RiskBudgetAnalyzer(data_manager)
    return analyzer.analyze(funds, weights)


def optimize_risk_parity(
    funds: list[str],
    volatilities: dict[str, float] | None = None,
    data_manager: DataManager | None = None,
) -> dict[str, float]:
    """
    风险平价优化便捷函数

    Args:
        funds: 基金代码列表
        volatilities: 各基金波动率
        data_manager: 数据管理器实例

    Returns:
        优化后的权重
    """
    analyzer = RiskBudgetAnalyzer(data_manager)
    return analyzer.optimize_weights(
        funds, volatilities=volatilities, objective=OptimizationObjective.RISK_PARITY
    )
