"""
基金对比命令

提供多基金对比分析功能。
"""

from datetime import date, timedelta

import typer
from rich.console import Console
from rich.table import Table

from fund_cli.analysis.performance import PerformanceAnalyzer
from fund_cli.core.data_manager import get_data_manager

app = typer.Typer(help="基金对比命令")
console = Console()


@app.command("funds")
def compare_funds(
    fund_codes: list[str] = typer.Argument(..., help="基金代码列表（至少2只）"),
    period: str = typer.Option("1y", "--period", "-p", help="对比周期: 1m, 3m, 6m, 1y, 3y"),
) -> None:
    """
    对比多只基金的业绩表现。

    示例:
        fund compare funds 000001 000002 000003
        fund compare funds 000001 000002 --period 3y
    """
    if len(fund_codes) < 2:
        console.print("[red]请至少输入2只基金代码[/red]")
        raise typer.Exit(1) from None

    try:
        dm = get_data_manager()
        analyzer = PerformanceAnalyzer()

        # 计算日期范围
        period_map = {
            "1m": 30,
            "3m": 90,
            "6m": 180,
            "1y": 365,
            "3y": 1095,
        }
        days = period_map.get(period, 365)
        start_date = date.today() - timedelta(days=days)

        console.print(f"[bold blue]对比分析 {len(fund_codes)} 只基金...[/bold blue]")

        # 收集数据
        results = []
        for code in fund_codes:
            try:
                nav_df = dm.get_fund_nav(code, start_date=start_date)
                if not nav_df.empty:
                    nav_series = nav_df.set_index("nav_date")["unit_nav"]
                    returns = nav_series.pct_change().dropna()
                    metrics = analyzer.analyze(returns)

                    info = dm.get_fund_info(code)
                    results.append(
                        {
                            "code": code,
                            "name": info.get("name", "-"),
                            "total_return": metrics.get("total_return", 0),
                            "cagr": metrics.get("cagr", 0),
                            "volatility": metrics.get("volatility", 0),
                            "max_drawdown": metrics.get("max_drawdown", 0),
                            "sharpe": metrics.get("sharpe", 0),
                        }
                    )
            except Exception as e:
                console.print(f"[yellow]获取 {code} 数据失败: {e}[/yellow]")

        if not results:
            console.print("[red]未能获取任何基金数据[/red]")
            return

        # 显示对比结果
        table = Table(title="基金对比结果")
        table.add_column("基金代码", style="cyan")
        table.add_column("基金名称", style="white")
        table.add_column("总收益率", style="green")
        table.add_column("年化收益", style="green")
        table.add_column("年化波动", style="yellow")
        table.add_column("最大回撤", style="red")
        table.add_column("夏普比率", style="blue")

        for r in results:
            table.add_row(
                r["code"],
                r["name"][:10] if r["name"] else "-",
                f"{r['total_return']:.2f}%",
                f"{r['cagr']:.2f}%",
                f"{r['volatility']:.2f}%",
                f"{r['max_drawdown']:.2f}%",
                f"{r['sharpe']:.2f}",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]对比分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("rolling-win")
def rolling_win_rate(
    fund_codes: str = typer.Argument(..., help="基金代码，逗号分隔"),
    window: int = typer.Option(60, help="滚动窗口(交易日)"),
    period: str = typer.Option("1y", help="分析周期"),
):
    """滚动胜率对比 (FUND-COMPARE-005)"""
    from datetime import date, timedelta

    from fund_cli.core.data_manager import DataManager

    dm = DataManager()
    codes = [c.strip() for c in fund_codes.split(",")]
    end = date.today()
    start = end - timedelta(
        days={"1m": 30, "3m": 90, "6m": 180, "1y": 365, "2y": 730}.get(period, 365)
    )

    all_returns = {}
    for code in codes:
        try:
            nav_df = dm.get_fund_nav(code, start_date=start, end_date=end)
            if not nav_df.empty and "daily_return" in nav_df.columns:
                all_returns[code] = nav_df["daily_return"].dropna() / 100.0
        except Exception:
            continue

    if len(all_returns) < 2:
        console.print("[yellow]至少需要2只基金的有效数据[/yellow]")
        return

    import pandas as pd

    returns_df = pd.DataFrame(all_returns)
    rolling = returns_df.rolling(window=window).apply(lambda x: (1 + x).prod() - 1)
    win_counts = {}
    for code in codes:
        if code in rolling.columns:
            others = [c for c in codes if c != code and c in rolling.columns]
            if others:
                wins = (rolling[code] > rolling[others].T).sum(axis=1).sum()
                total = rolling[code].notna().sum()
                win_counts[code] = round(wins / total * 100, 1) if total > 0 else 0

    console.print(f"\n[bold]滚动胜率对比[/bold] (窗口={window}日)：")
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("基金代码", style="cyan")
    table.add_column("胜率", justify="right")
    for code, rate in sorted(win_counts.items(), key=lambda x: x[1], reverse=True):
        table.add_row(code, f"{rate:.1f}%")
    console.print(table)


@app.command("correlation")
def correlation_analysis(
    fund_codes: str = typer.Argument(..., help="基金代码，逗号分隔"),
    period: str = typer.Option("1y", help="分析周期"),
):
    """相关性分析 (FUND-COMPARE-006)"""
    from datetime import date, timedelta

    from fund_cli.core.data_manager import DataManager

    dm = DataManager()
    codes = [c.strip() for c in fund_codes.split(",")]
    end = date.today()
    start = end - timedelta(days=365)

    all_returns = {}
    for code in codes:
        try:
            nav_df = dm.get_fund_nav(code, start_date=start, end_date=end)
            if not nav_df.empty and "daily_return" in nav_df.columns:
                all_returns[code] = nav_df["daily_return"].dropna() / 100.0
        except Exception:
            continue

    if len(all_returns) < 2:
        console.print("[yellow]至少需要2只基金的有效数据[/yellow]")
        return

    import pandas as pd

    returns_df = pd.DataFrame(all_returns).dropna()
    corr = returns_df.corr()

    console.print("\n[bold]相关性矩阵[/bold]：")
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("", style="cyan")
    for code in corr.columns:
        table.add_column(code, justify="right")
    for code in corr.index:
        row = [f"[bold]{code}[/bold]"]
        for val in corr[code]:
            color = "green" if val > 0.5 else "red" if val < -0.3 else ""
            row.append(f"[{color}]{val:.4f}[/{color}]")
        table.add_row(*row)
    console.print(table)


@app.command("report")
def compare_report(
    fund_codes: str = typer.Argument(..., help="基金代码，逗号分隔"),
    period: str = typer.Option("1y", help="分析周期"),
    output: str = typer.Option(None, help="输出文件路径"),
):
    """对比报告生成 (FUND-COMPARE-007)"""
    from datetime import date, timedelta

    from fund_cli.analysis.performance import PerformanceAnalyzer
    from fund_cli.core.data_manager import DataManager

    dm = DataManager()
    codes = [c.strip() for c in fund_codes.split(",")]
    end = date.today()
    start = end - timedelta(days=365)

    analyzer = PerformanceAnalyzer()
    results = []
    for code in codes:
        try:
            nav_df = dm.get_fund_nav(code, start_date=start, end_date=end)
            if nav_df.empty:
                continue
            returns = nav_df["daily_return"].dropna() / 100.0
            metrics = analyzer.analyze(returns)
            metrics["fund_code"] = code
            results.append(metrics)
        except Exception:
            continue

    if not results:
        console.print("[yellow]无有效数据[/yellow]")
        return

    from fund_cli.core.reporters.markdown_reporter import MarkdownReporter

    md = f"# 基金对比报告\n\n对比周期: {period}\n\n"
    md += "| 指标 | " + " | ".join(r["fund_code"] for r in results) + " |\n"
    md += "|------|" + "|".join(["------"] * len(results)) + "|\n"
    for key in ["total_return", "volatility", "sharpe_ratio", "max_drawdown"]:
        row = [key]
        for r in results:
            v = r.get(key, "N/A")
            row.append(f"{v:.4f}" if isinstance(v, float) else str(v))
        md += "|" + "|".join(row) + "|\n"

    reporter = MarkdownReporter()
    out = output or "comparison_report.md"
    reporter.save(md, out)
    console.print(f"[green]对比报告已生成: {out}[/green]")


if __name__ == "__main__":
    app()
