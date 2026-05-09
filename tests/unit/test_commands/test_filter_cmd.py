# -*- coding: utf-8 -*-
"""
基金筛选命令测试

测试 filter_cmd 模块的所有命令功能。
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from typer.testing import CliRunner

from fund_cli.commands.filter_cmd import app

runner = CliRunner()


@pytest.fixture
def mock_data_manager():
    """Mock 数据管理器"""
    mock_dm = MagicMock()

    # 模拟 search_funds 返回数据
    sample_funds = pd.DataFrame(
        {
            "code": ["000001", "000002", "000003"],
            "name": ["华夏成长混合", "易方达策略成长", "嘉实增长混合"],
            "type": ["混合型", "混合型", "混合型"],
            "company": ["华夏基金", "易方达基金", "嘉实基金"],
            "scale": [50.5, 120.3, 85.7],
            "return_1y": [15.2, 18.5, 12.3],
            "sharpe_ratio": [1.2, 1.5, 0.9],
            "max_drawdown": [-15.3, -12.5, -18.2],
        }
    )
    mock_dm.search_funds.return_value = sample_funds
    return mock_dm


@pytest.fixture
def mock_screener():
    """Mock 基金筛选器"""
    mock_screen = MagicMock()

    sample_funds = pd.DataFrame(
        {
            "code": ["000001", "000002"],
            "name": ["华夏成长混合", "易方达策略成长"],
            "type": ["混合型", "混合型"],
            "company": ["华夏基金", "易方达基金"],
            "scale": [50.5, 120.3],
        }
    )

    mock_screen.screen.return_value = sample_funds
    mock_screen.screen_by_fee.return_value = sample_funds
    mock_screen.screen_by_manager.return_value = sample_funds
    mock_screen.screen_by_rating.return_value = sample_funds
    mock_screen._dm.search_funds.return_value = sample_funds
    mock_screen.evaluate_expression.return_value = sample_funds
    mock_screen.list_templates.return_value = ["template1", "template2"]
    mock_screen.delete_template.return_value = True

    return mock_screen


class TestFilterBasicCommand:
    """基础筛选命令测试"""

    def test_basic_help(self):
        """测试基础筛选帮助信息"""
        result = runner.invoke(app, ["basic", "--help"])
        assert result.exit_code == 0
        assert "基金类型" in result.output or "fund_type" in result.output.lower()

    @patch("fund_cli.commands.filter_cmd.get_data_manager")
    def test_basic_with_type(self, mock_get_dm, mock_data_manager):
        """测试按类型筛选"""
        mock_get_dm.return_value = mock_data_manager
        result = runner.invoke(app, ["basic", "--type", "股票型"])
        assert result.exit_code == 0
        mock_data_manager.search_funds.assert_called_once()

    @patch("fund_cli.commands.filter_cmd.get_data_manager")
    def test_basic_with_company(self, mock_get_dm, mock_data_manager):
        """测试按公司筛选"""
        mock_get_dm.return_value = mock_data_manager
        result = runner.invoke(app, ["basic", "--company", "华夏基金"])
        assert result.exit_code == 0
        mock_data_manager.search_funds.assert_called_once()

    @patch("fund_cli.commands.filter_cmd.get_data_manager")
    def test_basic_with_scale_range(self, mock_get_dm, mock_data_manager):
        """测试按规模范围筛选"""
        mock_get_dm.return_value = mock_data_manager
        result = runner.invoke(app, ["basic", "--min-scale", "10", "--max-scale", "100"])
        assert result.exit_code == 0
        mock_data_manager.search_funds.assert_called_once()

    @patch("fund_cli.commands.filter_cmd.get_data_manager")
    def test_basic_with_keyword(self, mock_get_dm, mock_data_manager):
        """测试关键词搜索"""
        mock_get_dm.return_value = mock_data_manager
        result = runner.invoke(app, ["basic", "--keyword", "成长"])
        assert result.exit_code == 0
        mock_data_manager.search_funds.assert_called_once()

    @patch("fund_cli.commands.filter_cmd.get_data_manager")
    def test_basic_with_limit(self, mock_get_dm, mock_data_manager):
        """测试限制返回数量"""
        mock_get_dm.return_value = mock_data_manager
        result = runner.invoke(app, ["basic", "--limit", "10"])
        assert result.exit_code == 0

    @patch("fund_cli.commands.filter_cmd.get_data_manager")
    def test_basic_with_output(self, mock_get_dm, mock_data_manager, tmp_path):
        """测试导出到文件"""
        mock_get_dm.return_value = mock_data_manager
        output_file = tmp_path / "test_output.csv"
        result = runner.invoke(app, ["basic", "--output", str(output_file)])
        assert result.exit_code == 0

    @patch("fund_cli.commands.filter_cmd.get_data_manager")
    def test_basic_no_results(self, mock_get_dm, mock_data_manager):
        """测试无结果情况"""
        mock_get_dm.return_value = mock_data_manager
        mock_data_manager.search_funds.return_value = pd.DataFrame()
        result = runner.invoke(app, ["basic", "--type", "不存在的类型"])
        assert result.exit_code == 0
        assert "未找到" in result.output

    @patch("fund_cli.commands.filter_cmd.get_data_manager")
    def test_basic_with_error(self, mock_get_dm, mock_data_manager):
        """测试错误处理"""
        mock_get_dm.return_value = mock_data_manager
        mock_data_manager.search_funds.side_effect = Exception("测试错误")
        result = runner.invoke(app, ["basic"])
        assert result.exit_code == 1


class TestFilterFeeCommand:
    """费率筛选命令测试"""

    def test_fee_help(self):
        """测试费率筛选帮助信息"""
        result = runner.invoke(app, ["fee", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_fee_with_max_fee(self, mock_screener_class, mock_screener):
        """测试按最大费率筛选"""
        mock_screener_class.return_value = mock_screener
        result = runner.invoke(app, ["fee", "1.5"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_fee_with_type(self, mock_screener_class, mock_screener):
        """测试费率筛选带基金类型"""
        mock_screener_class.return_value = mock_screener
        result = runner.invoke(app, ["fee", "1.5", "--fund-type", "股票型"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_fee_no_results(self, mock_screener_class, mock_screener):
        """测试费率筛选无结果"""
        mock_screener_class.return_value = mock_screener
        mock_screener.screen_by_fee.return_value = pd.DataFrame()
        result = runner.invoke(app, ["fee", "0.1"])
        assert result.exit_code == 0
        assert "未找到" in result.output

    @patch("fund_cli.core.screener.FundScreener")
    def test_fee_with_error(self, mock_screener_class, mock_screener):
        """测试费率筛选错误处理"""
        mock_screener_class.return_value = mock_screener
        mock_screener.screen_by_fee.side_effect = Exception("测试错误")
        result = runner.invoke(app, ["fee", "1.5"])
        assert result.exit_code == 1


class TestFilterManagerCommand:
    """经理筛选命令测试"""

    def test_manager_help(self):
        """测试经理筛选帮助信息"""
        result = runner.invoke(app, ["manager", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_manager_by_name(self, mock_screener_class, mock_screener):
        """测试按经理名称筛选"""
        mock_screener_class.return_value = mock_screener
        result = runner.invoke(app, ["manager", "张三"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_manager_no_results(self, mock_screener_class, mock_screener):
        """测试经理筛选无结果"""
        mock_screener_class.return_value = mock_screener
        mock_screener.screen_by_manager.return_value = pd.DataFrame()
        result = runner.invoke(app, ["manager", "不存在的经理"])
        assert result.exit_code == 0
        assert "未找到" in result.output


class TestFilterRatingCommand:
    """评级筛选命令测试"""

    def test_rating_help(self):
        """测试评级筛选帮助信息"""
        result = runner.invoke(app, ["rating", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_rating_by_min_rating(self, mock_screener_class, mock_screener):
        """测试按最低评级筛选"""
        mock_screener_class.return_value = mock_screener
        result = runner.invoke(app, ["rating", "4"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_rating_no_results(self, mock_screener_class, mock_screener):
        """测试评级筛选无结果"""
        mock_screener_class.return_value = mock_screener
        mock_screener.screen_by_rating.return_value = pd.DataFrame()
        result = runner.invoke(app, ["rating", "5"])
        assert result.exit_code == 0
        assert "未找到" in result.output


class TestFilterAdvancedCommand:
    """高级表达式筛选命令测试"""

    def test_advanced_help(self):
        """测试高级筛选帮助信息"""
        result = runner.invoke(app, ["advanced", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_advanced_with_expression(self, mock_screener_class, mock_screener):
        """测试表达式筛选"""
        mock_screener_class.return_value = mock_screener
        result = runner.invoke(app, ["advanced", "return_1y > 10"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_advanced_no_data(self, mock_screener_class, mock_screener):
        """测试无数据情况"""
        mock_screener_class.return_value = mock_screener
        mock_screener._dm.search_funds.return_value = pd.DataFrame()
        result = runner.invoke(app, ["advanced", "return_1y > 10"])
        assert result.exit_code == 0
        assert "无基金数据" in result.output

    @patch("fund_cli.core.screener.FundScreener")
    def test_advanced_invalid_expression(self, mock_screener_class, mock_screener):
        """测试无效表达式"""
        mock_screener_class.return_value = mock_screener
        mock_screener.evaluate_expression.side_effect = ValueError("表达式错误")
        result = runner.invoke(app, ["advanced", "invalid expression"])
        assert result.exit_code == 1


class TestFilterTemplateCommand:
    """筛选模板管理命令测试"""

    def test_template_help(self):
        """测试模板管理帮助信息"""
        result = runner.invoke(app, ["template", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_template_list(self, mock_screener_class, mock_screener):
        """测试列出模板"""
        mock_screener_class.return_value = mock_screener
        result = runner.invoke(app, ["template", "list"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_template_list_empty(self, mock_screener_class, mock_screener):
        """测试空模板列表"""
        mock_screener_class.return_value = mock_screener
        mock_screener.list_templates.return_value = []
        result = runner.invoke(app, ["template", "list"])
        assert result.exit_code == 0
        assert "暂无" in result.output

    @patch("fund_cli.core.screener.FundScreener")
    def test_template_save_without_name(self, mock_screener_class, mock_screener):
        """测试保存模板未指定名称"""
        mock_screener_class.return_value = mock_screener
        result = runner.invoke(app, ["template", "save"])
        assert result.exit_code == 1
        assert "请指定模板名称" in result.output

    @patch("fund_cli.core.screener.FundScreener")
    def test_template_load_without_name(self, mock_screener_class, mock_screener):
        """测试加载模板未指定名称"""
        mock_screener_class.return_value = mock_screener
        result = runner.invoke(app, ["template", "load"])
        assert result.exit_code == 1
        assert "请指定模板名称" in result.output

    @patch("fund_cli.core.screener.FundScreener")
    def test_template_load_not_found(self, mock_screener_class, mock_screener):
        """测试加载不存在的模板"""
        mock_screener_class.return_value = mock_screener
        mock_screener.load_template.side_effect = FileNotFoundError("模板不存在")
        result = runner.invoke(app, ["template", "load", "--name", "not_exist"])
        assert result.exit_code == 1

    @patch("fund_cli.core.screener.FundScreener")
    def test_template_delete(self, mock_screener_class, mock_screener):
        """测试删除模板"""
        mock_screener_class.return_value = mock_screener
        result = runner.invoke(app, ["template", "delete", "--name", "template1"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_template_invalid_action(self, mock_screener_class, mock_screener):
        """测试无效操作"""
        mock_screener_class.return_value = mock_screener
        result = runner.invoke(app, ["template", "invalid"])
        assert result.exit_code == 1
        assert "未知操作" in result.output


class TestFilterPerformanceCommand:
    """业绩指标筛选命令测试"""

    def test_performance_help(self):
        """测试业绩筛选帮助信息"""
        result = runner.invoke(app, ["performance", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_performance_with_min_return(self, mock_screener_class, mock_screener):
        """测试按最低收益率筛选"""
        mock_screener_class.return_value = mock_screener
        result = runner.invoke(app, ["performance", "--min-return", "10"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_performance_with_max_drawdown(self, mock_screener_class, mock_screener):
        """测试按最大回撤筛选"""
        mock_screener_class.return_value = mock_screener
        result = runner.invoke(app, ["performance", "--max-drawdown", "-20"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_performance_with_min_sharpe(self, mock_screener_class, mock_screener):
        """测试按最低夏普比率筛选"""
        mock_screener_class.return_value = mock_screener
        result = runner.invoke(app, ["performance", "--min-sharpe", "1.0"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_performance_no_results(self, mock_screener_class, mock_screener):
        """测试业绩筛选无结果"""
        mock_screener_class.return_value = mock_screener
        mock_screener.screen.return_value = pd.DataFrame()
        result = runner.invoke(app, ["performance", "--min-return", "100"])
        assert result.exit_code == 0
        assert "未找到" in result.output


class TestFilterExportCommand:
    """导出筛选结果命令测试"""

    def test_export_help(self):
        """测试导出帮助信息"""
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_export_csv(self, mock_screener_class, mock_screener, tmp_path):
        """测试导出 CSV 格式"""
        mock_screener_class.return_value = mock_screener
        output_file = tmp_path / "test_export.csv"
        result = runner.invoke(app, ["export", str(output_file), "--format", "csv"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_export_json(self, mock_screener_class, mock_screener, tmp_path):
        """测试导出 JSON 格式"""
        mock_screener_class.return_value = mock_screener
        output_file = tmp_path / "test_export.json"
        result = runner.invoke(app, ["export", str(output_file), "--format", "json"])
        assert result.exit_code == 0

    @patch("fund_cli.core.screener.FundScreener")
    def test_export_invalid_format(self, mock_screener_class, mock_screener, tmp_path):
        """测试无效导出格式"""
        mock_screener_class.return_value = mock_screener
        output_file = tmp_path / "test_export.txt"
        result = runner.invoke(app, ["export", str(output_file), "--format", "txt"])
        assert result.exit_code == 1

    @patch("fund_cli.core.screener.FundScreener")
    def test_export_no_data(self, mock_screener_class, mock_screener, tmp_path):
        """测试无数据导出"""
        mock_screener_class.return_value = mock_screener
        mock_screener._dm.search_funds.return_value = pd.DataFrame()
        output_file = tmp_path / "test_export.csv"
        result = runner.invoke(app, ["export", str(output_file)])
        assert result.exit_code == 0
        assert "无数据" in result.output
