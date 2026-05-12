"""
基金账户诊断命令（V3.5 新增）

提供完整的账户诊断功能，支持：
- 完整诊断报告（fund diagnose account）
- 组合净值曲线（fund diagnose nav）
- 资产穿透分析（fund diagnose lookthrough）
- 单只基金评价（fund diagnose evaluate）
- 配置偏离度（fund diagnose deviation）
"""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="基金账户诊断 - 组合分析、穿透诊断、调仓建议")
console = Console()


@app.command("account")
def diagnose_account(
    funds: Annotated[Optional[str], typer.Option("--funds", "-f", help="基金代码（逗号分隔）")] = None,
    weights: Annotated[Optional[str], typer.Option("--weights", "-w", help="权重（逗号分隔）")] = None,
    transactions: Annotated[Optional[str], typer.Option("--transactions", "-t", help="交易记录Excel文件路径")] = None,
    min_weight: Annotated[float, typer.Option("--min-weight", help="最小持仓权重百分比（默认0，即包含所有持仓）")] = 0.0,
    start: Annotated[Optional[str], typer.Option("--start", "-s", help="开始日期")] = None,
    end: Annotated[Optional[str], typer.Option("--end", "-e", help="结束日期")] = None,
    module: Annotated[Optional[str], typer.Option("--module", "-m", help="指定模块: performance/overview/allocation/correlation/evaluation/rebalance")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="输出文件路径")] = None,
) -> None:
    """
    完整账户诊断（一键生成报告）

    示例:
        fund diagnose account --funds 000001,000002 --weights 0.6,0.4
        fund diagnose account --transactions 交易记录.xlsx
        fund diagnose account --transactions 交易记录.xlsx --min-weight 1.0
        fund diagnose account --funds 000001,000002 --module performance
        fund diagnose account --funds 000001,000002 --output report.md
    """
    from fund_cli.analysis.portfolio_nav import PortfolioNavCalculator
    from fund_cli.analysis.risk import RiskAnalyzer
    from fund_cli.analysis.performance import PerformanceAnalyzer

    try:
        # 参数校验：--funds 和 --transactions 至少提供一个
        if not funds and not transactions:
            console.print("[red]请提供 --funds 或 --transactions 参数[/red]")
            raise typer.Exit(1) from None

        # 从交易记录解析持仓（优先使用）
        holdings_df = None
        if transactions:
            from fund_cli.analysis.holding_calculator import HoldingCalculator
            from fund_cli.data.transaction_parser import TransactionParser

            console.print(f"[cyan]正在解析交易记录: {transactions}[/cyan]")
            parser = TransactionParser()
            trans_df = parser.parse_excel(transactions)

            console.print(f"[cyan]正在计算持仓...[/cyan]")
            calc = HoldingCalculator()
            holdings_df = calc.calculate_holdings(trans_df, min_weight_pct=min_weight)

            fund_codes = holdings_df["fund_code"].tolist()
            weight_list = holdings_df["weight"].tolist()

            console.print(f"[green]解析完成: {len(fund_codes)} 只基金[/green]")
        else:
            fund_codes = [c.strip() for c in funds.split(",")]
            weight_list = [float(w.strip()) for w in weights.split(",")] if weights else [1.0 / len(fund_codes)] * len(fund_codes)

        if len(fund_codes) != len(weight_list):
            console.print("[red]基金数量与权重数量不匹配[/red]")
            raise typer.Exit(1) from None

        lines = ["# 基金账户诊断报告\n"]
        lines.append(f"## 持仓概览")
        lines.append(f"- 基金数量: {len(fund_codes)}")
        lines.append(f"- 基金代码: {', '.join(fund_codes)}")
        lines.append("")

        # 模块一：收益风险表现
        if module is None or module == "performance":
            lines.append("## 一、账户收益风险表现\n")
            try:
                calculator = PortfolioNavCalculator()
                portfolio_nav = calculator.compute_portfolio_nav(
                    fund_codes, weight_list,
                    start or "2024-01-01",
                    end or "2026-05-12",
                )
                comparisons = calculator.compare_with_benchmarks(portfolio_nav)
                attribution = calculator.attribution_analysis(portfolio_nav)

                lines.append(f"### 组合涨幅")
                lines.append(f"- {attribution['归因摘要']}")
                lines.append("")

                lines.append(f"### 指数对比")
                for name, data in comparisons.items():
                    lines.append(f"- {name}: {data['结论']}（超额 {data['超额收益']:.2%}）")
                lines.append("")

                # 回撤分析
                returns = calculator.compute_portfolio_returns(portfolio_nav)
                risk = RiskAnalyzer()
                dd_period = risk.max_drawdown_period(returns)
                lines.append(f"### 回撤分析")
                lines.append(f"- 最大回撤: {dd_period['max_drawdown']:.2%}")
                lines.append(f"- 回撤期间: {dd_period['peak_date']} ~ {dd_period['trough_date']}（{dd_period['duration_days']}天）")
                if dd_period['recovery_date']:
                    lines.append(f"- 恢复日期: {dd_period['recovery_date']}")
                lines.append("")
            except Exception as e:
                lines.append(f"*收益表现分析失败: {e}*\n")

        # 模块二：诊断总览
        if module is None or module == "overview":
            lines.append("## 二、账户诊断总览\n")
            try:
                from fund_cli.ai.portfolio_doctor import diagnose_portfolio
                from fund_cli.core.data_manager import get_data_manager

                dm = get_data_manager()
                diagnosis = diagnose_portfolio(fund_codes, weight_list, dm)

                lines.append(f"- 整体评分: {diagnosis.overall_score:.0f}/100")
                lines.append(f"- 健康等级: {diagnosis.overall_level.value}")
                for item in diagnosis.diagnoses[:5]:
                    lines.append(f"- {item.category.value}: {item.score:.0f}分 - {item.description}")
                lines.append("")
            except Exception as e:
                lines.append(f"*诊断总览分析失败: {e}*\n")

        # 模块三：配置诊断
        if module is None or module == "allocation":
            lines.append("## 三、组合配置诊断\n")
            try:
                from fund_cli.analysis.asset_lookthrough import AssetLookthroughAnalyzer
                from fund_cli.analysis.allocation_deviation import AllocationDeviationAnalyzer

                lookthrough = AssetLookthroughAnalyzer()
                values = dict(zip(fund_codes, weight_list))

                asset_alloc = lookthrough.asset_allocation_lookthrough(fund_codes, values)
                lines.append("### 大类资产穿透")
                for asset, ratio in asset_alloc.items():
                    if ratio > 0:
                        lines.append(f"- {asset}: {ratio:.2%}")
                lines.append("")

                country_alloc = lookthrough.country_lookthrough(fund_codes, values)
                lines.append("### 国家/地区分布")
                for region, ratio in country_alloc.items():
                    lines.append(f"- {region}: {ratio:.2%}")
                lines.append("")

                deviation_analyzer = AllocationDeviationAnalyzer()
                deviation = deviation_analyzer.compute_deviation(asset_alloc)
                lines.append(f"### 配置偏离度")
                lines.append(f"- 总偏离度: {deviation['总偏离度']:.2%}")
                lines.append(f"- 评价: {deviation['评价']}")
                lines.append("")
            except Exception as e:
                lines.append(f"*配置诊断分析失败: {e}*\n")

        # 模块四：相关性分析
        if module is None or module == "correlation":
            lines.append("## 四、相关性分析\n")
            try:
                from fund_cli.analysis.group_correlation import GroupCorrelationAnalyzer

                analyzer = GroupCorrelationAnalyzer()
                result = analyzer.analyze_groups(fund_codes)

                for group_name, group_data in result.get("分组分析结果", {}).items():
                    lines.append(f"### {group_name}")
                    lines.append(f"- 组内平均相关: {group_data['组内平均相关']:.4f}")
                    for pair in group_data.get("高相关对", []):
                        lines.append(f"- ⚠️ {pair['基金A']} ↔ {pair['基金B']}: {pair['相关系数']:.4f}")
                    lines.append(f"- 建议: {group_data['建议']}")
                    lines.append("")

                lines.append(f"### 总体建议")
                lines.append(f"- {result['总体建议']}")
                lines.append("")
            except Exception as e:
                lines.append(f"*相关性分析失败: {e}*\n")

        # 模块五：单基评价
        if module is None or module == "evaluation":
            lines.append("## 五、单只基金评价\n")
            try:
                from fund_cli.analysis.fund_evaluation import FundEvaluator

                evaluator = FundEvaluator()
                for code in fund_codes:
                    result = evaluator.evaluate(code)
                    lines.append(f"### {result['基金名称']}（{code}）")
                    lines.append(f"- 类型: {result['基金类型']} | 路径: {result['评价路径']}")
                    lines.append(f"- 综合得分: {result['综合得分']:.2f}")
                    lines.append(f"- 建议: {result['建议']}")
                    lines.append("")
            except Exception as e:
                lines.append(f"*单基评价失败: {e}*\n")

        # 模块六：调仓建议
        if module is None or module == "rebalance":
            lines.append("## 六、调仓建议\n")
            try:
                from fund_cli.analysis.rebalance_advisor import RebalanceAdvisor

                advisor = RebalanceAdvisor()
                plan = advisor.generate_rebalance_plan(fund_codes, weight_list)

                lines.append(f"### 当前配置")
                for asset, ratio in plan["当前配置"].items():
                    lines.append(f"- {asset}: {ratio:.2%}")
                lines.append("")

                if plan["减仓建议"]:
                    lines.append("### 减仓建议")
                    for item in plan["减仓建议"]:
                        lines.append(f"- {item['资产类别']}（超配{item['超配幅度']}）: {item['建议操作']}")
                    lines.append("")

                if plan["加仓建议"]:
                    lines.append("### 加仓建议")
                    for item in plan["加仓建议"]:
                        lines.append(f"- {item['资产类别']}（低配{item['低配幅度']}）: {item['建议操作']}")
                    lines.append("")

                lines.append(f"### 预期改善")
                lines.append(f"- {plan['预期改善']}")
                lines.append("")
            except Exception as e:
                lines.append(f"*调仓建议生成失败: {e}*\n")

        result = "\n".join(lines)
        console.print(Panel(result, title="基金账户诊断报告", border_style="green"))

        if output:
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]报告已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]诊断失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("evaluate")
def diagnose_evaluate(
    fund_code: str = typer.Argument(help="基金代码"),
) -> None:
    """
    单只基金评价

    示例:
        fund diagnose evaluate 000001
    """
    from fund_cli.analysis.fund_evaluation import FundEvaluator

    try:
        evaluator = FundEvaluator()
        result = evaluator.evaluate(fund_code)

        table = Table(title=f"基金评价 - {result['基金名称']}")
        table.add_column("项目", style="cyan")
        table.add_column("值", style="green")

        table.add_row("基金代码", result["基金代码"])
        table.add_row("基金类型", result["基金类型"])
        table.add_row("评价路径", result["评价路径"])
        table.add_row("综合得分", f"{result['综合得分']:.2%}")
        table.add_row("建议", result["建议"])

        if result["评价路径"] == "主动型":
            table.add_row("收益得分", f"{result['收益得分']:.2%}")
            table.add_row("风险得分", f"{result['风险得分']:.2%}")
            table.add_row("等级", result.get("等级", ""))
        else:
            table.add_row("超额收益", f"{result.get('超额收益', 0):.4f}")
            table.add_row("估值判断", result.get("估值判断", ""))

        console.print(table)

    except Exception as e:
        console.print(f"[red]评价失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("lookthrough")
def diagnose_lookthrough(
    funds: Annotated[str, typer.Option("--funds", "-f", help="基金代码（逗号分隔）")],
    weights: Annotated[Optional[str], typer.Option("--weights", "-w", help="权重（逗号分隔）")] = None,
    lookthrough_type: Annotated[str, typer.Option("--type", "-t", help="穿透类型: asset/country/industry/stock")] = "asset",
) -> None:
    """
    资产穿透分析

    示例:
        fund diagnose lookthrough --funds 000001,000002 --type asset
        fund diagnose lookthrough --funds 000001,000002 --type stock
    """
    from fund_cli.analysis.asset_lookthrough import AssetLookthroughAnalyzer

    try:
        fund_codes = [c.strip() for c in funds.split(",")]
        weight_list = [float(w.strip()) for w in weights.split(",")] if weights else [1.0 / len(fund_codes)] * len(fund_codes)
        values = dict(zip(fund_codes, weight_list))

        analyzer = AssetLookthroughAnalyzer()

        if lookthrough_type == "asset":
            result = analyzer.asset_allocation_lookthrough(fund_codes, values)
            title = "大类资产穿透"
        elif lookthrough_type == "country":
            result = analyzer.country_lookthrough(fund_codes, values)
            title = "国家/地区穿透"
        elif lookthrough_type == "industry":
            result = analyzer.domestic_industry_lookthrough(fund_codes, values)
            title = "行业穿透"
        elif lookthrough_type == "stock":
            result = analyzer.stock_lookthrough(fund_codes, values)
            title = "重仓股穿透"
        else:
            console.print(f"[red]未知穿透类型: {lookthrough_type}[/red]")
            raise typer.Exit(1) from None

        table = Table(title=title)
        table.add_column("项目", style="cyan")
        table.add_column("占比", style="green")

        if isinstance(result, dict):
            for key, val in sorted(result.items(), key=lambda x: x[1], reverse=True):
                if val > 0:
                    table.add_row(key, f"{val:.2%}")
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    name = item.get("股票名称", item.get("经理姓名", ""))
                    ratio = item.get("合并占比", item.get("合计占比", 0))
                    table.add_row(name, f"{ratio:.2%}")

        console.print(table)

    except Exception as e:
        console.print(f"[red]穿透分析失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("deviation")
def diagnose_deviation(
    funds: Annotated[str, typer.Option("--funds", "-f", help="基金代码（逗号分隔）")],
    weights: Annotated[Optional[str], typer.Option("--weights", "-w", help="权重（逗号分隔）")] = None,
    target: Annotated[Optional[str], typer.Option("--target", "-t", help="目标配置（如: 权益:0.7,固收:0.15,现金:0.15）")] = None,
) -> None:
    """
    配置偏离度分析

    示例:
        fund diagnose deviation --funds 000001,000002
        fund diagnose deviation --funds 000001,000002 --target "权益:0.7,固收:0.15,现金:0.15"
    """
    from fund_cli.analysis.allocation_deviation import AllocationDeviationAnalyzer
    from fund_cli.analysis.asset_lookthrough import AssetLookthroughAnalyzer

    try:
        fund_codes = [c.strip() for c in funds.split(",")]
        weight_list = [float(w.strip()) for w in weights.split(",")] if weights else [1.0 / len(fund_codes)] * len(fund_codes)
        values = dict(zip(fund_codes, weight_list))

        # 获取当前配置
        lookthrough = AssetLookthroughAnalyzer()
        current = lookthrough.asset_allocation_lookthrough(fund_codes, values)

        # 解析目标配置
        analyzer = AllocationDeviationAnalyzer()
        target_alloc = None
        if target:
            target_alloc = analyzer.parse_target_string(target)

        result = analyzer.compute_deviation(current, target_alloc)

        table = Table(title="配置偏离度分析")
        table.add_column("项目", style="cyan")
        table.add_column("值", style="green")

        table.add_row("总偏离度", f"{result['总偏离度']:.2%}")
        table.add_row("评价", result["评价"])
        table.add_row("", "")
        table.add_row("[bold]各资产偏离[/bold]", "")
        for asset, dev in result["各资产偏离"].items():
            sign = "+" if dev > 0 else ""
            table.add_row(f"  {asset}", f"{sign}{dev:.2%}")
        table.add_row("", "")
        table.add_row("建议", result["建议"])

        console.print(table)

    except Exception as e:
        console.print(f"[red]偏离度分析失败: {e}[/red]")
        raise typer.Exit(1) from None
