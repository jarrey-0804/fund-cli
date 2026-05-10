"""
AI 工具定义

使用 LangChain @tool 装饰器定义 fund-cli 数据接口工具，
让 AI Agent 能够自主调用数据接口获取实时数据。
"""

from __future__ import annotations

from datetime import date, timedelta

from langchain_core.tools import tool

from fund_cli.analysis.performance import PerformanceAnalyzer
from fund_cli.core.data_manager import DataManager

# 全局实例（延迟初始化）
_data_manager = None
_analyzer = None


def _get_data_manager():
    """延迟初始化数据管理器"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager


def _get_adapter():
    """获取数据适配器"""
    return _get_data_manager().get_adapter()


def _get_analyzer():
    """延迟初始化业绩分析器"""
    global _analyzer
    if _analyzer is None:
        _analyzer = PerformanceAnalyzer()
    return _analyzer


def _period_to_dates(period: str) -> tuple[date | None, date | None]:
    """将周期字符串转换为起止日期。

    Args:
        period: 周期，如 1m, 3m, 6m, 1y, 3y, 5y, ytd

    Returns:
        (start_date, end_date) 元组，end_date 始终为 None（使用 API 默认值）
    """
    period_map = {
        "1m": 30,
        "3m": 90,
        "6m": 180,
        "1y": 365,
        "3y": 1095,
        "5y": 1825,
    }

    if period == "ytd":
        start_date = date(date.today().year, 1, 1)
        return (start_date, None)

    days = period_map.get(period, 365)
    start_date = date.today() - timedelta(days=days)
    return (start_date, None)


# ============================================
# 基金基础信息工具
# ============================================


@tool
def get_fund_basic_info(fund_code: str) -> str:
    """获取基金基本信息，包括名称、类型、经理、成立日期、规模等，以及同花顺基金信息和基金概览。

    Args:
        fund_code: 6位基金代码，如 "000001"

    Returns:
        基金基本信息文本
    """
    try:
        adapter = _get_adapter()
        info = adapter.get_fund_info(fund_code)
        output = f"""基金代码: {fund_code}
基金名称: {info.get("name") or info.get("基金简称") or "未知"}
基金类型: {info.get("type") or info.get("基金类型") or "未知"}
基金经理: {info.get("manager") or info.get("基金经理") or "未知"}
成立日期: {info.get("establish_date") or info.get("成立日期") or "未知"}
管理公司: {info.get("company") or info.get("管理公司") or "未知"}
基金规模: {info.get("scale") or info.get("基金规模") or "未知"}""".strip()

        # 同花顺基金信息
        try:
            ths_info = adapter.get_fund_info_ths(fund_code)
            if ths_info and isinstance(ths_info, dict):
                ths_items = []
                for k, v in ths_info.items():
                    if v is not None and str(v) not in ("nan", "None", ""):
                        ths_items.append(f"  {k}: {v}")
                if ths_items:
                    output += "\n\n同花顺基金信息:\n" + "\n".join(ths_items)
        except Exception:
            pass

        # 基金概览
        try:
            overview = adapter.get_fund_overview(fund_code)
            if overview and isinstance(overview, dict):
                ov_items = []
                for k, v in overview.items():
                    if v is not None and str(v) not in ("nan", "None", ""):
                        ov_items.append(f"  {k}: {v}")
                if ov_items:
                    output += "\n\n基金概览:\n" + "\n".join(ov_items)
        except Exception:
            pass

        return output
    except Exception as e:
        return f"获取基金信息失败: {str(e)}"


@tool
def get_fund_nav_history(fund_code: str, period: str = "1y") -> str:
    """获取基金净值历史数据。

    Args:
        fund_code: 6位基金代码
        period: 时间周期，可选 1m(1月), 3m(3月), 6m(6月), 1y(1年), 3y(3年), 5y(5年), ytd(年初至今)

    Returns:
        净值历史摘要
    """
    try:
        adapter = _get_adapter()
        start_date, end_date = _period_to_dates(period)
        nav_data = adapter.get_fund_nav(fund_code, start_date=start_date, end_date=end_date)

        if nav_data is None or (hasattr(nav_data, "empty") and nav_data.empty):
            return f"未找到基金 {fund_code} 在 {period} 期间的净值数据"

        # 获取最新和最早净值
        if hasattr(nav_data, "iloc"):
            latest = nav_data.iloc[-1]
            earliest = nav_data.iloc[0]
            count = len(nav_data)
        else:
            return f"获取到 {len(nav_data)} 条净值记录"

        latest_nav = latest.get("unit_nav", latest.get("净值", "N/A"))
        earliest_nav = earliest.get("unit_nav", earliest.get("净值", "N/A"))

        return f"""基金 {fund_code} 净值历史 ({period}):
- 数据条数: {count} 条
- 最新净值: {latest_nav}
- 期初净值: {earliest_nav}
- 净值变化: {float(latest_nav) - float(earliest_nav):.4f} (估算)""".strip()
    except Exception as e:
        return f"获取净值数据失败: {str(e)}"


@tool
def get_fund_performance(fund_code: str, period: str = "1y") -> str:
    """获取基金业绩指标，包括收益率、夏普比率、最大回撤、波动率等。

    Args:
        fund_code: 6位基金代码
        period: 时间周期，可选 1m, 3m, 6m, 1y, 3y, 5y

    Returns:
        基金业绩指标文本
    """
    try:
        adapter = _get_adapter()
        analyzer = _get_analyzer()

        start_date, end_date = _period_to_dates(period)
        nav_data = adapter.get_fund_nav(fund_code, start_date=start_date, end_date=end_date)

        if nav_data is None or (hasattr(nav_data, "empty") and nav_data.empty):
            return f"未找到基金 {fund_code} 在 {period} 期间的净值数据"

        metrics = analyzer.calculate_metrics(nav_data)

        return f"""基金 {fund_code} {period} 业绩表现:
- 累计收益: {metrics.get("total_return", 0):.2f}%
- 年化收益(CAGR): {metrics.get("cagr", 0):.2f}%
- 夏普比率: {metrics.get("sharpe_ratio", 0):.2f}
- 最大回撤: {metrics.get("max_drawdown", 0):.2f}%
- 波动率: {metrics.get("volatility", 0):.2f}%
- 索提诺比率: {metrics.get("sortino_ratio", 0):.2f}""".strip()
    except Exception as e:
        return f"获取业绩数据失败: {str(e)}"


@tool
def get_fund_holdings(fund_code: str, top_n: int = 10) -> str:
    """获取基金持仓信息，包括前N大重仓股及行业分布。

    Args:
        fund_code: 6位基金代码
        top_n: 返回前N大持仓，默认10

    Returns:
        基金持仓信息文本
    """
    try:
        adapter = _get_adapter()
        holding = adapter.get_fund_holdings(fund_code)

        if holding is None or (hasattr(holding, "empty") and holding.empty):
            return f"未找到基金 {fund_code} 的持仓数据"

        # 适配 DataFrame 格式（API 返回 DataFrame，含 stock_code/stock_name/weight 列）
        stocks = []
        if hasattr(holding, "iterrows"):
            for _, row in holding.head(top_n).iterrows():
                stocks.append(
                    {
                        "name": row.get("stock_name", row.get("股票名称", "未知")),
                        "code": row.get("stock_code", row.get("股票代码", "")),
                        "ratio": float(row.get("weight", row.get("占净值比例", 0))),
                    }
                )

        if stocks:
            stocks_text = "\n".join(
                [
                    f"  {i + 1}. {s['name']}({s['code']}): {s['ratio']:.2f}%"
                    for i, s in enumerate(stocks)
                ]
            )
        else:
            stocks_text = "暂无股票持仓数据"

        # 行业分布暂不可用（API 未返回行业数据）
        industries_text = "暂无行业分布数据"

        return f"""基金 {fund_code} 持仓情况:

前{top_n}大重仓股:
{stocks_text}

行业分布:
{industries_text}""".strip()
    except Exception as e:
        return f"获取持仓数据失败: {str(e)}"


@tool
def get_fund_manager(fund_code: str) -> str:
    """获取基金经理信息，包括经理履历、管理规模、业绩等。

    Args:
        fund_code: 6位基金代码

    Returns:
        基金经理信息文本
    """
    try:
        adapter = _get_adapter()
        manager = adapter.get_fund_manager(fund_code)

        if not manager:
            return f"未找到基金 {fund_code} 的经理信息"

        return f"""基金经理信息:
- 姓名: {manager.get("name", manager.get("姓名", "未知"))}
- 任职日期: {manager.get("appointment_date", manager.get("任职日期", "未知"))}
- 从业年限: {manager.get("experience_years", manager.get("从业年限", "未知"))}年
- 管理规模: {manager.get("managed_scale", manager.get("管理规模", "未知"))}
- 管理基金数: {manager.get("fund_count", manager.get("管理基金数", "未知"))}只""".strip()
    except Exception as e:
        return f"获取经理信息失败: {str(e)}"


# ============================================
# 基金筛选工具
# ============================================


@tool
def search_funds(
    fund_type: str | None = None,
    keyword: str | None = None,
    min_scale: float | None = None,
    max_scale: float | None = None,
    limit: int = 10,
) -> str:
    """搜索/筛选基金，支持按类型、关键词、规模筛选。

    Args:
        fund_type: 基金类型，如 "股票型", "债券型", "混合型", "指数型"
        keyword: 关键词，匹配基金名称或代码
        min_scale: 最小规模(亿元)
        max_scale: 最大规模(亿元)
        limit: 返回结果数量，默认10

    Returns:
        基金列表文本
    """
    try:
        adapter = _get_adapter()
        funds = adapter.search_funds(
            fund_type=fund_type,
            keyword=keyword,
            min_scale=min_scale,
            max_scale=max_scale,
            limit=limit,
        )

        if not funds:
            return "未找到符合条件的基金"

        if hasattr(funds, "iterrows"):
            # DataFrame 格式
            funds_list = []
            for _, row in funds.iterrows():
                funds_list.append(
                    f"{row.get('code', row.get('基金代码', ''))}: {row.get('name', row.get('基金简称', ''))} "
                    f"({row.get('type', row.get('基金类型', '未知类型'))}, 规模{row.get('scale', row.get('基金规模', '未知'))})"
                )
            funds_text = "\n".join(funds_list[:limit])
        else:
            # 列表格式
            funds_text = "\n".join(
                [
                    f"{f.get('code', '')}: {f.get('name', '')} ({f.get('type', '未知类型')}, 规模{f.get('scale', '未知')})"
                    for f in funds[:limit]
                ]
            )

        return f"找到 {len(funds) if hasattr(funds, '__len__') else limit} 只基金:\n{funds_text}"
    except Exception as e:
        return f"搜索基金失败: {str(e)}"


# ============================================
# 市场数据工具
# ============================================


@tool
def get_market_index(index_code: str = "000001.SH") -> str:
    """获取市场指数数据，如上证指数、深证成指等。

    Args:
        index_code: 指数代码，如 "000001.SH"(上证指数), "399001.SZ"(深证成指),
                   "000300.SH"(沪深300), "000905.SH"(中证500)

    Returns:
        指数数据文本
    """
    try:
        adapter = _get_adapter()
        start_date, end_date = _period_to_dates("1m")
        data = adapter.get_benchmark_nav(index_code, start_date=start_date, end_date=end_date)

        if data is None or (hasattr(data, "empty") and data.empty):
            return f"未找到指数 {index_code} 的数据"

        if hasattr(data, "iloc"):
            latest = data.iloc[-1]
            prev = data.iloc[-2] if len(data) > 1 else latest

            latest_close = latest.get("close", latest.get("收盘价", 0))
            prev_close = prev.get("close", prev.get("收盘价", latest_close))
            change = float(latest_close) - float(prev_close)
            change_pct = (change / float(prev_close)) * 100 if float(prev_close) != 0 else 0

            return f"""指数 {index_code} 行情:
- 最新点位: {latest_close:.2f}
- 涨跌: {change:+.2f} ({change_pct:+.2f}%)
- 日期: {latest.name if hasattr(latest, "name") else "最新"}""".strip()

        return f"获取到指数 {index_code} 的数据"
    except Exception as e:
        return f"获取指数数据失败: {str(e)}"


@tool
def get_etf_spot() -> str:
    """获取ETF实时行情数据。

    Returns:
        热门ETF实时行情
    """
    try:
        adapter = _get_adapter()
        etfs = adapter.get_etf_spot()

        if etfs is None or (hasattr(etfs, "empty") and etfs.empty):
            return "暂无ETF实时数据"

        if hasattr(etfs, "head"):
            top_etfs = etfs.head(10)
            etf_text = "\n".join(
                [
                    f"{row.get('代码', row.get('code', ''))}: {row.get('名称', row.get('name', ''))} - "
                    f"现价{row.get('最新价', row.get('close', 'N/A'))}, "
                    f"涨跌{row.get('涨跌幅', row.get('change_pct', 'N/A'))}"
                    for _, row in top_etfs.iterrows()
                ]
            )
        else:
            etf_text = "ETF数据格式不支持"

        return f"ETF 实时行情 (前10):\n{etf_text}"
    except Exception as e:
        return f"获取ETF行情失败: {str(e)}"


# ============================================
# 组合分析工具
# ============================================


@tool
def compare_funds(fund_codes: str) -> str:
    """对比多只基金的业绩表现。

    Args:
        fund_codes: 基金代码列表，逗号分隔，如 "000001,000002,000003"

    Returns:
        基金对比分析文本
    """
    try:
        codes = [c.strip() for c in fund_codes.split(",")]
        adapter = _get_adapter()
        analyzer = _get_analyzer()

        start_date, end_date = _period_to_dates("1y")

        results = []
        for code in codes:
            try:
                info = adapter.get_fund_info(code)
                nav_data = adapter.get_fund_nav(code, start_date=start_date, end_date=end_date)

                if nav_data is not None and not (hasattr(nav_data, "empty") and nav_data.empty):
                    metrics = analyzer.calculate_metrics(nav_data)
                else:
                    metrics = {}

                results.append(
                    {
                        "code": code,
                        "name": info.get("name") or info.get("基金简称") or "未知",
                        "return": metrics.get("cagr", 0),
                        "sharpe": metrics.get("sharpe_ratio", 0),
                        "drawdown": metrics.get("max_drawdown", 0),
                    }
                )
            except Exception:
                results.append(
                    {"code": code, "name": "获取失败", "return": 0, "sharpe": 0, "drawdown": 0}
                )

        if not results:
            return "无法获取对比数据"

        # 按收益排序
        results.sort(key=lambda x: x["return"], reverse=True)

        comparison_text = "\n".join(
            [
                f"{r['code']}: {r['name']}\n"
                f"  年化收益: {r['return']:.2f}%, 夏普: {r['sharpe']:.2f}, 最大回撤: {r['drawdown']:.2f}%"
                for r in results
            ]
        )

        return f"基金对比分析:\n{comparison_text}"
    except Exception as e:
        return f"对比基金失败: {str(e)}"


@tool
def analyze_investment_advice(fund_code: str, risk_profile: str = "moderate") -> str:
    """根据基金表现和用户风险偏好给出投资建议。

    Args:
        fund_code: 6位基金代码
        risk_profile: 风险偏好，可选 conservative(保守), moderate(稳健), aggressive(激进)

    Returns:
        投资建议文本
    """
    try:
        adapter = _get_adapter()
        analyzer = _get_analyzer()

        info = adapter.get_fund_info(fund_code)
        start_date, end_date = _period_to_dates("1y")
        nav_data = adapter.get_fund_nav(fund_code, start_date=start_date, end_date=end_date)

        if nav_data is None or (hasattr(nav_data, "empty") and nav_data.empty):
            return f"无法获取基金 {fund_code} 的数据进行分析"

        metrics = analyzer.calculate_metrics(nav_data)

        # 基于指标和风险偏好给出建议
        sharpe = metrics.get("sharpe_ratio", 0)
        drawdown = metrics.get("max_drawdown", 0)
        cagr = metrics.get("cagr", 0)
        fund_type = info.get("type") or info.get("基金类型") or "未知"
        fund_name = info.get("name") or info.get("基金简称") or "未知"

        # 简单的建议逻辑
        if sharpe > 1.0:
            risk_adj = "风险调整后收益优秀"
        elif sharpe > 0.5:
            risk_adj = "风险调整后收益良好"
        else:
            risk_adj = "风险调整后收益一般"

        if risk_profile == "conservative":
            if drawdown > 20:
                suitability = "不太适合保守型投资者"
            else:
                suitability = "可考虑少量配置"
        elif risk_profile == "aggressive":
            suitability = "适合激进型投资者"
        else:
            suitability = "适合稳健型投资者"

        return f"""基金 {fund_code} ({fund_name}) 投资建议:

基本信息:
- 基金类型: {fund_type}
- 年化收益: {cagr:.2f}%
- 最大回撤: {drawdown:.2f}%
- 夏普比率: {sharpe:.2f}

分析结论:
- {risk_adj}
- {suitability}

风险提示: 投资有风险，本建议仅供参考，不构成投资决策依据。""".strip()
    except Exception as e:
        return f"分析失败: {str(e)}"


# ============================================
# 业绩筛选工具
# ============================================


@tool
def filter_funds_by_performance(
    min_return_1y: float | None = None,
    max_drawdown: float | None = None,
    min_sharpe: float | None = None,
    fund_type: str | None = None,
    limit: int = 10,
) -> str:
    """按业绩指标筛选基金。

    Args:
        min_return_1y: 最小年化收益率(%)
        max_drawdown: 最大回撤上限(%)
        min_sharpe: 最小夏普比率
        fund_type: 基金类型筛选
        limit: 返回结果数量

    Returns:
        符合条件的基金列表
    """
    try:
        data_manager = _get_data_manager()
        adapter = _get_adapter()

        # 获取基金列表
        try:
            all_funds = data_manager.get_fund_list(fund_type)
        except Exception:
            try:
                all_funds = adapter.get_fund_list(fund_type)
            except Exception:
                return "无法获取基金列表"

        if all_funds is None or (hasattr(all_funds, "empty") and all_funds.empty):
            return "未找到基金数据"

        # 从 DataFrame 中正确提取基金代码列表
        if hasattr(all_funds, "columns"):
            code_col = None
            for col_name in ["基金代码", "code", "fund_code", "基金代号"]:
                if col_name in all_funds.columns:
                    code_col = col_name
                    break
            if code_col is None:
                code_col = all_funds.columns[0]
            fund_codes = all_funds[code_col].head(50).astype(str).tolist()
        else:
            fund_codes = list(all_funds)[:50]

        results = []
        analyzer = _get_analyzer()
        start_date, end_date = _period_to_dates("1y")

        for fund_code in fund_codes:
            try:
                code = str(fund_code).strip()
                if not code.isdigit() or len(code) != 6:
                    continue

                nav_data = data_manager.get_fund_nav(code, start_date=start_date, end_date=end_date)
                if nav_data is None or (hasattr(nav_data, "empty") and nav_data.empty):
                    continue

                metrics = analyzer.calculate_metrics(nav_data)

                # 筛选条件
                if min_return_1y is not None and metrics.get("cagr", 0) < min_return_1y:
                    continue
                if max_drawdown is not None and abs(metrics.get("max_drawdown", 0)) > abs(
                    max_drawdown
                ):
                    continue
                if min_sharpe is not None and metrics.get("sharpe_ratio", 0) < min_sharpe:
                    continue

                info = data_manager.get_fund_info(code)
                results.append(
                    {
                        "code": code,
                        "name": info.get("name") or info.get("基金简称") or "未知",
                        "return": metrics.get("cagr", 0),
                        "drawdown": metrics.get("max_drawdown", 0),
                        "sharpe": metrics.get("sharpe_ratio", 0),
                    }
                )

                if len(results) >= limit:
                    break

            except Exception:
                continue

        if not results:
            return "未找到符合条件的基金"

        # 按收益排序
        results.sort(key=lambda x: x["return"], reverse=True)

        funds_text = "\n".join(
            [
                f"{r['code']}: {r['name']}\n"
                f"  年化收益: {r['return']:.2f}%, 最大回撤: {r['drawdown']:.2f}%, 夏普: {r['sharpe']:.2f}"
                for r in results
            ]
        )

        return f"业绩筛选结果 (共{len(results)}只):\n{funds_text}"
    except Exception as e:
        return f"筛选基金失败: {str(e)}"


# ============================================
# 组合分析工具（完整版）
# ============================================


@tool
def analyze_portfolio(
    fund_codes: str, weights: str | None = None, risk_free_rate: float = 0.03
) -> str:
    """分析投资组合的风险收益特征。

    Args:
        fund_codes: 基金代码列表，逗号分隔
        weights: 权重列表，逗号分隔，如 "0.5,0.3,0.2"。不传则等权重
        risk_free_rate: 无风险利率，默认 3%

    Returns:
        组合分析结果
    """
    try:
        codes = [c.strip() for c in fund_codes.split(",")]

        if weights:
            weight_list = [float(w.strip()) for w in weights.split(",")]
            total = sum(weight_list)
            weight_list = [w / total for w in weight_list]
        else:
            weight_list = [1.0 / len(codes)] * len(codes)

        if len(codes) != len(weight_list):
            return "权重数量与基金数量不匹配"

        data_manager = _get_data_manager()
        analyzer = _get_analyzer()
        start_date, end_date = _period_to_dates("1y")

        # 获取各基金数据
        fund_data = []
        for i, code in enumerate(codes):
            try:
                nav = data_manager.get_fund_nav(code, start_date=start_date, end_date=end_date)
                info = data_manager.get_fund_info(code)
                if nav is not None and not (hasattr(nav, "empty") and nav.empty):
                    metrics = analyzer.calculate_metrics(nav)
                    fund_data.append(
                        {
                            "code": code,
                            "name": info.get("name") or info.get("基金简称") or "未知",
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
        weight_variance = sum((f["weight"] - ideal_weight) ** 2 for f in fund_data) / n
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
                f"- {f['code']} ({f['name']}): {f['weight'] * 100:.1f}% "
                f"(收益{f['cagr']:.1f}%, 波动{f['volatility']:.1f}%)"
                for f in fund_data
            ]
        )

        return f"""投资组合分析:

基金配置:
{holdings_text}

风险收益指标:
- 预期年化收益: {portfolio_return:.2f}%
- 预期波动率: {portfolio_volatility:.2f}%
- 组合夏普比率: {portfolio_sharpe:.2f}
- 最大回撤: {max_drawdown:.2f}%
- 无风险利率: {risk_free_rate * 100:.1f}%

评估:
- 分散度评分: {diversification_score}/10
- 配置建议: {suggestion}

风险提示: 以上分析基于历史数据，不构成投资建议。""".strip()
    except Exception as e:
        return f"组合分析失败: {str(e)}"


# ============================================
# 阶段一: 核心功能完善 - 基金费率与评级工具
# ============================================


@tool
def get_fund_fee_info(fund_code: str) -> str:
    """获取基金费率信息，包括管理费、托管费、申购费、赎回费等。

    Args:
        fund_code: 6位基金代码，如 "000001"

    Returns:
        基金费率信息文本
    """
    try:
        adapter = _get_adapter()
        fee_info = adapter.get_fund_fee(fund_code)

        if not fee_info:
            return f"未找到基金 {fund_code} 的费率信息"

        return f"""基金 {fund_code} 费率信息:

管理费率: {fee_info.get("management_fee", "未知")}
托管费率: {fee_info.get("custody_fee", "未知")}
申购费率: {fee_info.get("purchase_fee", "未知")}
赎回费率: {fee_info.get("redeem_fee", "未知")}""".strip()
    except Exception as e:
        return f"获取费率信息失败: {str(e)}"


@tool
def get_fund_rating_info(fund_code: str) -> str:
    """获取基金评级信息。

    Args:
        fund_code: 6位基金代码，如 "000001"

    Returns:
        基金评级信息文本
    """
    try:
        adapter = _get_adapter()
        rating = adapter.get_fund_rating(fund_code)

        if rating is None:
            return f"基金 {fund_code} 暂无评级信息"

        stars = "★" * rating + "☆" * (5 - rating)
        return f"""基金 {fund_code} 评级信息:

基金评级: {stars} ({rating}星)
评级说明: 最高5星，最低1星""".strip()
    except Exception as e:
        return f"获取评级信息失败: {str(e)}"


@tool
def get_fund_ratings_list(limit: int = 20) -> str:
    """获取基金评级列表，查看多只基金的评级情况。

    Args:
        limit: 返回结果数量，默认20

    Returns:
        基金评级列表文本
    """
    try:
        adapter = _get_adapter()
        ratings_df = adapter.get_fund_ratings()

        if ratings_df is None or (hasattr(ratings_df, "empty") and ratings_df.empty):
            return "暂无基金评级数据"

        if hasattr(ratings_df, "head"):
            ratings_df = ratings_df.head(limit)

        results = []
        if hasattr(ratings_df, "iterrows"):
            for _, row in ratings_df.iterrows():
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                rating = row.get("rating", row.get("评级", "暂无"))
                results.append(f"{code}: {name} - 评级: {rating}")

        if not results:
            return "未找到基金评级数据"

        return f"基金评级列表 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取评级列表失败: {str(e)}"


# ============================================
# 阶段一: 核心功能完善 - 分红拆分工具
# ============================================


@tool
def get_fund_dividend_history(fund_code: str, limit: int = 10) -> str:
    """获取基金分红历史记录。

    Args:
        fund_code: 6位基金代码，如 "000001"
        limit: 返回记录数量，默认10

    Returns:
        基金分红历史文本
    """
    try:
        adapter = _get_adapter()
        dividends = adapter.get_fund_dividends(fund_code)

        if dividends is None or (hasattr(dividends, "empty") and dividends.empty):
            return f"基金 {fund_code} 暂无分红记录"

        if hasattr(dividends, "head"):
            dividends = dividends.head(limit)

        records = []
        if hasattr(dividends, "iterrows"):
            for _, row in dividends.iterrows():
                date = row.get("date", row.get("权益登记日", "未知"))
                amount = row.get("amount", row.get("分红金额", "未知"))
                records.append(f"  {date}: 每份分红 {amount}")
        else:
            records.append("  暂无详细分红记录")

        return f"""基金 {fund_code} 分红历史 (最近{len(records)}次):

{chr(10).join(records) if records else "  暂无分红记录"}""".strip()
    except Exception as e:
        return f"获取分红历史失败: {str(e)}"


@tool
def get_fund_split_history(fund_code: str, limit: int = 10) -> str:
    """获取基金拆分历史记录。

    Args:
        fund_code: 6位基金代码，如 "000001"
        limit: 返回记录数量，默认10

    Returns:
        基金拆分历史文本
    """
    try:
        adapter = _get_adapter()
        splits = adapter.get_fund_splits(fund_code)

        if splits is None or (hasattr(splits, "empty") and splits.empty):
            return f"基金 {fund_code} 暂无拆分记录"

        if hasattr(splits, "head"):
            splits = splits.head(limit)

        records = []
        if hasattr(splits, "iterrows"):
            for _, row in splits.iterrows():
                date = row.get("date", row.get("拆分日期", "未知"))
                ratio = row.get("ratio", row.get("拆分比例", "未知"))
                records.append(f"  {date}: 拆分比例 {ratio}")
        else:
            records.append("  暂无详细拆分记录")

        return f"""基金 {fund_code} 拆分历史 (最近{len(records)}次):

{chr(10).join(records) if records else "  暂无拆分记录"}""".strip()
    except Exception as e:
        return f"获取拆分历史失败: {str(e)}"


# ============================================
# 阶段一: 核心功能完善 - 基金排行工具
# ============================================


@tool
def get_fund_rank_overall(fund_type: str = "全部", limit: int = 20) -> str:
    """获取基金综合排行。

    Args:
        fund_type: 基金类型，如 "全部", "股票型", "债券型", "混合型", "指数型"
        limit: 返回结果数量，默认20

    Returns:
        基金排行列表文本
    """
    try:
        adapter = _get_adapter()
        rank_df = adapter.get_fund_rank_by_type(fund_type)

        if rank_df is None or (hasattr(rank_df, "empty") and rank_df.empty):
            return f"暂无{fund_type}基金排行数据"

        if hasattr(rank_df, "head"):
            rank_df = rank_df.head(limit)

        results = []
        if hasattr(rank_df, "iterrows"):
            for i, (_, row) in enumerate(rank_df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                return_1y = row.get("return_1y", row.get("近1年", "未知"))
                results.append(f"{i}. {code}: {name} - 近1年收益: {return_1y}")

        if not results:
            return "未找到基金排行数据"

        return f"{fund_type}基金排行 (前{len(results)}名):\n" + "\n".join(results)
    except Exception as e:
        return f"获取基金排行失败: {str(e)}"


@tool
def get_fund_rank_by_etf(limit: int = 20) -> str:
    """获取ETF基金排行。

    Args:
        limit: 返回结果数量，默认20

    Returns:
        ETF排行列表文本
    """
    try:
        adapter = _get_adapter()
        rank_df = adapter.get_exchange_fund_rank()

        if rank_df is None or (hasattr(rank_df, "empty") and rank_df.empty):
            return "暂无ETF排行数据"

        if hasattr(rank_df, "head"):
            rank_df = rank_df.head(limit)

        results = []
        if hasattr(rank_df, "iterrows"):
            for i, (_, row) in enumerate(rank_df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                return_val = row.get("return", row.get("涨跌幅", "未知"))
                results.append(f"{i}. {code}: {name} - 涨幅: {return_val}")

        if not results:
            return "未找到ETF排行数据"

        return f"ETF基金排行 (前{len(results)}名):\n" + "\n".join(results)
    except Exception as e:
        return f"获取ETF排行失败: {str(e)}"


@tool
def get_fund_rank_by_money(limit: int = 20) -> str:
    """获取货币基金排行（按7日年化收益率）。

    Args:
        limit: 返回结果数量，默认20

    Returns:
        货币基金排行列表文本
    """
    try:
        adapter = _get_adapter()
        rank_df = adapter.get_money_fund_rank()

        if rank_df is None or (hasattr(rank_df, "empty") and rank_df.empty):
            return "暂无货币基金排行数据"

        if hasattr(rank_df, "head"):
            rank_df = rank_df.head(limit)

        results = []
        if hasattr(rank_df, "iterrows"):
            for i, (_, row) in enumerate(rank_df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                yield_7d = row.get("yield_7d", row.get("7日年化", "未知"))
                results.append(f"{i}. {code}: {name} - 7日年化: {yield_7d}")

        if not results:
            return "未找到货币基金排行数据"

        return f"货币基金排行 (前{len(results)}名):\n" + "\n".join(results)
    except Exception as e:
        return f"获取货币基金排行失败: {str(e)}"


# ============================================
# 阶段一: 核心功能完善 - 业绩与风险工具
# ============================================


@tool
def get_fund_achievement_analysis(fund_code: str) -> str:
    """获取基金业绩评价，包括阶段收益、同类排名等。

    Args:
        fund_code: 6位基金代码，如 "000001"

    Returns:
        基金业绩评价文本
    """
    try:
        adapter = _get_adapter()
        achievement = adapter.get_fund_achievement(fund_code)

        if achievement is None or (hasattr(achievement, "empty") and achievement.empty):
            return f"未找到基金 {fund_code} 的业绩评价"

        if hasattr(achievement, "iterrows"):
            rows = list(achievement.iterrows())
            if rows:
                _, row = rows[0]
                return f"""基金 {fund_code} 业绩评价:

近1月收益: {row.get("return_1m", row.get("近1月", "未知"))}
近3月收益: {row.get("return_3m", row.get("近3月", "未知"))}
近6月收益: {row.get("return_6m", row.get("近6月", "未知"))}
近1年收益: {row.get("return_1y", row.get("近1年", "未知"))}
同类排名: {row.get("rank", row.get("同类排名", "未知"))}
评价等级: {row.get("grade", row.get("评价", "未知"))}""".strip()

        return f"基金 {fund_code} 业绩评价数据获取成功"
    except Exception as e:
        return f"获取业绩评价失败: {str(e)}"


@tool
def get_fund_risk_metrics(fund_code: str) -> str:
    """获取基金风险指标分析。

    Args:
        fund_code: 6位基金代码，如 "000001"

    Returns:
        基金风险指标文本
    """
    try:
        adapter = _get_adapter()
        risk_data = adapter.get_fund_risk_analysis(fund_code)

        if risk_data is None or (hasattr(risk_data, "empty") and risk_data.empty):
            return f"未找到基金 {fund_code} 的风险指标"

        if hasattr(risk_data, "iterrows"):
            rows = list(risk_data.iterrows())
            if rows:
                _, row = rows[0]
                return f"""基金 {fund_code} 风险指标:

标准差: {row.get("std", row.get("标准差", "未知"))}
夏普比率: {row.get("sharpe", row.get("夏普比率", "未知"))}
最大回撤: {row.get("max_drawdown", row.get("最大回撤", "未知"))}
波动率: {row.get("volatility", row.get("波动率", "未知"))}
风险等级: {row.get("risk_level", row.get("风险等级", "未知"))}
风险评价: {row.get("risk_assessment", row.get("风险评价", "未知"))}""".strip()

        return f"基金 {fund_code} 风险指标数据获取成功"
    except Exception as e:
        return f"获取风险指标失败: {str(e)}"


@tool
def get_fund_profit_stats(fund_code: str) -> str:
    """获取基金盈利概率统计。

    Args:
        fund_code: 6位基金代码，如 "000001"

    Returns:
        基金盈利概率文本
    """
    try:
        adapter = _get_adapter()
        profit_data = adapter.get_fund_profit_probability(fund_code)

        if profit_data is None or (hasattr(profit_data, "empty") and profit_data.empty):
            return f"未找到基金 {fund_code} 的盈利统计"

        if hasattr(profit_data, "iterrows"):
            rows = list(profit_data.iterrows())
            if rows:
                _, row = rows[0]
                return f"""基金 {fund_code} 盈利概率统计:

持有1月盈利概率: {row.get("prob_1m", row.get("1月盈利概率", "未知"))}
持有3月盈利概率: {row.get("prob_3m", row.get("3月盈利概率", "未知"))}
持有6月盈利概率: {row.get("prob_6m", row.get("6月盈利概率", "未知"))}
持有1年盈利概率: {row.get("prob_1y", row.get("1年盈利概率", "未知"))}
平均收益率: {row.get("avg_return", row.get("平均收益", "未知"))}
统计周期: {row.get("period", row.get("统计周期", "未知"))}""".strip()

        return f"基金 {fund_code} 盈利统计数据获取成功"
    except Exception as e:
        return f"获取盈利统计失败: {str(e)}"


@tool
def get_fund_asset_allocation_info(fund_code: str) -> str:
    """获取基金资产配置信息。

    Args:
        fund_code: 6位基金代码，如 "000001"

    Returns:
        基金资产配置文本
    """
    try:
        adapter = _get_adapter()
        allocation = adapter.get_fund_asset_allocation(fund_code)

        if allocation is None or (hasattr(allocation, "empty") and allocation.empty):
            return f"未找到基金 {fund_code} 的资产配置"

        if hasattr(allocation, "iterrows"):
            rows = list(allocation.iterrows())
            if rows:
                _, row = rows[0]
                return f"""基金 {fund_code} 资产配置:

股票占比: {row.get("stock_ratio", row.get("股票占比", "未知"))}
债券占比: {row.get("bond_ratio", row.get("债券占比", "未知"))}
现金占比: {row.get("cash_ratio", row.get("现金占比", "未知"))}
其他占比: {row.get("other_ratio", row.get("其他占比", "未知"))}
报告期: {row.get("report_date", row.get("报告期", "未知"))}""".strip()

        return f"基金 {fund_code} 资产配置数据获取成功"
    except Exception as e:
        return f"获取资产配置失败: {str(e)}"


# ============================================
# 阶段二: 宏观数据增强 - 经济指标工具
# ============================================


@tool
def get_macro_gdp(freq: str = "yearly") -> str:
    """获取中国GDP数据。

    Args:
        freq: 数据频率，可选 "yearly"(年度) 或 "quarterly"(季度)

    Returns:
        GDP数据文本
    """
    try:
        adapter = _get_adapter()
        if freq == "quarterly":
            df = adapter.get_gdp_quarterly()
        else:
            df = adapter.get_gdp_yearly()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无GDP数据"

        if hasattr(df, "tail"):
            df = df.tail(5)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                period = row.get("date", row.get("季度", row.get("年份", "未知")))
                value = row.get("gdp", row.get("GDP", row.get("国内生产总值", "未知")))
                yoy = row.get("yoy", row.get("同比", "未知"))
                records.append(f"  {period}: GDP={value}, 同比={yoy}")

        return f"中国GDP数据 ({freq}):\n" + "\n".join(records)
    except Exception as e:
        return f"获取GDP数据失败: {str(e)}"


@tool
def get_macro_cpi(freq: str = "yearly") -> str:
    """获取中国CPI（居民消费价格指数）数据。

    Args:
        freq: 数据频率，可选 "yearly"(年度) 或 "monthly"(月度)

    Returns:
        CPI数据文本
    """
    try:
        adapter = _get_adapter()
        if freq == "monthly":
            df = adapter.get_cpi_monthly()
        else:
            df = adapter.get_cpi_yearly()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无CPI数据"

        if hasattr(df, "tail"):
            df = df.tail(6)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                period = row.get("date", row.get("月份", row.get("年份", "未知")))
                cpi = row.get("cpi", row.get("CPI", row.get("全国", "未知")))
                yoy = row.get("yoy", row.get("同比", "未知"))
                records.append(f"  {period}: CPI={cpi}, 同比={yoy}")

        return f"中国CPI数据 ({freq}):\n" + "\n".join(records)
    except Exception as e:
        return f"获取CPI数据失败: {str(e)}"


@tool
def get_macro_ppi(freq: str = "yearly") -> str:
    """获取中国PPI（工业生产者出厂价格指数）数据。

    Args:
        freq: 数据频率，可选 "yearly"(年度) 或 "monthly"(月度)

    Returns:
        PPI数据文本
    """
    try:
        adapter = _get_adapter()
        if freq == "monthly":
            df = adapter.get_ppi_monthly()
        else:
            df = adapter.get_ppi_yearly()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无PPI数据"

        if hasattr(df, "tail"):
            df = df.tail(6)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                period = row.get("date", row.get("月份", row.get("年份", "未知")))
                ppi = row.get("ppi", row.get("PPI", row.get("当月", "未知")))
                yoy = row.get("yoy", row.get("同比", "未知"))
                records.append(f"  {period}: PPI={ppi}, 同比={yoy}")

        return f"中国PPI数据 ({freq}):\n" + "\n".join(records)
    except Exception as e:
        return f"获取PPI数据失败: {str(e)}"


@tool
def get_macro_trade() -> str:
    """获取中国进出口贸易数据，包括出口、进口和贸易差额。

    Returns:
        进出口贸易数据文本
    """
    try:
        adapter = _get_adapter()
        exports = adapter.get_exports_yearly()
        imports = adapter.get_imports_yearly()
        balance = adapter.get_trade_balance()

        results = []

        for label, df in [("出口", exports), ("进口", imports), ("贸易差额", balance)]:
            if df is not None and hasattr(df, "tail") and not (hasattr(df, "empty") and df.empty):
                df = df.tail(3)
                items = []
                if hasattr(df, "iterrows"):
                    for _, row in df.iterrows():
                        period = row.get("date", row.get("月份", row.get("年份", "未知")))
                        value = row.get("value", row.get("金额", row.get("当月", "未知")))
                        items.append(f"{period}: {value}")
                if items:
                    results.append(f"{label}:\n    " + "\n    ".join(items))

        if not results:
            return "暂无进出口贸易数据"

        return "中国进出口贸易数据:\n" + "\n\n".join(results)
    except Exception as e:
        return f"获取贸易数据失败: {str(e)}"


@tool
def get_macro_pmi(source: str = "official") -> str:
    """获取中国PMI（采购经理指数）数据，包括制造业、非制造业和服务业PMI。

    Args:
        source: 数据来源，可选 "official"(官方制造业) 或 "caixin"(财新制造业)

    Returns:
        PMI数据文本
    """
    try:
        adapter = _get_adapter()
        if source == "caixin":
            df = adapter.get_pmi_caixin()
            label = "财新制造业PMI"
        else:
            df = adapter.get_pmi_official()
            label = "官方制造业PMI"

        results = []

        if df is not None and hasattr(df, "tail") and not (hasattr(df, "empty") and df.empty):
            df = df.tail(6)
            records = []
            if hasattr(df, "iterrows"):
                for _, row in df.iterrows():
                    period = row.get("date", row.get("月份", "未知"))
                    pmi = row.get("pmi", row.get("PMI", row.get("制造业PMI", "未知")))
                    records.append(f"  {period}: PMI={pmi}")
            if records:
                results.append(f"{label}:\n" + "\n".join(records))

        # 官方非制造业PMI
        try:
            non_mfg_df = adapter.get_non_manufacturing_pmi()
            if (
                non_mfg_df is not None
                and hasattr(non_mfg_df, "tail")
                and not (hasattr(non_mfg_df, "empty") and non_mfg_df.empty)
            ):
                non_mfg_df = non_mfg_df.tail(6)
                records = []
                if hasattr(non_mfg_df, "iterrows"):
                    for _, row in non_mfg_df.iterrows():
                        period = row.get("date", row.get("月份", "未知"))
                        pmi = row.get("pmi", row.get("PMI", row.get("非制造业PMI", "未知")))
                        records.append(f"  {period}: PMI={pmi}")
                if records:
                    results.append("官方非制造业PMI:\n" + "\n".join(records))
        except Exception:
            pass

        # 财新服务业PMI
        try:
            svc_df = adapter.get_services_pmi()
            if (
                svc_df is not None
                and hasattr(svc_df, "tail")
                and not (hasattr(svc_df, "empty") and svc_df.empty)
            ):
                svc_df = svc_df.tail(6)
                records = []
                if hasattr(svc_df, "iterrows"):
                    for _, row in svc_df.iterrows():
                        period = row.get("date", row.get("月份", "未知"))
                        pmi = row.get("pmi", row.get("PMI", row.get("服务业PMI", "未知")))
                        records.append(f"  {period}: PMI={pmi}")
                if records:
                    results.append("财新服务业PMI:\n" + "\n".join(records))
        except Exception:
            pass

        if not results:
            return "暂无PMI数据"

        return "\n\n".join(results)
    except Exception as e:
        return f"获取PMI数据失败: {str(e)}"


@tool
def get_macro_interest_rate() -> str:
    """获取全球利率数据，包括中国基准利率、LPR、SHIBOR、HIBOR及美欧日英央行利率。

    Returns:
        利率数据文本
    """
    try:
        adapter = _get_adapter()
        rate_df = adapter.get_china_interest_rate()
        lpr_df = adapter.get_lpr_data()

        results = []

        if (
            rate_df is not None
            and hasattr(rate_df, "tail")
            and not (hasattr(rate_df, "empty") and rate_df.empty)
        ):
            rate_df = rate_df.tail(3)
            items = []
            if hasattr(rate_df, "iterrows"):
                for _, row in rate_df.iterrows():
                    period = row.get("date", row.get("日期", "未知"))
                    rate = row.get("rate", row.get("利率", "未知"))
                    items.append(f"{period}: {rate}")
            if items:
                results.append("基准利率:\n    " + "\n    ".join(items))

        if (
            lpr_df is not None
            and hasattr(lpr_df, "tail")
            and not (hasattr(lpr_df, "empty") and lpr_df.empty)
        ):
            lpr_df = lpr_df.tail(3)
            items = []
            if hasattr(lpr_df, "iterrows"):
                for _, row in lpr_df.iterrows():
                    period = row.get("date", row.get("日期", "未知"))
                    lpr_1y = row.get("lpr_1y", row.get("LPR1Y", row.get("1年期", "未知")))
                    lpr_5y = row.get("lpr_5y", row.get("LPR5Y", row.get("5年期以上", "未知")))
                    items.append(f"{period}: 1年期={lpr_1y}, 5年期={lpr_5y}")
            if items:
                results.append("LPR利率:\n    " + "\n    ".join(items))

        # SHIBOR上海银行间同业拆放利率
        try:
            shibor_df = adapter.get_shibor()
            if (
                shibor_df is not None
                and hasattr(shibor_df, "tail")
                and not (hasattr(shibor_df, "empty") and shibor_df.empty)
            ):
                shibor_df = shibor_df.tail(3)
                items = []
                if hasattr(shibor_df, "iterrows"):
                    for _, row in shibor_df.iterrows():
                        period = row.get("date", row.get("日期", "未知"))
                        rate = row.get("rate", row.get("利率", "未知"))
                        items.append(f"{period}: {rate}")
                if items:
                    results.append("SHIBOR:\n    " + "\n    ".join(items))
        except Exception:
            pass

        # SHIBOR与LPR数据
        try:
            shibor_lpr_df = adapter.get_shibor_lpr()
            if (
                shibor_lpr_df is not None
                and hasattr(shibor_lpr_df, "tail")
                and not (hasattr(shibor_lpr_df, "empty") and shibor_lpr_df.empty)
            ):
                shibor_lpr_df = shibor_lpr_df.tail(3)
                items = []
                if hasattr(shibor_lpr_df, "iterrows"):
                    for _, row in shibor_lpr_df.iterrows():
                        period = row.get("date", row.get("日期", "未知"))
                        items.append(f"{period}: {dict(row)}")
                if items:
                    results.append("SHIBOR-LPR:\n    " + "\n    ".join(items))
        except Exception:
            pass

        # HIBOR香港银行同业拆息
        try:
            hibor_df = adapter.get_hibor()
            if (
                hibor_df is not None
                and hasattr(hibor_df, "tail")
                and not (hasattr(hibor_df, "empty") and hibor_df.empty)
            ):
                hibor_df = hibor_df.tail(3)
                items = []
                if hasattr(hibor_df, "iterrows"):
                    for _, row in hibor_df.iterrows():
                        period = row.get("date", row.get("日期", "未知"))
                        rate = row.get("rate", row.get("利率", "未知"))
                        items.append(f"{period}: {rate}")
                if items:
                    results.append("HIBOR:\n    " + "\n    ".join(items))
        except Exception:
            pass

        # 美国利率
        try:
            usa_df = adapter.get_usa_interest_rate()
            if (
                usa_df is not None
                and hasattr(usa_df, "tail")
                and not (hasattr(usa_df, "empty") and usa_df.empty)
            ):
                usa_df = usa_df.tail(3)
                items = []
                if hasattr(usa_df, "iterrows"):
                    for _, row in usa_df.iterrows():
                        period = row.get("date", row.get("日期", "未知"))
                        rate = row.get("rate", row.get("利率", "未知"))
                        items.append(f"{period}: {rate}")
                if items:
                    results.append("美国联邦基金利率:\n    " + "\n    ".join(items))
        except Exception:
            pass

        # 欧洲利率
        try:
            euro_df = adapter.get_euro_interest_rate()
            if (
                euro_df is not None
                and hasattr(euro_df, "tail")
                and not (hasattr(euro_df, "empty") and euro_df.empty)
            ):
                euro_df = euro_df.tail(3)
                items = []
                if hasattr(euro_df, "iterrows"):
                    for _, row in euro_df.iterrows():
                        period = row.get("date", row.get("日期", "未知"))
                        rate = row.get("rate", row.get("利率", "未知"))
                        items.append(f"{period}: {rate}")
                if items:
                    results.append("欧洲央行利率:\n    " + "\n    ".join(items))
        except Exception:
            pass

        # 日本利率
        try:
            japan_df = adapter.get_japan_interest_rate()
            if (
                japan_df is not None
                and hasattr(japan_df, "tail")
                and not (hasattr(japan_df, "empty") and japan_df.empty)
            ):
                japan_df = japan_df.tail(3)
                items = []
                if hasattr(japan_df, "iterrows"):
                    for _, row in japan_df.iterrows():
                        period = row.get("date", row.get("日期", "未知"))
                        rate = row.get("rate", row.get("利率", "未知"))
                        items.append(f"{period}: {rate}")
                if items:
                    results.append("日本央行利率:\n    " + "\n    ".join(items))
        except Exception:
            pass

        # 英国利率
        try:
            uk_df = adapter.get_uk_interest_rate()
            if (
                uk_df is not None
                and hasattr(uk_df, "tail")
                and not (hasattr(uk_df, "empty") and uk_df.empty)
            ):
                uk_df = uk_df.tail(3)
                items = []
                if hasattr(uk_df, "iterrows"):
                    for _, row in uk_df.iterrows():
                        period = row.get("date", row.get("日期", "未知"))
                        rate = row.get("rate", row.get("利率", "未知"))
                        items.append(f"{period}: {rate}")
                if items:
                    results.append("英国央行利率:\n    " + "\n    ".join(items))
        except Exception:
            pass

        if not results:
            return "暂无利率数据"

        return "全球利率数据:\n" + "\n\n".join(results)
    except Exception as e:
        return f"获取利率数据失败: {str(e)}"


@tool
def get_macro_money_supply() -> str:
    """获取中国货币供应量数据，包括M2、新增贷款、社会融资规模、FDI和宏观杠杆率。

    Returns:
        货币供应量数据文本
    """
    try:
        adapter = _get_adapter()
        m2 = adapter.get_m2_yearly()
        loan = adapter.get_new_loan()
        financing = adapter.get_social_financing()

        results = []

        for label, df in [
            ("M2货币供应量", m2),
            ("新增人民币贷款", loan),
            ("社会融资规模", financing),
        ]:
            if df is not None and hasattr(df, "tail") and not (hasattr(df, "empty") and df.empty):
                df = df.tail(3)
                items = []
                if hasattr(df, "iterrows"):
                    for _, row in df.iterrows():
                        period = row.get("date", row.get("月份", row.get("年份", "未知")))
                        value = row.get("value", row.get("金额", row.get("当月", "未知")))
                        yoy = row.get("yoy", row.get("同比", ""))
                        item = f"{period}: {value}"
                        if yoy and str(yoy) not in ("nan", "None", ""):
                            item += f", 同比={yoy}"
                        items.append(item)
                if items:
                    results.append(f"{label}:\n    " + "\n    ".join(items))

        # FDI外商直接投资数据
        try:
            fdi_df = adapter.get_fdi_data()
            if (
                fdi_df is not None
                and hasattr(fdi_df, "tail")
                and not (hasattr(fdi_df, "empty") and fdi_df.empty)
            ):
                fdi_df = fdi_df.tail(5)
                items = []
                if hasattr(fdi_df, "iterrows"):
                    for _, row in fdi_df.iterrows():
                        period = row.get("date", row.get("月份", row.get("年份", "未知")))
                        value = row.get("value", row.get("金额", "未知"))
                        yoy = row.get("yoy", row.get("同比", ""))
                        item = f"{period}: {value}"
                        if yoy and str(yoy) not in ("nan", "None", ""):
                            item += f", 同比={yoy}"
                        items.append(item)
                if items:
                    results.append("FDI外商直接投资:\n    " + "\n    ".join(items))
        except Exception:
            pass

        # 宏观杠杆率
        try:
            lev_df = adapter.get_macro_leverage_ratio()
            if (
                lev_df is not None
                and hasattr(lev_df, "tail")
                and not (hasattr(lev_df, "empty") and lev_df.empty)
            ):
                lev_df = lev_df.tail(5)
                items = []
                if hasattr(lev_df, "iterrows"):
                    for _, row in lev_df.iterrows():
                        period = row.get("date", row.get("日期", row.get("月份", "未知")))
                        value = row.get("value", row.get("杠杆率", "未知"))
                        items.append(f"{period}: {value}")
                if items:
                    results.append("宏观杠杆率:\n    " + "\n    ".join(items))
        except Exception:
            pass

        if not results:
            return "暂无货币供应量数据"

        return "中国货币供应量数据:\n" + "\n\n".join(results)
    except Exception as e:
        return f"获取货币供应量数据失败: {str(e)}"


@tool
def get_macro_industrial() -> str:
    """获取中国工业数据，包括工业增加值和固定资产投资。

    Returns:
        工业数据文本
    """
    try:
        adapter = _get_adapter()
        production = adapter.get_industrial_production()
        investment = adapter.get_fixed_asset_investment()

        results = []

        for label, df in [("工业增加值", production), ("固定资产投资", investment)]:
            if df is not None and hasattr(df, "tail") and not (hasattr(df, "empty") and df.empty):
                df = df.tail(3)
                items = []
                if hasattr(df, "iterrows"):
                    for _, row in df.iterrows():
                        period = row.get("date", row.get("月份", "未知"))
                        value = row.get("value", row.get("当月", row.get("累计", "未知")))
                        yoy = row.get("yoy", row.get("同比", ""))
                        item = f"{period}: {value}"
                        if yoy and str(yoy) not in ("nan", "None", ""):
                            item += f", 同比={yoy}"
                        items.append(item)
                if items:
                    results.append(f"{label}:\n    " + "\n    ".join(items))

        if not results:
            return "暂无工业数据"

        return "中国工业数据:\n" + "\n\n".join(results)
    except Exception as e:
        return f"获取工业数据失败: {str(e)}"


@tool
def get_macro_retail() -> str:
    """获取中国社会消费品零售总额数据。

    Returns:
        零售数据文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_retail_sales_yearly()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无零售数据"

        if hasattr(df, "tail"):
            df = df.tail(5)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                period = row.get("date", row.get("月份", row.get("年份", "未知")))
                value = row.get("value", row.get("当月", row.get("累计", "未知")))
                yoy = row.get("yoy", row.get("同比", ""))
                item = f"  {period}: {value}"
                if yoy and str(yoy) not in ("nan", "None", ""):
                    item += f", 同比={yoy}"
                records.append(item)

        return "社会消费品零售总额:\n" + "\n".join(records)
    except Exception as e:
        return f"获取零售数据失败: {str(e)}"


@tool
def get_macro_unemployment() -> str:
    """获取中国城镇调查失业率数据。

    Returns:
        失业率数据文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_urban_unemployment()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无失业率数据"

        if hasattr(df, "tail"):
            df = df.tail(6)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                period = row.get("date", row.get("月份", row.get("年份", "未知")))
                rate = row.get("rate", row.get("失业率", row.get("城镇调查失业率", "未知")))
                records.append(f"  {period}: {rate}")

        return "城镇调查失业率:\n" + "\n".join(records)
    except Exception as e:
        return f"获取失业率数据失败: {str(e)}"


# ============================================
# 阶段二: 宏观数据增强 - 资金流向与板块工具
# ============================================


@tool
def get_market_sector_flow(period: str = "今日") -> str:
    """获取行业板块资金流向数据。

    Args:
        period: 时间周期，可选 "今日", "5日", "10日"

    Returns:
        行业资金流向文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_sector_fund_flow(period)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"暂无{period}行业资金流向数据"

        if hasattr(df, "head"):
            df = df.head(10)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                name = row.get("name", row.get("行业", row.get("板块名称", "未知")))
                inflow = row.get("main_net_inflow", row.get("主力净流入", "未知"))
                results.append(f"{i}. {name}: 主力净流入 {inflow}")

        return f"行业板块资金流向 ({period}):\n" + "\n".join(results)
    except Exception as e:
        return f"获取行业资金流向失败: {str(e)}"


@tool
def get_market_north_flow(market: str = "北向资金") -> str:
    """获取北向/南向资金流向数据。

    Args:
        market: 资金方向，可选 "北向资金", "南向资金"

    Returns:
        资金流向文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_north_fund_flow(market)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"暂无{market}数据"

        if hasattr(df, "tail"):
            df = df.tail(5)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date = row.get("date", row.get("日期", "未知"))
                value = row.get("value", row.get("净流入", row.get("当日净买入", "未知")))
                records.append(f"  {date}: {value}")

        return f"{market}流向:\n" + "\n".join(records)
    except Exception as e:
        return f"获取资金流向失败: {str(e)}"


@tool
def get_market_overall_flow() -> str:
    """获取市场整体资金流向数据。

    Returns:
        市场资金流向文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_market_fund_flow()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无市场整体资金流向数据"

        if hasattr(df, "tail"):
            df = df.tail(5)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date = row.get("date", row.get("日期", "未知"))
                main_inflow = row.get("main_net_inflow", row.get("主力净流入", "未知"))
                records.append(f"  {date}: 主力净流入 {main_inflow}")

        return "市场整体资金流向:\n" + "\n".join(records)
    except Exception as e:
        return f"获取市场资金流向失败: {str(e)}"


@tool
def get_industry_boards_info(limit: int = 20) -> str:
    """获取行业板块列表及行情数据。

    Args:
        limit: 返回结果数量，默认20

    Returns:
        行业板块列表文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_industry_boards()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无行业板块数据"

        if hasattr(df, "head"):
            df = df.head(limit)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                name = row.get("name", row.get("板块名称", "未知"))
                change = row.get("change_pct", row.get("涨跌幅", "未知"))
                results.append(f"{i}. {name}: {change}")

        return f"行业板块 (前{len(results)}个):\n" + "\n".join(results)
    except Exception as e:
        return f"获取行业板块失败: {str(e)}"


@tool
def get_concept_boards_info(limit: int = 20) -> str:
    """获取概念板块列表及行情数据。

    Args:
        limit: 返回结果数量，默认20

    Returns:
        概念板块列表文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_concept_boards()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无概念板块数据"

        if hasattr(df, "head"):
            df = df.head(limit)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                name = row.get("name", row.get("板块名称", "未知"))
                change = row.get("change_pct", row.get("涨跌幅", "未知"))
                results.append(f"{i}. {name}: {change}")

        return f"概念板块 (前{len(results)}个):\n" + "\n".join(results)
    except Exception as e:
        return f"获取概念板块失败: {str(e)}"


# ============================================
# 阶段三: 专业数据完善 - 债券数据工具
# ============================================


@tool
def get_bond_yield_curve_info() -> str:
    """获取债券收益率曲线数据。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_bond_yield_curve()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无债券收益率曲线数据"

        if hasattr(df, "tail"):
            df = df.tail(10)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                period = row.get("term", row.get("期限", "未知"))
                yield_val = row.get("yield", row.get("收益率", "未知"))
                records.append(f"  {period}: {yield_val}")

        return "债券收益率曲线:\n" + "\n".join(records)
    except Exception as e:
        return f"获取债券收益率曲线失败: {str(e)}"


@tool
def get_bond_spot_market_info() -> str:
    """获取债券现货行情数据。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_bond_spot_quote()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无债券现货行情数据"

        if hasattr(df, "head"):
            df = df.head(20)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("债券代码", "未知"))
                name = row.get("name", row.get("债券简称", "未知"))
                price = row.get("price", row.get("净价", "未知"))
                change = row.get("change_pct", row.get("涨跌幅", "未知"))
                results.append(f"{i}. {code} {name}: 净价={price}, 涨跌幅={change}")

        return f"债券现货行情 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取债券现货行情失败: {str(e)}"


@tool
def get_convertible_bonds_list(limit: int = 20) -> str:
    """获取可转债列表。

    Args:
        limit: 返回结果数量，默认20

    Returns:
        可转债列表文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_convertible_bonds()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无可转债列表数据"

        if hasattr(df, "head"):
            df = df.head(limit)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("债券代码", "未知"))
                name = row.get("name", row.get("债券简称", "未知"))
                price = row.get("price", row.get("现价", "未知"))
                premium = row.get("premium_rate", row.get("溢价率", "未知"))
                results.append(f"{i}. {code} {name}: 现价={price}, 溢价率={premium}")

        return f"可转债列表 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取可转债列表失败: {str(e)}"


@tool
def get_convertible_bond_detail_info(code: str) -> str:
    """获取可转债详情。

    Args:
        code: 可转债代码

    Returns:
        可转债详情文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_convertible_bond_detail(code)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到可转债 {code} 的详情数据"

        if hasattr(df, "iterrows"):
            rows = list(df.iterrows())
            if rows:
                _, row = rows[0]
                return f"""可转债 {code} 详情:

债券名称: {row.get("name", row.get("债券简称", "未知"))}
现价: {row.get("price", row.get("现价", "未知"))}
转股价: {row.get("convert_price", row.get("转股价", "未知"))}
溢价率: {row.get("premium_rate", row.get("溢价率", "未知"))}
到期收益率: {row.get("ytm", row.get("到期收益率", "未知"))}
债券评级: {row.get("rating", row.get("信用评级", "未知"))}""".strip()

        return f"可转债 {code} 详情数据获取成功"
    except Exception as e:
        return f"获取可转债详情失败: {str(e)}"


@tool
def get_bond_info(code: str) -> str:
    """获取债券基本信息。

    Args:
        code: 债券代码

    Returns:
        债券基本信息文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_bond_spot(code)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到债券 {code} 的信息"

        if hasattr(df, "iterrows"):
            rows = list(df.iterrows())
            if rows:
                _, row = rows[0]
                return f"""债券 {code} 基本信息:

债券名称: {row.get("name", row.get("债券简称", "未知"))}
净价: {row.get("price", row.get("净价", "未知"))}
到期收益率: {row.get("ytm", row.get("到期收益率", "未知"))}
票面利率: {row.get("coupon_rate", row.get("票面利率", "未知"))}
到期日期: {row.get("maturity_date", row.get("到期日", "未知"))}
债券评级: {row.get("rating", row.get("信用评级", "未知"))}""".strip()

        return f"债券 {code} 信息获取成功"
    except Exception as e:
        return f"获取债券信息失败: {str(e)}"


# ============================================
# 阶段三: 专业数据完善 - 市场估值工具
# ============================================


@tool
def get_market_valuation_info() -> str:
    """获取A股市场整体估值数据。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_a_share_valuation()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无A股市场估值数据"

        if hasattr(df, "tail"):
            df = df.tail(5)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date = row.get("date", row.get("日期", "未知"))
                pe = row.get("pe", row.get("市盈率", "未知"))
                pb = row.get("pb", row.get("市净率", "未知"))
                records.append(f"  {date}: 市盈率={pe}, 市净率={pb}")

        return "A股市场整体估值:\n" + "\n".join(records)
    except Exception as e:
        return f"获取市场估值数据失败: {str(e)}"


@tool
def get_index_valuation_info(index_code: str = "000300") -> str:
    """获取指数估值数据。

    Args:
        index_code: 指数代码，默认 "000300"(沪深300)

    Returns:
        指数估值数据文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_index_valuation(index_code)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"暂无指数 {index_code} 的估值数据"

        if hasattr(df, "tail"):
            df = df.tail(5)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date = row.get("date", row.get("日期", "未知"))
                pe = row.get("pe", row.get("市盈率", "未知"))
                pb = row.get("pb", row.get("市净率", "未知"))
                dividend_yield = row.get("dividend_yield", row.get("股息率", "未知"))
                records.append(f"  {date}: 市盈率={pe}, 市净率={pb}, 股息率={dividend_yield}")

        return f"指数 {index_code} 估值:\n" + "\n".join(records)
    except Exception as e:
        return f"获取指数估值数据失败: {str(e)}"


@tool
def get_market_pe_pb_info(code: str = "000001") -> str:
    """获取市场PE/PB数据。

    Args:
        code: 指数代码，默认 "000001"(上证指数)

    Returns:
        市场PE/PB数据文本
    """
    try:
        adapter = _get_adapter()
        pe_df = adapter.get_market_pe_lg(code)
        pb_df = adapter.get_market_pb_lg(code)

        results = []

        if (
            pe_df is not None
            and hasattr(pe_df, "tail")
            and not (hasattr(pe_df, "empty") and pe_df.empty)
        ):
            pe_df = pe_df.tail(5)
            items = []
            if hasattr(pe_df, "iterrows"):
                for _, row in pe_df.iterrows():
                    date = row.get("date", row.get("日期", "未知"))
                    pe = row.get("pe", row.get("市盈率", "未知"))
                    items.append(f"{date}: 市盈率={pe}")
            if items:
                results.append("市盈率(PE):\n    " + "\n    ".join(items))

        if (
            pb_df is not None
            and hasattr(pb_df, "tail")
            and not (hasattr(pb_df, "empty") and pb_df.empty)
        ):
            pb_df = pb_df.tail(5)
            items = []
            if hasattr(pb_df, "iterrows"):
                for _, row in pb_df.iterrows():
                    date = row.get("date", row.get("日期", "未知"))
                    pb = row.get("pb", row.get("市净率", "未知"))
                    items.append(f"{date}: 市净率={pb}")
            if items:
                results.append("市净率(PB):\n    " + "\n    ".join(items))

        if not results:
            return f"暂无指数 {code} 的PE/PB数据"

        return f"指数 {code} PE/PB数据:\n" + "\n\n".join(results)
    except Exception as e:
        return f"获取市场PE/PB数据失败: {str(e)}"


# ============================================
# 阶段三: 专业数据完善 - 资金流向工具
# ============================================


@tool
def get_stock_fund_flow_detail(code: str, market: str = "sh") -> str:
    """获取个股资金流向详情。

    Args:
        code: 股票代码
        market: 市场标识，"sh"(上海) 或 "sz"(深圳)，默认 "sh"

    Returns:
        个股资金流向文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_stock_fund_flow(code, market)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"暂无股票 {code} 的资金流向数据"

        if hasattr(df, "tail"):
            df = df.tail(5)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date = row.get("date", row.get("日期", "未知"))
                main_inflow = row.get("main_net_inflow", row.get("主力净流入", "未知"))
                super_inflow = row.get("super_net_inflow", row.get("超大单净流入", "未知"))
                big_inflow = row.get("big_net_inflow", row.get("大单净流入", "未知"))
                records.append(
                    f"  {date}: 主力净流入={main_inflow}, 超大单={super_inflow}, 大单={big_inflow}"
                )

        return f"股票 {code} 资金流向:\n" + "\n".join(records)
    except Exception as e:
        return f"获取个股资金流向失败: {str(e)}"


# ============================================
# 阶段三: 专业数据完善 - 基金公司工具
# ============================================


@tool
def get_fund_company_aum_rank(limit: int = 20) -> str:
    """获取基金公司管理规模排行及历史规模变化。

    Args:
        limit: 返回结果数量，默认20

    Returns:
        基金公司规模排行文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_company_aum()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无基金公司规模排行数据"

        if hasattr(df, "head"):
            df = df.head(limit)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                name = row.get("name", row.get("公司名称", "未知"))
                aum = row.get("aum", row.get("管理规模", "未知"))
                fund_count = row.get("fund_count", row.get("基金数量", "未知"))
                results.append(f"{i}. {name}: 管理规模={aum}, 基金数量={fund_count}")

        output = f"基金公司管理规模排行 (前{len(results)}名):\n" + "\n".join(results)

        # 基金公司历史规模
        try:
            hist_df = adapter.get_fund_company_aum_history()
            if (
                hist_df is not None
                and hasattr(hist_df, "tail")
                and not (hasattr(hist_df, "empty") and hist_df.empty)
            ):
                hist_df = hist_df.tail(5)
                items = []
                if hasattr(hist_df, "iterrows"):
                    for _, row in hist_df.iterrows():
                        period = row.get("date", row.get("日期", row.get("年份", "未知")))
                        total_aum = row.get("total_aum", row.get("总规模", "未知"))
                        items.append(f"  {period}: {total_aum}")
                if items:
                    output += "\n\n基金公司历史规模:\n" + "\n".join(items)
        except Exception:
            pass

        return output
    except Exception as e:
        return f"获取基金公司规模排行失败: {str(e)}"


@tool
def get_fund_aum_trend_analysis() -> str:
    """获取基金规模变化趋势。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_aum_trend()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无基金规模变化趋势数据"

        if hasattr(df, "tail"):
            df = df.tail(10)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date = row.get("date", row.get("日期", row.get("季度", "未知")))
                total_aum = row.get("total_aum", row.get("总规模", "未知"))
                change = row.get("change", row.get("变动", "未知"))
                item = f"  {date}: 总规模={total_aum}"
                if str(change) not in ("nan", "None", ""):
                    item += f", 变动={change}"
                records.append(item)

        return "基金规模变化趋势:\n" + "\n".join(records)
    except Exception as e:
        return f"获取基金规模趋势失败: {str(e)}"


@tool
def get_fund_scale_change_analysis() -> str:
    """获取基金规模变动数据。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_scale_change()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无基金规模变动数据"

        if hasattr(df, "head"):
            df = df.head(20)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                scale = row.get("scale", row.get("规模", "未知"))
                change = row.get("change", row.get("变动", "未知"))
                results.append(f"{i}. {code} {name}: 规模={scale}, 变动={change}")

        return f"基金规模变动 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取基金规模变动失败: {str(e)}"


@tool
def get_fund_holder_structure_info(fund_code: str) -> str:
    """获取基金持有人结构数据。

    Args:
        fund_code: 6位基金代码

    Returns:
        基金持有人结构文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_holder_structure(fund_code)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到基金 {fund_code} 的持有人结构数据"

        if hasattr(df, "tail"):
            df = df.tail(5)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date = row.get("date", row.get("报告期", "未知"))
                inst_ratio = row.get("inst_ratio", row.get("机构占比", "未知"))
                retail_ratio = row.get("retail_ratio", row.get("个人占比", "未知"))
                internal_ratio = row.get("internal_ratio", row.get("内部持有占比", "未知"))
                records.append(
                    f"  {date}: 机构={inst_ratio}, 个人={retail_ratio}, 内部持有={internal_ratio}"
                )

        return f"基金 {fund_code} 持有人结构:\n" + "\n".join(records)
    except Exception as e:
        return f"获取持有人结构失败: {str(e)}"


# ============================================
# 阶段三: 专业数据完善 - 基金经理工具
# ============================================


@tool
def get_all_fund_managers_list(limit: int = 20) -> str:
    """获取全部基金经理列表。

    Args:
        limit: 返回结果数量，默认20

    Returns:
        基金经理列表文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_all_fund_managers()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无基金经理列表数据"

        if hasattr(df, "head"):
            df = df.head(limit)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                name = row.get("name", row.get("姓名", "未知"))
                company = row.get("company", row.get("公司", "未知"))
                fund_count = row.get("fund_count", row.get("管理基金数", "未知"))
                total_scale = row.get("total_scale", row.get("管理规模", "未知"))
                results.append(
                    f"{i}. {name} ({company}): 管理基金数={fund_count}, 管理规模={total_scale}"
                )

        return f"基金经理列表 (前{len(results)}名):\n" + "\n".join(results)
    except Exception as e:
        return f"获取基金经理列表失败: {str(e)}"


# ============================================
# 阶段三: 专业数据完善 - 持仓分析工具
# ============================================


@tool
def get_fund_bond_holdings_info(fund_code: str) -> str:
    """获取基金债券持仓信息。

    Args:
        fund_code: 6位基金代码

    Returns:
        基金债券持仓文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_bond_holdings(fund_code)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到基金 {fund_code} 的债券持仓数据"

        if hasattr(df, "head"):
            df = df.head(10)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                name = row.get("bond_name", row.get("债券名称", "未知"))
                code = row.get("bond_code", row.get("债券代码", "未知"))
                ratio = row.get("weight", row.get("占净值比例", "未知"))
                results.append(f"{i}. {name}({code}): 占比={ratio}")

        return f"基金 {fund_code} 债券持仓 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取债券持仓失败: {str(e)}"


@tool
def get_fund_industry_allocation_info(fund_code: str) -> str:
    """获取基金行业配置信息。

    Args:
        fund_code: 6位基金代码

    Returns:
        基金行业配置文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_industry_allocation(fund_code)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到基金 {fund_code} 的行业配置数据"

        if hasattr(df, "head"):
            df = df.head(10)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                industry = row.get("industry", row.get("行业", "未知"))
                ratio = row.get("weight", row.get("占净值比例", "未知"))
                change = row.get("change", row.get("变动", "未知"))
                item = f"{i}. {industry}: 占比={ratio}"
                if str(change) not in ("nan", "None", ""):
                    item += f", 变动={change}"
                results.append(item)

        return f"基金 {fund_code} 行业配置:\n" + "\n".join(results)
    except Exception as e:
        return f"获取行业配置失败: {str(e)}"


@tool
def get_fund_portfolio_change_info(fund_code: str) -> str:
    """获取基金持仓变动信息。

    Args:
        fund_code: 6位基金代码

    Returns:
        基金持仓变动文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_portfolio_change(fund_code)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到基金 {fund_code} 的持仓变动数据"

        if hasattr(df, "head"):
            df = df.head(10)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                name = row.get("stock_name", row.get("股票名称", "未知"))
                code = row.get("stock_code", row.get("股票代码", "未知"))
                change_type = row.get("change_type", row.get("变动类型", "未知"))
                shares = row.get("shares", row.get("变动股数", "未知"))
                results.append(f"{i}. {name}({code}): {change_type}, 变动股数={shares}")

        return f"基金 {fund_code} 持仓变动 (前{len(results)}条):\n" + "\n".join(results)
    except Exception as e:
        return f"获取持仓变动失败: {str(e)}"


@tool
def get_china_us_bond_spread() -> str:
    """获取中美债券利差数据。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_china_us_bond_yield()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无中美债券利差数据"

        if hasattr(df, "tail"):
            df = df.tail(10)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date = row.get("date", row.get("日期", "未知"))
                cn_yield = row.get("cn_yield", row.get("中国国债收益率", "未知"))
                us_yield = row.get("us_yield", row.get("美国国债收益率", "未知"))
                spread = row.get("spread", row.get("利差", "未知"))
                records.append(f"  {date}: 中国={cn_yield}, 美国={us_yield}, 利差={spread}")

        return "中美债券利差:\n" + "\n".join(records)
    except Exception as e:
        return f"获取中美债券利差失败: {str(e)}"


# ============================================
# 阶段四: 边缘功能覆盖 - ETF/LOF行情工具
# ============================================


@tool
def get_etf_hist_data(code: str, period: str = "1y") -> str:
    """获取ETF历史行情数据。

    Args:
        code: ETF代码
        period: 时间周期，可选 1m, 3m, 6m, 1y, 3y, 5y, ytd

    Returns:
        ETF历史行情文本
    """
    try:
        adapter = _get_adapter()
        start_date, end_date = _period_to_dates(period)
        df = adapter.get_etf_hist(code, start_date=start_date, end_date=end_date)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到ETF {code} 在 {period} 期间的历史数据"

        if hasattr(df, "tail"):
            df = df.tail(5)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date = row.get("date", row.get("日期", "未知"))
                close = row.get("close", row.get("收盘", "未知"))
                volume = row.get("volume", row.get("成交量", "未知"))
                change = row.get("change_pct", row.get("涨跌幅", "未知"))
                records.append(f"  {date}: 收盘={close}, 涨跌幅={change}, 成交量={volume}")

        return f"ETF {code} 历史行情 ({period}, 最近5条):\n" + "\n".join(records)
    except Exception as e:
        return f"获取ETF历史行情失败: {str(e)}"


@tool
def get_lof_hist_data(code: str, period: str = "1y") -> str:
    """获取LOF历史行情数据。

    Args:
        code: LOF基金代码
        period: 时间周期，可选 1m, 3m, 6m, 1y, 3y, 5y, ytd

    Returns:
        LOF历史行情文本
    """
    try:
        adapter = _get_adapter()
        start_date, end_date = _period_to_dates(period)
        df = adapter.get_lof_hist(code, start_date=start_date, end_date=end_date)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到LOF {code} 在 {period} 期间的历史数据"

        if hasattr(df, "tail"):
            df = df.tail(5)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date = row.get("date", row.get("日期", "未知"))
                close = row.get("close", row.get("收盘", "未知"))
                volume = row.get("volume", row.get("成交量", "未知"))
                change = row.get("change_pct", row.get("涨跌幅", "未知"))
                records.append(f"  {date}: 收盘={close}, 涨跌幅={change}, 成交量={volume}")

        return f"LOF {code} 历史行情 ({period}, 最近5条):\n" + "\n".join(records)
    except Exception as e:
        return f"获取LOF历史行情失败: {str(e)}"


@tool
def get_etf_minute_data(code: str) -> str:
    """获取ETF分钟级行情数据。

    Args:
        code: ETF代码

    Returns:
        ETF分钟级行情文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_etf_minute(code, period="1")

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"暂无ETF {code} 的分钟级行情数据"

        if hasattr(df, "tail"):
            df = df.tail(10)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                time = row.get("time", row.get("时间", "未知"))
                price = row.get("price", row.get("价格", "未知"))
                volume = row.get("volume", row.get("成交量", "未知"))
                records.append(f"  {time}: 价格={price}, 成交量={volume}")

        return f"ETF {code} 分钟级行情 (最近10条):\n" + "\n".join(records)
    except Exception as e:
        return f"获取ETF分钟行情失败: {str(e)}"


@tool
def get_lof_minute_data(code: str) -> str:
    """获取LOF分钟级行情数据。

    Args:
        code: LOF基金代码

    Returns:
        LOF分钟级行情文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_lof_minute(code, period="1")

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"暂无LOF {code} 的分钟级行情数据"

        if hasattr(df, "tail"):
            df = df.tail(10)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                time = row.get("time", row.get("时间", "未知"))
                price = row.get("price", row.get("价格", "未知"))
                volume = row.get("volume", row.get("成交量", "未知"))
                records.append(f"  {time}: 价格={price}, 成交量={volume}")

        return f"LOF {code} 分钟级行情 (最近10条):\n" + "\n".join(records)
    except Exception as e:
        return f"获取LOF分钟行情失败: {str(e)}"


@tool
def get_lof_spot_info() -> str:
    """获取LOF基金实时行情。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_lof_spot()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无LOF实时行情数据"

        if hasattr(df, "head"):
            df = df.head(10)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                price = row.get("price", row.get("最新价", "未知"))
                change = row.get("change_pct", row.get("涨跌幅", "未知"))
                results.append(f"{i}. {code} {name}: 现价={price}, 涨跌幅={change}")

        return f"LOF实时行情 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取LOF实时行情失败: {str(e)}"


# ============================================
# 阶段四: 边缘功能覆盖 - 基金状态工具
# ============================================


@tool
def get_fund_purchase_status_info() -> str:
    """获取基金申购赎回状态。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_purchase_status()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无基金申购赎回状态数据"

        if hasattr(df, "head"):
            df = df.head(20)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                status = row.get("status", row.get("申购状态", "未知"))
                redeem_status = row.get("redeem_status", row.get("赎回状态", "未知"))
                results.append(f"{i}. {code} {name}: 申购={status}, 赎回={redeem_status}")

        return f"基金申购赎回状态 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取基金申购状态失败: {str(e)}"


@tool
def get_fund_daily_nav_overview() -> str:
    """获取基金每日净值概览。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_daily_nav()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无基金每日净值数据"

        if hasattr(df, "head"):
            df = df.head(20)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                nav = row.get("nav", row.get("单位净值", "未知"))
                acc_nav = row.get("acc_nav", row.get("累计净值", "未知"))
                change = row.get("change_pct", row.get("日涨跌幅", "未知"))
                results.append(
                    f"{i}. {code} {name}: 单位净值={nav}, 累计净值={acc_nav}, 涨跌幅={change}"
                )

        return f"基金每日净值概览 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取基金每日净值失败: {str(e)}"


@tool
def get_fund_category_spot_info(category: str = "") -> str:
    """获取分类基金实时行情。

    Args:
        category: 基金分类，如 "股票型", "债券型", "混合型" 等，为空则返回全部

    Returns:
        分类基金实时行情文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_category_spot(category)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"暂无{category or '全部'}基金实时行情数据"

        if hasattr(df, "head"):
            df = df.head(20)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                nav = row.get("nav", row.get("单位净值", "未知"))
                change = row.get("change_pct", row.get("日涨跌幅", "未知"))
                results.append(f"{i}. {code} {name}: 净值={nav}, 涨跌幅={change}")

        label = f"{category}" if category else "全部"
        return f"{label}基金实时行情 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取分类基金行情失败: {str(e)}"


@tool
def get_etf_spot_ths_info() -> str:
    """获取同花顺ETF实时行情。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_etf_spot_ths()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无同花顺ETF实时行情数据"

        if hasattr(df, "head"):
            df = df.head(20)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("代码", "未知"))
                name = row.get("name", row.get("名称", "未知"))
                price = row.get("price", row.get("最新价", "未知"))
                change = row.get("change_pct", row.get("涨跌幅", "未知"))
                results.append(f"{i}. {code} {name}: 现价={price}, 涨跌幅={change}")

        return f"同花顺ETF实时行情 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取同花顺ETF行情失败: {str(e)}"


# ============================================
# 阶段四: 边缘功能覆盖 - 指数数据工具
# ============================================


@tool
def get_index_spot_em_info(category: str = "沪深重要指数") -> str:
    """获取东方财富指数实时行情。

    Args:
        category: 指数分类，默认 "沪深重要指数"

    Returns:
        指数实时行情文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_index_spot_em(category)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"暂无{category}实时行情数据"

        if hasattr(df, "head"):
            df = df.head(20)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("代码", "未知"))
                name = row.get("name", row.get("名称", "未知"))
                price = row.get("price", row.get("最新价", "未知"))
                change = row.get("change_pct", row.get("涨跌幅", "未知"))
                results.append(f"{i}. {code} {name}: 点位={price}, 涨跌幅={change}")

        return f"{category}实时行情 (前{len(results)}个):\n" + "\n".join(results)
    except Exception as e:
        return f"获取东方财富指数行情失败: {str(e)}"


@tool
def get_index_spot_sina_info() -> str:
    """获取新浪指数实时行情。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_index_spot_sina()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无新浪指数实时行情数据"

        if hasattr(df, "head"):
            df = df.head(20)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("代码", "未知"))
                name = row.get("name", row.get("名称", "未知"))
                price = row.get("price", row.get("最新价", "未知"))
                change = row.get("change_pct", row.get("涨跌幅", "未知"))
                results.append(f"{i}. {code} {name}: 点位={price}, 涨跌幅={change}")

        return f"新浪指数实时行情 (前{len(results)}个):\n" + "\n".join(results)
    except Exception as e:
        return f"获取新浪指数行情失败: {str(e)}"


@tool
def get_index_hist_data(code: str, period: str = "1y") -> str:
    """获取指数历史数据。

    Args:
        code: 指数代码
        period: 时间周期，可选 1m, 3m, 6m, 1y, 3y, 5y, ytd

    Returns:
        指数历史数据文本
    """
    try:
        adapter = _get_adapter()
        start_date, end_date = _period_to_dates(period)
        df = adapter.get_index_hist(code, start_date=start_date, end_date=end_date)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到指数 {code} 在 {period} 期间的历史数据"

        if hasattr(df, "tail"):
            df = df.tail(5)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date = row.get("date", row.get("日期", "未知"))
                close = row.get("close", row.get("收盘", "未知"))
                volume = row.get("volume", row.get("成交量", "未知"))
                change = row.get("change_pct", row.get("涨跌幅", "未知"))
                records.append(f"  {date}: 收盘={close}, 涨跌幅={change}, 成交量={volume}")

        return f"指数 {code} 历史数据 ({period}, 最近5条):\n" + "\n".join(records)
    except Exception as e:
        return f"获取指数历史数据失败: {str(e)}"


@tool
def get_index_minute_data(code: str) -> str:
    """获取指数分钟级行情数据。

    Args:
        code: 指数代码

    Returns:
        指数分钟级行情文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_index_minute(code, period="1")

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"暂无指数 {code} 的分钟级行情数据"

        if hasattr(df, "tail"):
            df = df.tail(10)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                time = row.get("time", row.get("时间", "未知"))
                price = row.get("price", row.get("价格", "未知"))
                volume = row.get("volume", row.get("成交量", "未知"))
                records.append(f"  {time}: 点位={price}, 成交量={volume}")

        return f"指数 {code} 分钟级行情 (最近10条):\n" + "\n".join(records)
    except Exception as e:
        return f"获取指数分钟行情失败: {str(e)}"


# ============================================
# 阶段四: 边缘功能覆盖 - 评级排行工具
# ============================================


@tool
def get_fund_dividend_ranking(limit: int = 20) -> str:
    """获取基金分红排行。

    Args:
        limit: 返回结果数量，默认20

    Returns:
        基金分红排行文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_dividend_rank()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无基金分红排行数据"

        if hasattr(df, "head"):
            df = df.head(limit)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                dividend = row.get("dividend", row.get("累计分红", "未知"))
                count = row.get("dividend_count", row.get("分红次数", "未知"))
                results.append(f"{i}. {code} {name}: 累计分红={dividend}, 分红次数={count}")

        return f"基金分红排行 (前{len(results)}名):\n" + "\n".join(results)
    except Exception as e:
        return f"获取基金分红排行失败: {str(e)}"


@tool
def get_fund_rating_sh_detail() -> str:
    """获取上海证券基金评级数据。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_rating_sh()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无上海证券基金评级数据"

        if hasattr(df, "head"):
            df = df.head(20)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                rating = row.get("rating", row.get("评级", "未知"))
                results.append(f"{i}. {code} {name}: 评级={rating}")

        return f"上海证券基金评级 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取上海证券评级失败: {str(e)}"


@tool
def get_fund_rating_zs_detail() -> str:
    """获取招商证券基金评级数据。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_rating_zs()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无招商证券基金评级数据"

        if hasattr(df, "head"):
            df = df.head(20)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                rating = row.get("rating", row.get("评级", "未知"))
                results.append(f"{i}. {code} {name}: 评级={rating}")

        return f"招商证券基金评级 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取招商证券评级失败: {str(e)}"


@tool
def get_fund_rating_ja_detail() -> str:
    """获取济安金信基金评级数据。"""
    try:
        adapter = _get_adapter()
        df = adapter.get_fund_rating_ja()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无济安金信基金评级数据"

        if hasattr(df, "head"):
            df = df.head(20)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                rating = row.get("rating", row.get("评级", "未知"))
                results.append(f"{i}. {code} {name}: 评级={rating}")

        return f"济安金信基金评级 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取济安金信评级失败: {str(e)}"


@tool
def get_lcx_fund_ranking(limit: int = 20) -> str:
    """获取理财型基金排行。

    Args:
        limit: 返回结果数量，默认20

    Returns:
        理财型基金排行文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_lcx_fund_rank()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无理财型基金排行数据"

        if hasattr(df, "head"):
            df = df.head(limit)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                yield_val = row.get("yield", row.get("七日年化", row.get("万份收益", "未知")))
                results.append(f"{i}. {code} {name}: {yield_val}")

        return f"理财型基金排行 (前{len(results)}名):\n" + "\n".join(results)
    except Exception as e:
        return f"获取理财型基金排行失败: {str(e)}"


@tool
def get_hk_fund_ranking(limit: int = 20) -> str:
    """获取香港基金排行。

    Args:
        limit: 返回结果数量，默认20

    Returns:
        香港基金排行文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_hk_fund_rank()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无香港基金排行数据"

        if hasattr(df, "head"):
            df = df.head(limit)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                return_val = row.get("return", row.get("收益率", row.get("涨跌幅", "未知")))
                results.append(f"{i}. {code} {name}: {return_val}")

        return f"香港基金排行 (前{len(results)}名):\n" + "\n".join(results)
    except Exception as e:
        return f"获取香港基金排行失败: {str(e)}"


@tool
def get_index_fund_info_detail(category: str = "全部") -> str:
    """获取指数型基金详细信息。

    Args:
        category: 基金分类，默认 "全部"

    Returns:
        指数型基金信息文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_index_fund_info(category)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"暂无{category}指数型基金数据"

        if hasattr(df, "head"):
            df = df.head(20)

        results = []
        if hasattr(df, "iterrows"):
            for i, (_, row) in enumerate(df.iterrows(), 1):
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                index_name = row.get("index_name", row.get("跟踪指数", "未知"))
                scale = row.get("scale", row.get("规模", "未知"))
                results.append(f"{i}. {code} {name}: 跟踪指数={index_name}, 规模={scale}")

        return f"{category}指数型基金 (前{len(results)}只):\n" + "\n".join(results)
    except Exception as e:
        return f"获取指数型基金信息失败: {str(e)}"


# ============================================
# 补充覆盖: 剩余API方法
# ============================================


@tool
def get_bond_hist_data(code: str, period: str = "1y") -> str:
    """获取债券历史行情数据。

    Args:
        code: 债券代码
        period: 时间周期，可选 1m, 3m, 6m, 1y, 3y, 5y

    Returns:
        债券历史行情文本
    """
    try:
        adapter = _get_adapter()
        start_date, end_date = _period_to_dates(period)
        start_str = start_date.strftime("%Y%m%d") if start_date else None
        end_str = end_date.strftime("%Y%m%d") if end_date else None
        df = adapter.get_bond_hist(code, start_date=start_str, end_date=end_str)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到债券 {code} 的历史行情数据"

        if hasattr(df, "tail"):
            df = df.tail(10)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date_val = row.get("date", row.get("日期", "未知"))
                close = row.get("close", row.get("收盘价", "未知"))
                records.append(f"  {date_val}: 收盘价={close}")

        return f"债券 {code} 历史行情 ({period}):\n" + "\n".join(records)
    except Exception as e:
        return f"获取债券历史行情失败: {str(e)}"


@tool
def get_concept_board_hist_data(code: str, period: str = "3m") -> str:
    """获取概念板块历史行情数据。

    Args:
        code: 概念板块代码
        period: 时间周期，可选 1m, 3m, 6m, 1y, 3y, 5y

    Returns:
        概念板块历史行情文本
    """
    try:
        adapter = _get_adapter()
        start_date, end_date = _period_to_dates(period)
        start_str = start_date.strftime("%Y%m%d") if start_date else None
        end_str = end_date.strftime("%Y%m%d") if end_date else None
        df = adapter.get_concept_board_hist(code, start_date=start_str, end_date=end_str)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到概念板块 {code} 的历史行情数据"

        if hasattr(df, "tail"):
            df = df.tail(10)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date_val = row.get("date", row.get("日期", "未知"))
                close = row.get("close", row.get("收盘价", "未知"))
                records.append(f"  {date_val}: 收盘价={close}")

        return f"概念板块 {code} 历史行情 ({period}):\n" + "\n".join(records)
    except Exception as e:
        return f"获取概念板块历史行情失败: {str(e)}"


@tool
def get_industry_board_hist_data(code: str, period: str = "3m") -> str:
    """获取行业板块历史行情数据。

    Args:
        code: 行业板块代码
        period: 时间周期，可选 1m, 3m, 6m, 1y, 3y, 5y

    Returns:
        行业板块历史行情文本
    """
    try:
        adapter = _get_adapter()
        start_date, end_date = _period_to_dates(period)
        start_str = start_date.strftime("%Y%m%d") if start_date else None
        end_str = end_date.strftime("%Y%m%d") if end_date else None
        df = adapter.get_industry_board_hist(code, start_date=start_str, end_date=end_str)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到行业板块 {code} 的历史行情数据"

        if hasattr(df, "tail"):
            df = df.tail(10)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date_val = row.get("date", row.get("日期", "未知"))
                close = row.get("close", row.get("收盘价", "未知"))
                records.append(f"  {date_val}: 收盘价={close}")

        return f"行业板块 {code} 历史行情 ({period}):\n" + "\n".join(records)
    except Exception as e:
        return f"获取行业板块历史行情失败: {str(e)}"


@tool
def get_enterprise_price_index_data() -> str:
    """获取企业商品价格指数数据。

    Returns:
        企业商品价格指数文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_enterprise_price_index()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无企业商品价格指数数据"

        if hasattr(df, "tail"):
            df = df.tail(6)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                period = row.get("date", row.get("日期", "未知"))
                value = row.get("value", row.get("价格指数", "未知"))
                records.append(f"  {period}: {value}")

        return "企业商品价格指数:\n" + "\n".join(records)
    except Exception as e:
        return f"获取企业商品价格指数失败: {str(e)}"


@tool
def get_all_fund_names_list() -> str:
    """获取全部基金名称列表。

    Returns:
        基金名称列表文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_all_fund_names()

        if df is None or (hasattr(df, "empty") and df.empty):
            return "暂无基金名称数据"

        if hasattr(df, "head"):
            df = df.head(50)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                code = row.get("code", row.get("基金代码", "未知"))
                name = row.get("name", row.get("基金简称", "未知"))
                records.append(f"  {code}: {name}")

        return f"全部基金名称 (前{len(records)}只):\n" + "\n".join(records)
    except Exception as e:
        return f"获取基金名称列表失败: {str(e)}"


@tool
def get_batch_fund_nav(fund_codes: str) -> str:
    """批量获取基金净值数据。

    Args:
        fund_codes: 逗号分隔的基金代码，如 "000001,000002,000003"

    Returns:
        批量基金净值文本
    """
    try:
        adapter = _get_adapter()
        codes = [c.strip() for c in fund_codes.split(",") if c.strip()]
        if not codes:
            return "请提供有效的基金代码"

        start_date, end_date = _period_to_dates("1y")
        nav_dict = adapter.batch_get_fund_nav(codes, start_date=start_date, end_date=end_date)

        if not nav_dict:
            return "未获取到基金净值数据"

        results = []
        for code, df in nav_dict.items():
            if df is None or (hasattr(df, "empty") and df.empty):
                results.append(f"{code}: 暂无数据")
                continue
            if hasattr(df, "iloc"):
                latest = df.iloc[-1]
                nav = latest.get("unit_nav", latest.get("净值", "N/A"))
                results.append(f"{code}: 最新净值={nav}")
            else:
                results.append(f"{code}: 获取到数据")

        return "批量基金净值:\n" + "\n".join(results)
    except Exception as e:
        return f"批量获取基金净值失败: {str(e)}"


@tool
def get_index_daily_em_data(code: str) -> str:
    """获取东方财富指数日线数据。

    Args:
        code: 指数代码，如 "sz399552"

    Returns:
        指数日线数据文本
    """
    try:
        adapter = _get_adapter()
        start_date, end_date = _period_to_dates("1y")
        start_str = start_date.strftime("%Y%m%d") if start_date else None
        end_str = end_date.strftime("%Y%m%d") if end_date else None
        df = adapter.get_index_daily_em(code, start=start_str, end=end_str)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到指数 {code} 的日线数据"

        if hasattr(df, "tail"):
            df = df.tail(10)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date_val = row.get("date", row.get("日期", "未知"))
                close = row.get("close", row.get("收盘价", "未知"))
                records.append(f"  {date_val}: 收盘价={close}")

        return f"东方财富指数 {code} 日线:\n" + "\n".join(records)
    except Exception as e:
        return f"获取东方财富指数日线失败: {str(e)}"


@tool
def get_index_daily_tx_data(code: str) -> str:
    """获取腾讯指数日线数据。

    Args:
        code: 指数代码，如 "sh000001"

    Returns:
        指数日线数据文本
    """
    try:
        adapter = _get_adapter()
        start_date, end_date = _period_to_dates("1y")
        start_str = start_date.strftime("%Y%m%d") if start_date else None
        end_str = end_date.strftime("%Y%m%d") if end_date else None
        df = adapter.get_index_daily_tx(code, start=start_str, end=end_str)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到指数 {code} 的日线数据"

        if hasattr(df, "tail"):
            df = df.tail(10)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date_val = row.get("date", row.get("日期", "未知"))
                close = row.get("close", row.get("收盘价", "未知"))
                records.append(f"  {date_val}: 收盘价={close}")

        return f"腾讯指数 {code} 日线:\n" + "\n".join(records)
    except Exception as e:
        return f"获取腾讯指数日线失败: {str(e)}"


@tool
def get_stock_valuation_info(code: str) -> str:
    """获取个股估值数据。

    Args:
        code: 股票代码，如 "000001"

    Returns:
        个股估值数据文本
    """
    try:
        adapter = _get_adapter()
        df = adapter.get_stock_valuation_lg(code)

        if df is None or (hasattr(df, "empty") and df.empty):
            return f"未找到股票 {code} 的估值数据"

        if hasattr(df, "tail"):
            df = df.tail(5)

        records = []
        if hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                date_val = row.get("date", row.get("日期", "未知"))
                pe = row.get("pe", row.get("市盈率", "未知"))
                pb = row.get("pb", row.get("市净率", "未知"))
                records.append(f"  {date_val}: PE={pe}, PB={pb}")

        return f"股票 {code} 估值数据:\n" + "\n".join(records)
    except Exception as e:
        return f"获取个股估值数据失败: {str(e)}"


# ============================================
# 工具列表导出
# ============================================

FUND_TOOLS = [
    # 基金基础信息
    get_fund_basic_info,
    get_fund_nav_history,
    get_fund_performance,
    get_fund_holdings,
    get_fund_manager,
    # 基金筛选
    search_funds,
    filter_funds_by_performance,
    # 市场数据
    get_market_index,
    get_etf_spot,
    # 组合分析
    compare_funds,
    analyze_portfolio,
    analyze_investment_advice,
    # 阶段一: 核心功能完善 - 费率与评级
    get_fund_fee_info,
    get_fund_rating_info,
    get_fund_ratings_list,
    # 阶段一: 核心功能完善 - 分红拆分
    get_fund_dividend_history,
    get_fund_split_history,
    # 阶段一: 核心功能完善 - 基金排行
    get_fund_rank_overall,
    get_fund_rank_by_etf,
    get_fund_rank_by_money,
    # 阶段一: 核心功能完善 - 业绩与风险
    get_fund_achievement_analysis,
    get_fund_risk_metrics,
    get_fund_profit_stats,
    get_fund_asset_allocation_info,
    # 阶段二: 宏观数据增强 - 经济指标
    get_macro_gdp,
    get_macro_cpi,
    get_macro_ppi,
    get_macro_trade,
    get_macro_pmi,
    get_macro_interest_rate,
    get_macro_money_supply,
    get_macro_industrial,
    get_macro_retail,
    get_macro_unemployment,
    # 阶段二: 宏观数据增强 - 资金流向与板块
    get_market_sector_flow,
    get_market_north_flow,
    get_market_overall_flow,
    get_industry_boards_info,
    get_concept_boards_info,
    # 阶段三: 专业数据完善 - 债券数据
    get_bond_yield_curve_info,
    get_bond_spot_market_info,
    get_convertible_bonds_list,
    get_convertible_bond_detail_info,
    get_bond_info,
    # 阶段三: 专业数据完善 - 市场估值
    get_market_valuation_info,
    get_index_valuation_info,
    get_market_pe_pb_info,
    # 阶段三: 专业数据完善 - 资金流向
    get_stock_fund_flow_detail,
    # 阶段三: 专业数据完善 - 基金公司
    get_fund_company_aum_rank,
    get_fund_aum_trend_analysis,
    get_fund_scale_change_analysis,
    get_fund_holder_structure_info,
    # 阶段三: 专业数据完善 - 基金经理
    get_all_fund_managers_list,
    # 阶段三: 专业数据完善 - 持仓分析
    get_fund_bond_holdings_info,
    get_fund_industry_allocation_info,
    get_fund_portfolio_change_info,
    get_china_us_bond_spread,
    # 阶段四: 边缘功能覆盖 - ETF/LOF行情
    get_etf_hist_data,
    get_lof_hist_data,
    get_etf_minute_data,
    get_lof_minute_data,
    get_lof_spot_info,
    # 阶段四: 边缘功能覆盖 - 基金状态
    get_fund_purchase_status_info,
    get_fund_daily_nav_overview,
    get_fund_category_spot_info,
    get_etf_spot_ths_info,
    # 阶段四: 边缘功能覆盖 - 指数数据
    get_index_spot_em_info,
    get_index_spot_sina_info,
    get_index_hist_data,
    get_index_minute_data,
    # 阶段四: 边缘功能覆盖 - 评级排行
    get_fund_dividend_ranking,
    get_fund_rating_sh_detail,
    get_fund_rating_zs_detail,
    get_fund_rating_ja_detail,
    get_lcx_fund_ranking,
    get_hk_fund_ranking,
    get_index_fund_info_detail,
    # 补充覆盖: 剩余API方法
    get_bond_hist_data,
    get_concept_board_hist_data,
    get_industry_board_hist_data,
    get_enterprise_price_index_data,
    get_all_fund_names_list,
    get_batch_fund_nav,
    get_index_daily_em_data,
    get_index_daily_tx_data,
    get_stock_valuation_info,
]
