"""
Fund CLI 主入口

专业基金分析命令行工具的主程序入口。
"""

import typer
from rich.console import Console

from fund_cli import __version__

# 创建主应用
app = typer.Typer(
    name="fund",
    help="专业基金分析CLI工具 - 面向机构客户",
    add_completion=True,
    rich_markup_mode="rich",
)

# 全局控制台实例
console = Console()


def version_callback(value: bool) -> None:
    """显示版本信息"""
    if value:
        console.print(f"[bold blue]Fund CLI[/bold blue] 版本: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="显示版本信息",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """
    Fund CLI - 专业基金分析命令行工具

    面向机构客户的基金分析工具，支持基金筛选、业绩分析、组合优化等功能。

    使用 --help 查看各子命令的详细帮助。
    """
    pass


# 导入子命令模块
from fund_cli.commands import (  # noqa: E402
    ai_cmd,
    analyze_cmd,
    compare_cmd,
    config_cmd,
    data_cmd,
    filter_cmd,
    holding_cmd,
    interactive_cmd,
    manager_cmd,
    monitor_cmd,
    optimize_cmd,
)

# 注册子命令
app.add_typer(filter_cmd.app, name="filter")
app.add_typer(analyze_cmd.app, name="analyze")
app.add_typer(compare_cmd.app, name="compare")
app.add_typer(optimize_cmd.app, name="optimize")
app.add_typer(monitor_cmd.app, name="monitor")
app.add_typer(data_cmd.app, name="data")
app.add_typer(config_cmd.app, name="config")
app.add_typer(ai_cmd.app, name="ai")
app.add_typer(holding_cmd.app, name="holding")
app.add_typer(manager_cmd.app, name="manager")
app.add_typer(interactive_cmd.app, name="interactive")


# 直接调用的命令
@app.command("info")
def info(
    fund_code: str = typer.Argument(..., help="基金代码（6位数字）"),
) -> None:
    """
    查看基金基础信息。

    示例:
        fund info 000001
    """
    from fund_cli.commands.analyze_cmd import info_fund

    info_fund(fund_code)


if __name__ == "__main__":
    app()
