"""最大夏普比率优化器"""

from typing import Any

import pandas as pd

from fund_cli.core.optimizer import Optimizer
from fund_cli.core.optimizers.mean_variance import MeanVarianceOptimizer
from fund_cli.data.models import OptimizationConstraint


class MaxSharpeOptimizer(Optimizer):
    """最大夏普比率优化器 - PORTFOLIO-OPT-002"""

    def __init__(self, risk_free_rate: float = 0.03):
        self.risk_free_rate = risk_free_rate

    def optimize(
        self,
        returns: pd.DataFrame,
        constraints: OptimizationConstraint | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """执行最大夏普比率优化"""
        try:
            from pypfopt import EfficientFrontier, expected_returns, risk_models
        except ImportError:
            return MeanVarianceOptimizer._fallback_optimize(returns, constraints)

        try:
            mu = expected_returns.mean_historical_return(returns)
            S = risk_models.sample_cov(returns)

            min_w = constraints.min_weight if constraints else 0.0
            max_w = constraints.max_weight if constraints else 1.0

            ef = EfficientFrontier(mu, S, weight_bounds=(min_w, max_w))
            ef.max_sharpe(risk_free_rate=self.risk_free_rate)

            weights = ef.clean_weights()
            perf = ef.portfolio_performance(verbose=False, risk_free_rate=self.risk_free_rate)

            return {
                "weights": {k: round(v, 6) for k, v in weights.items()},
                "expected_return": round(perf[0], 6),
                "volatility": round(perf[1], 6),
                "sharpe_ratio": round(perf[2], 4),
                "method": "max_sharpe",
            }
        except Exception:
            return MeanVarianceOptimizer._fallback_optimize(returns, constraints)

    def get_methods(self) -> list[str]:
        return ["max_sharpe"]
