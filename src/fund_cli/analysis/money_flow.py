"""
资金流向分析模块

帮助用户追踪市场资金动向，发现投资信号。
支持基金申赎数据、板块资金流向、北向资金追踪等功能。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

from fund_cli.core.data_manager import DataManager

logger = logging.getLogger(__name__)


class FlowDirection(str, Enum):
    """资金流向方向"""

    INFLOW = "流入"
    OUTFLOW = "流出"
    NEUTRAL = "持平"


class FlowIntensity(str, Enum):
    """资金流向强度"""

    STRONG = "强"
    MODERATE = "中"
    WEAK = "弱"


@dataclass
class FundFlowItem:
    """基金申赎数据项"""

    fund_code: str
    fund_name: str
    net_purchase: float  # 净申购（亿份）
    total_purchase: float  # 总申购（亿份）
    total_redeem: float  # 总赎回（亿份）
    purchase_ratio: float  # 申赎比
    direction: FlowDirection
    intensity: FlowIntensity
    trend: str  # 上升/下降/持平


@dataclass
class SectorFlowItem:
    """板块资金流向项"""

    sector_name: str
    net_inflow: float  # 净流入（亿元）
    main_inflow: float  # 主力流入（亿元）
    retail_inflow: float  # 散户流入（亿元）
    direction: FlowDirection
    intensity: FlowIntensity
    consecutive_days: int  # 连续流入/流出天数
    rank: int


@dataclass
class NorthboundFlowItem:
    """北向资金数据项"""

    date: str
    net_buy: float  # 净买入（亿元）
    total_buy: float  # 总买入（亿元）
    total_sell: float  # 总卖出（亿元）
    holding_change: float  # 持仓变动（亿元）
    direction: FlowDirection


@dataclass
class FundFlowReport:
    """基金申赎报告"""

    report_date: str
    items: list[FundFlowItem]
    top_inflow: list[FundFlowItem]
    top_outflow: list[FundFlowItem]
    summary: str
    investment_signals: list[str]


@dataclass
class SectorFlowReport:
    """板块资金流向报告"""

    report_date: str
    items: list[SectorFlowItem]
    strong_inflow: list[SectorFlowItem]
    strong_outflow: list[SectorFlowItem]
    rotation_signals: list[str]
    investment_advice: str


@dataclass
class NorthboundFlowReport:
    """北向资金报告"""

    period: str
    items: list[NorthboundFlowItem]
    total_net_buy: float
    trend: str  # 持续流入/持续流出/波动
    historical_percentile: float  # 历史分位数
    investment_signals: list[str]


class FundFlowAnalyzer:
    """基金申赎分析器"""

    def analyze(
        self,
        fund_flow_data: list[dict[str, Any]] | None = None,
        top_n: int = 10,
    ) -> FundFlowReport:
        """
        分析基金申赎数据

        Args:
            fund_flow_data: 基金申赎数据
            top_n: 返回数量

        Returns:
            基金申赎报告
        """
        from datetime import datetime

        if fund_flow_data is None:
            fund_flow_data = self._generate_mock_fund_flow()

        items = []
        for data in fund_flow_data[:top_n * 2]:
            net = data.get("net_purchase", 0)
            total_p = data.get("total_purchase", 0)
            total_r = data.get("total_redeem", 0)

            # 判断方向
            if net > 1:
                direction = FlowDirection.INFLOW
            elif net < -1:
                direction = FlowDirection.OUTFLOW
            else:
                direction = FlowDirection.NEUTRAL

            # 判断强度
            if abs(net) > 10:
                intensity = FlowIntensity.STRONG
            elif abs(net) > 3:
                intensity = FlowIntensity.MODERATE
            else:
                intensity = FlowIntensity.WEAK

            # 申赎比
            ratio = total_p / total_r if total_r > 0 else 1.0

            # 趋势
            trend_data = data.get("trend", 0)
            if trend_data > 0.05:
                trend = "上升"
            elif trend_data < -0.05:
                trend = "下降"
            else:
                trend = "持平"

            items.append(
                FundFlowItem(
                    fund_code=data.get("code", ""),
                    fund_name=data.get("name", ""),
                    net_purchase=round(net, 2),
                    total_purchase=round(total_p, 2),
                    total_redeem=round(total_r, 2),
                    purchase_ratio=round(ratio, 4),
                    direction=direction,
                    intensity=intensity,
                    trend=trend,
                )
            )

        # 按净申购排序
        items.sort(key=lambda x: x.net_purchase, reverse=True)
        top_inflow = [i for i in items if i.direction == FlowDirection.INFLOW][:top_n]
        top_outflow = [i for i in items if i.direction == FlowDirection.OUTFLOW][:top_n]

        # 生成摘要
        total_net = sum(i.net_purchase for i in items)
        inflow_count = sum(1 for i in items if i.direction == FlowDirection.INFLOW)
        outflow_count = sum(1 for i in items if i.direction == FlowDirection.OUTFLOW)

        summary = (
            f"共分析{len(items)}只基金，净申购{total_net:.2f}亿份，"
            f"其中{inflow_count}只净流入，{outflow_count}只净流出"
        )

        # 生成投资信号
        signals = self._generate_fund_flow_signals(items, top_inflow, top_outflow)

        return FundFlowReport(
            report_date=datetime.now().strftime("%Y-%m-%d"),
            items=items[:top_n],
            top_inflow=top_inflow,
            top_outflow=top_outflow,
            summary=summary,
            investment_signals=signals,
        )

    def _generate_fund_flow_signals(
        self,
        items: list[FundFlowItem],
        top_inflow: list[FundFlowItem],
        top_outflow: list[FundFlowItem],
    ) -> list[str]:
        """生成基金申赎投资信号"""
        signals = []

        if top_inflow:
            top = top_inflow[0]
            signals.append(f"基金{top.fund_name}净申购{top.net_purchase:.2f}亿份，资金关注度高")

        if top_outflow:
            top = top_outflow[0]
            signals.append(f"基金{top.fund_name}净赎回{abs(top.net_purchase):.2f}亿份，需关注赎回压力")

        # 整体趋势
        inflow_items = [i for i in items if i.direction == FlowDirection.INFLOW and i.trend == "上升"]
        if len(inflow_items) > len(items) * 0.5:
            signals.append("多数基金申赎趋势向上，市场情绪偏乐观")

        return signals

    def _generate_mock_fund_flow(self) -> list[dict[str, Any]]:
        """生成模拟基金申赎数据"""
        np.random.seed(42)
        funds = [
            ("000001", "华夏成长", 15.0),
            ("000002", "易方达策略", -8.0),
            ("000003", "南方稳健", 12.0),
            ("000005", "嘉实增长", -3.0),
            ("000011", "华夏大盘", 20.0),
            ("000015", "易方达价值", -12.0),
            ("000020", "南方积极", 5.0),
            ("000025", "嘉实服务", -6.0),
        ]
        return [
            {
                "code": code,
                "name": name,
                "net_purchase": net + np.random.uniform(-2, 2),
                "total_purchase": abs(net) * 1.5 + np.random.uniform(0, 5),
                "total_redeem": abs(net) * 0.8 + np.random.uniform(0, 5),
                "trend": np.random.uniform(-0.1, 0.1),
            }
            for code, name, net in funds
        ]


class SectorFlowAnalyzer:
    """板块资金流向分析器"""

    def analyze(
        self,
        sector_flow_data: list[dict[str, Any]] | None = None,
        top_n: int = 10,
    ) -> SectorFlowReport:
        """
        分析板块资金流向

        Args:
            sector_flow_data: 板块资金数据
            top_n: 返回数量

        Returns:
            板块资金流向报告
        """
        from datetime import datetime

        if sector_flow_data is None:
            sector_flow_data = self._generate_mock_sector_flow()

        items = []
        for data in sector_flow_data:
            net = data.get("net_inflow", 0)

            if net > 5:
                direction = FlowDirection.INFLOW
            elif net < -5:
                direction = FlowDirection.OUTFLOW
            else:
                direction = FlowDirection.NEUTRAL

            if abs(net) > 20:
                intensity = FlowIntensity.STRONG
            elif abs(net) > 10:
                intensity = FlowIntensity.MODERATE
            else:
                intensity = FlowIntensity.WEAK

            items.append(
                SectorFlowItem(
                    sector_name=data.get("sector", ""),
                    net_inflow=round(net, 2),
                    main_inflow=round(data.get("main_inflow", net * 0.6), 2),
                    retail_inflow=round(data.get("retail_inflow", net * 0.4), 2),
                    direction=direction,
                    intensity=intensity,
                    consecutive_days=data.get("consecutive_days", 1),
                    rank=0,
                )
            )

        # 按净流入排序
        items.sort(key=lambda x: x.net_inflow, reverse=True)
        for i, item in enumerate(items):
            item.rank = i + 1

        strong_inflow = [i for i in items if i.direction == FlowDirection.INFLOW][:top_n]
        strong_outflow = [i for i in items if i.direction == FlowDirection.OUTFLOW][:top_n]

        # 轮动信号
        rotation_signals = self._generate_rotation_signals(strong_inflow, strong_outflow)

        # 投资建议
        investment_advice = self._generate_investment_advice(strong_inflow, strong_outflow)

        return SectorFlowReport(
            report_date=datetime.now().strftime("%Y-%m-%d"),
            items=items[:top_n],
            strong_inflow=strong_inflow,
            strong_outflow=strong_outflow,
            rotation_signals=rotation_signals,
            investment_advice=investment_advice,
        )

    def _generate_rotation_signals(
        self,
        inflow: list[SectorFlowItem],
        outflow: list[SectorFlowItem],
    ) -> list[str]:
        """生成轮动信号"""
        signals = []

        if inflow:
            names = "、".join([s.sector_name for s in inflow[:3]])
            signals.append(f"资金流入板块：{names}")

        if outflow:
            names = "、".join([s.sector_name for s in outflow[:3]])
            signals.append(f"资金流出板块：{names}")

        # 连续流入信号
        for item in inflow:
            if item.consecutive_days >= 3:
                signals.append(f"{item.sector_name}连续{item.consecutive_days}天资金流入，趋势强劲")
                break

        return signals

    def _generate_investment_advice(
        self,
        inflow: list[SectorFlowItem],
        outflow: list[SectorFlowItem],
    ) -> str:
        """生成投资建议"""
        if not inflow and not outflow:
            return "资金流向平稳，建议维持现有配置。"

        advice_parts = []

        if inflow:
            top = inflow[0]
            advice_parts.append(f"可关注{top.sector_name}板块的资金流入机会")

        if outflow:
            top = outflow[0]
            advice_parts.append(f"建议规避{top.sector_name}板块的资金流出风险")

        return "；".join(advice_parts)

    def _generate_mock_sector_flow(self) -> list[dict[str, Any]]:
        """生成模拟板块资金数据"""
        return [
            {"sector": "电力设备", "net_inflow": 35.0, "main_inflow": 25.0, "retail_inflow": 10.0, "consecutive_days": 5},
            {"sector": "电子", "net_inflow": 28.0, "main_inflow": 18.0, "retail_inflow": 10.0, "consecutive_days": 3},
            {"sector": "计算机", "net_inflow": 22.0, "main_inflow": 15.0, "retail_inflow": 7.0, "consecutive_days": 2},
            {"sector": "医药生物", "net_inflow": 15.0, "main_inflow": 8.0, "retail_inflow": 7.0, "consecutive_days": 1},
            {"sector": "食品饮料", "net_inflow": 8.0, "main_inflow": 3.0, "retail_inflow": 5.0, "consecutive_days": 1},
            {"sector": "银行", "net_inflow": -5.0, "main_inflow": -8.0, "retail_inflow": 3.0, "consecutive_days": 1},
            {"sector": "房地产", "net_inflow": -18.0, "main_inflow": -15.0, "retail_inflow": -3.0, "consecutive_days": 4},
            {"sector": "建筑材料", "net_inflow": -12.0, "main_inflow": -10.0, "retail_inflow": -2.0, "consecutive_days": 2},
            {"sector": "钢铁", "net_inflow": -8.0, "main_inflow": -6.0, "retail_inflow": -2.0, "consecutive_days": 1},
            {"sector": "非银金融", "net_inflow": -15.0, "main_inflow": -12.0, "retail_inflow": -3.0, "consecutive_days": 3},
        ]


class NorthboundFlowAnalyzer:
    """北向资金分析器"""

    def analyze(
        self,
        northbound_data: list[dict[str, Any]] | None = None,
        period: str = "近30日",
    ) -> NorthboundFlowReport:
        """
        分析北向资金数据

        Args:
            northbound_data: 北向资金数据
            period: 分析周期

        Returns:
            北向资金报告
        """
        if northbound_data is None:
            northbound_data = self._generate_mock_northbound()

        items = []
        for data in northbound_data:
            net = data.get("net_buy", 0)

            if net > 1:
                direction = FlowDirection.INFLOW
            elif net < -1:
                direction = FlowDirection.OUTFLOW
            else:
                direction = FlowDirection.NEUTRAL

            items.append(
                NorthboundFlowItem(
                    date=data.get("date", ""),
                    net_buy=round(net, 2),
                    total_buy=round(data.get("total_buy", abs(net) * 1.2), 2),
                    total_sell=round(data.get("total_sell", abs(net) * 0.8), 2),
                    holding_change=round(data.get("holding_change", net * 0.5), 2),
                    direction=direction,
                )
            )

        # 计算汇总
        total_net = sum(i.net_buy for i in items)
        inflow_days = sum(1 for i in items if i.direction == FlowDirection.INFLOW)
        outflow_days = sum(1 for i in items if i.direction == FlowDirection.OUTFLOW)

        # 趋势判断
        if inflow_days > len(items) * 0.6:
            trend = "持续流入"
        elif outflow_days > len(items) * 0.6:
            trend = "持续流出"
        else:
            trend = "波动"

        # 历史分位数（模拟）
        historical_percentile = 65.0 if total_net > 0 else 35.0

        # 投资信号
        signals = self._generate_northbound_signals(total_net, trend, inflow_days, outflow_days)

        return NorthboundFlowReport(
            period=period,
            items=items,
            total_net_buy=round(total_net, 2),
            trend=trend,
            historical_percentile=historical_percentile,
            investment_signals=signals,
        )

    def _generate_northbound_signals(
        self,
        total_net: float,
        trend: str,
        inflow_days: int,
        outflow_days: int,
    ) -> list[str]:
        """生成北向资金投资信号"""
        signals = []

        if total_net > 100:
            signals.append(f"北向资金大幅净流入{total_net:.1f}亿元，外资看好A股")
        elif total_net > 30:
            signals.append(f"北向资金净流入{total_net:.1f}亿元，外资态度偏积极")
        elif total_net < -100:
            signals.append(f"北向资金大幅净流出{abs(total_net):.1f}亿元，需警惕外资撤离")
        elif total_net < -30:
            signals.append(f"北向资金净流出{abs(total_net):.1f}亿元，外资态度谨慎")

        if trend == "持续流入" and inflow_days >= 5:
            signals.append(f"连续{inflow_days}天净流入，外资持续加仓信号明显")

        if trend == "持续流出" and outflow_days >= 5:
            signals.append(f"连续{outflow_days}天净流出，外资持续减仓需关注")

        return signals

    def _generate_mock_northbound(self) -> list[dict[str, Any]]:
        """生成模拟北向资金数据"""
        np.random.seed(42)
        dates = pd.date_range(end=pd.Timestamp.now(), periods=30, freq="B")
        return [
            {
                "date": d.strftime("%Y-%m-%d"),
                "net_buy": np.random.uniform(-50, 80),
                "total_buy": np.random.uniform(50, 150),
                "total_sell": np.random.uniform(40, 120),
                "holding_change": np.random.uniform(-30, 50),
            }
            for d in dates
        ]


class MoneyFlowAnalyzer:
    """
    资金流向分析主类

    整合基金申赎、板块资金流向、北向资金分析等功能。
    """

    def __init__(self, data_manager: DataManager | None = None):
        self._dm = data_manager or DataManager()
        self._fund_flow_analyzer = FundFlowAnalyzer()
        self._sector_flow_analyzer = SectorFlowAnalyzer()
        self._northbound_analyzer = NorthboundFlowAnalyzer()

    def analyze_fund_flow(
        self,
        fund_flow_data: list[dict[str, Any]] | None = None,
        top_n: int = 10,
    ) -> FundFlowReport:
        """分析基金申赎数据"""
        return self._fund_flow_analyzer.analyze(fund_flow_data, top_n)

    def analyze_sector_flow(
        self,
        sector_flow_data: list[dict[str, Any]] | None = None,
        top_n: int = 10,
    ) -> SectorFlowReport:
        """分析板块资金流向"""
        return self._sector_flow_analyzer.analyze(sector_flow_data, top_n)

    def analyze_northbound(
        self,
        northbound_data: list[dict[str, Any]] | None = None,
        period: str = "近30日",
    ) -> NorthboundFlowReport:
        """分析北向资金"""
        return self._northbound_analyzer.analyze(northbound_data, period)

    def format_fund_flow_report(self, report: FundFlowReport) -> str:
        """格式化基金申赎报告"""
        lines = ["# 基金申赎分析报告\n"]
        lines.append(f"报告日期: {report.report_date}")
        lines.append(f"摘要: {report.summary}\n")

        if report.top_inflow:
            lines.append("## 净申购TOP基金")
            for item in report.top_inflow[:5]:
                lines.append(f"- {item.fund_name}({item.fund_code}): 净申购{item.net_purchase:.2f}亿份 [{item.intensity.value}]")
            lines.append("")

        if report.top_outflow:
            lines.append("## 净赎回TOP基金")
            for item in report.top_outflow[:5]:
                lines.append(f"- {item.fund_name}({item.fund_code}): 净赎回{abs(item.net_purchase):.2f}亿份 [{item.intensity.value}]")
            lines.append("")

        if report.investment_signals:
            lines.append("## 投资信号")
            for s in report.investment_signals:
                lines.append(f"- {s}")

        return "\n".join(lines)

    def format_sector_flow_report(self, report: SectorFlowReport) -> str:
        """格式化板块资金报告"""
        lines = ["# 板块资金流向报告\n"]
        lines.append(f"报告日期: {report.report_date}\n")

        if report.strong_inflow:
            lines.append("## 资金流入板块")
            for item in report.strong_inflow[:5]:
                lines.append(f"- {item.sector_name}: 净流入{item.net_inflow:.2f}亿 [{item.intensity.value}] 连续{item.consecutive_days}天")
            lines.append("")

        if report.strong_outflow:
            lines.append("## 资金流出板块")
            for item in report.strong_outflow[:5]:
                lines.append(f"- {item.sector_name}: 净流出{abs(item.net_inflow):.2f}亿 [{item.intensity.value}] 连续{item.consecutive_days}天")
            lines.append("")

        if report.rotation_signals:
            lines.append("## 轮动信号")
            for s in report.rotation_signals:
                lines.append(f"- {s}")
            lines.append("")

        lines.append("## 投资建议")
        lines.append(report.investment_advice)

        return "\n".join(lines)

    def format_northbound_report(self, report: NorthboundFlowReport) -> str:
        """格式化北向资金报告"""
        lines = ["# 北向资金分析报告\n"]
        lines.append(f"分析周期: {report.period}")
        lines.append(f"净买入: {report.total_net_buy:.2f}亿元")
        lines.append(f"趋势: {report.trend}")
        lines.append(f"历史分位数: {report.historical_percentile:.0f}%\n")

        if report.investment_signals:
            lines.append("## 投资信号")
            for s in report.investment_signals:
                lines.append(f"- {s}")

        return "\n".join(lines)


def analyze_money_flow(
    flow_type: str = "fund",
    data_manager: DataManager | None = None,
) -> FundFlowReport | SectorFlowReport | NorthboundFlowReport:
    """资金流向分析便捷函数"""
    analyzer = MoneyFlowAnalyzer(data_manager)
    if flow_type == "fund":
        return analyzer.analyze_fund_flow()
    elif flow_type == "sector":
        return analyzer.analyze_sector_flow()
    elif flow_type == "northbound":
        return analyzer.analyze_northbound()
    else:
        return analyzer.analyze_fund_flow()
