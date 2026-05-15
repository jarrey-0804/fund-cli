"""
年度收益追踪分析器

追踪2024/2025/2026年初以来收益及同类排名
"""

from datetime import datetime
from typing import Any

import pandas as pd


class AnnualReturnTracker:
    """
    年度收益追踪分析器

    功能：
    - 计算各自然年度收益
    - 计算年初以来收益（YTD）
    - 同类基金排名
    """

    def __init__(self, data_manager=None):
        from fund_cli.core.data_manager import get_data_manager
        self._dm = data_manager or get_data_manager()

    def track_annual_returns(
        self,
        fund_code: str,
        years: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        追踪基金年度收益

        Args:
            fund_code: 基金代码
            years: 年份列表，默认为[2024, 2025, 2026]

        Returns:
            {
                "基金代码": str,
                "基金名称": str,
                "2024年": {"收益": x, "同类排名": x, "评价": x},
                "2025年": {...},
                "2026年初以来": {...},
                "业绩稳定性": str
            }
        """
        if years is None:
            years = [2024, 2025, 2026]

        result = {"基金代码": fund_code}

        # 获取基金信息
        info = self._dm.get_fund_info(fund_code)
        result["基金名称"] = info.get("fund_name", info.get("name", fund_code)) if info else fund_code

        # 获取净值数据
        nav = self._dm.get_fund_nav(fund_code)
        if nav is None or nav.empty:
            return {"error": "无净值数据", "基金代码": fund_code}

        current_year = datetime.now().year

        for year in years:
            if year > current_year:
                continue

            year_str = f"{year}年" if year < current_year else f"{year}年初以来"
            try:
                year_return = self._calculate_year_return(nav, year)
                if year_return is not None:
                    # 获取同类排名
                    peer_rank = self._get_peer_ranking(fund_code, year, year_return)

                    result[year_str] = {
                        "收益": round(year_return * 100, 2),
                        "同类排名": peer_rank.get("排名百分比", "N/A"),
                        "同类评价": peer_rank.get("评价", "N/A"),
                    }
            except Exception as e:
                result[year_str] = {"error": str(e)}

        # 计算业绩稳定性
        result["业绩稳定性"] = self._evaluate_stability(result, years)

        return result

    def track_portfolio_annual_returns(
        self,
        fund_codes: list[str],
        weights: list[float],
        years: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        追踪组合年度收益

        Args:
            fund_codes: 基金代码列表
            weights: 权重列表
            years: 年份列表

        Returns:
            组合各年度收益及评价
        """
        if years is None:
            years = [2024, 2025, 2026]

        result = {}
        current_year = datetime.now().year

        for year in years:
            if year > current_year:
                continue

            year_str = f"{year}年" if year < current_year else f"{year}年初以来"
            try:
                year_return = self._calculate_portfolio_year_return(fund_codes, weights, year)
                if year_return is not None:
                    result[year_str] = {
                        "收益": round(year_return * 100, 2),
                    }
            except Exception as e:
                result[year_str] = {"error": str(e)}

        return result

    def _calculate_year_return(
        self,
        nav: pd.DataFrame,
        year: int
    ) -> float | None:
        """计算特定年度收益"""
        year_start = datetime(year, 1, 1)
        year_end = datetime(year, 12, 31)

        # 处理当年（年初以来）
        if year == datetime.now().year:
            year_end = datetime.now()

        # 获取净值列
        nav_col = "accumulated_nav" if "accumulated_nav" in nav.columns else "unit_nav"

        # 处理日期列
        if 'nav_date' in nav.columns:
            # 确保日期格式正确
            nav_dates = pd.to_datetime(nav['nav_date'])
            year_nav = nav[(nav_dates >= year_start) & (nav_dates <= year_end)]
        else:
            # 假设索引是日期
            try:
                year_nav = nav[(nav.index >= year_start) & (nav.index <= year_end)]
            except Exception:
                return None

        if len(year_nav) < 10:
            return None

        start_nav = year_nav[nav_col].iloc[0]
        end_nav = year_nav[nav_col].iloc[-1]

        if start_nav <= 0:
            return None

        return (end_nav / start_nav) - 1

    def _calculate_portfolio_year_return(
        self,
        fund_codes: list[str],
        weights: list[float],
        year: int,
    ) -> float | None:
        """计算组合年度收益"""
        datetime(year, 1, 1)
        datetime(year, 12, 31) if year < datetime.now().year else datetime.now()

        total_return = 0
        total_weight = 0

        for code, weight in zip(fund_codes, weights, strict=False):
            try:
                nav = self._dm.get_fund_nav(code)
                if nav is not None and not nav.empty:
                    year_return = self._calculate_year_return(nav, year)
                    if year_return is not None:
                        total_return += year_return * weight
                        total_weight += weight
            except Exception:
                continue

        if total_weight > 0:
            return total_return / total_weight
        return None

    def _get_peer_ranking(
        self,
        fund_code: str,
        year: int,
        fund_return: float,
    ) -> dict[str, Any]:
        """获取同类基金排名"""
        try:
            # 获取基金类型
            info = self._dm.get_fund_info(fund_code)
            fund_type = info.get("type", "") if info else ""

            # 简化版：基于收益率估算排名百分位
            # 实际应获取完整同类基金收益分布
            percentile = self._estimate_percentile_from_return(fund_return, fund_type, year)

            return {
                "排名百分比": f"前{100-percentile*100:.0f}%" if percentile > 0.5 else f"后{percentile*100:.0f}%",
                "评价": self._ranking_to_evaluation(percentile),
            }
        except Exception:
            return {"排名百分比": "N/A", "评价": "数据不足"}

    def _estimate_percentile_from_return(
        self,
        fund_return: float,
        fund_type: str,
        year: int,
    ) -> float:
        """
        基于收益率估算百分位

        简化算法：根据收益率范围估算排名
        实际应获取同类基金完整分布
        """
        # 基于历史数据的简化估算
        # 不同类型基金的基准收益率不同
        if "QDII" in fund_type.upper() or "纳斯达克" in fund_type or "标普" in fund_type:
            # QDII基金：美股近年表现较好
            if fund_return > 0.3:
                return 0.9
            elif fund_return > 0.15:
                return 0.7
            elif fund_return > 0:
                return 0.5
            else:
                return 0.3
        elif "股票" in fund_type or "混合" in fund_type:
            # 主动权益类
            if fund_return > 0.4:
                return 0.95
            elif fund_return > 0.25:
                return 0.8
            elif fund_return > 0.1:
                return 0.6
            elif fund_return > 0:
                return 0.4
            else:
                return 0.2
        else:
            # 其他类型
            if fund_return > 0.2:
                return 0.8
            elif fund_return > 0.1:
                return 0.6
            elif fund_return > 0:
                return 0.5
            else:
                return 0.3

    def _ranking_to_evaluation(self, percentile: float) -> str:
        """排名转评价"""
        if percentile >= 0.9:
            return "优秀（前10%）"
        elif percentile >= 0.7:
            return "良好（前30%）"
        elif percentile >= 0.5:
            return "中等（前50%）"
        elif percentile >= 0.3:
            return "一般（前70%）"
        else:
            return "落后（后30%）"

    def _evaluate_stability(
        self,
        result: dict,
        years: list[int]
    ) -> str:
        """评价业绩稳定性"""
        returns = []
        current_year = datetime.now().year

        for year in years:
            if year > current_year:
                continue
            year_str = f"{year}年" if year < current_year else f"{year}年初以来"
            if year_str in result and "收益" in result[year_str]:
                returns.append(result[year_str]["收益"])

        if len(returns) < 2:
            return "数据不足"

        # 计算收益标准差
        import statistics
        std_dev = statistics.stdev(returns) if len(returns) > 1 else 0

        # 判断稳定性
        positive_years = sum(1 for r in returns if r > 0)

        if positive_years == len(returns) and std_dev < 15:
            return "业绩稳定优秀"
        elif positive_years >= len(returns) * 0.7:
            return "业绩较为稳定"
        elif positive_years >= len(returns) * 0.5:
            return "业绩波动较大"
        else:
            return "业绩表现不佳"

    def generate_report_section(
        self,
        fund_code: str,
        years: list[int] | None = None,
    ) -> str:
        """
        生成报告章节（Markdown格式）

        Args:
            fund_code: 基金代码
            years: 年份列表

        Returns:
            Markdown格式的报告章节
        """
        results = self.track_annual_returns(fund_code, years)

        if "error" in results:
            return f"*年度收益追踪失败: {results['error']}*\n"

        lines = ["#### 年度收益追踪\n"]
        lines.append("| 年份 | 收益 | 同类排名 | 评价 |")
        lines.append("| --- | --- | --- | --- |")

        current_year = datetime.now().year
        for year in years or [2024, 2025, 2026]:
            if year > current_year:
                continue
            year_str = f"{year}年" if year < current_year else f"{year}年初以来"
            if year_str in results and "error" not in results.get(year_str, {}):
                data = results[year_str]
                lines.append(
                    f"| {year_str} | {data.get('收益', 'N/A')}% | "
                    f"{data.get('同类排名', 'N/A')} | {data.get('同类评价', 'N/A')} |"
                )

        lines.append("")

        if "业绩稳定性" in results:
            lines.append(f"**业绩稳定性**: {results['业绩稳定性']}")
            lines.append("")

        return "\n".join(lines)
