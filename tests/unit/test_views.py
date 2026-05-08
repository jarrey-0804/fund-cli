"""
单元测试 - 视图层
"""

import numpy as np
import pandas as pd
import pytest

from fund_cli.views.charts import ChartRenderer
from fund_cli.views.reports import ReportRenderer
from fund_cli.views.tables import TableRenderer


class TestTableRenderer:
    """表格渲染器测试"""

    @pytest.fixture
    def renderer(self):
        return TableRenderer()

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame(
            {
                "code": ["000001", "000002", "000003"],
                "name": ["华夏成长", "易方达策略", "嘉实增长"],
                "type": ["混合型", "混合型", "股票型"],
                "scale": [50.5, 120.3, 85.7],
                "company": ["华夏基金", "易方达", "嘉实基金"],
            }
        )

    def test_render_fund_list(self, renderer, sample_df):
        """测试渲染基金列表"""
        table = renderer.render_fund_list(sample_df)
        assert table is not None
        assert table.row_count == 3

    def test_render_fund_list_empty(self, renderer):
        """测试空数据渲染"""
        df = pd.DataFrame(columns=["code", "name", "type", "scale", "company"])
        table = renderer.render_fund_list(df)
        assert table is not None

    def test_render_analysis_result(self, renderer):
        """测试渲染分析结果"""
        metrics = {
            "total_return": 15.5,
            "cagr": 12.3,
            "sharpe": 1.5,
            "max_drawdown": -8.2,
            "volatility": 18.5,
        }
        table = renderer.render_analysis_result(metrics)
        assert table is not None

    def test_render_analysis_result_empty(self, renderer):
        """测试空指标渲染"""
        table = renderer.render_analysis_result({})
        assert table is not None


class TestChartRenderer:
    """图表渲染器测试"""

    @pytest.fixture
    def renderer(self):
        return ChartRenderer()

    @pytest.fixture
    def sample_nav_data(self):
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=100, freq="B")
        nav_values = 1.0 + np.cumsum(np.random.normal(0.001, 0.02, 100))
        return pd.DataFrame(
            {
                "nav_date": dates,
                "unit_nav": nav_values,
                "accumulated_nav": nav_values * 1.5,
            }
        )

    def test_render_nav_chart(self, renderer, sample_nav_data):
        """测试渲染净值走势图"""
        fig_dict = renderer.render_nav_chart(sample_nav_data)
        assert isinstance(fig_dict, dict)
        assert "data" in fig_dict

    def test_render_drawdown_chart(self, renderer):
        """测试渲染回撤图"""
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=100, freq="B")
        returns = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)
        wealth = (1 + returns).cumprod()
        drawdown = (wealth - wealth.cummax()) / wealth.cummax()

        fig_dict = renderer.render_drawdown_chart(drawdown)
        assert isinstance(fig_dict, dict)
        assert "data" in fig_dict


class TestReportRenderer:
    """报告渲染器测试"""

    @pytest.fixture
    def renderer(self):
        return ReportRenderer()

    def test_generate_html_report(self, renderer):
        """测试生成HTML报告"""
        metrics = {
            "total_return": 15.5,
            "cagr": 12.3,
            "volatility": 18.5,
            "max_drawdown": -8.2,
            "sharpe": 1.5,
            "sortino": 1.8,
        }

        html = renderer.generate_html_report(
            fund_code="000001",
            fund_name="测试基金",
            metrics=metrics,
        )

        assert isinstance(html, str)
        assert "000001" in html
        assert "测试基金" in html
        assert "15.50%" in html
        assert "<html" in html
        assert "</html>" in html

    def test_generate_html_report_with_nav(self, renderer, sample_nav_data):
        """测试带净值数据的HTML报告"""
        metrics = {"total_return": 10.0, "sharpe": 1.2}

        html = renderer.generate_html_report(
            fund_code="000001",
            fund_name="测试基金",
            metrics=metrics,
            nav_data=sample_nav_data,
        )

        assert isinstance(html, str)
        assert "000001" in html
