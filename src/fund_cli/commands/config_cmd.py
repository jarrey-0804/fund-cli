"""
配置管理命令

提供配置查看和设置功能。
"""

import typer
from rich.console import Console
from rich.table import Table

from fund_cli.config import get_config

app = typer.Typer(help="配置管理命令")
console = Console()


@app.command("show")
def show_config() -> None:
    """显示当前配置。"""
    try:
        config = get_config()

        table = Table(title="当前配置")
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")

        # 应用配置
        table.add_row("应用名称", config.app_name)
        table.add_row("调试模式", str(config.debug))

        # 数据配置
        table.add_row("AKShare启用", str(config.data.akshare_enabled))
        table.add_row("缓存TTL", f"{config.data.cache_ttl}秒")
        table.add_row("缓存目录", config.data.cache_dir)

        # 分析配置
        table.add_row("无风险利率", f"{config.analysis.risk_free_rate * 100}%")
        table.add_row("默认基准", config.analysis.default_benchmark)

        console.print(table)

    except Exception as e:
        console.print(f"[red]获取配置失败: {e}[/red]")


@app.command("output")
def output_config(
    format: str = typer.Option(None, help="默认输出格式: table/csv/json"),
    encoding: str = typer.Option(None, help="CSV编码"),
    decimal: int = typer.Option(None, help="数字小数位"),
):
    """输出格式配置 (FUND-CONFIG-004)"""
    from fund_cli.config import AppConfig

    config = AppConfig()
    if format:
        config.output.default_format = format
    if encoding:
        config.output.csv_encoding = encoding
    if decimal is not None:
        config.output.number_decimal = decimal

    console.print("\n[bold]输出格式配置[/bold]")
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("配置项", style="cyan")
    table.add_column("当前值")
    table.add_row("默认格式", config.output.default_format)
    table.add_row("CSV编码", config.output.csv_encoding)
    table.add_row("CSV分隔符", config.output.csv_delimiter)
    table.add_row("JSON缩进", str(config.output.json_indent))
    table.add_row("数字小数位", str(config.output.number_decimal))
    table.add_row("日期格式", config.output.date_format)
    console.print(table)


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help="配置键"),
    value: str = typer.Argument(..., help="配置值"),
):
    """设置配置项"""
    from fund_cli.config import AppConfig

    AppConfig()
    console.print(f"[green]配置 {key} = {value} 已设置[/green]")
    console.print("[yellow]注意: 当前仅显示，持久化配置请编辑 .env 文件[/yellow]")


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context) -> None:
    """默认显示配置"""
    if ctx.invoked_subcommand is None:
        show_config()


if __name__ == "__main__":
    app()
