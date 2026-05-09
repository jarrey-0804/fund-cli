# -*- coding: utf-8 -*-
"""
report_cmd 报告生成命令单元测试

测试覆盖：
- generate 命令各种参数组合
- 缺少必要参数时的错误提示
- 不支持的报告类型和格式
- list_templates 命令
- get_reporter 工厂函数
- REPORTERS 和 REPORT_TYPES 常量
"""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from fund_cli.commands.report_cmd import (
    REPORTERS,
    REPORT_TYPES,
    app,
    get_reporter,
)

runner = CliRunner()


# =============================================================================
# 测试类：常量与工厂函数
# =============================================================================


class TestReportConstants:
    """测试报告相关常量"""

    def test_reporters_dict_keys(self):
        """测试 REPORTERS 包含预期的格式"""
        assert "html" in REPORTERS
        assert "markdown" in REPORTERS
        assert "pdf" in REPORTERS

    def test_report_types_list(self):
        """测试 REPORT_TYPES 包含预期的类型"""
        assert "single_fund" in REPORT_TYPES
        assert "portfolio" in REPORT_TYPES
        assert "market_flow" in REPORT_TYPES
        assert "risk_control" in REPORT_TYPES


class TestGetReporter:
    """测试 get_reporter 工厂函数"""

    def test_get_html_reporter(self):
        """测试获取 HTML 报告生成器"""
        reporter = get_reporter("html")
        from fund_cli.core.reporters.html_reporter import HtmlReporter
        assert isinstance(reporter, HtmlReporter)

    def test_get_markdown_reporter(self):
        """测试获取 Markdown 报告生成器"""
        reporter = get_reporter("markdown")
        from fund_cli.core.reporters.markdown_reporter import MarkdownReporter
        assert isinstance(reporter, MarkdownReporter)

    def test_get_unsupported_reporter(self):
        """测试获取不支持的格式时抛出异常"""
        with pytest.raises(Exception):
            get_reporter("excel")

    def test_get_reporter_returns_instance(self):
        """测试 get_reporter 返回实例而非类"""
        reporter = get_reporter("html")
        assert hasattr(reporter, "generate")
        assert hasattr(reporter, "save")


# =============================================================================
# 测试类：generate 命令
# =============================================================================


class TestGenerateCommand:
    """测试 generate 命令"""

    def _make_mock_reporter(self):
        """创建模拟的报告生成器"""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "<html>mock report</html>"
        return mock_instance

    def test_generate_single_fund_html(self):
        """测试生成单只基金 HTML 报告"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            result = runner.invoke(
                app,
                ["generate", "--type", "single_fund", "--fund", "000001", "--format", "html"],
            )
            assert result.exit_code == 0
            mock_instance.generate.assert_called_once()
            mock_instance.save.assert_called_once()

    def test_generate_single_fund_markdown(self):
        """测试生成单只基金 Markdown 报告"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            result = runner.invoke(
                app,
                ["generate", "--type", "single_fund", "--fund", "000001", "--format", "markdown"],
            )
            assert result.exit_code == 0
            mock_instance.generate.assert_called_once()
            mock_instance.save.assert_called_once()

    def test_generate_single_fund_pdf(self):
        """测试生成单只基金 PDF 报告"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            result = runner.invoke(
                app,
                ["generate", "--type", "single_fund", "--fund", "000001", "--format", "pdf"],
            )
            assert result.exit_code == 0
            mock_instance.generate.assert_called_once()
            mock_instance.save.assert_called_once()

    def test_generate_portfolio(self):
        """测试生成投资组合报告"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            result = runner.invoke(
                app,
                ["generate", "--type", "portfolio", "--funds", "000001,000002", "--format", "html"],
            )
            assert result.exit_code == 0
            mock_instance.generate.assert_called_once()

    def test_generate_market_flow(self):
        """测试生成市场资金流向报告"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            result = runner.invoke(
                app,
                ["generate", "--type", "market_flow", "--format", "html"],
            )
            assert result.exit_code == 0
            mock_instance.generate.assert_called_once()

    def test_generate_risk_control(self):
        """测试生成风控报告"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            result = runner.invoke(
                app,
                ["generate", "--type", "risk_control", "--format", "html"],
            )
            assert result.exit_code == 0
            mock_instance.generate.assert_called_once()

    def test_generate_with_output(self):
        """测试指定输出文件路径"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            result = runner.invoke(
                app,
                [
                    "generate", "--type", "single_fund", "--fund", "000001",
                    "--format", "html", "--output", "/tmp/my_report.html",
                ],
            )
            assert result.exit_code == 0
            mock_instance.save.assert_called_once_with(
                "<html>mock report</html>", "/tmp/my_report.html"
            )

    def test_generate_with_template(self):
        """测试指定自定义模板路径"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            result = runner.invoke(
                app,
                [
                    "generate", "--type", "single_fund", "--fund", "000001",
                    "--format", "html", "--template", "/custom/template.html",
                ],
            )
            assert result.exit_code == 0

    def test_generate_missing_fund_for_single_fund(self):
        """测试 single_fund 类型缺少 --fund 参数时报错"""
        result = runner.invoke(app, ["generate", "--type", "single_fund"])
        assert result.exit_code != 0
        assert "基金代码" in result.output

    def test_generate_missing_funds_for_portfolio(self):
        """测试 portfolio 类型缺少 --funds 参数时报错"""
        result = runner.invoke(app, ["generate", "--type", "portfolio"])
        assert result.exit_code != 0
        assert "基金代码" in result.output

    def test_generate_unsupported_type(self):
        """测试不支持的报告类型"""
        result = runner.invoke(
            app,
            ["generate", "--type", "invalid_type", "--fund", "000001"],
        )
        assert result.exit_code != 0
        assert "不支持的报告类型" in result.output

    def test_generate_unsupported_format(self):
        """测试不支持的输出格式"""
        result = runner.invoke(
            app,
            ["generate", "--type", "single_fund", "--fund", "000001", "--format", "excel"],
        )
        assert result.exit_code != 0
        assert "不支持的格式" in result.output

    def test_generate_default_format(self):
        """测试默认使用 html 格式"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance) as mock_get:
            result = runner.invoke(
                app,
                ["generate", "--type", "single_fund", "--fund", "000001"],
            )
            assert result.exit_code == 0
            mock_get.assert_called_once_with("html")

    def test_generate_default_type(self):
        """测试默认报告类型为 single_fund"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            result = runner.invoke(
                app,
                ["generate", "--fund", "000001"],
            )
            assert result.exit_code == 0

    def test_generate_output_message(self):
        """测试生成报告后输出提示信息"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            result = runner.invoke(
                app,
                ["generate", "--type", "single_fund", "--fund", "000001", "--format", "html"],
            )
            assert result.exit_code == 0
            assert "报告已生成" in result.output

    def test_generate_short_options(self):
        """测试短选项参数"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            result = runner.invoke(
                app,
                ["generate", "-t", "single_fund", "-f", "000001", "-o", "/tmp/out.html"],
            )
            assert result.exit_code == 0

    def test_generate_passes_fund_code_to_reporter(self):
        """测试 generate 将基金代码传递给 reporter"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            runner.invoke(
                app,
                ["generate", "--type", "single_fund", "--fund", "110011"],
            )
            mock_instance.generate.assert_called_once_with(fund_code="110011", metrics={})

    def test_generate_portfolio_passes_first_fund(self):
        """测试 portfolio 类型将第一个基金代码传递给 reporter"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            runner.invoke(
                app,
                ["generate", "--type", "portfolio", "--funds", "000001,000002,000003"],
            )
            mock_instance.generate.assert_called_once_with(fund_code="000001", metrics={})

    def test_generate_market_flow_uses_market_code(self):
        """测试 market_flow 类型使用 MARKET 作为基金代码"""
        mock_instance = self._make_mock_reporter()
        with patch("fund_cli.commands.report_cmd.get_reporter", return_value=mock_instance):
            runner.invoke(
                app,
                ["generate", "--type", "market_flow"],
            )
            mock_instance.generate.assert_called_once_with(fund_code="MARKET", metrics={})


# =============================================================================
# 测试类：list-templates 命令
# =============================================================================


class TestListTemplatesCommand:
    """测试 list-templates 命令"""

    def test_list_templates(self):
        """测试列出可用模板"""
        with patch("fund_cli.commands.report_cmd.get_template_engine") as MockEngine:
            mock_engine = MagicMock()
            mock_engine.list_templates.return_value = [
                "base.html",
                "single_fund/report.html",
            ]
            MockEngine.return_value = mock_engine
            result = runner.invoke(app, ["list-templates"])
            assert result.exit_code == 0
            assert "可用模板" in result.output
            assert "base.html" in result.output
            assert "single_fund/report.html" in result.output

    def test_list_templates_empty(self):
        """测试没有可用模板时的输出"""
        with patch("fund_cli.commands.report_cmd.get_template_engine") as MockEngine:
            mock_engine = MagicMock()
            mock_engine.list_templates.return_value = []
            MockEngine.return_value = mock_engine
            result = runner.invoke(app, ["list-templates"])
            assert result.exit_code == 0
            assert "可用模板" in result.output

    def test_list_templates_with_exception(self):
        """测试模板引擎异常时的处理"""
        with patch("fund_cli.commands.report_cmd.get_template_engine") as MockEngine:
            MockEngine.side_effect = Exception("模板引擎初始化失败")
            result = runner.invoke(app, ["list-templates"])
            assert result.exit_code != 0
