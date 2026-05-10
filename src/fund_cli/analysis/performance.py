"""
业绩分析引擎

基于 QuantStats 实现专业的业绩分析功能。
"""

from typing import Any

import numpy as np
import pandas as pd

from fund_cli.config import get_config
from fund_cli.core.analyzer import Analyzer


class PerformanceAnalyzer(Analyzer):
    """
    业绩分析引擎

    使用 QuantStats 库计算专业业绩指标，包括：
    - 收益指标：总收益、年化收益、累计收益
    - 风险指标：波动率、VaR、CVaR
    - 风险调整收益：夏普比率、索提诺比率、卡玛比率
    - 相对指标：Alpha、Beta、信息比率、跟踪误差
    """

    def __init__(self, risk_free_rate: float | None = None):
        """
        初始化业绩分析引擎

        Args:
            risk_free_rate: 无风险利率，默认从配置读取
        """
        config = get_config()
        self.risk_free_rate = risk_free_rate or config.analysis.risk_free_rate
        self._qs = None

    def _get_quantstats(self):
        """延迟加载 QuantStats"""
        if self._qs is None:
            try:
                import quantstats as qs

                self._qs = qs
            except ImportError as e:
                raise ImportError("QuantStats 未安装，请运行: pip install quantstats") from e
        return self._qs

    def analyze(  # type: ignore[override]
        self,
        returns: pd.Series,
        benchmark: pd.Series | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        执行业绩分析

        Args:
            returns: 收益率序列（日频）
            benchmark: 基准收益率序列（可选）
            **kwargs: 额外参数

        Returns:
            分析结果字典
        """
        qs = self._get_quantstats()

        # 确保输入为 Series
        if isinstance(returns, pd.DataFrame):
            returns = returns.iloc[:, 0]

        # 清理数据
        returns = returns.dropna()

        # 基础收益指标
        metrics = {
            # 收益指标
            "total_return": self._safe_calc(qs.stats.comp, returns) * 100,
            "cagr": self._safe_calc(qs.stats.cagr, returns) * 100,
            "mean_return": returns.mean() * 252 * 100,
            # 风险指标
            "volatility": self._safe_calc(qs.stats.volatility, returns) * 100,
            "max_drawdown": self._safe_calc(qs.stats.max_drawdown, returns) * 100,
            "var_95": self._safe_calc(qs.stats.var, returns) * 100,
            "cvar_95": self._safe_calc(qs.stats.cvar, returns) * 100,
            # 风险调整收益
            "sharpe": self._safe_calc(qs.stats.sharpe, returns, rf=self.risk_free_rate),
            "sortino": self._safe_calc(qs.stats.sortino, returns),
            "calmar": self._safe_calc(qs.stats.calmar, returns),
            # 其他指标
            "skew": self._safe_calc(qs.stats.skew, returns),
            "kurtosis": self._safe_calc(qs.stats.kurtosis, returns),
            "best_day": returns.max() * 100 if not returns.empty else 0,
            "worst_day": returns.min() * 100 if not returns.empty else 0,
            "avg_win": self._safe_calc(qs.stats.avg_win, returns) * 100,
            "avg_loss": self._safe_calc(qs.stats.avg_loss, returns) * 100,
            "win_rate": self._safe_calc(qs.stats.win_rate, returns) * 100,
        }

        # 相对指标（如果有基准）
        if benchmark is not None:
            if isinstance(benchmark, pd.DataFrame):
                benchmark = benchmark.iloc[:, 0]
            benchmark = benchmark.dropna()

            # 对齐日期
            common_dates = returns.index.intersection(benchmark.index)
            if len(common_dates) > 0:
                returns_aligned = returns.loc[common_dates]
                benchmark_aligned = benchmark.loc[common_dates]

                try:
                    greeks = qs.stats.greeks(returns_aligned, benchmark_aligned)
                    if greeks is not None:
                        metrics["alpha"] = float(greeks.iloc[0])
                        metrics["beta"] = float(greeks.iloc[1])
                    else:
                        metrics["alpha"] = None
                        metrics["beta"] = None
                except Exception:
                    metrics["alpha"] = None
                    metrics["beta"] = None

                # tracking_error / information_ratio / r_squared 在部分版本不可用
                # 使用 hasattr 检查，因为属性访问时会抛出 AttributeError
                if hasattr(qs.stats, "tracking_error"):
                    metrics["tracking_error"] = self._safe_calc(
                        qs.stats.tracking_error, returns_aligned, benchmark_aligned
                    )
                    if metrics["tracking_error"] is not None and not (
                        isinstance(metrics["tracking_error"], float)
                        and metrics["tracking_error"] != metrics["tracking_error"]
                    ):
                        metrics["tracking_error"] = metrics["tracking_error"] * 100
                    else:
                        metrics["tracking_error"] = None
                else:
                    metrics["tracking_error"] = None

                if metrics["tracking_error"] is None:
                    # 手动计算 tracking_error
                    excess = returns_aligned - benchmark_aligned
                    metrics["tracking_error"] = float(excess.std() * np.sqrt(252)) * 100

                if hasattr(qs.stats, "information_ratio"):
                    metrics["information_ratio"] = self._safe_calc(
                        qs.stats.information_ratio, returns_aligned, benchmark_aligned
                    )
                else:
                    metrics["information_ratio"] = None

                if metrics["information_ratio"] is None or (
                    isinstance(metrics["information_ratio"], float)
                    and metrics["information_ratio"] != metrics["information_ratio"]
                ):
                    # 手动计算 information_ratio
                    excess = returns_aligned - benchmark_aligned
                    te = excess.std() * np.sqrt(252)
                    metrics["information_ratio"] = (
                        float(excess.mean() * 252 / te) if te > 0 else None
                    )

                if hasattr(qs.stats, "r_squared"):
                    metrics["r_squared"] = self._safe_calc(
                        qs.stats.r_squared, returns_aligned, benchmark_aligned
                    )
                else:
                    metrics["r_squared"] = None

                if metrics["r_squared"] is None or (
                    isinstance(metrics["r_squared"], float)
                    and metrics["r_squared"] != metrics["r_squared"]
                ):
                    metrics["r_squared"] = float(returns_aligned.corr(benchmark_aligned) ** 2)

        return metrics

    def calculate_metrics(
        self,
        nav_data: pd.DataFrame | pd.Series,
        nav_column: str = "unit_nav",
    ) -> dict[str, Any]:
        """
        从净值数据计算业绩指标（便捷方法）.

        Args:
            nav_data: 净值数据 DataFrame 或收益率 Series
            nav_column: 净值列名（仅当 nav_data 为 DataFrame 时使用）

        Returns:
            分析指标字典
        """
        # 如果是 Series，直接作为收益率处理
        if isinstance(nav_data, pd.Series):
            returns = nav_data
        else:
            # 从 DataFrame 计算收益率
            returns = self.calculate_returns(nav_data, nav_column)

        return self.analyze(returns)

    def _safe_calc(self, func, *args, **kwargs) -> Any:
        """安全计算，捕获异常"""
        try:
            result = func(*args, **kwargs)
            if result is None:
                return float("nan")
            return result
        except Exception:
            return float("nan")

    def get_metrics(self) -> list[str]:
        """
        获取可计算的指标列表

        Returns:
            指标名称列表
        """
        return [
            "total_return",
            "cagr",
            "volatility",
            "max_drawdown",
            "sharpe",
            "sortino",
            "calmar",
            "var_95",
            "cvar_95",
            "alpha",
            "beta",
            "tracking_error",
            "information_ratio",
        ]

    def calculate_returns(
        self,
        nav_data: pd.DataFrame,
        nav_column: str = "unit_nav",
    ) -> pd.Series:
        """
        从净值数据计算收益率

        Args:
            nav_data: 净值数据 DataFrame
            nav_column: 净值列名

        Returns:
            日收益率序列
        """
        nav = nav_data.set_index("nav_date")[nav_column]
        returns = nav.pct_change().dropna()
        returns.name = "daily_return"
        return returns

    def calculate_cumulative_return(
        self,
        returns: pd.Series,
    ) -> pd.Series:
        """
        计算累计收益率

        Args:
            returns: 日收益率序列

        Returns:
            累计收益率序列
        """
        return (1 + returns).cumprod() - 1

    def calculate_drawdown(
        self,
        returns: pd.Series,
    ) -> pd.Series:
        """
        计算回撤序列

        Args:
            returns: 日收益率序列

        Returns:
            回撤序列
        """
        wealth = (1 + returns).cumprod()
        rolling_max = wealth.cummax()
        drawdown = (wealth - rolling_max) / rolling_max
        return drawdown

    def rolling_performance(self, returns: pd.Series, window: int = 60) -> pd.DataFrame:
        """
        滚动业绩分析 (FUND-ANALYZE-006)

        Args:
            returns: 日收益率序列
            window: 滚动窗口（交易日）

        Returns:
            滚动指标 DataFrame，包含 rolling_return, rolling_sharpe, rolling_volatility, rolling_max_drawdown
        """
        if len(returns) < window:
            return pd.DataFrame()

        rolling_ret = returns.rolling(window=window).apply(lambda x: (1 + x).prod() - 1) * 100
        rolling_vol = returns.rolling(window=window).std() * np.sqrt(252) * 100
        rolling_sharpe = (
            (rolling_ret / rolling_vol) if rolling_vol.notna().any() else pd.Series(dtype=float)
        )

        def _rolling_mdd(x):
            if len(x) == 0:
                return 0
            cumprod = (1 + x).cumprod()
            cummax = cumprod.cummax()
            return ((cummax - cumprod) / cummax).min() * 100

        rolling_mdd = returns.rolling(window=window).apply(_rolling_mdd)

        return pd.DataFrame(
            {
                "rolling_return": rolling_ret,
                "rolling_volatility": rolling_vol,
                "rolling_sharpe": rolling_sharpe,
                "rolling_max_drawdown": rolling_mdd,
            }
        ).dropna()

    def monthly_return_distribution(self, returns: pd.Series) -> dict[str, Any]:
        """
        月度收益分布 (FUND-ANALYZE-008)

        Args:
            returns: 日收益率序列

        Returns:
            月度分布统计字典
        """
        if returns.empty:
            return {
                "monthly_returns": [],
                "positive_months": 0,
                "negative_months": 0,
                "avg_monthly_return": 0,
                "max_month": 0,
                "min_month": 0,
            }

        monthly = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1) * 100
        monthly = monthly.dropna()

        positive = (monthly > 0).sum()
        negative = (monthly < 0).sum()

        return {
            "total_months": len(monthly),
            "positive_months": int(positive),
            "negative_months": int(negative),
            "win_rate": round(positive / len(monthly) * 100, 1) if len(monthly) > 0 else 0,
            "avg_monthly_return": round(monthly.mean(), 4),
            "std_monthly_return": round(monthly.std(), 4),
            "max_month": round(monthly.max(), 4),
            "min_month": round(monthly.min(), 4),
            "monthly_returns": monthly.to_dict(),
        }

    def scenario_analysis(
        self, returns: pd.Series, scenarios: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        情景分析 (FUND-ANALYZE-009)

        预定义情景：牛市(+20%年化)、熊市(-20%年化)、震荡市(0%年化)

        Args:
            returns: 日收益率序列
            scenarios: 自定义情景 {名称: 年化收益率}

        Returns:
            情景分析结果
        """
        if scenarios is None:
            scenarios = {
                "牛市": 0.20,
                "温和牛市": 0.10,
                "震荡市": 0.0,
                "温和熊市": -0.10,
                "熊市": -0.20,
            }

        results = {}
        for name, annual_return in scenarios.items():
            daily_return = (1 + annual_return) ** (1 / 252) - 1
            n_days = len(returns)
            simulated = np.random.normal(daily_return, returns.std(), n_days)
            total = (1 + pd.Series(simulated)).prod() - 1
            vol = pd.Series(simulated).std() * np.sqrt(252)
            results[name] = {
                "annual_return": round(annual_return * 100, 2),
                "simulated_total_return": round(total * 100, 2),
                "simulated_volatility": round(vol * 100, 2),
            }

        return results

    def performance_persistence(
        self, returns: pd.Series, periods_per_year: int = 12
    ) -> dict[str, Any]:
        """
        业绩持续性分析 (FUND-ANALYZE-010)

        Args:
            returns: 日收益率序列
            periods_per_year: 每年周期数

        Returns:
            持续性分析结果
        """
        if len(returns) < periods_per_year * 2:
            return {"persistence_score": 0, "message": "数据不足"}

        monthly = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
        monthly = monthly.dropna()

        if len(monthly) < 6:
            return {"persistence_score": 0, "message": "月度数据不足"}

        # 计算排名相关性（相邻周期排名的相关系数）
        half = len(monthly) // 2
        first_half = monthly.iloc[:half]
        second_half = monthly.iloc[half : 2 * half]

        if len(first_half) > 1 and len(second_half) > 1:
            rank_corr = first_half.rank().corr(second_half.rank())
        else:
            rank_corr = 0

        # 胜率
        win_rate = (monthly > 0).sum() / len(monthly) * 100

        # 连续正/负月数
        max_positive_streak = 0
        max_negative_streak = 0
        current_streak = 0
        current_sign = 1
        for val in monthly:
            sign = 1 if val > 0 else -1
            if sign == current_sign:
                current_streak += 1
            else:
                current_streak = 1
                current_sign = sign
            if sign == 1:
                max_positive_streak = max(max_positive_streak, current_streak)
            else:
                max_negative_streak = max(max_negative_streak, current_streak)

        persistence_score = max(0, min(100, (rank_corr + 1) * 50))

        return {
            "persistence_score": round(persistence_score, 1),
            "rank_correlation": round(rank_corr, 4),
            "monthly_win_rate": round(win_rate, 1),
            "max_positive_streak": max_positive_streak,
            "max_negative_streak": max_negative_streak,
            "total_months": len(monthly),
        }
