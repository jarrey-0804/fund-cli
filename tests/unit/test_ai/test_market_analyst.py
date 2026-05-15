"""
市场解读助手模块测试
"""


from fund_cli.ai.market_analyst import (
    HotspotItem,
    HotspotReport,
    HotspotTracker,
    MarketAnalyst,
    MarketSentiment,
    MarketSentimentReport,
    SectorRotationAnalyzer,
    SectorRotationItem,
    SectorRotationReport,
    SectorStrength,
    SentimentAnalyzer,
    SentimentIndicator,
    analyze_market_sentiment,
    analyze_sector_rotation,
    track_market_hotspots,
)


class TestSentimentAnalyzer:
    """市场情绪分析器测试"""

    def setup_method(self):
        self.analyzer = SentimentAnalyzer()

    def test_analyze_default(self):
        """测试默认分析"""
        report = self.analyzer.analyze()
        assert isinstance(report, MarketSentimentReport)
        assert 0 <= report.sentiment_index <= 100
        assert report.sentiment_level in list(MarketSentiment)

    def test_analyze_with_market_data(self):
        """测试带市场数据分析"""
        market_data = {
            "advance_decline_ratio": 1.5,
            "volatility": 20.0,
            "volume_ratio": 1.2,
        }
        fund_flow_data = {"net_inflow": 50.0}

        report = self.analyzer.analyze(market_data, fund_flow_data)
        assert isinstance(report, MarketSentimentReport)
        assert len(report.indicators) == 4

    def test_sentiment_levels(self):
        """测试情绪等级"""
        # 极度贪婪
        market_data = {
            "advance_decline_ratio": 3.0,
            "volatility": 5.0,
            "volume_ratio": 2.0,
        }
        fund_flow_data = {"net_inflow": 200.0}
        report = self.analyzer.analyze(market_data, fund_flow_data)
        # 应该偏向贪婪
        assert report.sentiment_index >= 50

    def test_interpretation_generation(self):
        """测试解读生成"""
        report = self.analyzer.analyze()
        assert report.interpretation != ""
        assert report.investment_advice != ""
        assert report.risk_warning != ""


class TestSectorRotationAnalyzer:
    """行业轮动分析器测试"""

    def setup_method(self):
        self.analyzer = SectorRotationAnalyzer()

    def test_analyze_default(self):
        """测试默认分析"""
        report = self.analyzer.analyze()
        assert isinstance(report, SectorRotationReport)
        assert isinstance(report.strong_sectors, list)
        assert isinstance(report.weak_sectors, list)

    def test_analyze_with_custom_returns(self):
        """测试自定义收益率分析"""
        sector_returns = {
            "计算机": 15.0,
            "电子": 12.0,
            "医药生物": 8.0,
            "银行": -5.0,
            "房地产": -10.0,
        }
        report = self.analyzer.analyze(sector_returns)
        assert len(report.strong_sectors) > 0 or len(report.weak_sectors) > 0

    def test_rotation_signals(self):
        """测试轮动信号"""
        sector_returns = {
            "计算机": 15.0,
            "银行": -8.0,
        }
        report = self.analyzer.analyze(sector_returns)
        assert isinstance(report.rotation_signals, list)

    def test_investment_advice(self):
        """测试投资建议"""
        report = self.analyzer.analyze()
        assert report.investment_advice != ""


class TestHotspotTracker:
    """热点追踪器测试"""

    def setup_method(self):
        self.tracker = HotspotTracker()

    def test_track_default(self):
        """测试默认追踪"""
        report = self.tracker.track()
        assert isinstance(report, HotspotReport)
        assert isinstance(report.hotspots, list)
        assert len(report.hotspots) > 0

    def test_track_with_custom_data(self):
        """测试自定义热点数据"""
        hotspot_data = [
            {"name": "人工智能", "type": "主题", "heat_score": 95, "related_funds": ["AI ETF"], "reason": "技术突破"},
            {"name": "新能源", "type": "行业", "heat_score": 85, "related_funds": ["新能源基金"], "reason": "政策支持"},
        ]
        report = self.tracker.track(hotspot_data)
        assert len(report.hotspots) == 2
        assert report.hotspots[0].name == "人工智能"

    def test_hotspot_sorting(self):
        """测试热点排序"""
        hotspot_data = [
            {"name": "低热度", "type": "主题", "heat_score": 50, "related_funds": [], "reason": ""},
            {"name": "高热度", "type": "主题", "heat_score": 90, "related_funds": [], "reason": ""},
        ]
        report = self.tracker.track(hotspot_data)
        # 按热度降序排列
        assert report.hotspots[0].heat_score >= report.hotspots[1].heat_score


class TestMarketAnalyst:
    """市场解读助手测试"""

    def setup_method(self):
        self.analyst = MarketAnalyst()

    def test_analyze_sentiment(self):
        """测试情绪分析"""
        report = self.analyst.analyze_sentiment()
        assert isinstance(report, MarketSentimentReport)

    def test_analyze_sector_rotation(self):
        """测试行业轮动分析"""
        report = self.analyst.analyze_sector_rotation()
        assert isinstance(report, SectorRotationReport)

    def test_track_hotspots(self):
        """测试热点追踪"""
        report = self.analyst.track_hotspots()
        assert isinstance(report, HotspotReport)

    def test_format_sentiment_report(self):
        """测试情绪报告格式化"""
        report = self.analyst.analyze_sentiment()
        formatted = self.analyst.format_sentiment_report(report)
        assert "市场情绪分析报告" in formatted
        assert "情绪指数" in formatted

    def test_format_sector_report(self):
        """测试行业轮动报告格式化"""
        report = self.analyst.analyze_sector_rotation()
        formatted = self.analyst.format_sector_report(report)
        assert "行业轮动分析报告" in formatted

    def test_format_hotspot_report(self):
        """测试热点报告格式化"""
        report = self.analyst.track_hotspots()
        formatted = self.analyst.format_hotspot_report(report)
        assert "市场热点追踪报告" in formatted


class TestMarketSentimentReport:
    """市场情绪报告测试"""

    def test_report_creation(self):
        """测试报告创建"""
        report = MarketSentimentReport(
            sentiment_index=65.0,
            sentiment_level=MarketSentiment.GREED,
            indicators=[
                SentimentIndicator(
                    name="涨跌比",
                    value=1.5,
                    weight=0.25,
                    contribution=16.25,
                    description="上涨下跌比1.50",
                )
            ],
            interpretation="市场情绪偏乐观",
            investment_advice="建议控制仓位",
            risk_warning="注意追高风险",
        )

        assert report.sentiment_index == 65.0
        assert report.sentiment_level == MarketSentiment.GREED
        assert len(report.indicators) == 1


class TestSectorRotationItem:
    """行业轮动项测试"""

    def test_item_creation(self):
        """测试轮动项创建"""
        item = SectorRotationItem(
            sector_name="计算机",
            strength=SectorStrength.STRONG,
            momentum=15.0,
            rank=1,
            trend="上升",
            recommendation="建议关注",
        )

        assert item.sector_name == "计算机"
        assert item.strength == SectorStrength.STRONG
        assert item.momentum == 15.0


class TestHotspotItem:
    """热点项测试"""

    def test_item_creation(self):
        """测试热点项创建"""
        item = HotspotItem(
            name="人工智能",
            type="主题",
            heat_score=95,
            related_funds=["AI ETF", "科技基金"],
            reason="技术突破+政策支持",
        )

        assert item.name == "人工智能"
        assert item.heat_score == 95
        assert len(item.related_funds) == 2


class TestMarketSentiment:
    """市场情绪枚举测试"""

    def test_sentiment_values(self):
        """测试情绪枚举值"""
        assert MarketSentiment.EXTREME_FEAR.value == "极度恐慌"
        assert MarketSentiment.FEAR.value == "恐慌"
        assert MarketSentiment.NEUTRAL.value == "中性"
        assert MarketSentiment.GREED.value == "贪婪"
        assert MarketSentiment.EXTREME_GREED.value == "极度贪婪"


class TestSectorStrength:
    """行业强度枚举测试"""

    def test_strength_values(self):
        """测试强度枚举值"""
        assert SectorStrength.STRONG.value == "强势"
        assert SectorStrength.MODERATE.value == "中等"
        assert SectorStrength.WEAK.value == "弱势"


def test_analyze_market_sentiment_convenience():
    """测试情绪分析便捷函数"""
    report = analyze_market_sentiment()
    assert isinstance(report, MarketSentimentReport)


def test_analyze_sector_rotation_convenience():
    """测试行业轮动便捷函数"""
    report = analyze_sector_rotation()
    assert isinstance(report, SectorRotationReport)


def test_track_market_hotspots_convenience():
    """测试热点追踪便捷函数"""
    report = track_market_hotspots()
    assert isinstance(report, HotspotReport)
