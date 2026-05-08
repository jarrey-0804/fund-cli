"""持仓分析引擎测试"""

import pandas as pd
import pytest

from fund_cli.analysis.holding import HoldingAnalyzer


@pytest.fixture
def analyzer():
    return HoldingAnalyzer()


@pytest.fixture
def sample_holdings():
    return pd.DataFrame(
        {
            "stock_code": [
                "600519",
                "000858",
                "601318",
                "600036",
                "000333",
                "601166",
                "000651",
                "600887",
                "002714",
                "601888",
            ],
            "stock_name": [
                "贵州茅台",
                "五粮液",
                "中国平安",
                "招商银行",
                "美的集团",
                "兴业银行",
                "格力电器",
                "伊利股份",
                "牧原股份",
                "中国中免",
            ],
            "weight": [9.5, 7.2, 6.8, 5.5, 4.3, 3.8, 3.5, 3.2, 2.8, 2.5],
            "market_value": [50000, 38000, 36000, 29000, 22000, 20000, 18000, 17000, 15000, 13000],
            "industry": [
                "食品饮料",
                "食品饮料",
                "非银金融",
                "银行",
                "家用电器",
                "银行",
                "家用电器",
                "食品饮料",
                "农林牧渔",
                "商贸零售",
            ],
        }
    )


class TestIndustryDistribution:
    def test_normal_data(self, analyzer, sample_holdings):
        result = analyzer.industry_distribution(sample_holdings)
        assert "食品饮料" in result
        assert result["食品饮料"] == pytest.approx(9.5 + 7.2 + 3.2, abs=0.01)

    def test_empty_data(self, analyzer):
        with pytest.raises(ValueError):
            analyzer.industry_distribution(pd.DataFrame())

    def test_missing_industry_column(self, analyzer):
        df = pd.DataFrame({"stock_code": ["600519"], "weight": [9.5]})
        with pytest.raises(ValueError):
            analyzer.industry_distribution(df)

    def test_single_industry(self, analyzer):
        df = pd.DataFrame({"industry": ["银行"] * 5, "weight": [10, 8, 6, 4, 2]})
        result = analyzer.industry_distribution(df)
        assert len(result) == 1
        assert result["银行"] == 30.0


class TestTopHoldings:
    def test_top_n(self, analyzer, sample_holdings):
        top = analyzer.top_holdings(sample_holdings, top_n=5)
        assert len(top) == 5
        assert top.iloc[0]["stock_code"] == "600519"

    def test_top_n_exceeds_data(self, analyzer, sample_holdings):
        top = analyzer.top_holdings(sample_holdings, top_n=20)
        assert len(top) == 10

    def test_empty_data(self, analyzer):
        top = analyzer.top_holdings(pd.DataFrame(), top_n=5)
        assert len(top) == 0


class TestConcentrationHHI:
    def test_equal_weight(self, analyzer):
        df = pd.DataFrame({"weight": [10.0] * 10})
        hhi = analyzer.concentration_hhi(df)
        expected = 10 * (0.1**2)
        assert hhi == pytest.approx(expected, abs=0.001)

    def test_concentrated(self, analyzer):
        df = pd.DataFrame({"weight": [50.0, 10.0, 10.0, 10.0, 10.0, 10.0]})
        hhi = analyzer.concentration_hhi(df)
        assert hhi > 0.25  # 高度集中

    def test_single_stock(self, analyzer):
        df = pd.DataFrame({"weight": [100.0]})
        hhi = analyzer.concentration_hhi(df)
        assert hhi == pytest.approx(1.0)

    def test_empty_data(self, analyzer):
        assert analyzer.concentration_hhi(pd.DataFrame()) == 0.0

    def test_missing_weight_column(self, analyzer):
        assert analyzer.concentration_hhi(pd.DataFrame({"stock_code": ["600519"]})) == 0.0


class TestTrackChanges:
    def test_new_stock(self, analyzer):
        curr = pd.DataFrame({"stock_code": ["600519"], "stock_name": ["贵州茅台"], "weight": [9.5]})
        prev = pd.DataFrame({"stock_code": ["000858"], "weight": [7.2]})
        result = analyzer.track_changes(curr, prev)
        assert "新增" in result["change_type"].values

    def test_removed_stock(self, analyzer):
        curr = pd.DataFrame({"stock_code": ["000858"], "stock_name": ["五粮液"], "weight": [7.2]})
        prev = pd.DataFrame({"stock_code": ["600519"], "weight": [9.5]})
        result = analyzer.track_changes(curr, prev)
        assert "删除" in result["change_type"].values

    def test_increased(self, analyzer):
        curr = pd.DataFrame(
            {"stock_code": ["600519"], "stock_name": ["贵州茅台"], "weight": [12.0]}
        )
        prev = pd.DataFrame({"stock_code": ["600519"], "weight": [9.5]})
        result = analyzer.track_changes(curr, prev)
        assert result.iloc[0]["change_type"] == "增持"

    def test_decreased(self, analyzer):
        curr = pd.DataFrame({"stock_code": ["600519"], "stock_name": ["贵州茅台"], "weight": [7.0]})
        prev = pd.DataFrame({"stock_code": ["600519"], "weight": [9.5]})
        result = analyzer.track_changes(curr, prev)
        assert result.iloc[0]["change_type"] == "减持"

    def test_unchanged(self, analyzer):
        curr = pd.DataFrame({"stock_code": ["600519"], "stock_name": ["贵州茅台"], "weight": [9.5]})
        prev = pd.DataFrame({"stock_code": ["600519"], "weight": [9.5]})
        result = analyzer.track_changes(curr, prev)
        assert result.iloc[0]["change_type"] == "不变"

    def test_empty_data(self, analyzer):
        result = analyzer.track_changes(pd.DataFrame(), pd.DataFrame())
        assert len(result) == 0


class TestStyleAnalysis:
    def test_large_cap_value(self, analyzer):
        df = pd.DataFrame(
            {
                "stock_code": ["600036", "601398", "601288", "601939", "600016"],
                "weight": [20, 20, 20, 20, 20],
                "industry": ["银行", "银行", "银行", "银行", "银行"],
            }
        )
        result = analyzer.style_analysis(df)
        assert result["market_cap_style"] == "大盘"
        assert result["investment_style"] == "价值"

    def test_small_cap_growth(self, analyzer):
        df = pd.DataFrame(
            {
                "stock_code": ["300001", "300002", "300003", "300004", "300005"],
                "weight": [20, 20, 20, 20, 20],
                "industry": ["计算机", "传媒", "通信", "电子", "国防军工"],
            }
        )
        result = analyzer.style_analysis(df)
        assert result["market_cap_style"] == "小盘"
        assert result["investment_style"] == "成长"

    def test_missing_industry(self, analyzer):
        df = pd.DataFrame({"stock_code": ["600519"], "weight": [9.5]})
        result = analyzer.style_analysis(df)
        assert result["market_cap_style"] == "未知"


class TestAnalyze:
    def test_full_analysis(self, analyzer, sample_holdings):
        result = analyzer.analyze(sample_holdings)
        assert "industry_distribution" in result
        assert "top_holdings" in result
        assert "concentration_hhi" in result
        assert "concentration_level" in result
        assert "style_analysis" in result

    def test_without_industry(self, analyzer):
        df = pd.DataFrame({"stock_code": ["600519"], "weight": [9.5]})
        result = analyzer.analyze(df)
        assert "style_analysis" not in result
        assert "industry_distribution" not in result


class TestGetMetrics:
    def test_metrics_list(self, analyzer):
        metrics = analyzer.get_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) >= 5
