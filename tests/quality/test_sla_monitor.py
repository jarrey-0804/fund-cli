"""
SLA监控器测试.

验证数据质量和时效性SLA监控功能。
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from fund_cli.core.sla_monitor import (
    SLAConfig,
    SLAMonitor,
    SLAViolation,
    get_sla_monitor,
)


class TestSLAConfig(unittest.TestCase):
    """测试SLA配置."""

    def test_default_values(self):
        """测试默认值."""
        config = SLAConfig()

        self.assertEqual(config.freshness_hours, 24)
        self.assertEqual(config.availability_percent, 99.0)
        self.assertEqual(config.min_quality_score, 70.0)
        self.assertEqual(config.response_time_seconds, 5.0)

    def test_custom_values(self):
        """测试自定义值."""
        config = SLAConfig(
            freshness_hours=12,
            availability_percent=99.9,
            min_quality_score=80.0,
            response_time_seconds=3.0,
        )

        self.assertEqual(config.freshness_hours, 12)
        self.assertEqual(config.availability_percent, 99.9)
        self.assertEqual(config.min_quality_score, 80.0)
        self.assertEqual(config.response_time_seconds, 3.0)


class TestSLAViolation(unittest.TestCase):
    """测试SLA违规记录."""

    def test_violation_creation(self):
        """测试创建违规记录."""
        violation = SLAViolation(
            sla_type="freshness",
            fund_code="000001",
            expected="<24h",
            actual="48h",
            severity="warning",
            message="数据已过期 48 小时",
        )

        self.assertEqual(violation.sla_type, "freshness")
        self.assertEqual(violation.fund_code, "000001")
        self.assertEqual(violation.expected, "<24h")
        self.assertEqual(violation.actual, "48h")
        self.assertEqual(violation.severity, "warning")
        self.assertEqual(violation.message, "数据已过期 48 小时")
        self.assertIsInstance(violation.timestamp, datetime)


class TestSLAMonitor(unittest.TestCase):
    """测试SLA监控器."""

    def setUp(self):
        """设置测试环境."""
        self.monitor = SLAMonitor()
        self.monitor._alert_notifier = MagicMock()

    def test_get_sla_monitor_singleton(self):
        """测试全局单例."""
        monitor1 = get_sla_monitor()
        monitor2 = get_sla_monitor()
        self.assertIs(monitor1, monitor2)

    def test_check_freshness_pass(self):
        """测试新鲜度检查通过."""
        # 1小时前更新的数据，在24小时内
        last_update = datetime.now() - timedelta(hours=1)

        result = self.monitor.check_freshness("000001", last_update)

        self.assertIsNone(result)
        self.monitor._alert_notifier.send.assert_not_called()

    def test_check_freshness_warning(self):
        """测试新鲜度警告."""
        # 25小时前更新的数据，超过24小时
        last_update = datetime.now() - timedelta(hours=25)

        result = self.monitor.check_freshness("000001", last_update)

        self.assertIsNotNone(result)
        self.assertEqual(result.sla_type, "freshness")
        self.assertEqual(result.fund_code, "000001")
        self.assertEqual(result.severity, "info")
        self.monitor._alert_notifier.send.assert_called_once()

    def test_check_freshness_critical(self):
        """测试新鲜度严重警告."""
        # 50小时前更新的数据，超过48小时
        last_update = datetime.now() - timedelta(hours=50)

        result = self.monitor.check_freshness("000001", last_update)

        self.assertIsNotNone(result)
        self.assertEqual(result.severity, "warning")

    def test_check_quality_score_pass(self):
        """测试质量评分检查通过."""
        result = self.monitor.check_quality_score("000001", 85.0)

        self.assertIsNone(result)
        self.monitor._alert_notifier.send.assert_not_called()

    def test_check_quality_score_warning(self):
        """测试质量评分警告."""
        result = self.monitor.check_quality_score("000001", 60.0)

        self.assertIsNotNone(result)
        self.assertEqual(result.sla_type, "quality_score")
        self.assertEqual(result.severity, "warning")
        self.monitor._alert_notifier.send.assert_called_once()

    def test_check_quality_score_critical(self):
        """测试质量评分严重警告."""
        result = self.monitor.check_quality_score("000001", 40.0)

        self.assertIsNotNone(result)
        self.assertEqual(result.severity, "critical")

    def test_check_response_time_pass(self):
        """测试响应时间检查通过."""
        result = self.monitor.check_response_time("get_nav", 3.0)

        self.assertIsNone(result)
        self.monitor._alert_notifier.send.assert_not_called()

    def test_check_response_time_warning(self):
        """测试响应时间警告."""
        result = self.monitor.check_response_time("get_nav", 6.0)

        self.assertIsNotNone(result)
        self.assertEqual(result.sla_type, "response_time")
        self.assertEqual(result.severity, "info")

    def test_check_response_time_critical(self):
        """测试响应时间严重警告."""
        result = self.monitor.check_response_time("get_nav", 12.0)

        self.assertIsNotNone(result)
        self.assertEqual(result.severity, "warning")

    def test_notify_violation_without_notifier(self):
        """测试无通知器时不报错."""
        self.monitor._alert_notifier = None

        # 不应抛出异常
        violation = SLAViolation(
            sla_type="freshness",
            fund_code="000001",
            expected="<24h",
            actual="48h",
            severity="warning",
        )
        self.monitor._notify_violation(violation)

    def test_get_sla_status(self):
        """测试获取SLA状态."""
        status = self.monitor.get_sla_status()

        self.assertIn("freshness_hours", status)
        self.assertIn("availability_percent", status)
        self.assertIn("min_quality_score", status)
        self.assertIn("response_time_seconds", status)

    @patch("fund_cli.core.sla_monitor.get_config")
    def test_load_config(self, mock_get_config):
        """测试配置加载."""
        mock_config = MagicMock()
        mock_config.sla = {
            "freshness_hours": 12,
            "availability_percent": 99.9,
            "min_quality_score": 80.0,
            "response_time_seconds": 3.0,
        }
        mock_get_config.return_value = mock_config

        monitor = SLAMonitor()

        self.assertEqual(monitor._config.freshness_hours, 12)
        self.assertEqual(monitor._config.availability_percent, 99.9)
        self.assertEqual(monitor._config.min_quality_score, 80.0)
        self.assertEqual(monitor._config.response_time_seconds, 3.0)


if __name__ == "__main__":
    unittest.main()
