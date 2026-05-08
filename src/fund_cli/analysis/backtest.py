"""组合回测引擎"""

from typing import Any

import numpy as np
import pandas as pd

from fund_cli.core.analyzer import Analyzer


class BacktestAnalyzer(Analyzer):
    """组合回测引擎 - PORTFOLIO-OPT-007"""

    def analyze(self, data: pd.DataFrame, **kwargs: Any) -> dict[str, Any]:
        weights = kwargs.get("weights", {})
        return self.run_backtest(data, weights)

    def run_backtest(
        self,
        returns: pd.DataFrame,
        weights: dict[str, float] | None = None,
        rebalance_freq: str = "monthly",
    ) -> dict[str, Any]:
        """
        运行组合回测

        Args:
            returns: 多基金收益率 DataFrame
            weights: 基金权重字典，None表示等权
            rebalance_freq: 再平衡频率 (daily/monthly/quarterly/yearly/never)

        Returns:
            回测结果字典
        """
        if weights is None:
            n = returns.shape[1]
            weights = dict.fromkeys(returns.columns, 1.0 / n)

        w = pd.Series(weights)
        daily_returns = (returns * w).sum(axis=1)

        # 计算净值曲线
        nav = (1 + daily_returns).cumprod()

        # 计算指标
        total_days = len(daily_returns)
        total_return = (nav.iloc[-1] / nav.iloc[0] - 1) * 100 if len(nav) > 1 else 0
        annual_return = (1 + total_return / 100) ** (252 / total_days) - 1 if total_days > 0 else 0
        annual_vol = daily_returns.std() * np.sqrt(252) * 100
        sharpe = (annual_return - 0.03) / (annual_vol / 100) if annual_vol > 0 else 0

        # 最大回撤
        peak = nav.cummax()
        drawdown = (nav - peak) / peak
        max_drawdown = drawdown.min() * 100

        # 胜率
        win_rate = (
            (daily_returns > 0).sum() / len(daily_returns) * 100 if len(daily_returns) > 0 else 0
        )

        return {
            "total_return": round(total_return, 4),
            "annual_return": round(annual_return * 100, 4),
            "annual_volatility": round(annual_vol, 4),
            "sharpe_ratio": round(sharpe, 4),
            "max_drawdown": round(max_drawdown, 4),
            "win_rate": round(win_rate, 2),
            "trading_days": total_days,
            "rebalance_freq": rebalance_freq,
            "nav_curve": nav.tolist()[-10:],  # 最后10个净值点
        }

    def get_metrics(self) -> list[str]:
        return ["total_return", "annual_return", "sharpe_ratio", "max_drawdown", "win_rate"]
