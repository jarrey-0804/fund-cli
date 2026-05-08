"""报告生成器测试"""

import pytest

from fund_cli.core.reporters.html_reporter import HtmlReporter
from fund_cli.core.reporters.markdown_reporter import MarkdownReporter


@pytest.fixture
def sample_metrics():
    return {
        "total_return": 25.5,
        "annualized_return": 8.2,
        "volatility": 15.3,
        "sharpe_ratio": 0.45,
        "max_drawdown": -12.5,
        "sortino_ratio": 0.55,
        "alpha": 2.1,
        "beta": 0.85,
    }


class TestHtmlReporter:
    def test_generate(self, sample_metrics):
        reporter = HtmlReporter()
        html = reporter.generate("000001", sample_metrics)
        assert "<!DOCTYPE html>" in html
        assert "000001" in html
        assert "25.5" in html

    def test_generate_with_nav(self, sample_metrics):
        reporter = HtmlReporter()
        import pandas as pd

        nav = pd.DataFrame({"nav_date": pd.date_range("2024-01-01", periods=10)})
        html = reporter.generate("000001", sample_metrics, nav_data=nav)
        assert "000001" in html

    def test_save(self, sample_metrics, tmp_path):
        reporter = HtmlReporter()
        html = reporter.generate("000001", sample_metrics)
        out = str(tmp_path / "report.html")
        reporter.save(html, out)
        content = open(out).read()
        assert "<!DOCTYPE html>" in content

    def test_get_formats(self):
        reporter = HtmlReporter()
        assert "html" in reporter.get_formats()


class TestMarkdownReporter:
    def test_generate(self, sample_metrics):
        reporter = MarkdownReporter()
        md = reporter.generate("000001", sample_metrics)
        assert "# 000001" in md
        assert "25.5" in md

    def test_save(self, sample_metrics, tmp_path):
        reporter = MarkdownReporter()
        md = reporter.generate("000001", sample_metrics)
        out = str(tmp_path / "report.md")
        reporter.save(md, out)
        content = open(out).read()
        assert "# 000001" in content

    def test_get_formats(self):
        reporter = MarkdownReporter()
        assert "markdown" in reporter.get_formats()
