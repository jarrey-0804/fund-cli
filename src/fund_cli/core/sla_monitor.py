"""
SLA监控器.

监控数据质量和时效性SLA，支持违规告警。
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from fund_cli.config import get_config
from fund_cli.core.alert_notifier import AlertLevel, get_alert_notifier

logger = logging.getLogger(__name__)


@dataclass
class SLAConfig:
    """SLA配置."""

    # 数据新鲜度SLA（小时）
    freshness_hours: int = 24
    # 数据可用性SLA（百分比）
    availability_percent: float = 99.0
    # 质量评分SLA
    min_quality_score: float = 70.0
    # 响应时间SLA（秒）
    response_time_seconds: float = 5.0


@dataclass
class SLAViolation:
    """SLA违规记录."""

    sla_type: str
    fund_code: Optional[str]
    expected: Any
    actual: Any
    severity: str
    timestamp: datetime = field(default_factory=datetime.now)
    message: str = ""


class SLAMonitor:
    """
    SLA监控器.

    监控数据质量和时效性SLA，违规时触发告警。
    """

    def __init__(self):
        """初始化SLA监控器."""
        self._config = SLAConfig()
        self._alert_notifier = None
        self._load_config()

    def _load_config(self) -> None:
        """加载配置."""
        config = get_config()
        sla_config = getattr(config, "sla", {})

        self._config.freshness_hours = sla_config.get("freshness_hours", 24)
        self._config.availability_percent = sla_config.get("availability_percent", 99.0)
        self._config.min_quality_score = sla_config.get("min_quality_score", 70.0)
        self._config.response_time_seconds = sla_config.get("response_time_seconds", 5.0)

        try:
            from fund_cli.core.alert_notifier import get_alert_notifier
            self._alert_notifier = get_alert_notifier()
        except Exception as e:
            logger.warning(f"无法获取告警通知器: {e}")

    def check_freshness(
        self,
        fund_code: str,
        last_update: datetime,
    ) -> Optional[SLAViolation]:
        """
        检查数据新鲜度SLA.

        Args:
            fund_code: 基金代码
            last_update: 最后更新时间

        Returns:
            违规记录或None
        """
        hours_since_update = (datetime.now() - last_update).total_seconds() / 3600

        if hours_since_update > self._config.freshness_hours:
            violation = SLAViolation(
                sla_type="freshness",
                fund_code=fund_code,
                expected=f"<{self._config.freshness_hours}h",
                actual=f"{hours_since_update:.1f}h",
                severity="warning" if hours_since_update > self._config.freshness_hours * 2 else "info",
                message=f"数据已过期 {hours_since_update:.1f} 小时",
            )
            self._notify_violation(violation)
            return violation

        return None

    def check_quality_score(
        self,
        fund_code: str,
        quality_score: float,
    ) -> Optional[SLAViolation]:
        """
        检查质量评分SLA.

        Args:
            fund_code: 基金代码
            quality_score: 质量评分

        Returns:
            违规记录或None
        """
        if quality_score < self._config.min_quality_score:
            violation = SLAViolation(
                sla_type="quality_score",
                fund_code=fund_code,
                expected=f">={self._config.min_quality_score}",
                actual=f"{quality_score:.1f}",
                severity="critical" if quality_score < 50 else "warning",
                message=f"质量评分 {quality_score:.1f} 低于SLA要求 {self._config.min_quality_score}",
            )
            self._notify_violation(violation)
            return violation

        return None

    def check_response_time(
        self,
        operation: str,
        response_time_seconds: float,
    ) -> Optional[SLAViolation]:
        """
        检查响应时间SLA.

        Args:
            operation: 操作名称
            response_time_seconds: 响应时间（秒）

        Returns:
            违规记录或None
        """
        if response_time_seconds > self._config.response_time_seconds:
            violation = SLAViolation(
                sla_type="response_time",
                fund_code=None,
                expected=f"<{self._config.response_time_seconds}s",
                actual=f"{response_time_seconds:.2f}s",
                severity="warning" if response_time_seconds > self._config.response_time_seconds * 2 else "info",
                message=f"操作 {operation} 响应时间 {response_time_seconds:.2f}s 超过SLA",
            )
            self._notify_violation(violation)
            return violation

        return None

    def _notify_violation(self, violation: SLAViolation) -> None:
        """通知SLA违规."""
        if not self._alert_notifier:
            return

        from fund_cli.core.alert_notifier import AlertMessage, AlertLevel

        level = AlertLevel.WARNING if violation.severity == "warning" else AlertLevel.CRITICAL

        self._alert_notifier.send(
            message=AlertMessage(
                title=f"SLA违规: {violation.sla_type}",
                content=violation.message,
                level=level,
                metadata={
                    "sla_type": violation.sla_type,
                    "fund_code": violation.fund_code,
                    "expected": str(violation.expected),
                    "actual": str(violation.actual),
                },
            ),
        )

    def get_sla_status(self) -> dict[str, Any]:
        """
        获取SLA状态.

        Returns:
            SLA状态字典
        """
        return {
            "freshness_hours": self._config.freshness_hours,
            "availability_percent": self._config.availability_percent,
            "min_quality_score": self._config.min_quality_score,
            "response_time_seconds": self._config.response_time_seconds,
        }


# 全局SLA监控器实例
_sla_monitor: Optional[SLAMonitor] = None


def get_sla_monitor() -> SLAMonitor:
    """获取全局SLA监控器实例."""
    global _sla_monitor
    if _sla_monitor is None:
        _sla_monitor = SLAMonitor()
    return _sla_monitor
