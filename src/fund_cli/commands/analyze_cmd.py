"""
基金分析命令

提供基金信息查询、业绩分析、报告生成等功能。
"""

import logging
from datetime import date, datetime, timedelta

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from fund_cli.analysis.performance import PerformanceAnalyzer
from fund_cli.analysis.risk import RiskAnalyzer
from fund_cli.core.calc_validator import CalcValidator
from fund_cli.core.cross_validator import CrossValidator
from fund_cli.core.data_manager import get_data_manager
from fund_cli.core.quality_gate import QualityGate

app = typer.Typer(help="基金分析命令")
console = Console()
logger = logging.getLogger(__name__)


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

        # 质量门禁检查
        console.print("[dim]执行数据质量检查...[/dim]")
        quality_gate = QualityGate(dm)
        quality_report = quality_gate.check(fund_code, nav_df)

        if quality_report.blocked:
            console.print(f"[red]数据质量检查未通过 (评分: {quality_report.score:.0f}/100)[/red]")
            for result in quality_report.results:
                if not result.passed and result.severity == "error":
                    console.print(f"  [red]✗ {result.name}: {result.message}[/red]")
            raise typer.Exit(1)
        elif quality_report.level == "warning":
            console.print(f"[yellow]数据质量警告 (评分: {quality_report.score:.0f}/100)[/yellow]")
            for result in quality_report.results:
                if not result.passed:
                    console.print(f"  [yellow]⚠ {result.name}: {result.message}[/yellow]")
        else:
            console.print(f"[green]数据质量检查通过 (评分: {quality_report.score:.0f}/100)[/green]")

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

        # 交叉验证
        cross_validator = CrossValidator()
        cross_results = cross_validator.validate(perf_metrics, risk_metrics)
        cross_summary = cross_validator.get_summary(cross_results)

        if cross_summary["failed"] > 0:
            console.print(
                f"[yellow]交叉验证警告: {cross_summary['failed']}/{cross_summary['total']} 项指标差异超标[/yellow]"
            )
            for failed in cross_summary["failed_metrics"]:
                console.print(
                    f"  [yellow]⚠ {failed['name']}: 差异 {failed['diff_percent']:.2%}[/yellow]"
                )
        else:
            console.print(
                f"[green]交叉验证通过: {cross_summary['passed']}/{cross_summary['total']} 项指标一致[/green]"
            )

        # 计算结果验证
        console.print("[dim]执行计算结果验证...[/dim]")
        calc_validator = CalcValidator()
        all_metrics = {**perf_metrics, **risk_metrics}
        calc_results = calc_validator.validate_metrics(all_metrics)
        calc_summary = calc_validator.get_summary(calc_results)

        if calc_summary["failed"] > 0:
            console.print(
                f"[yellow]计算验证警告: {calc_summary['failed']}/{calc_summary['total']} 项指标异常[/yellow]"
            )
            for warning in calc_summary["warnings"]:
                console.print(f"  [yellow]⚠ {warning['name']}: {warning['message']}[/yellow]")
        else:
            console.print(
                f"[green]计算验证通过: {calc_summary['passed']}/{calc_summary['total']} 项指标正常[/green]"
            )

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
    from fund_cli.core.quality_gate import QualityGate

    dm = DataManager()
    try:
        nav_df = dm.get_fund_nav(fund_code)
        if nav_df.empty:
            console.print("[yellow]无净值数据[/yellow]")
            return

        # 执行数据质量检查
        quality_gate = QualityGate(dm)
        quality_report = quality_gate.check(fund_code, nav_df)

        if quality_report.blocked:
            console.print(f"[red]数据质量检查未通过 (评分: {quality_report.score:.0f}/100)[/red]")
            for result in quality_report.results:
                if not result.passed and result.severity == "error":
                    console.print(f"  [red]✗ {result.name}: {result.message}[/red]")
            raise typer.Exit(1)
        elif quality_report.level == "warning":
            console.print(f"[yellow]数据质量警告 (评分: {quality_report.score:.0f}/100)[/yellow]")

        returns = nav_df["daily_return"].dropna() / 100.0
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.analyze(returns)

        if format == "html":
            from fund_cli.core.reporter import Reporter
            from fund_cli.core.reporters.html_reporter import HtmlReporter

            reporter: Reporter = HtmlReporter()
            ext = ".html"
        elif format == "markdown":
            from fund_cli.core.reporter import Reporter
            from fund_cli.core.reporters.markdown_reporter import MarkdownReporter

            reporter = MarkdownReporter()  # type: ignore[assignment]
            ext = ".md"
        else:
            console.print(f"[red]不支持的格式: {format}[/red]")
            raise typer.Exit(1) from None

        # Pass quality information to report generator
        content = reporter.generate(
            fund_code,
            metrics,
            nav_data=nav_df,
            quality_score=quality_report.score,
            quality_level=quality_report.level,
        )
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


# ============================================
# Phase 2: 风险分析深度增强命令
# ============================================


@app.command("stress-test")
def stress_test_fund(
    fund_code: str = typer.Argument(..., help="基金代码"),
    scenario: str = typer.Option("all", "--scenario", "-s", help="压力情景: all/2008金融危机/2015股灾/2020疫情"),
    beta: float = typer.Option(1.0, "--beta", "-b", help="基金Beta值"),
    custom_shock: float = typer.Option(None, "--shock", help="自定义冲击幅度(%)"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    压力测试：评估基金在极端市场情况下的表现

    示例:
        fund analyze stress-test 000001
        fund analyze stress-test 000001 --scenario "2008金融危机"
        fund analyze stress-test 000001 --shock -30
    """
    from fund_cli.analysis.stress_test import StressTester, StressScenario

    try:
        tester = StressTester()

        if scenario == "all":
            report = tester.generate_report(fund_code, fund_code, beta, custom_shock)
            result = tester.format_report(report)
        else:
            try:
                scenario_enum = StressScenario(scenario)
            except ValueError:
                scenario_enum = StressScenario.CRISIS_2008

            result_obj = tester.run_single(scenario_enum, beta, custom_shock)
            result = f"# 压力测试结果\n\n情景: {result_obj.scenario_name}\n预估损失: {abs(result_obj.portfolio_loss):.2f}%\n风险提示: {result_obj.risk_warning}"

        console.print(Panel(result, title="压力测试报告", border_style="red"))

        if output:
            from pathlib import Path
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]压力测试失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("scenario-v2")
def scenario_analyze_fund(
    fund_code: str = typer.Argument(..., help="基金代码"),
    fund_type: str = typer.Option("股票型", "--type", "-t", help="基金类型"),
    beta: float = typer.Option(1.0, "--beta", "-b", help="基金Beta值"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    情景分析V2：评估基金在不同市场环境下的预期收益和风险

    示例:
        fund analyze scenario-v2 000001
        fund analyze scenario-v2 000001 --type "债券型" --beta 0.5
    """
    from fund_cli.analysis.scenario_analysis import ScenarioAnalyzer

    try:
        analyzer = ScenarioAnalyzer()
        report = analyzer.analyze(
            fund_code=fund_code,
            fund_name=fund_code,
            fund_type=fund_type,
            beta=beta,
        )

        result = analyzer.format_report(report)
        console.print(Panel(result, title="情景分析报告", border_style="blue"))

        if output:
            from pathlib import Path
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]情景分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("risk-budget")
def risk_budget_analyze(
    fund_codes: str = typer.Argument(..., help="基金代码列表（逗号分隔）"),
    weights: str = typer.Option(None, "--weights", "-w", help="权重配置（逗号分隔）"),
    optimize: bool = typer.Option(False, "--optimize", "-o", help="是否进行风险平价优化"),
    output: str = typer.Option(None, "--output", help="输出文件路径"),
) -> None:
    """
    风险预算分析：分析组合风险贡献和风险集中度

    示例:
        fund analyze risk-budget 000001,000002,000003
        fund analyze risk-budget 000001,000002 --weights 0.6,0.4
        fund analyze risk-budget 000001,000002,000003 --optimize
    """
    from fund_cli.analysis.risk_budget import RiskBudgetAnalyzer, OptimizationObjective

    try:
        codes = [c.strip() for c in fund_codes.split(",")]

        weight_list = None
        if weights:
            weight_list = [float(w.strip()) for w in weights.split(",")]
            if len(weight_list) != len(codes):
                console.print("[red]权重数量必须与基金数量一致[/red]")
                raise typer.Exit(1) from None

        analyzer = RiskBudgetAnalyzer()

        if optimize:
            # 风险平价优化
            opt_weights = analyzer.optimize_weights(
                codes,
                objective=OptimizationObjective.RISK_PARITY,
            )
            lines = ["# 风险平价优化结果\n"]
            lines.append("优化后的权重配置：")
            for code, weight in opt_weights.items():
                lines.append(f"- {code}: {weight:.2%}")
            result = "\n".join(lines)
        else:
            # 风险预算分析
            report = analyzer.analyze(codes, weight_list)
            result = analyzer.format_report(report)

        console.print(Panel(result, title="风险预算分析", border_style="yellow"))

        if output:
            from pathlib import Path
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]风险预算分析失败: {e}[/red]")
        raise typer.Exit(1) from None


# ============================================
# Phase 3: 市场分析能力命令
# ============================================


@app.command("money-flow")
def money_flow_analyze(
    flow_type: str = typer.Option("fund", "--type", "-t", help="分析类型: fund(基金申赎)/sector(板块资金)/northbound(北向资金)"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    资金流向分析：追踪市场资金动向

    示例:
        fund analyze money-flow --type fund
        fund analyze money-flow --type sector
        fund analyze money-flow --type northbound
    """
    from fund_cli.analysis.money_flow import MoneyFlowAnalyzer

    try:
        analyzer = MoneyFlowAnalyzer()

        if flow_type == "fund":
            report = analyzer.analyze_fund_flow()
            result = analyzer.format_fund_flow_report(report)
            title = "基金申赎分析"
        elif flow_type == "sector":
            report = analyzer.analyze_sector_flow()
            result = analyzer.format_sector_flow_report(report)
            title = "板块资金流向"
        elif flow_type == "northbound":
            report = analyzer.analyze_northbound()
            result = analyzer.format_northbound_report(report)
            title = "北向资金分析"
        else:
            report = analyzer.analyze_fund_flow()
            result = analyzer.format_fund_flow_report(report)
            title = "基金申赎分析"

        console.print(Panel(result, title=title, border_style="green"))

        if output:
            from pathlib import Path
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]资金流向分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("sector-rotation")
def sector_rotation_analyze(
    period: str = typer.Option("近1月", "--period", "-p", help="分析周期"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    行业轮动分析：识别强势/弱势行业

    示例:
        fund analyze sector-rotation
        fund analyze sector-rotation --period "近3月"
    """
    from fund_cli.analysis.sector_rotation import SectorRotationAnalyzer

    try:
        analyzer = SectorRotationAnalyzer()
        report = analyzer.analyze(period=period)
        result = analyzer.format_report(report)

        console.print(Panel(result, title="行业轮动分析", border_style="cyan"))

        if output:
            from pathlib import Path
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]行业轮动分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("sentiment")
def market_sentiment_analyze(
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    市场情绪分析：恐慌贪婪指数、基金仓位、市场宽度

    示例:
        fund analyze sentiment
    """
    from fund_cli.analysis.market_sentiment import MarketSentimentAnalyzer

    try:
        analyzer = MarketSentimentAnalyzer()
        report = analyzer.analyze()
        result = analyzer.format_report(report)

        console.print(Panel(result, title="市场情绪分析", border_style="magenta"))

        if output:
            from pathlib import Path
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]市场情绪分析失败: {e}[/red]")
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
