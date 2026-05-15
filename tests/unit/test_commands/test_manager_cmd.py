"""
基金经理命令测试

测试 manager_cmd 模块的所有命令功能。
"""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from fund_cli.commands.manager_cmd import app

runner = CliRunner()


@pytest.fixture
def mock_data_manager():
    """Mock 数据管理器"""
    mock_dm = MagicMock()
    mock_dm.get_fund_manager.return_value = {
        "name": "张三",
        "fund_code": "000001",
        "fund_name": "华夏成长混合",
        "company": "华夏基金",
        "start_date": "2020-01-15",
        "tenure_days": 1500,
        "total_return": 45.5,
        "annual_return": 15.2,
        "funds": [
            {"fund_code": "000001", "fund_name": "华夏成长混合", "total_return": 45.5},
            {"fund_code": "000002", "fund_name": "华夏价值精选", "total_return": 32.8},
        ],
    }
    return mock_dm


@pytest.fixture
def mock_manager_analyzer():
    """Mock 基金经理分析器"""
    mock_analyzer = MagicMock()
    mock_analyzer.manager_info.return_value = {
        "name": "张三",
        "fund_code": "000001",
        "fund_name": "华夏成长混合",
        "company": "华夏基金",
        "start_date": "2020-01-15",
        "tenure_days": 1500,
    }
    mock_analyzer.performance_stats.return_value = {
        "total_funds": 2,
        "avg_return": 39.15,
        "best_fund": "华夏成长混合",
        "best_return": 45.5,
        "worst_fund": "华夏价值精选",
        "worst_return": 32.8,
    }
    mock_analyzer.stability_analysis.return_value = {
        "tenure_days": 1500,
        "tenure_years": 4.1,
        "stability_level": "稳定",
        "stability_score": 4,
        "multi_fund_manager": True,
        "managed_fund_count": 2,
    }
    return mock_analyzer


class TestManagerInfoCommand:
    """基金经理信息命令测试"""

    def test_info_help(self):
        """测试经理信息命令帮助"""
        result = runner.invoke(app, ["info", "--help"])
        assert result.exit_code == 0
        assert "基金代码" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_info_success(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试成功获取经理信息"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        result = runner.invoke(app, ["info", "000001"])
        assert result.exit_code == 0
        assert "张三" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_info_with_company(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试经理信息包含公司"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        result = runner.invoke(app, ["info", "000001"])
        assert result.exit_code == 0
        assert "华夏基金" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_info_with_tenure(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试经理信息包含任职天数"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        result = runner.invoke(app, ["info", "000001"])
        assert result.exit_code == 0
        assert "任职" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    def test_info_with_error(self, mock_dm_class, mock_data_manager):
        """测试获取经理信息错误处理"""
        mock_dm_class.return_value = mock_data_manager
        mock_data_manager.get_fund_manager.side_effect = Exception("测试错误")
        result = runner.invoke(app, ["info", "000001"])
        assert result.exit_code == 1


class TestManagerPerformanceCommand:
    """经理业绩统计命令测试"""

    def test_performance_help(self):
        """测试业绩统计命令帮助"""
        result = runner.invoke(app, ["performance", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_performance_success(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试成功获取业绩统计"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        result = runner.invoke(app, ["performance", "000001"])
        assert result.exit_code == 0
        assert "管理基金数" in result.output or "2" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_performance_with_avg_return(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试业绩统计包含平均收益率"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        result = runner.invoke(app, ["performance", "000001"])
        assert result.exit_code == 0
        assert "平均收益率" in result.output or "39.15" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_performance_with_best_fund(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试业绩统计包含最佳基金"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        result = runner.invoke(app, ["performance", "000001"])
        assert result.exit_code == 0
        assert "最佳" in result.output or "华夏成长混合" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    def test_performance_with_error(self, mock_dm_class, mock_data_manager):
        """测试业绩统计错误处理"""
        mock_dm_class.return_value = mock_data_manager
        mock_data_manager.get_fund_manager.side_effect = Exception("测试错误")
        result = runner.invoke(app, ["performance", "000001"])
        assert result.exit_code == 1


class TestManagerStabilityCommand:
    """经理稳定性分析命令测试"""

    def test_stability_help(self):
        """测试稳定性分析命令帮助"""
        result = runner.invoke(app, ["stability", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_stability_success(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试成功稳定性分析"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        result = runner.invoke(app, ["stability", "000001"])
        assert result.exit_code == 0
        assert "稳定性" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_stability_with_tenure_years(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试稳定性分析包含任职年限"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        result = runner.invoke(app, ["stability", "000001"])
        assert result.exit_code == 0
        assert "任职年限" in result.output or "4.1" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_stability_with_level(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试稳定性分析包含等级"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        result = runner.invoke(app, ["stability", "000001"])
        assert result.exit_code == 0
        assert "稳定" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_stability_with_score(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试稳定性分析包含评分"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        result = runner.invoke(app, ["stability", "000001"])
        assert result.exit_code == 0
        assert "评分" in result.output or "4" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_stability_multi_fund(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试多基金管理情况"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        result = runner.invoke(app, ["stability", "000001"])
        assert result.exit_code == 0
        assert "多基金管理" in result.output or "是" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    def test_stability_with_error(self, mock_dm_class, mock_data_manager):
        """测试稳定性分析错误处理"""
        mock_dm_class.return_value = mock_data_manager
        mock_data_manager.get_fund_manager.side_effect = Exception("测试错误")
        result = runner.invoke(app, ["stability", "000001"])
        assert result.exit_code == 1


class TestManagerCommandEdgeCases:
    """边界情况测试"""

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_info_new_manager(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试新经理信息"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        mock_data_manager.get_fund_manager.return_value = {
            "name": "李四",
            "fund_code": "000003",
            "fund_name": "新基金",
            "company": "测试基金公司",
            "start_date": "2024-01-01",
            "tenure_days": 30,
        }
        mock_manager_analyzer.manager_info.return_value = {
            "name": "李四",
            "fund_code": "000003",
            "fund_name": "新基金",
            "company": "测试基金公司",
            "start_date": "2024-01-01",
            "tenure_days": 30,
        }
        result = runner.invoke(app, ["info", "000003"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_performance_single_fund(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试单基金管理业绩"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        mock_data_manager.get_fund_manager.return_value = {
            "name": "王五",
            "fund_code": "000004",
            "fund_name": "单基金产品",
            "company": "测试基金公司",
            "total_return": 20.0,
            "funds": [],
        }
        mock_manager_analyzer.performance_stats.return_value = {
            "total_funds": 1,
            "avg_return": 20.0,
            "best_fund": "单基金产品",
            "best_return": 20.0,
            "worst_fund": "单基金产品",
            "worst_return": 20.0,
        }
        result = runner.invoke(app, ["performance", "000004"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_stability_very_stable(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试非常稳定的经理"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        mock_manager_analyzer.stability_analysis.return_value = {
            "tenure_days": 3650,  # 10年
            "tenure_years": 10.0,
            "stability_level": "非常稳定",
            "stability_score": 5,
            "multi_fund_manager": True,
            "managed_fund_count": 5,
        }
        result = runner.invoke(app, ["stability", "000001"])
        assert result.exit_code == 0
        assert "非常稳定" in result.output or "5" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_stability_new_manager(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试新经理稳定性"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        mock_manager_analyzer.stability_analysis.return_value = {
            "tenure_days": 180,
            "tenure_years": 0.5,
            "stability_level": "较新",
            "stability_score": 2,
            "multi_fund_manager": False,
            "managed_fund_count": 1,
        }
        result = runner.invoke(app, ["stability", "000001"])
        assert result.exit_code == 0
        assert "较新" in result.output or "2" in result.output

    @patch("fund_cli.commands.manager_cmd.DataManager")
    @patch("fund_cli.commands.manager_cmd.ManagerAnalyzer")
    def test_info_missing_fields(
        self,
        mock_analyzer_class,
        mock_dm_class,
        mock_data_manager,
        mock_manager_analyzer,
    ):
        """测试缺失字段情况"""
        mock_dm_class.return_value = mock_data_manager
        mock_analyzer_class.return_value = mock_manager_analyzer
        mock_data_manager.get_fund_manager.return_value = {
            "name": "测试经理",
        }
        mock_manager_analyzer.manager_info.return_value = {
            "name": "测试经理",
            "fund_code": "",
            "fund_name": "",
            "company": "",
            "start_date": "",
            "tenure_days": 0,
        }
        result = runner.invoke(app, ["info", "000001"])
        assert result.exit_code == 0
