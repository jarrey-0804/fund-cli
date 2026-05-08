"""
基金分析命令

提供基金信息查询、业绩分析、报告生成等功能。
"""

from datetime import date, datetime, timedelta

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from fund_cli.analysis.performance import PerformanceAnalyzer
from fund_cli.analysis.risk import RiskAnalyzer
from fund_cli.core.data_manager import get_data_manager

app = typer.Typer(help="基金分析命令")
console = Console()


@app.command("info")
def info_fund(
    fund_code: str = typer.Argument(..., help="基金代码（6位数字）"),
) -> None:
    """
    查看基金基础信息。

    示例:
        fund analyze info 000001
    """
    try:
        dm = get_data_manager()

        console.print(f"[bold blue]获取基金 {fund_code} 信息...[/bold blue]")

        info = dm.get_fund_info(fund_code)

        # 显示基金信息
        info_table = Table(show_header=False, box=None)
        info_table.add_column("字段", style="cyan")
        info_table.add_column("值", style="white")

        field_names = {
            "code": "基金代码",
            "name": "基金名称",
            "type": "基金类型",
            "establish_date": "成立日期",
            "manager": "基金经理",
            "company": "基金公司",
            "scale": "规模(亿元)",
        }

        for key, label in field_names.items():
            value = info.get(key, "-")
            if value is None:
                value = "-"
            info_table.add_row(label, str(value))

        console.print(
            Panel(
                info_table, title=f"[bold]{info.get('name', fund_code)}[/bold]", border_style="blue"
            )
        )

    except Exception as e:
        console.print(f"[red]获取信息失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("nav")
def nav_history(
    fund_code: str = typer.Argument(..., help="基金代码"),
    start_date: str | None = typer.Option(None, "--start", "-s", help="开始日期 (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end", "-e", help="结束日期 (YYYY-MM-DD)"),
    limit: int = typer.Option(30, "--limit", "-l", help="显示条数"),
) -> None:
    """
    查看基金净值历史。

    示例:
        fund analyze nav 000001
        fund analyze nav 000001 --start 2023-01-01 --end 2023-12-31
    """
    try:
        dm = get_data_manager()

        # 解析日期
        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

        console.print(f"[bold blue]获取基金 {fund_code} 净值数据...[/bold blue]")

        df = dm.get_fund_nav(fund_code, start_date=start, end_date=end)

        if df.empty:
            console.print("[yellow]未找到净值数据[/yellow]")
            return

        # 显示最近的数据
        df_display = df.tail(limit).copy()
        df_display["nav_date"] = df_display["nav_date"].dt.strftime("%Y-%m-%d")

        table = Table(title=f"基金 {fund_code} 净值历史")
        table.add_column("日期", style="cyan")
        table.add_column("单位净值", style="green")
        table.add_column("累计净值", style="blue")
        table.add_column("日涨跌(%)", style="yellow")

        for _, row in df_display.iterrows():
            daily_return = row.get("daily_return", "")
            if daily_return is not None:
                daily_return = f"{daily_return:.2f}"
            else:
                daily_return = "-"

            table.add_row(
                str(row["nav_date"]),
                f"{row['unit_nav']:.4f}",
                f"{row['accumulated_nav']:.4f}" if row.get("accumulated_nav") else "-",
                daily_return,
            )

        console.print(table)
        console.print(f"\n[green]共 {len(df)} 条记录，显示最近 {len(df_display)} 条[/green]")

    except Exception as e:
        console.print(f"[red]获取净值失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("metrics")
def analyze_metrics(
    fund_code: str = typer.Argument(..., help="基金代码"),
    start_date: str | None = typer.Option(None, "--start", "-s", help="开始日期"),
    end_date: str | None = typer.Option(None, "--end", "-e", help="结束日期"),
    benchmark: str | None = typer.Option(None, "-b", "--benchmark", help="基准指数代码"),
) -> None:
    """
    分析基金业绩指标。

    示例:
        fund analyze metrics 000001
        fund analyze metrics 000001 -b 000300
    """
    try:
        dm = get_data_manager()

        # 解析日期
        start = (
            datetime.strptime(start_date, "%Y-%m-%d").date()
            if start_date
            else date.today() - timedelta(days=365)
        )
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date.today()

        console.print(f"[bold blue]分析基金 {fund_code} 业绩指标...[/bold blue]")

        # 获取净值数据
        nav_df = dm.get_fund_nav(fund_code, start_date=start, end_date=end)

        if nav_df.empty:
            console.print("[yellow]未找到净值数据[/yellow]")
            return

        # 计算收益率
        nav_series = nav_df.set_index("nav_date")["unit_nav"]
        returns = nav_series.pct_change().dropna()

        # 获取基准数据
        benchmark_returns = None
        if benchmark:
            try:
                benchmark_df = dm.get_benchmark_nav(benchmark, start_date=start, end_date=end)
                if not benchmark_df.empty:
                    benchmark_series = benchmark_df.set_index("nav_date")["unit_nav"]
                    benchmark_returns = benchmark_series.pct_change().dropna()
            except Exception:
                console.print(f"[yellow]无法获取基准 {benchmark} 数据[/yellow]")

        # 执行分析
        perf_analyzer = PerformanceAnalyzer()
        risk_analyzer = RiskAnalyzer()

        perf_metrics = perf_analyzer.analyze(returns, benchmark=benchmark_returns)
        risk_metrics = risk_analyzer.analyze(returns, benchmark=benchmark_returns)

        # 显示结果
        metrics_table = Table(title=f"基金 {fund_code} 分析结果", show_header=True)
        metrics_table.add_column("指标", style="cyan")
        metrics_table.add_column("业绩指标", style="green")
        metrics_table.add_column("风险指标", style="yellow")

        # 收益指标
        metrics_table.add_row("总收益率", f"{perf_metrics.get('total_return', 0):.2f}%", "-")
        metrics_table.add_row("年化收益率", f"{perf_metrics.get('cagr', 0):.2f}%", "-")
        metrics_table.add_row(
            "年化波动率",
            f"{perf_metrics.get('volatility', 0):.2f}%",
            f"{risk_metrics.get('volatility_annual', 0):.2f}%",
        )
        metrics_table.add_row(
            "最大回撤",
            f"{perf_metrics.get('max_drawdown', 0):.2f}%",
            f"{risk_metrics.get('max_drawdown', 0):.2f}%",
        )
        metrics_table.add_row("夏普比率", f"{perf_metrics.get('sharpe', 0):.2f}", "-")
        metrics_table.add_row("索提诺比率", f"{perf_metrics.get('sortino', 0):.2f}", "-")
        metrics_table.add_row(
            "VaR(95%)",
            f"{perf_metrics.get('var_95', 0):.2f}%",
            f"{risk_metrics.get('var_95', 0):.2f}%",
        )

        # 相对指标
        if benchmark:
            metrics_table.add_row("Alpha", f"{perf_metrics.get('alpha', '-') or '-'}", "-")
            metrics_table.add_row(
                "Beta",
                f"{perf_metrics.get('beta', '-') or '-'}",
                f"{risk_metrics.get('beta', '-') or '-'}",
            )
            metrics_table.add_row(
                "信息比率", f"{perf_metrics.get('information_ratio', '-') or '-'}", "-"
            )
            metrics_table.add_row(
                "跟踪误差",
                f"{perf_metrics.get('tracking_error', '-') or '-'}%",
                f"{risk_metrics.get('tracking_error', '-') or '-'}%",
            )

        console.print(metrics_table)
        console.print(f"\n[dim]分析区间: {start} 至 {end}[/dim]")

    except Exception as e:
        console.print(f"[red]分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("report")
def generate_report(
    fund_code: str = typer.Argument(..., help="基金代码"),
    output: str = typer.Option(None, help="输出文件路径"),
    format: str = typer.Option("html", help="报告格式: html/markdown"),
):
    """生成分析报告 (FUND-ANALYZE-011)"""
    from fund_cli.analysis.performance import PerformanceAnalyzer
    from fund_cli.core.data_manager import DataManager

    dm = DataManager()
    try:
        nav_df = dm.get_fund_nav(fund_code)
        if nav_df.empty:
            console.print("[yellow]无净值数据[/yellow]")
            return
        returns = nav_df["daily_return"].dropna() / 100.0
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.analyze(returns)

        if format == "html":
            from fund_cli.core.reporters.html_reporter import HtmlReporter

            reporter = HtmlReporter()
            ext = ".html"
        elif format == "markdown":
            from fund_cli.core.reporters.markdown_reporter import MarkdownReporter

            reporter = MarkdownReporter()
            ext = ".md"
        else:
            console.print(f"[red]不支持的格式: {format}[/red]")
            raise typer.Exit(1) from None

        content = reporter.generate(fund_code, metrics, nav_data=nav_df)
        out_path = output or f"{fund_code}_report{ext}"
        reporter.save(content, out_path)
        console.print(f"[green]报告已生成: {out_path}[/green]")
    except Exception as e:
        console.print(f"[red]报告生成失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("rolling")
def rolling_performance(
    fund_code: str = typer.Argument(..., help="基金代码"),
    window: int = typer.Option(60, help="滚动窗口(交易日)"),
    start_date: str = typer.Option(None, help="开始日期"),
    end_date: str = typer.Option(None, help="结束日期"),
):
    """滚动业绩分析 (FUND-ANALYZE-006)"""
    from fund_cli.analysis.performance import PerformanceAnalyzer
    from fund_cli.core.data_manager import DataManager

    dm = DataManager()
    try:
        nav_df = dm.get_fund_nav(
            fund_code,
            start_date=date.fromisoformat(start_date) if start_date else None,
            end_date=date.fromisoformat(end_date) if end_date else None,
        )
        if nav_df.empty:
            console.print("[yellow]无净值数据[/yellow]")
            return
        returns = nav_df["daily_return"].dropna() / 100.0
        analyzer = PerformanceAnalyzer()
        result = analyzer.rolling_performance(returns, window)
        if result.empty:
            console.print("[yellow]数据不足以计算滚动指标[/yellow]")
            return
        console.print(f"\n[bold]{fund_code}[/bold] 滚动业绩 (窗口={window}日)：")
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("日期")
        table.add_column("滚动收益", justify="right")
        table.add_column("滚动夏普", justify="right")
        table.add_column("滚动波动", justify="right")
        for idx, row in result.tail(10).iterrows():
            table.add_row(
                str(idx.date()),
                f"{row['rolling_return']:.2f}%",
                f"{row['rolling_sharpe']:.4f}",
                f"{row['rolling_volatility']:.2f}%",
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("monthly")
def monthly_distribution(fund_code: str = typer.Argument(..., help="基金代码")):
    """月度收益分布 (FUND-ANALYZE-008)"""
    from fund_cli.analysis.performance import PerformanceAnalyzer
    from fund_cli.core.data_manager import DataManager

    dm = DataManager()
    try:
        nav_df = dm.get_fund_nav(fund_code)
        if nav_df.empty:
            console.print("[yellow]无净值数据[/yellow]")
            return
        returns = nav_df["daily_return"].dropna() / 100.0
        analyzer = PerformanceAnalyzer()
        result = analyzer.monthly_return_distribution(returns)
        console.print(f"\n[bold]{fund_code}[/bold] 月度收益分布：")
        console.print(f"  总月数: {result['total_months']}")
        console.print(f"  正收益月: [green]{result['positive_months']}[/green]")
        console.print(f"  负收益月: [red]{result['negative_months']}[/red]")
        console.print(f"  月胜率: {result['win_rate']:.1f}%")
        console.print(f"  平均月收益: {result['avg_monthly_return']:.4f}%")
        console.print(f"  最佳月: [green]{result['max_month']:.2f}%[/green]")
        console.print(f"  最差月: [red]{result['min_month']:.2f}%[/red]")
    except Exception as e:
        console.print(f"[red]分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("scenario")
def scenario_analysis(fund_code: str = typer.Argument(..., help="基金代码")):
    """情景分析 (FUND-ANALYZE-009)"""
    from fund_cli.analysis.performance import PerformanceAnalyzer
    from fund_cli.core.data_manager import DataManager

    dm = DataManager()
    try:
        nav_df = dm.get_fund_nav(fund_code)
        if nav_df.empty:
            console.print("[yellow]无净值数据[/yellow]")
            return
        returns = nav_df["daily_return"].dropna() / 100.0
        analyzer = PerformanceAnalyzer()
        result = analyzer.scenario_analysis(returns)
        console.print(f"\n[bold]{fund_code}[/bold] 情景分析：")
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("情景", style="cyan")
        table.add_column("年化假设", justify="right")
        table.add_column("模拟总收益", justify="right")
        table.add_column("模拟波动率", justify="right")
        for name, data in result.items():
            table.add_row(
                name,
                f"{data['annual_return']:.1f}%",
                f"{data['simulated_total_return']:.2f}%",
                f"{data['simulated_volatility']:.2f}%",
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("persistence")
def performance_persistence(fund_code: str = typer.Argument(..., help="基金代码")):
    """业绩持续性分析 (FUND-ANALYZE-010)"""
    from fund_cli.analysis.performance import PerformanceAnalyzer
    from fund_cli.core.data_manager import DataManager

    dm = DataManager()
    try:
        nav_df = dm.get_fund_nav(fund_code)
        if nav_df.empty:
            console.print("[yellow]无净值数据[/yellow]")
            return
        returns = nav_df["daily_return"].dropna() / 100.0
        analyzer = PerformanceAnalyzer()
        result = analyzer.performance_persistence(returns)
        console.print(f"\n[bold]{fund_code}[/bold] 业绩持续性分析：")
        console.print(f"  持续性评分: {result['persistence_score']}/100")
        console.print(f"  排名相关性: {result['rank_correlation']:.4f}")
        console.print(f"  月胜率: {result['monthly_win_rate']:.1f}%")
        console.print(f"  最长连续正收益: {result['max_positive_streak']}月")
        console.print(f"  最长连续负收益: {result['max_negative_streak']}月")
    except Exception as e:
        console.print(f"[red]分析失败: {e}[/red]")
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
