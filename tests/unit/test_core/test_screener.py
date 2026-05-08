"""基金筛选引擎测试"""

import pandas as pd
import pytest

from fund_cli.core.screener import FundScreener
from fund_cli.data.models import FundFilter


def mock_data():
    return pd.DataFrame(
        {
            "code": ["000001", "000002", "000003", "000004", "000005"],
            "name": ["基金A", "基金B", "基金C", "基金D", "基金E"],
            "type": ["股票型", "债券型", "股票型", "混合型", "股票型"],
            "manager": ["张三", "李四", "张三", "王五", "张三"],
            "scale": [50.0, 20.0, 100.0, 30.0, 80.0],
            "return_1y": [15.0, 3.0, 25.0, 8.0, -5.0],
            "max_drawdown": [-10.0, -3.0, -20.0, -8.0, -30.0],
            "sharpe_ratio": [1.5, 0.8, 2.0, 1.0, -0.5],
            "fee_rate": [1.5, 0.5, 1.2, 1.0, 1.8],
            "rating": [5, 3, 4, 4, 2],
        }
    )


class MockDM:
    def search_funds(self, **kwargs):
        return mock_data()


@pytest.fixture
def screener(tmp_path):
    s = FundScreener(data_manager=MockDM())
    s._template_dir = tmp_path
    return s


class TestFeeFilter:
    def test_fee_filter(self, screener):
        df = screener.screen_by_fee(1.0)
        assert len(df) == 2
        assert df.iloc[0]["code"] == "000002"

    def test_fee_filter_high(self, screener):
        df = screener.screen_by_fee(2.0)
        assert len(df) == 5


class TestManagerFilter:
    def test_manager_filter(self, screener):
        df = screener.screen_by_manager("张三")
        assert len(df) == 3

    def test_manager_not_found(self, screener):
        df = screener.screen_by_manager("赵六")
        assert len(df) == 0


class TestRatingFilter:
    def test_rating_filter(self, screener):
        df = screener.screen_by_rating(4)
        assert len(df) == 3

    def test_rating_filter_5(self, screener):
        df = screener.screen_by_rating(5)
        assert len(df) == 1


class TestAdvancedExpression:
    def test_simple_expression(self, screener):
        df = screener.evaluate_expression(mock_data(), "return_1y > 10")
        assert len(df) == 2

    def test_and_expression(self, screener):
        df = screener.evaluate_expression(mock_data(), "return_1y > 5 and sharpe_ratio > 1.0")
        assert len(df) == 2

    def test_or_expression(self, screener):
        df = screener.evaluate_expression(mock_data(), "type == '债券型' or type == '混合型'")
        assert len(df) == 2

    def test_dangerous_expression(self, screener):
        with pytest.raises(ValueError, match="不允许"):
            screener.evaluate_expression(mock_data(), "__import__('os')")


class TestTemplateManagement:
    def test_save_and_load(self, screener, tmp_path):
        f = FundFilter(min_return_1y=10.0)
        screener.save_template("test_template", f)
        loaded = screener.load_template("test_template")
        assert loaded.min_return_1y == 10.0

    def test_list_templates(self, screener):
        screener.save_template("t1", FundFilter())
        screener.save_template("t2", FundFilter())
        templates = screener.list_templates()
        assert "t1" in templates
        assert "t2" in templates

    def test_delete_template(self, screener):
        screener.save_template("temp", FundFilter())
        assert screener.delete_template("temp") is True
        assert screener.delete_template("temp") is False

    def test_load_nonexistent(self, screener):
        with pytest.raises(FileNotFoundError):
            screener.load_template("nonexistent")


class TestScreen:
    def test_combined_filter(self, screener):
        f = FundFilter(min_return_1y=5.0, min_sharpe=1.0)
        df = screener.screen(f)
        assert len(df) == 3

    def test_empty_result(self, screener):
        f = FundFilter(min_return_1y=100.0)
        df = screener.screen(f)
        assert len(df) == 0
