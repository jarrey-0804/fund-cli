"""基金监控管理器测试"""

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

    def test_repr(self, monitor):
        monitor.add_to_pool("000001")
        assert "FundMonitor" in repr(monitor)
