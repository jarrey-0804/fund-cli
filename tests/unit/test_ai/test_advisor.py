"""投资建议生成器测试"""

import pytest
from fund_cli.ai.advisor import (
    InvestmentAdvisor,
    HoldingAnalyzer,
    RebalanceAdvisor,
    DCAAdvisor,
    RiskAlerter,
    AdviceItem,
    RebalanceSuggestion,
    DCASuggestion,
    InvestmentAdviceReport,
    AdviceType,
    Priority,
    generate_investment_advice,
)
from fund_cli.ai.user_profile import (
    UserProfile,
    RiskAssessment,
    InvestmentPreferences,
    RiskTolerance,
    InvestmentGoal,
    InvestmentHorizon,
    InvestmentStyle,
)


@pytest.fixture
def sample_profile():
    return UserProfile(
        user_id="test001",
        name="测试用户",
        risk_assessment=RiskAssessment(
            score=50,
            tolerance=RiskTolerance.BALANCED,
            max_drawdown_acceptable=-15,
            volatility_preference="中等波动",
        ),
        investment_goal=InvestmentGoal.BALANCED_GROWTH,
        investment_horizon=InvestmentHorizon.MEDIUM_TERM,
        investment_style=InvestmentStyle.BALANCED,
        preferences=InvestmentPreferences(
            preferred_fund_types=["混合型"],
            preferred_sectors=["消费"],
            excluded_sectors=[],
            min_fund_scale=10,
            max_fund_scale=500,
            preferred_managers=[],
            esg_preference=False,
        ),
        total_assets=100,
        experience_years=3,
        created_at="2024-01-01",
        updated_at="2024-01-01",
    )


class TestHoldingAnalyzer:
    def setup_method(self):
        self.analyzer = HoldingAnalyzer()

    def test_analyze_empty_holdings(self, sample_profile):
        advices = self.analyzer.analyze([], sample_profile)
        assert len(advices) == 1
        assert advices[0].advice_type == AdviceType.HOLDING

    def test_analyze_concentrated_holdings(self, sample_profile):
        holdings = [
            {"fund_code": "000001", "fund_name": "基金A", "value": 800, "fund_type": "股票型"},
            {"fund_code": "000002", "fund_name": "基金B", "value": 200, "fund_type": "债券型"},
        ]
        advices = self.analyzer.analyze(holdings, sample_profile)
        assert any(a.advice_type == AdviceType.RISK_ALERT for a in advices)

    def test_analyze_risk_mismatch(self):
        conservative_profile = UserProfile(
            user_id="test002",
            name="保守用户",
            risk_assessment=RiskAssessment(
                score=15,
                tolerance=RiskTolerance.CONSERVATIVE,
                max_drawdown_acceptable=-5,
                volatility_preference="低波动",
            ),
            investment_goal=InvestmentGoal.WEALTH_PRESERVATION,
            investment_horizon=InvestmentHorizon.SHORT_TERM,
            investment_style=InvestmentStyle.INCOME,
            preferences=InvestmentPreferences(
                preferred_fund_types=["债券型"],
                preferred_sectors=[],
                excluded_sectors=[],
                min_fund_scale=10,
                max_fund_scale=500,
                preferred_managers=[],
                esg_preference=False,
            ),
            total_assets=100,
            experience_years=1,
            created_at="2024-01-01",
            updated_at="2024-01-01",
        )
        holdings = [
            {"fund_code": "000001", "fund_name": "股票基金", "value": 500, "fund_type": "股票型"},
        ]
        advices = self.analyzer.analyze(holdings, conservative_profile)
        assert any("风险偏高" in a.title for a in advices)


class TestRebalanceAdvisor:
    def setup_method(self):
        self.advisor = RebalanceAdvisor()

    def test_suggest_empty_holdings(self, sample_profile):
        suggestions = self.advisor.suggest([], sample_profile)
        assert len(suggestions) == 0

    def test_suggest_with_holdings(self, sample_profile):
        holdings = [
            {"fund_code": "000001", "fund_name": "基金A", "value": 500},
            {"fund_code": "000002", "fund_name": "基金B", "value": 500},
        ]
        suggestions = self.advisor.suggest(holdings, sample_profile)
        assert isinstance(suggestions, list)


class TestDCAAdvisor:
    def setup_method(self):
        self.advisor = DCAAdvisor()

    def test_suggest_default(self, sample_profile):
        suggestions = self.advisor.suggest(sample_profile)
        assert isinstance(suggestions, list)
        assert all(isinstance(s, DCASuggestion) for s in suggestions)

    def test_suggest_conservative(self):
        conservative_profile = UserProfile(
            user_id="test002",
            name="保守用户",
            risk_assessment=RiskAssessment(
                score=15,
                tolerance=RiskTolerance.CONSERVATIVE,
                max_drawdown_acceptable=-5,
                volatility_preference="低波动",
            ),
            investment_goal=InvestmentGoal.WEALTH_PRESERVATION,
            investment_horizon=InvestmentHorizon.SHORT_TERM,
            investment_style=InvestmentStyle.INCOME,
            preferences=InvestmentPreferences(
                preferred_fund_types=["债券型"],
                preferred_sectors=[],
                excluded_sectors=[],
                min_fund_scale=10,
                max_fund_scale=500,
                preferred_managers=[],
                esg_preference=False,
            ),
            total_assets=100,
            experience_years=1,
            created_at="2024-01-01",
            updated_at="2024-01-01",
        )
        suggestions = self.advisor.suggest(conservative_profile)
        assert all("债券" in s.fund_name or "货币" in s.fund_name for s in suggestions)


class TestRiskAlerter:
    def setup_method(self):
        self.alerter = RiskAlerter()

    def test_check_empty_holdings(self, sample_profile):
        warnings = self.alerter.check([], sample_profile)
        assert len(warnings) > 0

    def test_check_concentrated_holdings(self, sample_profile):
        holdings = [
            {"fund_code": "000001", "fund_name": "基金A", "value": 800},
            {"fund_code": "000002", "fund_name": "基金B", "value": 200},
        ]
        warnings = self.alerter.check(holdings, sample_profile)
        assert any("集中度" in w for w in warnings)

    def test_check_market_risk(self, sample_profile):
        market_data = {"sentiment": "极度贪婪"}
        warnings = self.alerter.check([], sample_profile, market_data)
        assert any("过热" in w for w in warnings)


class TestInvestmentAdvisor:
    def setup_method(self):
        self.advisor = InvestmentAdvisor()

    def test_advise_empty_holdings(self, sample_profile):
        report = self.advisor.advise(sample_profile)
        assert isinstance(report, InvestmentAdviceReport)
        assert report.user_id == sample_profile.user_id

    def test_advise_with_holdings(self, sample_profile):
        holdings = [
            {"fund_code": "000001", "fund_name": "基金A", "value": 500, "fund_type": "混合型"},
            {"fund_code": "000002", "fund_name": "基金B", "value": 500, "fund_type": "债券型"},
        ]
        report = self.advisor.advise(sample_profile, holdings)
        assert isinstance(report, InvestmentAdviceReport)
        assert len(report.risk_warnings) > 0

    def test_format_report(self, sample_profile):
        report = self.advisor.advise(sample_profile)
        formatted = self.advisor.format_report(report)
        assert "投资建议报告" in formatted
        assert "综合建议" in formatted


class TestEnums:
    def test_advice_type(self):
        assert AdviceType.HOLDING.value == "持仓建议"
        assert AdviceType.REBALANCE.value == "调仓建议"
        assert AdviceType.DCA.value == "定投建议"

    def test_priority(self):
        assert Priority.HIGH.value == "高"
        assert Priority.MEDIUM.value == "中"
        assert Priority.LOW.value == "低"


def test_generate_investment_advice_convenience(sample_profile):
    report = generate_investment_advice(sample_profile)
    assert isinstance(report, InvestmentAdviceReport)
