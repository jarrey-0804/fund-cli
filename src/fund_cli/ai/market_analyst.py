"""
市场解读助手

帮助用户理解市场动态，把握投资机会。
提供市场情绪分析、行业轮动分析、热点追踪等功能。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

from fund_cli.core.data_manager import DataManager

logger = logging.getLogger(__name__)


class MarketSentiment(str, Enum):
    """市场情绪"""

    EXTREME_FEAR = "极度恐慌"
    FEAR = "恐慌"
    NEUTRAL = "中性"
    GREED = "贪婪"
    EXTREME_GREED = "极度贪婪"


class SectorStrength(str, Enum):
    """行业强度"""

    STRONG = "强势"
    MODERATE = "中等"
    WEAK = "弱势"


@dataclass
class SentimentIndicator:
    """情绪指标"""

    name: str
    value: float
    weight: float
    contribution: float
    description: str


@dataclass
class MarketSentimentReport:
    """市场情绪报告"""

    # 综合情绪指数 (0-100)
    sentiment_index: float
    # 情绪等级
    sentiment_level: MarketSentiment
    # 各分项指标
    indicators: list[SentimentIndicator]
    # 市场解读
    interpretation: str
    # 投资建议
    investment_advice: str
    # 风险提示
    risk_warning: str


@dataclass
class SectorRotationItem:
    """行业轮动项"""

    sector_name: str
    strength: SectorStrength
    momentum: float  # 动量得分
    rank: int
    trend: str  # 上升/下降/持平
    recommendation: str


@dataclass
class SectorRotationReport:
    """行业轮动报告"""

    # 强势行业
    strong_sectors: list[SectorRotationItem]
    # 弱势行业
    weak_sectors: list[SectorRotationItem]
    # 轮动信号
    rotation_signals: list[str]
    # 投资建议
    investment_advice: str


@dataclass
class HotspotItem:
    """热点项"""

    name: str
    type: str  # 行业/主题/概念
    heat_score: float  # 热度得分
    related_funds: list[str]
    reason: str


@dataclass
class HotspotReport:
    """热点追踪报告"""

    # 热点列表
    hotspots: list[HotspotItem]
    # 热点解读
    interpretation: str
    # 投资机会
    opportunities: list[str]


class SentimentAnalyzer:
    """市场情绪分析器"""

    def analyze(
        self,
        market_data: dict[str, Any] | None = None,
        fund_flow_data: dict[str, Any] | None = None,
    ) -> MarketSentimentReport:
        """
        分析市场情绪

        Args:
            market_data: 市场数据（指数涨跌、成交量等）
            fund_flow_data: 资金流向数据

        Returns:
            市场情绪报告
        """
        indicators = []

        # 1. 涨跌比指标（模拟）
        if market_data and "advance_decline_ratio" in market_data:
            ratio = market_data["advance_decline_ratio"]
            score = min(100, ratio * 50)
            indicators.append(
                SentimentIndicator(
                    name="涨跌比",
                    value=ratio,
                    weight=0.25,
                    contribution=score * 0.25,
                    description=f"上涨下跌比{ratio:.2f}",
                )
            )
        else:
            # 默认中性
            indicators.append(
                SentimentIndicator(
                    name="涨跌比",
                    value=1.0,
                    weight=0.25,
                    contribution=50 * 0.25,
                    description="数据暂缺，默认中性",
                )
            )

        # 2. 资金流向指标（模拟）
        if fund_flow_data and "net_inflow" in fund_flow_data:
            net_flow = fund_flow_data["net_inflow"]
            # 假设正流入为贪婪
            score = 50 + min(50, net_flow / 100) if net_flow > 0 else 50 + max(-50, net_flow / 100)
            indicators.append(
                SentimentIndicator(
                    name="资金流向",
                    value=net_flow,
                    weight=0.30,
                    contribution=score * 0.30,
                    description=f"净流入{net_flow:.1f}亿",
                )
            )
        else:
            indicators.append(
                SentimentIndicator(
                    name="资金流向",
                    value=0,
                    weight=0.30,
                    contribution=50 * 0.30,
                    description="数据暂缺，默认中性",
                )
            )

        # 3. 波动率指标（模拟）
        if market_data and "volatility" in market_data:
            vol = market_data["volatility"]
            # 波动率越高越恐慌
            score = max(0, 100 - vol * 10)
            indicators.append(
                SentimentIndicator(
                    name="波动率",
                    value=vol,
                    weight=0.25,
                    contribution=score * 0.25,
                    description=f"波动率{vol:.1f}%",
                )
            )
        else:
            indicators.append(
                SentimentIndicator(
                    name="波动率",
                    value=15,
                    weight=0.25,
                    contribution=50 * 0.25,
                    description="数据暂缺，默认中性",
                )
            )

        # 4. 成交量指标（模拟）
        if market_data and "volume_ratio" in market_data:
            vol_ratio = market_data["volume_ratio"]
            # 量比高表示活跃
            score = min(100, vol_ratio * 50)
            indicators.append(
                SentimentIndicator(
                    name="成交量",
                    value=vol_ratio,
                    weight=0.20,
                    contribution=score * 0.20,
                    description=f"量比{vol_ratio:.2f}",
                )
            )
        else:
            indicators.append(
                SentimentIndicator(
                    name="成交量",
                    value=1.0,
                    weight=0.20,
                    contribution=50 * 0.20,
                    description="数据暂缺，默认中性",
                )
            )

        # 计算综合情绪指数
        sentiment_index = sum(ind.contribution for ind in indicators)

        # 确定情绪等级
        if sentiment_index >= 80:
            sentiment_level = MarketSentiment.EXTREME_GREED
        elif sentiment_index >= 60:
            sentiment_level = MarketSentiment.GREED
        elif sentiment_index >= 40:
            sentiment_level = MarketSentiment.NEUTRAL
        elif sentiment_index >= 20:
            sentiment_level = MarketSentiment.FEAR
        else:
            sentiment_level = MarketSentiment.EXTREME_FEAR

        # 生成解读
        interpretation = self._generate_interpretation(sentiment_level, sentiment_index)

        # 生成投资建议
        investment_advice = self._generate_investment_advice(sentiment_level)

        # 生成风险提示
        risk_warning = self._generate_risk_warning(sentiment_level)

        return MarketSentimentReport(
            sentiment_index=round(sentiment_index, 2),
            sentiment_level=sentiment_level,
            indicators=indicators,
            interpretation=interpretation,
            investment_advice=investment_advice,
            risk_warning=risk_warning,
        )

    def _generate_interpretation(self, level: MarketSentiment, index: float) -> str:
        """生成市场解读"""
        interpretations = {
            MarketSentiment.EXTREME_GREED: f"市场情绪指数{index:.0f}，处于极度贪婪状态。投资者情绪高涨，市场可能存在过热风险。",
            MarketSentiment.GREED: f"市场情绪指数{index:.0f}，处于贪婪状态。投资者信心较强，但需警惕追高风险。",
            MarketSentiment.NEUTRAL: f"市场情绪指数{index:.0f}，处于中性状态。市场情绪平稳，可按正常策略操作。",
            MarketSentiment.FEAR: f"市场情绪指数{index:.0f}，处于恐慌状态。投资者情绪谨慎，可能是逢低布局的机会。",
            MarketSentiment.EXTREME_FEAR: f"市场情绪指数{index:.0f}，处于极度恐慌状态。市场可能过度悲观，存在反弹机会。",
        }
        return interpretations[level]

    def _generate_investment_advice(self, level: MarketSentiment) -> str:
        """生成投资建议"""
        advices = {
            MarketSentiment.EXTREME_GREED: "建议保持谨慎，可适当降低仓位，避免追高。",
            MarketSentiment.GREED: "建议控制仓位，关注估值合理的标的。",
            MarketSentiment.NEUTRAL: "建议维持正常投资策略，均衡配置。",
            MarketSentiment.FEAR: "建议关注优质标的，可考虑逐步建仓。",
            MarketSentiment.EXTREME_FEAR: "建议逆向思考，优质资产可能被错杀，可择机布局。",
        }
        return advices[level]

    def _generate_risk_warning(self, level: MarketSentiment) -> str:
        """生成风险提示"""
        warnings = {
            MarketSentiment.EXTREME_GREED: "⚠️ 市场过热风险：情绪极度贪婪时往往是市场见顶信号，需警惕回调风险。",
            MarketSentiment.GREED: "⚠️ 追高风险：市场情绪偏乐观，需注意控制仓位和止损。",
            MarketSentiment.NEUTRAL: "市场情绪平稳，正常投资风险。",
            MarketSentiment.FEAR: "市场情绪低迷，需关注基本面变化，避免恐慌性抛售。",
            MarketSentiment.EXTREME_FEAR: "市场情绪极度悲观，可能存在系统性风险，但也可能是布局良机。",
        }
        return warnings[level]


class SectorRotationAnalyzer:
    """行业轮动分析器"""

    # 行业列表
    SECTORS = [
        "银行",
        "非银金融",
        "房地产",
        "建筑装饰",
        "建筑材料",
        "钢铁",
        "采掘",
        "有色金属",
        "化工",
        "石油石化",
        "机械设备",
        "电气设备",
        "国防军工",
        "汽车",
        "家用电器",
        "轻工制造",
        "纺织服饰",
        "商贸零售",
        "消费者服务",
        "食品饮料",
        "农林牧渔",
        "医药生物",
        "公用事业",
        "交通运输",
        "通信",
        "计算机",
        "电子",
        "传媒",
    ]

    def analyze(
        self,
        sector_returns: dict[str, float] | None = None,
        period: str = "1m",
    ) -> SectorRotationReport:
        """
        分析行业轮动

        Args:
            sector_returns: 各行业收益率数据
            period: 分析周期

        Returns:
            行业轮动报告
        """
        # 如果没有提供数据，使用模拟数据
        if sector_returns is None:
            sector_returns = self._generate_mock_returns()

        # 计算动量得分
        items = []
        for sector, ret in sector_returns.items():
            momentum = ret  # 简化处理，实际应考虑多周期动量

            if momentum > 5:
                strength = SectorStrength.STRONG
                trend = "上升"
                recommendation = f"建议关注{sector}板块，近期表现强势"
            elif momentum > -5:
                strength = SectorStrength.MODERATE
                trend = "持平"
                recommendation = f"{sector}板块表现中性，可保持观察"
            else:
                strength = SectorStrength.WEAK
                trend = "下降"
                recommendation = f"{sector}板块表现较弱，建议谨慎"

            items.append(
                SectorRotationItem(
                    sector_name=sector,
                    strength=strength,
                    momentum=round(momentum, 2),
                    rank=0,  # 后续排序
                    trend=trend,
                    recommendation=recommendation,
                )
            )

        # 按动量排序
        items.sort(key=lambda x: x.momentum, reverse=True)
        for i, item in enumerate(items):
            item.rank = i + 1

        # 分离强势和弱势行业
        strong_sectors = [item for item in items if item.strength == SectorStrength.STRONG][:5]
        weak_sectors = [item for item in items if item.strength == SectorStrength.WEAK][:5]

        # 生成轮动信号
        rotation_signals = self._generate_rotation_signals(strong_sectors, weak_sectors)

        # 生成投资建议
        investment_advice = self._generate_investment_advice(strong_sectors, weak_sectors)

        return SectorRotationReport(
            strong_sectors=strong_sectors,
            weak_sectors=weak_sectors,
            rotation_signals=rotation_signals,
            investment_advice=investment_advice,
        )

    def _generate_mock_returns(self) -> dict[str, float]:
        """生成模拟收益率数据"""
        np.random.seed(42)
        return {sector: np.random.uniform(-10, 15) for sector in self.SECTORS[:10]}

    def _generate_rotation_signals(
        self,
        strong: list[SectorRotationItem],
        weak: list[SectorRotationItem],
    ) -> list[str]:
        """生成轮动信号"""
        signals = []

        if strong:
            strong_names = "、".join([s.sector_name for s in strong[:3]])
            signals.append(f"强势板块：{strong_names}，可关注相关投资机会")

        if weak:
            weak_names = "、".join([s.sector_name for s in weak[:3]])
            signals.append(f"弱势板块：{weak_names}，建议规避或减仓")

        if strong and weak:
            signals.append("市场分化明显，建议关注板块轮动节奏")

        return signals

    def _generate_investment_advice(
        self,
        strong: list[SectorRotationItem],
        weak: list[SectorRotationItem],
    ) -> str:
        """生成投资建议"""
        if not strong and not weak:
            return "市场整体平稳，可维持均衡配置策略。"

        strong_names = "、".join([s.sector_name for s in strong[:3]]) if strong else "无"
        return f"建议关注强势板块{strong_names}的投资机会，同时规避弱势板块。注意控制仓位，做好风险管理。"


class HotspotTracker:
    """热点追踪器"""

    def track(
        self,
        hotspot_data: list[dict[str, Any]] | None = None,
    ) -> HotspotReport:
        """
        追踪市场热点

        Args:
            hotspot_data: 热点数据

        Returns:
            热点追踪报告
        """
        # 如果没有提供数据，使用模拟数据
        if hotspot_data is None:
            hotspot_data = self._generate_mock_hotspots()

        # 构建热点列表
        hotspots = []
        for item in hotspot_data[:10]:
            hotspots.append(
                HotspotItem(
                    name=item.get("name", ""),
                    type=item.get("type", "主题"),
                    heat_score=item.get("heat_score", 50),
                    related_funds=item.get("related_funds", []),
                    reason=item.get("reason", ""),
                )
            )

        # 按热度排序
        hotspots.sort(key=lambda x: x.heat_score, reverse=True)

        # 生成解读
        interpretation = self._generate_interpretation(hotspots)

        # 生成投资机会
        opportunities = self._generate_opportunities(hotspots)

        return HotspotReport(
            hotspots=hotspots,
            interpretation=interpretation,
            opportunities=opportunities,
        )

    def _generate_mock_hotspots(self) -> list[dict[str, Any]]:
        """生成模拟热点数据"""
        return [
            {"name": "人工智能", "type": "主题", "heat_score": 95, "related_funds": ["AI相关ETF"], "reason": "政策支持+技术突破"},
            {"name": "新能源", "type": "行业", "heat_score": 85, "related_funds": ["新能源基金"], "reason": "碳中和政策驱动"},
            {"name": "半导体", "type": "行业", "heat_score": 80, "related_funds": ["芯片ETF"], "reason": "国产替代加速"},
            {"name": "医药生物", "type": "行业", "heat_score": 70, "related_funds": ["医药基金"], "reason": "创新药研发进展"},
            {"name": "消费升级", "type": "主题", "heat_score": 65, "related_funds": ["消费基金"], "reason": "消费复苏预期"},
        ]

    def _generate_interpretation(self, hotspots: list[HotspotItem]) -> str:
        """生成热点解读"""
        if not hotspots:
            return "暂无明显市场热点。"

        top_hotspot = hotspots[0]
        return f"当前市场最热主题为【{top_hotspot.name}】，热度得分{top_hotspot.heat_score}。{top_hotspot.reason}。"

    def _generate_opportunities(self, hotspots: list[HotspotItem]) -> list[str]:
        """生成投资机会"""
        opportunities = []

        for item in hotspots[:3]:
            if item.heat_score >= 80:
                opportunities.append(f"【{item.name}】热度较高，可关注相关基金投资机会")
            elif item.heat_score >= 60:
                opportunities.append(f"【{item.name}】热度中等，可持续观察")

        return opportunities


class MarketAnalyst:
    """
    市场解读助手

    整合市场情绪分析、行业轮动分析、热点追踪等功能。
    """

    def __init__(self, data_manager: DataManager | None = None):
        """
        初始化市场解读助手

        Args:
            data_manager: 数据管理器实例
        """
        self._dm = data_manager or DataManager()
        self._sentiment_analyzer = SentimentAnalyzer()
        self._sector_analyzer = SectorRotationAnalyzer()
        self._hotspot_tracker = HotspotTracker()

    def analyze_sentiment(
        self,
        market_data: dict[str, Any] | None = None,
        fund_flow_data: dict[str, Any] | None = None,
    ) -> MarketSentimentReport:
        """
        分析市场情绪

        Args:
            market_data: 市场数据
            fund_flow_data: 资金流向数据

        Returns:
            市场情绪报告
        """
        return self._sentiment_analyzer.analyze(market_data, fund_flow_data)

    def analyze_sector_rotation(
        self,
        sector_returns: dict[str, float] | None = None,
        period: str = "1m",
    ) -> SectorRotationReport:
        """
        分析行业轮动

        Args:
            sector_returns: 各行业收益率数据
            period: 分析周期

        Returns:
            行业轮动报告
        """
        return self._sector_analyzer.analyze(sector_returns, period)

    def track_hotspots(
        self,
        hotspot_data: list[dict[str, Any]] | None = None,
    ) -> HotspotReport:
        """
        追踪市场热点

        Args:
            hotspot_data: 热点数据

        Returns:
            热点追踪报告
        """
        return self._hotspot_tracker.track(hotspot_data)

    def format_sentiment_report(self, report: MarketSentimentReport) -> str:
        """格式化情绪报告"""
        lines = ["# 市场情绪分析报告\n"]

        lines.append("## 综合情绪指数")
        lines.append(f"- 情绪指数: {report.sentiment_index}/100")
        lines.append(f"- 情绪等级: {report.sentiment_level.value}")
        lines.append("")

        lines.append("## 分项指标")
        for ind in report.indicators:
            lines.append(f"- {ind.name}: {ind.description} (权重{ind.weight*100:.0f}%)")
        lines.append("")

        lines.append("## 市场解读")
        lines.append(report.interpretation)
        lines.append("")

        lines.append("## 投资建议")
        lines.append(report.investment_advice)
        lines.append("")

        lines.append("## 风险提示")
        lines.append(report.risk_warning)

        return "\n".join(lines)

    def format_sector_report(self, report: SectorRotationReport) -> str:
        """格式化行业轮动报告"""
        lines = ["# 行业轮动分析报告\n"]

        lines.append("## 强势行业")
        for item in report.strong_sectors:
            lines.append(f"- {item.rank}. {item.sector_name}: 动量{item.momentum:.2f}%, {item.recommendation}")
        lines.append("")

        lines.append("## 弱势行业")
        for item in report.weak_sectors:
            lines.append(f"- {item.rank}. {item.sector_name}: 动量{item.momentum:.2f}%, {item.recommendation}")
        lines.append("")

        lines.append("## 轮动信号")
        for signal in report.rotation_signals:
            lines.append(f"- {signal}")
        lines.append("")

        lines.append("## 投资建议")
        lines.append(report.investment_advice)

        return "\n".join(lines)

    def format_hotspot_report(self, report: HotspotReport) -> str:
        """格式化热点追踪报告"""
        lines = ["# 市场热点追踪报告\n"]

        lines.append("## 热点列表")
        for i, item in enumerate(report.hotspots, 1):
            lines.append(f"- {i}. {item.name} ({item.type}): 热度{item.heat_score}")
            if item.related_funds:
                lines.append(f"  相关基金: {', '.join(item.related_funds)}")
            lines.append(f"  原因: {item.reason}")
        lines.append("")

        lines.append("## 热点解读")
        lines.append(report.interpretation)
        lines.append("")

        lines.append("## 投资机会")
        for opp in report.opportunities:
            lines.append(f"- {opp}")

        return "\n".join(lines)


def analyze_market_sentiment(
    market_data: dict[str, Any] | None = None,
    data_manager: DataManager | None = None,
) -> MarketSentimentReport:
    """市场情绪分析便捷函数"""
    analyst = MarketAnalyst(data_manager)
    return analyst.analyze_sentiment(market_data)


def analyze_sector_rotation(
    sector_returns: dict[str, float] | None = None,
    data_manager: DataManager | None = None,
) -> SectorRotationReport:
    """行业轮动分析便捷函数"""
    analyst = MarketAnalyst(data_manager)
    return analyst.analyze_sector_rotation(sector_returns)


def track_market_hotspots(
    hotspot_data: list[dict[str, Any]] | None = None,
    data_manager: DataManager | None = None,
) -> HotspotReport:
    """热点追踪便捷函数"""
    analyst = MarketAnalyst(data_manager)
    return analyst.track_hotspots(hotspot_data)
