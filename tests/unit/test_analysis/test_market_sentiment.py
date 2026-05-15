"""市场情绪指标模块测试"""

from fund_cli.analysis.market_sentiment import (
    FearGreedCalculator,
    FearGreedIndex,
    FundPositionEstimate,
    FundPositionEstimator,
    MarketBreadth,
    MarketBreadthCalculator,
    MarketBreadthIndicator,
    MarketSentimentAnalyzer,
    MarketSentimentReport,
    SentimentAlertGenerator,
    SentimentLevel,
    analyze_market_sentiment,
)


class TestFearGreedCalculator:
    def setup_method(self):
        self.calculator = FearGreedCalculator()

    def test_calculate_default(self):
        result = self.calculator.calculate()
        assert isinstance(result, FearGreedIndex)
        assert 0 <= result.value <= 100

    def test_extreme_greed(self):
        data = {"advance_decline_ratio": 3.0, "volatility": 8.0, "volume_ratio": 2.5, "new_high_low": 300, "net_flow": 200, "market_breadth": 85}
        result = self.calculator.calculate(data)
        assert result.level == SentimentLevel.EXTREME_GREED
        assert result.value >= 80

    def test_extreme_fear(self):
        data = {"advance_decline_ratio": 0.3, "volatility": 40.0, "volume_ratio": 0.5, "new_high_low": -200, "net_flow": -150, "market_breadth": 15}
        result = self.calculator.calculate(data)
        assert result.level == SentimentLevel.EXTREME_FEAR
        assert result.value <= 20

    def test_neutral(self):
        data = {"advance_decline_ratio": 1.0, "volatility": 18.0, "volume_ratio": 1.0, "new_high_low": 0, "net_flow": 0, "market_breadth": 50}
        result = self.calculator.calculate(data)
        assert result.level == SentimentLevel.NEUTRAL

    def test_indicators_count(self):
        result = self.calculator.calculate()
        assert len(result.indicators) == 6

    def test_interpretation_and_advice(self):
        result = self.calculator.calculate()
        assert result.interpretation != ""
        assert result.investment_advice != ""
        assert result.risk_warning != ""


class TestFundPositionEstimator:
    def setup_method(self):
        self.estimator = FundPositionEstimator()

    def test_estimate_default(self):
        result = self.estimator.estimate()
        assert isinstance(result, FundPositionEstimate)
        assert 0 <= result.average_position <= 100

    def test_high_position(self):
        data = {"average_position": 90.0, "position_change": 3.0, "high_position_ratio": 60, "low_position_ratio": 5}
        result = self.estimator.estimate(data)
        assert result.average_position == 90.0
        assert result.trend == "加仓"

    def test_low_position(self):
        data = {"average_position": 55.0, "position_change": -5.0}
        result = self.estimator.estimate(data)
        assert result.trend == "减仓"


class TestMarketBreadthCalculator:
    def setup_method(self):
        self.calculator = MarketBreadthCalculator()

    def test_calculate_default(self):
        result = self.calculator.calculate()
        assert isinstance(result, MarketBreadthIndicator)

    def test_strong_breadth(self):
        data = {"advance_decline_ratio": 3.0, "new_high_low": 200, "up_volume_ratio": 70}
        result = self.calculator.calculate(data)
        assert result.breadth_level == MarketBreadth.STRONG

    def test_weak_breadth(self):
        data = {"advance_decline_ratio": 0.3, "new_high_low": -100, "up_volume_ratio": 30}
        result = self.calculator.calculate(data)
        assert result.breadth_level == MarketBreadth.WEAK


class TestSentimentAlertGenerator:
    def setup_method(self):
        self.generator = SentimentAlertGenerator()

    def test_extreme_greed_alert(self):
        fg = FearGreedIndex(85, SentimentLevel.EXTREME_GREED, [], 90, "", "", "")
        fp = FundPositionEstimate("股票型", 75, 1.0, 50, 10, "加仓")
        mb = MarketBreadthIndicator(1.5, 50, MarketBreadth.NORMAL, 55, "")
        alerts = self.generator.generate(fg, fp, mb)
        assert any(a.alert_type == "极度贪婪" for a in alerts)

    def test_extreme_fear_alert(self):
        fg = FearGreedIndex(10, SentimentLevel.EXTREME_FEAR, [], 5, "", "", "")
        fp = FundPositionEstimate("股票型", 65, -2.0, 30, 20, "减仓")
        mb = MarketBreadthIndicator(0.5, -50, MarketBreadth.WEAK, 35, "")
        alerts = self.generator.generate(fg, fp, mb)
        assert any(a.alert_type == "极度恐慌" for a in alerts)

    def test_normal_no_alert(self):
        fg = FearGreedIndex(50, SentimentLevel.NEUTRAL, [], 50, "", "", "")
        fp = FundPositionEstimate("股票型", 72, 0.5, 40, 15, "持平")
        mb = MarketBreadthIndicator(1.2, 30, MarketBreadth.NORMAL, 52, "")
        alerts = self.generator.generate(fg, fp, mb)
        assert all(a.level == "低" for a in alerts)


class TestMarketSentimentAnalyzer:
    def setup_method(self):
        self.analyzer = MarketSentimentAnalyzer()

    def test_analyze_default(self):
        report = self.analyzer.analyze()
        assert isinstance(report, MarketSentimentReport)
        assert report.fear_greed_index is not None
        assert report.fund_position is not None
        assert report.market_breadth is not None

    def test_alerts(self):
        report = self.analyzer.analyze()
        assert isinstance(report.alerts, list)
        assert len(report.alerts) > 0

    def test_timing_advice(self):
        report = self.analyzer.analyze()
        assert report.timing_advice != ""

    def test_format_report(self):
        report = self.analyzer.analyze()
        formatted = self.analyzer.format_report(report)
        assert "市场情绪综合报告" in formatted
        assert "恐慌贪婪指数" in formatted
        assert "基金仓位估算" in formatted
        assert "市场宽度" in formatted


class TestEnums:
    def test_sentiment_level(self):
        assert SentimentLevel.EXTREME_FEAR.value == "极度恐慌"
        assert SentimentLevel.FEAR.value == "恐慌"
        assert SentimentLevel.NEUTRAL.value == "中性"
        assert SentimentLevel.GREED.value == "贪婪"
        assert SentimentLevel.EXTREME_GREED.value == "极度贪婪"

    def test_market_breadth(self):
        assert MarketBreadth.STRONG.value == "强势"
        assert MarketBreadth.NORMAL.value == "正常"
        assert MarketBreadth.WEAK.value == "弱势"


def test_analyze_market_sentiment_convenience():
    report = analyze_market_sentiment()
    assert isinstance(report, MarketSentimentReport)
