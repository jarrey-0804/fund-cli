# -*- coding: utf-8 -*-
"""
数据管理命令测试

测试 data_cmd 模块的所有命令功能。
"""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from fund_cli.commands.data_cmd import app

runner = CliRunner()


@pytest.fixture
def mock_data_manager():
    """Mock 数据管理器"""
    mock_dm = MagicMock()
    mock_dm.get_cache_stats.return_value = {
        "size": 150,
        "volume": 52428800,  # 50 MB
        "directory": "/tmp/.fund_cli_cache",
    }
    mock_dm.clear_cache.return_value = None
    return mock_dm


@pytest.fixture
def mock_quality_checker():
    """Mock 数据质量检查器"""
    mock_checker = MagicMock()
    mock_checker.check.return_value = {
        "overall_status": "good",
        "completeness": {
            "score": 95,
            "total_rows": 252,
            "missing_values": {"unit_nav": 0, "accumulated_nav": 2},
        },
        "accuracy": {
            "score": 92,
            "anomaly_count": 3,
        },
        "timeliness": {
            "status": "up_to_date",
            "last_date": "2024-12-31",
        },
    }
    mock_checker.incremental_update.return_value = {
        "status": "success",
        "new_records": 5,
    }
    mock_checker.batch_download.return_value = {
        "total": 3,
        "success": 2,
        "failed": 1,
        "details": {
            "000001": {"status": "success"},
            "000002": {"status": "success"},
            "000003": {"status": "error", "message": "网络错误"},
        },
    }
    return mock_checker


class TestCacheStatsCommand:
    """缓存统计命令测试"""

    def test_stats_help(self):
        """测试缓存统计命令帮助"""
        result = runner.invoke(app, ["stats", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.data_cmd.get_data_manager")
    def test_stats_success(self, mock_get_dm, mock_data_manager):
        """测试成功获取缓存统计"""
        mock_get_dm.return_value = mock_data_manager
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "150" in result.output or "缓存" in result.output

    @patch("fund_cli.commands.data_cmd.get_data_manager")
    def test_stats_with_error(self, mock_get_dm, mock_data_manager):
        """测试获取缓存统计错误处理"""
        mock_get_dm.return_value = mock_data_manager
        mock_data_manager.get_cache_stats.side_effect = Exception("测试错误")
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "失败" in result.output


class TestClearCacheCommand:
    """清空缓存命令测试"""

    def test_clear_help(self):
        """测试清空缓存命令帮助"""
        result = runner.invoke(app, ["clear", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.data_cmd.get_data_manager")
    def test_clear_success(self, mock_get_dm, mock_data_manager):
        """测试成功清空缓存"""
        mock_get_dm.return_value = mock_data_manager
        result = runner.invoke(app, ["clear"])
        assert result.exit_code == 0
        assert "已清空" in result.output

    @patch("fund_cli.commands.data_cmd.get_data_manager")
    def test_clear_with_error(self, mock_get_dm, mock_data_manager):
        """测试清空缓存错误处理"""
        mock_get_dm.return_value = mock_data_manager
        mock_data_manager.clear_cache.side_effect = Exception("测试错误")
        result = runner.invoke(app, ["clear"])
        assert result.exit_code == 0
        assert "失败" in result.output


class TestDataQualityCommand:
    """数据质量检查命令测试"""

    def test_quality_help(self):
        """测试数据质量检查命令帮助"""
        result = runner.invoke(app, ["quality", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_quality.DataQualityChecker")
    def test_quality_success(self, mock_checker_class, mock_quality_checker):
        """测试成功数据质量检查"""
        mock_checker_class.return_value = mock_quality_checker
        result = runner.invoke(app, ["quality", "000001"])
        assert result.exit_code == 0
        assert "good" in result.output or "质量" in result.output

    @patch("fund_cli.core.data_quality.DataQualityChecker")
    def test_quality_with_completeness(self, mock_checker_class, mock_quality_checker):
        """测试数据完整性检查"""
        mock_checker_class.return_value = mock_quality_checker
        result = runner.invoke(app, ["quality", "000001"])
        assert result.exit_code == 0
        assert "完整性" in result.output or "95" in result.output

    @patch("fund_cli.core.data_quality.DataQualityChecker")
    def test_quality_with_accuracy(self, mock_checker_class, mock_quality_checker):
        """测试数据准确性检查"""
        mock_checker_class.return_value = mock_quality_checker
        result = runner.invoke(app, ["quality", "000001"])
        assert result.exit_code == 0
        assert "准确性" in result.output or "92" in result.output

    @patch("fund_cli.core.data_quality.DataQualityChecker")
    def test_quality_with_timeliness(self, mock_checker_class, mock_quality_checker):
        """测试数据时效性检查"""
        mock_checker_class.return_value = mock_quality_checker
        result = runner.invoke(app, ["quality", "000001"])
        assert result.exit_code == 0
        assert "时效" in result.output or "up_to_date" in result.output


class TestIncrementalUpdateCommand:
    """增量更新命令测试"""

    def test_update_help(self):
        """测试增量更新命令帮助"""
        result = runner.invoke(app, ["update", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_quality.DataQualityChecker")
    def test_update_success(self, mock_checker_class, mock_quality_checker):
        """测试成功增量更新"""
        mock_checker_class.return_value = mock_quality_checker
        result = runner.invoke(app, ["update", "000001"])
        assert result.exit_code == 0
        assert "新增" in result.output or "5" in result.output

    @patch("fund_cli.core.data_quality.DataQualityChecker")
    def test_update_failure(self, mock_checker_class, mock_quality_checker):
        """测试增量更新失败"""
        mock_checker_class.return_value = mock_quality_checker
        mock_quality_checker.incremental_update.return_value = {
            "status": "error",
            "message": "网络连接失败",
        }
        result = runner.invoke(app, ["update", "000001"])
        assert result.exit_code == 0
        assert "失败" in result.output


class TestBatchDownloadCommand:
    """批量下载命令测试"""

    def test_batch_download_help(self):
        """测试批量下载命令帮助"""
        result = runner.invoke(app, ["batch-download", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_quality.DataQualityChecker")
    def test_batch_download_success(self, mock_checker_class, mock_quality_checker):
        """测试成功批量下载"""
        mock_checker_class.return_value = mock_quality_checker
        result = runner.invoke(app, ["batch-download", "000001,000002,000003"])
        assert result.exit_code == 0
        assert "成功" in result.output or "2" in result.output

    @patch("fund_cli.core.data_quality.DataQualityChecker")
    def test_batch_download_with_failures(self, mock_checker_class, mock_quality_checker):
        """测试批量下载部分失败"""
        mock_checker_class.return_value = mock_quality_checker
        result = runner.invoke(app, ["batch-download", "000001,000002,000003"])
        assert result.exit_code == 0
        assert "失败" in result.output or "1" in result.output

    @patch("fund_cli.core.data_quality.DataQualityChecker")
    def test_batch_download_all_failed(self, mock_checker_class, mock_quality_checker):
        """测试批量下载全部失败"""
        mock_checker_class.return_value = mock_quality_checker
        mock_quality_checker.batch_download.return_value = {
            "total": 3,
            "success": 0,
            "failed": 3,
            "details": {
                "000001": {"status": "error", "message": "网络错误"},
                "000002": {"status": "error", "message": "超时"},
                "000003": {"status": "error", "message": "无数据"},
            },
        }
        result = runner.invoke(app, ["batch-download", "000001,000002,000003"])
        assert result.exit_code == 0
        assert "失败" in result.output


class TestDataCommandEdgeCases:
    """边界情况测试"""

    @patch("fund_cli.commands.data_cmd.get_data_manager")
    def test_stats_empty_cache(self, mock_get_dm, mock_data_manager):
        """测试空缓存统计"""
        mock_get_dm.return_value = mock_data_manager
        mock_data_manager.get_cache_stats.return_value = {
            "size": 0,
            "volume": 0,
            "directory": "/tmp/.fund_cli_cache",
        }
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_quality.DataQualityChecker")
    def test_quality_missing_fields(self, mock_checker_class, mock_quality_checker):
        """测试数据质量检查缺失字段"""
        mock_checker_class.return_value = mock_quality_checker
        mock_quality_checker.check.return_value = {
            "overall_status": "warning",
        }
        result = runner.invoke(app, ["quality", "000001"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_quality.DataQualityChecker")
    def test_update_no_new_data(self, mock_checker_class, mock_quality_checker):
        """测试增量更新无新数据"""
        mock_checker_class.return_value = mock_quality_checker
        mock_quality_checker.incremental_update.return_value = {
            "status": "success",
            "new_records": 0,
        }
        result = runner.invoke(app, ["update", "000001"])
        assert result.exit_code == 0

    @patch("fund_cli.core.data_quality.DataQualityChecker")
    def test_batch_download_single_code(self, mock_checker_class, mock_quality_checker):
        """测试单个基金代码批量下载"""
        mock_checker_class.return_value = mock_quality_checker
        mock_quality_checker.batch_download.return_value = {
            "total": 1,
            "success": 1,
            "failed": 0,
            "details": {
                "000001": {"status": "success"},
            },
        }
        result = runner.invoke(app, ["batch-download", "000001"])
        assert result.exit_code == 0
