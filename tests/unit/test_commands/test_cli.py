"""
单元测试 - CLI 命令
"""

from typer.testing import CliRunner

from fund_cli.cli import app

runner = CliRunner()


class TestCLI:
    """CLI 测试"""

    def test_version(self):
        """测试版本显示"""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "3.1.0" in result.output

    def test_help(self):
        """测试帮助显示"""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Fund CLI" in result.output or "fund" in result.output

    def test_info_command_help(self):
        """测试 info 命令帮助"""
        result = runner.invoke(app, ["info", "--help"])

        assert result.exit_code == 0
        assert "基金代码" in result.output


class TestFilterCommands:
    """筛选命令测试"""

    def test_filter_basic_help(self):
        """测试基础筛选帮助"""
        result = runner.invoke(app, ["filter", "basic", "--help"])

        assert result.exit_code == 0
        assert "基金类型" in result.output or "fund_type" in result.output.lower()


class TestAnalyzeCommands:
    """分析命令测试"""

    def test_analyze_info_help(self):
        """测试基金信息命令帮助"""
        result = runner.invoke(app, ["analyze", "info", "--help"])

        assert result.exit_code == 0

    def test_analyze_nav_help(self):
        """测试净值命令帮助"""
        result = runner.invoke(app, ["analyze", "nav", "--help"])

        assert result.exit_code == 0

    def test_analyze_metrics_help(self):
        """测试指标分析命令帮助"""
        result = runner.invoke(app, ["analyze", "metrics", "--help"])

        assert result.exit_code == 0


class TestCompareCommands:
    """对比命令测试"""

    def test_compare_funds_help(self):
        """测试对比命令帮助"""
        result = runner.invoke(app, ["compare", "funds", "--help"])

        assert result.exit_code == 0


class TestDataCommands:
    """数据命令测试"""

    def test_data_stats_help(self):
        """测试缓存统计命令帮助"""
        result = runner.invoke(app, ["data", "stats", "--help"])

        assert result.exit_code == 0

    def test_data_clear_help(self):
        """测试清空缓存命令帮助"""
        result = runner.invoke(app, ["data", "clear", "--help"])

        assert result.exit_code == 0


class TestConfigCommands:
    """配置命令测试"""

    def test_config_show(self):
        """测试显示配置"""
        result = runner.invoke(app, ["config", "show"])

        assert result.exit_code == 0
        assert "Fund CLI" in result.output or "配置" in result.output
