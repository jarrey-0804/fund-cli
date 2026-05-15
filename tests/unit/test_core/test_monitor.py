"""基金监控管理器测试"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from fund_cli.core.monitor import FundMonitor


@pytest.fixture
def monitor(tmp_path):
    return FundMonitor(config_dir=str(tmp_path / "fund_cli"))


class TestPoolManagement:
    def test_add_to_pool(self, monitor):
        monitor.add_to_pool("000001")
        funds = monitor.list_pool("default")
        assert len(funds) == 1
        assert funds[0]["code"] == "000001"

    def test_add_duplicate(self, monitor):
        monitor.add_to_pool("000001")
        monitor.add_to_pool("000001")
        funds = monitor.list_pool("default")
        assert len(funds) == 1

    def test_add_to_custom_group(self, monitor):
        monitor.add_to_pool("000001", group="my_group")
        funds = monitor.list_pool("my_group")
        assert len(funds) == 1

    def test_remove_from_pool(self, monitor):
        monitor.add_to_pool("000001")
        result = monitor.remove_from_pool("000001")
        assert result is True
        assert len(monitor.list_pool("default")) == 0

    def test_remove_nonexistent(self, monitor):
        result = monitor.remove_from_pool("999999")
        assert result is False

    def test_remove_from_all_groups(self, monitor):
        monitor.add_to_pool("000001", group="g1")
        monitor.add_to_pool("000001", group="g2")
        result = monitor.remove_from_pool("000001")
        assert result is True
        assert len(monitor.list_pool("g1")) == 0
        assert len(monitor.list_pool("g2")) == 0

    def test_list_all(self, monitor):
        monitor.add_to_pool("000001", group="g1")
        monitor.add_to_pool("000002", group="g2")
        all_funds = monitor.list_pool()
        assert len(all_funds) == 2

    def test_create_pool(self, monitor):
        result = monitor.create_pool("new_pool")
        assert result is True
        assert "new_pool" in monitor.get_pool_names()

    def test_create_duplicate_pool(self, monitor):
        monitor.create_pool("test")
        result = monitor.create_pool("test")
        assert result is False

    def test_delete_pool(self, monitor):
        monitor.add_to_pool("000001", group="temp")
        result = monitor.delete_pool("temp")
        assert result is True
        assert "temp" not in monitor.get_pool_names()

    def test_delete_default_pool(self, monitor):
        result = monitor.delete_pool("default")
        assert result is False


class TestRules:
    def test_add_rule(self, monitor):
        monitor.add_rule("000001", "nav_change", -3.0)
        rules = monitor.get_rules("000001")
        assert len(rules) == 1
        assert rules[0]["threshold"] == -3.0

    def test_add_rule_with_default_threshold(self, monitor):
        """测试使用默认阈值添加规则."""
        monitor.add_rule("000001", "nav_change")
        rules = monitor.get_rules("000001")
        assert len(rules) == 1
        # 默认阈值应该是 -2.0
        assert rules[0]["threshold"] == -2.0

    def test_add_rule_invalid_type(self, monitor):
        """测试添加无效规则类型."""
        result = monitor.add_rule("000001", "invalid_type")
        assert result is False

    def test_get_all_rules(self, monitor):
        monitor.add_rule("000001")
        monitor.add_rule("000002")
        rules = monitor.get_rules()
        assert len(rules) == 2

    def test_filter_by_fund(self, monitor):
        monitor.add_rule("000001")
        monitor.add_rule("000002")
        rules = monitor.get_rules("000001")
        assert len(rules) == 1


class TestCheckNavChanges:
    """测试净值变动检查."""

    @patch("fund_cli.core.data_manager.DataManager")
    def test_check_nav_changes_below_threshold(self, mock_dm_cls, monitor):
        """测试净值变动低于阈值触发预警."""
        mock_dm = MagicMock()
        mock_nav = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=10),
            "daily_return": [-3.0, -1.0, 0.5, 1.0, -0.5, 2.0, -1.5, 0.0, 1.5, -2.5]
        })
        mock_dm.get_fund_nav.return_value = mock_nav
        mock_dm_cls.return_value = mock_dm

        alerts = monitor.check_nav_changes(["000001"], threshold=-2.0)

        # 应该有预警
        assert len(alerts) >= 1

    @patch("fund_cli.core.data_manager.DataManager")
    def test_check_nav_changes_above_threshold(self, mock_dm_cls, monitor):
        """测试净值变动高于阈值不触发预警."""
        mock_dm = MagicMock()
        mock_nav = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=10),
            "daily_return": [1.0, 0.5, 0.3, 0.2, 0.1, 0.4, 0.6, 0.2, 0.3, 0.5]
        })
        mock_dm.get_fund_nav.return_value = mock_nav
        mock_dm_cls.return_value = mock_dm

        alerts = monitor.check_nav_changes(["000001"], threshold=-2.0)

        # 不应该有预警
        assert len(alerts) == 0

    @patch("fund_cli.core.data_manager.DataManager")
    def test_check_nav_changes_empty_data(self, mock_dm_cls, monitor):
        """测试空数据情况."""
        mock_dm = MagicMock()
        mock_dm.get_fund_nav.return_value = pd.DataFrame()
        mock_dm_cls.return_value = mock_dm

        alerts = monitor.check_nav_changes(["000001"])

        # 应该返回空列表
        assert alerts == []

    @patch("fund_cli.core.data_manager.DataManager")
    def test_check_nav_changes_error(self, mock_dm_cls, monitor):
        """测试数据获取错误情况."""
        mock_dm = MagicMock()
        mock_dm.get_fund_nav.side_effect = Exception("数据获取失败")
        mock_dm_cls.return_value = mock_dm

        alerts = monitor.check_nav_changes(["000001"])

        # 应该返回空列表，不抛出异常
        assert alerts == []


class TestCheckRules:
    """测试规则检查."""

    @patch("fund_cli.core.data_manager.DataManager")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    @patch("fund_cli.analysis.risk.RiskAnalyzer")
    def test_check_rules_empty(self, mock_risk_cls, mock_perf_cls, mock_dm_cls, monitor):
        """测试无规则时检查."""
        alerts = monitor.check_rules("000001")
        assert alerts == []

    @patch("fund_cli.core.data_manager.DataManager")
    @patch("fund_cli.analysis.performance.PerformanceAnalyzer")
    @patch("fund_cli.analysis.risk.RiskAnalyzer")
    def test_check_rules_with_nav_change_rule(self, mock_risk_cls, mock_perf_cls, mock_dm_cls, monitor):
        """测试净值变动规则检查."""
        # 添加规则
        monitor.add_rule("000001", "nav_change", -2.0)

        # Mock 数据
        mock_dm = MagicMock()
        mock_nav = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=60),
            "daily_return": [0.1] * 59 + [-3.0]  # 最后一天大跌
        })
        mock_dm.get_fund_nav.return_value = mock_nav
        mock_dm_cls.return_value = mock_dm

        mock_perf = MagicMock()
        mock_perf.analyze.return_value = {"sharpe": 1.5, "volatility": 0.15}
        mock_perf_cls.return_value = mock_perf

        mock_risk = MagicMock()
        mock_risk.analyze.return_value = {"max_drawdown": -0.05, "volatility_annual": 0.15}
        mock_risk_cls.return_value = mock_risk

        alerts = monitor.check_rules("000001")

        # 应该触发预警
        assert len(alerts) >= 1


class TestPersistence:
    def test_save_and_load(self, monitor, tmp_path):
        monitor.add_to_pool("000001")
        monitor.add_rule("000001", threshold=-5.0)

        # 重新加载
        monitor2 = FundMonitor(config_dir=str(tmp_path / "fund_cli"))
        funds = monitor2.list_pool("default")
        assert len(funds) == 1
        rules = monitor2.get_rules("000001")
        assert len(rules) == 1


class TestUtility:
    def test_get_all_codes(self, monitor):
        monitor.add_to_pool("000001")
        monitor.add_to_pool("000002")
        monitor.add_to_pool("000003")
        codes = monitor.get_all_fund_codes()
        assert codes == ["000001", "000002", "000003"]

    def test_empty_pool_codes(self, monitor):
        assert monitor.get_all_fund_codes() == []

    def test_get_pool_names(self, monitor):
        """测试获取基金池名称列表."""
        monitor.add_to_pool("000001", group="group1")
        monitor.add_to_pool("000002", group="group2")

        names = monitor.get_pool_names()
        assert "group1" in names
        assert "group2" in names

    def test_repr(self, monitor):
        monitor.add_to_pool("000001")
        assert "FundMonitor" in repr(monitor)
