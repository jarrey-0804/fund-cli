"""
交叉验证器.

对 PerformanceAnalyzer 和 RiskAnalyzer 计算的相同指标进行交叉验证。
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CrossValidationResult:
    """交叉验证结果."""

    metric_name: str
    perf_value: float | None
    risk_value: float | None
    diff: float
    diff_percent: float
    passed: bool
    tolerance: float


class CrossValidator:
    """
    分析引擎交叉验证器.

    验证 PerformanceAnalyzer 和 RiskAnalyzer 对相同指标的计算结果是否一致。
    """

    # 需要交叉验证的指标及其容忍度
    CROSS_CHECK_METRICS = {
        "volatility": 0.01,  # 波动率差异容忍 1%
        "max_drawdown": 0.01,  # 最大回撤差异容忍 1%
        "var_95": 0.02,  # VaR差异容忍 2%
        "beta": 0.05,  # Beta差异容忍 5%
        "sharpe_ratio": 0.05,  # 夏普比率差异容忍 5%
    }

    def __init__(self, custom_tolerance: dict[str, float] | None = None):
        """
        初始化交叉验证器.

        Args:
            custom_tolerance: 自定义容忍度，覆盖默认值
        """
        self._tolerance = {**self.CROSS_CHECK_METRICS}
        if custom_tolerance:
            self._tolerance.update(custom_tolerance)

    def validate(
        self, perf_metrics: dict[str, float], risk_metrics: dict[str, float]
    ) -> list[CrossValidationResult]:
        """
        执行交叉验证.

        Args:
            perf_metrics: PerformanceAnalyzer 输出指标
            risk_metrics: RiskAnalyzer 输出指标

        Returns:
            验证结果列表
        """
        results = []

        for metric, tolerance in self._tolerance.items():
            perf_val = perf_metrics.get(metric)
            risk_val = risk_metrics.get(metric)

            result = self._check_metric(metric, perf_val, risk_val, tolerance)
            results.append(result)

            if not result.passed:
                logger.warning(
                    "交叉验证失败: %s - Performance=%.4f, Risk=%.4f, 差异=%.2f%%",
                    metric,
                    perf_val or 0,
                    risk_val or 0,
                    result.diff_percent * 100,
                )

        return results

    def _check_metric(
        self, name: str, perf_val: float | None, risk_val: float | None, tolerance: float
    ) -> CrossValidationResult:
        """检查单个指标."""
        # 处理 None 值
        if perf_val is None and risk_val is None:
            return CrossValidationResult(
                metric_name=name,
                perf_value=None,
                risk_value=None,
                diff=0.0,
                diff_percent=0.0,
                passed=True,
                tolerance=tolerance,
            )

        if perf_val is None or risk_val is None:
            return CrossValidationResult(
                metric_name=name,
                perf_value=perf_val,
                risk_value=risk_val,
                diff=float("inf"),
                diff_percent=1.0,
                passed=False,
                tolerance=tolerance,
            )

        # 计算差异
        diff = abs(perf_val - risk_val)

        # 计算百分比差异
        if risk_val != 0:
            diff_percent = diff / abs(risk_val)
        elif perf_val != 0:
            diff_percent = diff / abs(perf_val)
        else:
            diff_percent = 0.0

        passed = diff_percent <= tolerance

        return CrossValidationResult(
            metric_name=name,
            perf_value=perf_val,
            risk_value=risk_val,
            diff=diff,
            diff_percent=diff_percent,
            passed=passed,
            tolerance=tolerance,
        )

    def get_summary(self, results: list[CrossValidationResult]) -> dict:
        """
        获取验证摘要.

        Args:
            results: 验证结果列表

        Returns:
            摘要字典
        """
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        failed_metrics = [
            {"name": r.metric_name, "diff": r.diff, "diff_percent": r.diff_percent}
            for r in results
            if not r.passed
        ]

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "failed_metrics": failed_metrics,
        }
