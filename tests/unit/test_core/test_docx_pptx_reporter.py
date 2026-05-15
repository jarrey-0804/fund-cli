"""
Word/PPT报告生成器单元测试
"""
from unittest.mock import MagicMock, patch

import pytest

from fund_cli.core.reporter import Reporter
from fund_cli.core.reporters.docx_reporter import DocxReporter
from fund_cli.core.reporters.pptx_reporter import PptxReporter


class TestDocxReporter:
    """测试Word报告生成器"""

    def test_inherits_reporter(self):
        """测试继承关系"""
        assert issubclass(DocxReporter, Reporter)

    def test_get_formats(self):
        """测试获取支持的格式"""
        reporter = DocxReporter()
        assert reporter.get_formats() == ["docx"]

    def test_generate_without_docx(self):
        """测试未安装 python-docx 时抛出异常"""
        reporter = DocxReporter()
        with patch.dict('sys.modules', {'docx': None}):
            with pytest.raises(RuntimeError, match="python-docx 未安装"):
                reporter.generate("000001", {})

    def test_generate_complete_flow(self):
        """测试 generate 方法完整流程"""
        reporter = DocxReporter()

        # 创建 mock 对象
        mock_doc = MagicMock()
        mock_title = MagicMock()
        mock_paragraph = MagicMock()
        mock_table = MagicMock()
        mock_cells = [MagicMock(), MagicMock()]
        mock_run = MagicMock()

        # 设置 mock 行为
        mock_doc.add_heading.return_value = mock_title
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_doc.add_table.return_value = mock_table
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = mock_cells
        mock_table.add_row.return_value.cells = mock_cells
        mock_paragraph.add_run.return_value = mock_run

        # Mock docx 模块
        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_docx.WD_ALIGN_PARAGRAPH.CENTER = 'center'
        mock_docx.WD_TABLE_ALIGNMENT.CENTER = 'center'
        mock_docx.RGBColor = MagicMock()
        mock_docx.Pt = MagicMock()

        with patch.dict('sys.modules', {'docx': mock_docx, 'docx.enum.table': MagicMock(), 'docx.enum.text': MagicMock(), 'docx.shared': MagicMock()}):
            metrics = {
                "total_return": 0.15,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.1,
                "annualized_return": 0.12,
                "volatility": 0.08,
                "alpha": 0.02,
                "beta": 0.95,
            }

            result = reporter.generate("000001", metrics)

            # 验证返回路径
            assert result.endswith(".docx")
            assert "000001" in result

            # 验证文档创建
            mock_docx.Document.assert_called_once()

            # 验证标题添加
            mock_doc.add_heading.assert_called()

            # 验证段落添加
            assert mock_doc.add_paragraph.call_count >= 2

            # 验证表格添加
            mock_doc.add_table.assert_called_once()

            # 验证保存
            mock_doc.save.assert_called_once()

    def test_generate_positive_return_color(self):
        """测试正收益率颜色为绿色"""
        reporter = DocxReporter()

        mock_doc = MagicMock()
        mock_title = MagicMock()
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_table = MagicMock()
        mock_cells = [MagicMock(), MagicMock()]

        mock_doc.add_heading.return_value = mock_title
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_doc.add_table.return_value = mock_table
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = mock_cells
        mock_table.add_row.return_value.cells = mock_cells
        mock_paragraph.add_run.return_value = mock_run

        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_docx.WD_ALIGN_PARAGRAPH.CENTER = 'center'
        mock_docx.WD_TABLE_ALIGNMENT.CENTER = 'center'
        mock_docx.Pt = MagicMock()

        # Mock docx.shared 模块中的 RGBColor
        mock_rgb_color = MagicMock()
        mock_shared = MagicMock()
        mock_shared.RGBColor = mock_rgb_color

        with patch.dict('sys.modules', {'docx': mock_docx, 'docx.enum.table': MagicMock(), 'docx.enum.text': MagicMock(), 'docx.shared': mock_shared}):
            # 正收益率
            metrics = {"total_return": 0.15}
            reporter.generate("000001", metrics)

            # 验证 RGB 被调用
            mock_rgb_color.assert_called()

    def test_generate_negative_return_color(self):
        """测试负收益率颜色为红色"""
        reporter = DocxReporter()

        mock_doc = MagicMock()
        mock_title = MagicMock()
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_table = MagicMock()
        mock_cells = [MagicMock(), MagicMock()]

        mock_doc.add_heading.return_value = mock_title
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_doc.add_table.return_value = mock_table
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = mock_cells
        mock_table.add_row.return_value.cells = mock_cells
        mock_paragraph.add_run.return_value = mock_run

        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_docx.WD_ALIGN_PARAGRAPH.CENTER = 'center'
        mock_docx.WD_TABLE_ALIGNMENT.CENTER = 'center'
        mock_docx.Pt = MagicMock()

        # Mock docx.shared 模块中的 RGBColor
        mock_rgb_color = MagicMock()
        mock_shared = MagicMock()
        mock_shared.RGBColor = mock_rgb_color

        with patch.dict('sys.modules', {'docx': mock_docx, 'docx.enum.table': MagicMock(), 'docx.enum.text': MagicMock(), 'docx.shared': mock_shared}):
            # 负收益率
            metrics = {"total_return": -0.1}
            reporter.generate("000001", metrics)

            # 验证 RGB 被调用
            mock_rgb_color.assert_called()

    def test_generate_zero_return_color(self):
        """测试零收益率颜色为红色（<=0 条件）"""
        reporter = DocxReporter()

        mock_doc = MagicMock()
        mock_title = MagicMock()
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_table = MagicMock()
        mock_cells = [MagicMock(), MagicMock()]

        mock_doc.add_heading.return_value = mock_title
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_doc.add_table.return_value = mock_table
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = mock_cells
        mock_table.add_row.return_value.cells = mock_cells
        mock_paragraph.add_run.return_value = mock_run

        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_docx.WD_ALIGN_PARAGRAPH.CENTER = 'center'
        mock_docx.WD_TABLE_ALIGNMENT.CENTER = 'center'
        mock_docx.Pt = MagicMock()

        # Mock docx.shared 模块中的 RGBColor
        mock_rgb_color = MagicMock()
        mock_shared = MagicMock()
        mock_shared.RGBColor = mock_rgb_color

        with patch.dict('sys.modules', {'docx': mock_docx, 'docx.enum.table': MagicMock(), 'docx.enum.text': MagicMock(), 'docx.shared': mock_shared}):
            # 零收益率
            metrics = {"total_return": 0}
            reporter.generate("000001", metrics)

            mock_rgb_color.assert_called()

    def test_generate_with_empty_metrics(self):
        """测试空 metrics 数据"""
        reporter = DocxReporter()

        mock_doc = MagicMock()
        mock_title = MagicMock()
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_table = MagicMock()
        mock_cells = [MagicMock(), MagicMock()]

        mock_doc.add_heading.return_value = mock_title
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_doc.add_table.return_value = mock_table
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = mock_cells
        mock_table.add_row.return_value.cells = mock_cells
        mock_paragraph.add_run.return_value = mock_run

        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_docx.WD_ALIGN_PARAGRAPH.CENTER = 'center'
        mock_docx.WD_TABLE_ALIGNMENT.CENTER = 'center'
        mock_docx.RGBColor = MagicMock()
        mock_docx.Pt = MagicMock()

        with patch.dict('sys.modules', {'docx': mock_docx, 'docx.enum.table': MagicMock(), 'docx.enum.text': MagicMock(), 'docx.shared': MagicMock()}):
            result = reporter.generate("000001", {})

            assert result.endswith(".docx")
            mock_doc.save.assert_called_once()

    def test_generate_with_partial_metrics(self):
        """测试部分 metrics 数据"""
        reporter = DocxReporter()

        mock_doc = MagicMock()
        mock_title = MagicMock()
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_table = MagicMock()
        mock_cells = [MagicMock(), MagicMock()]

        mock_doc.add_heading.return_value = mock_title
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_doc.add_table.return_value = mock_table
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = mock_cells
        mock_table.add_row.return_value.cells = mock_cells
        mock_paragraph.add_run.return_value = mock_run

        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_docx.WD_ALIGN_PARAGRAPH.CENTER = 'center'
        mock_docx.WD_TABLE_ALIGNMENT.CENTER = 'center'
        mock_docx.RGBColor = MagicMock()
        mock_docx.Pt = MagicMock()

        with patch.dict('sys.modules', {'docx': mock_docx, 'docx.enum.table': MagicMock(), 'docx.enum.text': MagicMock(), 'docx.shared': MagicMock()}):
            # 只有部分指标
            metrics = {
                "total_return": 0.1,
                "sharpe_ratio": 1.2,
            }

            result = reporter.generate("000001", metrics)

            assert result.endswith(".docx")

    def test_generate_table_with_numeric_values(self):
        """测试表格中数值格式化"""
        reporter = DocxReporter()

        mock_doc = MagicMock()
        mock_title = MagicMock()
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_table = MagicMock()
        mock_cells = [MagicMock(), MagicMock()]

        mock_doc.add_heading.return_value = mock_title
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_doc.add_table.return_value = mock_table
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = mock_cells
        mock_table.add_row.return_value.cells = mock_cells
        mock_paragraph.add_run.return_value = mock_run

        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_docx.WD_ALIGN_PARAGRAPH.CENTER = 'center'
        mock_docx.WD_TABLE_ALIGNMENT.CENTER = 'center'
        mock_docx.RGBColor = MagicMock()
        mock_docx.Pt = MagicMock()

        with patch.dict('sys.modules', {'docx': mock_docx, 'docx.enum.table': MagicMock(), 'docx.enum.text': MagicMock(), 'docx.shared': MagicMock()}):
            metrics = {
                "total_return": 0.123456,  # 数值类型
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.1,
                "annualized_return": 0.12,
                "volatility": 0.08,
                "alpha": 0.02,
                "beta": 0.95,
            }

            reporter.generate("000001", metrics)

            # 验证表格行被添加
            assert mock_table.add_row.call_count == 7  # 7 个核心指标

    def test_generate_table_with_string_values(self):
        """测试表格中字符串值"""
        reporter = DocxReporter()

        mock_doc = MagicMock()
        mock_title = MagicMock()
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_table = MagicMock()
        mock_cells = [MagicMock(), MagicMock()]

        mock_doc.add_heading.return_value = mock_title
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_doc.add_table.return_value = mock_table
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = mock_cells
        mock_table.add_row.return_value.cells = mock_cells
        mock_paragraph.add_run.return_value = mock_run

        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_docx.WD_ALIGN_PARAGRAPH.CENTER = 'center'
        mock_docx.WD_TABLE_ALIGNMENT.CENTER = 'center'
        mock_docx.Pt = MagicMock()

        mock_rgb_color = MagicMock()
        mock_shared = MagicMock()
        mock_shared.RGBColor = mock_rgb_color

        with patch.dict('sys.modules', {'docx': mock_docx, 'docx.enum.table': MagicMock(), 'docx.enum.text': MagicMock(), 'docx.shared': mock_shared}):
            # total_return 必须是数值类型（用于格式化），其他可以是字符串
            metrics = {
                "total_return": 0.1,
                "sharpe_ratio": "N/A",
                "max_drawdown": "N/A",
            }

            result = reporter.generate("000001", metrics)

            assert result.endswith(".docx")

    def test_generate_footer_content(self):
        """测试页脚内容生成"""
        reporter = DocxReporter()

        mock_doc = MagicMock()
        mock_title = MagicMock()
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_table = MagicMock()
        mock_cells = [MagicMock(), MagicMock()]

        mock_doc.add_heading.return_value = mock_title
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_doc.add_table.return_value = mock_table
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = mock_cells
        mock_table.add_row.return_value.cells = mock_cells
        mock_paragraph.add_run.return_value = mock_run

        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_docx.WD_ALIGN_PARAGRAPH.CENTER = 'center'
        mock_docx.WD_TABLE_ALIGNMENT.CENTER = 'center'
        mock_docx.RGBColor = MagicMock()
        mock_docx.Pt = MagicMock()

        with patch.dict('sys.modules', {'docx': mock_docx, 'docx.enum.table': MagicMock(), 'docx.enum.text': MagicMock(), 'docx.shared': MagicMock()}):
            reporter.generate("000001", {})

            # 验证多次调用 add_paragraph（日期、摘要、页脚等）
            assert mock_doc.add_paragraph.call_count >= 2

    def test_generate_with_nav_data_ignored(self):
        """测试 nav_data 参数被忽略（当前实现不使用）"""
        reporter = DocxReporter()

        mock_doc = MagicMock()
        mock_title = MagicMock()
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_table = MagicMock()
        mock_cells = [MagicMock(), MagicMock()]

        mock_doc.add_heading.return_value = mock_title
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_doc.add_table.return_value = mock_table
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = mock_cells
        mock_table.add_row.return_value.cells = mock_cells
        mock_paragraph.add_run.return_value = mock_run

        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_docx.WD_ALIGN_PARAGRAPH.CENTER = 'center'
        mock_docx.WD_TABLE_ALIGNMENT.CENTER = 'center'
        mock_docx.RGBColor = MagicMock()
        mock_docx.Pt = MagicMock()

        with patch.dict('sys.modules', {'docx': mock_docx, 'docx.enum.table': MagicMock(), 'docx.enum.text': MagicMock(), 'docx.shared': MagicMock()}):
            # 传入 nav_data，应该被忽略
            result = reporter.generate("000001", {}, nav_data="some_data")

            assert result.endswith(".docx")

    def test_generate_with_benchmark_data_ignored(self):
        """测试 benchmark_data 参数被忽略（当前实现不使用）"""
        reporter = DocxReporter()

        mock_doc = MagicMock()
        mock_title = MagicMock()
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_table = MagicMock()
        mock_cells = [MagicMock(), MagicMock()]

        mock_doc.add_heading.return_value = mock_title
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_doc.add_table.return_value = mock_table
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = mock_cells
        mock_table.add_row.return_value.cells = mock_cells
        mock_paragraph.add_run.return_value = mock_run

        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_docx.WD_ALIGN_PARAGRAPH.CENTER = 'center'
        mock_docx.WD_TABLE_ALIGNMENT.CENTER = 'center'
        mock_docx.RGBColor = MagicMock()
        mock_docx.Pt = MagicMock()

        with patch.dict('sys.modules', {'docx': mock_docx, 'docx.enum.table': MagicMock(), 'docx.enum.text': MagicMock(), 'docx.shared': MagicMock()}):
            result = reporter.generate("000001", {}, benchmark_data="benchmark")

            assert result.endswith(".docx")

    def test_save(self):
        """测试保存文档"""
        reporter = DocxReporter()
        with patch('shutil.copy2') as mock_copy:
            reporter.save("/tmp/test.docx", "/output/test.docx")
            mock_copy.assert_called_once_with("/tmp/test.docx", "/output/test.docx")

    def test_save_with_different_paths(self):
        """测试保存到不同路径"""
        reporter = DocxReporter()
        with patch('shutil.copy2') as mock_copy:
            reporter.save("/source/report.docx", "/destination/report.docx")
            mock_copy.assert_called_once()

    def test_generate_heading_alignment(self):
        """测试标题居中对齐"""
        reporter = DocxReporter()

        mock_doc = MagicMock()
        mock_title = MagicMock()
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_table = MagicMock()
        mock_cells = [MagicMock(), MagicMock()]

        mock_doc.add_heading.return_value = mock_title
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_doc.add_table.return_value = mock_table
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = mock_cells
        mock_table.add_row.return_value.cells = mock_cells
        mock_paragraph.add_run.return_value = mock_run

        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_docx.WD_ALIGN_PARAGRAPH.CENTER = 'center'
        mock_docx.WD_TABLE_ALIGNMENT.CENTER = 'center'
        mock_docx.RGBColor = MagicMock()
        mock_docx.Pt = MagicMock()

        with patch.dict('sys.modules', {'docx': mock_docx, 'docx.enum.table': MagicMock(), 'docx.enum.text': MagicMock(), 'docx.shared': MagicMock()}):
            reporter.generate("000001", {})

            # 验证标题对齐被设置
            assert mock_title.alignment is not None

    def test_generate_table_style(self):
        """测试表格样式设置"""
        reporter = DocxReporter()

        mock_doc = MagicMock()
        mock_title = MagicMock()
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_table = MagicMock()
        mock_cells = [MagicMock(), MagicMock()]

        mock_doc.add_heading.return_value = mock_title
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_doc.add_table.return_value = mock_table
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = mock_cells
        mock_table.add_row.return_value.cells = mock_cells
        mock_paragraph.add_run.return_value = mock_run

        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_docx.WD_ALIGN_PARAGRAPH.CENTER = 'center'
        mock_docx.WD_TABLE_ALIGNMENT.CENTER = 'center'
        mock_docx.RGBColor = MagicMock()
        mock_docx.Pt = MagicMock()

        with patch.dict('sys.modules', {'docx': mock_docx, 'docx.enum.table': MagicMock(), 'docx.enum.text': MagicMock(), 'docx.shared': MagicMock()}):
            reporter.generate("000001", {})

            # 验证表格样式被设置
            assert hasattr(mock_table, 'style')


class TestPptxReporter:
    """测试PPT报告生成器"""

    def test_inherits_reporter(self):
        """测试继承关系"""
        assert issubclass(PptxReporter, Reporter)

    def test_get_formats(self):
        """测试获取支持的格式"""
        reporter = PptxReporter()
        assert reporter.get_formats() == ["pptx"]

    def test_generate_without_pptx(self):
        """测试未安装 python-pptx 时抛出异常"""
        reporter = PptxReporter()
        with patch.dict('sys.modules', {'pptx': None}):
            with pytest.raises(RuntimeError, match="python-pptx 未安装"):
                reporter.generate("000001", {})

    def test_generate_complete_flow(self):
        """测试 generate 方法完整流程"""
        reporter = PptxReporter()

        # 创建 mock 对象
        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide_layout = MagicMock()
        mock_textbox = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        # 设置 mock 行为
        mock_prs.slide_layouts = [mock_slide_layout] * 10
        mock_prs.slides.add_slide.return_value = mock_slide
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        mock_textbox.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.add_run = MagicMock()
        mock_slide.shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        # Mock table cell
        mock_cell = MagicMock()
        mock_cell.text_frame.paragraphs = [MagicMock()]
        mock_table.cell.return_value = mock_cell

        # Mock pptx 模块
        mock_pptx = MagicMock()
        mock_pptx.Presentation.return_value = mock_prs
        mock_pptx.RGBColor = MagicMock()
        mock_pptx.PP_ALIGN.CENTER = 'center'
        mock_pptx.Inches = MagicMock(return_value=1.0)
        mock_pptx.Pt = MagicMock()

        with patch.dict('sys.modules', {'pptx': mock_pptx, 'pptx.dml.color': MagicMock(), 'pptx.enum.text': MagicMock(), 'pptx.util': MagicMock()}):
            metrics = {
                "total_return": 0.15,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.1,
                "annualized_return": 0.12,
                "volatility": 0.08,
                "alpha": 0.02,
            }

            result = reporter.generate("000001", metrics)

            # 验证返回路径
            assert result.endswith(".pptx")
            assert "000001" in result

            # 验证演示文稿创建
            mock_pptx.Presentation.assert_called_once()

            # 验证幻灯片添加（封面、核心指标、投资摘要）
            assert mock_prs.slides.add_slide.call_count == 3

            # 验证保存
            mock_prs.save.assert_called_once()

    def test_generate_positive_return_color(self):
        """测试正收益率颜色为绿色"""
        reporter = PptxReporter()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide_layout = MagicMock()
        mock_textbox = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        mock_prs.slide_layouts = [mock_slide_layout] * 10
        mock_prs.slides.add_slide.return_value = mock_slide
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        mock_textbox.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.add_run = MagicMock()
        mock_slide.shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        mock_cell = MagicMock()
        mock_cell.text_frame.paragraphs = [MagicMock()]
        mock_table.cell.return_value = mock_cell

        mock_pptx = MagicMock()
        mock_pptx.Presentation.return_value = mock_prs
        mock_pptx.PP_ALIGN.CENTER = 'center'
        mock_pptx.Inches = MagicMock(return_value=1.0)
        mock_pptx.Pt = MagicMock()

        # Mock pptx.dml.color 模块中的 RGBColor
        mock_rgb_color = MagicMock()
        mock_dml_color = MagicMock()
        mock_dml_color.RGBColor = mock_rgb_color

        with patch.dict('sys.modules', {'pptx': mock_pptx, 'pptx.dml.color': mock_dml_color, 'pptx.enum.text': MagicMock(), 'pptx.util': MagicMock()}):
            # 正收益率
            metrics = {"total_return": 0.15}
            reporter.generate("000001", metrics)

            # 验证 RGB 被调用
            mock_rgb_color.assert_called()

    def test_generate_negative_return_color(self):
        """测试负收益率颜色为红色"""
        reporter = PptxReporter()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide_layout = MagicMock()
        mock_textbox = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        mock_prs.slide_layouts = [mock_slide_layout] * 10
        mock_prs.slides.add_slide.return_value = mock_slide
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        mock_textbox.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.add_run = MagicMock()
        mock_slide.shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        mock_cell = MagicMock()
        mock_cell.text_frame.paragraphs = [MagicMock()]
        mock_table.cell.return_value = mock_cell

        mock_pptx = MagicMock()
        mock_pptx.Presentation.return_value = mock_prs
        mock_pptx.PP_ALIGN.CENTER = 'center'
        mock_pptx.Inches = MagicMock(return_value=1.0)
        mock_pptx.Pt = MagicMock()

        # Mock pptx.dml.color 模块中的 RGBColor
        mock_rgb_color = MagicMock()
        mock_dml_color = MagicMock()
        mock_dml_color.RGBColor = mock_rgb_color

        with patch.dict('sys.modules', {'pptx': mock_pptx, 'pptx.dml.color': mock_dml_color, 'pptx.enum.text': MagicMock(), 'pptx.util': MagicMock()}):
            # 负收益率
            metrics = {"total_return": -0.1}
            reporter.generate("000001", metrics)

            mock_rgb_color.assert_called()

    def test_generate_with_empty_metrics(self):
        """测试空 metrics 数据"""
        reporter = PptxReporter()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide_layout = MagicMock()
        mock_textbox = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        mock_prs.slide_layouts = [mock_slide_layout] * 10
        mock_prs.slides.add_slide.return_value = mock_slide
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        mock_textbox.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.add_run = MagicMock()
        mock_slide.shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        mock_cell = MagicMock()
        mock_cell.text_frame.paragraphs = [MagicMock()]
        mock_table.cell.return_value = mock_cell

        mock_pptx = MagicMock()
        mock_pptx.Presentation.return_value = mock_prs
        mock_pptx.RGBColor = MagicMock()
        mock_pptx.PP_ALIGN.CENTER = 'center'
        mock_pptx.Inches = MagicMock(return_value=1.0)
        mock_pptx.Pt = MagicMock()

        with patch.dict('sys.modules', {'pptx': mock_pptx, 'pptx.dml.color': MagicMock(), 'pptx.enum.text': MagicMock(), 'pptx.util': MagicMock()}):
            result = reporter.generate("000001", {})

            assert result.endswith(".pptx")
            mock_prs.save.assert_called_once()

    def test_generate_with_partial_metrics(self):
        """测试部分 metrics 数据"""
        reporter = PptxReporter()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide_layout = MagicMock()
        mock_textbox = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        mock_prs.slide_layouts = [mock_slide_layout] * 10
        mock_prs.slides.add_slide.return_value = mock_slide
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        mock_textbox.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.add_run = MagicMock()
        mock_slide.shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        mock_cell = MagicMock()
        mock_cell.text_frame.paragraphs = [MagicMock()]
        mock_table.cell.return_value = mock_cell

        mock_pptx = MagicMock()
        mock_pptx.Presentation.return_value = mock_prs
        mock_pptx.RGBColor = MagicMock()
        mock_pptx.PP_ALIGN.CENTER = 'center'
        mock_pptx.Inches = MagicMock(return_value=1.0)
        mock_pptx.Pt = MagicMock()

        with patch.dict('sys.modules', {'pptx': mock_pptx, 'pptx.dml.color': MagicMock(), 'pptx.enum.text': MagicMock(), 'pptx.util': MagicMock()}):
            metrics = {
                "total_return": 0.1,
                "sharpe_ratio": 1.2,
            }

            result = reporter.generate("000001", metrics)

            assert result.endswith(".pptx")

    def test_generate_slide_creation(self):
        """测试幻灯片创建逻辑"""
        reporter = PptxReporter()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide_layout = MagicMock()
        mock_textbox = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        mock_prs.slide_layouts = [mock_slide_layout] * 10
        mock_prs.slides.add_slide.return_value = mock_slide
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        mock_textbox.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.add_run = MagicMock()
        mock_slide.shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        mock_cell = MagicMock()
        mock_cell.text_frame.paragraphs = [MagicMock()]
        mock_table.cell.return_value = mock_cell

        mock_pptx = MagicMock()
        mock_pptx.Presentation.return_value = mock_prs
        mock_pptx.RGBColor = MagicMock()
        mock_pptx.PP_ALIGN.CENTER = 'center'
        mock_pptx.Inches = MagicMock(return_value=1.0)
        mock_pptx.Pt = MagicMock()

        with patch.dict('sys.modules', {'pptx': mock_pptx, 'pptx.dml.color': MagicMock(), 'pptx.enum.text': MagicMock(), 'pptx.util': MagicMock()}):
            reporter.generate("000001", {})

            # 验证创建了3张幻灯片
            assert mock_prs.slides.add_slide.call_count == 3

    def test_generate_table_with_numeric_values(self):
        """测试表格中数值格式化"""
        reporter = PptxReporter()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide_layout = MagicMock()
        mock_textbox = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        mock_prs.slide_layouts = [mock_slide_layout] * 10
        mock_prs.slides.add_slide.return_value = mock_slide
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        mock_textbox.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.add_run = MagicMock()
        mock_slide.shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        mock_cell = MagicMock()
        mock_cell.text_frame.paragraphs = [MagicMock()]
        mock_table.cell.return_value = mock_cell

        mock_pptx = MagicMock()
        mock_pptx.Presentation.return_value = mock_prs
        mock_pptx.RGBColor = MagicMock()
        mock_pptx.PP_ALIGN.CENTER = 'center'
        mock_pptx.Inches = MagicMock(return_value=1.0)
        mock_pptx.Pt = MagicMock()

        with patch.dict('sys.modules', {'pptx': mock_pptx, 'pptx.dml.color': MagicMock(), 'pptx.enum.text': MagicMock(), 'pptx.util': MagicMock()}):
            metrics = {
                "total_return": 0.123456,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.1,
                "annualized_return": 0.12,
                "volatility": 0.08,
                "alpha": 0.02,
            }

            reporter.generate("000001", metrics)

            # 验证表格单元格被设置
            assert mock_table.cell.call_count > 0

    def test_generate_table_with_string_values(self):
        """测试表格中字符串值"""
        reporter = PptxReporter()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide_layout = MagicMock()
        mock_textbox = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        mock_prs.slide_layouts = [mock_slide_layout] * 10
        mock_prs.slides.add_slide.return_value = mock_slide
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        mock_textbox.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.add_run = MagicMock()
        mock_slide.shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        mock_cell = MagicMock()
        mock_cell.text_frame.paragraphs = [MagicMock()]
        mock_table.cell.return_value = mock_cell

        mock_pptx = MagicMock()
        mock_pptx.Presentation.return_value = mock_prs
        mock_pptx.PP_ALIGN.CENTER = 'center'
        mock_pptx.Inches = MagicMock(return_value=1.0)
        mock_pptx.Pt = MagicMock()

        mock_rgb_color = MagicMock()
        mock_dml_color = MagicMock()
        mock_dml_color.RGBColor = mock_rgb_color

        with patch.dict('sys.modules', {'pptx': mock_pptx, 'pptx.dml.color': mock_dml_color, 'pptx.enum.text': MagicMock(), 'pptx.util': MagicMock()}):
            # total_return 必须是数值类型（用于格式化），其他可以是字符串
            metrics = {
                "total_return": 0.1,
                "sharpe_ratio": "N/A",
                "max_drawdown": "N/A",
            }

            result = reporter.generate("000001", metrics)

            assert result.endswith(".pptx")

    def test_generate_title_slide(self):
        """测试封面幻灯片"""
        reporter = PptxReporter()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide_layout = MagicMock()
        mock_textbox = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        mock_prs.slide_layouts = [mock_slide_layout] * 10
        mock_prs.slides.add_slide.return_value = mock_slide
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        mock_textbox.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.add_run = MagicMock()
        mock_slide.shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        mock_cell = MagicMock()
        mock_cell.text_frame.paragraphs = [MagicMock()]
        mock_table.cell.return_value = mock_cell

        mock_pptx = MagicMock()
        mock_pptx.Presentation.return_value = mock_prs
        mock_pptx.RGBColor = MagicMock()
        mock_pptx.PP_ALIGN.CENTER = 'center'
        mock_pptx.Inches = MagicMock(return_value=1.0)
        mock_pptx.Pt = MagicMock()

        with patch.dict('sys.modules', {'pptx': mock_pptx, 'pptx.dml.color': MagicMock(), 'pptx.enum.text': MagicMock(), 'pptx.util': MagicMock()}):
            reporter.generate("000001", {})

            # 验证文本框被添加
            assert mock_slide.shapes.add_textbox.call_count >= 3  # 多个幻灯片的文本框

    def test_generate_presentation_size(self):
        """测试演示文稿尺寸设置"""
        reporter = PptxReporter()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide_layout = MagicMock()
        mock_textbox = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        mock_prs.slide_layouts = [mock_slide_layout] * 10
        mock_prs.slides.add_slide.return_value = mock_slide
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        mock_textbox.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.add_run = MagicMock()
        mock_slide.shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        mock_cell = MagicMock()
        mock_cell.text_frame.paragraphs = [MagicMock()]
        mock_table.cell.return_value = mock_cell

        mock_pptx = MagicMock()
        mock_pptx.Presentation.return_value = mock_prs
        mock_pptx.RGBColor = MagicMock()
        mock_pptx.PP_ALIGN.CENTER = 'center'
        mock_pptx.Inches = MagicMock(return_value=1.0)
        mock_pptx.Pt = MagicMock()

        with patch.dict('sys.modules', {'pptx': mock_pptx, 'pptx.dml.color': MagicMock(), 'pptx.enum.text': MagicMock(), 'pptx.util': MagicMock()}):
            reporter.generate("000001", {})

            # 验证尺寸被设置
            assert hasattr(mock_prs, 'slide_width')
            assert hasattr(mock_prs, 'slide_height')

    def test_generate_with_nav_data_ignored(self):
        """测试 nav_data 参数被忽略"""
        reporter = PptxReporter()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide_layout = MagicMock()
        mock_textbox = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        mock_prs.slide_layouts = [mock_slide_layout] * 10
        mock_prs.slides.add_slide.return_value = mock_slide
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        mock_textbox.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.add_run = MagicMock()
        mock_slide.shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        mock_cell = MagicMock()
        mock_cell.text_frame.paragraphs = [MagicMock()]
        mock_table.cell.return_value = mock_cell

        mock_pptx = MagicMock()
        mock_pptx.Presentation.return_value = mock_prs
        mock_pptx.RGBColor = MagicMock()
        mock_pptx.PP_ALIGN.CENTER = 'center'
        mock_pptx.Inches = MagicMock(return_value=1.0)
        mock_pptx.Pt = MagicMock()

        with patch.dict('sys.modules', {'pptx': mock_pptx, 'pptx.dml.color': MagicMock(), 'pptx.enum.text': MagicMock(), 'pptx.util': MagicMock()}):
            result = reporter.generate("000001", {}, nav_data="some_data")

            assert result.endswith(".pptx")

    def test_generate_with_benchmark_data_ignored(self):
        """测试 benchmark_data 参数被忽略"""
        reporter = PptxReporter()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide_layout = MagicMock()
        mock_textbox = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        mock_prs.slide_layouts = [mock_slide_layout] * 10
        mock_prs.slides.add_slide.return_value = mock_slide
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        mock_textbox.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.add_run = MagicMock()
        mock_slide.shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        mock_cell = MagicMock()
        mock_cell.text_frame.paragraphs = [MagicMock()]
        mock_table.cell.return_value = mock_cell

        mock_pptx = MagicMock()
        mock_pptx.Presentation.return_value = mock_prs
        mock_pptx.RGBColor = MagicMock()
        mock_pptx.PP_ALIGN.CENTER = 'center'
        mock_pptx.Inches = MagicMock(return_value=1.0)
        mock_pptx.Pt = MagicMock()

        with patch.dict('sys.modules', {'pptx': mock_pptx, 'pptx.dml.color': MagicMock(), 'pptx.enum.text': MagicMock(), 'pptx.util': MagicMock()}):
            result = reporter.generate("000001", {}, benchmark_data="benchmark")

            assert result.endswith(".pptx")

    def test_save(self):
        """测试保存PPT"""
        reporter = PptxReporter()
        with patch('shutil.copy2') as mock_copy:
            reporter.save("/tmp/test.pptx", "/output/test.pptx")
            mock_copy.assert_called_once_with("/tmp/test.pptx", "/output/test.pptx")

    def test_save_with_different_paths(self):
        """测试保存到不同路径"""
        reporter = PptxReporter()
        with patch('shutil.copy2') as mock_copy:
            reporter.save("/source/report.pptx", "/destination/report.pptx")
            mock_copy.assert_called_once()

    def test_generate_investment_summary_slide(self):
        """测试投资摘要幻灯片"""
        reporter = PptxReporter()

        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_slide_layout = MagicMock()
        mock_textbox = MagicMock()
        mock_text_frame = MagicMock()
        mock_paragraph = MagicMock()
        mock_table_shape = MagicMock()
        mock_table = MagicMock()

        mock_prs.slide_layouts = [mock_slide_layout] * 10
        mock_prs.slides.add_slide.return_value = mock_slide
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        mock_textbox.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.add_run = MagicMock()
        mock_slide.shapes.add_table.return_value = mock_table_shape
        mock_table_shape.table = mock_table

        mock_cell = MagicMock()
        mock_cell.text_frame.paragraphs = [MagicMock()]
        mock_table.cell.return_value = mock_cell

        mock_pptx = MagicMock()
        mock_pptx.Presentation.return_value = mock_prs
        mock_pptx.RGBColor = MagicMock()
        mock_pptx.PP_ALIGN.CENTER = 'center'
        mock_pptx.Inches = MagicMock(return_value=1.0)
        mock_pptx.Pt = MagicMock()

        with patch.dict('sys.modules', {'pptx': mock_pptx, 'pptx.dml.color': MagicMock(), 'pptx.enum.text': MagicMock(), 'pptx.util': MagicMock()}):
            metrics = {
                "total_return": 0.15,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.1,
            }

            reporter.generate("000001", metrics)

            # 验证第三张幻灯片（投资摘要）被创建
            assert mock_prs.slides.add_slide.call_count == 3
