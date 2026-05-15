"""
数据源健康检查器.

实现主动健康检查机制，定时探测数据源可用性，提前发现故障。
"""

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fund_cli.config import get_config
from fund_cli.core.alert_notifier import AlertLevel

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """健康状态."""

    source_name: str
    is_healthy: bool
    last_check: datetime
    response_time_ms: float
    consecutive_failures: int
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        return {
            "source_name": self.source_name,
            "is_healthy": self.is_healthy,
            "last_check": self.last_check.isoformat(),
            "response_time_ms": self.response_time_ms,
            "consecutive_failures": self.consecutive_failures,
            "error_message": self.error_message,
        }


class HealthChecker:
    """
    健康检查器.

    定时主动探测数据源健康状态，支持告警通知。
    """

    def __init__(self):
        """初始化健康检查器."""
        self._status: dict[str, HealthStatus] = {}
        self._check_interval: int = 60  # 默认60秒检查一次
        self._timeout: int = 10  # 默认10秒超时
        self._enabled: bool = True
        self._alert_threshold: int = 3  # 连续失败3次告警
        self._running: bool = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._gateway = None
        self._alert_notifier = None

        self._load_config()

    def _load_config(self) -> None:
        """加载配置."""
        config = get_config()
        health_config = getattr(config, "health_check", {})

        self._check_interval = health_config.get("interval", 60)
        self._timeout = health_config.get("timeout", 10)
        self._enabled = health_config.get("enabled", True)
        self._alert_threshold = health_config.get("alert_threshold", 3)

        try:
            from fund_cli.core.data_gateway import get_data_gateway

            self._gateway = get_data_gateway()
        except Exception as e:
            logger.warning("无法获取数据源网关: %s", e)

        try:
            from fund_cli.core.alert_notifier import get_alert_notifier

            self._alert_notifier = get_alert_notifier()
        except Exception as e:
            logger.warning("无法获取告警通知器: %s", e)

    def check_source(self, source_name: str) -> HealthStatus:
        """
        检查单个数据源健康状态.

        Args:
            source_name: 数据源名称

        Returns:
            健康状态
        """
        if not self._gateway:
            return HealthStatus(
                source_name=source_name,
                is_healthy=False,
                last_check=datetime.now(),
                response_time_ms=0,
                consecutive_failures=0,
                error_message="网关未初始化",
            )

        start_time = time.monotonic()
        is_healthy = False
        error_message = ""

        try:
            # 获取适配器并检查可用性
            adapter = self._gateway._adapters.get(source_name)
            if not adapter:
                error_message = f"适配器 {source_name} 不存在"
            else:
                # 使用超时机制检查可用性
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(adapter.is_available)
                    try:
                        is_healthy = future.result(timeout=self._timeout)
                    except concurrent.futures.TimeoutError:
                        error_message = f"检查超时（{self._timeout}秒）"
                    except Exception as e:
                        error_message = str(e)

        except Exception as e:
            error_message = str(e)

        response_time_ms = (time.monotonic() - start_time) * 1000

        # 更新状态
        with self._lock:
            old_status = self._status.get(source_name)
            consecutive_failures = 0

            if is_healthy:
                consecutive_failures = 0
            else:
                consecutive_failures = (old_status.consecutive_failures + 1) if old_status else 1

            status = HealthStatus(
                source_name=source_name,
                is_healthy=is_healthy,
                last_check=datetime.now(),
                response_time_ms=response_time_ms,
                consecutive_failures=consecutive_failures,
                error_message=error_message,
            )
            self._status[source_name] = status

            # 触发告警
            if (
                self._alert_notifier
                and consecutive_failures >= self._alert_threshold
                and (not old_status or old_status.consecutive_failures < self._alert_threshold)
            ):
                self._alert_notifier.alert_datasource_failure(
                    source_name=source_name,
                    error_message=f"连续{consecutive_failures}次健康检查失败: {error_message}",
                    level=AlertLevel.CRITICAL,
                )

        return status

    def check_all(self) -> dict[str, HealthStatus]:
        """
        检查所有数据源健康状态.

        Returns:
            各数据源健康状态字典
        """
        if not self._gateway:
            return {}

        results = {}
        for source_name in self._gateway._adapters.keys():
            results[source_name] = self.check_source(source_name)

        return results

    def get_status(self, source_name: str | None = None) -> HealthStatus | dict[str, HealthStatus]:
        """
        获取健康状态.

        Args:
            source_name: 数据源名称，None则返回所有

        Returns:
            健康状态
        """
        with self._lock:
            if source_name:
                return self._status.get(source_name)
            return dict(self._status)

    def start_monitoring(self) -> None:
        """启动定时监控."""
        if not self._enabled or self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("健康检查监控已启动，检查间隔: %d秒", self._check_interval)

    def stop_monitoring(self) -> None:
        """停止定时监控."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            logger.info("健康检查监控已停止")

    def _monitor_loop(self) -> None:
        """监控循环."""
        while self._running:
            try:
                self.check_all()
            except Exception as e:
                logger.error("健康检查循环异常: %s", e)

            # 等待下一次检查
            for _ in range(self._check_interval):
                if not self._running:
                    break
                time.sleep(1)

    def get_summary(self) -> dict[str, Any]:
        """
        获取健康检查摘要.

        Returns:
            摘要信息
        """
        with self._lock:
            total = len(self._status)
            healthy = sum(1 for s in self._status.values() if s.is_healthy)
            unhealthy = total - healthy

            return {
                "total_sources": total,
                "healthy": healthy,
                "unhealthy": unhealthy,
                "monitoring_enabled": self._enabled,
                "check_interval": self._check_interval,
                "sources": {name: status.to_dict() for name, status in self._status.items()},
            }


# 全局健康检查器实例
_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """获取全局健康检查器实例."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
