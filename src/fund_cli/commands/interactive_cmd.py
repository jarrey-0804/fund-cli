"""交互式模式"""

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="交互式模式")
console = Console()


@app.command()
def interactive_mode():
    """启动交互式REPL模式 (CLI-UX-006)"""
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.completion import WordCompleter
        from prompt_toolkit.history import InMemoryHistory
    except ImportError:
        console.print("[yellow]需要安装 prompt_toolkit: pip install prompt_toolkit[/yellow]")
        raise typer.Exit(1) from None

    commands = [
        "info",
        "filter",
        "analyze",
        "compare",
        "optimize",
        "monitor",
        "holding",
        "manager",
        "data",
        "config",
        "help",
        "exit",
        "quit",
    ]

    completer = WordCompleter(commands, ignore_case=True)
    session = PromptSession(completer=completer, history=InMemoryHistory())

    console.print(
        Panel(
            "[bold]Fund CLI 交互式模式[/bold]\n"
            "输入命令（如 info 000001）或 help 查看帮助\n"
            "输入 exit 或 quit 退出",
            box=box.ROUNDED,
            border_style="blue",
        )
    )

    while True:
        try:
            user_input = session.prompt("fund> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]再见！[/yellow]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            console.print("[yellow]再见！[/yellow]")
            break

        if user_input.lower() == "help":
            console.print("可用命令: info, filter, analyze, compare, optimize,")
            console.print("          monitor, holding, manager, data, config")
            console.print("输入 exit 或 quit 退出")
            continue

        # 执行命令
        try:
            from typer.testing import CliRunner

            from fund_cli.cli import app as main_app

            runner = CliRunner()
            args = user_input.split()
            result = runner.invoke(main_app, args)
            if result.output:
                console.print(result.output)
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
