"""
AI 分析命令（V3.0 - LangGraph Agent 实现）

提供 AI 辅助分析功能，支持：
- 智能对话（Agent 驱动，支持工具调用和记忆）
- 基金摘要生成、对比分析、投资建议等（V2.0 兼容）
- 智能选基、组合诊断、市场解读（V3.3 新增）
- 用户画像、个性化推荐、投资建议（V3.4 新增）
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="AI分析命令（V3.0 - Agent驱动）")
console = Console()


# ============================================
# V3.3 新增命令 - AI 决策支持
# ============================================


@app.command("select")
def ai_select(
    query: str = typer.Argument(..., help="自然语言需求描述"),
    top_n: int = typer.Option(10, "--top", "-n", help="返回推荐数量"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    智能选基：基于自然语言描述智能推荐基金

    示例:
        fund ai select "稳健的股票型基金，年化收益10%以上，最大回撤不超过20%"
        fund ai select "债券型基金，规模50亿以上" --top 5
        fund ai select "成长风格基金" --output result.txt
    """
    from fund_cli.ai.fund_selector import FundSelector

    try:
        selector = FundSelector()
        recommendations = selector.select(query, top_n)

        if not recommendations:
            console.print("[yellow]未找到符合条件的基金，请尝试调整筛选条件[/yellow]")
            raise typer.Exit(0) from None

        # 格式化输出
        lines = ["# 智能选基推荐结果\n"]
        lines.append(f"查询条件: {query}")
        lines.append(f"共找到 {len(recommendations)} 只符合条件的基金：\n")

        for rec in recommendations:
            lines.append(f"## {rec.rank}. {rec.fund_name} ({rec.fund_code})")
            lines.append(f"- 基金类型: {rec.fund_type}")
            lines.append(f"- 综合评分: {rec.score:.2f}")
            lines.append(f"- 推荐理由: {rec.recommendation_reason}")
            lines.append(f"- 风险提示: {rec.risk_warning}")
            if rec.key_metrics.get("return_1y") is not None:
                lines.append(f"- 近一年收益: {rec.key_metrics['return_1y']:.2f}%")
            if rec.key_metrics.get("max_drawdown") is not None:
                lines.append(f"- 最大回撤: {abs(rec.key_metrics['max_drawdown']):.2f}%")
            lines.append("")

        result = "\n".join(lines)
        console.print(Panel(result, title="智能选基结果", border_style="green"))

        if output:
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]智能选基失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("diagnose")
def ai_diagnose(
    fund_codes: str = typer.Argument(..., help="基金代码列表（逗号分隔）"),
    weights: str = typer.Option(
        None, "--weights", "-w", help="权重配置（逗号分隔，如0.4,0.3,0.3）"
    ),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    投资组合诊断：评估组合健康状况，发现潜在风险

    示例:
        fund ai diagnose 000001,000002,000003
        fund ai diagnose 000001,000002 --weights 0.6,0.4
        fund ai diagnose 000001,000002,000003 --weights 0.4,0.3,0.3 --output report.txt
    """
    from fund_cli.ai.portfolio_doctor import PortfolioDoctor

    try:
        codes = [c.strip() for c in fund_codes.split(",")]

        # 解析权重
        weight_list = None
        if weights:
            weight_list = [float(w.strip()) for w in weights.split(",")]
            if len(weight_list) != len(codes):
                console.print("[red]权重数量必须与基金数量一致[/red]")
                raise typer.Exit(1) from None

        # 执行诊断
        doctor = PortfolioDoctor()
        diagnosis = doctor.diagnose(codes, weight_list)

        # 格式化输出
        result = doctor.format_diagnosis(diagnosis)
        console.print(Panel(result, title="组合诊断报告", border_style="blue"))

        if output:
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]组合诊断失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("market")
def ai_market(
    market_type: str = typer.Option(
        "sentiment", "--type", "-t", help="分析类型: sentiment(情绪)/rotation(轮动)/hotspot(热点)"
    ),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    市场解读：分析市场情绪、行业轮动或热点追踪

    示例:
        fund ai market                    # 市场情绪分析
        fund ai market --type rotation    # 行业轮动分析
        fund ai market --type hotspot     # 热点追踪
        fund ai market --output market.txt
    """
    from fund_cli.ai.market_analyst import MarketAnalyst

    try:
        analyst = MarketAnalyst()

        if market_type in ["sentiment", "情绪"]:
            report = analyst.analyze_sentiment()
            result = analyst.format_sentiment_report(report)
            title = "市场情绪分析"
        elif market_type in ["rotation", "轮动"]:
            report = analyst.analyze_sector_rotation()
            result = analyst.format_sector_report(report)
            title = "行业轮动分析"
        elif market_type in ["hotspot", "热点"]:
            report = analyst.track_hotspots()
            result = analyst.format_hotspot_report(report)
            title = "热点追踪报告"
        else:
            # 默认情绪分析
            report = analyst.analyze_sentiment()
            result = analyst.format_sentiment_report(report)
            title = "市场情绪分析"

        console.print(Panel(result, title=title, border_style="cyan"))

        if output:
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]市场分析失败: {e}[/red]")
        raise typer.Exit(1) from None


# ============================================
# V3.4 新增命令 - 智能推荐系统
# ============================================


@app.command("profile")
def ai_profile(
    action: str = typer.Argument("show", help="操作: show/create/assess"),
    name: str = typer.Option(None, "--name", "-n", help="用户名称"),
    risk_level: str = typer.Option(
        None, "--risk", "-r", help="风险等级: conservative/moderate/balanced/growth/aggressive"
    ),
    investment_horizon: str = typer.Option(
        None, "--horizon", "-h", help="投资期限: short/medium/long"
    ),
    goals: str = typer.Option(None, "--goals", "-g", help="投资目标（逗号分隔）"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    用户画像管理：创建和管理用户投资画像

    示例:
        fund ai profile show                              # 显示当前画像
        fund ai profile create --name 张三 --risk moderate --horizon long
        fund ai profile assess                            # 风险评估问卷
        fund ai profile create --name 张三 --risk aggressive --goals 退休养老,子女教育
    """
    from fund_cli.ai.user_profile import ProfileManager, RiskQuestionnaire

    try:
        manager = ProfileManager()

        if action == "show":
            profile = manager.get_current_profile()
            if profile is None:
                console.print("[yellow]尚未创建用户画像，请使用 'fund ai profile create' 创建[/yellow]")
                raise typer.Exit(0) from None

            # 显示画像信息
            table = Table(title=f"用户画像 - {profile.name}")
            table.add_column("项目", style="cyan")
            table.add_column("值", style="green")

            table.add_row("用户名", profile.name)
            table.add_row("风险等级", profile.risk_assessment.tolerance.value)
            table.add_row("风险得分", f"{profile.risk_assessment.score:.0f}/100")
            table.add_row("投资期限", profile.investment_horizon.value)
            table.add_row("投资风格", profile.investment_style.value)
            table.add_row("投资目标", profile.investment_goal.value)
            created_at = profile.created_at if isinstance(profile.created_at, str) else profile.created_at.strftime("%Y-%m-%d %H:%M")
            table.add_row("创建时间", created_at)

            console.print(table)

        elif action == "create":
            if not name:
                console.print("[red]请使用 --name 指定用户名称[/red]")
                raise typer.Exit(1) from None

            # 解析风险等级映射为问卷答案
            risk_answer_map = {
                "conservative": {"q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 0},
                "moderate": {"q1": 1, "q2": 1, "q3": 1, "q4": 1, "q5": 1},
                "balanced": {"q1": 2, "q2": 2, "q3": 2, "q4": 2, "q5": 2},
                "growth": {"q1": 3, "q2": 3, "q3": 3, "q4": 3, "q5": 3},
                "aggressive": {"q1": 4, "q2": 4, "q3": 4, "q4": 4, "q5": 4},
            }
            risk_answers = risk_answer_map.get(risk_level or "moderate", risk_answer_map["moderate"])

            # 解析投资期限
            from fund_cli.ai.user_profile import InvestmentGoal, InvestmentHorizon
            horizon_map = {
                "short": InvestmentHorizon.SHORT_TERM,
                "medium": InvestmentHorizon.MEDIUM_TERM,
                "long": InvestmentHorizon.LONG_TERM,
            }
            horizon = horizon_map.get(investment_horizon or "medium", InvestmentHorizon.MEDIUM_TERM)

            # 解析投资目标
            goal_map = {
                "wealth_preservation": InvestmentGoal.WEALTH_PRESERVATION,
                "steady_income": InvestmentGoal.STEADY_INCOME,
                "balanced_growth": InvestmentGoal.BALANCED_GROWTH,
                "aggressive_growth": InvestmentGoal.AGGRESSIVE_GROWTH,
            }
            goal = InvestmentGoal.BALANCED_GROWTH
            if goals:
                first_goal = goals.split(",")[0].strip()
                goal = goal_map.get(first_goal.lower().replace(" ", "_"), InvestmentGoal.BALANCED_GROWTH)

            # 创建画像
            import uuid
            profile = manager.create_profile(
                user_id=str(uuid.uuid4())[:8],
                name=name,
                risk_answers=risk_answers,
                investment_goal=goal,
                investment_horizon=horizon,
            )

            console.print("[green]✓ 用户画像创建成功[/green]")
            console.print(f"  用户名: {profile.name}")
            console.print(f"  风险等级: {profile.risk_assessment.tolerance.value}")
            console.print(f"  投资期限: {profile.investment_horizon.value}")

            if output:
                import json
                profile_dict = {
                    "name": profile.name,
                    "risk_level": profile.risk_assessment.tolerance.value,
                    "risk_score": profile.risk_assessment.score,
                    "investment_horizon": profile.investment_horizon.value,
                    "investment_style": profile.investment_style.value,
                    "goals": [g.value for g in profile.goals],
                }
                Path(output).write_text(
                    json.dumps(profile_dict, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                console.print(f"[green]结果已保存至: {output}[/green]")

        elif action == "assess":
            # 风险评估问卷
            questionnaire = RiskQuestionnaire()
            questions = questionnaire.get_questions()

            console.print(Panel("[bold]风险评估问卷[/bold]\n请回答以下问题以评估您的风险承受能力", border_style="blue"))

            answers = []
            for i, q in enumerate(questions, 1):
                console.print(f"\n[bold]{i}. {q['question']}[/bold]")
                for j, opt in enumerate(q["options"], 1):
                    console.print(f"  {j}. {opt['text']}")

                while True:
                    try:
                        choice = int(console.input("[cyan]请选择 (1-4): [/cyan]"))
                        if 1 <= choice <= 4:
                            answers.append(q["options"][choice - 1]["score"])
                            break
                        else:
                            console.print("[red]请输入1-4之间的数字[/red]")
                    except ValueError:
                        console.print("[red]请输入有效数字[/red]")

            # 计算风险等级
            total_score = sum(answers)
            assessment = questionnaire.calculate_risk_level(total_score)

            console.print("\n[green]风险评估完成！[/green]")
            console.print(f"  总得分: {total_score}")
            console.print(f"  风险等级: {assessment['level']}")
            console.print(f"  风险描述: {assessment['description']}")

        else:
            console.print(f"[red]未知操作: {action}[/red]")
            console.print("支持的操作: show, create, assess")
            raise typer.Exit(1) from None

    except Exception as e:
        console.print(f"[red]用户画像操作失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("recommend")
def ai_recommend(
    fund_code: str = typer.Option(None, "--fund", "-f", help="参考基金代码"),
    top_n: int = typer.Option(5, "--top", "-n", help="推荐数量"),
    strategy: str = typer.Option(
        "hybrid", "--strategy", "-s", help="推荐策略: content/collaborative/hybrid"
    ),
    risk_match: bool = typer.Option(True, "--risk-match/--no-risk-match", help="是否匹配风险偏好"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    个性化基金推荐：基于用户画像和基金特征推荐基金

    示例:
        fund ai recommend                           # 基于用户画像推荐
        fund ai recommend --fund 000001             # 推荐与000001相似的基金
        fund ai recommend --strategy content --top 10
        fund ai recommend --no-risk-match           # 不考虑风险匹配
    """
    from fund_cli.ai.recommender import FundRecommender
    from fund_cli.ai.user_profile import ProfileManager

    try:
        recommender = FundRecommender()
        profile_manager = ProfileManager()

        # 获取用户画像
        profile = profile_manager.get_current_profile()
        if profile is None and risk_match:
            console.print("[yellow]未找到用户画像，使用默认推荐策略[/yellow]")
            risk_match = False

        if fund_code:
            # 基于基金推荐相似基金
            recommendations = recommender.recommend_similar(fund_code, top_n)

            lines = ["# 相似基金推荐\n"]
            lines.append(f"参考基金: {fund_code}")
            lines.append(f"推荐策略: {strategy}")
            lines.append(f"共推荐 {len(recommendations)} 只相似基金：\n")

            for i, rec in enumerate(recommendations, 1):
                lines.append(f"## {i}. {rec.fund_name} ({rec.fund_code})")
                lines.append(f"- 基金类型: {rec.fund_type}")
                lines.append(f"- 相似度: {rec.score:.2%}")
                lines.append(f"- 推荐理由: {rec.recommendation_reason}")
                lines.append("")

        else:
            # 基于用户画像推荐
            if profile is None:
                console.print("[red]请先创建用户画像: fund ai profile create[/red]")
                raise typer.Exit(1) from None

            # 策略映射
            strategy_map = {
                "content": "RISK_MATCHED",
                "collaborative": "SIMILAR",
                "hybrid": "RISK_MATCHED",
            }
            rec_type = strategy_map.get(strategy.lower(), "RISK_MATCHED")
            report = recommender.recommend(profile, top_n, rec_type)

            lines = ["# 个性化基金推荐\n"]
            lines.append(f"用户: {profile.name}")
            lines.append(f"风险等级: {profile.risk_assessment.tolerance.value}")
            lines.append(f"推荐策略: {strategy}")
            lines.append(f"共推荐 {len(report.recommendations)} 只基金：\n")

            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"## {i}. {rec.fund_name} ({rec.fund_code})")
                lines.append(f"- 基金类型: {rec.fund_type}")
                lines.append(f"- 匹配得分: {rec.score:.2f}")
                lines.append(f"- 推荐理由: {rec.recommendation_reason}")
                lines.append("")

        result = "\n".join(lines)
        console.print(Panel(result, title="基金推荐结果", border_style="green"))

        if output:
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]基金推荐失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("advise")
def ai_advise(
    fund_codes: str = typer.Option(None, "--funds", "-f", help="持仓基金代码（逗号分隔）"),
    weights: str = typer.Option(None, "--weights", "-w", help="持仓权重（逗号分隔）"),
    advice_type: str = typer.Option(
        "all", "--type", "-t", help="建议类型: holding/rebalance/dca/risk/all"
    ),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
) -> None:
    """
    智能投资建议：生成持仓分析、调仓建议、定投方案、风险预警

    示例:
        fund ai advise                                    # 综合投资建议
        fund ai advise --funds 000001,000002              # 指定持仓基金
        fund ai advise --funds 000001,000002 --weights 0.6,0.4
        fund ai advise --type rebalance                   # 仅调仓建议
        fund ai advise --type dca                         # 定投方案
    """
    from fund_cli.ai.advisor import InvestmentAdvisor
    from fund_cli.ai.user_profile import ProfileManager

    try:
        advisor = InvestmentAdvisor()
        profile_manager = ProfileManager()

        # 获取用户画像
        profile = profile_manager.get_current_profile()

        # 解析持仓
        codes = []
        weight_list = []
        if fund_codes:
            codes = [c.strip() for c in fund_codes.split(",")]
            if weights:
                weight_list = [float(w.strip()) for w in weights.split(",")]
                if len(weight_list) != len(codes):
                    console.print("[red]权重数量必须与基金数量一致[/red]")
                    raise typer.Exit(1) from None

        # 构建持仓数据
        holdings = []
        if codes:
            for i, code in enumerate(codes):
                weight = weight_list[i] if i < len(weight_list) else 1.0 / len(codes)
                holdings.append({
                    "fund_code": code,
                    "fund_name": f"基金{code}",
                    "value": weight * 1000,  # 模拟持仓价值
                })

        # 生成投资建议
        report = advisor.advise(profile, holdings if holdings else None)

        # 格式化输出
        lines = ["# 智能投资建议\n"]
        lines.append(f"用户ID: {report.user_id}")
        lines.append(f"报告日期: {report.report_date}\n")

        # 综合建议
        lines.append("## 综合建议")
        lines.append(f"- {report.overall_advice}")
        lines.append("")

        # 持仓建议
        if report.advices:
            lines.append("## 持仓建议")
            for advice in report.advices:
                lines.append(f"### {advice.fund_code}")
                lines.append(f"- 建议类型: {advice.advice_type.value}")
                lines.append(f"- 优先级: {advice.priority.value}")
                lines.append(f"- 标题: {advice.title}")
                lines.append(f"- 内容: {advice.content}")
                lines.append("")

        # 调仓建议
        if report.rebalance_suggestions:
            lines.append("## 调仓建议")
            for suggestion in report.rebalance_suggestions:
                lines.append(f"- 操作: {suggestion.suggested_action}")
                lines.append(f"- 理由: {suggestion.reason}")
            lines.append("")

        # 定投建议
        if report.dca_suggestions:
            lines.append("## 定投方案")
            for dca in report.dca_suggestions:
                lines.append(f"### {dca.fund_code}")
                lines.append(f"- 基金名称: {dca.fund_name}")
                lines.append(f"- 频率: {dca.frequency}")
                lines.append(f"- 建议金额: {dca.suggested_amount:.0f}元")
                lines.append(f"- 预期年化: {dca.expected_return:.1f}%")
            lines.append("")

        # 风险预警
        if report.risk_warnings:
            lines.append("## 风险预警")
            for warning in report.risk_warnings:
                lines.append(f"- ⚠️ {warning}")
            lines.append("")

        result = "\n".join(lines)
        console.print(Panel(result, title="智能投资建议", border_style="blue"))

        if output:
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]结果已保存至: {output}[/green]")

    except Exception as e:
        console.print(f"[red]生成投资建议失败: {e}[/red]")
        raise typer.Exit(1) from None


# ============================================
# V3.0 新增命令 - Agent 驱动的智能对话
# ============================================


@app.command("chat")
def ai_chat(
    message: str = typer.Argument(..., help="输入消息"),
    user_id: str = typer.Option("default", "--user", "-u", help="用户标识"),
    thread_id: str = typer.Option(None, "--thread", "-t", help="会话标识（用于多轮对话）"),
) -> None:
    """
    与 AI 助手对话（Agent 驱动，支持工具调用和记忆）

    示例:
        fund ai chat "分析基金000001"
        fund ai chat "对比000001和000002" --user user123
        fund ai chat "刚才分析的基金风险如何？" --thread xxx
    """
    from fund_cli.ai.agent import get_fund_agent

    try:
        agent = get_fund_agent()
        response = agent.invoke(message, user_id, thread_id)
        console.print(Panel(response, title="AI助手", border_style="green"))
    except Exception as e:
        console.print(f"[red]对话失败: {e}[/red]")
        raise typer.Exit(1) from None


@app.command("interactive")
def ai_interactive(
    user_id: str = typer.Option("default", "--user", "-u", help="用户标识"),
) -> None:
    """
    启动交互式 AI 对话模式

    示例:
        fund ai interactive
        fund ai interactive --user user123
    """
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import InMemoryHistory
    except ImportError:
        console.print("[yellow]需要安装 prompt_toolkit: pip install prompt_toolkit[/yellow]")
        console.print("[dim]使用简单的交互模式...[/dim]")
        _simple_interactive(user_id)
        return

    from fund_cli.ai.agent import get_fund_agent

    agent = get_fund_agent()
    session = PromptSession(history=InMemoryHistory())

    console.print(
        Panel(
            "[bold]Fund-CLI AI 交互模式[/bold]\n输入问题与 AI 助手对话，输入 exit 或 quit 退出",
            border_style="blue",
        )
    )

    thread_id = str(uuid.uuid4())

    while True:
        try:
            user_input = session.prompt("AI> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]再见！[/yellow]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            console.print("[yellow]再见！[/yellow]")
            break

        try:
            response = agent.invoke(user_input, user_id, thread_id)
            console.print(Panel(response, title="AI", border_style="green"))
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")


def _simple_interactive(user_id: str) -> None:
    """简单的交互模式（不依赖 prompt_toolkit）"""
    from fund_cli.ai.agent import get_fund_agent

    agent = get_fund_agent()
    thread_id = str(uuid.uuid4())

    console.print(
        Panel(
            "[bold]Fund-CLI AI 交互模式[/bold]\n输入问题与 AI 助手对话，输入 exit 退出",
            border_style="blue",
        )
    )

    while True:
        try:
            user_input = input("AI> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]再见！[/yellow]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            console.print("[yellow]再见！[/yellow]")
            break

        try:
            response = agent.invoke(user_input, user_id, thread_id)
            console.print(Panel(response, title="AI", border_style="green"))
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")


# ============================================
# V2.0 兼容命令 - 保留原有功能
# ============================================


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
    from fund_cli.data.adapters import get_adapter  # type: ignore[attr-defined]

    try:
        # 获取基金数据
        adapter = get_adapter()
        fund_info = adapter.get_fund_info(fund_code)
        nav_data = adapter.get_fund_nav(fund_code, period="1y")

        # 计算业绩指标
        perf_analyzer = PerformanceAnalyzer()
        metrics = perf_analyzer.calculate_metrics(nav_data)  # type: ignore[attr-defined]

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
    from fund_cli.data.adapters import get_adapter  # type: ignore[attr-defined]

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

        portfolio_data: dict[str, Any] = {
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
