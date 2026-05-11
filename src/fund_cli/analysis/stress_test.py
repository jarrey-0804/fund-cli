"""
压力测试模块

帮助用户了解基金/组合在极端市场情况下的表现。
支持历史情景回溯和自定义压力测试。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

from fund_cli.core.data_manager import DataManager

logger = logging.getLogger(__name__)


class StressScenario(str, Enum):
    """预设压力情景"""

    CRISIS_2008 = "2008金融危机"
    CRASH_2015 = "2015股灾"
    PANDEMIC_2020 = "2020疫情"
    RATE_HIKE = "加息周期"
    BEAR_MARKET = "熊市情景"
    FLASH_CRASH = "闪崩情景"
    CUSTOM = "自定义"


@dataclass
class HistoricalScenario:
    """历史情景定义"""

    name: str
    start_date: str
    end_date: str
    description: str
    market_shock: float  # 市场整体跌幅 (%)
    affected_sectors: list[str]  # 受影响行业
    recovery_days: int  # 恢复天数


# 历史情景数据库
HISTORICAL_SCENARIOS: dict[StressScenario, HistoricalScenario] = {
    StressScenario.CRISIS_2008: HistoricalScenario(
        name="2008全球金融危机",
        start_date="2008-09-01",
        end_date="2008-11-30",
        description="雷曼兄弟破产引发的全球金融危机，股市暴跌",
        market_shock=-45.0,
        affected_sectors=["金融", "房地产", "工业", "材料"],
        recovery_days=720,
    ),
    StressScenario.CRASH_2015: HistoricalScenario(
        name="2015年中国股灾",
        start_date="2015-06-15",
        end_date="2015-08-26",
        description="杠杆资金平仓引发的股市暴跌",
        market_shock=-35.0,
        affected_sectors=["证券", "科技", "创业板"],
        recovery_days=365,
    ),
    StressScenario.PANDEMIC_2020: HistoricalScenario(
        name="2020年新冠疫情",
        start_date="2020-02-20",
        end_date="2020-03-23",
        description="新冠疫情全球爆发引发的恐慌性抛售",
        market_shock=-30.0,
        affected_sectors=["航空", "旅游", "餐饮", "娱乐"],
        recovery_days=180,
    ),
    StressScenario.RATE_HIKE: HistoricalScenario(
        name="加息周期压力",
        start_date="2022-01-01",
        end_date="2022-12-31",
        description="美联储激进加息导致的资产价格下跌",
        market_shock=-20.0,
        affected_sectors=["债券", "成长股", "科技"],
        recovery_days=365,
    ),
    StressScenario.BEAR_MARKET: HistoricalScenario(
        name="熊市情景",
        start_date="2018-01-01",
        end_date="2018-12-31",
        description="贸易摩擦引发的全年熊市",
        market_shock=-25.0,
        affected_sectors=["全市场"],
        recovery_days=300,
    ),
    StressScenario.FLASH_CRASH: HistoricalScenario(
        name="闪崩情景",
        start_date="2015-01-01",
        end_date="2015-01-05",
        description="短期内的剧烈下跌",
        market_shock=-15.0,
        affected_sectors=["全市场"],
        recovery_days=30,
    ),
}


@dataclass
class StressTestResult:
    """压力测试结果"""

    scenario_name: str
    scenario_type: StressScenario
    # 组合表现
    portfolio_loss: float  # 组合损失 (%)
    portfolio_recovery_days: int  # 预计恢复天数
    # 风险指标
    var_breach: bool  # 是否突破VaR
    max_drawdown: float  # 压力情景下最大回撤
    # 敏感性分析
    sensitivity: dict[str, float] = field(default_factory=dict)  # 各因子敏感性
    # 建议
    risk_warning: str = ""
    hedging_suggestion: str = ""
    # 详细数据
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class StressTestReport:
    """压力测试报告"""

    fund_code: str
    fund_name: str
    test_date: str
    # 各情景测试结果
    results: list[StressTestResult]
    # 综合评估
    worst_case: StressTestResult
    average_loss: float
    risk_rating: str  # 低/中/高/极高
    # 建议
    overall_suggestion: str


class HistoricalScenarioEngine:
    """历史情景引擎"""

    def run(
        self,
        scenario: StressScenario,
        nav_series: pd.Series | None = None,
        beta: float = 1.0,
    ) -> StressTestResult:
        """
        运行历史情景压力测试

        Args:
            scenario: 压力情景
            nav_series: 净值序列（用于计算实际历史表现）
            beta: 基金Beta值（用于估算损失）

        Returns:
            压力测试结果
        """
        if scenario == StressScenario.CUSTOM:
            raise ValueError("自定义情景请使用 CustomScenarioEngine")

        scenario_def = HISTORICAL_SCENARIOS[scenario]

        # 计算预估损失
        # 基于Beta调整的市场冲击
        estimated_loss = scenario_def.market_shock * beta

        # 预估恢复天数
        recovery_days = int(scenario_def.recovery_days * abs(beta))

        # 判断是否突破VaR（假设VaR为-20%）
        var_breach = estimated_loss < -20

        # 计算敏感性
        sensitivity = {
            "市场敏感度": round(beta, 2),
            "行业暴露": len(scenario_def.affected_sectors),
        }

        # 生成风险提示
        risk_warning = self._generate_risk_warning(estimated_loss, scenario_def)
        hedging_suggestion = self._generate_hedging_suggestion(estimated_loss, beta)

        return StressTestResult(
            scenario_name=scenario_def.name,
            scenario_type=scenario,
            portfolio_loss=round(estimated_loss, 2),
            portfolio_recovery_days=recovery_days,
            var_breach=var_breach,
            max_drawdown=round(estimated_loss, 2),
            sensitivity=sensitivity,
            risk_warning=risk_warning,
            hedging_suggestion=hedging_suggestion,
            details={
                "market_shock": scenario_def.market_shock,
                "affected_sectors": scenario_def.affected_sectors,
                "historical_period": f"{scenario_def.start_date} ~ {scenario_def.end_date}",
            },
        )

    def _generate_risk_warning(self, loss: float, scenario: HistoricalScenario) -> str:
        """生成风险提示"""
        if loss < -40:
            return f"⚠️ 极高风险：在{scenario.name}情景下预估损失{abs(loss):.1f}%，建议立即调整仓位"
        elif loss < -25:
            return f"⚠️ 高风险：在{scenario.name}情景下预估损失{abs(loss):.1f}%，需要关注风险敞口"
        elif loss < -15:
            return f"中等风险：在{scenario.name}情景下预估损失{abs(loss):.1f}%，属于正常波动范围"
        else:
            return f"低风险：在{scenario.name}情景下预估损失{abs(loss):.1f}%，抗风险能力较强"

    def _generate_hedging_suggestion(self, loss: float, beta: float) -> str:
        """生成对冲建议"""
        suggestions = []

        if beta > 1.2:
            suggestions.append("Beta较高，可考虑降低仓位或使用股指期货对冲")

        if loss < -30:
            suggestions.append("建议配置防御性资产如债券、黄金等")

        if loss < -20:
            suggestions.append("可考虑购买看跌期权作为保险")

        if not suggestions:
            suggestions.append("当前风险水平可接受，维持现有配置")

        return "；".join(suggestions)


class CustomScenarioEngine:
    """自定义情景引擎"""

    def run(
        self,
        shock_percent: float,
        nav_series: pd.Series | None = None,
        beta: float = 1.0,
        shock_type: str = "market",
    ) -> StressTestResult:
        """
        运行自定义压力测试

        Args:
            shock_percent: 冲击幅度 (%)
            nav_series: 净值序列
            beta: 基金Beta值
            shock_type: 冲击类型 (market/sector/rate)

        Returns:
            压力测试结果
        """
        # 计算预估损失
        estimated_loss = shock_percent * beta

        # 根据冲击类型调整恢复时间
        recovery_multiplier = {
            "market": 1.0,
            "sector": 0.5,  # 行业冲击恢复较快
            "rate": 1.5,  # 利率冲击恢复较慢
        }.get(shock_type, 1.0)

        base_recovery = abs(shock_percent) * 3  # 基础恢复天数
        recovery_days = int(base_recovery * recovery_multiplier)

        # VaR突破判断
        var_breach = estimated_loss < -20

        # 敏感性分析
        sensitivity = {
            "冲击类型": shock_type,
            "冲击幅度": f"{shock_percent}%",
            "Beta": round(beta, 2),
        }

        # 生成提示
        if estimated_loss < -30:
            risk_warning = f"自定义压力测试：冲击{shock_percent}%下预估损失{abs(estimated_loss):.1f}%，风险较高"
            hedging_suggestion = "建议进行风险对冲或调整仓位"
        else:
            risk_warning = f"自定义压力测试：冲击{shock_percent}%下预估损失{abs(estimated_loss):.1f}%"
            hedging_suggestion = "风险可控"

        return StressTestResult(
            scenario_name=f"自定义{shock_type}冲击{shock_percent}%",
            scenario_type=StressScenario.CUSTOM,
            portfolio_loss=round(estimated_loss, 2),
            portfolio_recovery_days=recovery_days,
            var_breach=var_breach,
            max_drawdown=round(estimated_loss, 2),
            sensitivity=sensitivity,
            risk_warning=risk_warning,
            hedging_suggestion=hedging_suggestion,
            details={
                "shock_percent": shock_percent,
                "shock_type": shock_type,
                "beta": beta,
            },
        )


class SensitivityAnalyzer:
    """敏感性分析器"""

    def analyze(
        self,
        nav_series: pd.Series,
        factors: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """
        分析基金对各因子的敏感性

        Args:
            nav_series: 净值序列
            factors: 因子冲击幅度字典

        Returns:
            各因子敏感性
        """
        if factors is None:
            factors = {
                "市场因子": -20.0,
                "利率因子": 1.0,  # 利率上升1%
                "信用利差": 2.0,  # 信用利差扩大2%
                "汇率因子": -5.0,  # 汇率贬值5%
            }

        # 计算净值波动率
        nav_returns = nav_series.pct_change().dropna()
        volatility = nav_returns.std() * np.sqrt(252) * 100

        # 基于波动率估算敏感性
        sensitivity = {}
        for factor, shock in factors.items():
            # 简化模型：敏感性 = 波动率 * 冲击幅度 / 20
            sens = volatility * abs(shock) / 20
            sensitivity[factor] = round(sens, 2)

        return sensitivity


class StressTester:
    """
    压力测试主类

    整合历史情景、自定义情景、敏感性分析等功能。
    """

    def __init__(self, data_manager: DataManager | None = None):
        """
        初始化压力测试器

        Args:
            data_manager: 数据管理器实例
        """
        self._dm = data_manager or DataManager()
        self._historical_engine = HistoricalScenarioEngine()
        self._custom_engine = CustomScenarioEngine()
        self._sensitivity_analyzer = SensitivityAnalyzer()

    def run_single(
        self,
        scenario: StressScenario,
        beta: float = 1.0,
        custom_shock: float | None = None,
    ) -> StressTestResult:
        """
        运行单一情景压力测试

        Args:
            scenario: 压力情景
            beta: 基金Beta值
            custom_shock: 自定义冲击幅度（仅用于CUSTOM情景）

        Returns:
            压力测试结果
        """
        if scenario == StressScenario.CUSTOM:
            if custom_shock is None:
                custom_shock = -30.0
            return self._custom_engine.run(custom_shock, beta=beta)
        else:
            return self._historical_engine.run(scenario, beta=beta)

    def run_all(
        self,
        beta: float = 1.0,
        scenarios: list[StressScenario] | None = None,
    ) -> list[StressTestResult]:
        """
        运行所有预设情景压力测试

        Args:
            beta: 基金Beta值
            scenarios: 要测试的情景列表（默认测试所有历史情景）

        Returns:
            所有情景测试结果
        """
        if scenarios is None:
            scenarios = [
                StressScenario.CRISIS_2008,
                StressScenario.CRASH_2015,
                StressScenario.PANDEMIC_2020,
                StressScenario.RATE_HIKE,
                StressScenario.BEAR_MARKET,
            ]

        results = []
        for scenario in scenarios:
            result = self.run_single(scenario, beta)
            results.append(result)

        return results

    def generate_report(
        self,
        fund_code: str,
        fund_name: str,
        beta: float = 1.0,
        custom_shock: float | None = None,
    ) -> StressTestReport:
        """
        生成完整压力测试报告

        Args:
            fund_code: 基金代码
            fund_name: 基金名称
            beta: 基金Beta值
            custom_shock: 自定义冲击幅度

        Returns:
            压力测试报告
        """
        from datetime import datetime

        # 运行所有情景
        results = self.run_all(beta)

        # 添加自定义情景
        if custom_shock is not None:
            custom_result = self.run_single(
                StressScenario.CUSTOM, beta, custom_shock
            )
            results.append(custom_result)

        # 找出最差情景
        worst_case = min(results, key=lambda x: x.portfolio_loss)

        # 计算平均损失
        average_loss = np.mean([r.portfolio_loss for r in results])

        # 风险评级
        if average_loss < -30:
            risk_rating = "极高"
        elif average_loss < -20:
            risk_rating = "高"
        elif average_loss < -10:
            risk_rating = "中"
        else:
            risk_rating = "低"

        # 综合建议
        overall_suggestion = self._generate_overall_suggestion(
            worst_case, average_loss, risk_rating
        )

        return StressTestReport(
            fund_code=fund_code,
            fund_name=fund_name,
            test_date=datetime.now().strftime("%Y-%m-%d"),
            results=results,
            worst_case=worst_case,
            average_loss=round(average_loss, 2),
            risk_rating=risk_rating,
            overall_suggestion=overall_suggestion,
        )

    def _generate_overall_suggestion(
        self,
        worst_case: StressTestResult,
        average_loss: float,
        risk_rating: str,
    ) -> str:
        """生成综合建议"""
        lines = []

        lines.append(f"压力测试综合评估：风险等级【{risk_rating}】")
        lines.append(f"最差情景【{worst_case.scenario_name}】下预估损失{abs(worst_case.portfolio_loss):.1f}%")
        lines.append(f"各情景平均损失{abs(average_loss):.1f}%")

        if risk_rating == "极高":
            lines.append("建议：立即评估风险敞口，考虑大幅降低仓位或进行对冲")
        elif risk_rating == "高":
            lines.append("建议：关注风险敞口，适度降低仓位或配置防御性资产")
        elif risk_rating == "中":
            lines.append("建议：维持正常风险管理，定期监控市场变化")
        else:
            lines.append("建议：风险水平较低，可维持现有配置")

        return "\n".join(lines)

    def format_report(self, report: StressTestReport) -> str:
        """
        格式化压力测试报告

        Args:
            report: 压力测试报告

        Returns:
            格式化的报告文本
        """
        lines = ["# 压力测试报告\n"]

        lines.append("## 基本信息")
        lines.append(f"- 基金代码: {report.fund_code}")
        lines.append(f"- 基金名称: {report.fund_name}")
        lines.append(f"- 测试日期: {report.test_date}")
        lines.append("")

        lines.append("## 综合评估")
        lines.append(f"- 风险等级: {report.risk_rating}")
        lines.append(f"- 平均损失: {abs(report.average_loss):.2f}%")
        lines.append(f"- 最差情景: {report.worst_case.scenario_name}")
        lines.append("")

        lines.append("## 各情景测试结果")
        for result in report.results:
            lines.append(f"### {result.scenario_name}")
            lines.append(f"- 预估损失: {abs(result.portfolio_loss):.2f}%")
            lines.append(f"- 恢复天数: {result.portfolio_recovery_days}天")
            lines.append(f"- VaR突破: {'是' if result.var_breach else '否'}")
            lines.append(f"- 风险提示: {result.risk_warning}")
            lines.append(f"- 对冲建议: {result.hedging_suggestion}")
            lines.append("")

        lines.append("## 综合建议")
        lines.append(report.overall_suggestion)

        return "\n".join(lines)


def run_stress_test(
    fund_code: str,
    scenario: str | StressScenario = "all",
    beta: float = 1.0,
    custom_shock: float | None = None,
    data_manager: DataManager | None = None,
) -> StressTestReport | StressTestResult:
    """
    压力测试便捷函数

    Args:
        fund_code: 基金代码
        scenario: 情景名称或"all"
        beta: 基金Beta值
        custom_shock: 自定义冲击幅度
        data_manager: 数据管理器实例

    Returns:
        压力测试结果或报告
    """
    tester = StressTester(data_manager)

    if scenario == "all":
        return tester.generate_report(fund_code, fund_code, beta, custom_shock)
    else:
        if isinstance(scenario, str):
            scenario = StressScenario(scenario)
        return tester.run_single(scenario, beta, custom_shock)
