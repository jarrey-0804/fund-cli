# -*- coding: utf-8 -*-
"""
监控预警命令测试

测试 monitor_cmd 模块的所有命令功能。
"""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from fund_cli.commands.monitor_cmd import app

runner = CliRunner()


@pytest.fixture
def mock_monitor():
    """Mock 基金监控器"""
    mock_mon = MagicMock()
    mock_mon.add_to_pool.return_value = None
    mock_mon.remove_from_pool.return_value = True
    mock_mon.list_pool.return_value = [
        {"code": "000001", "group": "default", "added_at": "2024-01-01T10:00:00"},
        {"code": "000002", "group": "default", "added_at": "2024-01-02T10:00:00"},
    ]
    mock_mon.add_rule.return_value = None
    mock_mon.get_rules.return_value = [
        {"fund_code": "000001", "rule_type": "nav_change", "threshold": -2.0},
        {"fund_code": "000002", "rule_type": "nav_change", "threshold": -3.0},
    ]
    mock_mon.get_all_fund_codes.return_value = ["000001", "000002"]
    mock_mon.check_nav_changes.return_value = [
        {"fund_code": "000001", "daily_return": -3.5, "threshold": -2.0, "alert_type": "nav_change"},
    ]
    return mock_mon


class TestMonitorAddCommand:
    """添加基金到监控池命令测试"""

    def test_add_help(self):
        """测试添加命令帮助"""
        result = runner.invoke(app, ["add", "--help"])
        assert result.exit_code == 0
        assert "基金代码" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_add_success(self, mock_get_monitor, mock_monitor):
        """测试成功添加基金"""
        mock_get_monitor.return_value = mock_monitor
        result = runner.invoke(app, ["add", "000001"])
        assert result.exit_code == 0
        assert "已添加" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_add_with_group(self, mock_get_monitor, mock_monitor):
        """测试添加基金到指定分组"""
        mock_get_monitor.return_value = mock_monitor
        result = runner.invoke(app, ["add", "000001", "--group", "test_group"])
        assert result.exit_code == 0
        mock_monitor.add_to_pool.assert_called_once_with("000001", "test_group")


class TestMonitorRemoveCommand:
    """从监控池移除基金命令测试"""

    def test_remove_help(self):
        """测试移除命令帮助"""
        result = runner.invoke(app, ["remove", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_remove_success(self, mock_get_monitor, mock_monitor):
        """测试成功移除基金"""
        mock_get_monitor.return_value = mock_monitor
        result = runner.invoke(app, ["remove", "000001"])
        assert result.exit_code == 0
        assert "已从监控池移除" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_remove_not_found(self, mock_get_monitor, mock_monitor):
        """测试移除不存在的基金"""
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.remove_from_pool.return_value = False
        result = runner.invoke(app, ["remove", "999999"])
        assert result.exit_code == 0
        assert "不在监控池中" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_remove_with_group(self, mock_get_monitor, mock_monitor):
        """测试从指定分组移除基金"""
        mock_get_monitor.return_value = mock_monitor
        result = runner.invoke(app, ["remove", "000001", "--group", "test_group"])
        assert result.exit_code == 0
        mock_monitor.remove_from_pool.assert_called_once()


class TestMonitorListCommand:
    """列出监控池命令测试"""

    def test_list_help(self):
        """测试列表命令帮助"""
        result = runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_list_success(self, mock_get_monitor, mock_monitor):
        """测试成功列出监控池"""
        mock_get_monitor.return_value = mock_monitor
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "000001" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_list_empty(self, mock_get_monitor, mock_monitor):
        """测试空监控池"""
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.list_pool.return_value = []
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "为空" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_list_with_group(self, mock_get_monitor, mock_monitor):
        """测试列出指定分组"""
        mock_get_monitor.return_value = mock_monitor
        result = runner.invoke(app, ["list", "--group", "test_group"])
        assert result.exit_code == 0
        mock_monitor.list_pool.assert_called_once_with("test_group")


class TestMonitorWatchCommand:
    """监控基金净值变动命令测试"""

    def test_watch_help(self):
        """测试监控命令帮助"""
        result = runner.invoke(app, ["watch", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_watch_success(self, mock_get_monitor, mock_monitor):
        """测试成功设置监控"""
        mock_get_monitor.return_value = mock_monitor
        result = runner.invoke(app, ["watch", "000001"])
        assert result.exit_code == 0
        assert "已开始监控" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_watch_with_threshold(self, mock_get_monitor, mock_monitor):
        """测试设置自定义阈值"""
        mock_get_monitor.return_value = mock_monitor
        result = runner.invoke(app, ["watch", "000001", "--threshold", "-5.0"])
        assert result.exit_code == 0
        mock_monitor.add_rule.assert_called_once()


class TestMonitorCheckCommand:
    """检查所有监控基金命令测试"""

    def test_check_help(self):
        """测试检查命令帮助"""
        result = runner.invoke(app, ["check", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_check_with_alerts(self, mock_get_monitor, mock_monitor):
        """测试检查有预警"""
        mock_get_monitor.return_value = mock_monitor
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0
        assert "预警" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_check_no_alerts(self, mock_get_monitor, mock_monitor):
        """测试检查无预警"""
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.check_nav_changes.return_value = []
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0
        assert "正常" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_check_empty_pool(self, mock_get_monitor, mock_monitor):
        """测试空监控池检查"""
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.get_all_fund_codes.return_value = []
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0
        assert "为空" in result.output


class TestMonitorAlertCommand:
    """查看预警规则命令测试"""

    def test_alert_help(self):
        """测试预警规则命令帮助"""
        result = runner.invoke(app, ["alert", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_alert_success(self, mock_get_monitor, mock_monitor):
        """测试成功查看预警规则"""
        mock_get_monitor.return_value = mock_monitor
        result = runner.invoke(app, ["alert"])
        assert result.exit_code == 0
        assert "nav_change" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_alert_empty(self, mock_get_monitor, mock_monitor):
        """测试无预警规则"""
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.get_rules.return_value = []
        result = runner.invoke(app, ["alert"])
        assert result.exit_code == 0
        assert "暂无" in result.output


class TestMonitorCommandEdgeCases:
    """边界情况测试"""

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_add_duplicate(self, mock_get_monitor, mock_monitor):
        """测试添加重复基金"""
        mock_get_monitor.return_value = mock_monitor
        # 模拟重复添加（应该被忽略）
        result = runner.invoke(app, ["add", "000001"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_list_multiple_groups(self, mock_get_monitor, mock_monitor):
        """测试多分组列表"""
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.list_pool.return_value = [
            {"code": "000001", "group": "group_a", "added_at": "2024-01-01"},
            {"code": "000002", "group": "group_b", "added_at": "2024-01-02"},
            {"code": "000003", "group": "group_a", "added_at": "2024-01-03"},
        ]
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "000001" in result.output
        assert "000002" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_check_multiple_alerts(self, mock_get_monitor, mock_monitor):
        """测试多个预警"""
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.check_nav_changes.return_value = [
            {"fund_code": "000001", "daily_return": -3.5, "threshold": -2.0},
            {"fund_code": "000002", "daily_return": -4.2, "threshold": -3.0},
        ]
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0
        assert "2" in result.output or "预警" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_watch_negative_threshold(self, mock_get_monitor, mock_monitor):
        """测试负阈值监控"""
        mock_get_monitor.return_value = mock_monitor
        result = runner.invoke(app, ["watch", "000001", "--threshold", "-5.0"])
        assert result.exit_code == 0
        assert "已开始监控" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_watch_positive_threshold(self, mock_get_monitor, mock_monitor):
        """测试正阈值监控（上涨预警）"""
        mock_get_monitor.return_value = mock_monitor
        result = runner.invoke(app, ["watch", "000001", "--threshold", "5.0"])
        assert result.exit_code == 0
        assert "已开始监控" in result.output

    @patch("fund_cli.commands.monitor_cmd._get_monitor")
    def test_alert_multiple_rules(self, mock_get_monitor, mock_monitor):
        """测试多条预警规则"""
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.get_rules.return_value = [
            {"fund_code": "000001", "rule_type": "nav_change", "threshold": -2.0},
            {"fund_code": "000001", "rule_type": "max_drawdown", "threshold": -10.0},
            {"fund_code": "000002", "rule_type": "nav_change", "threshold": -3.0},
        ]
        result = runner.invoke(app, ["alert"])
        assert result.exit_code == 0
        assert "nav_change" in result.output or "max_drawdown" in result.output
