"""用户画像模块测试"""

from fund_cli.ai.user_profile import (
    InvestmentGoal,
    InvestmentHorizon,
    InvestmentStyle,
    ProfileManager,
    RiskAssessment,
    RiskQuestionnaire,
    RiskTolerance,
    StyleAnalyzer,
    UserProfile,
    create_user_profile,
)


class TestRiskQuestionnaire:
    def setup_method(self):
        self.questionnaire = RiskQuestionnaire()

    def test_get_questions(self):
        questions = self.questionnaire.get_questions()
        assert len(questions) == 5
        assert all("id" in q and "question" in q and "options" in q for q in questions)

    def test_assess_conservative(self):
        answers = {"q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 0}
        result = self.questionnaire.assess(answers)
        assert isinstance(result, RiskAssessment)
        assert result.tolerance == RiskTolerance.CONSERVATIVE
        assert result.score <= 20

    def test_assess_aggressive(self):
        answers = {"q1": 4, "q2": 4, "q3": 4, "q4": 4, "q5": 4}
        result = self.questionnaire.assess(answers)
        assert result.tolerance == RiskTolerance.AGGRESSIVE
        assert result.score >= 80

    def test_assess_balanced(self):
        answers = {"q1": 2, "q2": 2, "q3": 2, "q4": 2, "q5": 2}
        result = self.questionnaire.assess(answers)
        assert result.tolerance == RiskTolerance.BALANCED
        assert 40 <= result.score <= 60


class TestStyleAnalyzer:
    def setup_method(self):
        self.analyzer = StyleAnalyzer()

    def test_analyze_default(self):
        result = self.analyzer.analyze()
        assert result == InvestmentStyle.BALANCED

    def test_analyze_momentum(self):
        behavior = {"avg_holding_days": 15, "turnover_rate": 3.0}
        result = self.analyzer.analyze(trading_behavior=behavior)
        assert result == InvestmentStyle.MOMENTUM

    def test_analyze_value(self):
        behavior = {"avg_holding_days": 400, "turnover_rate": 0.3}
        result = self.analyzer.analyze(trading_behavior=behavior)
        assert result == InvestmentStyle.VALUE

    def test_analyze_income(self):
        holdings = [{"fund_type": "债券型"}, {"fund_type": "货币型"}, {"fund_type": "债券型"}]
        result = self.analyzer.analyze(holding_history=holdings)
        assert result == InvestmentStyle.INCOME


class TestProfileManager:
    def setup_method(self):
        self.manager = ProfileManager()

    def test_create_profile(self):
        answers = {"q1": 2, "q2": 2, "q3": 2, "q4": 2, "q5": 2}
        profile = self.manager.create_profile(
            user_id="test001",
            name="测试用户",
            risk_answers=answers,
            investment_goal=InvestmentGoal.BALANCED_GROWTH,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
        )
        assert isinstance(profile, UserProfile)
        assert profile.user_id == "test001"
        assert profile.risk_assessment.tolerance == RiskTolerance.BALANCED

    def test_get_questionnaire(self):
        questions = self.manager.get_questionnaire()
        assert len(questions) == 5

    def test_assess_risk(self):
        answers = {"q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 0}
        result = self.manager.assess_risk(answers)
        assert isinstance(result, RiskAssessment)

    def test_format_profile(self):
        answers = {"q1": 2, "q2": 2, "q3": 2, "q4": 2, "q5": 2}
        profile = self.manager.create_profile(
            user_id="test001",
            name="测试用户",
            risk_answers=answers,
            investment_goal=InvestmentGoal.BALANCED_GROWTH,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
        )
        formatted = self.manager.format_profile(profile)
        assert "用户画像" in formatted
        assert "风险评估" in formatted


class TestEnums:
    def test_risk_tolerance(self):
        assert RiskTolerance.CONSERVATIVE.value == "保守型"
        assert RiskTolerance.AGGRESSIVE.value == "进取型"

    def test_investment_goal(self):
        assert InvestmentGoal.WEALTH_PRESERVATION.value == "资产保值"
        assert InvestmentGoal.AGGRESSIVE_GROWTH.value == "积极成长"

    def test_investment_horizon(self):
        assert InvestmentHorizon.SHORT_TERM.value == "短期（<1年）"
        assert InvestmentHorizon.LONG_TERM.value == "长期（3-10年）"

    def test_investment_style(self):
        assert InvestmentStyle.VALUE.value == "价值型"
        assert InvestmentStyle.GROWTH.value == "成长型"


def test_create_user_profile_convenience():
    answers = {"q1": 2, "q2": 2, "q3": 2, "q4": 2, "q5": 2}
    profile = create_user_profile(
        user_id="test001",
        name="测试用户",
        risk_answers=answers,
    )
    assert isinstance(profile, UserProfile)
