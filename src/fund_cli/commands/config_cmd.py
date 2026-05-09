"""
配置管理命令

提供配置查看和设置功能。
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from fund_cli.config import get_config

app = typer.Typer(help="配置管理命令")
console = Console()


def _get_env_path() -> Path:
    """获取 .env 文件路径"""
    return Path.cwd() / ".env"


def _load_env_lines() -> list[str]:
    """读取 .env 文件所有行"""
    env_path = _get_env_path()
    if env_path.exists():
        return env_path.read_text(encoding="utf-8").splitlines()
    return []


def _save_env_lines(lines: list[str]) -> None:
    """写入 .env 文件"""
    env_path = _get_env_path()
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _key_to_env_var(key: str) -> str | None:
    """将用户友好的配置键映射为环境变量名。

    支持格式:
      - data.cache_ttl -> FUND_DATA_CACHE_TTL
      - ai.provider -> FUND_AI_PROVIDER
      - debug -> FUND_DEBUG
      - akshare_enabled -> FUND_DATA_AKSHARE_ENABLED
    """
    key_map = {
        # 顶层
        "debug": "FUND_DEBUG",
        "dev_mode": "FUND_DEV_MODE",
        # data
        "data.akshare_enabled": "FUND_DATA_AKSHARE_ENABLED",
        "data.cache_ttl": "FUND_DATA_CACHE_TTL",
        "data.cache_dir": "FUND_DATA_CACHE_DIR",
        "data.tushare_token": "FUND_DATA_TUSHARE_TOKEN",
        # analysis
        "analysis.risk_free_rate": "FUND_ANALYSIS_RISK_FREE_RATE",
        "analysis.default_benchmark": "FUND_ANALYSIS_DEFAULT_BENCHMARK",
        "analysis.default_period": "FUND_ANALYSIS_DEFAULT_PERIOD",
        # ai
        "ai.provider": "FUND_AI_PROVIDER",
        "ai.model": "FUND_AI_MODEL",
        "ai.api_key": "FUND_AI_API_KEY",
        "ai.api_base": "FUND_AI_API_BASE",
        "ai.temperature": "FUND_AI_TEMPERATURE",
        "ai.max_tokens": "FUND_AI_MAX_TOKENS",
        "ai.timeout": "FUND_AI_TIMEOUT",
        "ai.retry_count": "FUND_AI_RETRY_COUNT",
        "ai.qwen_api_key": "FUND_AI_QWEN_API_KEY",
        "ai.qwen_model": "FUND_AI_QWEN_MODEL",
        # output
        "output.default_format": "FUND_OUTPUT_DEFAULT_FORMAT",
        "output.csv_encoding": "FUND_OUTPUT_CSV_ENCODING",
        "output.number_decimal": "FUND_OUTPUT_NUMBER_DECIMAL",
        "output.date_format": "FUND_OUTPUT_DATE_FORMAT",
        # database
        "database.use_postgres": "FUND_DB_USE_POSTGRES",
        "database.host": "FUND_DB_HOST",
        "database.port": "FUND_DB_PORT",
        "database.database": "FUND_DB_DATABASE",
        "database.user": "FUND_DB_USER",
        "database.password": "FUND_DB_PASSWORD",
        # agent
        "agent.enable_human_review": "FUND_AGENT_ENABLE_HUMAN_REVIEW",
        "agent.use_chroma_memory": "FUND_AGENT_USE_CHROMA_MEMORY",
        # 简写别名
        "akshare_enabled": "FUND_DATA_AKSHARE_ENABLED",
        "cache_ttl": "FUND_DATA_CACHE_TTL",
        "cache_dir": "FUND_DATA_CACHE_DIR",
        "tushare_token": "FUND_DATA_TUSHARE_TOKEN",
        "risk_free_rate": "FUND_ANALYSIS_RISK_FREE_RATE",
        "default_benchmark": "FUND_ANALYSIS_DEFAULT_BENCHMARK",
        "provider": "FUND_AI_PROVIDER",
        "model": "FUND_AI_MODEL",
        "api_key": "FUND_AI_API_KEY",
        "api_base": "FUND_AI_API_BASE",
        "temperature": "FUND_AI_TEMPERATURE",
        "max_tokens": "FUND_AI_MAX_TOKENS",
        "timeout": "FUND_AI_TIMEOUT",
        "retry_count": "FUND_AI_RETRY_COUNT",
        "qwen_api_key": "FUND_AI_QWEN_API_KEY",
        "qwen_model": "FUND_AI_QWEN_MODEL",
        "default_format": "FUND_OUTPUT_DEFAULT_FORMAT",
        "csv_encoding": "FUND_OUTPUT_CSV_ENCODING",
        "number_decimal": "FUND_OUTPUT_NUMBER_DECIMAL",
        "date_format": "FUND_OUTPUT_DATE_FORMAT",
    }
    return key_map.get(key)


def _persist_config(key: str, value: str) -> bool:
    """将配置项持久化到 .env 文件。

    Returns:
        是否成功写入
    """
    env_var = _key_to_env_var(key)
    if env_var is None:
        return False

    lines = _load_env_lines()
    found = False
    entry = f"{env_var}={value}"

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(f"{env_var}=") or stripped.startswith(f"{env_var} ="):
            lines[i] = entry
            found = True
            break
        if stripped == env_var:
            lines[i] = entry
            found = True
            break

    if not found:
        # 确保文件末尾有空行
        if lines and lines[-1].strip() != "":
            lines.append("")
        lines.append(entry)

    _save_env_lines(lines)
    return True


@app.command("show")
def show_config() -> None:
    """显示当前配置。"""
    try:
        config = get_config()

        table = Table(title="当前配置")
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")

        # 应用配置
        table.add_row("应用名称", config.app_name)
        table.add_row("调试模式", str(config.debug))

        # 数据配置
        table.add_row("AKShare启用", str(config.data.akshare_enabled))
        table.add_row("缓存TTL", f"{config.data.cache_ttl}秒")
        table.add_row("缓存目录", config.data.cache_dir)

        # 分析配置
        table.add_row("无风险利率", f"{config.analysis.risk_free_rate * 100}%")
        table.add_row("默认基准", config.analysis.default_benchmark)

        console.print(table)

    except Exception as e:
        console.print(f"[red]获取配置失败: {e}[/red]")


@app.command("output")
def output_config(
    format: str = typer.Option(None, help="默认输出格式: table/csv/json"),
    encoding: str = typer.Option(None, help="CSV编码"),
    decimal: int = typer.Option(None, help="数字小数位"),
):
    """输出格式配置 (FUND-CONFIG-004)"""
    from fund_cli.config import AppConfig

    config = AppConfig()
    if format:
        config.output.default_format = format
    if encoding:
        config.output.csv_encoding = encoding
    if decimal is not None:
        config.output.number_decimal = decimal

    console.print("\n[bold]输出格式配置[/bold]")
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("配置项", style="cyan")
    table.add_column("当前值")
    table.add_row("默认格式", config.output.default_format)
    table.add_row("CSV编码", config.output.csv_encoding)
    table.add_row("CSV分隔符", config.output.csv_delimiter)
    table.add_row("JSON缩进", str(config.output.json_indent))
    table.add_row("数字小数位", str(config.output.number_decimal))
    table.add_row("日期格式", config.output.date_format)
    console.print(table)


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help="配置键（如 ai.provider, data.cache_ttl）"),
    value: str = typer.Argument(..., help="配置值"),
    persist: bool = typer.Option(True, "--persist/--no-persist", help="是否持久化到 .env 文件"),
):
    """设置配置项。

    支持的配置键格式:
      - 点分隔: ai.provider, data.cache_ttl, analysis.risk_free_rate
      - 简写: provider, cache_ttl, debug

    示例:
        fund config set ai.provider qwen
        fund config set data.cache_ttl 7200
        fund config set debug true
        fund config set ai.api_key sk-xxx --no-persist
    """
    env_var = _key_to_env_var(key)

    if env_var is None:
        console.print(f"[red]未知配置键: {key}[/red]")
        console.print("[dim]使用 fund config set --help 查看支持的配置键[/dim]")
        raise typer.Exit(1) from None

    if persist:
        try:
            _persist_config(key, value)
            env_path = _get_env_path()
            console.print("[green]✓ 配置已持久化[/green]")
            console.print(f"  {env_var}={value}")
            console.print(f"  文件: {env_path}")
            console.print("[dim]提示: 重启应用后生效[/dim]")
        except Exception as e:
            console.print(f"[red]持久化失败: {e}[/red]")
            console.print(f"[yellow]配置仅在当前会话生效: {key}={value}[/yellow]")
    else:
        console.print(f"[yellow]配置仅在当前会话生效: {key}={value}[/yellow]")
        console.print("[dim]使用 --persist 持久化到 .env 文件[/dim]")


@app.command("list-keys")
def list_config_keys() -> None:
    """列出所有可配置的键。"""
    table = Table(title="可配置项")
    table.add_column("配置键", style="cyan")
    table.add_column("环境变量", style="dim")
    table.add_column("说明", style="green")

    entries = [
        ("debug", "FUND_DEBUG", "调试模式 (true/false)"),
        ("data.akshare_enabled", "FUND_DATA_AKSHARE_ENABLED", "启用AKShare数据源"),
        ("data.cache_ttl", "FUND_DATA_CACHE_TTL", "缓存过期时间(秒)"),
        ("data.cache_dir", "FUND_DATA_CACHE_DIR", "缓存目录路径"),
        ("data.tushare_token", "FUND_DATA_TUSHARE_TOKEN", "Tushare API Token"),
        ("analysis.risk_free_rate", "FUND_ANALYSIS_RISK_FREE_RATE", "无风险利率 (0-1)"),
        ("analysis.default_benchmark", "FUND_ANALYSIS_DEFAULT_BENCHMARK", "默认基准指数代码"),
        ("ai.provider", "FUND_AI_PROVIDER", "LLM提供商 (openai/qwen/litellm)"),
        ("ai.model", "FUND_AI_MODEL", "模型名称"),
        ("ai.api_key", "FUND_AI_API_KEY", "API密钥"),
        ("ai.api_base", "FUND_AI_API_BASE", "API基础URL"),
        ("ai.temperature", "FUND_AI_TEMPERATURE", "温度参数 (0-2)"),
        ("ai.max_tokens", "FUND_AI_MAX_TOKENS", "最大token数"),
        ("ai.qwen_api_key", "FUND_AI_QWEN_API_KEY", "阿里云Qwen API Key"),
        ("ai.qwen_model", "FUND_AI_QWEN_MODEL", "Qwen模型名称"),
        ("output.default_format", "FUND_OUTPUT_DEFAULT_FORMAT", "默认输出格式 (table/csv/json)"),
        ("output.number_decimal", "FUND_OUTPUT_NUMBER_DECIMAL", "数字小数位"),
        ("database.use_postgres", "FUND_DB_USE_POSTGRES", "启用PostgreSQL (true/false)"),
        ("database.host", "FUND_DB_HOST", "数据库主机"),
        ("database.port", "FUND_DB_PORT", "数据库端口"),
        ("database.database", "FUND_DB_DATABASE", "数据库名"),
        ("database.user", "FUND_DB_USER", "数据库用户名"),
        ("database.password", "FUND_DB_PASSWORD", "数据库密码"),
        ("agent.enable_human_review", "FUND_AGENT_ENABLE_HUMAN_REVIEW", "启用人工审核 (true/false)"),
        ("agent.use_chroma_memory", "FUND_AGENT_USE_CHROMA_MEMORY", "启用ChromaDB记忆 (true/false)"),
    ]

    for key, env_var, desc in entries:
        table.add_row(key, env_var, desc)

    console.print(table)


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context) -> None:
    """默认显示配置"""
    if ctx.invoked_subcommand is None:
        show_config()


if __name__ == "__main__":
    app()
