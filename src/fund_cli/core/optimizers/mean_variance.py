"""均值-方差优化器（Markowitz模型）"""

from typing import Any

import numpy as np
import pandas as pd

from fund_cli.core.optimizer import Optimizer
from fund_cli.data.models import OptimizationConstraint


class MeanVarianceOptimizer(Optimizer):
    """均值-方差优化器 - PORTFOLIO-OPT-001"""

    def __init__(self, risk_free_rate: float = 0.03):
        self.risk_free_rate = risk_free_rate

    def optimize(
        self,
        returns: pd.DataFrame,
        constraints: OptimizationConstraint | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        执行均值-方差优化

        Args:
            returns: 收益率 DataFrame，每列一只基金
            constraints: 优化约束条件

        Returns:
            优化结果字典，包含 weights, expected_return, volatility, sharpe_ratio
        """
        try:
            from pypfopt import EfficientFrontier, expected_returns, risk_models
        except ImportError:
            return self._fallback_optimize(returns, constraints)

        try:
            mu = expected_returns.mean_historical_return(returns)
            S = risk_models.sample_cov(returns)

            min_w = constraints.min_weight if constraints else 0.0
            max_w = constraints.max_weight if constraints else 1.0

            ef = EfficientFrontier(mu, S, weight_bounds=(min_w, max_w))

            if constraints and constraints.target_return is not None:
                ef.efficient_return(constraints.target_return)
            else:
                ef.max_sharpe(risk_free_rate=self.risk_free_rate)

            weights = ef.clean_weights()
            perf = ef.portfolio_performance(verbose=False, risk_free_rate=self.risk_free_rate)

            return {
                "weights": {k: round(v, 6) for k, v in weights.items()},
                "expected_return": round(perf[0], 6),
                "volatility": round(perf[1], 6),
                "sharpe_ratio": round(perf[2], 4),
                "method": "mean_variance",
            }
        except Exception:
            return self._fallback_optimize(returns, constraints)

    def get_methods(self) -> list[str]:
        return ["mean_variance"]

    @staticmethod
    def _fallback_optimize(
        returns: pd.DataFrame, constraints: OptimizationConstraint | None = None
    ) -> dict[str, Any]:
        """PyPortfolioOpt不可用时的回退实现"""
        n = returns.shape[1]
        equal_weights = {col: round(1.0 / n, 6) for col in returns.columns}
        port_return = (returns.mean() * 252).mean()
        port_vol = returns.std().mean() * np.sqrt(252)
        return {
            "weights": equal_weights,
            "expected_return": round(port_return, 6),
            "volatility": round(port_vol, 6),
            "sharpe_ratio": round((port_return - 0.03) / port_vol, 4) if port_vol > 0 else 0.0,
            "method": "equal_weight_fallback",
        }
