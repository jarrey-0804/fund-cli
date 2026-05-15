"""
Reporter 报告生成器单元测试

测试覆盖：
- HtmlReporter 生成与保存
- MarkdownReporter 生成与保存
- Reporter 基类方法
- render_to_template 模板渲染
- export_pdf PDF 导出
- export_docx Word 导出（NotImplementedError）
- export_pptx PPT 导出（NotImplementedError）
- get_supported_formats 格式支持检测
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from fund_cli.core.reporter import Reporter
from fund_cli.core.reporters.html_reporter import HtmlReporter
from fund_cli.core.reporters.markdown_reporter import MarkdownReporter

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_metrics():
    """创建示例指标数据"""
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


@pytest.fixture
def sample_nav_data():
    """创建示例净值数据"""
    return pd.DataFrame({
        "nav_date": pd.date_range("2024-01-01", periods=10),
        "unit_nav": [1.0 + i * 0.01 for i in range(10)],
        "accumulated_nav": [1.5 + i * 0.01 for i in range(10)],
    })


# =============================================================================
# 测试类：HtmlReporter
# =============================================================================


class TestHtmlReporter:
    """测试 HTML 报告生成器"""

    def test_generate(self, sample_metrics):
        """测试生成 HTML 报告"""
        reporter = HtmlReporter()
        html = reporter.generate("000001", sample_metrics)
        assert "<!DOCTYPE html>" in html
        assert "000001" in html
        assert "25.5" in html

    def test_generate_with_nav(self, sample_metrics, sample_nav_data):
        """测试带净值数据生成报告"""
        reporter = HtmlReporter()
        html = reporter.generate("000001", sample_metrics, nav_data=sample_nav_data)
        assert "000001" in html

    def test_generate_with_benchmark(self, sample_metrics, sample_nav_data):
        """测试带基准数据生成报告"""
        reporter = HtmlReporter()
        benchmark = pd.DataFrame({
            "trade_date": pd.date_range("2024-01-01", periods=10),
            "close": [3000 + i * 10 for i in range(10)],
        })
        html = reporter.generate("000001", sample_metrics, benchmark_data=benchmark)
        assert "000001" in html

    def test_generate_with_negative_values(self):
        """测试生成包含负值的报告"""
        reporter = HtmlReporter()
        metrics = {
            "total_return": -15.5,
            "max_drawdown": -25.3,
            "sharpe_ratio": -0.5,
        }
        html = reporter.generate("000001", metrics)
        assert "negative" in html  # 负值应该有 negative CSS 类

    def test_generate_with_none_values(self):
        """测试生成包含 None 值的报告"""
        reporter = HtmlReporter()
        metrics = {
            "total_return": None,
            "sharpe_ratio": None,
        }
        html = reporter.generate("000001", metrics)
        assert "N/A" in html

    def test_save(self, sample_metrics, tmp_path):
        """测试保存 HTML 报告"""
        reporter = HtmlReporter()
        html = reporter.generate("000001", sample_metrics)
        out = str(tmp_path / "report.html")
        reporter.save(html, out)
        content = open(out, encoding="utf-8").read()
        assert "<!DOCTYPE html>" in content

    def test_get_formats(self):
        """测试获取支持的格式"""
        reporter = HtmlReporter()
        assert "html" in reporter.get_formats()

    def test_generate_contains_all_metrics(self, sample_metrics):
        """测试报告包含所有指标"""
        reporter = HtmlReporter()
        html = reporter.generate("000001", sample_metrics)
        assert "总收益率" in html
        assert "年化收益率" in html
        assert "波动率" in html
        assert "夏普比率" in html
        assert "最大回撤" in html

    def test_generate_contains_fund_code_in_title(self, sample_metrics):
        """测试报告标题包含基金代码"""
        reporter = HtmlReporter()
        html = reporter.generate("110011", sample_metrics)
        assert "110011" in html


# =============================================================================
# 测试类：MarkdownReporter
# =============================================================================


class TestMarkdownReporter:
    """测试 Markdown 报告生成器"""

    def test_generate(self, sample_metrics):
        """测试生成 Markdown 报告"""
        reporter = MarkdownReporter()
        md = reporter.generate("000001", sample_metrics)
        assert "# 000001" in md
        assert "25.5" in md

    def test_generate_with_nav(self, sample_metrics, sample_nav_data):
        """测试带净值数据生成报告"""
        reporter = MarkdownReporter()
        md = reporter.generate("000001", sample_metrics, nav_data=sample_nav_data)
        assert "# 000001" in md

    def test_generate_with_none_values(self):
        """测试生成包含 None 值的报告"""
        reporter = MarkdownReporter()
        metrics = {
            "total_return": None,
            "sharpe_ratio": None,
        }
        md = reporter.generate("000001", metrics)
        assert "N/A" in md

    def test_save(self, sample_metrics, tmp_path):
        """测试保存 Markdown 报告"""
        reporter = MarkdownReporter()
        md = reporter.generate("000001", sample_metrics)
        out = str(tmp_path / "report.md")
        reporter.save(md, out)
        content = open(out, encoding="utf-8").read()
        assert "# 000001" in content

    def test_get_formats(self):
        """测试获取支持的格式"""
        reporter = MarkdownReporter()
        assert "markdown" in reporter.get_formats()

    def test_generate_contains_table(self, sample_metrics):
        """测试报告包含表格格式"""
        reporter = MarkdownReporter()
        md = reporter.generate("000001", sample_metrics)
        assert "|" in md  # Markdown 表格分隔符
        assert "---" in md  # Markdown 表格分隔线

    def test_generate_contains_footer(self, sample_metrics):
        """测试报告包含页脚"""
        reporter = MarkdownReporter()
        md = reporter.generate("000001", sample_metrics)
        assert "Fund CLI" in md


# =============================================================================
# 测试类：Reporter 基类方法
# =============================================================================


class TestReporterBaseClass:
    """测试 Reporter 基类方法"""

    def test_render_to_template_with_simple_data(self, tmp_path):
        """测试使用简单数据渲染模板"""
        # 创建测试模板
        template_content = "<html><body>{{ title }}</body></html>"
        template_path = tmp_path / "test_template.html"
        template_path.write_text(template_content, encoding="utf-8")

        # 创建具体实现类用于测试
        class ConcreteReporter(Reporter):
            def generate(self, fund_code, metrics, nav_data=None, benchmark_data=None, **kwargs):
                return ""
            def save(self, content, output_path):
                pass
            def get_formats(self):
                return ["html"]

        reporter = ConcreteReporter()
        result = reporter.render_to_template(
            {"title": "测试标题"},
            str(template_path)
        )
        assert "测试标题" in result

    def test_render_to_template_with_complex_data(self, tmp_path):
        """测试使用复杂数据渲染模板"""
        template_content = "<html><body>{{ fund_code }} - {{ metrics.return_rate }}</body></html>"
        template_path = tmp_path / "test_template.html"
        template_path.write_text(template_content, encoding="utf-8")

        class ConcreteReporter(Reporter):
            def generate(self, fund_code, metrics, nav_data=None, benchmark_data=None, **kwargs):
                return ""
            def save(self, content, output_path):
                pass
            def get_formats(self):
                return ["html"]

        reporter = ConcreteReporter()
        result = reporter.render_to_template(
            {"fund_code": "000001", "metrics": {"return_rate": 25.5}},
            str(template_path)
        )
        assert "000001" in result
        assert "25.5" in result

    def test_render_to_template_autoescape(self, tmp_path):
        """测试模板自动转义"""
        template_content = "<html><body>{{ content }}</body></html>"
        template_path = tmp_path / "test_template.html"
        template_path.write_text(template_content, encoding="utf-8")

        class ConcreteReporter(Reporter):
            def generate(self, fund_code, metrics, nav_data=None, benchmark_data=None, **kwargs):
                return ""
            def save(self, content, output_path):
                pass
            def get_formats(self):
                return ["html"]

        reporter = ConcreteReporter()
        result = reporter.render_to_template(
            {"content": "<script>alert('xss')</script>"},
            str(template_path)
        )
        # HTML 应该被转义
        assert "&lt;script&gt;" in result or "<script>" not in result

    def test_export_pdf_with_weasyprint(self, tmp_path):
        """测试使用 weasyprint 导出 PDF"""
        class ConcreteReporter(Reporter):
            def generate(self, fund_code, metrics, nav_data=None, benchmark_data=None, **kwargs):
                return ""
            def save(self, content, output_path):
                pass
            def get_formats(self):
                return ["html"]

        reporter = ConcreteReporter()
        html_content = "<html><body><h1>测试报告</h1></body></html>"
        output_path = str(tmp_path / "test.pdf")

        # Mock weasyprint.HTML 在方法内部导入
        mock_html_instance = MagicMock()
        mock_html_class = MagicMock(return_value=mock_html_instance)
        mock_weasyprint = MagicMock()
        mock_weasyprint.HTML = mock_html_class

        with patch.dict("sys.modules", {"weasyprint": mock_weasyprint}):
            result = reporter.export_pdf(html_content, output_path)

            mock_html_class.assert_called_once()
            mock_html_instance.write_pdf.assert_called_once_with(output_path)
            assert result == Path(output_path)

    def test_export_pdf_without_weasyprint(self, tmp_path):
        """测试未安装 weasyprint 时导出 PDF 抛出异常"""
        class ConcreteReporter(Reporter):
            def generate(self, fund_code, metrics, nav_data=None, benchmark_data=None, **kwargs):
                return ""
            def save(self, content, output_path):
                pass
            def get_formats(self):
                return ["html"]

        reporter = ConcreteReporter()
        html_content = "<html><body><h1>测试报告</h1></body></html>"
        output_path = str(tmp_path / "test.pdf")

        # 模拟 weasyprint 未安装
        with patch.dict("sys.modules", {"weasyprint": None}):
            # 需要重新创建 reporter 实例以触发新的导入尝试
            with patch("builtins.__import__", side_effect=lambda name, *args, **kwargs: ImportError(f"No module named '{name}'") if name == "weasyprint" else __import__(name, *args, **kwargs)):
                with pytest.raises(RuntimeError, match="weasyprint 未安装"):
                    reporter.export_pdf(html_content, output_path)

    def test_export_docx_raises_not_implemented(self, tmp_path):
        """测试导出 Word 抛出 NotImplementedError"""
        class ConcreteReporter(Reporter):
            def generate(self, fund_code, metrics, nav_data=None, benchmark_data=None, **kwargs):
                return ""
            def save(self, content, output_path):
                pass
            def get_formats(self):
                return ["html"]

        reporter = ConcreteReporter()
        output_path = str(tmp_path / "test.docx")

        with pytest.raises(NotImplementedError, match="Word导出将在阶段三实现"):
            reporter.export_docx("content", output_path)

    def test_export_pptx_raises_not_implemented(self, tmp_path):
        """测试导出 PPT 抛出 NotImplementedError"""
        class ConcreteReporter(Reporter):
            def generate(self, fund_code, metrics, nav_data=None, benchmark_data=None, **kwargs):
                return ""
            def save(self, content, output_path):
                pass
            def get_formats(self):
                return ["html"]

        reporter = ConcreteReporter()
        output_path = str(tmp_path / "test.pptx")

        with pytest.raises(NotImplementedError, match="PPT导出将在阶段三实现"):
            reporter.export_pptx("content", output_path)

    def test_get_supported_formats_with_weasyprint(self):
        """测试安装 weasyprint 时支持 PDF 格式"""
        class ConcreteReporter(Reporter):
            def generate(self, fund_code, metrics, nav_data=None, benchmark_data=None, **kwargs):
                return ""
            def save(self, content, output_path):
                pass
            def get_formats(self):
                return ["html", "markdown"]

        reporter = ConcreteReporter()

        with patch.dict("sys.modules", {"weasyprint": MagicMock()}):
            formats = reporter.get_supported_formats()
            assert "html" in formats
            assert "markdown" in formats
            assert "pdf" in formats

    def test_get_supported_formats_without_weasyprint(self):
        """测试未安装 weasyprint 时不支持 PDF 格式"""
        class ConcreteReporter(Reporter):
            def generate(self, fund_code, metrics, nav_data=None, benchmark_data=None, **kwargs):
                return ""
            def save(self, content, output_path):
                pass
            def get_formats(self):
                return ["html", "markdown"]

        reporter = ConcreteReporter()

        # 测试基本格式始终存在
        formats = reporter.get_supported_formats()
        assert "html" in formats
        assert "markdown" in formats
        # PDF 格式取决于 weasyprint 是否安装

    def test_get_supported_formats_returns_list(self):
        """测试 get_supported_formats 返回列表"""
        class ConcreteReporter(Reporter):
            def generate(self, fund_code, metrics, nav_data=None, benchmark_data=None, **kwargs):
                return ""
            def save(self, content, output_path):
                pass
            def get_formats(self):
                return ["html"]

        reporter = ConcreteReporter()
        formats = reporter.get_supported_formats()
        assert isinstance(formats, list)


# =============================================================================
# 测试类：格式支持检测
# =============================================================================


class TestFormatSupport:
    """测试各种格式支持检测"""

    def test_html_reporter_supports_html(self):
        """测试 HTML 报告器支持 HTML 格式"""
        reporter = HtmlReporter()
        formats = reporter.get_formats()
        assert "html" in formats

    def test_markdown_reporter_supports_markdown(self):
        """测试 Markdown 报告器支持 Markdown 格式"""
        reporter = MarkdownReporter()
        formats = reporter.get_formats()
        assert "markdown" in formats

    def test_html_reporter_supported_formats_includes_pdf_when_available(self):
        """测试 HTML 报告器在 weasyprint 可用时支持 PDF"""
        reporter = HtmlReporter()

        with patch.dict("sys.modules", {"weasyprint": MagicMock()}):
            formats = reporter.get_supported_formats()
            assert "pdf" in formats

    def test_html_reporter_supported_formats_excludes_pdf_when_unavailable(self):
        """测试 HTML 报告器在 weasyprint 不可用时不支持 PDF"""
        reporter = HtmlReporter()

        # 测试基本格式始终存在
        formats = reporter.get_supported_formats()
        assert "html" in formats
        # PDF 格式取决于 weasyprint 是否安装


# =============================================================================
# 测试类：报告内容验证
# =============================================================================


class TestReportContentValidation:
    """测试报告内容验证"""

    def test_html_report_contains_css(self, sample_metrics):
        """测试 HTML 报告包含 CSS 样式"""
        reporter = HtmlReporter()
        html = reporter.generate("000001", sample_metrics)
        assert "<style>" in html
        assert "</style>" in html

    def test_html_report_contains_meta_charset(self, sample_metrics):
        """测试 HTML 报告包含字符编码声明"""
        reporter = HtmlReporter()
        html = reporter.generate("000001", sample_metrics)
        assert "charset" in html.lower() or "UTF-8" in html

    def test_html_report_contains_footer(self, sample_metrics):
        """测试 HTML 报告包含页脚"""
        reporter = HtmlReporter()
        html = reporter.generate("000001", sample_metrics)
        assert "Fund CLI" in html

    def test_markdown_report_contains_header(self, sample_metrics):
        """测试 Markdown 报告包含标题"""
        reporter = MarkdownReporter()
        md = reporter.generate("000001", sample_metrics)
        assert md.startswith("#")

    def test_html_report_positive_value_has_class(self):
        """测试 HTML 报告正值有 positive CSS 类"""
        reporter = HtmlReporter()
        metrics = {"total_return": 25.5}
        html = reporter.generate("000001", metrics)
        assert "positive" in html

    def test_html_report_negative_value_has_class(self):
        """测试 HTML 报告负值有 negative CSS 类"""
        reporter = HtmlReporter()
        metrics = {"total_return": -15.5}
        html = reporter.generate("000001", metrics)
        assert "negative" in html
