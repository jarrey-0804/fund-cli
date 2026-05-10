"""
报告生成命令.

fund report --type single_fund --fund 000001 --format pdf
fund report --type portfolio --funds 000001,000002 --format html
"""

from typing import Annotated, Any

import typer
from rich.console import Console

from fund_cli.analysis.performance import PerformanceAnalyzer
from fund_cli.analysis.risk import RiskAnalyzer
from fund_cli.core.data_manager import get_data_manager
from fund_cli.core.report_validator import ReportValidator
from fund_cli.core.reporter import Reporter
from fund_cli.core.reporters.html_reporter import HtmlReporter
from fund_cli.core.reporters.markdown_reporter import MarkdownReporter
from fund_cli.core.reporters.pdf_reporter import PdfReporter
from fund_cli.core.reporters.risk_control_reporter import RiskControlReporter
from fund_cli.core.template_engine import get_template_engine

console = Console()

app = typer.Typer(help="基金报告生成")

REPORTERS: dict[str, type[Reporter]] = {
    "html": HtmlReporter,
    "markdown": MarkdownReporter,
    "pdf": PdfReporter,
    "risk_control": RiskControlReporter,
}

REPORT_TYPES = ["single_fund", "portfolio", "market_flow", "risk_control"]


def get_reporter(format_name: str, report_type: str = "single_fund"):
    """获取报告生成器."""
    # 风控报告强制使用 RiskControlReporter
    if report_type == "risk_control":
        return RiskControlReporter()

    reporter_cls = REPORTERS.get(format_name)
    if reporter_cls is None:
        typer.echo(f"不支持的格式: {format_name}，可选: {list(REPORTERS.keys())}", err=True)
        raise typer.Exit(1)
    return reporter_cls()


def fetch_and_analyze(fund_code: str) -> tuple[dict, Any, Any]:
    """获取数据并执行分析."""
    dm = get_data_manager()

    # 获取净值数据
    nav_data = dm.get_fund_nav(fund_code)
    if nav_data is None or nav_data.empty:
        raise ValueError(f"无法获取基金 {fund_code} 的净值数据")

    # 获取基准数据
    try:
        benchmark_data = dm.get_benchmark_nav("000300.SH")
    except Exception:
        benchmark_data = None

    # 执行业绩分析
    perf_analyzer = PerformanceAnalyzer()
    perf_result = perf_analyzer.analyze(nav_data["daily_return"].dropna())

    # 执行风险分析
    risk_analyzer = RiskAnalyzer()
    risk_result = risk_analyzer.analyze(nav_data["daily_return"].dropna())

    # 合并指标
    metrics = {
        **perf_result,
        **risk_result,
        "fund_code": fund_code,
    }

    return metrics, nav_data, benchmark_data


@app.command()
def generate(
    type: Annotated[str, typer.Option("--type", "-t", help="报告类型")] = "single_fund",
    fund: Annotated[str | None, typer.Option("--fund", "-f", help="基金代码")] = None,
    funds: Annotated[str | None, typer.Option("--funds", help="多个基金代码(逗号分隔)")] = None,
    format: Annotated[str, typer.Option("--format", help="输出格式(html/markdown/pdf)")] = "html",
    output: Annotated[str | None, typer.Option("--output", "-o", help="输出文件路径")] = None,
    template: Annotated[str | None, typer.Option("--template", help="自定义模板路径")] = None,
):
    """生成基金分析报告."""
    if type not in REPORT_TYPES:
        typer.echo(f"不支持的报告类型: {type}，可选: {REPORT_TYPES}", err=True)
        raise typer.Exit(1)

    reporter = get_reporter(format, type)

    # 根据报告类型生成内容
    if type == "single_fund":
        if not fund:
            typer.echo("请指定基金代码: --fund 000001", err=True)
            raise typer.Exit(1)
        try:
            metrics, nav_data, benchmark_data = fetch_and_analyze(fund)
        except Exception as e:
            typer.echo(f"数据获取或分析失败: {e}", err=True)
            raise typer.Exit(1) from None
        # Validate report data before generating
        validator = ReportValidator()
        validation = validator.validate_metrics(metrics, report_type=type)

        if not validation.passed:
            console.print(f"[red]报告数据不完整，缺少字段: {validation.missing_fields}[/red]")
            raise typer.Exit(1)

        if validation.warnings:
            console.print(f"[yellow]报告警告: {validation.warnings}[/yellow]")
        content = reporter.generate(
            fund_code=fund, metrics=metrics, nav_data=nav_data, benchmark_data=benchmark_data
        )

    elif type == "portfolio":
        if not funds:
            typer.echo("请指定基金代码列表: --funds 000001,000002", err=True)
            raise typer.Exit(1)
        fund_list = [f.strip() for f in funds.split(",")]
        # 简化为第一个基金的分析
        try:
            metrics, nav_data, benchmark_data = fetch_and_analyze(fund_list[0])
        except Exception as e:
            typer.echo(f"数据获取或分析失败: {e}", err=True)
            raise typer.Exit(1) from None
        # Validate report data before generating
        validator = ReportValidator()
        validation = validator.validate_metrics(metrics, report_type=type)

        if not validation.passed:
            console.print(f"[red]报告数据不完整，缺少字段: {validation.missing_fields}[/red]")
            raise typer.Exit(1)

        if validation.warnings:
            console.print(f"[yellow]报告警告: {validation.warnings}[/yellow]")
        content = reporter.generate(
            fund_code=fund_list[0],
            metrics=metrics,
            nav_data=nav_data,
            benchmark_data=benchmark_data,
        )

    elif type == "risk_control":
        if not fund:
            typer.echo("请指定基金代码: --fund 000001", err=True)
            raise typer.Exit(1)
        try:
            metrics, nav_data, benchmark_data = fetch_and_analyze(fund)
        except Exception as e:
            typer.echo(f"数据获取或分析失败: {e}", err=True)
            raise typer.Exit(1) from None
        # Validate report data before generating
        validator = ReportValidator()
        validation = validator.validate_metrics(metrics, report_type=type)

        if not validation.passed:
            console.print(f"[red]报告数据不完整，缺少字段: {validation.missing_fields}[/red]")
            raise typer.Exit(1)

        if validation.warnings:
            console.print(f"[yellow]报告警告: {validation.warnings}[/yellow]")
        content = reporter.generate(
            fund_code=fund,
            metrics=metrics,
            nav_data=nav_data,
            benchmark_data=benchmark_data,
            template_path=template,
        )

    else:
        content = reporter.generate(fund_code="MARKET", metrics={})

    # 确定输出路径
    if output is None:
        suffix = "html" if format == "html" else "md" if format == "markdown" else "pdf"
        output = f"report_{type}_{fund or 'portfolio'}.{suffix}"

    reporter.save(content, output)
    typer.echo(f"报告已生成: {output}")


@app.command("list-templates")
def list_templates():
    """列出可用的报告模板."""
    engine = get_template_engine()
    templates = engine.list_templates()
    typer.echo("可用模板:")
    for t in templates:
        typer.echo(f"  - {t}")


if __name__ == "__main__":
    app()
