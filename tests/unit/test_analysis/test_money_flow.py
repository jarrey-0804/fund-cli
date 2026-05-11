"""资金流向分析模块测试"""

import pytest
from fund_cli.analysis.money_flow import (
    MoneyFlowAnalyzer,
    FundFlowAnalyzer,
    SectorFlowAnalyzer,
    NorthboundFlowAnalyzer,
    FundFlowReport,
    SectorFlowReport,
    NorthboundFlowReport,
    FlowDirection,
    FlowIntensity,
    analyze_money_flow,
)


class TestFundFlowAnalyzer:
    def setup_method(self):
        self.analyzer = FundFlowAnalyzer()

    def test_analyze_default(self):
        report = self.analyzer.analyze()
        assert isinstance(report, FundFlowReport)
        assert len(report.items) > 0

    def test_analyze_with_custom_data(self):
        data = [
            {"code": "000001", "name": "基金A", "net_purchase": 15.0, "total_purchase": 25.0, "total_redeem": 10.0, "trend": 0.1},
            {"code": "000002", "name": "基金B", "net_purchase": -8.0, "total_purchase": 10.0, "total_redeem": 18.0, "trend": -0.1},
        ]
        report = self.analyzer.analyze(data, top_n=5)
        assert len(report.items) == 2
        assert report.top_inflow[0].direction == FlowDirection.INFLOW
        assert report.top_outflow[0].direction == FlowDirection.OUTFLOW

    def test_direction_and_intensity(self):
        data = [
            {"code": "000001", "name": "基金A", "net_purchase": 20.0, "total_purchase": 30.0, "total_redeem": 10.0, "trend": 0.1},
        ]
        report = self.analyzer.analyze(data)
        item = report.items[0]
        assert item.direction == FlowDirection.INFLOW
        assert item.intensity == FlowIntensity.STRONG

    def test_investment_signals(self):
        report = self.analyzer.analyze()
        assert isinstance(report.investment_signals, list)


class TestSectorFlowAnalyzer:
    def setup_method(self):
        self.analyzer = SectorFlowAnalyzer()

    def test_analyze_default(self):
        report = self.analyzer.analyze()
        assert isinstance(report, SectorFlowReport)
        assert len(report.items) > 0

    def test_strong_inflow_outflow(self):
        report = self.analyzer.analyze()
        assert len(report.strong_inflow) > 0
        assert len(report.strong_outflow) > 0

    def test_rotation_signals(self):
        report = self.analyzer.analyze()
        assert isinstance(report.rotation_signals, list)

    def test_consecutive_days(self):
        data = [{"sector": "科技", "net_inflow": 30.0, "main_inflow": 20.0, "retail_inflow": 10.0, "consecutive_days": 5}]
        report = self.analyzer.analyze(data)
        assert report.strong_inflow[0].consecutive_days == 5


class TestNorthboundFlowAnalyzer:
    def setup_method(self):
        self.analyzer = NorthboundFlowAnalyzer()

    def test_analyze_default(self):
        report = self.analyzer.analyze()
        assert isinstance(report, NorthboundFlowReport)
        assert len(report.items) > 0

    def test_trend_detection(self):
        report = self.analyzer.analyze()
        assert report.trend in ["持续流入", "持续流出", "波动"]

    def test_investment_signals(self):
        report = self.analyzer.analyze()
        assert isinstance(report.investment_signals, list)

    def test_total_net_buy(self):
        report = self.analyzer.analyze()
        assert isinstance(report.total_net_buy, float)


class TestMoneyFlowAnalyzer:
    def setup_method(self):
        self.analyzer = MoneyFlowAnalyzer()

    def test_analyze_fund_flow(self):
        report = self.analyzer.analyze_fund_flow()
        assert isinstance(report, FundFlowReport)

    def test_analyze_sector_flow(self):
        report = self.analyzer.analyze_sector_flow()
        assert isinstance(report, SectorFlowReport)

    def test_analyze_northbound(self):
        report = self.analyzer.analyze_northbound()
        assert isinstance(report, NorthboundFlowReport)

    def test_format_reports(self):
        fr = self.analyzer.analyze_fund_flow()
        assert "基金申赎分析报告" in self.analyzer.format_fund_flow_report(fr)

        sr = self.analyzer.analyze_sector_flow()
        assert "板块资金流向报告" in self.analyzer.format_sector_flow_report(sr)

        nr = self.analyzer.analyze_northbound()
        assert "北向资金分析报告" in self.analyzer.format_northbound_report(nr)


class TestEnums:
    def test_flow_direction(self):
        assert FlowDirection.INFLOW.value == "流入"
        assert FlowDirection.OUTFLOW.value == "流出"
        assert FlowDirection.NEUTRAL.value == "持平"

    def test_flow_intensity(self):
        assert FlowIntensity.STRONG.value == "强"
        assert FlowIntensity.MODERATE.value == "中"
        assert FlowIntensity.WEAK.value == "弱"


def test_analyze_money_flow_convenience():
    result = analyze_money_flow("fund")
    assert isinstance(result, FundFlowReport)

    result = analyze_money_flow("sector")
    assert isinstance(result, SectorFlowReport)

    result = analyze_money_flow("northbound")
    assert isinstance(result, NorthboundFlowReport)
