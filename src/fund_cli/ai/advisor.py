"""
投资建议生成器

将分析结果转化为可执行的投资建议。
支持持仓建议、调仓建议、定投建议、风险提示等功能。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

from fund_cli.ai.user_profile import UserProfile, RiskTolerance
from fund_cli.core.data_manager import DataManager

logger = logging.getLogger(__name__)


class AdviceType(str, Enum):
    """建议类型"""

    HOLDING = "持仓建议"
    REBALANCE = "调仓建议"
    DCA = "定投建议"
    RISK_ALERT = "风险提示"
    OPPORTUNITY = "投资机会"
    EXIT = "退出建议"


class Priority(str, Enum):
    """优先级"""

    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


@dataclass
class AdviceItem:
    """建议项"""

    advice_type: AdviceType
    priority: Priority
    title: str
    description: str
    action: str  # 具体操作建议
    expected_impact: str  # 预期影响
    risk_warning: str
    related_funds: list[str] = field(default_factory=list)


@dataclass
class RebalanceSuggestion:
    """调仓建议"""

    fund_code: str
    fund_name: str
    current_weight: float
    suggested_weight: float
    weight_change: float
    reason: str


@dataclass
class DCASuggestion:
    """定投建议"""

    fund_code: str
    fund_name: str
    suggested_amount: float  # 建议金额（元）
    frequency: str  # 定投频率
    expected_return: float  # 预期年化收益
    risk_level: str


@dataclass
class InvestmentAdviceReport:
    """投资建议报告"""

    user_id: str
    report_date: str
    # 建议列表
    advices: list[AdviceItem]
    # 调仓建议
    rebalance_suggestions: list[RebalanceSuggestion]
    # 定投建议
    dca_suggestions: list[DCASuggestion]
    # 综合建议
    overall_advice: str
    # 风险提示
    risk_warnings: list[str]


class HoldingAnalyzer:
    """持仓分析器"""

    def analyze(
        self,
        holdings: list[dict[str, Any]],
        profile: UserProfile,
    ) -> list[AdviceItem]:
        """
        分析持仓并生成建议

        Args:
            holdings: 持仓列表
            profile: 用户画像

        Returns:
            持仓建议列表
        """
        advices = []

        if not holdings:
            advices.append(
                AdviceItem(
                    advice_type=AdviceType.HOLDING,
                    priority=Priority.HIGH,
                    title="建议建立投资组合",
                    description="您当前没有持仓，建议根据您的风险偏好建立投资组合",
                    action="参考推荐基金，建立分散化的投资组合",
                    expected_impact="实现资产增值目标",
                    risk_warning="投资有风险，请根据自身情况配置",
                )
            )
            return advices

        # 分析集中度
        total_value = sum(h.get("value", h.get("market_value", 0)) for h in holdings)
        if total_value > 0:
            max_holding = max(holdings, key=lambda x: x.get("value", x.get("market_value", 0)))
            max_weight = max_holding.get("value", max_holding.get("market_value", 0)) / total_value

            if max_weight > 0.5:
                advices.append(
                    AdviceItem(
                        advice_type=AdviceType.RISK_ALERT,
                        priority=Priority.HIGH,
                        title="持仓集中度过高",
                        description=f"最大持仓{max_holding.get('fund_name', max_holding.get('fund_code', '未知'))}占比{max_weight*100:.1f}%，风险集中",
                        action="建议降低单一持仓权重至30%以下",
                        expected_impact="降低单一资产风险",
                        risk_warning="集中持仓可能导致较大回撤",
                        related_funds=[max_holding.get("fund_code", "")],
                    )
                )

        # 分析风险匹配
        for h in holdings:
            fund_risk = h.get("risk_level", "中风险")
            if profile.risk_assessment.tolerance == RiskTolerance.CONSERVATIVE:
                if "股票" in h.get("fund_type", ""):
                    advices.append(
                        AdviceItem(
                            advice_type=AdviceType.RISK_ALERT,
                            priority=Priority.MEDIUM,
                            title="持仓风险偏高",
                            description=f"{h.get('fund_name', h.get('fund_code', ''))}为股票型基金，与您的保守型风险偏好不匹配",
                            action="建议降低股票型基金配置比例",
                            expected_impact="降低组合波动",
                            risk_warning="股票型基金波动较大",
                            related_funds=[h.get("fund_code", "")],
                        )
                    )
                    break

        return advices


class RebalanceAdvisor:
    """调仓顾问"""

    def suggest(
        self,
        holdings: list[dict[str, Any]],
        profile: UserProfile,
        target_allocation: dict[str, float] | None = None,
    ) -> list[RebalanceSuggestion]:
        """
        生成调仓建议

        Args:
            holdings: 当前持仓
            profile: 用户画像
            target_allocation: 目标配置

        Returns:
            调仓建议列表
        """
        suggestions = []

        if not holdings:
            return suggestions

        # 计算当前权重
        total_value = sum(h.get("value", h.get("market_value", 0)) for h in holdings)
        if total_value == 0:
            return suggestions

        current_weights = {}
        for h in holdings:
            code = h.get("fund_code", "")
            value = h.get("value", h.get("market_value", 0))
            current_weights[code] = value / total_value

        # 如果没有目标配置，根据风险偏好生成
        if target_allocation is None:
            target_allocation = self._get_default_allocation(profile)

        # 生成调仓建议
        for h in holdings:
            code = h.get("fund_code", "")
            name = h.get("fund_name", code)
            current = current_weights.get(code, 0)
            target = target_allocation.get(code, current)
            change = target - current

            if abs(change) > 0.05:  # 变动超过5%
                if change > 0:
                    reason = f"根据{profile.risk_assessment.tolerance.value}风险偏好，建议增持"
                else:
                    reason = "建议减持以优化组合结构"

                suggestions.append(
                    RebalanceSuggestion(
                        fund_code=code,
                        fund_name=name,
                        current_weight=round(current * 100, 2),
                        suggested_weight=round(target * 100, 2),
                        weight_change=round(change * 100, 2),
                        reason=reason,
                    )
                )

        return suggestions

    def _get_default_allocation(self, profile: UserProfile) -> dict[str, float]:
        """获取默认配置"""
        # 简化实现
        return {}


class DCAAdvisor:
    """定投顾问"""

    def suggest(
        self,
        profile: UserProfile,
        available_funds: list[str] | None = None,
        monthly_amount: float = 1000,
    ) -> list[DCASuggestion]:
        """
        生成定投建议

        Args:
            profile: 用户画像
            available_funds: 可选基金
            monthly_amount: 每月定投金额

        Returns:
            定投建议列表
        """
        suggestions = []

        # 根据风险偏好推荐定投基金
        if profile.risk_assessment.tolerance == RiskTolerance.CONSERVATIVE:
            fund_types = ["债券型", "货币型"]
            expected_return = 4.0
            risk_level = "低"
        elif profile.risk_assessment.tolerance == RiskTolerance.AGGRESSIVE:
            fund_types = ["股票型", "指数型"]
            expected_return = 12.0
            risk_level = "高"
        else:
            fund_types = ["混合型", "股票型"]
            expected_return = 8.0
            risk_level = "中"

        # 生成建议
        np.random.seed(42)
        for i, ftype in enumerate(fund_types[:2]):
            suggestions.append(
                DCASuggestion(
                    fund_code=f"00000{i+1}",
                    fund_name=f"{ftype}基金{i+1}",
                    suggested_amount=monthly_amount / len(fund_types),
                    frequency="每月",
                    expected_return=expected_return,
                    risk_level=risk_level,
                )
            )

        return suggestions


class RiskAlerter:
    """风险预警器"""

    def check(
        self,
        holdings: list[dict[str, Any]],
        profile: UserProfile,
        market_data: dict[str, Any] | None = None,
    ) -> list[str]:
        """
        检查风险并生成预警

        Args:
            holdings: 持仓
            profile: 用户画像
            market_data: 市场数据

        Returns:
            风险预警列表
        """
        warnings = []

        # 检查集中度风险
        if holdings:
            total_value = sum(h.get("value", h.get("market_value", 0)) for h in holdings)
            if total_value > 0:
                max_weight = max(
                    h.get("value", h.get("market_value", 0)) / total_value for h in holdings
                )
                if max_weight > 0.5:
                    warnings.append("⚠️ 单一持仓占比过高，存在集中度风险")

        # 检查风险偏好匹配
        stock_ratio = 0
        for h in holdings:
            if "股票" in h.get("fund_type", ""):
                stock_ratio += h.get("value", h.get("market_value", 0))

        if holdings and total_value > 0:
            stock_ratio /= total_value
            if profile.risk_assessment.tolerance == RiskTolerance.CONSERVATIVE and stock_ratio > 0.3:
                warnings.append("⚠️ 股票型基金配置比例超过保守型投资者建议")

        # 检查市场风险
        if market_data:
            sentiment = market_data.get("sentiment", "中性")
            if sentiment == "极度贪婪":
                warnings.append("⚠️ 市场情绪过热，注意回调风险")
            elif sentiment == "极度恐慌":
                warnings.append("⚠️ 市场情绪恐慌，注意控制仓位")

        if not warnings:
            warnings.append("✓ 当前持仓风险水平正常")

        return warnings


class InvestmentAdvisor:
    """
    投资建议生成器主类

    整合持仓分析、调仓建议、定投建议、风险预警等功能。
    """

    def __init__(self, data_manager: DataManager | None = None):
        self._dm = data_manager or DataManager()
        self._holding_analyzer = HoldingAnalyzer()
        self._rebalance_advisor = RebalanceAdvisor()
        self._dca_advisor = DCAAdvisor()
        self._risk_alerter = RiskAlerter()

    def advise(
        self,
        profile: UserProfile,
        holdings: list[dict[str, Any]] | None = None,
        market_data: dict[str, Any] | None = None,
    ) -> InvestmentAdviceReport:
        """
        生成投资建议

        Args:
            profile: 用户画像
            holdings: 当前持仓
            market_data: 市场数据

        Returns:
            投资建议报告
        """
        from datetime import datetime

        if holdings is None:
            holdings = []

        # 持仓分析
        holding_advices = self._holding_analyzer.analyze(holdings, profile)

        # 调仓建议
        rebalance_suggestions = self._rebalance_advisor.suggest(holdings, profile)

        # 定投建议
        dca_suggestions = self._dca_advisor.suggest(profile)

        # 风险预警
        risk_warnings = self._risk_alerter.check(holdings, profile, market_data)

        # 综合建议
        overall_advice = self._generate_overall_advice(
            profile, holdings, holding_advices, rebalance_suggestions
        )

        return InvestmentAdviceReport(
            user_id=profile.user_id,
            report_date=datetime.now().strftime("%Y-%m-%d"),
            advices=holding_advices,
            rebalance_suggestions=rebalance_suggestions,
            dca_suggestions=dca_suggestions,
            overall_advice=overall_advice,
            risk_warnings=risk_warnings,
        )

    def _generate_overall_advice(
        self,
        profile: UserProfile,
        holdings: list[dict],
        advices: list[AdviceItem],
        rebalance: list[RebalanceSuggestion],
    ) -> str:
        """生成综合建议"""
        parts = []

        # 基于投资目标
        parts.append(f"根据您的{profile.investment_goal.value}目标")

        # 基于持仓情况
        if not holdings:
            parts.append("建议先建立基础投资组合")
        elif rebalance:
            parts.append(f"建议进行{len(rebalance)}项调仓优化")
        else:
            parts.append("当前组合结构合理，建议继续持有")

        # 基于风险偏好
        if profile.risk_assessment.tolerance == RiskTolerance.CONSERVATIVE:
            parts.append("保持稳健配置，关注债券类资产")
        elif profile.risk_assessment.tolerance == RiskTolerance.AGGRESSIVE:
            parts.append("可适当把握市场机会，但注意风险控制")

        return "；".join(parts)

    def format_report(self, report: InvestmentAdviceReport) -> str:
        """格式化建议报告"""
        lines = ["# 投资建议报告\n"]

        lines.append(f"用户ID: {report.user_id}")
        lines.append(f"报告日期: {report.report_date}\n")

        # 综合建议
        lines.append("## 综合建议")
        lines.append(report.overall_advice)
        lines.append("")

        # 具体建议
        if report.advices:
            lines.append("## 具体建议")
            for i, advice in enumerate(report.advices, 1):
                lines.append(f"### {i}. {advice.title}")
                lines.append(f"- 类型: {advice.advice_type.value}")
                lines.append(f"- 优先级: {advice.priority.value}")
                lines.append(f"- 说明: {advice.description}")
                lines.append(f"- 操作: {advice.action}")
                lines.append(f"- 预期影响: {advice.expected_impact}")
                lines.append(f"- 风险提示: {advice.risk_warning}")
                lines.append("")

        # 调仓建议
        if report.rebalance_suggestions:
            lines.append("## 调仓建议")
            lines.append("| 基金 | 当前权重 | 建议权重 | 调整 | 原因 |")
            lines.append("|------|----------|----------|------|------|")
            for s in report.rebalance_suggestions:
                change = f"+{s.weight_change:.1f}%" if s.weight_change > 0 else f"{s.weight_change:.1f}%"
                lines.append(f"| {s.fund_name} | {s.current_weight:.1f}% | {s.suggested_weight:.1f}% | {change} | {s.reason} |")
            lines.append("")

        # 定投建议
        if report.dca_suggestions:
            lines.append("## 定投建议")
            for s in report.dca_suggestions:
                lines.append(f"- {s.fund_name}({s.fund_code}): 每月{s.suggested_amount:.0f}元, 预期收益{s.expected_return:.1f}%, 风险{s.risk_level}")
            lines.append("")

        # 风险提示
        lines.append("## 风险提示")
        for w in report.risk_warnings:
            lines.append(f"- {w}")

        return "\n".join(lines)


def generate_investment_advice(
    profile: UserProfile,
    holdings: list[dict[str, Any]] | None = None,
    data_manager: DataManager | None = None,
) -> InvestmentAdviceReport:
    """投资建议便捷函数"""
    advisor = InvestmentAdvisor(data_manager)
    return advisor.advise(profile, holdings)
