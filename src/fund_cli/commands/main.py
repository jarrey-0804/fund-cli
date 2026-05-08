"""
命令主入口

CLI 命令模块的主入口，提供命令注册辅助功能。
"""


def register_commands(app, commands: dict) -> None:
    """
    批量注册子命令

    Args:
        app: Typer 主应用
        commands: {名称: 子应用} 字典
    """
    for name, sub_app in commands.items():
        app.add_typer(sub_app, name=name)
