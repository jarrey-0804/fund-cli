"""
基金经理命令

提供基金经理信息查询、业绩统计和稳定性分析功能。
"""

import typer
from rich.console import Console
from rich.table import Table

from fund_cli.analysis.manager import ManagerAnalyzer
from fund_cli.core.data_manager import DataManager

app = typer.Typer(help="基金经理命令")
console = Console()


@app.command("info")
def manager_info(fund_code: str = typer.Argument(..., help="基金代码")):
    """查询基金经理信息 (FUND-MANAGER-001)"""
    dm = DataManager()
    try:
        manager_data = dm.get_fund_manager(fund_code)
        analyzer = ManagerAnalyzer()
        info = analyzer.manager_info(manager_data)
        console.print("\n[bold]基金经理信息[/bold]")
        console.print(f"  姓名: {info['name']}")
        console.print(f"  基金: {info['fund_name']}")
        console.print(f"  公司: {info['company']}")
        console.print(f"  任职日期: {info['start_date']}")
        console.print(f"  任职天数: {info['tenure_days']}")
    except Exception as e:
        console.print(f"[red]获取经理信息失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("performance")
def manager_performance(fund_code: str = typer.Argument(..., help="基金代码")):
    """经理业绩统计 (FUND-MANAGER-002)"""
    dm = DataManager()
    try:
        manager_data = dm.get_fund_manager(fund_code)
        analyzer = ManagerAnalyzer()
        stats = analyzer.performance_stats(manager_data)
        console.print(f"\n[bold]{manager_data.get('name', '')}[/bold] 业绩统计：")
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("指标", style="cyan")
        table.add_column("值", justify="right")
        table.add_row("管理基金数", str(stats["total_funds"]))
        table.add_row("平均收益率", f"{stats['avg_return']:.2f}%")
        table.add_row("最佳基金", stats["best_fund"])
        table.add_row("最佳收益率", f"{stats['best_return']:.2f}%")
        console.print(table)
    except Exception as e:
        console.print(f"[red]业绩统计失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("stability")
def manager_stability(fund_code: str = typer.Argument(..., help="基金代码")):
    """经理稳定性分析 (FUND-MANAGER-003)"""
    dm = DataManager()
    try:
        manager_data = dm.get_fund_manager(fund_code)
        analyzer = ManagerAnalyzer()
        stability = analyzer.stability_analysis(manager_data)
        console.print(f"\n[bold]{manager_data.get('name', '')}[/bold] 稳定性分析：")
        console.print(f"  任职年限: {stability['tenure_years']}年")
        console.print(f"  稳定性等级: [bold]{stability['stability_level']}[/bold]")
        console.print(f"  稳定性评分: {stability['stability_score']}/5")
        console.print(f"  多基金管理: {'是' if stability['multi_fund_manager'] else '否'}")
    except Exception as e:
        console.print(f"[red]稳定性分析失败: {e}[/red]")
        raise typer.Exit(1) from None
