"""
持仓分析引擎

提供基金持仓分析功能，包括行业配置、重仓股、集中度、变化追踪和风格分析。
"""

from typing import Any

import numpy as np
import pandas as pd

from fund_cli.core.analyzer import Analyzer


class HoldingAnalyzer(Analyzer):
    """
    持仓分析引擎

    分析基金持仓数据，提供：
    - 行业配置分析
    - 重仓股分析
    - 持仓集中度（HHI指数）
    - 持仓变化追踪
    - 风格分析（九宫格）
    """

    def analyze(self, data: pd.DataFrame, **kwargs: Any) -> dict[str, Any]:
        """
        执行综合持仓分析

        Args:
            data: 持仓数据 DataFrame，需包含 stock_code, stock_name, weight, industry 列

        Returns:
            综合分析结果字典
        """
        result = {}
        if "industry" in data.columns:
            result["industry_distribution"] = self.industry_distribution(data)
        result["top_holdings"] = self.top_holdings(data)
        result["concentration_hhi"] = self.concentration_hhi(data)
        result["concentration_level"] = self._hhi_level(result["concentration_hhi"])
        if "industry" in data.columns:
            result["style_analysis"] = self.style_analysis(data)
        return result

    def industry_distribution(self, holdings: pd.DataFrame) -> dict[str, float]:
        """
        行业配置分析 (FUND-HOLDING-002)

        Args:
            holdings: 持仓数据，需包含 industry 和 weight 列

        Returns:
            行业分布字典 {行业名称: 占比(%)}

        Raises:
            ValueError: 数据缺少 industry 列
        """
        if "industry" not in holdings.columns:
            raise ValueError("持仓数据缺少 industry 列")
        distribution = holdings.groupby("industry")["weight"].sum()
        return distribution.sort_values(ascending=False).to_dict()

    def top_holdings(self, holdings: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """
        重仓股分析 (FUND-HOLDING-003)

        Args:
            holdings: 持仓数据
            top_n: 返回前N大持仓，默认10

        Returns:
            前N大持仓 DataFrame
        """
        df = holdings.copy()
        if "weight" in df.columns:
            df = df.sort_values("weight", ascending=False)
        return df.head(top_n).reset_index(drop=True)

    def concentration_hhi(self, holdings: pd.DataFrame) -> float:
        """
        持仓集中度 - HHI指数 (FUND-HOLDING-004)

        HHI = sum(weight_i^2)，其中 weight_i 为第i只股票占净值比例（小数形式）

        Args:
            holdings: 持仓数据，需包含 weight 列

        Returns:
            HHI指数值。>0.25 高度集中, 0.15~0.25 中度集中, <0.15 分散
        """
        if holdings.empty or "weight" not in holdings.columns:
            return 0.0
        weights = holdings["weight"].values / 100.0  # 转为小数
        return float(np.sum(weights**2))

    def track_changes(
        self,
        current: pd.DataFrame,
        previous: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        持仓变化追踪 (FUND-HOLDING-005)

        对比两期持仓数据，标识新增、删除、增持、减持的股票。

        Args:
            current: 当期持仓数据
            previous: 上期持仓数据

        Returns:
            变化分析 DataFrame，包含 change_type 列（新增/删除/增持/减持/不变）
        """
        if current.empty or previous.empty:
            return pd.DataFrame()

        curr = (
            current[["stock_code", "stock_name", "weight"]].copy()
            if "stock_code" in current.columns
            else current.copy()
        )
        prev = (
            previous[["stock_code", "weight"]].copy()
            if "stock_code" in previous.columns
            else previous.copy()
        )

        merged = curr.merge(prev, on="stock_code", how="outer", suffixes=("_curr", "_prev"))

        def classify_change(row: pd.Series) -> str:
            if pd.isna(row.get("weight_prev")):
                return "新增"
            if pd.isna(row.get("weight_curr")):
                return "删除"
            diff = row["weight_curr"] - row["weight_prev"]
            if abs(diff) < 0.01:
                return "不变"
            return "增持" if diff > 0 else "减持"

        merged["change_type"] = merged.apply(classify_change, axis=1)
        merged["weight_change"] = merged.get("weight_curr", 0) - merged.get("weight_prev", 0)
        return merged.sort_values("weight_change", ascending=False, na_position="last").reset_index(
            drop=True
        )

    def style_analysis(self, holdings: pd.DataFrame) -> dict[str, Any]:
        """
        风格分析 (FUND-HOLDING-006)

        基于持仓股票的行业分布进行风格分析，输出风格九宫格位置。
        简化实现：基于行业分布判断大盘/小盘和价值/成长倾向。

        Args:
            holdings: 持仓数据，需包含 industry 列

        Returns:
            风格分析结果字典
        """
        if "industry" not in holdings.columns:
            return {"market_cap_style": "未知", "investment_style": "未知", "grid_position": "中"}

        # 基于行业分布判断风格
        distribution = self.industry_distribution(holdings)
        total = sum(distribution.values()) or 1.0

        # 大盘行业权重
        large_cap_industries = {"银行", "非银金融", "食品饮料", "医药生物", "电子", "电力设备"}
        large_cap_weight = sum(distribution.get(ind, 0) for ind in large_cap_industries) / total

        # 价值行业权重
        value_industries = {
            "银行",
            "房地产",
            "建筑装饰",
            "公用事业",
            "交通运输",
            "煤炭",
            "石油石化",
        }
        value_weight = sum(distribution.get(ind, 0) for ind in value_industries) / total

        market_cap_style = (
            "大盘" if large_cap_weight > 0.5 else ("小盘" if large_cap_weight < 0.3 else "中盘")
        )
        investment_style = (
            "价值" if value_weight > 0.3 else ("成长" if value_weight < 0.15 else "平衡")
        )

        return {
            "market_cap_style": market_cap_style,
            "investment_style": investment_style,
            "grid_position": f"{market_cap_style}{investment_style}",
            "large_cap_weight": round(large_cap_weight * 100, 2),
            "value_weight": round(value_weight * 100, 2),
            "industry_distribution": distribution,
        }

    def get_metrics(self) -> list[str]:
        """返回支持的指标列表"""
        return [
            "industry_distribution",
            "top_holdings",
            "concentration_hhi",
            "concentration_level",
            "style_analysis",
        ]

    @staticmethod
    def _hhi_level(hhi: float) -> str:
        """根据HHI值返回集中度等级"""
        if hhi >= 0.25:
            return "高度集中"
        elif hhi >= 0.15:
            return "中度集中"
        else:
            return "分散"
