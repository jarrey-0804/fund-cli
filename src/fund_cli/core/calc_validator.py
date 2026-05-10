"""
计算结果验证器.

对分析引擎输出的计算结果进行合理性验证。
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MetricValidation:
    """单条指标验证结果."""

    name: str
    value: float
    lower_bound: float
    upper_bound: float
    passed: bool
    message: str = ""


# 合理性边界定义 (基于行业经验)
REASONABLE_BOUNDS = {
    "annualized_return": (-0.5, 2.0),  # 年化收益率 -50% ~ 200%
    "sharpe_ratio": (-3.0, 5.0),  # 夏普比率
    "max_drawdown": (-1.0, 0.0),  # 最大回撤 -100% ~ 0%
    "volatility": (0.0, 1.0),  # 波动率 0% ~ 100%
    "beta": (-2.0, 3.0),  # Beta系数
    "sortino_ratio": (-3.0, 5.0),  # 索提诺比率
    "calmar_ratio": (-5.0, 10.0),  # 卡玛比率
    "information_ratio": (-3.0, 5.0),  # 信息比率
    "var_95": (-0.5, 0.0),  # VaR(95%) -50% ~ 0%
    "tracking_error": (0.0, 0.5),  # 跟踪误差
    "r_squared": (0.0, 1.0),  # R-squared
    "alpha": (-0.5, 0.5),  # Alpha
}


class CalcValidator:
    """
    计算结果验证器.

    验证分析引擎输出的各项指标是否在合理范围内。
    """

    def __init__(self, custom_bounds: dict[str, tuple[float, float]] | None = None):
        """
        初始化验证器.

        Args:
            custom_bounds: 自定义边界，会覆盖默认值
        """
        self._bounds = {**REASONABLE_BOUNDS}
        if custom_bounds:
            self._bounds.update(custom_bounds)
        # Read NaN threshold from config
        self._default_nan_threshold = 0.2
        try:
            from fund_cli.config import get_config

            config = get_config()
            self._default_nan_threshold = config.quality.max_nan_ratio
        except Exception:
            pass

    def validate_metric(self, name: str, value: float) -> MetricValidation:
        """
        验证单个指标.

        Args:
            name: 指标名称
            value: 指标值

        Returns:
            验证结果
        """
        if name not in self._bounds:
            return MetricValidation(
                name=name,
                value=value,
                lower_bound=0,
                upper_bound=0,
                passed=True,
                message=f"未知指标 {name}, 跳过验证",
            )

        lower, upper = self._bounds[name]

        # NaN check
        if value is None or (isinstance(value, float) and value != value):  # NaN check
            return MetricValidation(
                name=name,
                value=value,
                lower_bound=lower,
                upper_bound=upper,
                passed=False,
                message="值为 NaN",
            )

        passed = lower <= value <= upper
        message = "" if passed else f"{name}={value:.4f} 超出合理范围 [{lower}, {upper}]"

        if not passed:
            logger.warning("计算验证警告: %s", message)

        return MetricValidation(
            name=name,
            value=value,
            lower_bound=lower,
            upper_bound=upper,
            passed=passed,
            message=message,
        )

    def validate_metrics(self, metrics: dict[str, float]) -> list[MetricValidation]:
        """
        批量验证指标.

        Args:
            metrics: 指标字典 {名称: 值}

        Returns:
            验证结果列表
        """
        results = []
        for name, value in metrics.items():
            if value is not None:
                results.append(self.validate_metric(name, value))
        return results

    def check_nan_ratio(
        self, metrics: dict[str, float], threshold: float = 0.2
    ) -> tuple[bool, str]:
        """
        检查 NaN 比例.

        Args:
            metrics: 指标字典
            threshold: NaN 比例阈值 (默认 20%)

        Returns:
            (是否通过, 描述信息)
        """
        total = len(metrics)
        if total == 0:
            return True, "无指标"

        nan_count = sum(
            1 for v in metrics.values() if v is None or (isinstance(v, float) and v != v)
        )

        ratio = nan_count / total
        passed = ratio <= threshold
        msg = f"NaN 比例: {ratio:.1%} ({nan_count}/{total})"

        if not passed:
            logger.warning("计算验证警告: %s, 超过阈值 %.0f%%", msg, threshold * 100)

        return passed, msg

    def get_summary(self, results: list[MetricValidation]) -> dict:
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
        warnings = [r for r in results if not r.passed]

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "warnings": [{"name": r.name, "message": r.message} for r in warnings],
        }
