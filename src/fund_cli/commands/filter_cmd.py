"""
基金筛选命令

提供基金筛选、排序、导出等功能。
"""

from enum import Enum

import typer
from rich.console import Console

from fund_cli.core.data_manager import get_data_manager
from fund_cli.views.tables import TableRenderer

app = typer.Typer(help="基金筛选命令")
console = Console()


class SortField(str, Enum):
    """排序字段"""

    return_1y = "return_1y"
    return_3y = "return_3y"
    sharpe = "sharpe"
    max_drawdown = "max_drawdown"
    scale = "scale"


class SortOrder(str, Enum):
    """排序方向"""

    asc = "asc"
    desc = "desc"


def _render_fund_table(df) -> None:
    """渲染基金列表表格"""
    renderer = TableRenderer()
    table = renderer.render_fund_list(df)
    console.print(table)
    console.print(f"\n[green]共找到 {len(df)} 只基金[/green]")


@app.command("basic")
def filter_basic(
    fund_type: str | None = typer.Option(None, "--type", "-t", help="基金类型"),
    company: str | None = typer.Option(None, "--company", "-c", help="基金公司"),
    min_scale: float | None = typer.Option(None, "--min-scale", help="最小规模(亿)"),
    max_scale: float | None = typer.Option(None, "--max-scale", help="最大规模(亿)"),
    keyword: str | None = typer.Option(None, "--keyword", "-k", help="关键词搜索"),
    limit: int = typer.Option(20, "--limit", "-l", help="返回数量"),
    output: str | None = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    基础筛选 - 按基金类型、公司、规模等条件筛选基金。

    示例:
        fund filter basic --type 股票型 --min-scale 10
        fund filter basic -c 华夏基金 -l 50
        fund filter basic -k 成长
    """
    try:
        dm = get_data_manager()

        console.print("[bold blue]正在筛选基金...[/bold blue]")

        df = dm.search_funds(
            fund_type=fund_type,
            company=company,
            min_scale=min_scale,
            max_scale=max_scale,
            keyword=keyword,
            limit=limit,
        )

        if df.empty:
            console.print("[yellow]未找到符合条件的基金[/yellow]")
            return

        # 显示结果
        renderer = TableRenderer()
        table = renderer.render_fund_list(df)
        console.print(table)

        console.print(f"\n[green]共找到 {len(df)} 只基金[/green]")

        # 导出
        if output:
            df.to_csv(output, index=False, encoding="utf-8-sig")
            console.print(f"[green]已导出到: {output}[/green]")

    except Exception as e:
        console.print(f"[red]筛选失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("fee")
def filter_by_fee(
    max_fee: float = typer.Argument(..., help="最大费率(%)"),
    fund_type: str = typer.Option(None, help="基金类型"),
    limit: int = typer.Option(20, help="返回数量"),
):
    """费率筛选 (FUND-FILTER-005)"""
    from fund_cli.core.screener import FundScreener

    screener = FundScreener()
    try:
        df = screener.screen_by_fee(max_fee, fund_type)
        if df.empty:
            console.print("[yellow]未找到符合条件的基金[/yellow]")
            return
        _render_fund_table(df.head(limit))
    except Exception as e:
        console.print(f"[red]筛选失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("manager")
def filter_by_manager(
    manager_name: str = typer.Argument(..., help="基金经理名称"),
    limit: int = typer.Option(20, help="返回数量"),
):
    """经理筛选 (FUND-FILTER-006)"""
    from fund_cli.core.screener import FundScreener

    screener = FundScreener()
    try:
        df = screener.screen_by_manager(manager_name)
        if df.empty:
            console.print(f"[yellow]未找到经理 {manager_name} 管理的基金[/yellow]")
            return
        _render_fund_table(df.head(limit))
    except Exception as e:
        console.print(f"[red]筛选失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("rating")
def filter_by_rating(
    min_rating: int = typer.Argument(..., help="最低评级(1-5)"),
    limit: int = typer.Option(20, help="返回数量"),
):
    """评级筛选 (FUND-FILTER-007)"""
    from fund_cli.core.screener import FundScreener

    screener = FundScreener()
    try:
        df = screener.screen_by_rating(min_rating)
        if df.empty:
            console.print(f"[yellow]未找到评级>={min_rating}的基金[/yellow]")
            return
        _render_fund_table(df.head(limit))
    except Exception as e:
        console.print(f"[red]筛选失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("advanced")
def filter_advanced(
    expression: str = typer.Argument(..., help="筛选表达式"),
    limit: int = typer.Option(20, help="返回数量"),
):
    """高级表达式筛选 (FUND-FILTER-012)"""
    from fund_cli.core.screener import FundScreener

    screener = FundScreener()
    try:
        all_funds = screener._dm.search_funds(limit=1000)
        if all_funds.empty:
            console.print("[yellow]无基金数据[/yellow]")
            return
        result = screener.evaluate_expression(all_funds, expression)
        if result.empty:
            console.print("[yellow]无匹配结果[/yellow]")
            return
        _render_fund_table(result.head(limit))
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]筛选失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("template")
def filter_template(
    action: str = typer.Argument(..., help="操作: save/load/list/delete"),
    name: str = typer.Option(None, help="模板名称"),
):
    """筛选模板管理 (FUND-FILTER-011)"""
    from fund_cli.core.screener import FundScreener

    screener = FundScreener()
    if action == "list":
        templates = screener.list_templates()
        if not templates:
            console.print("[yellow]暂无保存的模板[/yellow]")
            return
        for t in templates:
            console.print(f"  - {t}")
    elif action == "save":
        if not name:
            console.print("[red]请指定模板名称[/red]")
            raise typer.Exit(1) from None
        from fund_cli.data.models import FundFilter

        screener.save_template(name, FundFilter())
        console.print(f"[green]模板 {name} 已保存[/green]")
    elif action == "load":
        if not name:
            console.print("[red]请指定模板名称[/red]")
            raise typer.Exit(1) from None
        try:
            template = screener.load_template(name)
            console.print(f"模板 {name}: {template.model_dump_json(indent=2)}")
        except FileNotFoundError:
            console.print(f"[red]模板 {name} 不存在[/red]")
            raise typer.Exit(1) from None
    elif action == "delete":
        if not name:
            console.print("[red]请指定模板名称[/red]")
            raise typer.Exit(1) from None
        if screener.delete_template(name):
            console.print(f"[green]模板 {name} 已删除[/green]")
        else:
            console.print(f"[yellow]模板 {name} 不存在[/yellow]")
    else:
        console.print(f"[red]未知操作: {action}，支持: save/load/list/delete[/red]")
        raise typer.Exit(1) from None


@app.command("performance")
def filter_performance(
    min_return: float = typer.Option(None, help="最低年化收益率(%)"),
    max_drawdown: float = typer.Option(None, help="最大回撤(%)"),
    min_sharpe: float = typer.Option(None, help="最低夏普比率"),
    limit: int = typer.Option(20, help="返回数量"),
):
    """业绩指标筛选"""
    from fund_cli.core.screener import FundScreener
    from fund_cli.data.models import FundFilter

    screener = FundScreener()
    f = FundFilter(
        min_return_1y=min_return, max_drawdown=max_drawdown, min_sharpe=min_sharpe, limit=limit
    )
    try:
        df = screener.screen(f)
        if df.empty:
            console.print("[yellow]未找到符合条件的基金[/yellow]")
            return
        _render_fund_table(df)
    except Exception as e:
        console.print(f"[red]筛选失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("export")
def export_results(
    output: str = typer.Argument(..., help="输出文件路径"),
    format: str = typer.Option("csv", help="输出格式: csv/json"),
):
    """导出筛选结果"""
    from fund_cli.core.screener import FundScreener

    screener = FundScreener()
    try:
        df = screener._dm.search_funds(limit=1000)
        if df.empty:
            console.print("[yellow]无数据可导出[/yellow]")
            return
        if format == "csv":
            df.to_csv(output, index=False, encoding="utf-8-sig")
        elif format == "json":
            df.to_json(output, orient="records", force_ascii=False, indent=2)
        else:
            console.print(f"[red]不支持的格式: {format}[/red]")
            raise typer.Exit(1) from None
        console.print(f"[green]已导出 {len(df)} 条记录到 {output}[/green]")
    except Exception as e:
        console.print(f"[red]导出失败: {e}[/red]")
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
