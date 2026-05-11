"""个性化推荐引擎测试"""

import pytest
from fund_cli.ai.recommender import (
    FundRecommender,
    ContentBasedRecommender,
    CollaborativeRecommender,
    HybridRecommender,
    FundScore,
    RecommendationItem,
    RecommendationReport,
    RecommendationType,
    recommend_funds,
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
            preferred_fund_types=["混合型", "股票型"],
            preferred_sectors=["消费", "医药"],
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


class TestContentBasedRecommender:
    def setup_method(self):
        self.recommender = ContentBasedRecommender()

    def test_recommend_default(self, sample_profile):
        scores = self.recommender.recommend(sample_profile)
        assert isinstance(scores, list)
        assert len(scores) > 0
        assert all(isinstance(s, FundScore) for s in scores)

    def test_scores_sorted(self, sample_profile):
        scores = self.recommender.recommend(sample_profile)
        for i in range(len(scores) - 1):
            assert scores[i].overall_score >= scores[i + 1].overall_score

    def test_fund_score_structure(self, sample_profile):
        scores = self.recommender.recommend(sample_profile)
        score = scores[0]
        assert hasattr(score, "fund_code")
        assert hasattr(score, "fund_name")
        assert hasattr(score, "overall_score")
        assert hasattr(score, "detail_scores")


class TestCollaborativeRecommender:
    def setup_method(self):
        self.recommender = CollaborativeRecommender()

    def test_recommend_default(self):
        result = self.recommender.recommend("test001")
        assert isinstance(result, list)
        assert len(result) > 0


class TestHybridRecommender:
    def setup_method(self):
        self.recommender = HybridRecommender()

    def test_recommend(self, sample_profile):
        result = self.recommender.recommend(sample_profile)
        assert isinstance(result, list)
        assert all(isinstance(r, RecommendationItem) for r in result)

    def test_recommendation_item_structure(self, sample_profile):
        result = self.recommender.recommend(sample_profile)
        item = result[0]
        assert hasattr(item, "fund_code")
        assert hasattr(item, "score")
        assert hasattr(item, "recommendation_reason")
        assert hasattr(item, "risk_warning")


class TestFundRecommender:
    def setup_method(self):
        self.recommender = FundRecommender()

    def test_recommend(self, sample_profile):
        report = self.recommender.recommend(sample_profile)
        assert isinstance(report, RecommendationReport)
        assert report.user_id == sample_profile.user_id

    def test_recommend_similar(self):
        result = self.recommender.recommend_similar("000001")
        assert isinstance(result, list)
        assert all(r.recommendation_type == RecommendationType.SIMILAR for r in result)

    def test_recommend_alternative(self):
        result = self.recommender.recommend_alternative("000001")
        assert isinstance(result, list)
        assert all(r.recommendation_type == RecommendationType.ALTERNATIVE for r in result)

    def test_format_report(self, sample_profile):
        report = self.recommender.recommend(sample_profile)
        formatted = self.recommender.format_report(report)
        assert "基金推荐报告" in formatted


class TestEnums:
    def test_recommendation_type(self):
        assert RecommendationType.SIMILAR.value == "相似基金"
        assert RecommendationType.ALTERNATIVE.value == "替代基金"
        assert RecommendationType.RISK_MATCHED.value == "风险匹配"


def test_recommend_funds_convenience(sample_profile):
    report = recommend_funds(sample_profile)
    assert isinstance(report, RecommendationReport)
