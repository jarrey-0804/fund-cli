"""
AI 分析命令（V2.0 实现）

提供 AI 辅助分析功能，支持基金摘要生成、对比分析、投资建议等。
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="AI分析命令（V2.0功能）")
console = Console()


@app.command("config")
def ai_config(
    action: str = typer.Argument("show", help="操作: show/set-provider/test"),
    provider: str = typer.Option(None, "--provider", "-p", help="提供商名称"),
    model: str = typer.Option(None, "--model", "-m", help="模型名称"),
) -> None:
    """
    AI配置管理

    示例:
        fund ai config show                    # 显示当前配置
        fund ai config test                    # 测试AI连接
        fund ai config set-provider --provider qwen  # 设置提供商
    """
    from fund_cli.ai.providers import get_provider
    from fund_cli.config import get_config

    if action == "show":
        config = get_config().ai
        table = Table(title="AI配置")
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")

        table.add_row("提供商", config.provider)
        table.add_row("模型", config.model)
        table.add_row("Qwen模型", config.qwen_model)
        table.add_row("温度参数", str(config.temperature))
        table.add_row("最大Token", str(config.max_tokens))
        table.add_row("超时(秒)", str(config.timeout))
        table.add_row("重试次数", str(config.retry_count))
        table.add_row("API Key", "已设置" if config.api_key else "未设置")
        table.add_row("Qwen API Key", "已设置" if config.qwen_api_key else "未设置")

        console.print(table)

    elif action == "test":
        config = get_config().ai

        if not config.validate_config():
            console.print("[red]配置无效，请检查API Key和模型设置[/red]")
            raise typer.Exit(1) from None

        console.print(f"[dim]测试 {config.provider} 提供商连接...[/dim]")

        try:
            provider_instance = get_provider(config)
            if provider_instance.is_available():
                console.print(f"[green]✓ {config.provider} 连接成功[/green]")
            else:
                console.print(f"[red]✗ {config.provider} 连接失败[/red]")
                raise typer.Exit(1) from None
        except Exception as e:
            console.print(f"[red]连接测试失败: {e}[/red]")
            raise typer.Exit(1) from None

    elif action == "set-provider":
        if not provider:
            console.print("[red]请使用 --provider 指定提供商[/red]")
            raise typer.Exit(1) from None

        # 更新配置（仅内存中，不持久化到文件）
        config = get_config().ai
        config.provider = provider
        if model:
            if provider == "qwen":
                config.qwen_model = model
            else:
                config.model = model

        console.print(f"[green]提供商已设置为: {provider}[/green]")
        if model:
            console.print(f"[green]模型已设置为: {model}[/green]")

    else:
        console.print(f"[red]未知操作: {action}[/red]")
        console.print("支持的操作: show, test, set-provider")
        raise typer.Exit(1) from None


@app.command("summarize")
def ai_summarize(
    fund_code: str = typer.Argument(..., help="基金代码"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    AI生成基金分析摘要

    示例:
        fund ai summarize 000001
        fund ai summarize 000001 --output summary.txt
    """
    from fund_cli.ai.analyzer import AIAnalyzer
    from fund_cli.analysis.performance import PerformanceAnalyzer
    from fund_cli.data.adapters import get_adapter

    try:
        # 获取基金数据
        adapter = get_adapter()
        fund_info = adapter.get_fund_info(fund_code)
        nav_data = adapter.get_fund_nav(fund_code, period="1y")

        # 计算业绩指标
        perf_analyzer = PerformanceAnalyzer()
        metrics = perf_analyzer.calculate_metrics(nav_data)

        # 生成AI摘要
        ai_analyzer = AIAnalyzer()
        fund_data = {
            "info": fund_info,
            "nav": nav_data,
            "metrics": metrics,
        }
        summary = ai_analyzer.summarize_fund(fund_code, fund_data)

        # 输出结果
        console.print(Panel(summary, title=f"AI分析摘要 - {fund_code}"))

        if output:
            Path(output).write_text(summary, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("compare")
def ai_compare(
    fund_codes: str = typer.Argument(..., help="基金代码列表（逗号分隔）"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    AI对比分析多只基金

    示例:
        fund ai compare 000001,000002,000003
        fund ai compare 000001,000002 --output compare.txt
    """
    from fund_cli.ai.analyzer import AIAnalyzer
    from fund_cli.analysis.performance import PerformanceAnalyzer
    from fund_cli.data.adapters import get_adapter

    try:
        codes = [c.strip() for c in fund_codes.split(",")]
        if len(codes) < 2:
            console.print("[red]请至少提供2只基金进行对比[/red]")
            raise typer.Exit(1) from None

        # 获取基金数据
        adapter = get_adapter()
        perf_analyzer = PerformanceAnalyzer()

        funds_data = []
        for code in codes:
            fund_info = adapter.get_fund_info(code)
            nav_data = adapter.get_fund_nav(code, period="1y")
            metrics = perf_analyzer.calculate_metrics(nav_data)
            funds_data.append(
                {
                    "code": code,
                    "info": fund_info,
                    "nav": nav_data,
                    "metrics": metrics,
                }
            )

        # 生成AI对比分析
        ai_analyzer = AIAnalyzer()
        comparison = ai_analyzer.compare_funds(codes, funds_data)

        # 输出结果
        console.print(Panel(comparison, title=f"AI对比分析 - {', '.join(codes)}"))

        if output:
            Path(output).write_text(comparison, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]对比分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("advice")
def ai_advice(
    fund_code: str = typer.Argument(..., help="基金代码"),
    risk_profile: str = typer.Option(
        "moderate", "--risk", "-r", help="风险偏好: conservative/moderate/aggressive"
    ),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    AI生成投资建议

    示例:
        fund ai advice 000001
        fund ai advice 000001 --risk conservative
        fund ai advice 000001 --risk aggressive --output advice.txt
    """
    from fund_cli.ai.analyzer import AIAnalyzer
    from fund_cli.analysis.performance import PerformanceAnalyzer
    from fund_cli.data.adapters import get_adapter

    try:
        # 验证风险偏好
        valid_profiles = ["conservative", "moderate", "aggressive"]
        if risk_profile not in valid_profiles:
            console.print(f"[red]无效的风险偏好，请选择: {', '.join(valid_profiles)}[/red]")
            raise typer.Exit(1) from None

        # 获取基金数据
        adapter = get_adapter()
        fund_info = adapter.get_fund_info(fund_code)
        nav_data = adapter.get_fund_nav(fund_code, period="1y")

        # 计算业绩指标
        perf_analyzer = PerformanceAnalyzer()
        metrics = perf_analyzer.calculate_metrics(nav_data)

        # 生成投资建议
        ai_analyzer = AIAnalyzer()
        fund_data = {
            "info": fund_info,
            "nav": nav_data,
            "metrics": metrics,
        }
        advice = ai_analyzer.investment_advice(fund_code, fund_data, risk_profile)

        # 格式化输出
        table = Table(title=f"AI投资建议 - {fund_code} ({risk_profile})")
        table.add_column("项目", style="cyan")
        table.add_column("内容", style="green")

        table.add_row("适合性", advice.get("suitability", "未知"))
        table.add_row("配置比例", advice.get("allocation", "未知"))
        table.add_row("风险提示", advice.get("risk_warning", "未知"))
        table.add_row("持有建议", advice.get("holding_period", "未知"))

        console.print(table)

        if output:
            import json

            Path(output).write_text(
                json.dumps(advice, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]生成建议失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("risk")
def ai_risk(
    fund_code: str = typer.Argument(..., help="基金代码"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="详细分析"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    AI深度风险评估

    示例:
        fund ai risk 000001
        fund ai risk 000001 --detailed
        fund ai risk 000001 --detailed --output risk.txt
    """
    from fund_cli.ai.analyzer import AIAnalyzer
    from fund_cli.data.adapters import get_adapter

    try:
        # 获取基金数据
        adapter = get_adapter()
        fund_info = adapter.get_fund_info(fund_code)
        nav_data = adapter.get_fund_nav(fund_code, period="1y")

        # 生成风险评估
        ai_analyzer = AIAnalyzer()
        fund_data = {
            "code": fund_code,
            "info": fund_info,
            "nav": nav_data,
        }
        risk_assessment = ai_analyzer.risk_assessment(fund_code, fund_data, detailed)

        # 格式化输出
        table = Table(title=f"AI风险评估 - {fund_code}")
        table.add_column("项目", style="cyan")
        table.add_column("内容", style="green")

        table.add_row("风险等级", risk_assessment.get("risk_level", "未知"))
        table.add_row("主要风险", risk_assessment.get("main_risks", "未知"))
        table.add_row("风险预警", risk_assessment.get("warnings", "无"))
        table.add_row("控制建议", risk_assessment.get("control_suggestions", "未知"))

        if detailed:
            table.add_row("详细分析", risk_assessment.get("detailed_analysis", "未知"))

        console.print(table)

        if output:
            import json

            Path(output).write_text(
                json.dumps(risk_assessment, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]风险评估失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("insight")
def ai_insight(
    fund_code: str = typer.Argument(..., help="基金代码"),
    market_context: str = typer.Option(None, "--context", "-c", help="市场环境描述"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    AI市场解读

    示例:
        fund ai insight 000001
        fund ai insight 000001 --context "当前市场处于震荡期"
        fund ai insight 000001 --output insight.txt
    """
    from fund_cli.ai.analyzer import AIAnalyzer
    from fund_cli.data.adapters import get_adapter

    try:
        # 获取基金数据
        adapter = get_adapter()
        fund_info = adapter.get_fund_info(fund_code)
        nav_data = adapter.get_fund_nav(fund_code, period="1y")

        # 生成市场解读
        ai_analyzer = AIAnalyzer()
        fund_data = {
            "code": fund_code,
            "info": fund_info,
            "nav": nav_data,
        }
        insight = ai_analyzer.market_insight(fund_code, fund_data, market_context)

        # 输出结果
        console.print(Panel(insight, title=f"AI市场解读 - {fund_code}"))

        if output:
            Path(output).write_text(insight, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]市场解读失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("portfolio")
def ai_portfolio(
    fund_codes: str = typer.Argument(..., help="基金代码列表（逗号分隔）"),
    weights: str = typer.Option(
        None, "--weights", "-w", help="权重配置（逗号分隔，如0.5,0.3,0.2）"
    ),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    AI组合分析

    示例:
        fund ai portfolio 000001,000002
        fund ai portfolio 000001,000002 --weights 0.6,0.4
        fund ai portfolio 000001,000002,000003 --weights 0.5,0.3,0.2
    """
    from fund_cli.ai.analyzer import AIAnalyzer
    from fund_cli.analysis.performance import PerformanceAnalyzer
    from fund_cli.data.adapters import get_adapter

    try:
        codes = [c.strip() for c in fund_codes.split(",")]
        if len(codes) < 2:
            console.print("[red]请至少提供2只基金进行组合分析[/red]")
            raise typer.Exit(1) from None

        # 解析权重
        weight_list = None
        if weights:
            weight_list = [float(w.strip()) for w in weights.split(",")]
            if len(weight_list) != len(codes):
                console.print("[red]权重数量必须与基金数量一致[/red]")
                raise typer.Exit(1) from None
            if abs(sum(weight_list) - 1.0) > 0.01:
                console.print("[red]权重总和必须等于1[/red]")
                raise typer.Exit(1) from None

        # 获取基金数据
        adapter = get_adapter()
        perf_analyzer = PerformanceAnalyzer()

        portfolio_data = {
            "funds": [],
            "weights": weight_list or [1.0 / len(codes)] * len(codes),
        }

        for code in codes:
            fund_info = adapter.get_fund_info(code)
            nav_data = adapter.get_fund_nav(code, period="1y")
            metrics = perf_analyzer.calculate_metrics(nav_data)
            portfolio_data["funds"].append(
                {
                    "code": code,
                    "info": fund_info,
                    "metrics": metrics,
                }
            )

        # 生成组合分析
        ai_analyzer = AIAnalyzer()
        review = ai_analyzer.portfolio_review(portfolio_data)

        # 格式化输出
        table = Table(title=f"AI组合分析 - {', '.join(codes)}")
        table.add_column("项目", style="cyan")
        table.add_column("内容", style="green")

        table.add_row("组合评价", review.get("overall_assessment", "未知"))
        table.add_row("优化建议", review.get("optimization_suggestions", "未知"))
        table.add_row("风险分散度", review.get("diversification", "未知"))

        console.print(table)

        if output:
            import json

            Path(output).write_text(
                json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]组合分析失败: {e}[/red]")
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
