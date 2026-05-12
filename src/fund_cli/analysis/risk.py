"""
风险分析引擎

实现专业的风险分析功能。
"""

from typing import Any

import numpy as np
import pandas as pd

from fund_cli.core.analyzer import Analyzer


class RiskAnalyzer(Analyzer):
    """
    风险分析引擎

    计算各类风险指标，包括：
    - 波动率风险：年化波动率、下行波动率
    - 回撤风险：最大回撤、平均回撤、回撤持续时间
    - 尾部风险：VaR、CVaR、偏度、峰度
    - 相关性风险：相关性矩阵、Beta
    """

    def __init__(
        self,
        confidence_level: float = 0.95,
        periods_per_year: int = 252,
    ):
        """
        初始化风险分析引擎

        Args:
            confidence_level: VaR 置信水平
            periods_per_year: 年交易日数
        """
        self.confidence_level = confidence_level
        self.periods_per_year = periods_per_year

    def analyze(  # type: ignore[override]
        self,
        returns: pd.Series,
        benchmark: pd.Series | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        执行风险分析

        Args:
            returns: 收益率序列
            benchmark: 基准收益率序列（可选）
            **kwargs: 额外参数

        Returns:
            风险分析结果字典
        """
        # 确保输入为 Series
        if isinstance(returns, pd.DataFrame):
            returns = returns.iloc[:, 0]

        returns = returns.dropna()

        metrics = {
            # 波动率风险
            "volatility_annual": self.annualized_volatility(returns) * 100,
            "downside_volatility": self.downside_volatility(returns) * 100,
            # 回撤风险
            "max_drawdown": self.max_drawdown(returns) * 100,
            "avg_drawdown": self.avg_drawdown(returns) * 100,
            "max_drawdown_duration": self.max_drawdown_duration(returns),
            # 尾部风险
            "var_95": self.var(returns, 0.95) * 100,
            "var_99": self.var(returns, 0.99) * 100,
            "cvar_95": self.cvar(returns, 0.95) * 100,
            "skewness": self.skewness(returns),
            "kurtosis": self.kurtosis(returns),
            # 分布特征
            "best_day": returns.max() * 100 if not returns.empty else 0,
            "worst_day": returns.min() * 100 if not returns.empty else 0,
            "std_dev": returns.std() * 100 if not returns.empty else 0,
        }

        # 相对风险指标
        if benchmark is not None:
            if isinstance(benchmark, pd.DataFrame):
                benchmark = benchmark.iloc[:, 0]
            benchmark = benchmark.dropna()

            common_dates = returns.index.intersection(benchmark.index)
            if len(common_dates) > 0:
                returns_aligned = returns.loc[common_dates]
                benchmark_aligned = benchmark.loc[common_dates]

                metrics["beta"] = self.beta(returns_aligned, benchmark_aligned)
                metrics["correlation"] = self.correlation(returns_aligned, benchmark_aligned)
                metrics["tracking_error"] = (
                    self.tracking_error(returns_aligned, benchmark_aligned) * 100
                )

        return metrics

    def get_metrics(self) -> list[str]:
        """获取可计算的指标列表"""
        return [
            "volatility_annual",
            "downside_volatility",
            "max_drawdown",
            "var_95",
            "var_99",
            "cvar_95",
            "skewness",
            "kurtosis",
            "beta",
            "correlation",
            "tracking_error",
        ]

    # ========== 波动率计算 ==========

    def annualized_volatility(self, returns: pd.Series) -> float:
        """计算年化波动率"""
        if returns.empty:
            return 0.0
        return returns.std() * np.sqrt(self.periods_per_year)

    def downside_volatility(
        self,
        returns: pd.Series,
        mar: float = 0.0,
    ) -> float:
        """
        计算下行波动率

        Args:
            returns: 收益率序列
            mar: 最低可接受收益率

        Returns:
            下行波动率
        """
        if returns.empty:
            return 0.0

        downside_returns = returns[returns < mar] - mar
        return np.sqrt((downside_returns**2).mean()) * np.sqrt(self.periods_per_year)

    # ========== 回撤计算 ==========

    def max_drawdown(self, returns: pd.Series) -> float:
        """计算最大回撤"""
        if returns.empty:
            return 0.0

        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    def avg_drawdown(self, returns: pd.Series) -> float:
        """计算平均回撤"""
        if returns.empty:
            return 0.0

        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.mean()

    def max_drawdown_duration(self, returns: pd.Series) -> int:
        """
        计算最大回撤持续天数

        Returns:
            最大回撤持续天数
        """
        if returns.empty:
            return 0

        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()

        # 找到回撤期间
        in_drawdown = cumulative < running_max

        if not in_drawdown.any():
            return 0

        # 计算最长回撤期
        drawdown_periods = []
        current_period = 0

        for is_dd in in_drawdown:
            if is_dd:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0

        if current_period > 0:
            drawdown_periods.append(current_period)

        return max(drawdown_periods) if drawdown_periods else 0

    def max_drawdown_period(self, returns: pd.Series) -> dict[str, Any]:
        """
        计算最大回撤及其发生的时间段

        Returns:
            {
                'max_drawdown': float,       # 最大回撤值（负数）
                'peak_date': str,            # 回撤起始日（峰值日）
                'trough_date': str,          # 回撤结束日（谷值日）
                'duration_days': int,         # 持续天数
                'recovery_date': str | None,  # 恢复日期（如有）
            }
        """
        if returns.empty:
            return {
                "max_drawdown": 0.0,
                "peak_date": "",
                "trough_date": "",
                "duration_days": 0,
                "recovery_date": None,
            }

        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max

        max_dd = drawdown.min()
        trough_date = drawdown.idxmin()
        peak_date = cumulative[:trough_date].idxmax()

        # 计算恢复日期
        recovery_date = None
        post_trough = cumulative[trough_date:]
        for dt, val in post_trough.items():
            if val >= cumulative[peak_date]:
                recovery_date = dt
                break

        return {
            "max_drawdown": round(float(max_dd), 6),
            "peak_date": peak_date.strftime("%Y-%m-%d") if hasattr(peak_date, "strftime") else str(peak_date),
            "trough_date": trough_date.strftime("%Y-%m-%d") if hasattr(trough_date, "strftime") else str(trough_date),
            "duration_days": (trough_date - peak_date).days,
            "recovery_date": recovery_date.strftime("%Y-%m-%d") if recovery_date is not None and hasattr(recovery_date, "strftime") else None,
        }

    # ========== 尾部风险计算 ==========

    def var(
        self,
        returns: pd.Series,
        confidence: float = 0.95,
    ) -> float:
        """
        计算风险价值 (Value at Risk)

        Args:
            returns: 收益率序列
            confidence: 置信水平

        Returns:
            VaR 值（负数表示损失）
        """
        if returns.empty:
            return 0.0

        return float(np.percentile(returns, (1 - confidence) * 100))

    def cvar(
        self,
        returns: pd.Series,
        confidence: float = 0.95,
    ) -> float:
        """
        计算条件风险价值 (Conditional VaR / Expected Shortfall)

        Args:
            returns: 收益率序列
            confidence: 置信水平

        Returns:
            CVaR 值
        """
        if returns.empty:
            return 0.0

        var = self.var(returns, confidence)
        return returns[returns <= var].mean()

    def skewness(self, returns: pd.Series) -> float:
        """计算偏度"""
        if returns.empty:
            return 0.0
        return returns.skew()

    def kurtosis(self, returns: pd.Series) -> float:
        """计算峰度"""
        if returns.empty:
            return 0.0
        return returns.kurtosis()

    # ========== 相对风险计算 ==========

    def beta(
        self,
        returns: pd.Series,
        benchmark: pd.Series,
    ) -> float:
        """计算 Beta"""
        if returns.empty or benchmark.empty:
            return 0.0

        covariance = returns.cov(benchmark)
        variance = benchmark.var()

        if variance == 0:
            return 0.0

        return covariance / variance

    def correlation(
        self,
        returns: pd.Series,
        benchmark: pd.Series,
    ) -> float:
        """计算相关系数"""
        if returns.empty or benchmark.empty:
            return 0.0
        return returns.corr(benchmark)

    def tracking_error(
        self,
        returns: pd.Series,
        benchmark: pd.Series,
    ) -> float:
        """计算跟踪误差"""
        if returns.empty or benchmark.empty:
            return 0.0

        excess_returns = returns - benchmark
        return excess_returns.std() * np.sqrt(self.periods_per_year)
