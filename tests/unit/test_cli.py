"""
CLI 主入口测试.

测试 fund 命令的主入口和全局命令。
"""

from unittest.mock import patch

from typer.testing import CliRunner

from fund_cli.cli import app, version_callback

runner = CliRunner()


class TestCLIMain:
    """测试 CLI 主入口."""

    def test_cli_help(self):
        """测试 CLI 帮助信息."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_cli_version_flag(self):
        """测试 --version 标志."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "3.8.1" in result.output

    def test_cli_version_short_flag(self):
        """测试 -v 短标志."""
        result = runner.invoke(app, ["-v"])

        assert result.exit_code == 0
        assert "3.8.1" in result.output

    def test_version_command(self):
        """测试 version 命令."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "Fund CLI" in result.output
        assert "3.8.1" in result.output

    def test_version_callback(self):
        """测试 version_callback 函数."""
        import typer
        # 应该抛出 typer.Exit
        try:
            version_callback(True)
            raise AssertionError("应该抛出异常")
        except typer.Exit:
            pass  # 正确

    def test_version_callback_false(self):
        """测试 version_callback 参数为 False."""
        # 不应该抛出异常
        version_callback(False)


class TestDoctorCommand:
    """测试 doctor 命令."""

    def test_doctor_command(self):
        """测试 doctor 诊断命令."""
        result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "环境诊断" in result.output
        assert "Python 版本" in result.output

    def test_doctor_checks_core_deps(self):
        """测试 doctor 检查核心依赖."""
        result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "核心依赖" in result.output
        assert "typer" in result.output.lower() or "CLI框架" in result.output

    def test_doctor_checks_data_sources(self):
        """测试 doctor 检查数据源."""
        result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "数据源" in result.output

    def test_doctor_checks_ai_deps(self):
        """测试 doctor 检查 AI 依赖."""
        result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "AI" in result.output

    def test_doctor_shows_summary(self):
        """测试 doctor 显示汇总结果."""
        result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "诊断结果" in result.output


class TestInfoCommand:
    """测试 info 命令."""

    @patch("fund_cli.commands.analyze_cmd.info_fund")
    def test_info_command(self, mock_info):
        """测试 info 命令调用."""
        runner.invoke(app, ["info", "000001"])

        # 命令应该被调用
        mock_info.assert_called_once_with("000001")


class TestCLISubcommands:
    """测试子命令注册."""

    def test_filter_subcommand_exists(self):
        """测试 filter 子命令存在."""
        result = runner.invoke(app, ["filter", "--help"])
        assert result.exit_code == 0

    def test_analyze_subcommand_exists(self):
        """测试 analyze 子命令存在."""
        result = runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0

    def test_compare_subcommand_exists(self):
        """测试 compare 子命令存在."""
        result = runner.invoke(app, ["compare", "--help"])
        assert result.exit_code == 0

    def test_optimize_subcommand_exists(self):
        """测试 optimize 子命令存在."""
        result = runner.invoke(app, ["optimize", "--help"])
        assert result.exit_code == 0

    def test_monitor_subcommand_exists(self):
        """测试 monitor 子命令存在."""
        result = runner.invoke(app, ["monitor", "--help"])
        assert result.exit_code == 0

    def test_data_subcommand_exists(self):
        """测试 data 子命令存在."""
        result = runner.invoke(app, ["data", "--help"])
        assert result.exit_code == 0

    def test_config_subcommand_exists(self):
        """测试 config 子命令存在."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0

    def test_ai_subcommand_exists(self):
        """测试 ai 子命令存在."""
        result = runner.invoke(app, ["ai", "--help"])
        assert result.exit_code == 0

    def test_holding_subcommand_exists(self):
        """测试 holding 子命令存在."""
        result = runner.invoke(app, ["holding", "--help"])
        assert result.exit_code == 0

    def test_manager_subcommand_exists(self):
        """测试 manager 子命令存在."""
        result = runner.invoke(app, ["manager", "--help"])
        assert result.exit_code == 0

    def test_interactive_subcommand_exists(self):
        """测试 interactive 子命令存在."""
        result = runner.invoke(app, ["interactive", "--help"])
        assert result.exit_code == 0

    def test_report_subcommand_exists(self):
        """测试 report 子命令存在."""
        result = runner.invoke(app, ["report", "--help"])
        assert result.exit_code == 0


class TestCLIAppStructure:
    """测试 CLI 应用结构."""

    def test_app_exists(self):
        """测试应用存在."""
        assert app is not None

    def test_app_name(self):
        """测试应用名称."""
        assert app.info.name == "fund"

    def test_app_has_help(self):
        """测试应用有帮助信息."""
        assert app.info.help is not None


class TestCLIMainEntry:
    """测试 CLI 主入口点."""

    def test_main_entry_no_args(self):
        """测试主入口无参数."""
        result = runner.invoke(app, [])
        # 无参数时应该显示帮助或正常退出
        assert result.exit_code in [0, 2]

    def test_main_callback(self):
        """测试主回调函数."""
        # 主回调应该正常执行
        result = runner.invoke(app, [])
        assert result.exit_code in [0, 2]


class TestDoctorDetailedChecks:
    """测试 doctor 详细检查项."""

    def test_doctor_checks_config_file(self):
        """测试 doctor 检查配置文件."""
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "配置" in result.output or ".env" in result.output

    def test_doctor_checks_cache_dir(self):
        """测试 doctor 检查缓存目录."""
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "缓存" in result.output or "cache" in result.output.lower()

    def test_doctor_checks_database(self):
        """测试 doctor 检查数据库配置."""
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "数据库" in result.output or "PostgreSQL" in result.output
