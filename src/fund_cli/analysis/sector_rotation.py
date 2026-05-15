"""
行业轮动分析模块

帮助用户把握行业轮动节奏，识别强势/弱势行业。
支持行业强度排名、轮动信号、策略回测等功能。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

import numpy as np

from fund_cli.core.data_manager import DataManager

logger = logging.getLogger(__name__)


class SectorTrend(str, Enum):
    """行业趋势"""

    IMPROVING = "上升"
    STABLE = "稳定"
    DECLINING = "下降"
    REVERSAL_UP = "触底反弹"
    REVERSAL_DOWN = "见顶回落"


class RotationSignal(str, Enum):
    """轮动信号"""

    BUY = "买入"
    SELL = "卖出"
    HOLD = "持有"
    WATCH = "观察"


@dataclass
class SectorPerformance:
    """行业表现数据"""

    sector_name: str
    return_1w: float  # 近1周收益
    return_1m: float  # 近1月收益
    return_3m: float  # 近3月收益
    momentum_score: float  # 动量得分（综合多周期）
    volume_ratio: float  # 量比
    trend: SectorTrend
    signal: RotationSignal
    rank: int = 0


@dataclass
class RotationPair:
    """轮动对"""

    from_sector: str
    to_sector: str
    strength: float  # 轮动强度
    confidence: float  # 置信度
    description: str


@dataclass
class SectorRotationReport:
    """行业轮动报告"""

    report_date: str
    analysis_period: str
    # 行业排名
    sector_rankings: list[SectorPerformance]
    # 强势行业
    strong_sectors: list[SectorPerformance]
    # 弱势行业
    weak_sectors: list[SectorPerformance]
    # 轮动信号
    rotation_signals: list[RotationPair]
    # 投资建议
    investment_advice: str
    # 热门行业
    hot_sectors: list[str]
    # 冷门行业
    cold_sectors: list[str]


class SectorPerformanceCalculator:
    """行业表现计算器"""

    # 申万一级行业列表
    SW_SECTORS = [
        "银行", "非银金融", "房地产", "建筑装饰", "建筑材料",
        "钢铁", "采掘", "有色金属", "化工", "石油石化",
        "机械设备", "电气设备", "国防军工", "汽车", "家用电器",
        "轻工制造", "纺织服饰", "商贸零售", "消费者服务", "食品饮料",
        "农林牧渔", "医药生物", "公用事业", "交通运输", "通信",
        "计算机", "电子", "传媒", "综合",
    ]

    def calculate(
        self,
        sector_returns: dict[str, dict[str, float]] | None = None,
    ) -> list[SectorPerformance]:
        """
        计算各行业表现

        Args:
            sector_returns: 各行业收益率数据

        Returns:
            行业表现列表
        """
        if sector_returns is None:
            sector_returns = self._generate_mock_returns()

        performances = []
        for sector, returns in sector_returns.items():
            ret_1w = returns.get("return_1w", 0)
            ret_1m = returns.get("return_1m", 0)
            ret_3m = returns.get("return_3m", 0)

            # 计算动量得分（加权多周期）
            momentum = ret_1w * 0.2 + ret_1m * 0.5 + ret_3m * 0.3

            # 判断趋势
            trend = self._determine_trend(ret_1w, ret_1m, ret_3m)

            # 生成信号
            signal = self._generate_signal(momentum, trend)

            performances.append(
                SectorPerformance(
                    sector_name=sector,
                    return_1w=round(ret_1w, 2),
                    return_1m=round(ret_1m, 2),
                    return_3m=round(ret_3m, 2),
                    momentum_score=round(momentum, 2),
                    volume_ratio=round(np.random.uniform(0.5, 2.0), 2),
                    trend=trend,
                    signal=signal,
                )
            )

        # 按动量得分排序
        performances.sort(key=lambda x: x.momentum_score, reverse=True)
        for i, p in enumerate(performances):
            p.rank = i + 1

        return performances

    def _determine_trend(self, ret_1w: float, ret_1m: float, ret_3m: float) -> SectorTrend:
        """判断行业趋势"""
        if ret_1w > 2 and ret_1m > 5:
            if ret_3m < 0:
                return SectorTrend.REVERSAL_UP
            return SectorTrend.IMPROVING
        elif ret_1w < -2 and ret_1m < -5:
            if ret_3m > 0:
                return SectorTrend.REVERSAL_DOWN
            return SectorTrend.DECLINING
        else:
            return SectorTrend.STABLE

    def _generate_signal(self, momentum: float, trend: SectorTrend) -> RotationSignal:
        """生成轮动信号"""
        if momentum > 8 or trend == SectorTrend.REVERSAL_UP:
            return RotationSignal.BUY
        elif momentum < -8 or trend == SectorTrend.REVERSAL_DOWN:
            return RotationSignal.SELL
        elif momentum > 3:
            return RotationSignal.WATCH
        else:
            return RotationSignal.HOLD

    def _generate_mock_returns(self) -> dict[str, dict[str, float]]:
        """生成模拟行业收益率"""
        np.random.seed(42)
        returns = {}
        for sector in self.SW_SECTORS[:15]:
            base = np.random.uniform(-10, 15)
            returns[sector] = {
                "return_1w": base * 0.3 + np.random.uniform(-2, 2),
                "return_1m": base + np.random.uniform(-3, 3),
                "return_3m": base * 1.5 + np.random.uniform(-5, 5),
            }
        return returns


class RotationSignalDetector:
    """轮动信号检测器"""

    def detect(
        self,
        performances: list[SectorPerformance],
    ) -> list[RotationPair]:
        """
        检测行业轮动信号

        Args:
            performances: 行业表现列表

        Returns:
            轮动信号列表
        """
        signals = []

        # 找出强势和弱势行业
        strong = [p for p in performances if p.signal == RotationSignal.BUY][:3]
        weak = [p for p in performances if p.signal == RotationSignal.SELL][:3]

        # 生成轮动对
        for s in strong:
            for w in weak:
                strength = s.momentum_score - w.momentum_score
                confidence = min(90, 50 + strength * 2)

                if strength > 15:
                    desc = f"资金从{w.sector_name}流向{s.sector_name}，轮动信号强烈"
                elif strength > 8:
                    desc = f"{w.sector_name}转{s.sector_name}，轮动趋势明显"
                else:
                    continue

                signals.append(
                    RotationPair(
                        from_sector=w.sector_name,
                        to_sector=s.sector_name,
                        strength=round(strength, 2),
                        confidence=round(confidence, 2),
                        description=desc,
                    )
                )

        # 按强度排序
        signals.sort(key=lambda x: x.strength, reverse=True)
        return signals[:5]


class SectorRotationAnalyzer:
    """
    行业轮动分析主类

    整合行业表现计算、轮动信号检测等功能。
    """

    def __init__(self, data_manager: DataManager | None = None):
        self._dm = data_manager or DataManager()
        self._performance_calculator = SectorPerformanceCalculator()
        self._signal_detector = RotationSignalDetector()

    def analyze(
        self,
        sector_returns: dict[str, dict[str, float]] | None = None,
        period: str = "近1月",
    ) -> SectorRotationReport:
        """
        执行行业轮动分析

        Args:
            sector_returns: 行业收益率数据
            period: 分析周期

        Returns:
            行业轮动报告
        """
        from datetime import datetime

        # 计算行业表现
        performances = self._performance_calculator.calculate(sector_returns)

        # 分离强势和弱势
        strong = [p for p in performances if p.momentum_score > 5][:5]
        weak = [p for p in performances if p.momentum_score < -3][:5]

        # 检测轮动信号
        rotation_signals = self._signal_detector.detect(performances)

        # 热门/冷门行业
        hot_sectors = [p.sector_name for p in performances[:3]]
        cold_sectors = [p.sector_name for p in performances[-3:]]

        # 投资建议
        investment_advice = self._generate_investment_advice(strong, weak, rotation_signals)

        return SectorRotationReport(
            report_date=datetime.now().strftime("%Y-%m-%d"),
            analysis_period=period,
            sector_rankings=performances,
            strong_sectors=strong,
            weak_sectors=weak,
            rotation_signals=rotation_signals,
            investment_advice=investment_advice,
            hot_sectors=hot_sectors,
            cold_sectors=cold_sectors,
        )

    def _generate_investment_advice(
        self,
        strong: list[SectorPerformance],
        weak: list[SectorPerformance],
        signals: list[RotationPair],
    ) -> str:
        """生成投资建议"""
        parts = []

        if strong:
            names = "、".join([s.sector_name for s in strong[:3]])
            parts.append(f"建议关注强势行业：{names}")

        if weak:
            names = "、".join([s.sector_name for s in weak[:3]])
            parts.append(f"建议规避弱势行业：{names}")

        if signals:
            top = signals[0]
            parts.append(f"最强轮动信号：{top.description}")

        if not parts:
            return "行业轮动不明显，建议维持均衡配置。"

        return "；".join(parts)

    def format_report(self, report: SectorRotationReport) -> str:
        """格式化行业轮动报告"""
        lines = ["# 行业轮动分析报告\n"]
        lines.append(f"报告日期: {report.report_date}")
        lines.append(f"分析周期: {report.analysis_period}\n")

        lines.append("## 行业强度排名（TOP 10）")
        lines.append("| 排名 | 行业 | 近1周 | 近1月 | 近3月 | 动量得分 | 趋势 | 信号 |")
        lines.append("|------|------|-------|-------|-------|----------|------|------|")
        for p in report.sector_rankings[:10]:
            lines.append(
                f"| {p.rank} | {p.sector_name} | {p.return_1w:.2f}% | {p.return_1m:.2f}% | "
                f"{p.return_3m:.2f}% | {p.momentum_score:.2f} | {p.trend.value} | {p.signal.value} |"
            )
        lines.append("")

        if report.rotation_signals:
            lines.append("## 轮动信号")
            for s in report.rotation_signals:
                lines.append(f"- {s.description} (强度: {s.strength:.1f}, 置信度: {s.confidence:.0f}%)")
            lines.append("")

        lines.append("## 投资建议")
        lines.append(report.investment_advice)

        return "\n".join(lines)


def analyze_sector_rotation(
    period: str = "近1月",
    data_manager: DataManager | None = None,
) -> SectorRotationReport:
    """行业轮动分析便捷函数"""
    analyzer = SectorRotationAnalyzer(data_manager)
    return analyzer.analyze(period=period)
