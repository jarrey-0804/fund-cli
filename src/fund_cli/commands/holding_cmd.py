"""
持仓分析命令

提供基金持仓查询、行业配置、集中度、变化追踪和风格分析功能。
"""

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from fund_cli.analysis.holding import HoldingAnalyzer
from fund_cli.core.data_manager import DataManager
from fund_cli.utils.validators import validate_fund_code

app = typer.Typer(help="持仓分析命令")
console = Console()


@app.command("query")
def query_holdings(
    fund_code: str = typer.Argument(..., help="基金代码"),
    top_n: int = typer.Option(10, help="显示前N大持仓"),
):
    """查询基金持仓 (FUND-HOLDING-001)"""
    validate_fund_code(fund_code)
    dm = DataManager()
    try:
        holdings = dm.get_fund_holdings(fund_code)
        analyzer = HoldingAnalyzer()
        top = analyzer.top_holdings(holdings, top_n=top_n)
        console.print(f"\n[bold]{fund_code}[/bold] 前十大持仓：")
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("股票代码", style="cyan")
        table.add_column("股票名称")
        table.add_column("占净值比", justify="right")
        table.add_column("持仓市值(万)", justify="right")
        for _, row in top.iterrows():
            table.add_row(
                str(row.get("stock_code", "")),
                str(row.get("stock_name", "")),
                f"{row.get('weight', 0):.2f}%",
                f"{row.get('market_value', 0):,.0f}" if pd.notna(row.get("market_value")) else "-",
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]获取持仓数据失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("industry")
def industry_analysis(fund_code: str = typer.Argument(..., help="基金代码")):
    """行业配置分析 (FUND-HOLDING-002)"""
    validate_fund_code(fund_code)
    dm = DataManager()
    try:
        holdings = dm.get_fund_holdings(fund_code)
        analyzer = HoldingAnalyzer()
        distribution = analyzer.industry_distribution(holdings)
        console.print(f"\n[bold]{fund_code}[/bold] 行业配置：")
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("行业", style="cyan")
        table.add_column("占比", justify="right")
        for industry, weight in distribution.items():
            table.add_row(str(industry), f"{weight:.2f}%")
        console.print(table)
    except Exception as e:
        console.print(f"[red]行业分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("concentration")
def concentration_analysis(fund_code: str = typer.Argument(..., help="基金代码")):
    """持仓集中度分析 (FUND-HOLDING-004)"""
    validate_fund_code(fund_code)
    dm = DataManager()
    try:
        holdings = dm.get_fund_holdings(fund_code)
        analyzer = HoldingAnalyzer()
        hhi = analyzer.concentration_hhi(holdings)
        level = analyzer._hhi_level(hhi)
        console.print(f"\n[bold]{fund_code}[/bold] 持仓集中度：")
        console.print(f"  HHI指数: {hhi:.4f}")
        console.print(f"  集中度等级: [bold]{level}[/bold]")
    except Exception as e:
        console.print(f"[red]集中度分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("changes")
def holding_changes(
    fund_code: str = typer.Argument(..., help="基金代码"),
    period: str = typer.Option("latest", help="对比周期: latest/quarter"),
):
    """持仓变化追踪 (FUND-HOLDING-005)"""
    validate_fund_code(fund_code)
    dm = DataManager()
    try:
        current = dm.get_fund_holdings(fund_code)
        if current.empty:
            console.print("[yellow]暂无持仓数据[/yellow]")
            return
        analyzer = HoldingAnalyzer()
        console.print(f"\n[bold]{fund_code}[/bold] 最新持仓（前10）：")
        top = analyzer.top_holdings(current, top_n=10)
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("股票代码", style="cyan")
        table.add_column("股票名称")
        table.add_column("占净值比", justify="right")
        for _, row in top.iterrows():
            table.add_row(
                str(row.get("stock_code", "")),
                str(row.get("stock_name", "")),
                f"{row.get('weight', 0):.2f}%",
            )
        console.print(table)
        console.print("[yellow]提示: 历史持仓对比需要多期数据支持[/yellow]")
    except Exception as e:
        console.print(f"[red]持仓变化分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("style")
def style_analysis_cmd(fund_code: str = typer.Argument(..., help="基金代码")):
    """风格分析 (FUND-HOLDING-006)"""
    validate_fund_code(fund_code)
    dm = DataManager()
    try:
        holdings = dm.get_fund_holdings(fund_code)
        analyzer = HoldingAnalyzer()
        result = analyzer.style_analysis(holdings)
        console.print(f"\n[bold]{fund_code}[/bold] 风格分析：")
        console.print(f"  市值风格: [bold]{result['market_cap_style']}[/bold]")
        console.print(f"  投资风格: [bold]{result['investment_style']}[/bold]")
        console.print(f"  九宫格位置: [bold]{result['grid_position']}[/bold]")
        console.print(f"  大盘股权重: {result['large_cap_weight']:.1f}%")
        console.print(f"  价值股权重: {result['value_weight']:.1f}%")
    except Exception as e:
        console.print(f"[red]风格分析失败: {e}[/red]")
        raise typer.Exit(1) from None
