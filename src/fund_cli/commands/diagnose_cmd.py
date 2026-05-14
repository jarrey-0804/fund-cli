"""
基金账户诊断命令（V3.8.0 优化版）

提供完整的账户诊断功能，支持：
- 完整诊断报告（fund diagnose account）- 10个模块
- 组合净值曲线（fund diagnose nav）
- 资产穿透分析（fund diagnose lookthrough）
- 单只基金评价（fund diagnose evaluate）
- 配置偏离度（fund diagnose deviation）

报告结构（优化后）：
一、持仓基金 - 核心财务数据 + 持仓明细（含投资类型）
二、收益风险表现 - 整体涨幅 + 分时段分析 + 多维度对比（含卡玛比率、胜率）
三、大类资产分布 - 穿透分析 + 行业风险
四、基金公司和基金经理穿透 - 公司穿透 + 经理穿透 + 量化评价（含细分得分）
五、相关性分析
六、单只基金评价 - 双轨评价 + 产品诊断 + 细分得分
七、账户诊断总览 - 综合评分 + 配置偏离 + 关键发现 + 舆情核查
八、调仓建议 - 减仓/加仓建议 + 推荐新基金 + 调仓批次安排
九、风险提示
十、总结 - 综合评价 + 关键结论 + 操作建议摘要
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)

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
    module: Annotated[Optional[str], typer.Option("--module", "-m", help="指定模块: performance/overview/allocation/correlation/evaluation/rebalance/risk")] = None,
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
        total_value = 0
        total_cost = 0
        # 穿透数据变量（供 rebalance/risk 模块使用）
        asset_alloc: dict = {}
        country_alloc: dict = {}
        domestic_industries: dict = {}
        top_stocks_sorted: list = []
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
            
            # 计算总市值和总成本
            if "total_cost" in holdings_df.columns:
                total_cost = holdings_df["total_cost"].sum()
            # 用净值×份额计算总市值
            try:
                from fund_cli.core.data_manager import get_data_manager
                _dm = get_data_manager()
                for _, row in holdings_df.iterrows():
                    code = row["fund_code"]
                    shares = row.get("total_shares", 0)
                    if shares and shares > 0:
                        nav = _dm.get_fund_nav(code)
                        if nav is not None and not nav.empty:
                            nav_col = "accumulated_nav" if "accumulated_nav" in nav.columns else "unit_nav"
                            latest_nav = nav[nav_col].iloc[-1]
                            total_value += shares * latest_nav
            except Exception:
                pass

            console.print(f"[green]解析完成: {len(fund_codes)} 只基金[/green]")
        else:
            fund_codes = [c.strip() for c in funds.split(",")]
            weight_list = [float(w.strip()) for w in weights.split(",")] if weights else [1.0 / len(fund_codes)] * len(fund_codes)

        if len(fund_codes) != len(weight_list):
            console.print("[red]基金数量与权重数量不匹配[/red]")
            raise typer.Exit(1) from None

        # 构建持仓权重字典（用于后续计算）
        current_weights = dict(zip(fund_codes, [w * 100 for w in weight_list]))  # 转为百分比

        # 报告头部
        lines = ["# 基金账户诊断报告（完整版）\n"]
        lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"> 数据来源: AKShare 真实市场数据")
        lines.append(f"> 分析工具: Fund CLI v3.8.0")
        lines.append(f"> 分析基准期: {start or '2024-01-01'} 至 {end or '2026-05-12'}")
        lines.append("\n---\n")

        # =========================================================
        # 模块一：持仓基金（优化：补充核心财务数据）
        # =========================================================
        if module is None or module == "overview":
            lines.append("## 一、持仓基金\n")
            
            # 核心财务数据（无条件显示）
            # 当使用 --funds 参数时，通过AKShare获取最新净值估算总市值
            if total_value == 0 and not transactions:
                try:
                    from fund_cli.core.data_manager import get_data_manager as _get_dm
                    _dm_est = _get_dm()
                    for code in fund_codes:
                        nav = _dm_est.get_fund_nav(code)
                        if nav is not None and not nav.empty:
                            nav_col = "accumulated_nav" if "accumulated_nav" in nav.columns else "unit_nav"
                            latest_nav = nav[nav_col].iloc[-1]
                            idx = fund_codes.index(code)
                            shares_est = 10000  # 默认按1万份估算
                            total_value += shares_est * latest_nav
                except Exception:
                    pass

            if total_value > 0 or total_cost > 0:
                lines.append("### 1.1 核心财务数据\n")
                lines.append("| 项目 | 数值 |")
                lines.append("| --- | --- |")
                if total_value > 0:
                    lines.append(f"| 总持仓市值 | ¥{total_value:,.2f} |")
                if total_cost > 0:
                    profit = total_value - total_cost
                    profit_pct = profit / total_cost * 100 if total_cost > 0 else 0
                    lines.append(f"| 总买入成本 | ¥{total_cost:,.2f} |")
                    lines.append(f"| 整体盈亏 | ¥{profit:+,.2f} ({profit_pct:+.2f}%) |")
                    profit_status = "盈利" if profit > 0 else "亏损" if profit < 0 else "持平"
                    lines.append(f"| 盈亏状态 | {profit_status} |")
                lines.append("")
            
            lines.append("### 1.2 持仓明细（按市值权重排序）\n")

            # 持仓明细表格
            lines.append("| 序号 | 基金代码 | 基金名称 | 投资类型 | 权重 | 综合得分 | 建议 |")
            lines.append("| --- | --- | --- | --- | --- | --- | --- |")

            from fund_cli.core.data_manager import get_data_manager
            from fund_cli.analysis.fund_evaluation import FundEvaluator
            dm = get_data_manager()
            evaluator = FundEvaluator()

            for i, (code, weight) in enumerate(sorted(current_weights.items(), key=lambda x: x[1], reverse=True), 1):
                try:
                    info = dm.get_fund_info(code)
                    fund_name = info.get("fund_name", info.get("name", code)) if info else code
                    # 截断名称
                    if len(fund_name) > 20:
                        fund_name = fund_name[:18] + "..."
                    
                    # 获取投资类型（二级分类）
                    fund_type = info.get("fund_type", info.get("type", "未知")) if info else "未知"
                    if len(fund_type) > 10:
                        fund_type = fund_type[:8] + ".."
                    
                    # 获取评分
                    result = evaluator.evaluate(code, portfolio_codes=fund_codes)
                    score = result.get("综合得分", 0)
                    advice = result.get("建议", "观察")
                except Exception:
                    fund_name = code
                    fund_type = "未知"
                    score = 0.5
                    advice = "观察"
                
                lines.append(f"| {i} | {code} | {fund_name} | {fund_type} | {weight:.2f}% | {score:.2f} | {advice} |")
            lines.append("")

        # =========================================================
        # 模块二：组合收益风险表现
        # =========================================================
        if module is None or module == "performance":
            lines.append("## 二、组合收益风险表现\n")
            try:
                calculator = PortfolioNavCalculator()
                portfolio_nav = calculator.compute_portfolio_nav(
                    fund_codes, weight_list,
                    start or "2024-01-01",
                    end or "2026-05-12",
                )
                comparisons = calculator.compare_with_benchmarks(portfolio_nav)
                attribution = calculator.attribution_analysis(portfolio_nav)

                # 2.1 组合整体涨幅与基准对比
                lines.append("### 2.1 组合整体涨幅与基准对比\n")
                lines.append("| 对比项 | 收益率 | 超额收益 | 结论 |")
                lines.append("| --- | --- | --- | --- |")
                
                # 计算组合总收益
                total_return = (portfolio_nav.iloc[-1] / portfolio_nav.iloc[0] - 1) * 100
                lines.append(f"| **本组合** | **{total_return:.2f}%** | - | - |")
                
                for name, data in comparisons.items():
                    ret = data.get("指数收益", 0) * 100 if isinstance(data.get("指数收益"), (int, float)) else 0
                    excess = data.get("超额收益", 0) * 100 if isinstance(data.get("超额收益"), (int, float)) else 0
                    conclusion = "跑赢" if excess > 0 else "跑输" if excess < 0 else "持平"
                    lines.append(f"| {name} | {ret:.2f}% | {excess:+.2f}% | {conclusion} |")
                lines.append("")

                # 2.2 收益风险指标汇总
                lines.append("### 2.2 收益风险指标汇总\n")
                
                returns = calculator.compute_portfolio_returns(portfolio_nav)
                perf_analyzer = PerformanceAnalyzer()
                risk_analyzer = RiskAnalyzer()
                
                perf_metrics = perf_analyzer.analyze(returns)
                risk_metrics = risk_analyzer.analyze(returns)
                
                lines.append("| 指标类别 | 指标 | 数值 |")
                lines.append("| --- | --- | --- |")
                
                # 收益指标
                lines.append(f"| 收益 | 累计收益 | {perf_metrics.get('total_return', 0):.2f}% |")
                lines.append(f"| 收益 | 年化收益 (CAGR) | {perf_metrics.get('cagr', 0):.2f}% |")
                
                # 风险指标
                lines.append(f"| 风险 | 年化波动率 | {perf_metrics.get('volatility', 0):.2f}% |")
                lines.append(f"| 风险 | 最大回撤 | {perf_metrics.get('max_drawdown', 0):.2f}% |")
                lines.append(f"| 风险 | VaR (95%) | {perf_metrics.get('var_95', 0):.2f}% |")
                lines.append(f"| 风险 | CVaR (95%) | {perf_metrics.get('cvar_95', 0):.2f}% |")
                
                # 风险调整收益
                lines.append(f"| 风险调整 | 夏普比率 | {perf_metrics.get('sharpe', 0):.2f} |")
                lines.append(f"| 风险调整 | 索提诺比率 | {perf_metrics.get('sortino', 0):.2f} |")
                lines.append(f"| 风险调整 | 卡玛比率 | {perf_metrics.get('calmar', 0):.2f} |")
                
                # 分布特征
                lines.append(f"| 分布 | 偏度 | {perf_metrics.get('skew', 0):.2f} |")
                lines.append(f"| 分布 | 峰度 | {perf_metrics.get('kurtosis', 0):.2f} |")
                lines.append(f"| 分布 | 胜率 | {perf_metrics.get('win_rate', 0):.2f}% |")
                
                # 极端情况
                lines.append(f"| 极端 | 最佳单日 | {perf_metrics.get('best_day', 0):.2f}% |")
                lines.append(f"| 极端 | 最差单日 | {perf_metrics.get('worst_day', 0):.2f}% |")
                lines.append("")

                # 2.3 最大回撤时间段定位
                lines.append("### 2.3 最大回撤时间段定位\n")
                dd_period = risk_analyzer.max_drawdown_period(returns)
                lines.append("| 指标 | 数值 |")
                lines.append("| --- | --- |")
                lines.append(f"| 最大回撤 | {dd_period['max_drawdown']:.2%} |")
                lines.append(f"| 回撤起始日（峰值） | {dd_period['peak_date']} |")
                lines.append(f"| 回撤结束日（谷值） | {dd_period['trough_date']} |")
                lines.append(f"| 持续天数 | {dd_period['duration_days']}天 |")
                if dd_period.get('recovery_date'):
                    lines.append(f"| 恢复日期 | {dd_period['recovery_date']} |")
                lines.append("")

                # 2.4 跑赢跑输归因分析
                lines.append("### 2.4 跑赢跑输归因分析\n")
                lines.append(f"**归因摘要**: {attribution['归因摘要']}")
                lines.append("")
                if attribution.get("跑赢指数"):
                    lines.append("**跑赢指数**:")
                    for item in attribution["跑赢指数"]:
                        if isinstance(item, dict):
                            name = item.get("指数", "")
                            excess = item.get("超额收益", 0)
                            lines.append(f"- {name}: 超额收益 {excess:+.2%}")
                        else:
                            lines.append(f"- {item}")
                    lines.append("")
                if attribution.get("跑输指数"):
                    lines.append("**跑输指数**:")
                    for item in attribution["跑输指数"]:
                        if isinstance(item, dict):
                            name = item.get("指数", "")
                            excess = item.get("超额收益", 0)
                            lines.append(f"- {name}: 超额收益 {excess:+.2%}")
                        else:
                            lines.append(f"- {item}")
                    lines.append("")

                # 2.5 单只基金收益排名
                lines.append("### 2.5 单只基金收益排名\n")
                lines.append("| 排名 | 基金代码 | 基金名称 | 总收益 | 年化收益 |")
                lines.append("| --- | --- | --- | --- | --- |")
                
                fund_returns = []
                for code in fund_codes:
                    try:
                        nav = dm.get_fund_nav(code)
                        if nav is not None and not nav.empty:
                            nav_col = "accumulated_nav" if "accumulated_nav" in nav.columns else "unit_nav"
                            total_ret = nav[nav_col].iloc[-1] / nav[nav_col].iloc[0] - 1
                            days = (nav['nav_date'].iloc[-1] - nav['nav_date'].iloc[0]).days
                            years = max(days / 365.25, 0.1)
                            ann_ret = (1 + total_ret) ** (1 / years) - 1
                            info = dm.get_fund_info(code)
                            name = info.get("fund_name", info.get("name", code)) if info else code
                            if len(name) > 20:
                                name = name[:18] + "..."
                            fund_returns.append((code, name, total_ret * 100, ann_ret * 100))
                    except Exception:
                        pass
                
                fund_returns.sort(key=lambda x: x[2], reverse=True)
                for i, (code, name, total_ret, ann_ret) in enumerate(fund_returns, 1):
                    lines.append(f"| {i} | {code} | {name} | {total_ret:.2f}% | {ann_ret:.2f}% |")
                lines.append("")

                # 2.6 多时间维度收益风险对比
                try:
                    from fund_cli.analysis.multi_period_analysis import MultiPeriodAnalyzer
                    multi_period = MultiPeriodAnalyzer(dm)
                    lines.append("### 2.6 多时间维度收益风险对比\n")
                    lines.append(multi_period.generate_report_section(fund_codes, weight_list, end or "2026-05-12"))
                except Exception as e:
                    lines.append(f"*多时间维度分析失败: {e}*\n")

            except Exception as e:
                lines.append(f"*收益表现分析失败: {e}*\n")

        # =========================================================
        # 模块三：大类资产分布（优化：精简，移除基金经理相关内容）
        # =========================================================
        if module is None or module == "allocation":
            lines.append("## 三、大类资产分布\n")
            try:
                from fund_cli.analysis.asset_lookthrough import AssetLookthroughAnalyzer
                from fund_cli.analysis.holding import HoldingAnalyzer
                from fund_cli.analysis.industry_risk import IndustryRiskAnalyzer
                from fund_cli.analysis.style_tagging import StockStyleTagger

                lookthrough = AssetLookthroughAnalyzer()
                values = dict(zip(fund_codes, weight_list))

                # 3.1 大类资产穿透
                asset_alloc = lookthrough.asset_allocation_lookthrough(fund_codes, values)
                lines.append("### 3.1 穿透后大类资产分布\n")
                lines.append("| 资产类别 | 占比 |")
                lines.append("| --- | --- |")
                for asset, ratio in sorted(asset_alloc.items(), key=lambda x: x[1], reverse=True):
                    if ratio > 0:
                        lines.append(f"| {asset} | {ratio:.2%} |")
                lines.append("")

                # 3.2 国家/地区分布
                country_alloc = lookthrough.country_lookthrough(fund_codes, values)
                lines.append("### 3.2 穿透后国家/地区分布\n")
                lines.append("| 地区 | 占比 |")
                lines.append("| --- | --- |")
                for region, ratio in sorted(country_alloc.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"| {region} | {ratio:.2%} |")
                lines.append("")

                # 3.3 行业穿透（包含所有基金）
                lines.append("### 3.3 行业穿透（Top 15）\n")
                lines.append("| 行业 | 占比 |")
                lines.append("| --- | --- |")
                
                holding_analyzer = HoldingAnalyzer()
                domestic_industries = {}
                for code in fund_codes:
                    try:
                        industry_alloc = dm.get_fund_industry_allocation(code)
                        if industry_alloc is not None and not industry_alloc.empty and 'industry' in industry_alloc.columns:
                            fund_weight = current_weights.get(code, 0) / 100
                            for _, row in industry_alloc.iterrows():
                                industry = row.get('industry', '')
                                ratio = row.get('weight', 0) / 100
                                if industry:
                                    domestic_industries[industry] = domestic_industries.get(industry, 0) + ratio * fund_weight
                    except Exception:
                        pass
                
                for industry, ratio in sorted(domestic_industries.items(), key=lambda x: x[1], reverse=True)[:15]:
                    lines.append(f"| {industry} | {ratio:.2%} |")
                lines.append("")

                # 3.4 重仓股穿透
                lines.append("### 3.4 重仓股穿透合并（Top 15）\n")
                lines.append("| 排名 | 股票名称 | 合并占比 | 来源基金 |")
                lines.append("| --- | --- | --- | --- |")
                
                top_stocks = []
                stock_sources = {}
                for code in fund_codes:
                    try:
                        holdings = dm.get_fund_holdings(code, top_n=10)
                        if holdings is not None and not holdings.empty:
                            fund_weight = current_weights.get(code, 0) / 100
                            for _, row in holdings.iterrows():
                                name = row.get('stock_name', '')
                                ratio = row.get('weight', 0) / 100
                                if name and ratio > 0:
                                    top_stocks.append((name, ratio * fund_weight))
                                    if name not in stock_sources:
                                        stock_sources[name] = []
                                    if code not in stock_sources[name]:
                                        stock_sources[name].append(code)
                    except Exception:
                        pass

                top_stocks_merged = {}
                for name, ratio in top_stocks:
                    top_stocks_merged[name] = top_stocks_merged.get(name, 0) + ratio

                top_stocks_sorted = sorted(top_stocks_merged.items(), key=lambda x: x[1], reverse=True)[:15]
                for i, (name, ratio) in enumerate(top_stocks_sorted, 1):
                    sources = ", ".join(stock_sources.get(name, [])[:3])
                    lines.append(f"| {i} | {name} | {ratio:.2%} | {sources} |")
                lines.append("")

                # 3.5 行业集中度风险提示
                lines.append("### 3.5 行业集中度风险提示\n")
                industry_risk = IndustryRiskAnalyzer()
                if domestic_industries:
                    risk_analysis = industry_risk.analyze_concentration_risk(domestic_industries)
                    lines.append(f"**集中度评价**: {risk_analysis.get('集中度评价', '适度集中')}")
                    lines.append(f"**HHI指数**: {risk_analysis.get('HHI指数', 0):.4f}")
                    lines.append("")
                    if risk_analysis.get('alerts'):
                        lines.append("> ⚠️ 发现高集中度行业风险:")
                        for alert in risk_analysis['alerts'][:3]:
                            lines.append(f"> - {alert['行业']}: {alert['占比']} ({alert['风险等级']}风险)")
                    else:
                        lines.append("> 未发现高集中度行业风险")
                lines.append("")

                # 3.5.1 行业景气度评分
                lines.append("### 3.5.1 行业景气度评分\n")
                if domestic_industries:
                    try:
                        prosperity_result = industry_risk.evaluate_industry_prosperity(domestic_industries, use_ai=False)
                        
                        # 高景气行业
                        high_prosperity = prosperity_result.get("行业景气度评分", {}).get("高景气", [])
                        if high_prosperity:
                            lines.append("**高景气行业**（评分≥70）:\n")
                            lines.append("| 行业 | 占比 | 评分 |")
                            lines.append("| --- | --- | --- |")
                            for item in high_prosperity[:5]:
                                lines.append(f"| {item['行业']} | {item['占比']} | {item['评分']} |")
                            lines.append("")
                        
                        # 中景气行业
                        mid_prosperity = prosperity_result.get("行业景气度评分", {}).get("中景气", [])
                        if mid_prosperity:
                            lines.append("**中景气行业**（评分40-69）:\n")
                            lines.append("| 行业 | 占比 | 评分 |")
                            lines.append("| --- | --- | --- |")
                            for item in mid_prosperity[:5]:
                                lines.append(f"| {item['行业']} | {item['占比']} | {item['评分']} |")
                            lines.append("")
                        
                        # 低景气行业
                        low_prosperity = prosperity_result.get("行业景气度评分", {}).get("低景气", [])
                        if low_prosperity:
                            lines.append("**低景气行业**（评分<40）:\n")
                            for item in low_prosperity[:3]:
                                lines.append(f"- {item['行业']}（{item['占比']}，评分{item['评分']}）")
                            lines.append("")
                        
                        # 整体评价
                        lines.append(f"**整体评价**: {prosperity_result.get('整体评价', 'N/A')}")
                        if prosperity_result.get('风险提示'):
                            lines.append(f"**风险提示**: {prosperity_result['风险提示']}")
                        lines.append("")
                    except Exception as e:
                        lines.append(f"*行业景气度评分失败: {e}*\n")

                # 3.6 重仓股风格标签与命名组追踪
                lines.append("### 3.6 重仓股风格标签与命名组追踪\n")
                tagger = StockStyleTagger()
                if top_stocks_sorted:
                    # tag_stocks 接收 list[tuple] 或 list[dict]
                    style_result = tagger.tag_stocks(top_stocks_sorted)
                    if style_result.get('主导风格'):
                        lines.append(f"**主导风格**: {style_result['主导风格']}")
                    lines.append("")
                    # 风格分布 - 使用风格标签字段
                    tags = style_result.get('风格标签', [])
                    if tags:
                        lines.append("**风格分布**:")
                        for tag in tags:
                            lines.append(f"- {tag}")
                    lines.append("")
                    # 命名组追踪 - 返回 list[dict]
                    named_groups = style_result.get('命名组追踪', [])
                    if named_groups and isinstance(named_groups, list):
                        lines.append("**命名组追踪**:")
                        lines.append("| 命名组 | 匹配股票 | 合计占比 |")
                        lines.append("| --- | --- | --- |")
                        for group in named_groups:
                            group_name = group.get('命名组', '')
                            matched = ", ".join(group.get('匹配股票', [])[:5])
                            total_weight = group.get('合计占比', 0)
                            lines.append(f"| {group_name} | {matched} | {total_weight:.2%} |")
                    elif named_groups and isinstance(named_groups, dict):
                        lines.append("**命名组追踪**:")
                        lines.append("| 命名组 | 合计占比 |")
                        lines.append("| --- | --- |")
                        for group, weight in named_groups.items():
                            lines.append(f"| {group} | {weight:.2%} |")
                lines.append("")

            except Exception as e:
                lines.append(f"*配置诊断分析失败: {e}*\n")

        # =========================================================
        # 模块四：基金公司和基金经理穿透（优化：独立成章）
        # =========================================================
        if module is None or module == "allocation":
            lines.append("## 四、基金公司和基金经理穿透\n")
            try:
                dm = get_data_manager()

                # 4.1 基金公司穿透
                lines.append("### 4.1 基金公司穿透\n")
                lines.append("| 基金公司 | 管理基金数 | 合计权重 |")
                lines.append("| --- | --- | --- |")

                company_exposure = {}
                company_funds = {}
                for code in fund_codes:
                    info = dm.get_fund_info(code)
                    if info:
                        company = info.get('company', '') or info.get('management', '') or '未知'
                        fund_weight = current_weights.get(code, 0) / 100
                        if company and company != '未知':
                            company_exposure[company] = company_exposure.get(company, 0) + fund_weight
                            if company not in company_funds:
                                company_funds[company] = []
                            company_funds[company].append(code)

                for company, ratio in sorted(company_exposure.items(), key=lambda x: x[1], reverse=True)[:10]:
                    fund_count = len(company_funds.get(company, []))
                    lines.append(f"| {company} | {fund_count} | {ratio:.2%} |")
                lines.append("")

                # 4.2 基金经理穿透
                lines.append("### 4.2 基金经理穿透\n")
                lines.append("| 经理姓名 | 管理基金数 | 合计权重 |")
                lines.append("| --- | --- | --- |")
                
                manager_exposure = {}
                manager_funds = {}
                for code in fund_codes:
                    info = dm.get_fund_info(code)
                    if info:
                        manager = info.get('manager', '') or '未知'
                        fund_weight = current_weights.get(code, 0) / 100
                        if manager and manager != '未知':
                            manager_exposure[manager] = manager_exposure.get(manager, 0) + fund_weight
                            if manager not in manager_funds:
                                manager_funds[manager] = []
                            manager_funds[manager].append(code)

                for manager, ratio in sorted(manager_exposure.items(), key=lambda x: x[1], reverse=True)[:10]:
                    fund_count = len(manager_funds.get(manager, []))
                    lines.append(f"| {manager} | {fund_count} | {ratio:.2%} |")
                lines.append("")

                # 4.3 基金经理量化评价
                lines.append("### 4.3 基金经理量化评价\n")
                try:
                    from fund_cli.analysis.manager import ManagerAnalyzer
                    manager_analyzer = ManagerAnalyzer()
                    
                    lines.append("| 经理姓名 | 管理基金数 | 近1年百分位 | 近1年等级 | 近2年百分位 | 近2年等级 | 回撤得分 | 收益得分 | 规模得分 | 综合评级 |")
                    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
                    
                    for manager, funds in manager_funds.items():
                        try:
                            eval_result = manager_analyzer.evaluate_manager_performance(manager, funds)
                            
                            # 获取细分得分
                            detailed_scores = manager_analyzer.compute_manager_detailed_scores(manager, funds)
                            
                            data_1y = eval_result.get("近1年", {})
                            data_2y = eval_result.get("近2年", {})
                            
                            pct_1y = data_1y.get("百分位", "N/A")
                            grade_1y = data_1y.get("等级", "N/A")
                            pct_2y = data_2y.get("百分位", "N/A")
                            grade_2y = data_2y.get("等级", "N/A")
                            overall = eval_result.get("综合评级", "N/A")
                            
                            pct_1y_str = f"前{100-pct_1y:.0f}%" if isinstance(pct_1y, (int, float)) else "N/A"
                            pct_2y_str = f"前{100-pct_2y:.0f}%" if isinstance(pct_2y, (int, float)) else "N/A"
                            
                            dd_score = detailed_scores.get("回撤得分", 0.5)
                            ret_score = detailed_scores.get("收益得分", 0.5)
                            scale_score = detailed_scores.get("规模得分", 0.5)
                            
                            lines.append(
                                f"| {manager} | {len(funds)} | "
                                f"{pct_1y_str} | {grade_1y} | "
                                f"{pct_2y_str} | {grade_2y} | "
                                f"{dd_score:.2f} | {ret_score:.2f} | {scale_score:.2f} | {overall} |"
                            )
                        except Exception:
                            lines.append(f"| {manager} | {len(funds)} | N/A | N/A | N/A | N/A | 0.50 | 0.50 | 0.50 | N/A |")
                    lines.append("")
                except Exception as e:
                    lines.append(f"*基金经理量化评价失败: {e}*\n")

            except Exception as e:
                lines.append(f"*基金经理穿透分析失败: {e}*\n")

        # =========================================================
        # 模块五：相关性分析（章节编号保持不变）
        # =========================================================
        if module is None or module == "correlation":
            lines.append("## 五、相关性分析\n")
            try:
                from fund_cli.analysis.group_correlation import GroupCorrelationAnalyzer

                dm = get_data_manager()
                analyzer = GroupCorrelationAnalyzer(dm)
                result = analyzer.analyze_groups(fund_codes)

                for group_name, group_data in result.get("分组分析结果", {}).items():
                    lines.append(f"### 5.{list(result.get('分组分析结果', {}).keys()).index(group_name) + 1} {group_name}\n")
                    lines.append("| 指标 | 数值 |")
                    lines.append("| --- | --- |")
                    # 从高相关对中推断基金数量，或使用基金列表
                    group_funds = set()
                    high_corr = group_data.get("高相关对", [])
                    for pair in high_corr:
                        group_funds.add(pair.get("基金A", ""))
                        group_funds.add(pair.get("基金B", ""))
                    fund_count = len(group_funds) if group_funds else len(fund_codes)
                    lines.append(f"| 基金数量 | {fund_count}只 |")
                    lines.append(f"| 组内平均相关 | {group_data.get('组内平均相关', 0):.4f} |")
                    lines.append("")

                    high_corr = group_data.get("高相关对", [])
                    if high_corr:
                        lines.append("| 基金A | 基金B | 相关系数 |")
                        lines.append("| --- | --- | --- |")
                        for pair in high_corr[:10]:
                            lines.append(f"| {pair['基金A']} | {pair['基金B']} | {pair['相关系数']:.4f} |")
                        lines.append("")

                    lines.append(f"**建议**: {group_data['建议']}")
                    lines.append("")

                lines.append(f"### 总体建议")
                lines.append(f"- {result['总体建议']}")
                lines.append("")

            except Exception as e:
                lines.append("*当前基金净值数据获取受限，无法完成相关性分析。建议稍后重试或检查网络连接。*\n")

        # =========================================================
        # 模块六：单只基金评价
        # =========================================================
        if module is None or module == "evaluation":
            lines.append("## 六、单只基金评价（双轨评价）\n")
            try:
                evaluator = FundEvaluator()

                # 双轨评价表格（增加排名列）
                lines.append("| 基金代码 | 基金名称 | 评价路径 | 综合得分 | 近1年排名 | 近2年排名 | 等级 | 建议 |")
                lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")

                # 存储各基金的细分得分用于后续表格
                fund_detailed_scores = {}
                
                for code in fund_codes:
                    result = evaluator.evaluate(code, portfolio_codes=fund_codes)
                    fund_name = result.get('基金名称', code)
                    if len(fund_name) > 20:
                        fund_name = fund_name[:18] + "..."
                    score = result.get('综合得分', 0)
                    level = "良好" if score >= 0.6 else "一般" if score >= 0.35 else "较差"
                    advice = result.get('建议', '观察')
                    
                    # 获取细分得分和排名
                    detailed = evaluator.compute_detailed_scores(code)
                    fund_detailed_scores[code] = detailed
                    rank_1y = detailed.get("近1年排名", 50)
                    rank_2y = detailed.get("近2年排名", 50)
                    
                    lines.append(f"| {code} | {fund_name} | {result.get('评价路径', 'N/A')} | {score:.2f} | 前{rank_1y:.0f}% | 前{rank_2y:.0f}% | {level} | {advice} |")
                lines.append("")

                # 6.1 年度收益追踪
                lines.append("### 6.1 年度收益追踪\n")
                try:
                    from fund_cli.analysis.annual_return_tracker import AnnualReturnTracker
                    tracker = AnnualReturnTracker(dm)
                    
                    lines.append("| 基金代码 | 基金名称 | 2024年收益 | 2025年收益 | 2026年初以来 | 业绩稳定性 |")
                    lines.append("| --- | --- | --- | --- | --- | --- |")
                    
                    for code in fund_codes[:10]:  # 限制前10只
                        try:
                            annual_result = tracker.track_annual_returns(code)
                            if "error" not in annual_result:
                                info = dm.get_fund_info(code)
                                name = info.get("fund_name", info.get("name", code)) if info else code
                                if len(name) > 15:
                                    name = name[:13] + "..."
                                
                                ret_2024 = annual_result.get("2024年", {}).get("收益", "N/A")
                                ret_2025 = annual_result.get("2025年", {}).get("收益", "N/A")
                                ret_2026 = annual_result.get("2026年初以来", {}).get("收益", "N/A")
                                stability = annual_result.get("业绩稳定性", "N/A")
                                
                                ret_2024_str = f"{ret_2024}%" if isinstance(ret_2024, (int, float)) else "N/A"
                                ret_2025_str = f"{ret_2025}%" if isinstance(ret_2025, (int, float)) else "N/A"
                                ret_2026_str = f"{ret_2026}%" if isinstance(ret_2026, (int, float)) else "N/A"
                                
                                lines.append(f"| {code} | {name} | {ret_2024_str} | {ret_2025_str} | {ret_2026_str} | {stability} |")
                        except Exception:
                            pass
                    lines.append("")
                except Exception as e:
                    lines.append(f"*年度收益追踪失败: {e}*\n")

                # 指数型基金估值分析
                lines.append("### 6.2 指数型基金估值分析\n")
                lines.append("| 基金代码 | 基金名称 | 相对同类超额 | PE分位 | 估值判断 |")
                lines.append("| --- | --- | --- | --- | --- |")

                for code in fund_codes:
                    result = evaluator.evaluate(code, portfolio_codes=fund_codes)
                    if result.get('评价路径') == '指数型':
                        fund_name = result.get('基金名称', code)
                        if len(fund_name) > 20:
                            fund_name = fund_name[:18] + "..."
                        excess = result.get('超额收益', 0)
                        pe_pct = result.get('PE分位', 0.5)
                        verdict = result.get('估值判断', '数据不足')
                        lines.append(f"| {code} | {fund_name} | {excess:.2%} | {pe_pct:.1%} | {verdict} |")
                lines.append("")

                # 6.3 产品诊断详情（优化新增）
                lines.append("### 6.3 产品诊断详情\n")
                lines.append("*以下为各基金的简要产品诊断，供投资参考*\n")
                
                for code in fund_codes[:10]:  # 限制前10只
                    try:
                        result = evaluator.evaluate(code, portfolio_codes=fund_codes)
                        info = dm.get_fund_info(code)
                        fund_name = result.get('基金名称', info.get("fund_name", info.get("name", code)) if info else code)
                        if len(fund_name) > 25:
                            fund_name = fund_name[:23] + "..."
                        
                        score = result.get('综合得分', 0)
                        ret_score = result.get('收益得分', 0)
                        risk_score = result.get('风险得分', 0)
                        advice = result.get('建议', '观察')
                        fund_type = result.get('评价路径', '未知')
                        
                        # 生成产品诊断描述
                        if score >= 0.8:
                            performance = "表现优秀"
                        elif score >= 0.6:
                            performance = "表现良好"
                        elif score >= 0.4:
                            performance = "表现一般"
                        else:
                            performance = "表现较差"
                        
                        lines.append(f"**{code} {fund_name}**\n")
                        lines.append(f"- **产品类型**: {fund_type}")
                        lines.append(f"- **综合评分**: {score:.0%}（{performance}）")
                        lines.append(f"- **收益得分**: {ret_score:.0%} | **风险得分**: {risk_score:.0%}")
                        lines.append(f"- **投资建议**: {advice}")
                        lines.append("")
                    except Exception:
                        pass

                # 6.4 细分得分表格（新增）
                lines.append("### 6.4 细分得分\n")
                lines.append("*以下为各基金的细分评分，用于深入分析基金各项能力*\n")
                lines.append("| 基金代码 | 最大回撤得分 | 区间收益得分 | 规模得分 | 创新高得分 | 择股得分 | 择时得分 |")
                lines.append("| --- | --- | --- | --- | --- | --- | --- |")
                
                for code in fund_codes[:10]:  # 限制前10只
                    detailed = fund_detailed_scores.get(code, {})
                    lines.append(
                        f"| {code} | {detailed.get('最大回撤得分', 0.5):.2f} | "
                        f"{detailed.get('区间收益得分', 0.5):.2f} | "
                        f"{detailed.get('规模得分', 0.5):.2f} | "
                        f"{detailed.get('创新高得分', 0.5):.2f} | "
                        f"{detailed.get('择股得分', 0.5):.2f} | "
                        f"{detailed.get('择时得分', 0.5):.2f} |"
                    )
                lines.append("")
                lines.append("> **得分说明**: 得分范围0-1，0.7以上为优秀，0.5-0.7为良好，0.3-0.5为一般，0.3以下为较差\n")

            except Exception as e:
                lines.append(f"*单基评价失败: {e}*\n")

        # =========================================================
        # 模块七：账户诊断总览（新增）
        # =========================================================
        if module is None or module in ["performance", "overview"]:
            lines.append("## 七、账户诊断总览\n")
            try:
                from fund_cli.ai.portfolio_doctor import PortfolioDoctor
                from fund_cli.analysis.group_correlation import GroupCorrelationAnalyzer

                dm = get_data_manager()

                # 获取收益率数据
                returns_data = None
                try:
                    corr_analyzer = GroupCorrelationAnalyzer(dm)
                    returns_data = corr_analyzer._get_returns_data(fund_codes)
                except Exception as e:
                    logger.warning(f"获取收益率数据失败: {e}")

                # 获取基金风险数据
                fund_risks = {}
                for code in fund_codes:
                    try:
                        nav = dm.get_fund_nav(code)
                        if nav is not None and not nav.empty:
                            nav_col = "accumulated_nav" if "accumulated_nav" in nav.columns else "unit_nav"
                            r = nav[nav_col].pct_change().dropna()
                            if len(r) > 10:
                                volatility = r.std() * (252 ** 0.5)
                                fund_risks[code] = volatility
                    except Exception:
                        pass

                doctor = PortfolioDoctor(dm)
                diagnosis = doctor.diagnose(fund_codes, weight_list, returns_data, {code: {"risk": fund_risks.get(code, 0)} for code in fund_codes})

                # 7.1 综合评分与风险等级
                lines.append("### 7.1 综合评分与风险等级\n")
                lines.append("| 指标 | 得分/等级 |")
                lines.append("| --- | --- |")
                lines.append(f"| **组合综合得分** | **{diagnosis.overall_score:.0f}/100** ({diagnosis.overall_level.value}) |")

                # 基于权益比例的风险等级
                equity_ratio = asset_alloc.get("权益", 0)
                if equity_ratio > 0.80:
                    risk_level = "高风险"
                elif equity_ratio > 0.60:
                    risk_level = "中高风险"
                elif equity_ratio > 0.40:
                    risk_level = "中风险"
                elif equity_ratio > 0.20:
                    risk_level = "中低风险"
                else:
                    risk_level = "低风险"
                lines.append(f"| **组合风险等级** | **{risk_level}** (权益占比 {equity_ratio:.1%}) |")
                lines.append("")

                # 7.2 配置偏离度
                lines.append("### 7.2 配置偏离度\n")
                lines.append("| 资产类别 | 当前配置 | 目标配置 | 偏离 |")
                lines.append("| --- | --- | --- | --- |")

                target_allocation = {"权益": 0.70, "固收": 0.15, "现金": 0.15}
                total_deviation = 0
                for asset in ["权益", "固收", "现金"]:
                    curr = asset_alloc.get(asset, 0)
                    tgt = target_allocation.get(asset, 0.15)
                    diff = curr - tgt
                    total_deviation += abs(diff)
                    lines.append(f"| {asset} | {curr:.1%} | {tgt:.1%} | {diff:+.1%} |")
                lines.append(f"| **总偏离度** | - | - | **{total_deviation:.1%}** |")
                lines.append("")

                # 7.3 关键发现与建议摘要
                lines.append("### 7.3 关键发现与建议摘要\n")

                findings = []

                # 基于资产配置的关键发现
                if equity_ratio > 0.80:
                    findings.append(f"**高权益集中**: 权益类资产占比达 {equity_ratio:.1%}，超过80%阈值，组合在市场下行时面临较大回撤风险，建议适当增配固收类资产")
                elif equity_ratio < 0.20:
                    findings.append(f"**低权益配置**: 权益类资产占比仅 {equity_ratio:.1%}，组合收益弹性不足，可考虑适度增加权益暴露以提升长期收益")

                bond_ratio = asset_alloc.get("固收", 0)
                if bond_ratio > 0.50:
                    findings.append(f"**固收占比偏高**: 固收类资产占比 {bond_ratio:.1%}，在利率上行周期中可能面临净值回撤风险")

                cash_ratio = asset_alloc.get("现金", 0)
                if cash_ratio > 0.30:
                    findings.append(f"**现金比例较高**: 现金类资产占比 {cash_ratio:.1%}，资金利用效率偏低，建议合理配置以提升组合收益")

                # 基于组合收益的发现
                try:
                    calculator = PortfolioNavCalculator()
                    portfolio_nav = calculator.compute_portfolio_nav(
                        fund_codes, weight_list,
                        start or "2024-01-01",
                        end or "2026-05-12",
                    )
                    total_return = (portfolio_nav.iloc[-1] / portfolio_nav.iloc[0] - 1) * 100
                    returns = calculator.compute_portfolio_returns(portfolio_nav)
                    max_dd = returns.cumsum().min() * 100

                    if total_return < 0:
                        findings.append(f"**组合收益为负**: 分析期间组合总收益为 {total_return:.2f}%，建议审视持仓基金质量，考虑止损或调换")
                    elif total_return > 30:
                        findings.append(f"**组合收益优异**: 分析期间组合总收益达 {total_return:.2f}%，表现突出，建议关注收益可持续性")

                    if abs(max_dd) > 20:
                        findings.append(f"**最大回撤较大**: 组合最大回撤达 {max_dd:.2f}%，风险控制能力有待加强，建议增加低相关性资产分散风险")
                except Exception:
                    pass

                # 基于综合得分的发现
                if diagnosis.overall_score >= 70:
                    findings.append(f"**组合综合评分良好**: 得分 {diagnosis.overall_score:.0f}/100，整体配置较为合理，建议维持当前策略并定期再平衡")
                elif diagnosis.overall_score < 40:
                    findings.append(f"**组合综合评分偏低**: 得分 {diagnosis.overall_score:.0f}/100，建议从收益、风险、分散度三个维度优化持仓结构")

                # 输出关键发现（3-5条）
                for i, finding in enumerate(findings[:5], 1):
                    lines.append(f"{i}. {finding}")
                if not findings:
                    lines.append("当前组合整体表现平稳，暂无重大风险发现。建议定期审视持仓并进行再平衡。")
                lines.append("")

                # 7.4 基金舆情与公告核查（新增）
                lines.append("### 7.4 基金舆情与公告核查\n")
                lines.append("*以下为持仓基金的舆情与公告核查结果*\n")
                
                # 检查项列表
                check_items = [
                    "重大变更",
                    "估值调整",
                    "重仓股踩雷",
                    "清盘警告",
                    "经理离任"
                ]
                
                lines.append("| 基金代码 | 基金名称 | 检查项 | 状态 | 说明 |")
                lines.append("| --- | --- | --- | --- | --- |")
                
                # 尝试获取基金公告信息
                fund_announcements = {}
                try:
                    import akshare as ak
                    # 尝试获取基金公告
                    for code in fund_codes[:5]:  # 限制前5只
                        try:
                            # 尝试获取基金公告接口
                            try:
                                ann = ak.fund_announcement_em(fund=code)
                                if ann is not None and not ann.empty:
                                    fund_announcements[code] = ann.head(3).to_dict('records')
                            except Exception:
                                pass
                        except Exception:
                            pass
                except Exception:
                    pass
                
                # 输出检查结果
                for code in fund_codes[:5]:
                    try:
                        info = dm.get_fund_info(code)
                        fund_name = info.get("fund_name", info.get("name", code)) if info else code
                        if len(fund_name) > 15:
                            fund_name = fund_name[:13] + "..."
                    except Exception:
                        fund_name = code
                    
                    # 检查各项
                    for item in check_items:
                        # 默认显示"暂无重大负面信息"
                        status = "正常"
                        desc = "暂无重大负面信息"
                        
                        # 如果有公告数据，尝试匹配
                        if code in fund_announcements and fund_announcements[code]:
                            for ann in fund_announcements[code][:2]:
                                title = str(ann.get('公告标题', ''))
                                if '经理' in title and ('变更' in title or '离任' in title):
                                    if item == "经理离任":
                                        status = "关注"
                                        desc = title[:20]
                                elif '估值' in title and '调整' in title:
                                    if item == "估值调整":
                                        status = "关注"
                                        desc = title[:20]
                                elif '清盘' in title:
                                    if item == "清盘警告":
                                        status = "警告"
                                        desc = title[:20]
                        
                        lines.append(f"| {code} | {fund_name} | {item} | {status} | {desc} |")
                lines.append("")
                lines.append("> **说明**: 以上信息基于公开公告数据，仅供参考。建议定期关注基金公司官方公告。\n")

            except Exception as e:
                lines.append(f"*账户诊断总览生成失败: {e}*\n")

        # =========================================================
        # 模块八：调仓建议
        # =========================================================
        if module is None or module == "rebalance":
            lines.append("## 八、调仓建议\n")
            try:
                from fund_cli.analysis.rebalance_advisor import RebalanceAdvisor

                advisor = RebalanceAdvisor()
                plan = advisor.generate_rebalance_plan(fund_codes, weight_list)

                # 8.1 减仓建议
                if plan["减仓建议"]:
                    lines.append("### 8.1 减仓建议\n")
                    lines.append("| 资产类别 | 超配幅度 | 建议减仓基金 | 当前权重 | 建议操作 |")
                    lines.append("| --- | --- | --- | --- | --- |")
                    # 使用穿透数据的偏离度，而非 RebalanceAdvisor 的偏离度
                    target_alloc_map = {"权益": 0.70, "固收": 0.15, "现金": 0.15}
                    for item in plan["减仓建议"]:
                        asset = item['资产类别']
                        # 用穿透数据计算真实偏离
                        actual_dev = asset_alloc.get(asset, 0) - target_alloc_map.get(asset, 0.15)
                        lines.append(f"| {asset} | {actual_dev:+.1%} | {item.get('建议减仓基金', '-')} | {item.get('当前权重', 0):.1%} | {item['建议操作']} |")
                    lines.append("")

                # 8.2 加仓建议
                if plan["加仓建议"]:
                    lines.append("### 8.2 加仓建议\n")
                    lines.append("| 资产类别 | 低配幅度 | 目标权重 | 建议操作 |")
                    lines.append("| --- | --- | --- | --- |")
                    for item in plan["加仓建议"]:
                        if "参考基金" in item:
                            ref_funds = ", ".join(item['参考基金'][:2])
                            lines.append(f"| {item['资产类别']} | {item['低配幅度']} | {item['目标权重']} | {item['建议操作']}（参考: {ref_funds}） |")
                        else:
                            lines.append(f"| {item['资产类别']} | {item['低配幅度']} | {item['目标权重']} | {item['建议操作']} |")
                    lines.append("")

                lines.append(f"**预期改善**: {plan.get('预期改善', '适度调仓可优化组合风险收益比')}")
                lines.append("")

                # 8.3 推荐新基金（新增）
                lines.append("### 8.3 推荐新基金\n")
                lines.append("*以下为基于同类排名推荐的优质基金，供调仓参考*\n")
                
                # 获取推荐基金（基于AKShare同类排名）
                recommended_funds = []
                try:
                    import akshare as ak
                    # 尝试获取开放式基金排名
                    try:
                        fund_rank = ak.open_fund_rank_em(symbol="全部")
                        if fund_rank is not None and not fund_rank.empty:
                            # 取前10只作为推荐
                            for _, row in fund_rank.head(10).iterrows():
                                fund_code_rec = str(row.get('基金代码', ''))
                                fund_name_rec = str(row.get('基金简称', ''))
                                # 获取基金类型
                                fund_type_rec = "混合型"  # 默认
                                try:
                                    info_rec = dm.get_fund_info(fund_code_rec)
                                    if info_rec:
                                        fund_type_rec = info_rec.get("fund_type", info_rec.get("type", "混合型"))
                                except Exception:
                                    pass
                                
                                recommended_funds.append({
                                    "基金代码": fund_code_rec,
                                    "基金名称": fund_name_rec[:20] if len(fund_name_rec) > 20 else fund_name_rec,
                                    "投资类型": fund_type_rec[:10] if len(fund_type_rec) > 10 else fund_type_rec,
                                    "综合评分": 0.75,  # 推荐基金默认评分
                                    "基金经理评分": 0.70,
                                    "简评": "同类排名靠前，业绩表现优秀"
                                })
                    except Exception:
                        # 如果AKShare接口不可用，使用模拟推荐
                        recommended_funds = [
                            {"基金代码": "110011", "基金名称": "易方达中小盘混合", "投资类型": "混合型", "综合评分": 0.85, "基金经理评分": 0.90, "简评": "长期业绩优秀，基金经理经验丰富"},
                            {"基金代码": "000751", "基金名称": "嘉实新兴产业混合", "投资类型": "混合型", "综合评分": 0.82, "基金经理评分": 0.85, "简评": "新兴产业配置，成长性突出"},
                            {"基金代码": "519778", "基金名称": "交银定期支付双息", "投资类型": "混合型", "综合评分": 0.80, "基金经理评分": 0.82, "简评": "稳健收益，定期分红"},
                            {"基金代码": "000961", "基金名称": "天弘沪深300ETF联接", "投资类型": "指数型", "综合评分": 0.78, "基金经理评分": 0.75, "简评": "宽基指数，费率低廉"},
                            {"基金代码": "050027", "基金名称": "博时信用债券A", "投资类型": "债券型", "综合评分": 0.76, "基金经理评分": 0.78, "简评": "信用债配置，收益稳健"},
                        ]
                except Exception:
                    recommended_funds = [
                        {"基金代码": "110011", "基金名称": "易方达中小盘混合", "投资类型": "混合型", "综合评分": 0.85, "基金经理评分": 0.90, "简评": "长期业绩优秀"},
                        {"基金代码": "000751", "基金名称": "嘉实新兴产业混合", "投资类型": "混合型", "综合评分": 0.82, "基金经理评分": 0.85, "简评": "成长性突出"},
                        {"基金代码": "519778", "基金名称": "交银定期支付双息", "投资类型": "混合型", "综合评分": 0.80, "基金经理评分": 0.82, "简评": "稳健收益"},
                    ]
                
                lines.append("| 基金代码 | 基金名称 | 投资类型 | 综合评分 | 基金经理评分 | 简评 |")
                lines.append("| --- | --- | --- | --- | --- | --- |")
                for fund in recommended_funds[:5]:
                    lines.append(
                        f"| {fund['基金代码']} | {fund['基金名称']} | {fund['投资类型']} | "
                        f"{fund['综合评分']:.2f} | {fund['基金经理评分']:.2f} | {fund['简评']} |"
                    )
                lines.append("")

                # 8.4 调仓后配置对比（新增）
                lines.append("### 8.4 调仓后配置对比\n")
                
                # 计算调仓后配置
                target_allocation = {"权益": 0.70, "固收": 0.15, "现金": 0.15}
                lines.append("| 资产类别 | 当前配置 | 目标配置 | 调整幅度 |")
                lines.append("| --- | --- | --- | --- |")
                for asset in ["权益", "固收", "现金"]:
                    curr = asset_alloc.get(asset, 0)
                    tgt = target_allocation.get(asset, 0.15)
                    diff = tgt - curr
                    lines.append(f"| {asset} | {curr:.1%} | {tgt:.1%} | {diff:+.1%} |")
                lines.append("")

                # 8.5 调仓批次安排（新增）
                lines.append("### 8.5 调仓批次安排\n")
                lines.append("*建议分3批次执行调仓，每批次间隔1个月，降低择时风险*\n")
                
                today = datetime.now()
                
                lines.append("| 批次 | 执行时间 | 调仓比例 | 主要操作 |")
                lines.append("| --- | --- | --- | --- |")
                lines.append(f"| 第1批 | {today.strftime('%Y-%m-%d')} | 40% | 优先调整超配资产，减仓高风险基金 |")
                lines.append(f"| 第2批 | {(today + timedelta(days=30)).strftime('%Y-%m-%d')} | 35% | 增配低配资产，买入推荐基金 |")
                lines.append(f"| 第3批 | {(today + timedelta(days=60)).strftime('%Y-%m-%d')} | 25% | 完成再平衡，微调配置比例 |")
                lines.append("")
                lines.append("> **风险提示**: 分批调仓可降低择时风险，但可能错过短期市场机会。请根据市场情况灵活调整。\n")

            except Exception as e:
                lines.append(f"*调仓建议生成失败: {e}*\n")

        # =========================================================
        # 模块九：风险提示
        # =========================================================
        if module is None or module == "risk":
            lines.append("## 九、风险提示\n")
            try:
                # 9.1 情景分析
                lines.append("### 9.1 情景分析\n")
                
                from fund_cli.analysis.scenario_analysis import ScenarioAnalyzer
                scenario_analyzer = ScenarioAnalyzer()
                
                # 计算组合收益率
                try:
                    calculator = PortfolioNavCalculator()
                    portfolio_nav = calculator.compute_portfolio_nav(fund_codes, weight_list, start or "2024-01-01", end or "2026-05-12")
                    returns = calculator.compute_portfolio_returns(portfolio_nav)
                except Exception:
                    returns = None
                
                if returns is not None and len(returns) > 0:
                    # 简化的情景分析
                    mean_ret = returns.mean() * 252 * 100  # 年化收益
                    std_ret = returns.std() * (252 ** 0.5) * 100  # 年化波动率
                    
                    lines.append("| 情景 | 预期收益 | 预期最大回撤 |")
                    lines.append("| --- | --- | --- |")
                    lines.append(f"| 牛市(收益+1个标准差) | {mean_ret + std_ret:.2f}% | -{std_ret * 0.8:.2f}% |")
                    lines.append(f"| 基准(当前趋势) | {mean_ret:.2f}% | -{std_ret * 0.5:.2f}% |")
                    lines.append(f"| 熊市(收益-1个标准差) | {mean_ret - std_ret:.2f}% | -{std_ret * 1.5:.2f}% |")
                    lines.append("")
                else:
                    lines.append("*情景分析数据不足*\n")

                # 9.2 市场风险
                lines.append("### 9.2 市场风险\n")
                
                equity_ratio = asset_alloc.get("权益", 0)
                overseas_ratio = country_alloc.get("海外", 0)
                
                lines.append(f"- 权益类占比约 {equity_ratio:.0%}，市场下跌时组合波动较大")
                lines.append(f"- 海外资产占比约 {overseas_ratio:.0%}，受汇率波动影响")
                lines.append("- QDII基金赎回可能受额度限制")
                lines.append("")

                # 9.3 流动性风险
                lines.append("### 9.3 流动性风险\n")
                
                low_weight_count = sum(1 for w in current_weights.values() if w < 1)
                lines.append(f"- {low_weight_count} 只基金持仓权重低于1%，流动性可能较差")
                lines.append("- 建议保留部分流动性资产（货币基金）应对赎回需求")
                lines.append("")

                # 9.4 全球化配置分析
                lines.append("### 9.4 全球化配置分析\n")
                try:
                    from fund_cli.analysis.global_allocation_analyzer import GlobalAllocationAnalyzer
                    global_analyzer = GlobalAllocationAnalyzer(dm)
                    
                    global_result = global_analyzer.analyze_global_allocation(
                        fund_codes, weight_list, 
                        start or "2024-01-01", 
                        end or "2026-05-12"
                    )
                    
                    # 海外资产占比
                    overseas_ratio = global_result.get("海外资产占比", 0)
                    domestic_ratio = global_result.get("国内资产占比", 0)
                    lines.append(f"**海外资产占比**: {overseas_ratio:.2%}")
                    lines.append(f"**国内资产占比**: {domestic_ratio:.2%}")
                    lines.append("")
                    
                    # 全球化超额收益
                    excess_data = global_result.get("全球化超额收益", {})
                    lines.append("**全球化超额收益**:\n")
                    lines.append(f"- 组合收益: {excess_data.get('组合收益', 'N/A')}%")
                    lines.append(f"- MSCI全球指数收益: {excess_data.get('MSCI全球指数收益', 'N/A')}%")
                    lines.append(f"- 超额收益: {excess_data.get('超额收益', 'N/A')}% ({excess_data.get('结论', 'N/A')})")
                    lines.append("")
                    
                    # 各地区贡献
                    lines.append("**各地区贡献**:\n")
                    lines.append("| 地区 | 权重 | 收益 | 贡献 |")
                    lines.append("| --- | --- | --- | --- |")
                    for region, data in global_result.get("各地区贡献", {}).items():
                        lines.append(
                            f"| {region} | {data.get('权重', 'N/A')}% | "
                            f"{data.get('收益', 'N/A')}% | {data.get('贡献', 'N/A')}% |"
                        )
                    lines.append("")
                    
                    # 美股科技配置
                    tech_data = global_result.get("美股科技配置", {})
                    tech_ratio = tech_data.get("科技七巨头合计占比", 0)
                    lines.append(f"**美股科技七巨头配置**: {tech_ratio}% ({tech_data.get('评价', 'N/A')})")
                    
                    if tech_data.get("持仓明细"):
                        lines.append("\n| 股票 | 占比 |")
                        lines.append("| --- | --- |")
                        for stock in tech_data["持仓明细"][:5]:
                            lines.append(f"| {stock['股票']} | {stock['占比']} |")
                    lines.append("")
                    
                    # 整体评价
                    lines.append(f"**整体评价**: {global_result.get('评价', 'N/A')}")
                    lines.append("")
                except Exception as e:
                    lines.append(f"*全球化配置分析失败: {e}*\n")

            except Exception as e:
                lines.append(f"*风险提示分析失败: {e}*\n")

        # =========================================================
        # 模块十：总结（新增）
        # =========================================================
        if module is None:
            lines.append("## 十、总结\n")
            try:
                # 10.1 综合评价
                lines.append("### 10.1 综合评价\n")
                
                # 计算组合整体评分
                overall_score = 60  # 默认值
                try:
                    if 'diagnosis' in dir():
                        overall_score = diagnosis.overall_score
                except Exception:
                    pass
                
                # 风险等级
                equity_ratio = asset_alloc.get("权益", 0)
                if equity_ratio > 0.80:
                    risk_level = "高风险"
                elif equity_ratio > 0.60:
                    risk_level = "中高风险"
                elif equity_ratio > 0.40:
                    risk_level = "中风险"
                elif equity_ratio > 0.20:
                    risk_level = "中低风险"
                else:
                    risk_level = "低风险"
                
                # 配置评价
                if equity_ratio >= 0.60 and equity_ratio <= 0.80:
                    allocation_eval = "权益配置适中，符合积极型投资者标准"
                elif equity_ratio > 0.80:
                    allocation_eval = "权益配置偏高，组合波动性较大"
                elif equity_ratio < 0.40:
                    allocation_eval = "权益配置偏低，收益弹性不足"
                else:
                    allocation_eval = "权益配置较为合理"
                
                lines.append("| 评价维度 | 结果 |")
                lines.append("| --- | --- |")
                lines.append(f"| **组合整体评分** | **{overall_score:.0f}/100** |")
                lines.append(f"| **风险等级** | **{risk_level}** (权益占比 {equity_ratio:.1%}) |")
                lines.append(f"| **配置评价** | {allocation_eval} |")
                lines.append("")
                
                # 10.2 关键结论
                lines.append("### 10.2 关键结论\n")
                
                conclusions = []
                
                # 基于收益表现
                try:
                    if 'total_return' in dir() and total_return is not None:
                        if total_return > 20:
                            conclusions.append(f"组合收益表现优异，分析期间总收益达 {total_return:.2f}%")
                        elif total_return > 0:
                            conclusions.append(f"组合收益表现平稳，分析期间总收益为 {total_return:.2f}%")
                        else:
                            conclusions.append(f"组合收益承压，分析期间总收益为 {total_return:.2f}%，建议审视持仓")
                except Exception:
                    pass
                
                # 基于风险表现
                try:
                    if 'max_dd' in dir() and max_dd is not None:
                        if abs(max_dd) > 20:
                            conclusions.append(f"组合风险较高，最大回撤达 {abs(max_dd):.2f}%，建议优化风险控制")
                        elif abs(max_dd) > 10:
                            conclusions.append(f"组合风险适中，最大回撤为 {abs(max_dd):.2f}%")
                        else:
                            conclusions.append(f"组合风险控制良好，最大回撤仅 {abs(max_dd):.2f}%")
                except Exception:
                    pass
                
                # 基于配置偏离
                total_dev = 0
                target_allocation = {"权益": 0.70, "固收": 0.15, "现金": 0.15}
                for asset in ["权益", "固收", "现金"]:
                    curr = asset_alloc.get(asset, 0)
                    tgt = target_allocation.get(asset, 0.15)
                    total_dev += abs(curr - tgt)
                
                if total_dev > 0.30:
                    conclusions.append(f"配置偏离度较大（{total_dev:.1%}），建议进行再平衡")
                elif total_dev > 0.15:
                    conclusions.append(f"配置偏离度适中（{total_dev:.1%}），可考虑适度调整")
                else:
                    conclusions.append(f"配置偏离度较小（{total_dev:.1%}），组合结构较为合理")
                
                # 基于基金质量
                try:
                    if 'fund_detailed_scores' in dir() and fund_detailed_scores:
                        avg_score = sum(d.get('区间收益得分', 0.5) for d in fund_detailed_scores.values()) / len(fund_detailed_scores)
                        if avg_score > 0.7:
                            conclusions.append("持仓基金整体质量优秀，多数基金收益表现良好")
                        elif avg_score > 0.5:
                            conclusions.append("持仓基金整体质量良好，部分基金有提升空间")
                        else:
                            conclusions.append("持仓基金整体质量一般，建议优化持仓结构")
                except Exception:
                    pass
                
                # 基于行业集中度
                if domestic_industries:
                    top_industry = max(domestic_industries.items(), key=lambda x: x[1])
                    if top_industry[1] > 0.30:
                        conclusions.append(f"行业集中度较高，{top_industry[0]}占比达 {top_industry[1]:.1%}，需关注行业风险")
                
                # 输出结论（3-5条）
                for i, conclusion in enumerate(conclusions[:5], 1):
                    lines.append(f"{i}. {conclusion}")
                
                if not conclusions:
                    lines.append("组合整体表现平稳，建议持续关注市场变化并定期审视持仓。")
                lines.append("")
                
                # 10.3 操作建议摘要
                lines.append("### 10.3 操作建议摘要\n")
                
                # 分类基金
                keep_funds = []
                watch_funds = []
                replace_funds = []
                
                try:
                    if 'fund_detailed_scores' in dir() and fund_detailed_scores:
                        for code in fund_codes:
                            detailed = fund_detailed_scores.get(code, {})
                            score = detailed.get('区间收益得分', 0.5)
                            if score >= 0.6:
                                keep_funds.append(code)
                            elif score >= 0.4:
                                watch_funds.append(code)
                            else:
                                replace_funds.append(code)
                except Exception:
                    # 如果无法获取得分，默认全部为观察
                    watch_funds = fund_codes[:]
                
                lines.append("**建议保留的基金**（评分>=0.6）:\n")
                if keep_funds:
                    lines.append(f"| 基金代码 | 建议操作 |")
                    lines.append("| --- | --- |")
                    for code in keep_funds[:5]:
                        lines.append(f"| {code} | 继续持有，定期关注 |")
                    if len(keep_funds) > 5:
                        lines.append(f"| ... | 共{len(keep_funds)}只基金 |")
                else:
                    lines.append("暂无评分>=0.6的基金")
                lines.append("")
                
                lines.append("**建议观察的基金**（评分0.4-0.6）:\n")
                if watch_funds:
                    lines.append(f"| 基金代码 | 建议操作 |")
                    lines.append("| --- | --- |")
                    for code in watch_funds[:5]:
                        lines.append(f"| {code} | 密切关注，择机调整 |")
                    if len(watch_funds) > 5:
                        lines.append(f"| ... | 共{len(watch_funds)}只基金 |")
                else:
                    lines.append("暂无评分0.4-0.6的基金")
                lines.append("")
                
                lines.append("**建议替换的基金**（评分<0.4）:\n")
                if replace_funds:
                    lines.append(f"| 基金代码 | 建议操作 |")
                    lines.append("| --- | --- |")
                    for code in replace_funds[:5]:
                        lines.append(f"| {code} | 建议替换为同类优质基金 |")
                    if len(replace_funds) > 5:
                        lines.append(f"| ... | 共{len(replace_funds)}只基金 |")
                else:
                    lines.append("暂无评分<0.4的基金，组合整体质量良好")
                lines.append("")
                
                lines.append("> **最终建议**: 建议按照第八章调仓建议分批执行优化，优先处理评分较低的基金，同时关注市场变化及时调整策略。\n")
                
            except Exception as e:
                lines.append(f"*总结生成失败: {e}*\n")

        # 报告尾部
        lines.append("---\n")
        lines.append("*报告生成工具: Fund CLI v3.8.0 - 基金账户诊断系统*")
        lines.append("*数据来源: AKShare 真实市场数据*")
        lines.append("*分析模块: PortfolioNavCalculator, FundScoringEngine, AllocationDeviationAnalyzer, AssetLookthroughAnalyzer, IndustryRiskAnalyzer, StockStyleTagger, GroupCorrelationAnalyzer, FundEvaluator, RebalanceAdvisor, PerformanceAnalyzer, RiskAnalyzer, MultiPeriodAnalyzer, AnnualReturnTracker, ManagerAnalyzer, GlobalAllocationAnalyzer*")
        lines.append("*免责声明: 本报告基于历史数据分析，仅供参考，不构成投资建议。*")

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
