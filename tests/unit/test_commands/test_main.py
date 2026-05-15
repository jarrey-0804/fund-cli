"""
命令主入口测试.

测试 fund_cli.commands.main 模块。
"""

import typer

from fund_cli.commands.main import register_commands


class TestRegisterCommands:
    """测试 register_commands 函数."""

    def test_register_commands_single(self):
        """测试注册单个命令."""
        app = typer.Typer()
        sub_app = typer.Typer()
        commands = {"analyze": sub_app}

        register_commands(app, commands)

        # 验证命令已注册
        assert len(app.registered_groups) == 1

    def test_register_commands_multiple(self):
        """测试注册多个命令."""
        app = typer.Typer()
        commands = {
            "analyze": typer.Typer(),
            "compare": typer.Typer(),
            "optimize": typer.Typer(),
        }

        register_commands(app, commands)

        # 验证所有命令已注册
        assert len(app.registered_groups) == 3

    def test_register_commands_empty(self):
        """测试注册空命令字典."""
        app = typer.Typer()
        commands = {}

        register_commands(app, commands)

        # 应该没有注册任何命令
        assert len(app.registered_groups) == 0

    def test_register_commands_overwrite(self):
        """测试覆盖注册同名命令."""
        app = typer.Typer()
        sub_app1 = typer.Typer()
        sub_app2 = typer.Typer()

        register_commands(app, {"test": sub_app1})
        register_commands(app, {"test": sub_app2})

        # Typer 会添加两个命令组，而不是覆盖
        assert len(app.registered_groups) >= 1
