"""
基金经理分析引擎

提供基金经理信息查询、业绩统计和稳定性分析功能。
"""

from typing import Any

import pandas as pd

from fund_cli.core.analyzer import Analyzer


class ManagerAnalyzer(Analyzer):
    """
    基金经理分析引擎

    分析基金经理的综合信息，包括：
    - 经理基本信息查询
    - 业绩统计（管理基金数、平均收益率等）
    - 稳定性分析（任职年限、管理规模变化）
    """

    def analyze(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """
        执行综合经理分析

        Args:
            data: 经理数据字典，需包含 name, fund_code, fund_name 等字段

        Returns:
            综合分析结果
        """
        result = {}
        result["info"] = self.manager_info(data)
        result["performance"] = self.performance_stats(data)
        result["stability"] = self.stability_analysis(data)
        return result

    def manager_info(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        经理信息查询 (FUND-MANAGER-001)

        Args:
            data: 经理数据字典

        Returns:
            经理信息字典
        """
        return {
            "name": data.get("name", ""),
            "fund_code": data.get("fund_code", ""),
            "fund_name": data.get("fund_name", ""),
            "company": data.get("company", ""),
            "start_date": str(data.get("start_date", "")),
            "tenure_days": data.get("tenure_days", 0),
        }

    def performance_stats(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        经理业绩统计 (FUND-MANAGER-002)

        Args:
            data: 经理数据字典，可包含 total_return, annual_return, funds 列表

        Returns:
            业绩统计字典
        """
        funds = data.get("funds", [])
        if funds:
            returns = [f.get("total_return", 0) for f in funds if f.get("total_return") is not None]
            avg_return = sum(returns) / len(returns) if returns else 0
            best_fund = max(funds, key=lambda f: f.get("total_return", float("-inf")), default=None)
            worst_fund = min(funds, key=lambda f: f.get("total_return", float("inf")), default=None)
            return {
                "total_funds": len(funds),
                "avg_return": round(avg_return, 2),
                "best_fund": best_fund.get("fund_name", "") if best_fund else "",
                "best_return": best_fund.get("total_return", 0) if best_fund else 0,
                "worst_fund": worst_fund.get("fund_name", "") if worst_fund else "",
                "worst_return": worst_fund.get("total_return", 0) if worst_fund else 0,
            }
        else:
            return {
                "total_funds": 1,
                "avg_return": data.get("annual_return", 0),
                "best_fund": data.get("fund_name", ""),
                "best_return": data.get("total_return", 0),
                "worst_fund": data.get("fund_name", ""),
                "worst_return": data.get("total_return", 0),
            }

    def stability_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        经理稳定性分析 (FUND-MANAGER-003)

        Args:
            data: 经理数据字典，可包含 tenure_days, start_date, funds 列表

        Returns:
            稳定性分析字典
        """
        tenure_days = data.get("tenure_days", 0)
        tenure_years = tenure_days / 365.25 if tenure_days else 0

        # 稳定性评级
        if tenure_years >= 5:
            stability_level = "非常稳定"
            stability_score = 5
        elif tenure_years >= 3:
            stability_level = "稳定"
            stability_score = 4
        elif tenure_years >= 1:
            stability_level = "一般"
            stability_score = 3
        else:
            stability_level = "较新"
            stability_score = 2

        # 多基金管理分析
        funds = data.get("funds", [])
        multi_fund = len(funds) > 1

        return {
            "tenure_days": tenure_days,
            "tenure_years": round(tenure_years, 1),
            "stability_level": stability_level,
            "stability_score": stability_score,
            "multi_fund_manager": multi_fund,
            "managed_fund_count": len(funds) if funds else 1,
        }

    def get_metrics(self) -> list[str]:
        """返回支持的指标列表"""
        return ["manager_info", "performance_stats", "stability_analysis", "evaluate_manager_performance"]

    def evaluate_manager_performance(
        self,
        manager_name: str,
        fund_codes: list[str],
        period_years: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        基金经理量化评价（基于收益率的同类排名）

        Args:
            manager_name: 基金经理姓名
            fund_codes: 该经理管理的基金代码列表
            period_years: 评价周期（年），默认[1, 2]

        Returns:
            {
                "经理姓名": str,
                "近1年评价": {"百分位": x, "等级": x},
                "近2年评价": {"百分位": x, "等级": x},
                "综合评级": str
            }
        """
        if period_years is None:
            period_years = [1, 2]

        from datetime import datetime, timedelta

        result = {
            "经理姓名": manager_name,
            "管理基金数": len(fund_codes),
        }

        for years in period_years:
            period_name = f"近{years}年"
            try:
                # 获取该经理所有基金在指定周期的收益
                fund_returns = []
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365 * years)

                for code in fund_codes:
                    try:
                        nav = self._get_nav_for_period(code, start_date, end_date)
                        if nav is not None and len(nav) > 30:
                            total_ret = nav.iloc[-1] / nav.iloc[0] - 1
                            fund_returns.append(total_ret)
                    except Exception:
                        continue

                if fund_returns:
                    avg_return = sum(fund_returns) / len(fund_returns)

                    # 计算百分位
                    percentile = self._calculate_manager_percentile(avg_return, years)

                    result[period_name] = {
                        "平均收益": round(avg_return * 100, 2),
                        "百分位": round(percentile * 100, 1),
                        "等级": self._percentile_to_grade(percentile),
                    }
                else:
                    result[period_name] = {"error": "数据不足"}
            except Exception as e:
                result[period_name] = {"error": str(e)}

        # 综合评级
        result["综合评级"] = self._calculate_overall_rating(result, period_years)
        return result

    def _get_nav_for_period(
        self,
        fund_code: str,
        start_date,
        end_date,
    ):
        """获取指定时间段的净值"""
        try:
            from fund_cli.core.data_manager import get_data_manager
            dm = get_data_manager()

            nav = dm.get_fund_nav(fund_code)
            if nav is None or nav.empty:
                return None

            # 获取净值列
            nav_col = "accumulated_nav" if "accumulated_nav" in nav.columns else "unit_nav"

            # 处理日期筛选
            if 'nav_date' in nav.columns:
                nav_dates = nav['nav_date']
                if not pd.api.types.is_datetime64_any_dtype(nav_dates):
                    nav_dates = pd.to_datetime(nav_dates)
                mask = (nav_dates >= start_date) & (nav_dates <= end_date)
                filtered = nav.loc[mask, nav_col]
            else:
                filtered = nav[nav_col]

            return filtered
        except Exception:
            return None

    def _calculate_manager_percentile(
        self,
        manager_return: float,
        years: int
    ) -> float:
        """
        计算经理百分位

        简化算法：基于收益率估算百分位
        实际应获取完整同类基金收益分布计算真实百分位
        """
        # 基于历史数据的简化估算
        # 年化收益率与百分位的映射
        annual_return = manager_return / years if years > 0 else manager_return

        if annual_return > 0.3:  # 30%以上
            return 0.95
        elif annual_return > 0.2:  # 20-30%
            return 0.85
        elif annual_return > 0.15:  # 15-20%
            return 0.70
        elif annual_return > 0.10:  # 10-15%
            return 0.55
        elif annual_return > 0.05:  # 5-10%
            return 0.40
        elif annual_return > 0:  # 0-5%
            return 0.30
        else:  # 负收益
            return 0.15

    def _percentile_to_grade(self, percentile: float) -> str:
        """百分位转等级"""
        if percentile >= 0.9:
            return "优秀（前10%）"
        elif percentile >= 0.7:
            return "良好（前30%）"
        elif percentile >= 0.5:
            return "中等（前50%）"
        elif percentile >= 0.3:
            return "一般（前70%）"
        else:
            return "较差（后30%）"

    def _calculate_overall_rating(
        self,
        result: dict,
        period_years: list[int]
    ) -> str:
        """计算综合评级"""
        percentiles = []
        for years in period_years:
            period_name = f"近{years}年"
            if period_name in result and "百分位" in result.get(period_name, {}):
                percentiles.append(result[period_name]["百分位"] / 100)

        if not percentiles:
            return "数据不足"

        avg_percentile = sum(percentiles) / len(percentiles)
        return self._percentile_to_grade(avg_percentile)

    def compute_manager_detailed_scores(
        self,
        manager_name: str,
        fund_codes: list[str],
        period_years: int = 1,
    ) -> dict[str, Any]:
        """
        计算基金经理细分得分

        Args:
            manager_name: 基金经理姓名
            fund_codes: 管理的基金代码列表
            period_years: 评价周期（年）

        Returns:
            {
                "回撤得分": float,
                "收益得分": float,
                "规模得分": float,
            }
        """
        from datetime import datetime, timedelta

        result = {
            "回撤得分": 0.5,
            "收益得分": 0.5,
            "规模得分": 0.5,
        }

        if not fund_codes:
            return result

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * period_years)

            all_returns = []
            all_drawdowns = []
            total_scale = 0

            for code in fund_codes:
                try:
                    nav = self._get_nav_for_period(code, start_date, end_date)
                    if nav is not None and len(nav) > 30:
                        # 计算收益率
                        total_ret = nav.iloc[-1] / nav.iloc[0] - 1
                        all_returns.append(total_ret)

                        # 计算最大回撤
                        cum_returns = (1 + nav.pct_change().dropna()).cumprod()
                        rolling_max = cum_returns.cummax()
                        drawdown = (cum_returns - rolling_max) / rolling_max
                        max_dd = abs(drawdown.min())
                        all_drawdowns.append(max_dd)

                        # 获取规模
                        try:
                            from fund_cli.core.data_manager import get_data_manager
                            dm = get_data_manager()
                            info = dm.get_fund_info(code)
                            if info:
                                scale = info.get("scale", info.get("fund_scale", 0))
                                if isinstance(scale, (int, float)):
                                    total_scale += scale
                        except Exception:
                            pass
                except Exception:
                    continue

            # 计算回撤得分
            if all_drawdowns:
                avg_drawdown = sum(all_drawdowns) / len(all_drawdowns)
                # 回撤0%得1分，回撤30%得0分
                result["回撤得分"] = max(0, min(1, 1 - avg_drawdown * 3.33))

            # 计算收益得分
            if all_returns:
                avg_return = sum(all_returns) / len(all_returns)
                annual_return = avg_return / period_years if period_years > 0 else avg_return
                if annual_return > 0.3:
                    result["收益得分"] = 0.9
                elif annual_return > 0.2:
                    result["收益得分"] = 0.8
                elif annual_return > 0.1:
                    result["收益得分"] = 0.7
                elif annual_return > 0.05:
                    result["收益得分"] = 0.6
                elif annual_return > 0:
                    result["收益得分"] = 0.5
                else:
                    result["收益得分"] = max(0.2, 0.5 + annual_return)

            # 计算规模得分
            if total_scale > 0:
                # 规模20-100亿为最佳区间
                if 20 <= total_scale <= 100:
                    result["规模得分"] = 0.9
                elif 100 < total_scale <= 300:
                    result["规模得分"] = 0.7
                elif total_scale > 300:
                    result["规模得分"] = 0.5  # 规模过大
                elif 10 <= total_scale < 20:
                    result["规模得分"] = 0.7
                else:
                    result["规模得分"] = 0.5  # 规模较小

        except Exception:
            pass

        return result

    def generate_manager_report(
        self,
        manager_name: str,
        fund_codes: list[str],
    ) -> str:
        """
        生成基金经理评价报告（Markdown格式）

        Args:
            manager_name: 基金经理姓名
            fund_codes: 管理的基金代码列表

        Returns:
            Markdown格式的报告
        """
        result = self.evaluate_manager_performance(manager_name, fund_codes)

        lines = [f"#### 基金经理评价: {manager_name}\n"]
        lines.append(f"管理基金数: {result.get('管理基金数', 0)}只\n")

        lines.append("| 评价周期 | 平均收益 | 百分位 | 等级 |")
        lines.append("| --- | --- | --- | --- |")

        for period in ["近1年", "近2年"]:
            if period in result and "error" not in result.get(period, {}):
                data = result[period]
                lines.append(
                    f"| {period} | {data.get('平均收益', 'N/A')}% | "
                    f"前{100-data.get('百分位', 50):.0f}% | {data.get('等级', 'N/A')} |"
                )

        lines.append("")
        lines.append(f"**综合评级**: {result.get('综合评级', 'N/A')}")

        return "\n".join(lines)
