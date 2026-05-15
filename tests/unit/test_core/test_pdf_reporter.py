"""PdfReporter PDF报告生成器单元测试"""

from unittest.mock import patch

import pytest

from fund_cli.core.reporter import Reporter
from fund_cli.core.reporters.pdf_reporter import PdfReporter


@pytest.fixture
def sample_metrics():
    """示例指标数据"""
    return {
        "total_return": 0.255,
        "annualized_return": 0.082,
        "volatility": 0.153,
        "sharpe_ratio": 0.45,
        "max_drawdown": -0.125,
        "sortino_ratio": 0.55,
        "alpha": 2.1,
        "beta": 0.85,
        "information_ratio": 0.32,
        "calmar_ratio": 0.65,
    }


@pytest.fixture
def reporter():
    """创建PdfReporter实例"""
    return PdfReporter()


class TestPdfReporterInit:
    """PdfReporter 初始化测试"""

    def test_instantiate(self, reporter):
        """测试实例化PdfReporter"""
        assert reporter is not None

    def test_inherits_from_reporter(self, reporter):
        """测试PdfReporter继承自Reporter"""
        assert isinstance(reporter, Reporter)


class TestPdfReporterGenerate:
    """PdfReporter.generate 生成HTML测试"""

    def test_generate_returns_non_empty_string(self, reporter, sample_metrics):
        """测试generate返回非空HTML字符串"""
        html = reporter.generate("000001", sample_metrics)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_generate_contains_doctype(self, reporter, sample_metrics):
        """测试生成的HTML包含DOCTYPE声明"""
        html = reporter.generate("000001", sample_metrics)
        assert "<!DOCTYPE html>" in html

    def test_generate_contains_html_tag(self, reporter, sample_metrics):
        """测试生成的HTML包含html标签"""
        html = reporter.generate("000001", sample_metrics)
        assert "<html" in html
        assert "</html>" in html

    def test_generate_contains_fund_code(self, reporter, sample_metrics):
        """测试生成的HTML包含基金代码"""
        html = reporter.generate("000001", sample_metrics)
        assert "000001" in html

    def test_generate_contains_css_styles(self, reporter, sample_metrics):
        """测试生成的HTML包含关键CSS样式"""
        html = reporter.generate("000001", sample_metrics)
        assert "@page" in html
        assert ".positive" in html
        assert ".negative" in html
        assert ".summary-box" in html

    def test_generate_contains_table(self, reporter, sample_metrics):
        """测试生成的HTML包含数据表格"""
        html = reporter.generate("000001", sample_metrics)
        assert "<table>" in html
        assert "</table>" in html
        assert "<th>" in html

    def test_generate_contains_metrics(self, reporter, sample_metrics):
        """测试生成的HTML包含核心指标"""
        html = reporter.generate("000001", sample_metrics)
        assert "总收益率" in html
        assert "夏普比率" in html
        assert "最大回撤" in html
        assert "Alpha" in html

    def test_generate_positive_value_color_class(self, reporter, sample_metrics):
        """测试正值指标使用positive颜色类"""
        html = reporter.generate("000001", sample_metrics)
        # total_return = 0.255 > 0, 应该有 positive 类
        assert "positive" in html

    def test_generate_negative_value_color_class(self, reporter, sample_metrics):
        """测试负值指标使用negative颜色类"""
        html = reporter.generate("000001", sample_metrics)
        # max_drawdown = -0.125 < 0, 应该有 negative 类
        assert "negative" in html

    def test_generate_footer(self, reporter, sample_metrics):
        """测试生成的HTML包含页脚"""
        html = reporter.generate("000001", sample_metrics)
        assert "Fund CLI" in html
        assert "仅供参考" in html

    def test_generate_with_empty_metrics(self, reporter):
        """测试空指标数据时正常生成"""
        html = reporter.generate("000001", {})
        assert "<!DOCTYPE html>" in html
        assert "000001" in html
        assert "N/A" in html


class TestPdfReporterGetFormats:
    """PdfReporter.get_formats 格式测试"""

    def test_get_formats_returns_pdf(self, reporter):
        """测试get_formats返回包含pdf的列表"""
        formats = reporter.get_formats()
        assert isinstance(formats, list)
        assert formats == ["pdf"]

    def test_get_formats_length(self, reporter):
        """测试get_formats返回列表长度为1"""
        formats = reporter.get_formats()
        assert len(formats) == 1


class TestPdfReporterSave:
    """PdfReporter.save 保存测试"""

    @patch("fund_cli.core.reporters.pdf_reporter.PdfReporter.export_pdf")
    def test_save_calls_export_pdf(self, mock_export_pdf, reporter, sample_metrics):
        """测试save方法调用export_pdf"""
        html = reporter.generate("000001", sample_metrics)
        reporter.save(html, "/tmp/test_report.pdf")
        mock_export_pdf.assert_called_once_with(html, "/tmp/test_report.pdf")

    @patch("fund_cli.core.reporters.pdf_reporter.PdfReporter.export_pdf")
    def test_save_with_custom_path(self, mock_export_pdf, reporter, sample_metrics):
        """测试save方法使用自定义路径"""
        html = reporter.generate("000001", sample_metrics)
        reporter.save(html, "/custom/path/report.pdf")
        mock_export_pdf.assert_called_once_with(html, "/custom/path/report.pdf")

    @patch("fund_cli.core.reporter.Reporter.export_pdf")
    def test_save_delegates_to_base_export_pdf(self, mock_export_pdf, reporter, sample_metrics):
        """测试save方法委托给基类的export_pdf"""
        html = reporter.generate("000001", sample_metrics)
        reporter.save(html, "output.pdf")
        mock_export_pdf.assert_called_once_with(html, "output.pdf")


class TestPdfReporterInheritance:
    """PdfReporter 继承关系测试"""

    def test_is_subclass_of_reporter(self):
        """测试PdfReporter是Reporter的子类"""
        assert issubclass(PdfReporter, Reporter)

    def test_has_generate_method(self, reporter):
        """测试PdfReporter有generate方法"""
        assert hasattr(reporter, "generate")
        assert callable(reporter.generate)

    def test_has_save_method(self, reporter):
        """测试PdfReporter有save方法"""
        assert hasattr(reporter, "save")
        assert callable(reporter.save)

    def test_has_get_formats_method(self, reporter):
        """测试PdfReporter有get_formats方法"""
        assert hasattr(reporter, "get_formats")
        assert callable(reporter.get_formats)

    def test_has_export_pdf_method(self, reporter):
        """测试PdfReporter继承基类的export_pdf方法"""
        assert hasattr(reporter, "export_pdf")
        assert callable(reporter.export_pdf)
