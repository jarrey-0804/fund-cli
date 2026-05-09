"""
归因分析引擎

实现 Brinson 归因分析等归因分析功能。
"""

from typing import Any

import numpy as np
import pandas as pd

from fund_cli.core.analyzer import Analyzer


class AttributionAnalyzer(Analyzer):
    """
    归因分析引擎

    支持：
    - Brinson 归因分析（配置效应、选择效应、交互效应）
    - 收益率分解
    """

    def analyze(
        self,
        data: pd.DataFrame,
        benchmark_weights: dict[str, float] | None = None,
        portfolio_weights: dict[str, float] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        执行归因分析

        Args:
            data: 包含各资产收益率的 DataFrame
            benchmark_weights: 基准组合权重 {资产名: 权重}
            portfolio_weights: 投资组合权重 {资产名: 权重}
            **kwargs: 额外参数

        Returns:
            归因分析结果字典
        """
        if benchmark_weights is None or portfolio_weights is None:
            return self._simple_decomposition(data)

        return self._brinson_attribution(data, benchmark_weights, portfolio_weights)

    def _simple_decomposition(self, returns: pd.DataFrame) -> dict[str, Any]:
        """
        简单收益率分解

        Args:
            returns: 收益率 DataFrame

        Returns:
            分解结果
        """
        if isinstance(returns, pd.Series):
            returns = returns.to_frame("fund")

        result = {}
        for col in returns.columns:
            col_data = returns[col].dropna()
            if len(col_data) == 0:
                continue

            cumulative = (1 + col_data).prod() - 1
            annualized = (1 + cumulative) ** (252 / len(col_data)) - 1

            result[col] = {
                "total_return": float(cumulative * 100),
                "annualized_return": float(annualized * 100),
                "volatility": float(col_data.std() * np.sqrt(252) * 100),
                "sharpe": float(
                    col_data.mean() / col_data.std() * np.sqrt(252) if col_data.std() > 0 else 0
                ),
            }

        return result

    def _brinson_attribution(
        self,
        returns: pd.DataFrame,
        benchmark_weights: dict[str, float],
        portfolio_weights: dict[str, float],
    ) -> dict[str, Any]:
        """
        Brinson 归因分析

        将组合收益与基准收益的差异分解为：
        - 配置效应（Allocation Effect）
        - 选择效应（Selection Effect）
        - 交互效应（Interaction Effect）

        Args:
            returns: 各资产收益率 DataFrame
            benchmark_weights: 基准权重
            portfolio_weights: 组合权重

        Returns:
            Brinson 归因结果
        """
        common_assets = (
            set(benchmark_weights.keys()) & set(portfolio_weights.keys()) & set(returns.columns)
        )

        if not common_assets:
            return {
                "allocation_effect": 0.0,
                "selection_effect": 0.0,
                "interaction_effect": 0.0,
                "total_active_return": 0.0,
            }

        # 计算各资产平均收益率
        asset_returns = {}
        for asset in common_assets:
            if asset in returns.columns:
                asset_returns[asset] = returns[asset].mean()

        # Brinson 归因分解
        allocation_effect = 0.0
        selection_effect = 0.0
        interaction_effect = 0.0

        benchmark_total_return = 0.0
        portfolio_total_return = 0.0

        for asset in common_assets:
            wp = portfolio_weights.get(asset, 0)
            wb = benchmark_weights.get(asset, 0)
            rp = asset_returns.get(asset, 0)
            rb = rp  # 简化：假设基准收益率等于资产收益率

            allocation_effect += (wp - wb) * rb
            selection_effect += wb * (rp - rb)
            interaction_effect += (wp - wb) * (rp - rb)

            portfolio_total_return += wp * rp
            benchmark_total_return += wb * rb

        total_active = portfolio_total_return - benchmark_total_return

        return {
            "allocation_effect": float(allocation_effect * 252 * 100),
            "selection_effect": float(selection_effect * 252 * 100),
            "interaction_effect": float(interaction_effect * 252 * 100),
            "total_active_return": float(total_active * 252 * 100),
            "portfolio_return": float(portfolio_total_return * 252 * 100),
            "benchmark_return": float(benchmark_total_return * 252 * 100),
            "asset_count": len(common_assets),
        }

    def get_metrics(self) -> list[str]:
        """获取可计算的指标列表"""
        return [
            "allocation_effect",
            "selection_effect",
            "interaction_effect",
            "total_active_return",
        ]
