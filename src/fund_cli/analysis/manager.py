"""
基金经理分析引擎

提供基金经理信息查询、业绩统计和稳定性分析功能。
"""

from typing import Any

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
        return ["manager_info", "performance_stats", "stability_analysis"]
