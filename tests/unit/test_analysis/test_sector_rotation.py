"""行业轮动分析模块测试"""

import pytest
from fund_cli.analysis.sector_rotation import (
    SectorRotationAnalyzer,
    SectorPerformanceCalculator,
    RotationSignalDetector,
    SectorPerformance,
    RotationPair,
    SectorRotationReport,
    SectorTrend,
    RotationSignal,
    analyze_sector_rotation,
)


class TestSectorPerformanceCalculator:
    def setup_method(self):
        self.calculator = SectorPerformanceCalculator()

    def test_calculate_default(self):
        results = self.calculator.calculate()
        assert isinstance(results, list)
        assert len(results) > 0

    def test_ranking(self):
        results = self.calculator.calculate()
        scores = [r.momentum_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_trend_detection(self):
        assert self.calculator._determine_trend(3, 8, 10) == SectorTrend.IMPROVING
        assert self.calculator._determine_trend(-3, -8, -10) == SectorTrend.DECLINING
        assert self.calculator._determine_trend(0, 0, 0) == SectorTrend.STABLE

    def test_signal_generation(self):
        assert self.calculator._generate_signal(15, SectorTrend.IMPROVING) == RotationSignal.BUY
        assert self.calculator._generate_signal(-15, SectorTrend.DECLINING) == RotationSignal.SELL

    def test_custom_data(self):
        data = {
            "科技": {"return_1w": 5.0, "return_1m": 15.0, "return_3m": 20.0},
            "银行": {"return_1w": -2.0, "return_1m": -8.0, "return_3m": -15.0},
        }
        results = self.calculator.calculate(data)
        assert len(results) == 2
        assert results[0].sector_name == "科技"
        assert results[0].signal == RotationSignal.BUY


class TestRotationSignalDetector:
    def setup_method(self):
        self.detector = RotationSignalDetector()

    def test_detect_signals(self):
        performances = [
            SectorPerformance("A", 5, 15, 20, 15, 1.2, SectorTrend.IMPROVING, RotationSignal.BUY, 1),
            SectorPerformance("B", -5, -15, -20, -15, 0.8, SectorTrend.DECLINING, RotationSignal.SELL, 2),
        ]
        signals = self.detector.detect(performances)
        assert isinstance(signals, list)
        if signals:
            assert signals[0].from_sector == "B"
            assert signals[0].to_sector == "A"

    def test_no_signals_when_flat(self):
        performances = [
            SectorPerformance("A", 0, 1, 2, 1, 1.0, SectorTrend.STABLE, RotationSignal.HOLD, 1),
        ]
        signals = self.detector.detect(performances)
        assert len(signals) == 0


class TestSectorRotationAnalyzer:
    def setup_method(self):
        self.analyzer = SectorRotationAnalyzer()

    def test_analyze_default(self):
        report = self.analyzer.analyze()
        assert isinstance(report, SectorRotationReport)
        assert len(report.sector_rankings) > 0

    def test_strong_weak_sectors(self):
        report = self.analyzer.analyze()
        assert isinstance(report.strong_sectors, list)
        assert isinstance(report.weak_sectors, list)

    def test_hot_cold_sectors(self):
        report = self.analyzer.analyze()
        assert len(report.hot_sectors) > 0
        assert len(report.cold_sectors) > 0

    def test_format_report(self):
        report = self.analyzer.analyze()
        formatted = self.analyzer.format_report(report)
        assert "行业轮动分析报告" in formatted
        assert "行业强度排名" in formatted


class TestEnums:
    def test_sector_trend(self):
        assert SectorTrend.IMPROVING.value == "上升"
        assert SectorTrend.STABLE.value == "稳定"
        assert SectorTrend.DECLINING.value == "下降"
        assert SectorTrend.REVERSAL_UP.value == "触底反弹"
        assert SectorTrend.REVERSAL_DOWN.value == "见顶回落"

    def test_rotation_signal(self):
        assert RotationSignal.BUY.value == "买入"
        assert RotationSignal.SELL.value == "卖出"
        assert RotationSignal.HOLD.value == "持有"
        assert RotationSignal.WATCH.value == "观察"


def test_analyze_sector_rotation_convenience():
    report = analyze_sector_rotation()
    assert isinstance(report, SectorRotationReport)
