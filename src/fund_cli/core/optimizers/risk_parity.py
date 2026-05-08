"""风险平价优化器"""

from typing import Any

import numpy as np
import pandas as pd

from fund_cli.core.optimizer import Optimizer


class RiskParityOptimizer(Optimizer):
    """风险平价优化器 - PORTFOLIO-OPT-003"""

    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """执行风险平价优化"""
        try:
            from pypfopt import HRPOpt
        except ImportError:
            return self._fallback_risk_parity(returns)

        hrp = HRPOpt(returns)
        weights = hrp.optimize()

        port_returns = (returns * pd.Series(weights)).sum(axis=1)
        expected_return = port_returns.mean() * 252
        volatility = port_returns.std() * np.sqrt(252)
        sharpe = (expected_return - 0.03) / volatility if volatility > 0 else 0.0

        return {
            "weights": {k: round(v, 6) for k, v in weights.items()},
            "expected_return": round(expected_return, 6),
            "volatility": round(volatility, 6),
            "sharpe_ratio": round(sharpe, 4),
            "method": "risk_parity",
        }

    def get_methods(self) -> list[str]:
        return ["risk_parity"]

    @staticmethod
    def _fallback_risk_parity(returns: pd.DataFrame) -> dict[str, Any]:
        """回退实现：基于波动率倒数加权"""
        vols = returns.std()
        inv_vols = 1.0 / vols
        weights = inv_vols / inv_vols.sum()
        port_returns = (returns * weights).sum(axis=1)
        expected_return = port_returns.mean() * 252
        volatility = port_returns.std() * np.sqrt(252)
        sharpe = (expected_return - 0.03) / volatility if volatility > 0 else 0.0
        return {
            "weights": {k: round(v, 6) for k, v in weights.items()},
            "expected_return": round(expected_return, 6),
            "volatility": round(volatility, 6),
            "sharpe_ratio": round(sharpe, 4),
            "method": "inverse_volatility_fallback",
        }
