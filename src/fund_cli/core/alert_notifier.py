"""
主动告警通知系统.

支持多渠道告警：Webhook、邮件、CLI通知。
与 FundMonitor 和 AuditLogger 集成，实现定时巡检和主动推送。
"""

import json
import logging
import smtplib
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.text import MIMEText
from enum import Enum
from typing import Any

from fund_cli.config import get_config

logger = logging.getLogger(__name__)


class AlertChannel(Enum):
    """告警渠道."""

    WEBHOOK = "webhook"
    EMAIL = "email"
    CLI = "cli"


class AlertLevel(Enum):
    """告警级别."""

    CRITICAL = "critical"  # 严重
    WARNING = "warning"    # 警告
    INFO = "info"          # 信息


@dataclass
class AlertMessage:
    """告警消息."""

    title: str
    content: str
    level: AlertLevel = AlertLevel.INFO
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        return {
            "title": self.title,
            "content": self.content,
            "level": self.level.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    def to_markdown(self) -> str:
        """转换为 Markdown 格式."""
        level_emoji = {
            AlertLevel.CRITICAL: "🔴",
            AlertLevel.WARNING: "🟡",
            AlertLevel.INFO: "🟢",
        }.get(self.level, "⚪")

        return f"""{level_emoji} **{self.title}**

**级别**: {self.level.value.upper()}
**时间**: {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}

{self.content}
"""


@dataclass
class WebhookConfig:
    """Webhook 配置."""

    url: str
    headers: dict[str, str] = field(default_factory=dict)
    timeout: int = 30


@dataclass
class EmailConfig:
    """邮件配置."""

    smtp_host: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True
    from_addr: str = ""
    to_addrs: list[str] = field(default_factory=list)


class AlertNotifier:
    """
    告警通知器.

    支持多渠道告警通知，与监控和审计系统集成。
    """

    def __init__(self):
        """初始化告警通知器."""
        self._webhook_configs: list[WebhookConfig] = []
        self._email_config: EmailConfig | None = None
        self._cli_enabled: bool = True
        self._min_level: AlertLevel = AlertLevel.INFO

        self._load_config()

    def _load_config(self) -> None:
        """加载配置."""
        config = get_config()
        alert_config = getattr(config, "alert", {})

        # 加载 Webhook 配置
        webhooks = alert_config.get("webhooks", [])
        for webhook in webhooks:
            if webhook.get("enabled", True):
                self._webhook_configs.append(
                    WebhookConfig(
                        url=webhook["url"],
                        headers=webhook.get("headers", {}),
                        timeout=webhook.get("timeout", 30),
                    )
                )

        # 加载邮件配置
        email = alert_config.get("email", {})
        if email.get("enabled", False):
            self._email_config = EmailConfig(
                smtp_host=email["smtp_host"],
                smtp_port=email["smtp_port"],
                username=email["username"],
                password=email["password"],
                use_tls=email.get("use_tls", True),
                from_addr=email.get("from_addr", email["username"]),
                to_addrs=email.get("to_addrs", []),
            )

        # 加载 CLI 配置
        self._cli_enabled = alert_config.get("cli_enabled", True)

        # 加载最小告警级别
        level_str = alert_config.get("min_level", "info")
        self._min_level = AlertLevel(level_str.lower())

    def send(self, message: AlertMessage) -> dict[str, bool]:
        """
        发送告警.

        Args:
            message: 告警消息

        Returns:
            各渠道发送结果
        """
        # 检查级别
        if self._level_priority(message.level) < self._level_priority(self._min_level):
            return {}

        results = {}

        # CLI 通知
        if self._cli_enabled:
            results["cli"] = self._send_cli(message)

        # Webhook 通知
        for i, webhook_config in enumerate(self._webhook_configs):
            results[f"webhook_{i}"] = self._send_webhook(message, webhook_config)

        # 邮件通知
        if self._email_config:
            results["email"] = self._send_email(message, self._email_config)

        return results

    def _send_cli(self, message: AlertMessage) -> bool:
        """发送 CLI 通知."""
        try:
            level_color = {
                AlertLevel.CRITICAL: "\033[91m",  # 红色
                AlertLevel.WARNING: "\033[93m",  # 黄色
                AlertLevel.INFO: "\033[92m",     # 绿色
            }.get(message.level, "")
            reset_color = "\033[0m"

            print(f"\n{level_color}[ALERT] {message.title}{reset_color}")
            print(f"级别: {message.level.value.upper()}")
            print(f"时间: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"内容: {message.content}")
            if message.metadata:
                print(f"元数据: {json.dumps(message.metadata, ensure_ascii=False)}")
            print()

            return True
        except Exception as e:
            logger.error("CLI 通知失败: %s", e)
            return False

    def _send_webhook(self, message: AlertMessage, config: WebhookConfig) -> bool:
        """发送 Webhook 通知."""
        try:
            payload = json.dumps(message.to_dict(), ensure_ascii=False).encode("utf-8")

            req = urllib.request.Request(
                config.url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    **config.headers,
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=config.timeout) as response:
                return response.status == 200

        except Exception as e:
            logger.error("Webhook 通知失败: %s", e)
            return False

    def _send_email(self, message: AlertMessage, config: EmailConfig) -> bool:
        """发送邮件通知."""
        try:
            msg = MIMEText(message.to_markdown(), "plain", "utf-8")
            msg["Subject"] = f"[{message.level.value.upper()}] {message.title}"
            msg["From"] = config.from_addr
            msg["To"] = ", ".join(config.to_addrs)

            with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
                if config.use_tls:
                    server.starttls()
                server.login(config.username, config.password)
                server.sendmail(config.from_addr, config.to_addrs, msg.as_string())

            return True

        except Exception as e:
            logger.error("邮件通知失败: %s", e)
            return False

    def _level_priority(self, level: AlertLevel) -> int:
        """获取告警级别优先级."""
        return {
            AlertLevel.CRITICAL: 3,
            AlertLevel.WARNING: 2,
            AlertLevel.INFO: 1,
        }.get(level, 0)

    def alert_data_quality(
        self,
        fund_code: str,
        quality_score: float,
        issues: list[str],
        level: AlertLevel = AlertLevel.WARNING,
    ) -> dict[str, bool]:
        """
        数据质量告警.

        Args:
            fund_code: 基金代码
            quality_score: 质量评分
            issues: 问题列表
            level: 告警级别

        Returns:
            发送结果
        """
        message = AlertMessage(
            title=f"基金 {fund_code} 数据质量异常",
            content=f"质量评分: {quality_score:.1f}/100\n\n发现问题:\n" + "\n".join(f"- {issue}" for issue in issues),
            level=level,
            metadata={"fund_code": fund_code, "quality_score": quality_score},
        )
        return self.send(message)

    def alert_monitor_trigger(
        self,
        fund_code: str,
        rule_name: str,
        current_value: float,
        threshold: float,
        level: AlertLevel = AlertLevel.WARNING,
    ) -> dict[str, bool]:
        """
        监控规则触发告警.

        Args:
            fund_code: 基金代码
            rule_name: 规则名称
            current_value: 当前值
            threshold: 阈值
            level: 告警级别

        Returns:
            发送结果
        """
        message = AlertMessage(
            title=f"基金 {fund_code} 监控告警: {rule_name}",
            content=f"当前值: {current_value:.4f}\n阈值: {threshold:.4f}",
            level=level,
            metadata={
                "fund_code": fund_code,
                "rule_name": rule_name,
                "current_value": current_value,
                "threshold": threshold,
            },
        )
        return self.send(message)

    def alert_datasource_failure(
        self,
        source_name: str,
        error_message: str,
        level: AlertLevel = AlertLevel.CRITICAL,
    ) -> dict[str, bool]:
        """
        数据源故障告警.

        Args:
            source_name: 数据源名称
            error_message: 错误信息
            level: 告警级别

        Returns:
            发送结果
        """
        message = AlertMessage(
            title=f"数据源 {source_name} 故障",
            content=f"错误信息: {error_message}",
            level=level,
            metadata={"source_name": source_name},
        )
        return self.send(message)

    def get_status(self) -> dict[str, Any]:
        """
        获取通知器状态.

        Returns:
            状态信息字典
        """
        return {
            "cli_enabled": self._cli_enabled,
            "webhook_count": len(self._webhook_configs),
            "email_enabled": self._email_config is not None,
            "min_level": self._min_level.value,
        }


# 全局通知器实例
_notifier: AlertNotifier | None = None


def get_alert_notifier() -> AlertNotifier:
    """获取全局告警通知器实例."""
    global _notifier
    if _notifier is None:
        _notifier = AlertNotifier()
    return _notifier
