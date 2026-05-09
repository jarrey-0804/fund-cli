"""
MCP Server 实现 - 基于 FastMCP 暴露 fund-cli 数据工具

本模块将 fund-cli 的核心数据能力封装为 MCP (Model Context Protocol) 工具，
使外部 AI Agent（如 Claude Desktop、Cursor 等）能够通过 MCP 协议直接调用
基金查询、筛选、组合分析、宏观经济数据等功能。

依赖:
    - mcp (可选): 需要安装 ``pip install mcp``，未安装时调用
      :func:`create_fund_mcp_server` 会抛出 :exc:`ImportError`

工具列表:
    - query_fund: 查询单只基金的基本信息、净值、业绩、持仓
    - screen_funds: 按条件筛选基金（类型、规模、业绩指标等）
    - analyze_portfolio: 分析投资组合的风险收益特征
    - get_macro_data: 获取宏观经济数据（GDP、CPI、PMI、利率等）

使用示例:
    >>> server = create_fund_mcp_server()
    >>> server.run(transport="stdio")
"""

from __future__ import annotations

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise ImportError(
        "mcp 包未安装，请执行: pip install mcp"
    ) from exc

# ============================================
# 延迟初始化 fund-cli 内部模块
# ============================================

_data_manager = None
_analyzer = None


def _get_data_manager():
    """延迟初始化数据管理器（单例模式）。

    Returns:
        DataManager: 数据管理器实例
    """
    global _data_manager
    if _data_manager is None:
        from fund_cli.core.data_manager import DataManager

        _data_manager = DataManager()
    return _data_manager


def _get_adapter():
    """获取当前主数据源适配器。

    Returns:
        DataSourceAdapter: 数据源适配器实例
    """
    return _get_data_manager().get_adapter()


def _get_analyzer():
    """延迟初始化业绩分析器（单例模式）。

    Returns:
        PerformanceAnalyzer: 业绩分析器实例
    """
    global _analyzer
    if _analyzer is None:
        from fund_cli.analysis.performance import PerformanceAnalyzer

        _analyzer = PerformanceAnalyzer()
    return _analyzer


# ============================================
# MCP Server 创建与工具注册
# ============================================


def create_fund_mcp_server(name: str = "fund-cli") -> FastMCP:
    """创建并配置 fund-cli MCP Server 实例。

    将基金查询、筛选、组合分析、宏观经济数据等能力
    注册为 MCP 工具，供 MCP 客户端调用。

    Args:
        name: MCP Server 名称，默认为 ``"fund-cli"``

    Returns:
        FastMCP: 配置完成的 MCP Server 实例

    Raises:
        ImportError: 当 mcp 包未安装时

    使用示例:
        >>> server = create_fund_mcp_server()
        >>> server.run(transport="stdio")
    """
    mcp = FastMCP(name)

    # ------------------------------------------
    # 工具 1: query_fund - 查询基金信息
    # ------------------------------------------
    @mcp.tool()
    def query_fund(
        fund_code: str,
        info_type: str = "basic",
        period: str = "1y",
    ) -> str:
        """查询基金详细信息。

        根据基金代码查询基金的基本信息、净值历史、业绩指标或持仓情况。

        Args:
            fund_code: 6位基金代码，如 "000001"、"110011"
            info_type: 查询类型，可选值:
                - "basic": 基本信息（名称、类型、经理、规模等）
                - "nav": 净值历史数据摘要
                - "performance": 业绩指标（收益率、夏普、回撤等）
                - "holdings": 持仓信息（重仓股、行业分布）
                - "manager": 基金经理信息
                - "all": 以上全部信息
            period: 时间周期，仅对 nav/performance 有效。
                可选 "1m", "3m", "6m", "1y", "3y", "5y"，默认 "1y"

        Returns:
            str: 格式化的基金信息文本
        """
        try:
            adapter = _get_adapter()
            analyzer = _get_analyzer()

            if info_type == "all":
                # 返回全部信息
                parts = []

                # 基本信息
                info = adapter.get_fund_info(fund_code)
                parts.append(
                    f"基金代码: {fund_code}\n"
                    f"基金名称: {info.get('name', '未知')}\n"
                    f"基金类型: {info.get('type', '未知')}\n"
                    f"基金经理: {info.get('manager', '未知')}\n"
                    f"成立日期: {info.get('establish_date', '未知')}\n"
                    f"管理公司: {info.get('company', '未知')}\n"
                    f"基金规模: {info.get('scale', '未知')}"
                )

                # 业绩指标
                nav_data = adapter.get_fund_nav(fund_code, period)
                if nav_data is not None and not (
                    hasattr(nav_data, "empty") and nav_data.empty
                ):
                    metrics = analyzer.calculate_metrics(nav_data)
                    parts.append(
                        f"\n业绩指标 ({period}):\n"
                        f"- 累计收益: {metrics.get('total_return', 0):.2f}%\n"
                        f"- 年化收益(CAGR): {metrics.get('cagr', 0):.2f}%\n"
                        f"- 夏普比率: {metrics.get('sharpe_ratio', 0):.2f}\n"
                        f"- 最大回撤: {metrics.get('max_drawdown', 0):.2f}%\n"
                        f"- 波动率: {metrics.get('volatility', 0):.2f}%"
                    )

                # 持仓信息
                holding = adapter.get_fund_holdings(fund_code)
                if holding:
                    stocks = holding.get("stocks", [])
                    if stocks and hasattr(stocks, "__iter__"):
                        stocks_list = list(stocks)[:5]
                        stocks_text = "\n".join(
                            [
                                f"  {s.get('name', s.get('股票名称', '未知'))}"
                                f"({s.get('code', s.get('股票代码', ''))}): "
                                f"{s.get('ratio', s.get('占净值比例', 0)):.2f}%"
                                for s in stocks_list
                            ]
                        )
                        parts.append(f"\n前5大重仓股:\n{stocks_text}")

                return "\n".join(parts)

            elif info_type == "basic":
                info = adapter.get_fund_info(fund_code)
                return (
                    f"基金代码: {fund_code}\n"
                    f"基金名称: {info.get('name', '未知')}\n"
                    f"基金类型: {info.get('type', '未知')}\n"
                    f"基金经理: {info.get('manager', '未知')}\n"
                    f"成立日期: {info.get('establish_date', '未知')}\n"
                    f"管理公司: {info.get('company', '未知')}\n"
                    f"基金规模: {info.get('scale', '未知')}"
                )

            elif info_type == "nav":
                nav_data = adapter.get_fund_nav(fund_code, period)
                if nav_data is None or (
                    hasattr(nav_data, "empty") and nav_data.empty
                ):
                    return f"未找到基金 {fund_code} 在 {period} 期间的净值数据"

                latest = nav_data.iloc[-1]
                earliest = nav_data.iloc[0]
                count = len(nav_data)
                latest_nav = latest.get("unit_nav", latest.get("净值", "N/A"))
                earliest_nav = earliest.get("unit_nav", earliest.get("净值", "N/A"))

                return (
                    f"基金 {fund_code} 净值历史 ({period}):\n"
                    f"- 数据条数: {count} 条\n"
                    f"- 最新净值: {latest_nav}\n"
                    f"- 期初净值: {earliest_nav}\n"
                    f"- 净值变化: {float(latest_nav) - float(earliest_nav):.4f} (估算)"
                )

            elif info_type == "performance":
                nav_data = adapter.get_fund_nav(fund_code, period)
                if nav_data is None or (
                    hasattr(nav_data, "empty") and nav_data.empty
                ):
                    return f"未找到基金 {fund_code} 在 {period} 期间的净值数据"

                metrics = analyzer.calculate_metrics(nav_data)
                return (
                    f"基金 {fund_code} {period} 业绩表现:\n"
                    f"- 累计收益: {metrics.get('total_return', 0):.2f}%\n"
                    f"- 年化收益(CAGR): {metrics.get('cagr', 0):.2f}%\n"
                    f"- 夏普比率: {metrics.get('sharpe_ratio', 0):.2f}\n"
                    f"- 最大回撤: {metrics.get('max_drawdown', 0):.2f}%\n"
                    f"- 波动率: {metrics.get('volatility', 0):.2f}%\n"
                    f"- 索提诺比率: {metrics.get('sortino_ratio', 0):.2f}"
                )

            elif info_type == "holdings":
                holding = adapter.get_fund_holdings(fund_code)
                if not holding:
                    return f"未找到基金 {fund_code} 的持仓数据"

                stocks = holding.get("stocks", [])
                if stocks and hasattr(stocks, "__iter__"):
                    stocks_list = list(stocks)[:10]
                    stocks_text = "\n".join(
                        [
                            f"  {i+1}. {s.get('name', s.get('股票名称', '未知'))}"
                            f"({s.get('code', s.get('股票代码', ''))}): "
                            f"{s.get('ratio', s.get('占净值比例', 0)):.2f}%"
                            for i, s in enumerate(stocks_list)
                        ]
                    )
                else:
                    stocks_text = "暂无股票持仓数据"

                industries = holding.get("industries", {})
                if industries:
                    industries_text = "\n".join(
                        [
                            f"  {name}: {ratio:.2f}%"
                            for name, ratio in sorted(
                                industries.items(), key=lambda x: x[1], reverse=True
                            )[:5]
                        ]
                    )
                else:
                    industries_text = "暂无行业分布数据"

                return (
                    f"基金 {fund_code} 持仓情况:\n\n"
                    f"前10大重仓股:\n{stocks_text}\n\n"
                    f"行业分布(前5):\n{industries_text}"
                )

            elif info_type == "manager":
                manager = adapter.get_fund_manager(fund_code)
                if not manager:
                    return f"未找到基金 {fund_code} 的经理信息"

                return (
                    f"基金经理信息:\n"
                    f"- 姓名: {manager.get('name', manager.get('姓名', '未知'))}\n"
                    f"- 任职日期: {manager.get('appointment_date', manager.get('任职日期', '未知'))}\n"
                    f"- 从业年限: {manager.get('experience_years', manager.get('从业年限', '未知'))}年\n"
                    f"- 管理规模: {manager.get('managed_scale', manager.get('管理规模', '未知'))}\n"
                    f"- 管理基金数: {manager.get('fund_count', manager.get('管理基金数', '未知'))}只"
                )

            else:
                return f"不支持的查询类型: {info_type}，可选: basic, nav, performance, holdings, manager, all"

        except Exception as e:
            return f"查询基金失败: {str(e)}"

    # ------------------------------------------
    # 工具 2: screen_funds - 基金筛选
    # ------------------------------------------
    @mcp.tool()
    def screen_funds(
        fund_type: str | None = None,
        keyword: str | None = None,
        min_scale: float | None = None,
        max_scale: float | None = None,
        min_return_1y: float | None = None,
        max_drawdown: float | None = None,
        min_sharpe: float | None = None,
        sort_by: str | None = None,
        limit: int = 10,
    ) -> str:
        """按多维度条件筛选基金。

        支持按基金类型、关键词、规模、业绩指标等条件筛选基金，
        并可指定排序方式和返回数量。

        Args:
            fund_type: 基金类型，可选 "股票型", "债券型", "混合型", "指数型", "QDII", "货币型" 等
            keyword: 关键词，匹配基金名称或代码
            min_scale: 最小基金规模（亿元）
            max_scale: 最大基金规模（亿元）
            min_return_1y: 最小近1年年化收益率（%）
            max_drawdown: 最大回撤上限（%），如 -20 表示回撤不超过20%
            min_sharpe: 最小夏普比率
            sort_by: 排序字段，如 "return_1y", "sharpe_ratio", "scale"
            limit: 返回结果数量上限，默认 10

        Returns:
            str: 格式化的筛选结果文本
        """
        try:
            dm = _get_data_manager()

            # 基础搜索
            funds_df = dm.search_funds(
                fund_type=fund_type,
                keyword=keyword,
                min_scale=min_scale,
                max_scale=max_scale,
                limit=limit * 3,  # 多取一些用于后续过滤
            )

            if funds_df is None or (
                hasattr(funds_df, "empty") and funds_df.empty
            ):
                return "未找到符合条件的基金"

            # 业绩指标过滤（如果提供了相关条件）
            if min_return_1y is not None or max_drawdown is not None or min_sharpe is not None:
                analyzer = _get_analyzer()
                filtered_results = []

                # 限制扫描数量避免超时
                scan_codes = []
                if hasattr(funds_df, "iterrows"):
                    for _, row in funds_df.iterrows():
                        code = row.get("code", row.get("基金代码", ""))
                        if code:
                            scan_codes.append(str(code))
                else:
                    scan_codes = [str(f.get("code", "")) for f in funds_df]

                for code in scan_codes[:50]:
                    try:
                        nav_data = dm.get_fund_nav(code, "1y")
                        if nav_data is None or (
                            hasattr(nav_data, "empty") and nav_data.empty
                        ):
                            continue

                        metrics = analyzer.calculate_metrics(nav_data)

                        if min_return_1y is not None and metrics.get("cagr", 0) < min_return_1y:
                            continue
                        if max_drawdown is not None and abs(metrics.get("max_drawdown", 0)) > abs(max_drawdown):
                            continue
                        if min_sharpe is not None and metrics.get("sharpe_ratio", 0) < min_sharpe:
                            continue

                        info = dm.get_fund_info(code)
                        filtered_results.append(
                            {
                                "code": code,
                                "name": info.get("name", "未知"),
                                "type": info.get("type", "未知"),
                                "return": metrics.get("cagr", 0),
                                "drawdown": metrics.get("max_drawdown", 0),
                                "sharpe": metrics.get("sharpe_ratio", 0),
                            }
                        )

                        if len(filtered_results) >= limit:
                            break
                    except Exception:
                        continue

                if not filtered_results:
                    return "未找到符合条件的基金（业绩指标筛选后无结果）"

                # 排序
                if sort_by == "return_1y":
                    filtered_results.sort(key=lambda x: x["return"], reverse=True)
                elif sort_by == "sharpe_ratio":
                    filtered_results.sort(key=lambda x: x["sharpe"], reverse=True)
                elif sort_by == "max_drawdown":
                    filtered_results.sort(key=lambda x: x["drawdown"], reverse=True)

                funds_text = "\n".join(
                    [
                        f"{r['code']}: {r['name']} ({r['type']})\n"
                        f"  年化收益: {r['return']:.2f}%, "
                        f"最大回撤: {r['drawdown']:.2f}%, "
                        f"夏普: {r['sharpe']:.2f}"
                        for r in filtered_results[:limit]
                    ]
                )
                return f"筛选结果 (共{len(filtered_results)}只):\n{funds_text}"

            # 无业绩条件，直接返回搜索结果
            results = []
            if hasattr(funds_df, "iterrows"):
                for _, row in funds_df.iterrows():
                    results.append(
                        {
                            "code": row.get("code", row.get("基金代码", "")),
                            "name": row.get("name", row.get("基金简称", "")),
                            "type": row.get("type", row.get("基金类型", "未知类型")),
                            "scale": row.get("scale", row.get("基金规模", "未知")),
                        }
                    )
            else:
                results = [
                    {
                        "code": f.get("code", ""),
                        "name": f.get("name", ""),
                        "type": f.get("type", "未知类型"),
                        "scale": f.get("scale", "未知"),
                    }
                    for f in funds_df
                ]

            funds_text = "\n".join(
                [
                    f"{r['code']}: {r['name']} ({r['type']}, 规模{r['scale']})"
                    for r in results[:limit]
                ]
            )
            total = len(results)
            return f"找到 {total} 只基金 (显示前{min(limit, total)}只):\n{funds_text}"

        except Exception as e:
            return f"筛选基金失败: {str(e)}"

    # ------------------------------------------
    # 工具 3: analyze_portfolio - 组合分析
    # ------------------------------------------
    @mcp.tool()
    def analyze_portfolio(
        fund_codes: str,
        weights: str | None = None,
        risk_free_rate: float = 0.03,
    ) -> str:
        """分析投资组合的风险收益特征。

        对多只基金组成的投资组合进行综合分析，包括预期收益、
        波动率、夏普比率、最大回撤和分散度评估。

        Args:
            fund_codes: 基金代码列表，逗号分隔，如 "000001,110011,519736"
            weights: 各基金权重列表，逗号分隔，如 "0.5,0.3,0.2"。
                不传则使用等权重分配。权重会自动归一化。
            risk_free_rate: 无风险利率（用于计算夏普比率），默认 0.03（3%）

        Returns:
            str: 格式化的组合分析报告文本
        """
        try:
            codes = [c.strip() for c in fund_codes.split(",")]

            if len(codes) < 2:
                return "组合分析需要至少 2 只基金"

            # 解析权重
            if weights:
                weight_list = [float(w.strip()) for w in weights.split(",")]
                total = sum(weight_list)
                weight_list = [w / total for w in weight_list]
            else:
                weight_list = [1.0 / len(codes)] * len(codes)

            if len(codes) != len(weight_list):
                return "权重数量与基金数量不匹配"

            dm = _get_data_manager()
            analyzer = _get_analyzer()

            # 获取各基金数据
            fund_data: list[dict] = []
            for i, code in enumerate(codes):
                try:
                    nav = dm.get_fund_nav(code, "1y")
                    info = dm.get_fund_info(code)
                    if nav is not None and not (
                        hasattr(nav, "empty") and nav.empty
                    ):
                        metrics = analyzer.calculate_metrics(nav)
                        fund_data.append(
                            {
                                "code": code,
                                "name": info.get("name", "未知"),
                                "weight": weight_list[i],
                                "cagr": metrics.get("cagr", 0),
                                "volatility": metrics.get("volatility", 0),
                                "sharpe": metrics.get("sharpe_ratio", 0),
                                "max_drawdown": metrics.get("max_drawdown", 0),
                            }
                        )
                except Exception:
                    continue

            if len(fund_data) < 2:
                return "需要至少 2 只有效基金进行分析"

            # 计算组合指标
            portfolio_return = sum(f["weight"] * f["cagr"] for f in fund_data)
            portfolio_volatility = sum(f["weight"] * f["volatility"] for f in fund_data)
            portfolio_sharpe = (
                (portfolio_return - risk_free_rate * 100) / portfolio_volatility
                if portfolio_volatility > 0
                else 0
            )
            max_drawdown = max(f["max_drawdown"] for f in fund_data)

            # 分散度评分（基于权重均匀度）
            n = len(fund_data)
            ideal_weight = 1.0 / n
            weight_variance = sum(
                (f["weight"] - ideal_weight) ** 2 for f in fund_data
            ) / n
            diversification_score = max(1, min(10, int(10 - weight_variance * 100)))

            # 配置建议
            if portfolio_sharpe > 1.0:
                suggestion = "组合配置优秀，风险调整后收益良好"
            elif portfolio_sharpe > 0.5:
                suggestion = "组合配置合理，可考虑优化权重"
            else:
                suggestion = "组合风险较高，建议调整配置或降低仓位"

            holdings_text = "\n".join(
                [
                    f"- {f['code']} ({f['name']}): {f['weight']*100:.1f}% "
                    f"(收益{f['cagr']:.1f}%, 波动{f['volatility']:.1f}%)"
                    for f in fund_data
                ]
            )

            return (
                f"投资组合分析:\n\n"
                f"基金配置:\n{holdings_text}\n\n"
                f"风险收益指标:\n"
                f"- 预期年化收益: {portfolio_return:.2f}%\n"
                f"- 预期波动率: {portfolio_volatility:.2f}%\n"
                f"- 组合夏普比率: {portfolio_sharpe:.2f}\n"
                f"- 最大回撤: {max_drawdown:.2f}%\n"
                f"- 无风险利率: {risk_free_rate*100:.1f}%\n\n"
                f"评估:\n"
                f"- 分散度评分: {diversification_score}/10\n"
                f"- 配置建议: {suggestion}\n\n"
                f"风险提示: 以上分析基于历史数据，不构成投资建议。"
            )

        except Exception as e:
            return f"组合分析失败: {str(e)}"

    # ------------------------------------------
    # 工具 4: get_macro_data - 宏观经济数据
    # ------------------------------------------
    @mcp.tool()
    def get_macro_data(
        data_type: str = "gdp",
        period: str | None = None,
    ) -> str:
        """获取宏观经济数据。

        提供中国宏观经济核心指标数据，包括 GDP、CPI、PPI、PMI、
        利率、货币供应、社会融资等。

        Args:
            data_type: 数据类型，可选值:
                - "gdp": GDP 数据（年率/季度）
                - "cpi": CPI 居民消费价格指数
                - "ppi": PPI 工业生产者出厂价格指数
                - "pmi": PMI 制造业采购经理指数（官方+财新）
                - "interest_rate": 央行利率决议
                - "m2": M2 货币供应量
                - "lpr": LPR 贷款市场报价利率
                - "social_financing": 社会融资规模增量
                - "trade": 进出口贸易数据
                - "shibor": SHIBOR 上海银行间同业拆放利率
                - "fund_flow": 大盘资金流向
                - "north_flow": 北向资金流向
            period: 时间周期（部分数据类型支持），如 "yearly", "monthly"

        Returns:
            str: 格式化的宏观经济数据文本
        """
        try:
            dm = _get_data_manager()

            data_type = data_type.lower().strip()

            if data_type == "gdp":
                if period == "quarterly":
                    df = dm.get_gdp_quarterly()
                else:
                    df = dm.get_gdp_yearly()

            elif data_type == "cpi":
                if period == "monthly":
                    df = dm.get_cpi_monthly()
                else:
                    df = dm.get_cpi_yearly()

            elif data_type == "ppi":
                if period == "monthly":
                    df = dm.get_ppi_monthly()
                else:
                    df = dm.get_ppi_yearly()

            elif data_type == "pmi":
                # 返回官方+财新 PMI
                df_official = dm.get_pmi_official()
                df_caixin = dm.get_pmi_caixin()

                result_parts = ["宏观经济数据 - PMI:"]
                if df_official is not None and not (
                    hasattr(df_official, "empty") and df_official.empty
                ):
                    result_parts.append(
                        f"\n官方制造业PMI (最近5期):\n"
                        f"{df_official.tail(5).to_string(index=False)}"
                    )
                if df_caixin is not None and not (
                    hasattr(df_caixin, "empty") and df_caixin.empty
                ):
                    result_parts.append(
                        f"\n财新制造业PMI (最近5期):\n"
                        f"{df_caixin.tail(5).to_string(index=False)}"
                    )
                return "\n".join(result_parts)

            elif data_type == "interest_rate":
                df = dm.get_china_interest_rate()

            elif data_type == "m2":
                df = dm.get_m2_yearly()

            elif data_type == "lpr":
                df = dm.get_lpr_data()

            elif data_type == "social_financing":
                df = dm.get_social_financing()

            elif data_type == "trade":
                # 返回进出口数据
                df_exports = dm.get_exports_yearly()
                df_imports = dm.get_imports_yearly()
                df_balance = dm.get_trade_balance()

                result_parts = ["宏观经济数据 - 进出口贸易:"]
                for label, df_item in [
                    ("出口年率", df_exports),
                    ("进口年率", df_imports),
                    ("贸易帐", df_balance),
                ]:
                    if df_item is not None and not (
                        hasattr(df_item, "empty") and df_item.empty
                    ):
                        result_parts.append(
                            f"\n{label} (最近5期):\n"
                            f"{df_item.tail(5).to_string(index=False)}"
                        )
                return "\n".join(result_parts)

            elif data_type == "shibor":
                df = dm.get_shibor()

            elif data_type == "fund_flow":
                df = dm.get_market_fund_flow()

            elif data_type == "north_flow":
                df = dm.get_north_fund_flow()

            else:
                supported = (
                    "gdp, cpi, ppi, pmi, interest_rate, m2, lpr, "
                    "social_financing, trade, shibor, fund_flow, north_flow"
                )
                return f"不支持的数据类型: {data_type}\n支持的数据类型: {supported}"

            # 通用 DataFrame 输出处理
            if df is None or (hasattr(df, "empty") and df.empty):
                return f"未获取到 {data_type} 类型的宏观经济数据"

            label_map = {
                "gdp": "GDP",
                "cpi": "CPI",
                "ppi": "PPI",
                "interest_rate": "央行利率",
                "m2": "M2货币供应",
                "lpr": "LPR利率",
                "social_financing": "社融规模",
                "shibor": "SHIBOR利率",
                "fund_flow": "大盘资金流向",
                "north_flow": "北向资金流向",
            }
            label = label_map.get(data_type, data_type)

            return (
                f"宏观经济数据 - {label} (最近5期):\n"
                f"{df.tail(5).to_string(index=False)}"
            )

        except Exception as e:
            return f"获取宏观经济数据失败: {str(e)}"

    return mcp
