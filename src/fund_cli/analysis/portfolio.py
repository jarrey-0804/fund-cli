"""
投资组合分析引擎

实现组合层面的分析功能，包括组合收益、风险分散度等。
"""

from typing import Any

import numpy as np
import pandas as pd

from fund_cli.core.analyzer import Analyzer


class PortfolioAnalyzer(Analyzer):
    """
    投资组合分析引擎

    支持：
    - 组合权重分析
    - 组合风险分散度
    - 资产相关性分析
    - 组合收益贡献分析
    """

    def analyze(
        self,
        data: pd.DataFrame,
        weights: dict[str, float] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        执行组合分析

        Args:
            data: 多资产收益率 DataFrame，每列一个资产
            weights: 各资产权重字典
            **kwargs: 额外参数

        Returns:
            组合分析结果字典
        """
        if isinstance(data, pd.Series):
            data = data.to_frame("asset")

        if weights is None:
            # 等权配置
            n = data.shape[1]
            weights = dict.fromkeys(data.columns, 1.0 / n)

        result = {
            "asset_count": len(weights),
            "weights": weights,
        }

        # 组合收益率
        portfolio_returns = self._calculate_portfolio_returns(data, weights)
        result["portfolio_return"] = float(portfolio_returns.mean() * 252 * 100)
        result["portfolio_volatility"] = float(portfolio_returns.std() * np.sqrt(252) * 100)
        result["portfolio_sharpe"] = float(
            portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252)
            if portfolio_returns.std() > 0
            else 0
        )

        # 相关性分析
        result["correlation_matrix"] = data.corr().to_dict()
        avg_correlation = self._average_correlation(data.corr())
        result["average_correlation"] = float(avg_correlation)

        # 风险分散度（DR）
        result["diversification_ratio"] = float(self._diversification_ratio(data, weights))

        # 各资产贡献
        result["contribution"] = self._return_contribution(data, weights)

        return result

    def _calculate_portfolio_returns(
        self,
        returns: pd.DataFrame,
        weights: dict[str, float],
    ) -> pd.Series:
        """计算组合收益率序列"""
        valid_cols = [c for c in weights.keys() if c in returns.columns]
        w = np.array([weights[c] for c in valid_cols])
        return returns[valid_cols].dot(w)

    def _average_correlation(self, corr_matrix: pd.DataFrame) -> float:
        """计算平均相关系数"""
        n = len(corr_matrix)
        if n <= 1:
            return 1.0

        # 取上三角（不含对角线）
        mask = np.triu(np.ones((n, n), dtype=bool), k=1)
        values = corr_matrix.values[mask]

        return float(np.mean(values)) if len(values) > 0 else 1.0

    def _diversification_ratio(
        self,
        returns: pd.DataFrame,
        weights: dict[str, float],
    ) -> float:
        """
        计算风险分散度（Diversification Ratio）

        DR = 加权平均波动率 / 组合波动率
        DR > 1 表示组合具有分散化效果
        """
        valid_cols = [c for c in weights.keys() if c in returns.columns]
        if not valid_cols:
            return 1.0

        w = np.array([weights[c] for c in valid_cols])
        vols = returns[valid_cols].std() * np.sqrt(252)

        weighted_vol = float(np.dot(w, vols))
        portfolio_vol = float(returns[valid_cols].dot(w).std() * np.sqrt(252))

        if portfolio_vol == 0:
            return 1.0

        return weighted_vol / portfolio_vol

    def _return_contribution(
        self,
        returns: pd.DataFrame,
        weights: dict[str, float],
    ) -> dict[str, float]:
        """计算各资产收益贡献"""
        contribution = {}
        for asset, weight in weights.items():
            if asset in returns.columns:
                annual_return = returns[asset].mean() * 252 * 100
                contribution[asset] = {
                    "weight": weight,
                    "return": float(annual_return),
                    "contribution": float(weight * annual_return),
                }
        return contribution

    def get_metrics(self) -> list[str]:
        """获取可计算的指标列表"""
        return [
            "portfolio_return",
            "portfolio_volatility",
            "portfolio_sharpe",
            "average_correlation",
            "diversification_ratio",
        ]
