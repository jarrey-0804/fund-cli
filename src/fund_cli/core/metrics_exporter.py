"""
质量指标可观测性导出器.

支持Prometheus/OpenTelemetry格式的指标导出。
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from fund_cli.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """指标."""

    name: str
    value: float
    metric_type: str  # counter, gauge, histogram
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""

    def to_prometheus(self) -> str:
        """转换为Prometheus格式."""
        labels_str = ",".join([f'{k}="{v}"' for k, v in self.labels.items()]) if self.labels else ""
        if labels_str:
            return f'{self.name}{{{labels_str}}} {self.value}'
        return f"{self.name} {self.value}"


class MetricsExporter:
    """
    指标导出器.

    收集和导出数据质量指标，支持Prometheus格式。
    """

    def __init__(self):
        """初始化指标导出器."""
        self._metrics: list[Metric] = []
        self._enabled = True
        self._load_config()

    def _load_config(self) -> None:
        """加载配置."""
        config = get_config()
        metrics_config = getattr(config, "metrics", {})
        self._enabled = metrics_config.get("enabled", True)

    def record_quality_score(
        self,
        fund_code: str,
        score: float,
        level: str,
    ) -> None:
        """
        记录质量评分指标.

        Args:
            fund_code: 基金代码
            score: 评分
            level: 级别
        """
        if not self._enabled:
            return

        self._metrics.append(Metric(
            name="fund_cli_quality_score",
            value=score,
            metric_type="gauge",
            labels={"fund_code": fund_code, "level": level},
            description="数据质量评分",
        ))

    def record_data_freshness(
        self,
        fund_code: str,
        hours_since_update: float,
    ) -> None:
        """
        记录数据新鲜度指标.

        Args:
            fund_code: 基金代码
            hours_since_update: 距离上次更新的小时数
        """
        if not self._enabled:
            return

        self._metrics.append(Metric(
            name="fund_cli_data_freshness_hours",
            value=hours_since_update,
            metric_type="gauge",
            labels={"fund_code": fund_code},
            description="数据新鲜度（小时）",
        ))

    def record_request_duration(
        self,
        operation: str,
        duration_seconds: float,
        source: str = "",
    ) -> None:
        """
        记录请求耗时指标.

        Args:
            operation: 操作名称
            duration_seconds: 耗时（秒）
            source: 数据源
        """
        if not self._enabled:
            return

        labels = {"operation": operation}
        if source:
            labels["source"] = source

        self._metrics.append(Metric(
            name="fund_cli_request_duration_seconds",
            value=duration_seconds,
            metric_type="histogram",
            labels=labels,
            description="请求耗时（秒）",
        ))

    def record_cache_hit(
        self,
        cache_type: str,
        hit: bool,
    ) -> None:
        """
        记录缓存命中率指标.

        Args:
            cache_type: 缓存类型
            hit: 是否命中
        """
        if not self._enabled:
            return

        self._metrics.append(Metric(
            name="fund_cli_cache_hit",
            value=1.0 if hit else 0.0,
            metric_type="counter",
            labels={"cache_type": cache_type, "result": "hit" if hit else "miss"},
            description="缓存命中",
        ))

    def record_error(
        self,
        error_type: str,
        source: str = "",
    ) -> None:
        """
        记录错误指标.

        Args:
            error_type: 错误类型
            source: 数据源
        """
        if not self._enabled:
            return

        labels = {"error_type": error_type}
        if source:
            labels["source"] = source

        self._metrics.append(Metric(
            name="fund_cli_errors_total",
            value=1.0,
            metric_type="counter",
            labels=labels,
            description="错误总数",
        ))

    def export_prometheus(self) -> str:
        """
        导出Prometheus格式指标.

        Returns:
            Prometheus格式字符串
        """
        lines = []

        # 按名称分组
        metrics_by_name: dict[str, list[Metric]] = {}
        for metric in self._metrics:
            if metric.name not in metrics_by_name:
                metrics_by_name[metric.name] = []
            metrics_by_name[metric.name].append(metric)

        # 生成Prometheus格式
        for name, metrics in metrics_by_name.items():
            if metrics:
                lines.append(f"# HELP {name} {metrics[0].description}")
                lines.append(f"# TYPE {name} {metrics[0].metric_type}")
                for metric in metrics:
                    lines.append(metric.to_prometheus())
                lines.append("")

        return "\n".join(lines)

    def export_dict(self) -> list[dict[str, Any]]:
        """
        导出字典格式指标.

        Returns:
            指标字典列表
        """
        return [
            {
                "name": m.name,
                "value": m.value,
                "type": m.metric_type,
                "labels": m.labels,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in self._metrics
        ]

    def clear(self) -> None:
        """清除所有指标."""
        self._metrics.clear()

    def get_summary(self) -> dict[str, Any]:
        """
        获取指标摘要.

        Returns:
            摘要信息
        """
        return {
            "total_metrics": len(self._metrics),
            "metric_names": list({m.name for m in self._metrics}),
        }


# 全局指标导出器实例
_exporter: MetricsExporter | None = None


def get_metrics_exporter() -> MetricsExporter:
    """获取全局指标导出器实例."""
    global _exporter
    if _exporter is None:
        _exporter = MetricsExporter()
    return _exporter
