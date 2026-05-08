"""
数据管理命令

提供数据缓存管理、数据导出等功能。
"""

import typer
from rich.console import Console
from rich.table import Table

from fund_cli.core.data_manager import get_data_manager

app = typer.Typer(help="数据管理命令")
console = Console()


@app.command("stats")
def cache_stats() -> None:
    """查看数据缓存统计信息。"""
    try:
        dm = get_data_manager()
        stats = dm.get_cache_stats()

        table = Table(title="缓存统计")
        table.add_column("指标", style="cyan")
        table.add_column("值", style="green")

        table.add_row("缓存条目数", str(stats.get("size", 0)))
        table.add_row("缓存大小", f"{stats.get('volume', 0) / 1024 / 1024:.2f} MB")
        table.add_row("缓存目录", stats.get("directory", "-"))

        console.print(table)

    except Exception as e:
        console.print(f"[red]获取缓存统计失败: {e}[/red]")


@app.command("clear")
def clear_cache() -> None:
    """清空数据缓存。"""
    try:
        dm = get_data_manager()
        dm.clear_cache()
        console.print("[green]缓存已清空[/green]")
    except Exception as e:
        console.print(f"[red]清空缓存失败: {e}[/red]")


@app.command("quality")
def data_quality(fund_code: str = typer.Argument(..., help="基金代码")):
    """数据质量检查 (FUND-DATA-005)"""
    from fund_cli.core.data_quality import DataQualityChecker

    checker = DataQualityChecker()
    result = checker.check(fund_code)
    console.print(f"\n[bold]{fund_code}[/bold] 数据质量报告：")
    console.print(f"  整体状态: [bold]{result.get('overall_status', 'unknown')}[/bold]")
    if "completeness" in result:
        c = result["completeness"]
        console.print(
            f"  完整性评分: {c['score']}/100 (共{c['total_rows']}行, 缺失{sum(c['missing_values'].values())}个)"
        )
    if "accuracy" in result:
        a = result["accuracy"]
        console.print(f"  准确性评分: {a['score']}/100 (异常值{a['anomaly_count']}个)")
    if "timeliness" in result:
        t = result["timeliness"]
        console.print(f"  时效性: {t['status']} (最后更新: {t.get('last_date', 'N/A')})")


@app.command("update")
def incremental_update(fund_code: str = typer.Argument(..., help="基金代码")):
    """增量更新 (FUND-DATA-006)"""
    from fund_cli.core.data_quality import DataQualityChecker

    checker = DataQualityChecker()
    result = checker.incremental_update(fund_code)
    if result["status"] == "success":
        console.print(f"[green]{fund_code}: 新增 {result['new_records']} 条记录[/green]")
    else:
        console.print(f"[red]{fund_code}: 更新失败 - {result.get('message', '')}[/red]")


@app.command("batch-download")
def batch_download(
    fund_codes: str = typer.Argument(..., help="基金代码，逗号分隔"),
    output: str = typer.Option(None, help="输出目录"),
):
    """批量下载 (FUND-DATA-007)"""
    from fund_cli.core.data_quality import DataQualityChecker

    codes = [c.strip() for c in fund_codes.split(",")]
    checker = DataQualityChecker()
    with console.status("正在批量下载..."):
        result = checker.batch_download(codes)
    console.print("\n[bold]批量下载完成[/bold]")
    console.print(f"  总计: {result['total']} 只基金")
    console.print(f"  成功: [green]{result['success']}[/green]")
    console.print(f"  失败: [red]{result['failed']}[/red]")
    for code, detail in result["details"].items():
        if detail["status"] == "error":
            console.print(f"    {code}: {detail.get('message', '失败')}")


if __name__ == "__main__":
    app()
