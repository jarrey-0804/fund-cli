"""
Fund CLI 主入口

专业基金分析命令行工具的主程序入口。
"""

import typer
from rich.console import Console

from fund_cli import __version__

# 创建主应用
app = typer.Typer(
    name="fund",
    help="专业基金分析CLI工具 - 面向机构客户",
    add_completion=True,
    rich_markup_mode="rich",
)

# 全局控制台实例
console = Console()


def version_callback(value: bool) -> None:
    """显示版本信息"""
    if value:
        console.print(f"[bold blue]Fund CLI[/bold blue] 版本: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="显示版本信息",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """
    Fund CLI - 专业基金分析命令行工具

    面向机构客户的基金分析工具，支持基金筛选、业绩分析、组合优化等功能。

    使用 --help 查看各子命令的详细帮助。
    """
    pass


# 导入子命令模块
from fund_cli.commands import (  # noqa: E402
    ai_cmd,
    analyze_cmd,
    compare_cmd,
    config_cmd,
    data_cmd,
    filter_cmd,
    holding_cmd,
    interactive_cmd,
    manager_cmd,
    monitor_cmd,
    optimize_cmd,
    report_cmd,  # noqa: E402  # v3.1 新增
)

# 注册子命令
app.add_typer(filter_cmd.app, name="filter")
app.add_typer(analyze_cmd.app, name="analyze")
app.add_typer(compare_cmd.app, name="compare")
app.add_typer(optimize_cmd.app, name="optimize")
app.add_typer(monitor_cmd.app, name="monitor")
app.add_typer(data_cmd.app, name="data")
app.add_typer(config_cmd.app, name="config")
app.add_typer(ai_cmd.app, name="ai")
app.add_typer(holding_cmd.app, name="holding")
app.add_typer(manager_cmd.app, name="manager")
app.add_typer(interactive_cmd.app, name="interactive")
app.add_typer(report_cmd.app, name="report")  # v3.1 新增


# 直接调用的命令
@app.command("version")
def version() -> None:
    """
    显示版本信息。

    示例:
        fund version
    """
    console.print(f"[bold blue]Fund CLI[/bold blue] 版本: {__version__}")


@app.command("info")
def info(
    fund_code: str = typer.Argument(..., help="基金代码（6位数字）"),
) -> None:
    """
    查看基金基础信息。

    示例:
        fund info 000001
    """
    from fund_cli.commands.analyze_cmd import info_fund

    info_fund(fund_code)


@app.command("doctor")
def doctor() -> None:
    """
    诊断环境配置，检查依赖和数据源可用性。

    示例:
        fund doctor
    """
    import sys
    from importlib import import_module
    from pathlib import Path

    console.print("\n[bold]Fund CLI 环境诊断[/bold]\n")

    checks_passed = 0
    checks_total = 0

    # 1. Python 版本
    checks_total += 1
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    console.print(f"  [green]✓[/green] Python 版本: {py_version} (>=3.10)")
    checks_passed += 1

    # 2. 核心依赖检查
    core_deps = [
        ("typer", "CLI框架"),
        ("rich", "终端美化"),
        ("pandas", "数据处理"),
        ("numpy", "数值计算"),
        ("pydantic", "数据校验"),
        ("pydantic_settings", "配置管理"),
    ]

    console.print("\n[bold]核心依赖:[/bold]")
    for module_name, desc in core_deps:
        checks_total += 1
        try:
            mod = import_module(module_name)
            ver = getattr(mod, "__version__", "未知")
            console.print(f"  [green]✓[/green] {desc} ({module_name}): {ver}")
            checks_passed += 1
        except ImportError:
            console.print(f"  [red]✗[/red] {desc} ({module_name}): 未安装")

    # 3. 数据源检查
    data_deps = [
        ("akshare", "AKShare数据源"),
        ("tushare", "Tushare数据源"),
    ]

    console.print("\n[bold]数据源:[/bold]")
    for module_name, desc in data_deps:
        checks_total += 1
        try:
            import_module(module_name)
            console.print(f"  [green]✓[/green] {desc} ({module_name}): 已安装")
            checks_passed += 1
        except ImportError:
            console.print(f"  [yellow]⚠[/yellow] {desc} ({module_name}): 未安装（可选）")

    # 4. AI 依赖检查
    ai_deps = [
        ("langchain_core", "LangChain核心"),
        ("langgraph", "LangGraph"),
        ("litellm", "LiteLLM"),
    ]

    console.print("\n[bold]AI功能:[/bold]")
    for module_name, desc in ai_deps:
        checks_total += 1
        try:
            mod = import_module(module_name)
            ver = getattr(mod, "__version__", "未知")
            console.print(f"  [green]✓[/green] {desc} ({module_name}): {ver}")
            checks_passed += 1
        except ImportError:
            console.print(f"  [yellow]⚠[/yellow] {desc} ({module_name}): 未安装")

    # 5. 配置文件检查
    console.print("\n[bold]配置文件:[/bold]")
    env_path = Path.cwd() / ".env"
    checks_total += 1
    if env_path.exists():
        console.print("  [green]✓[/green] .env 文件: 已存在")
        checks_passed += 1
    else:
        console.print("  [yellow]⚠[/yellow] .env 文件: 不存在（可选）")

    # 6. 缓存目录检查
    cache_dir = Path.home() / ".fund_cli" / "cache"
    checks_total += 1
    if cache_dir.exists():
        console.print(f"  [green]✓[/green] 缓存目录: {cache_dir}")
        checks_passed += 1
    else:
        console.print("  [yellow]⚠[/yellow] 缓存目录: 不存在（首次运行时自动创建）")

    # 7. AI 配置检查
    console.print("\n[bold]AI配置:[/bold]")
    try:
        from fund_cli.config import get_config
        cfg = get_config()
        checks_total += 1
        if cfg.ai.api_key or cfg.ai.qwen_api_key:
            console.print(f"  [green]✓[/green] API Key: 已配置 (provider={cfg.ai.provider})")
            checks_passed += 1
        else:
            console.print("  [yellow]⚠[/yellow] API Key: 未配置（AI功能需要）")
    except Exception as e:
        checks_total += 1
        console.print(f"  [red]✗[/red] 配置加载失败: {e}")

    # 8. 数据库检查
    console.print("\n[bold]数据库:[/bold]")
    try:
        from fund_cli.config import get_config
        cfg = get_config()
        checks_total += 1
        if cfg.database.use_postgres:
            try:
                import psycopg2  # noqa: F401
                console.print("  [green]✓[/green] PostgreSQL驱动: 已安装")
                checks_passed += 1
            except ImportError:
                console.print("  [yellow]⚠[/yellow] PostgreSQL驱动: 未安装（psycopg2）")
        else:
            console.print("  [dim]  PostgreSQL: 未启用（使用内存存储）[/dim]")
            checks_passed += 1
    except Exception:
        pass

    # 汇总
    console.print(f"\n[bold]诊断结果: {checks_passed}/{checks_total} 项通过[/bold]")
    if checks_passed == checks_total:
        console.print("[green]所有检查通过，环境配置正常！[/green]\n")
    elif checks_passed >= checks_total * 0.8:
        console.print("[yellow]大部分检查通过，部分可选组件未安装。[/yellow]\n")
    else:
        console.print("[red]多项检查未通过，请检查环境配置。[/red]\n")


if __name__ == "__main__":
    app()
