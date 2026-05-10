"""
交互式命令测试.

测试 fund_cli.commands.interactive_cmd 模块。
"""

import pytest
from typer.testing import CliRunner

from fund_cli.commands.interactive_cmd import app, interactive_mode

runner = CliRunner()


class TestInteractiveMode:
    """测试 interactive_mode 函数."""

    def test_interactive_mode_exists(self):
        """测试交互模式函数存在."""
        assert callable(interactive_mode)

    def test_interactive_mode_help(self):
        """测试交互模式帮助."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # 帮助信息包含 REPL
        assert "REPL" in result.output or "交互" in result.output


class TestInteractiveApp:
    """测试交互式应用结构."""

    def test_app_exists(self):
        """测试应用存在."""
        assert app is not None

    def test_app_has_command(self):
        """测试应用包含命令."""
        commands = app.registered_commands
        assert len(commands) > 0
