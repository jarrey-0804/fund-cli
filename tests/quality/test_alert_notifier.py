"""
告警通知器测试.

验证主动告警通知功能。
"""

import unittest
from unittest.mock import patch

from fund_cli.core.alert_notifier import (
    AlertLevel,
    AlertMessage,
    AlertNotifier,
    get_alert_notifier,
)


class TestAlertMessage(unittest.TestCase):
    """测试告警消息."""

    def test_to_dict(self):
        """测试转换为字典."""
        message = AlertMessage(
            title="测试告警",
            content="测试内容",
            level=AlertLevel.WARNING,
            metadata={"key": "value"},
        )

        result = message.to_dict()

        self.assertEqual(result["title"], "测试告警")
        self.assertEqual(result["content"], "测试内容")
        self.assertEqual(result["level"], "warning")
        self.assertEqual(result["metadata"], {"key": "value"})

    def test_to_markdown(self):
        """测试转换为 Markdown."""
        message = AlertMessage(
            title="测试告警",
            content="测试内容",
            level=AlertLevel.CRITICAL,
        )

        result = message.to_markdown()

        self.assertIn("🔴", result)
        self.assertIn("测试告警", result)
        self.assertIn("CRITICAL", result)


class TestAlertNotifier(unittest.TestCase):
    """测试告警通知器."""

    def setUp(self):
        """设置测试环境."""
        self.notifier = AlertNotifier()
        # 禁用邮件和 webhook，只保留 CLI
        self.notifier._webhook_configs = []
        self.notifier._email_config = None
        self.notifier._cli_enabled = True

    def test_get_alert_notifier_singleton(self):
        """测试全局单例."""
        notifier1 = get_alert_notifier()
        notifier2 = get_alert_notifier()
        self.assertIs(notifier1, notifier2)

    def test_send_cli_notification(self):
        """测试发送 CLI 通知."""
        message = AlertMessage(
            title="测试告警",
            content="测试内容",
            level=AlertLevel.INFO,
        )

        with patch("builtins.print") as mock_print:
            result = self.notifier._send_cli(message)

        self.assertTrue(result)
        mock_print.assert_called()

    def test_level_filtering(self):
        """测试告警级别过滤."""
        self.notifier._min_level = AlertLevel.WARNING

        # INFO 级别应该被过滤
        info_message = AlertMessage(
            title="信息",
            content="内容",
            level=AlertLevel.INFO,
        )
        result = self.notifier.send(info_message)
        self.assertEqual(result, {})  # 被过滤，无结果

        # WARNING 级别应该通过
        warning_message = AlertMessage(
            title="警告",
            content="内容",
            level=AlertLevel.WARNING,
        )
        result = self.notifier.send(warning_message)
        self.assertIn("cli", result)

    def test_alert_data_quality(self):
        """测试数据质量告警."""
        with patch.object(self.notifier, "send") as mock_send:
            self.notifier.alert_data_quality(
                fund_code="000001",
                quality_score=45.0,
                issues=["数据缺失", "异常值"],
                level=AlertLevel.WARNING,
            )

            mock_send.assert_called_once()
            message = mock_send.call_args[0][0]
            self.assertEqual(message.title, "基金 000001 数据质量异常")
            self.assertIn("45.0", message.content)

    def test_alert_monitor_trigger(self):
        """测试监控规则触发告警."""
        with patch.object(self.notifier, "send") as mock_send:
            self.notifier.alert_monitor_trigger(
                fund_code="000001",
                rule_name="日收益率预警",
                current_value=-0.05,
                threshold=-0.02,
                level=AlertLevel.WARNING,
            )

            mock_send.assert_called_once()
            message = mock_send.call_args[0][0]
            self.assertEqual(message.title, "基金 000001 监控告警: 日收益率预警")

    def test_alert_datasource_failure(self):
        """测试数据源故障告警."""
        with patch.object(self.notifier, "send") as mock_send:
            self.notifier.alert_datasource_failure(
                source_name="akshare",
                error_message="连接超时",
                level=AlertLevel.CRITICAL,
            )

            mock_send.assert_called_once()
            message = mock_send.call_args[0][0]
            self.assertEqual(message.title, "数据源 akshare 故障")

    def test_get_status(self):
        """测试获取通知器状态."""
        status = self.notifier.get_status()

        self.assertIn("cli_enabled", status)
        self.assertIn("webhook_count", status)
        self.assertIn("email_enabled", status)
        self.assertIn("min_level", status)


if __name__ == "__main__":
    unittest.main()
