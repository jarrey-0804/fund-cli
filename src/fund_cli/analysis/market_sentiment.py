"""
市场情绪指标模块

帮助用户判断市场情绪，辅助择时决策。
提供恐慌贪婪指数、基金仓位估算、市场宽度、情绪预警等功能。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from fund_cli.core.data_manager import DataManager

logger = logging.getLogger(__name__)


class SentimentLevel(str, Enum):
    """情绪等级"""

    EXTREME_FEAR = "极度恐慌"
    FEAR = "恐慌"
    NEUTRAL = "中性"
    GREED = "贪婪"
    EXTREME_GREED = "极度贪婪"


class MarketBreadth(str, Enum):
    """市场宽度"""

    STRONG = "强势"
    NORMAL = "正常"
    WEAK = "弱势"


@dataclass
class SentimentIndicator:
    """情绪指标"""

    name: str
    value: float
    normalized_score: float  # 0-100
    weight: float
    contribution: float
    description: str


@dataclass
class FearGreedIndex:
    """恐慌贪婪指数"""

    value: float  # 0-100
    level: SentimentLevel
    indicators: list[SentimentIndicator]
    historical_percentile: float  # 历史分位数
    interpretation: str
    investment_advice: str
    risk_warning: str


@dataclass
class FundPositionEstimate:
    """基金仓位估算"""

    fund_type: str
    average_position: float  # 平均仓位 (%)
    position_change: float  # 仓位变动 (百分点)
    high_position_ratio: float  # 高仓位基金占比 (%)
    low_position_ratio: float  # 低仓位基金占比 (%)
    trend: str  # 加仓/减仓/持平


@dataclass
class MarketBreadthIndicator:
    """市场宽度指标"""

    advance_decline_ratio: float  # 涨跌比
    new_high_low: int  # 创新高-创新低差
    breadth_level: MarketBreadth
    up_volume_ratio: float  # 上涨成交量占比
    description: str


@dataclass
class SentimentAlert:
    """情绪预警"""

    alert_type: str  # 极端恐慌/极端贪婪/异常波动
    level: str  # 高/中/低
    description: str
    suggestion: str
    timestamp: str


@dataclass
class MarketSentimentReport:
    """市场情绪综合报告"""

    report_date: str
    # 恐慌贪婪指数
    fear_greed_index: FearGreedIndex
    # 基金仓位估算
    fund_position: FundPositionEstimate
    # 市场宽度
    market_breadth: MarketBreadthIndicator
    # 情绪预警
    alerts: list[SentimentAlert]
    # 综合评估
    overall_sentiment: SentimentLevel
    timing_advice: str


class FearGreedCalculator:
    """恐慌贪婪指数计算器"""

    def calculate(
        self,
        market_data: dict[str, Any] | None = None,
    ) -> FearGreedIndex:
        """
        计算恐慌贪婪指数

        Args:
            market_data: 市场数据

        Returns:
            恐慌贪婪指数
        """
        if market_data is None:
            market_data = {}

        indicators = []

        # 1. 涨跌比指标 (权重20%)
        ad_ratio = market_data.get("advance_decline_ratio", 1.2)
        ad_score = self._normalize_ad_ratio(ad_ratio)
        indicators.append(
            SentimentIndicator(
                name="涨跌比",
                value=ad_ratio,
                normalized_score=ad_score,
                weight=0.20,
                contribution=ad_score * 0.20,
                description=f"上涨下跌比{ad_ratio:.2f}",
            )
        )

        # 2. 波动率指标 (权重20%)
        volatility = market_data.get("volatility", 18.0)
        vol_score = self._normalize_volatility(volatility)
        indicators.append(
            SentimentIndicator(
                name="波动率",
                value=volatility,
                normalized_score=vol_score,
                weight=0.20,
                contribution=vol_score * 0.20,
                description=f"市场波动率{volatility:.1f}%",
            )
        )

        # 3. 成交量指标 (权重15%)
        volume_ratio = market_data.get("volume_ratio", 1.0)
        vol_r_score = self._normalize_volume_ratio(volume_ratio)
        indicators.append(
            SentimentIndicator(
                name="成交量",
                value=volume_ratio,
                normalized_score=vol_r_score,
                weight=0.15,
                contribution=vol_r_score * 0.15,
                description=f"量比{volume_ratio:.2f}",
            )
        )

        # 4. 新高新低指标 (权重15%)
        new_hl = market_data.get("new_high_low", 50)
        hl_score = self._normalize_new_high_low(new_hl)
        indicators.append(
            SentimentIndicator(
                name="新高新低",
                value=new_hl,
                normalized_score=hl_score,
                weight=0.15,
                contribution=hl_score * 0.15,
                description=f"创新高-创新低差{new_hl}",
            )
        )

        # 5. 资金流向指标 (权重15%)
        net_flow = market_data.get("net_flow", 30.0)
        flow_score = self._normalize_net_flow(net_flow)
        indicators.append(
            SentimentIndicator(
                name="资金流向",
                value=net_flow,
                normalized_score=flow_score,
                weight=0.15,
                contribution=flow_score * 0.15,
                description=f"北向资金净流入{net_flow:.1f}亿",
            )
        )

        # 6. 市场宽度指标 (权重15%)
        breadth = market_data.get("market_breadth", 55.0)
        breadth_score = self._normalize_breadth(breadth)
        indicators.append(
            SentimentIndicator(
                name="市场宽度",
                value=breadth,
                normalized_score=breadth_score,
                weight=0.15,
                contribution=breadth_score * 0.15,
                description=f"上涨占比{breadth:.1f}%",
            )
        )

        # 计算综合指数
        total = sum(ind.contribution for ind in indicators)
        total = max(0, min(100, total))

        # 确定情绪等级
        level = self._get_sentiment_level(total)

        # 历史分位数（模拟）
        historical_percentile = self._estimate_percentile(total)

        # 生成解读
        interpretation = self._generate_interpretation(total, level)
        investment_advice = self._generate_investment_advice(level)
        risk_warning = self._generate_risk_warning(level)

        return FearGreedIndex(
            value=round(total, 2),
            level=level,
            indicators=indicators,
            historical_percentile=historical_percentile,
            interpretation=interpretation,
            investment_advice=investment_advice,
            risk_warning=risk_warning,
        )

    def _normalize_ad_ratio(self, ratio: float) -> float:
        """归一化涨跌比"""
        if ratio >= 3:
            return 100
        elif ratio >= 2:
            return 80
        elif ratio >= 1.5:
            return 65
        elif ratio >= 1:
            return 50
        elif ratio >= 0.5:
            return 35
        else:
            return 20

    def _normalize_volatility(self, vol: float) -> float:
        """归一化波动率（低波动=贪婪）"""
        if vol <= 10:
            return 90
        elif vol <= 15:
            return 70
        elif vol <= 20:
            return 50
        elif vol <= 30:
            return 30
        else:
            return 15

    def _normalize_volume_ratio(self, ratio: float) -> float:
        """归一化量比"""
        if ratio >= 2:
            return 85
        elif ratio >= 1.5:
            return 70
        elif ratio >= 1:
            return 50
        elif ratio >= 0.7:
            return 35
        else:
            return 20

    def _normalize_new_high_low(self, value: int) -> float:
        """归一化新高新低"""
        if value >= 200:
            return 90
        elif value >= 100:
            return 70
        elif value >= 0:
            return 50
        elif value >= -100:
            return 30
        else:
            return 15

    def _normalize_net_flow(self, flow: float) -> float:
        """归一化资金流向"""
        if flow >= 100:
            return 90
        elif flow >= 50:
            return 75
        elif flow >= 0:
            return 55
        elif flow >= -50:
            return 35
        else:
            return 15

    def _normalize_breadth(self, breadth: float) -> float:
        """归一化市场宽度"""
        return min(100, max(0, breadth))

    def _get_sentiment_level(self, value: float) -> SentimentLevel:
        """获取情绪等级"""
        if value >= 80:
            return SentimentLevel.EXTREME_GREED
        elif value >= 60:
            return SentimentLevel.GREED
        elif value >= 40:
            return SentimentLevel.NEUTRAL
        elif value >= 20:
            return SentimentLevel.FEAR
        else:
            return SentimentLevel.EXTREME_FEAR

    def _estimate_percentile(self, value: float) -> float:
        """估算历史分位数"""
        return min(99, max(1, value))

    def _generate_interpretation(self, value: float, level: SentimentLevel) -> str:
        """生成解读"""
        interpretations = {
            SentimentLevel.EXTREME_GREED: f"恐慌贪婪指数{value:.0f}，市场极度贪婪。投资者情绪高涨，需警惕过热风险。",
            SentimentLevel.GREED: f"恐慌贪婪指数{value:.0f}，市场偏贪婪。投资者信心较强，但需注意追高风险。",
            SentimentLevel.NEUTRAL: f"恐慌贪婪指数{value:.0f}，市场情绪中性。多空力量相对均衡。",
            SentimentLevel.FEAR: f"恐慌贪婪指数{value:.0f}，市场偏恐慌。投资者情绪谨慎，可能是布局机会。",
            SentimentLevel.EXTREME_FEAR: f"恐慌贪婪指数{value:.0f}，市场极度恐慌。往往对应市场底部区域。",
        }
        return interpretations[level]

    def _generate_investment_advice(self, level: SentimentLevel) -> str:
        """生成投资建议"""
        advices = {
            SentimentLevel.EXTREME_GREED: "建议大幅降低仓位，锁定收益，等待回调",
            SentimentLevel.GREED: "建议适度降低仓位，控制风险",
            SentimentLevel.NEUTRAL: "建议维持正常仓位，均衡配置",
            SentimentLevel.FEAR: "建议关注优质标的，可考虑逐步建仓",
            SentimentLevel.EXTREME_FEAR: "建议逆向布局，优质资产可能被错杀",
        }
        return advices[level]

    def _generate_risk_warning(self, level: SentimentLevel) -> str:
        """生成风险提示"""
        warnings = {
            SentimentLevel.EXTREME_GREED: "⚠️ 市场过热风险极高，历史上极度贪婪后往往伴随较大回调",
            SentimentLevel.GREED: "⚠️ 追高风险存在，建议设置止盈",
            SentimentLevel.NEUTRAL: "市场情绪平稳，正常投资风险",
            SentimentLevel.FEAR: "市场情绪低迷，注意控制仓位，避免恐慌性操作",
            SentimentLevel.EXTREME_FEAR: "⚠️ 市场极度恐慌，但也可能是中长期布局良机",
        }
        return warnings[level]


class FundPositionEstimator:
    """基金仓位估算器"""

    def estimate(
        self,
        position_data: dict[str, Any] | None = None,
    ) -> FundPositionEstimate:
        """
        估算基金仓位

        Args:
            position_data: 仓位数据

        Returns:
            基金仓位估算
        """
        if position_data is None:
            position_data = {}

        avg_position = position_data.get("average_position", 72.0)
        position_change = position_data.get("position_change", 1.5)
        high_ratio = position_data.get("high_position_ratio", 45.0)
        low_ratio = position_data.get("low_position_ratio", 15.0)

        if position_change > 2:
            trend = "加仓"
        elif position_change < -2:
            trend = "减仓"
        else:
            trend = "持平"

        return FundPositionEstimate(
            fund_type="股票型",
            average_position=round(avg_position, 2),
            position_change=round(position_change, 2),
            high_position_ratio=round(high_ratio, 2),
            low_position_ratio=round(low_ratio, 2),
            trend=trend,
        )


class MarketBreadthCalculator:
    """市场宽度计算器"""

    def calculate(
        self,
        breadth_data: dict[str, Any] | None = None,
    ) -> MarketBreadthIndicator:
        """
        计算市场宽度

        Args:
            breadth_data: 市场宽度数据

        Returns:
            市场宽度指标
        """
        if breadth_data is None:
            breadth_data = {}

        ad_ratio = breadth_data.get("advance_decline_ratio", 1.2)
        new_hl = breadth_data.get("new_high_low", 50)
        up_vol_ratio = breadth_data.get("up_volume_ratio", 55.0)

        if ad_ratio > 2:
            level = MarketBreadth.STRONG
        elif ad_ratio > 0.8:
            level = MarketBreadth.NORMAL
        else:
            level = MarketBreadth.WEAK

        if level == MarketBreadth.STRONG:
            desc = "市场宽度良好，多数个股上涨"
        elif level == MarketBreadth.NORMAL:
            desc = "市场宽度正常，涨跌互现"
        else:
            desc = "市场宽度较差，多数个股下跌"

        return MarketBreadthIndicator(
            advance_decline_ratio=round(ad_ratio, 2),
            new_high_low=new_hl,
            breadth_level=level,
            up_volume_ratio=round(up_vol_ratio, 2),
            description=desc,
        )


class SentimentAlertGenerator:
    """情绪预警生成器"""

    def generate(
        self,
        fear_greed: FearGreedIndex,
        fund_position: FundPositionEstimate,
        market_breadth: MarketBreadthIndicator,
    ) -> list[SentimentAlert]:
        """生成情绪预警"""
        from datetime import datetime

        alerts = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 极端情绪预警
        if fear_greed.level == SentimentLevel.EXTREME_GREED:
            alerts.append(
                SentimentAlert(
                    alert_type="极度贪婪",
                    level="高",
                    description=f"恐慌贪婪指数{fear_greed.value:.0f}，处于极度贪婪区间",
                    suggestion="建议降低仓位，锁定收益",
                    timestamp=timestamp,
                )
            )
        elif fear_greed.level == SentimentLevel.EXTREME_FEAR:
            alerts.append(
                SentimentAlert(
                    alert_type="极度恐慌",
                    level="高",
                    description=f"恐慌贪婪指数{fear_greed.value:.0f}，处于极度恐慌区间",
                    suggestion="可考虑逆向布局优质资产",
                    timestamp=timestamp,
                )
            )

        # 仓位异常预警
        if fund_position.average_position > 85:
            alerts.append(
                SentimentAlert(
                    alert_type="仓位偏高",
                    level="中",
                    description=f"基金平均仓位{fund_position.average_position:.1f}%，处于高位",
                    suggestion="注意仓位风险，市场回调时可能引发赎回",
                    timestamp=timestamp,
                )
            )
        elif fund_position.average_position < 60:
            alerts.append(
                SentimentAlert(
                    alert_type="仓位偏低",
                    level="中",
                    description=f"基金平均仓位{fund_position.average_position:.1f}%，处于低位",
                    suggestion="基金经理偏谨慎，注意市场不确定性",
                    timestamp=timestamp,
                )
            )

        # 市场宽度异常
        if market_breadth.breadth_level == MarketBreadth.WEAK:
            alerts.append(
                SentimentAlert(
                    alert_type="市场宽度较差",
                    level="中",
                    description=f"涨跌比{market_breadth.advance_decline_ratio:.2f}，多数个股下跌",
                    suggestion="市场赚钱效应差，建议降低仓位或观望",
                    timestamp=timestamp,
                )
            )

        if not alerts:
            alerts.append(
                SentimentAlert(
                    alert_type="正常",
                    level="低",
                    description="市场情绪正常，无异常信号",
                    suggestion="维持正常投资策略",
                    timestamp=timestamp,
                )
            )

        return alerts


class MarketSentimentAnalyzer:
    """
    市场情绪分析主类

    整合恐慌贪婪指数、基金仓位估算、市场宽度、情绪预警等功能。
    """

    def __init__(self, data_manager: DataManager | None = None):
        self._dm = data_manager or DataManager()
        self._fg_calculator = FearGreedCalculator()
        self._position_estimator = FundPositionEstimator()
        self._breadth_calculator = MarketBreadthCalculator()
        self._alert_generator = SentimentAlertGenerator()

    def analyze(
        self,
        market_data: dict[str, Any] | None = None,
    ) -> MarketSentimentReport:
        """
        执行市场情绪分析

        Args:
            market_data: 市场数据

        Returns:
            市场情绪综合报告
        """
        from datetime import datetime

        # 计算各指标
        fear_greed = self._fg_calculator.calculate(market_data)
        fund_position = self._position_estimator.estimate(market_data)
        market_breadth = self._breadth_calculator.calculate(market_data)

        # 生成预警
        alerts = self._alert_generator.generate(fear_greed, fund_position, market_breadth)

        # 综合择时建议
        timing_advice = self._generate_timing_advice(fear_greed, fund_position, market_breadth)

        return MarketSentimentReport(
            report_date=datetime.now().strftime("%Y-%m-%d"),
            fear_greed_index=fear_greed,
            fund_position=fund_position,
            market_breadth=market_breadth,
            alerts=alerts,
            overall_sentiment=fear_greed.level,
            timing_advice=timing_advice,
        )

    def _generate_timing_advice(
        self,
        fear_greed: FearGreedIndex,
        fund_position: FundPositionEstimate,
        market_breadth: MarketBreadthIndicator,
    ) -> str:
        """生成择时建议"""
        parts = []

        # 基于恐慌贪婪指数
        if fear_greed.level in [SentimentLevel.EXTREME_GREED, SentimentLevel.GREED]:
            parts.append("情绪偏热，建议逐步减仓")
        elif fear_greed.level in [SentimentLevel.EXTREME_FEAR, SentimentLevel.FEAR]:
            parts.append("情绪偏冷，可考虑逐步建仓")
        else:
            parts.append("情绪中性，维持现有仓位")

        # 基于仓位
        if fund_position.trend == "加仓" and fear_greed.level in [SentimentLevel.GREED, SentimentLevel.EXTREME_GREED]:
            parts.append("基金在高位加仓，需警惕风险")

        # 基于市场宽度
        if market_breadth.breadth_level == MarketBreadth.STRONG:
            parts.append("市场宽度良好，赚钱效应较好")

        return "；".join(parts)

    def format_report(self, report: MarketSentimentReport) -> str:
        """格式化市场情绪报告"""
        lines = ["# 市场情绪综合报告\n"]
        lines.append(f"报告日期: {report.report_date}")
        lines.append(f"综合情绪: {report.overall_sentiment.value}\n")

        # 恐慌贪婪指数
        fg = report.fear_greed_index
        lines.append("## 恐慌贪婪指数")
        lines.append(f"- 指数值: {fg.value:.2f}/100")
        lines.append(f"- 情绪等级: {fg.level.value}")
        lines.append(f"- 历史分位数: {fg.historical_percentile:.0f}%")
        lines.append("- 分项指标:")
        for ind in fg.indicators:
            lines.append(f"  - {ind.name}: {ind.description} (得分{ind.normalized_score:.0f})")
        lines.append("")
        lines.append(f"- 解读: {fg.interpretation}")
        lines.append(f"- 建议: {fg.investment_advice}")
        lines.append(f"- 风险: {fg.risk_warning}")
        lines.append("")

        # 基金仓位
        fp = report.fund_position
        lines.append("## 基金仓位估算")
        lines.append(f"- 平均仓位: {fp.average_position:.2f}%")
        lines.append(f"- 仓位变动: {fp.position_change:+.2f}个百分点")
        lines.append(f"- 趋势: {fp.trend}")
        lines.append(f"- 高仓位占比: {fp.high_position_ratio:.1f}%")
        lines.append(f"- 低仓位占比: {fp.low_position_ratio:.1f}%")
        lines.append("")

        # 市场宽度
        mb = report.market_breadth
        lines.append("## 市场宽度")
        lines.append(f"- 涨跌比: {mb.advance_decline_ratio:.2f}")
        lines.append(f"- 新高-新低: {mb.new_high_low}")
        lines.append(f"- 上涨成交量占比: {mb.up_volume_ratio:.1f}%")
        lines.append(f"- 宽度等级: {mb.breadth_level.value}")
        lines.append(f"- 说明: {mb.description}")
        lines.append("")

        # 预警
        if report.alerts:
            lines.append("## 情绪预警")
            for alert in report.alerts:
                if alert.level != "低":
                    lines.append(f"- [{alert.level}]{alert.alert_type}: {alert.description}")
                    lines.append(f"  建议: {alert.suggestion}")
            lines.append("")

        # 择时建议
        lines.append("## 择时建议")
        lines.append(report.timing_advice)

        return "\n".join(lines)


def analyze_market_sentiment(
    market_data: dict[str, Any] | None = None,
    data_manager: DataManager | None = None,
) -> MarketSentimentReport:
    """市场情绪分析便捷函数"""
    analyzer = MarketSentimentAnalyzer(data_manager)
    return analyzer.analyze(market_data)
