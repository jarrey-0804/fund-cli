"""监控预警集成测试"""


class TestMonitoringFlow:
    def test_pool_management_flow(self, tmp_path):
        """基金池管理完整流程"""
        from fund_cli.core.monitor import FundMonitor

        monitor = FundMonitor(config_dir=str(tmp_path / "test_monitor"))

        # 添加基金
        monitor.add_to_pool("000001")
        monitor.add_to_pool("000002", group="my_funds")
        monitor.add_to_pool("000003", group="my_funds")

        # 列出
        all_funds = monitor.list_pool()
        assert len(all_funds) == 3

        my_funds = monitor.list_pool("my_funds")
        assert len(my_funds) == 2

        # 移除
        monitor.remove_from_pool("000003", group="my_funds")
        assert len(monitor.list_pool("my_funds")) == 1

        # 持久化验证
        monitor2 = FundMonitor(config_dir=str(tmp_path / "test_monitor"))
        assert len(monitor2.list_pool()) == 2

    def test_monitor_rules_flow(self, tmp_path):
        """监控规则流程"""
        from fund_cli.core.monitor import FundMonitor

        monitor = FundMonitor(config_dir=str(tmp_path / "test_rules"))

        # 添加规则
        monitor.add_rule("000001", "nav_change", -3.0)
        monitor.add_rule("000002", "nav_change", -5.0)

        # 查询规则
        rules = monitor.get_rules()
        assert len(rules) == 2

        rules_001 = monitor.get_rules("000001")
        assert len(rules_001) == 1
        assert rules_001[0]["threshold"] == -3.0

    def test_data_quality_flow(self):
        """数据质量检查流程"""
        import numpy as np
        import pandas as pd

        from fund_cli.core.data_quality import DataQualityChecker

        # 创建模拟数据
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=200, freq="B")
        nav = 1.0 + np.cumsum(np.random.normal(0.001, 0.01, 200))

        nav_df = pd.DataFrame(
            {
                "nav_date": dates,
                "unit_nav": nav,
                "daily_return": np.random.normal(0.05, 1.5, 200),
            }
        )

        checker = DataQualityChecker.__new__(DataQualityChecker)
        # 不初始化 DM，直接测试检查方法

        completeness = checker.check_completeness(nav_df)
        assert completeness["score"] > 50
        assert completeness["total_rows"] == 200

        accuracy = checker.check_accuracy(nav_df)
        assert accuracy["score"] > 50

        timeliness = checker.check_timeliness(nav_df)
        assert timeliness["status"] in ("current", "recent", "outdated")
