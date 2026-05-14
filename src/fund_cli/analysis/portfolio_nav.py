"""
组合净值计算器

计算组合层面的净值曲线、涨幅对比、跑赢跑输归因。
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import pandas as pd

from fund_cli.core.analyzer import Analyzer

logger = logging.getLogger(__name__)


class PortfolioNavCalculator:
    """
    组合净值计算器

    功能：
    - 按权重计算组合净值曲线
    - 组合整体涨幅与多个指数对比
    - 自动生成跑赢/跑输/接近判定
    """

    # 默认对比指数
    DEFAULT_BENCHMARKS: dict[str, str] = {
        "偏股混合基金指数": "885001.WI",
        "QDII股票型基金指数": "885065.WI",
        "沪深300": "000300.SH",
    }

    def __init__(self, data_manager=None):
        """
        初始化组合净值计算器

        Args:
            data_manager: 数据管理器，默认使用全局实例
        """
        from fund_cli.core.data_manager import get_data_manager

        self._dm = data_manager or get_data_manager()

    def compute_portfolio_nav(
        self,
        fund_codes: list[str],
        weights: list[float],
        start_date: str,
        end_date: str,
    ) -> pd.Series:
        """
        按权重计算组合净值曲线

        Args:
            fund_codes: 基金代码列表
            weights: 持仓权重（按市值占比，之和应为1）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            组合净值序列（标准化为初始值=1）

        Raises:
            ValueError: 基金代码与权重数量不匹配
        """
        if len(fund_codes) != len(weights):
            raise ValueError(f"基金代码数量({len(fund_codes)})与权重数量({len(weights)})不匹配")

        nav_dict: dict[str, pd.Series] = {}
        for code in fund_codes:
            try:
                df = self._dm.get_fund_nav(code, start_date=start_date, end_date=end_date)
                if df is not None and not df.empty:
                    # 优先使用累计净值，回退到单位净值（兼容中英文列名）
                    if "accumulated_nav" in df.columns:
                        nav_dict[code] = df["accumulated_nav"]
                    elif "累计净值" in df.columns:
                        nav_dict[code] = df["累计净值"]
                    elif "unit_nav" in df.columns:
                        nav_dict[code] = df["unit_nav"]
                    elif "单位净值" in df.columns:
                        nav_dict[code] = df["单位净值"]
                    else:
                        logger.warning(f"基金 {code} 净值数据无可用列: {df.columns.tolist()}")
                        continue
                else:
                    logger.warning(f"基金 {code} 无净值数据")
            except Exception as e:
                logger.warning(f"获取基金 {code} 净值失败: {e}")

        if not nav_dict:
            raise ValueError("所有基金均无净值数据，无法计算组合净值")

        nav_df = pd.DataFrame(nav_dict).ffill().bfill()
        # 标准化为初始值=1
        nav_normalized = nav_df / nav_df.iloc[0]
        weight_series = pd.Series(weights, index=fund_codes)
        # 仅使用有数据的基金权重
        available_weights = weight_series[nav_df.columns]
        # 权重重新标准化前添加警告
        if len(available_weights) != len(weight_series):
            logger.warning(
                f"{len(weight_series) - len(available_weights)} 只基金因无净值数据被排除，"
                f"权重已按可用基金重新标准化"
            )
        available_weights = available_weights / available_weights.sum()

        return (nav_normalized * available_weights).sum(axis=1)

    def compare_with_benchmarks(
        self,
        portfolio_nav: pd.Series,
        benchmarks: dict[str, str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        组合涨幅与多个指数对比

        Args:
            portfolio_nav: 组合净值序列
            benchmarks: {指数名称: 指数代码}，默认使用 DEFAULT_BENCHMARKS

        Returns:
            {指数名称: {指数收益, 组合收益, 超额收益, 结论}}
        """
        if benchmarks is None:
            benchmarks = self.DEFAULT_BENCHMARKS

        portfolio_return = portfolio_nav.iloc[-1] / portfolio_nav.iloc[0] - 1
        conclusions: dict[str, dict[str, Any]] = {}

        for name, index_code in benchmarks.items():
            try:
                index_nav = self._dm.get_benchmark_nav(
                    index_code,
                    start_date=date.fromisoformat(portfolio_nav.index[0].strftime("%Y-%m-%d")),
                    end_date=date.fromisoformat(portfolio_nav.index[-1].strftime("%Y-%m-%d")),
                )
                if index_nav is not None and not index_nav.empty:
                    # index_nav 是 DataFrame，需要指定列名
                    if "accumulated_nav" in index_nav.columns:
                        nav_col = "accumulated_nav"
                    elif "unit_nav" in index_nav.columns:
                        nav_col = "unit_nav"
                    else:
                        nav_col = index_nav.columns[-1]  # 回退到最后一列
                    index_return = index_nav[nav_col].iloc[-1] / index_nav[nav_col].iloc[0] - 1
                else:
                    index_return = 0.0
                    logger.warning(f"指数 {name}({index_code}) 无数据")
            except Exception as e:
                index_return = 0.0
                logger.warning(f"获取指数 {name}({index_code}) 失败: {e}")

            diff = portfolio_return - index_return

            if diff > 0.02:
                verdict = "跑赢"
            elif diff < -0.02:
                verdict = "跑输"
            else:
                verdict = "接近"

            conclusions[name] = {
                "指数收益": round(index_return, 4),
                "组合收益": round(portfolio_return, 4),
                "超额收益": round(diff, 4),
                "结论": verdict,
            }

        return conclusions

    def compute_portfolio_returns(
        self,
        portfolio_nav: pd.Series,
    ) -> pd.Series:
        """
        从组合净值序列计算日收益率

        Args:
            portfolio_nav: 组合净值序列

        Returns:
            日收益率序列
        """
        return portfolio_nav.pct_change().dropna()

    def attribution_analysis(
        self,
        portfolio_nav: pd.Series,
        benchmarks: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        跑赢跑输归因分析

        Args:
            portfolio_nav: 组合净值序列
            benchmarks: 对比指数

        Returns:
            {组合总收益, 跑赢指数列表, 跑输指数列表, 归因摘要}
        """
        comparisons = self.compare_with_benchmarks(portfolio_nav, benchmarks)
        portfolio_return = portfolio_nav.iloc[-1] / portfolio_nav.iloc[0] - 1

        outperform = []
        underperform = []
        for name, data in comparisons.items():
            if data["超额收益"] > 0:
                outperform.append({"指数": name, "超额收益": data["超额收益"]})
            else:
                underperform.append({"指数": name, "超额收益": data["超额收益"]})

        # 生成摘要
        summary_parts = [f"组合整体涨幅约{portfolio_return:.2%}"]
        if outperform:
            names = "、".join(item["指数"] for item in outperform)
            summary_parts.append(f"跑赢{names}")
        if underperform:
            names = "、".join(item["指数"] for item in underperform)
            summary_parts.append(f"跑输{names}")

        return {
            "组合总收益": round(portfolio_return, 4),
            "跑赢指数": outperform,
            "跑输指数": underperform,
            "归因摘要": "，".join(summary_parts),
        }
