"""报告生成器"""

from fund_cli.core.reporters.docx_reporter import DocxReporter  # v3.1 新增
from fund_cli.core.reporters.html_reporter import HtmlReporter
from fund_cli.core.reporters.markdown_reporter import MarkdownReporter
from fund_cli.core.reporters.pdf_reporter import PdfReporter  # v3.1 新增
from fund_cli.core.reporters.pptx_reporter import PptxReporter  # v3.1 新增

__all__ = [
    "HtmlReporter",
    "MarkdownReporter",
    "PdfReporter",  # v3.1 新增
    "DocxReporter",  # v3.1 新增
    "PptxReporter",  # v3.1 新增
]
