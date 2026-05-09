"""
报告生成命令.

fund report --type single_fund --fund 000001 --format pdf
fund report --type portfolio --funds 000001,000002 --format html
"""
from typing import Annotated

import typer

from fund_cli.core.reporters.html_reporter import HtmlReporter
from fund_cli.core.reporters.markdown_reporter import MarkdownReporter
from fund_cli.core.reporters.pdf_reporter import PdfReporter
from fund_cli.core.template_engine import get_template_engine

app = typer.Typer(help="基金报告生成")

REPORTERS = {
    "html": HtmlReporter,
    "markdown": MarkdownReporter,
    "pdf": PdfReporter,
}

REPORT_TYPES = ["single_fund", "portfolio", "market_flow", "risk_control"]


def get_reporter(format_name: str):
    """获取报告生成器."""
    reporter_cls = REPORTERS.get(format_name)
    if reporter_cls is None:
        typer.echo(f"不支持的格式: {format_name}，可选: {list(REPORTERS.keys())}", err=True)
        raise typer.Exit(1)
    return reporter_cls()  # type: ignore[abstract]


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

    reporter = get_reporter(format)

    # 根据报告类型生成内容
    if type == "single_fund":
        if not fund:
            typer.echo("请指定基金代码: --fund 000001", err=True)
            raise typer.Exit(1)
        content = reporter.generate(fund_code=fund, metrics={})
    elif type == "portfolio":
        if not funds:
            typer.echo("请指定基金代码列表: --funds 000001,000002", err=True)
            raise typer.Exit(1)
        content = reporter.generate(fund_code=funds.split(",")[0], metrics={})
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
