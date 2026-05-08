"""监控预警命令"""

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="监控预警命令")
console = Console()


def _get_monitor(config_dir: str = "~/.fund_cli"):
    from fund_cli.core.monitor import FundMonitor

    return FundMonitor(config_dir=config_dir)


@app.command("add")
def add_to_pool(
    fund_code: str = typer.Argument(..., help="基金代码"),
    group: str = typer.Option("default", help="分组名称"),
):
    """添加基金到监控池 (FUND-MONITOR-001)"""
    monitor = _get_monitor()
    monitor.add_to_pool(fund_code, group)
    console.print(f"[green]已添加 {fund_code} 到 {group} 监控池[/green]")


@app.command("remove")
def remove_from_pool(
    fund_code: str = typer.Argument(..., help="基金代码"),
    group: str = typer.Option(None, help="分组名称"),
):
    """从监控池移除基金"""
    monitor = _get_monitor()
    if monitor.remove_from_pool(fund_code, group):
        console.print(f"[green]已从监控池移除 {fund_code}[/green]")
    else:
        console.print(f"[yellow]{fund_code} 不在监控池中[/yellow]")


@app.command("list")
def list_pool(
    group: str = typer.Option(None, help="分组名称"),
):
    """列出监控池中的基金 (FUND-MONITOR-001)"""
    monitor = _get_monitor()
    funds = monitor.list_pool(group)
    if not funds:
        console.print("[yellow]监控池为空[/yellow]")
        return

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("基金代码", style="cyan")
    table.add_column("分组")
    table.add_column("添加时间")
    for f in funds:
        table.add_row(f["code"], f.get("group", "default"), f.get("added_at", ""))
    console.print(table)
    console.print(f"\n共 {len(funds)} 只基金")


@app.command("watch")
def watch_fund(
    fund_code: str = typer.Argument(..., help="基金代码"),
    threshold: float = typer.Option(-2.0, help="预警阈值(%)"),
):
    """监控基金净值变动 (FUND-MONITOR-002)"""
    monitor = _get_monitor()
    monitor.add_to_pool(fund_code)
    monitor.add_rule(fund_code, "nav_change", threshold)
    console.print(f"[green]已开始监控 {fund_code}，阈值: {threshold}%[/green]")


@app.command("check")
def check_all():
    """检查所有监控基金的净值变动"""
    monitor = _get_monitor()
    codes = monitor.get_all_fund_codes()
    if not codes:
        console.print("[yellow]监控池为空，请先添加基金[/yellow]")
        return

    console.print(f"正在检查 {len(codes)} 只基金...")
    alerts = monitor.check_nav_changes(codes)
    if alerts:
        table = Table(show_header=True, header_style="bold red")
        table.add_column("基金代码", style="cyan")
        table.add_column("日收益率", justify="right", style="red")
        table.add_column("阈值", justify="right")
        for a in alerts:
            table.add_row(a["fund_code"], f"{a['daily_return']:.2f}%", f"{a['threshold']:.2f}%")
        console.print(table)
        console.print(f"\n[bold red]{len(alerts)} 只基金触发预警[/bold red]")
    else:
        console.print("[green]所有基金正常，无预警[/green]")


@app.command("alert")
def alert_list():
    """查看预警规则"""
    monitor = _get_monitor()
    rules = monitor.get_rules()
    if not rules:
        console.print("[yellow]暂无预警规则[/yellow]")
        return

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("基金代码", style="cyan")
    table.add_column("规则类型")
    table.add_column("阈值", justify="right")
    for r in rules:
        table.add_row(r["fund_code"], r["rule_type"], f"{r['threshold']:.2f}%")
    console.print(table)
