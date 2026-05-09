# -*- coding: utf-8 -*-
"""
数据质量检查器补充测试

测试覆盖：
- 初始化
- batch_download 方法
- incremental_update 方法
- 异常处理
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from fund_cli.core.data_quality import DataQualityChecker


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_data_manager():
    """创建模拟数据管理器"""
    dm = MagicMock()
    dm._cache = MagicMock()
    return dm


@pytest.fixture
def checker_with_mock_dm(mock_data_manager):
    """创建带模拟数据管理器的检查器"""
    checker = DataQualityChecker.__new__(DataQualityChecker)
    checker._dm = mock_data_manager
    return checker


# =============================================================================
# 初始化测试
# =============================================================================


class TestInit:
    """测试初始化"""

    def test_init_with_data_manager(self):
        """测试使用数据管理器初始化"""
        mock_dm = MagicMock()
        checker = DataQualityChecker(data_manager=mock_dm)
        assert checker._dm is mock_dm

    def test_init_without_data_manager(self):
        """测试不使用数据管理器初始化"""
        # DataManager 在 __init__ 方法内部导入
        # 这个测试验证初始化不会抛出异常
        with patch("fund_cli.core.data_manager.DataManager") as mock_dm_class:
            mock_dm_instance = MagicMock()
            mock_dm_class.return_value = mock_dm_instance
            checker = DataQualityChecker()
            assert checker._dm is mock_dm_instance


# =============================================================================
# incremental_update 方法测试
# =============================================================================


class TestIncrementalUpdate:
    """测试 incremental_update 方法"""

    def test_incremental_update_success(self, checker_with_mock_dm, mock_data_manager):
        """测试增量更新成功"""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # 无缓存
        mock_data_manager._cache = mock_cache

        new_data = pd.DataFrame({
            "nav_date": ["2024-01-01", "2024-01-02"],
            "unit_nav": [1.5, 1.51],
        })
        mock_data_manager.get_fund_nav.return_value = new_data

        result = checker_with_mock_dm.incremental_update("000001")

        assert result["fund_code"] == "000001"
        assert result["status"] == "success"
        assert "new_records" in result

    def test_incremental_update_error(self, checker_with_mock_dm, mock_data_manager):
        """测试增量更新失败"""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_data_manager._cache = mock_cache
        mock_data_manager.get_fund_nav.side_effect = Exception("网络错误")

        result = checker_with_mock_dm.incremental_update("000001")

        assert result["status"] == "error"
        assert "网络错误" in result["message"]

    def test_incremental_update_empty_cache(self, checker_with_mock_dm, mock_data_manager):
        """测试空缓存的增量更新"""
        mock_cache = MagicMock()
        mock_cache.get.return_value = pd.DataFrame()
        mock_data_manager._cache = mock_cache

        new_data = pd.DataFrame({
            "nav_date": ["2024-01-01", "2024-01-02"],
            "unit_nav": [1.5, 1.51],
        })
        mock_data_manager.get_fund_nav.return_value = new_data

        result = checker_with_mock_dm.incremental_update("000001")

        assert result["status"] == "success"


# =============================================================================
# batch_download 方法测试
# =============================================================================


class TestBatchDownload:
    """测试 batch_download 方法"""

    def test_batch_download_all_success(self, checker_with_mock_dm, mock_data_manager):
        """测试批量下载全部成功"""
        mock_data_manager.get_fund_nav.return_value = pd.DataFrame({
            "nav_date": ["2024-01-01"],
            "unit_nav": [1.5],
        })

        result = checker_with_mock_dm.batch_download(["000001", "000002", "000003"])

        assert result["total"] == 3
        assert result["success"] == 3
        assert result["failed"] == 0

    def test_batch_download_partial_success(self, checker_with_mock_dm, mock_data_manager):
        """测试批量下载部分成功"""
        call_count = [0]

        def side_effect(code):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("获取失败")
            return pd.DataFrame({"nav_date": ["2024-01-01"], "unit_nav": [1.5]})

        mock_data_manager.get_fund_nav.side_effect = side_effect

        result = checker_with_mock_dm.batch_download(["000001", "000002", "000003"])

        assert result["total"] == 3
        assert result["success"] == 2
        assert result["failed"] == 1

    def test_batch_download_all_failed(self, checker_with_mock_dm, mock_data_manager):
        """测试批量下载全部失败"""
        mock_data_manager.get_fund_nav.side_effect = Exception("网络错误")

        result = checker_with_mock_dm.batch_download(["000001", "000002"])

        assert result["total"] == 2
        assert result["success"] == 0
        assert result["failed"] == 2

    def test_batch_download_empty_list(self, checker_with_mock_dm, mock_data_manager):
        """测试批量下载空列表"""
        result = checker_with_mock_dm.batch_download([])

        assert result["total"] == 0
        assert result["success"] == 0
        assert result["failed"] == 0

    def test_batch_download_details(self, checker_with_mock_dm, mock_data_manager):
        """测试批量下载详情"""
        call_count = [0]

        def side_effect(code):
            call_count[0] += 1
            if code == "000002":
                raise Exception("获取失败")
            return pd.DataFrame({"nav_date": ["2024-01-01"], "unit_nav": [1.5]})

        mock_data_manager.get_fund_nav.side_effect = side_effect

        result = checker_with_mock_dm.batch_download(["000001", "000002"])

        assert "details" in result
        assert result["details"]["000001"]["status"] == "success"
        assert result["details"]["000002"]["status"] == "error"


# =============================================================================
# check 方法测试
# =============================================================================


class TestCheckMethod:
    """测试 check 方法"""

    def test_check_with_empty_data(self, checker_with_mock_dm, mock_data_manager):
        """测试空数据"""
        mock_data_manager.get_fund_nav.return_value = pd.DataFrame()

        result = checker_with_mock_dm.check("000001")

        assert result["fund_code"] == "000001"
        assert result["status"] == "error"
        assert result["message"] == "无数据"

    def test_check_with_exception(self, checker_with_mock_dm, mock_data_manager):
        """测试异常情况"""
        mock_data_manager.get_fund_nav.side_effect = Exception("网络错误")

        result = checker_with_mock_dm.check("000001")

        assert result["fund_code"] == "000001"
        assert result["status"] == "error"
        assert "网络错误" in result["message"]


# =============================================================================
# check_completeness 方法测试
# =============================================================================


class TestCheckCompleteness:
    """测试 check_completeness 方法"""

    def test_completeness_empty_data(self):
        """测试空数据完整性"""
        checker = DataQualityChecker.__new__(DataQualityChecker)
        checker._dm = MagicMock()

        result = checker.check_completeness(pd.DataFrame())

        assert result["score"] == 0
        assert result["total_rows"] == 0
        assert result["missing_values"] == {}
        assert result["date_gaps"] == 0


# =============================================================================
# check_accuracy 方法测试
# =============================================================================


class TestCheckAccuracy:
    """测试 check_accuracy 方法"""

    def test_accuracy_empty_data(self):
        """测试空数据准确性"""
        checker = DataQualityChecker.__new__(DataQualityChecker)
        checker._dm = MagicMock()

        result = checker.check_accuracy(pd.DataFrame())

        assert result["score"] == 100
        assert result["anomalies"] == []

    def test_accuracy_without_unit_nav(self):
        """测试无 unit_nav 列的数据"""
        checker = DataQualityChecker.__new__(DataQualityChecker)
        checker._dm = MagicMock()

        nav_df = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=100, freq="B"),
        })

        result = checker.check_accuracy(nav_df)

        assert result["score"] == 100

    def test_accuracy_insufficient_data(self):
        """测试数据量不足"""
        checker = DataQualityChecker.__new__(DataQualityChecker)
        checker._dm = MagicMock()

        nav_df = pd.DataFrame({
            "nav_date": pd.date_range("2024-01-01", periods=5, freq="B"),
            "unit_nav": np.random.uniform(1.0, 2.0, 5),
        })

        result = checker.check_accuracy(nav_df)

        # 数据量小于 10 时返回默认值
        assert result["score"] == 100


# =============================================================================
# check_timeliness 方法测试
# =============================================================================


class TestCheckTimeliness:
    """测试 check_timeliness 方法"""

    def test_timeliness_empty_data(self):
        """测试空数据时效性"""
        checker = DataQualityChecker.__new__(DataQualityChecker)
        checker._dm = MagicMock()

        result = checker.check_timeliness(pd.DataFrame())

        assert result["status"] == "unknown"
        assert result["last_date"] is None
        assert result["days_since_update"] is None

    def test_timeliness_without_nav_date(self):
        """测试无 nav_date 列的数据"""
        checker = DataQualityChecker.__new__(DataQualityChecker)
        checker._dm = MagicMock()

        nav_df = pd.DataFrame({
            "unit_nav": [1.5],
        })

        result = checker.check_timeliness(nav_df)

        assert result["status"] == "unknown"
