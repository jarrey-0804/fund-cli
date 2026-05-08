"""组合优化命令"""

import typer
from rich.console import Console
from rich.table import Table

from fund_cli.data.models import OptimizationConstraint

app = typer.Typer(help="组合优化命令")
console = Console()


def _get_returns(fund_codes: list[str], period: str):
    """获取多基金收益率数据"""
    from datetime import date, timedelta

    import pandas as pd

    from fund_cli.core.data_manager import DataManager

    dm = DataManager()
    end = date.today()
    days_map = {"1m": 30, "3m": 90, "6m": 180, "1y": 365, "2y": 730, "3y": 1095}
    start = end - timedelta(days=days_map.get(period, 365))

    all_nav = {}
    for code in fund_codes:
        try:
            nav_df = dm.get_fund_nav(code, start_date=start, end_date=end)
            if not nav_df.empty and "daily_return" in nav_df.columns:
                nav_df = nav_df.dropna(subset=["daily_return"])
                nav_df["daily_return"] = nav_df["daily_return"] / 100.0
                all_nav[code] = nav_df.set_index("nav_date")["daily_return"]
        except Exception:
            continue

    if not all_nav:
        return None

    return pd.DataFrame(all_nav)


@app.command("mean-variance")
def mean_variance(
    fund_codes: str = typer.Argument(..., help="基金代码，逗号分隔"),
    period: str = typer.Option("1y", help="分析周期"),
    risk_free: float = typer.Option(0.03, help="无风险利率"),
    min_weight: float = typer.Option(0.0, help="最小权重"),
    max_weight: float = typer.Option(1.0, help="最大权重"),
):
    """均值-方差优化 (PORTFOLIO-OPT-001)"""
    codes = [c.strip() for c in fund_codes.split(",")]
    returns = _get_returns(codes, period)
    if returns is None or returns.empty:
        console.print("[red]无法获取收益率数据[/red]")
        raise typer.Exit(1) from None

    from fund_cli.core.optimizers.mean_variance import MeanVarianceOptimizer

    constraints = OptimizationConstraint(min_weight=min_weight, max_weight=max_weight)
    optimizer = MeanVarianceOptimizer(risk_free_rate=risk_free)
    result = optimizer.optimize(returns, constraints)

    console.print("\n[bold]均值-方差优化结果[/bold]")
    _print_result(result)


@app.command("max-sharpe")
def max_sharpe(
    fund_codes: str = typer.Argument(..., help="基金代码，逗号分隔"),
    period: str = typer.Option("1y", help="分析周期"),
    risk_free: float = typer.Option(0.03, help="无风险利率"),
    min_weight: float = typer.Option(0.0, help="最小权重"),
    max_weight: float = typer.Option(1.0, help="最大权重"),
):
    """最大夏普比率优化 (PORTFOLIO-OPT-002)"""
    codes = [c.strip() for c in fund_codes.split(",")]
    returns = _get_returns(codes, period)
    if returns is None or returns.empty:
        console.print("[red]无法获取收益率数据[/red]")
        raise typer.Exit(1) from None

    from fund_cli.core.optimizers.max_sharpe import MaxSharpeOptimizer

    constraints = OptimizationConstraint(min_weight=min_weight, max_weight=max_weight)
    optimizer = MaxSharpeOptimizer(risk_free_rate=risk_free)
    result = optimizer.optimize(returns, constraints)

    console.print("\n[bold]最大夏普比率优化结果[/bold]")
    _print_result(result)


@app.command("risk-parity")
def risk_parity(
    fund_codes: str = typer.Argument(..., help="基金代码，逗号分隔"),
    period: str = typer.Option("1y", help="分析周期"),
):
    """风险平价优化 (PORTFOLIO-OPT-003)"""
    codes = [c.strip() for c in fund_codes.split(",")]
    returns = _get_returns(codes, period)
    if returns is None or returns.empty:
        console.print("[red]无法获取收益率数据[/red]")
        raise typer.Exit(1) from None

    from fund_cli.core.optimizers.risk_parity import RiskParityOptimizer

    optimizer = RiskParityOptimizer()
    result = optimizer.optimize(returns)

    console.print("\n[bold]风险平价优化结果[/bold]")
    _print_result(result)


@app.command("frontier")
def efficient_frontier(
    fund_codes: str = typer.Argument(..., help="基金代码，逗号分隔"),
    period: str = typer.Option("1y", help="分析周期"),
    points: int = typer.Option(50, help="前沿点数"),
):
    """有效前沿计算 (PORTFOLIO-OPT-006)"""
    codes = [c.strip() for c in fund_codes.split(",")]
    returns = _get_returns(codes, period)
    if returns is None or returns.empty:
        console.print("[red]无法获取收益率数据[/red]")
        raise typer.Exit(1) from None

    from fund_cli.core.optimizers.efficient_frontier import EfficientFrontierCalculator

    calc = EfficientFrontierCalculator()
    result = calc.calculate(returns, n_points=points)

    console.print(f"\n[bold]有效前沿[/bold] ({result['n_points']}个点)")
    console.print(
        f"  收益范围: {min(result['frontier_returns']):.2%} ~ {max(result['frontier_returns']):.2%}"
    )
    console.print(
        f"  波动范围: {min(result['frontier_volatilities']):.2%} ~ {max(result['frontier_volatilities']):.2%}"
    )


@app.command("backtest")
def backtest(
    fund_codes: str = typer.Argument(..., help="基金代码，逗号分隔"),
    weights: str = typer.Option(None, help="权重，逗号分隔(如0.4,0.3,0.3)"),
    period: str = typer.Option("1y", help="分析周期"),
    rebalance: str = typer.Option("monthly", help="再平衡频率"),
):
    """组合回测 (PORTFOLIO-OPT-007)"""
    codes = [c.strip() for c in fund_codes.split(",")]
    returns = _get_returns(codes, period)
    if returns is None or returns.empty:
        console.print("[red]无法获取收益率数据[/red]")
        raise typer.Exit(1) from None

    w = None
    if weights:
        w_list = [float(x.strip()) for x in weights.split(",")]
        if len(w_list) == len(codes):
            w = dict(zip(codes, w_list, strict=False))

    from fund_cli.analysis.backtest import BacktestAnalyzer

    analyzer = BacktestAnalyzer()
    result = analyzer.run_backtest(returns, weights=w, rebalance_freq=rebalance)

    console.print("\n[bold]组合回测结果[/bold]")
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("指标", style="cyan")
    table.add_column("值", justify="right")
    table.add_row("累计收益率", f"{result['total_return']:.2f}%")
    table.add_row("年化收益率", f"{result['annual_return']:.2f}%")
    table.add_row("年化波动率", f"{result['annual_volatility']:.2f}%")
    table.add_row("夏普比率", f"{result['sharpe_ratio']:.4f}")
    table.add_row("最大回撤", f"{result['max_drawdown']:.2f}%")
    table.add_row("日胜率", f"{result['win_rate']:.1f}%")
    table.add_row("交易天数", str(result["trading_days"]))
    console.print(table)


def _print_result(result: dict) -> None:
    """打印优化结果"""
    console.print(f"  方法: {result['method']}")
    console.print(f"  预期收益: {result['expected_return']:.2%}")
    console.print(f"  预期波动: {result['volatility']:.2%}")
    console.print(f"  夏普比率: {result['sharpe_ratio']:.4f}")
    console.print("\n  [bold]权重分配:[/bold]")
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("基金代码", style="cyan")
    table.add_column("权重", justify="right")
    for code, weight in sorted(result["weights"].items(), key=lambda x: x[1], reverse=True):
        table.add_row(code, f"{weight:.2%}")
    console.print(table)
