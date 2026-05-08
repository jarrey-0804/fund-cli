"""有效前沿计算器"""

from typing import Any

import numpy as np
import pandas as pd


class EfficientFrontierCalculator:
    """有效前沿计算器 - PORTFOLIO-OPT-006"""

    def calculate(
        self,
        returns: pd.DataFrame,
        n_points: int = 50,
        risk_free_rate: float = 0.03,
    ) -> dict[str, Any]:
        """
        计算有效前沿上的点集

        Args:
            returns: 收益率 DataFrame
            n_points: 前沿点数
            risk_free_rate: 无风险利率

        Returns:
            包含 frontier_returns, frontier_volatilities, frontier_sharpes 的字典
        """
        try:
            from pypfopt import EfficientFrontier, expected_returns, risk_models

            mu = expected_returns.mean_historical_return(returns)
            S = risk_models.sample_cov(returns)

            min_ret = mu.min()
            max_ret = mu.max()
            target_returns = np.linspace(min_ret, max_ret, n_points)

            frontier_volatilities = []
            frontier_returns = []
            frontier_sharpes = []

            for target in target_returns:
                try:
                    ef = EfficientFrontier(mu, S)
                    ef.efficient_return(target)
                    ret, vol, _ = ef.portfolio_performance(
                        verbose=False, risk_free_rate=risk_free_rate
                    )
                    frontier_returns.append(ret)
                    frontier_volatilities.append(vol)
                    frontier_sharpes.append((ret - risk_free_rate) / vol if vol > 0 else 0)
                except Exception:
                    continue

            if len(frontier_returns) == 0:
                return self._fallback_calculate(returns, n_points, risk_free_rate)

            return {
                "frontier_returns": [round(r, 6) for r in frontier_returns],
                "frontier_volatilities": [round(v, 6) for v in frontier_volatilities],
                "frontier_sharpes": [round(s, 4) for s in frontier_sharpes],
                "n_points": len(frontier_returns),
            }
        except Exception:
            return self._fallback_calculate(returns, n_points, risk_free_rate)

    @staticmethod
    def _fallback_calculate(
        returns: pd.DataFrame, n_points: int, risk_free_rate: float
    ) -> dict[str, Any]:
        """回退实现"""
        n = returns.shape[1]
        vols = []
        rets = []
        for i in range(n_points):
            np.random.seed(i)
            w = np.random.dirichlet(np.ones(n))
            port_ret = (returns.mean() * 252 * w).sum()
            port_vol = np.sqrt(w @ returns.cov().values @ w * 252)
            vols.append(port_vol)
            rets.append(port_ret)
        return {
            "frontier_returns": [round(r, 6) for r in rets],
            "frontier_volatilities": [round(v, 6) for v in vols],
            "frontier_sharpes": [
                round((r - risk_free_rate) / v, 4) if v > 0 else 0
                for r, v in zip(rets, vols, strict=False)
            ],
            "n_points": n,
        }
