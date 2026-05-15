"""
智能选基助手测试
"""

from unittest.mock import MagicMock, patch

from fund_cli.ai.fund_selector import (
    FundRecommendation,
    FundScorer,
    FundSelector,
    InvestmentNeed,
    InvestmentStyle,
    NeedParser,
    RecommendationGenerator,
    RiskLevel,
    select_funds,
)
from fund_cli.data.models import FundType


class TestNeedParser:
    """需求解析器测试"""

    def setup_method(self):
        self.parser = NeedParser()

    def test_parse_fund_type_equity(self):
        """测试解析股票型基金"""
        need = self.parser.parse("我想找一只股票型基金")
        assert need.fund_type == FundType.EQUITY

    def test_parse_fund_type_bond(self):
        """测试解析债券型基金"""
        need = self.parser.parse("推荐一些债券基金")
        assert need.fund_type == FundType.BOND

    def test_parse_fund_type_index(self):
        """测试解析指数型基金"""
        need = self.parser.parse("我想买指数基金或ETF")
        assert need.fund_type == FundType.INDEX

    def test_parse_return_target(self):
        """测试解析收益目标"""
        need = self.parser.parse("年化收益10%以上")
        assert need.min_return == 10.0

    def test_parse_max_drawdown(self):
        """测试解析最大回撤约束"""
        need = self.parser.parse("最大回撤不超过20%")
        assert need.max_drawdown == -20.0

    def test_parse_scale(self):
        """测试解析规模约束"""
        need = self.parser.parse("规模50亿以上")
        assert need.min_scale == 50.0

    def test_parse_risk_level_conservative(self):
        """测试解析保守型风险偏好"""
        need = self.parser.parse("我是保守型投资者，想要低风险产品")
        assert need.risk_level == RiskLevel.CONSERVATIVE

    def test_parse_risk_level_aggressive(self):
        """测试解析激进型风险偏好"""
        need = self.parser.parse("我是激进型投资者，追求高收益")
        assert need.risk_level == RiskLevel.AGGRESSIVE

    def test_parse_style_value(self):
        """测试解析价值风格"""
        need = self.parser.parse("我偏好价值投资风格")
        assert need.style == InvestmentStyle.VALUE

    def test_parse_complex_query(self):
        """测试解析复杂查询"""
        need = self.parser.parse("稳健的股票型基金，年化收益10%以上，最大回撤不超过20%，规模50亿以上")
        assert need.fund_type == FundType.EQUITY
        assert need.min_return == 10.0
        assert need.max_drawdown == -20.0
        assert need.min_scale == 50.0


class TestFundScorer:
    """基金评分器测试"""

    def setup_method(self):
        self.scorer = FundScorer()

    def test_score_empty_dataframe(self):
        """测试空数据评分"""
        import pandas as pd

        df = pd.DataFrame()
        need = InvestmentNeed()
        result = self.scorer.score(df, need)
        assert result.empty

    def test_score_with_data(self):
        """测试有数据评分"""
        import pandas as pd

        df = pd.DataFrame(
            {
                "code": ["000001", "000002"],
                "name": ["基金A", "基金B"],
                "return_1y": [15.0, 10.0],
                "max_drawdown": [-10.0, -15.0],
                "sharpe_ratio": [1.5, 1.0],
                "scale": [50.0, 30.0],
            }
        )
        need = InvestmentNeed()
        result = self.scorer.score(df, need)
        assert "score" in result.columns
        assert len(result) == 2

    def test_score_with_risk_level(self):
        """测试不同风险偏好的评分权重"""
        import pandas as pd

        df = pd.DataFrame(
            {
                "code": ["000001"],
                "name": ["基金A"],
                "return_1y": [15.0],
                "max_drawdown": [-10.0],
                "sharpe_ratio": [1.5],
                "scale": [50.0],
            }
        )

        # 保守型
        need_conservative = InvestmentNeed(risk_level=RiskLevel.CONSERVATIVE)
        result_c = self.scorer.score(df, need_conservative)
        assert "score" in result_c.columns

        # 激进型
        need_aggressive = InvestmentNeed(risk_level=RiskLevel.AGGRESSIVE)
        result_a = self.scorer.score(df, need_aggressive)
        assert "score" in result_a.columns


class TestRecommendationGenerator:
    """推荐理由生成器测试"""

    def setup_method(self):
        self.generator = RecommendationGenerator()

    def test_generate_excellent_fund(self):
        """测试优秀基金推荐"""
        fund_info = {
            "name": "优秀基金",
            "type": "股票型",
            "return_1y": 25.0,
            "max_drawdown": -8.0,
            "sharpe_ratio": 2.5,
            "scale": 50.0,
        }
        need = InvestmentNeed(fund_type=FundType.EQUITY)
        reason, warning = self.generator.generate(fund_info, need, 0.9, 1)

        assert "第1位" in reason
        assert "收益" in reason or "表现" in reason

    def test_generate_poor_fund(self):
        """测试表现不佳基金推荐"""
        fund_info = {
            "name": "表现不佳基金",
            "type": "股票型",
            "return_1y": -5.0,
            "max_drawdown": -35.0,
            "sharpe_ratio": 0.3,
            "scale": 3.0,
        }
        need = InvestmentNeed()
        reason, warning = self.generator.generate(fund_info, need, 0.3, 10)

        assert "风险" in warning or "波动" in warning


class TestFundSelector:
    """智能选基助手测试"""

    def test_select_with_mock_data(self):
        """测试选基功能（模拟数据）"""
        with patch("fund_cli.ai.fund_selector.DataManager") as mock_dm:
            mock_instance = MagicMock()
            mock_dm.return_value = mock_instance

            # 模拟返回空数据
            mock_instance.search_funds.return_value = MagicMock(empty=True)

            selector = FundSelector()
            result = selector.select("股票型基金", top_n=5)

            assert isinstance(result, list)


class TestFundRecommendation:
    """基金推荐结果测试"""

    def test_recommendation_creation(self):
        """测试推荐结果创建"""
        rec = FundRecommendation(
            fund_code="000001",
            fund_name="测试基金",
            fund_type="股票型",
            score=0.85,
            rank=1,
            recommendation_reason="表现优秀",
            risk_warning="市场有风险",
            key_metrics={"return_1y": 15.0, "max_drawdown": -10.0},
        )

        assert rec.fund_code == "000001"
        assert rec.score == 0.85
        assert rec.rank == 1


class TestInvestmentNeed:
    """投资需求测试"""

    def test_need_defaults(self):
        """测试默认值"""
        need = InvestmentNeed()
        assert need.fund_type is None
        assert need.min_return is None
        assert need.max_drawdown is None
        assert need.keywords == []

    def test_need_with_values(self):
        """测试带值创建"""
        need = InvestmentNeed(
            fund_type=FundType.EQUITY,
            min_return=10.0,
            max_drawdown=-20.0,
            risk_level=RiskLevel.MODERATE,
        )

        assert need.fund_type == FundType.EQUITY
        assert need.min_return == 10.0
        assert need.risk_level == RiskLevel.MODERATE


def test_select_funds_convenience_function():
    """测试便捷函数"""
    with patch("fund_cli.ai.fund_selector.FundSelector") as mock_selector:
        mock_instance = MagicMock()
        mock_selector.return_value = mock_instance
        mock_instance.select.return_value = []

        result = select_funds("测试查询")
        assert result == []
