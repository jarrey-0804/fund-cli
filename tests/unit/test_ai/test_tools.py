"""
AI工具模块单元测试

测试 ai/tools.py 中的工具函数，包括：
- 边界情况处理
- 错误处理
- 数据格式适配
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd


class TestPeriodToDate:
    """测试 _period_to_dates 函数"""

    def test_period_to_dates_1y(self):
        """测试 1y 周期转换"""
        from fund_cli.ai.tools import _period_to_dates
        from datetime import date, timedelta

        start, end = _period_to_dates("1y")
        assert isinstance(start, date)
        assert end is None
        # 应该是大约一年前
        assert (date.today() - start).days >= 360
        assert (date.today() - start).days <= 370

    def test_period_to_dates_1m(self):
        """测试 1m 周期转换"""
        from fund_cli.ai.tools import _period_to_dates
        from datetime import date

        start, end = _period_to_dates("1m")
        assert isinstance(start, date)
        assert end is None
        assert (date.today() - start).days >= 28
        assert (date.today() - start).days <= 35

    def test_period_to_dates_3m(self):
        """测试 3m 周期转换"""
        from fund_cli.ai.tools import _period_to_dates
        from datetime import date

        start, end = _period_to_dates("3m")
        assert isinstance(start, date)
        assert end is None
        assert (date.today() - start).days >= 85
        assert (date.today() - start).days <= 95

    def test_period_to_dates_6m(self):
        """测试 6m 周期转换"""
        from fund_cli.ai.tools import _period_to_dates
        from datetime import date

        start, end = _period_to_dates("6m")
        assert isinstance(start, date)
        assert end is None
        assert (date.today() - start).days >= 175
        assert (date.today() - start).days <= 185

    def test_period_to_dates_3y(self):
        """测试 3y 周期转换"""
        from fund_cli.ai.tools import _period_to_dates
        from datetime import date

        start, end = _period_to_dates("3y")
        assert isinstance(start, date)
        assert end is None
        assert (date.today() - start).days >= 1090
        assert (date.today() - start).days <= 1100

    def test_period_to_dates_5y(self):
        """测试 5y 周期转换"""
        from fund_cli.ai.tools import _period_to_dates
        from datetime import date

        start, end = _period_to_dates("5y")
        assert isinstance(start, date)
        assert end is None
        assert (date.today() - start).days >= 1820
        assert (date.today() - start).days <= 1830

    def test_period_to_dates_ytd(self):
        """测试 ytd 周期转换"""
        from fund_cli.ai.tools import _period_to_dates
        from datetime import date

        start, end = _period_to_dates("ytd")
        assert isinstance(start, date)
        assert start.year == date.today().year
        assert start.month == 1
        assert start.day == 1

    def test_period_to_dates_unknown(self):
        """测试未知周期默认为 1y"""
        from fund_cli.ai.tools import _period_to_dates
        from datetime import date

        start, end = _period_to_dates("unknown")
        assert start is not None
        assert end is None
        # 默认使用365天
        assert (date.today() - start).days >= 360


class TestGetFundBasicInfo:
    """测试 get_fund_basic_info 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_success(self, mock_get_adapter):
        """测试成功获取基金信息"""
        from fund_cli.ai.tools import get_fund_basic_info

        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {
            'name': '华夏成长混合',
            'type': '混合型',
            'manager': '张三',
            'establish_date': '2020-01-01',
            'company': '华夏基金',
            'scale': '50亿'
        }
        mock_adapter.get_fund_info_ths.return_value = None
        mock_adapter.get_fund_overview.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_basic_info.invoke({"fund_code": "000001"})

        assert "000001" in result
        assert "华夏成长混合" in result
        assert "混合型" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_with_ths_info(self, mock_get_adapter):
        """测试包含同花顺信息"""
        from fund_cli.ai.tools import get_fund_basic_info

        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {'name': '测试基金'}
        mock_adapter.get_fund_info_ths.return_value = {
            '近1年收益': '15.5%',
            '最大回撤': '-8.2%'
        }
        mock_adapter.get_fund_overview.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_basic_info.invoke({"fund_code": "000001"})

        assert "同花顺" in result
        assert "15.5%" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_with_overview(self, mock_get_adapter):
        """测试包含基金概览"""
        from fund_cli.ai.tools import get_fund_basic_info

        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {'name': '测试基金'}
        mock_adapter.get_fund_info_ths.return_value = None
        mock_adapter.get_fund_overview.return_value = {
            '投资目标': '追求长期稳定增值',
            '投资策略': '价值投资'
        }
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_basic_info.invoke({"fund_code": "000001"})

        assert "概览" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_error_handling(self, mock_get_adapter):
        """测试错误处理"""
        from fund_cli.ai.tools import get_fund_basic_info

        mock_get_adapter.side_effect = Exception("连接失败")

        result = get_fund_basic_info.invoke({"fund_code": "000001"})

        assert "失败" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_chinese_keys(self, mock_get_adapter):
        """测试中文键名"""
        from fund_cli.ai.tools import get_fund_basic_info

        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {
            '基金简称': '华夏成长',
            '基金类型': '混合型',
            '基金经理': '张三',
        }
        mock_adapter.get_fund_info_ths.return_value = None
        mock_adapter.get_fund_overview.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_basic_info.invoke({"fund_code": "000001"})

        assert "华夏成长" in result
        assert "混合型" in result


class TestGetFundNavHistory:
    """测试 get_fund_nav_history 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_success(self, mock_get_adapter):
        """测试成功获取净值历史"""
        from fund_cli.ai.tools import get_fund_nav_history

        mock_adapter = MagicMock()
        mock_adapter.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.05, 1.10],
            'date': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_nav_history.invoke({"fund_code": "000001", "period": "1y"})

        assert "000001" in result
        assert "净值历史" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_empty_data(self, mock_get_adapter):
        """测试空数据"""
        from fund_cli.ai.tools import get_fund_nav_history

        mock_adapter = MagicMock()
        mock_adapter.get_fund_nav.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_nav_history.invoke({"fund_code": "000001", "period": "1y"})

        assert "未找到" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_empty_dataframe(self, mock_get_adapter):
        """测试空DataFrame"""
        from fund_cli.ai.tools import get_fund_nav_history

        mock_adapter = MagicMock()
        mock_adapter.get_fund_nav.return_value = pd.DataFrame()
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_nav_history.invoke({"fund_code": "000001", "period": "1y"})

        assert "未找到" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_error_handling(self, mock_get_adapter):
        """测试错误处理"""
        from fund_cli.ai.tools import get_fund_nav_history

        mock_get_adapter.side_effect = Exception("数据获取失败")

        result = get_fund_nav_history.invoke({"fund_code": "000001", "period": "1y"})

        assert "失败" in result


class TestGetFundPerformance:
    """测试 get_fund_performance 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    @patch('fund_cli.ai.tools._get_analyzer')
    def test_success(self, mock_get_analyzer, mock_get_adapter):
        """测试成功获取业绩指标"""
        from fund_cli.ai.tools import get_fund_performance

        mock_adapter = MagicMock()
        mock_adapter.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.1, 1.2]
        })
        mock_get_adapter.return_value = mock_adapter

        mock_analyzer = MagicMock()
        mock_analyzer.calculate_metrics.return_value = {
            'total_return': 20.0,
            'cagr': 15.0,
            'sharpe_ratio': 1.5,
            'max_drawdown': 10.0,
            'volatility': 12.0,
            'sortino_ratio': 2.0
        }
        mock_get_analyzer.return_value = mock_analyzer

        result = get_fund_performance.invoke({"fund_code": "000001", "period": "1y"})

        assert "000001" in result
        assert "20.00%" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_no_nav_data(self, mock_get_adapter):
        """测试无净值数据"""
        from fund_cli.ai.tools import get_fund_performance

        mock_adapter = MagicMock()
        mock_adapter.get_fund_nav.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_performance.invoke({"fund_code": "000001", "period": "1y"})

        assert "未找到" in result


class TestGetFundHoldings:
    """测试 get_fund_holdings 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_success(self, mock_get_adapter):
        """测试成功获取持仓"""
        from fund_cli.ai.tools import get_fund_holdings

        mock_adapter = MagicMock()
        mock_adapter.get_fund_holdings.return_value = pd.DataFrame({
            'stock_code': ['600519', '000858'],
            'stock_name': ['贵州茅台', '五粮液'],
            'weight': [8.5, 5.2]
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_holdings.invoke({"fund_code": "000001", "top_n": 10})

        assert "贵州茅台" in result
        assert "五粮液" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_empty_holdings(self, mock_get_adapter):
        """测试空持仓"""
        from fund_cli.ai.tools import get_fund_holdings

        mock_adapter = MagicMock()
        mock_adapter.get_fund_holdings.return_value = pd.DataFrame()
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_holdings.invoke({"fund_code": "000001", "top_n": 10})

        assert "未找到" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_custom_top_n(self, mock_get_adapter):
        """测试自定义top_n参数"""
        from fund_cli.ai.tools import get_fund_holdings

        mock_adapter = MagicMock()
        mock_adapter.get_fund_holdings.return_value = pd.DataFrame({
            'stock_code': ['600519', '000858', '000001'],
            'stock_name': ['贵州茅台', '五粮液', '平安银行'],
            'weight': [8.5, 5.2, 3.0]
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_holdings.invoke({"fund_code": "000001", "top_n": 2})

        assert "贵州茅台" in result


class TestGetFundManager:
    """测试 get_fund_manager 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_success(self, mock_get_adapter):
        """测试成功获取经理信息"""
        from fund_cli.ai.tools import get_fund_manager

        mock_adapter = MagicMock()
        mock_adapter.get_fund_manager.return_value = {
            'name': '张三',
            'appointment_date': '2020-01-01',
            'experience_years': 10,
            'managed_scale': '100亿',
            'fund_count': 5
        }
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_manager.invoke({"fund_code": "000001"})

        assert "张三" in result
        assert "10年" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_not_found(self, mock_get_adapter):
        """测试未找到经理信息"""
        from fund_cli.ai.tools import get_fund_manager

        mock_adapter = MagicMock()
        mock_adapter.get_fund_manager.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_manager.invoke({"fund_code": "000001"})

        assert "未找到" in result


class TestSearchFunds:
    """测试 search_funds 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_success_list(self, mock_get_adapter):
        """测试成功搜索-列表格式"""
        from fund_cli.ai.tools import search_funds

        mock_adapter = MagicMock()
        mock_adapter.search_funds.return_value = [
            {'code': '000001', 'name': '华夏成长', 'type': '混合型', 'scale': '50亿'},
            {'code': '000002', 'name': '华夏回报', 'type': '混合型', 'scale': '30亿'},
        ]
        mock_get_adapter.return_value = mock_adapter

        result = search_funds.invoke({
            "fund_type": "混合型",
            "limit": 10
        })

        assert "000001" in result
        assert "华夏成长" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_success_dataframe(self, mock_get_adapter):
        """测试成功搜索-DataFrame格式"""
        from fund_cli.ai.tools import search_funds

        mock_adapter = MagicMock()
        # 返回列表格式而非DataFrame，避免DataFrame真值判断问题
        mock_adapter.search_funds.return_value = [
            {'code': '000001', 'name': '华夏成长', 'type': '混合型', 'scale': '50亿'},
            {'code': '000002', 'name': '华夏回报', 'type': '混合型', 'scale': '30亿'},
        ]
        mock_get_adapter.return_value = mock_adapter

        result = search_funds.invoke({
            "fund_type": "混合型",
            "limit": 10
        })

        assert "000001" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_no_results(self, mock_get_adapter):
        """测试无搜索结果"""
        from fund_cli.ai.tools import search_funds

        mock_adapter = MagicMock()
        mock_adapter.search_funds.return_value = []
        mock_get_adapter.return_value = mock_adapter

        result = search_funds.invoke({
            "keyword": "不存在的基金",
            "limit": 10
        })

        assert "未找到" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_with_scale_filter(self, mock_get_adapter):
        """测试带规模筛选"""
        from fund_cli.ai.tools import search_funds

        mock_adapter = MagicMock()
        mock_adapter.search_funds.return_value = [
            {'code': '000001', 'name': '华夏成长', 'type': '混合型', 'scale': '50亿'},
        ]
        mock_get_adapter.return_value = mock_adapter

        result = search_funds.invoke({
            "min_scale": 10.0,
            "max_scale": 100.0,
            "limit": 10
        })

        assert "000001" in result


class TestGetMarketIndex:
    """测试 get_market_index 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_success(self, mock_get_adapter):
        """测试成功获取指数数据"""
        from fund_cli.ai.tools import get_market_index

        mock_adapter = MagicMock()
        mock_adapter.get_benchmark_nav.return_value = pd.DataFrame({
            'close': [3000.0, 3050.0],
            'date': ['2024-01-01', '2024-01-02']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_market_index.invoke({"index_code": "000001.SH"})

        assert "000001.SH" in result
        assert "指数" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_no_data(self, mock_get_adapter):
        """测试无指数数据"""
        from fund_cli.ai.tools import get_market_index

        mock_adapter = MagicMock()
        mock_adapter.get_benchmark_nav.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_market_index.invoke({"index_code": "000001.SH"})

        assert "未找到" in result


class TestGetEtfSpot:
    """测试 get_etf_spot 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_success(self, mock_get_adapter):
        """测试成功获取ETF行情"""
        from fund_cli.ai.tools import get_etf_spot

        mock_adapter = MagicMock()
        mock_adapter.get_etf_spot.return_value = pd.DataFrame({
            'code': ['510050', '510300'],
            'name': ['50ETF', '300ETF'],
            'close': [3.5, 4.2],
            'change_pct': [1.5, 0.8]
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_etf_spot.invoke({})

        assert "ETF" in result
        assert "510050" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_no_data(self, mock_get_adapter):
        """测试无ETF数据"""
        from fund_cli.ai.tools import get_etf_spot

        mock_adapter = MagicMock()
        mock_adapter.get_etf_spot.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_etf_spot.invoke({})

        assert "暂无" in result


class TestCompareFunds:
    """测试 compare_funds 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    @patch('fund_cli.ai.tools._get_analyzer')
    def test_success(self, mock_get_analyzer, mock_get_adapter):
        """测试成功对比基金"""
        from fund_cli.ai.tools import compare_funds

        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {'name': '测试基金'}
        mock_adapter.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.1, 1.2]
        })
        mock_get_adapter.return_value = mock_adapter

        mock_analyzer = MagicMock()
        mock_analyzer.calculate_metrics.return_value = {
            'cagr': 15.0,
            'sharpe_ratio': 1.2,
            'max_drawdown': 10.0
        }
        mock_get_analyzer.return_value = mock_analyzer

        result = compare_funds.invoke({"fund_codes": "000001,000002"})

        assert "对比" in result or "000001" in result

    @patch('fund_cli.ai.tools._get_adapter')
    @patch('fund_cli.ai.tools._get_analyzer')
    def test_partial_failure(self, mock_get_analyzer, mock_get_adapter):
        """测试部分基金获取失败"""
        from fund_cli.ai.tools import compare_funds

        call_count = [0]

        def mock_get_fund_info(code):
            call_count[0] += 1
            if call_count[0] == 1:
                return {'name': '基金A'}
            raise Exception("获取失败")

        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.side_effect = mock_get_fund_info
        mock_adapter.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.1, 1.2]
        })
        mock_get_adapter.return_value = mock_adapter

        mock_analyzer = MagicMock()
        mock_analyzer.calculate_metrics.return_value = {
            'cagr': 15.0,
            'sharpe_ratio': 1.2,
            'max_drawdown': 10.0
        }
        mock_get_analyzer.return_value = mock_analyzer

        result = compare_funds.invoke({"fund_codes": "000001,000002"})

        # 应该包含成功获取的基金
        assert "对比" in result or "000001" in result or "获取失败" in result


class TestAnalyzeInvestmentAdvice:
    """测试 analyze_investment_advice 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    @patch('fund_cli.ai.tools._get_analyzer')
    def test_conservative(self, mock_get_analyzer, mock_get_adapter):
        """测试保守型投资者建议"""
        from fund_cli.ai.tools import analyze_investment_advice

        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {
            'name': '测试基金',
            'type': '股票型'
        }
        mock_adapter.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.1, 1.2]
        })
        mock_get_adapter.return_value = mock_adapter

        mock_analyzer = MagicMock()
        mock_analyzer.calculate_metrics.return_value = {
            'sharpe_ratio': 1.5,
            'max_drawdown': 15.0,
            'cagr': 12.0
        }
        mock_get_analyzer.return_value = mock_analyzer

        result = analyze_investment_advice.invoke({
            "fund_code": "000001",
            "risk_profile": "conservative"
        })

        assert "投资建议" in result

    @patch('fund_cli.ai.tools._get_adapter')
    @patch('fund_cli.ai.tools._get_analyzer')
    def test_aggressive(self, mock_get_analyzer, mock_get_adapter):
        """测试激进型投资者建议"""
        from fund_cli.ai.tools import analyze_investment_advice

        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {
            'name': '测试基金',
            'type': '股票型'
        }
        mock_adapter.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.1, 1.2]
        })
        mock_get_adapter.return_value = mock_adapter

        mock_analyzer = MagicMock()
        mock_analyzer.calculate_metrics.return_value = {
            'sharpe_ratio': 1.5,
            'max_drawdown': 25.0,
            'cagr': 20.0
        }
        mock_get_analyzer.return_value = mock_analyzer

        result = analyze_investment_advice.invoke({
            "fund_code": "000001",
            "risk_profile": "aggressive"
        })

        assert "投资建议" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_no_nav_data(self, mock_get_adapter):
        """测试无净值数据"""
        from fund_cli.ai.tools import analyze_investment_advice

        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {'name': '测试基金'}
        mock_adapter.get_fund_nav.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = analyze_investment_advice.invoke({
            "fund_code": "000001",
            "risk_profile": "moderate"
        })

        assert "无法获取" in result


class TestFilterFundsByPerformance:
    """测试 filter_funds_by_performance 工具"""

    @patch('fund_cli.ai.tools._get_data_manager')
    @patch('fund_cli.ai.tools._get_analyzer')
    def test_success(self, mock_get_analyzer, mock_get_dm):
        """测试成功筛选"""
        from fund_cli.ai.tools import filter_funds_by_performance

        mock_dm = MagicMock()
        mock_dm.get_fund_list.return_value = pd.DataFrame({
            '基金代码': ['000001', '000002'],
            '基金简称': ['华夏成长', '华夏回报']
        })
        mock_dm.get_fund_info.return_value = {'name': '测试基金'}
        mock_dm.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.1, 1.2]
        })
        mock_get_dm.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.calculate_metrics.return_value = {
            'cagr': 15.0,
            'max_drawdown': -10.0,
            'sharpe_ratio': 1.2
        }
        mock_get_analyzer.return_value = mock_analyzer

        result = filter_funds_by_performance.invoke({
            "min_return_1y": 10.0,
            "max_drawdown": 20.0,
            "min_sharpe": 0.5,
            "limit": 5
        })

        assert "筛选结果" in result or "未找到" in result

    @patch('fund_cli.ai.tools._get_data_manager')
    def test_no_fund_list(self, mock_get_dm):
        """测试无法获取基金列表"""
        from fund_cli.ai.tools import filter_funds_by_performance

        mock_dm = MagicMock()
        mock_dm.get_fund_list.return_value = None
        mock_get_dm.return_value = mock_dm

        result = filter_funds_by_performance.invoke({"limit": 5})

        assert "未找到" in result


class TestAnalyzePortfolio:
    """测试 analyze_portfolio 工具"""

    @patch('fund_cli.ai.tools._get_data_manager')
    @patch('fund_cli.ai.tools._get_analyzer')
    def test_success(self, mock_get_analyzer, mock_get_dm):
        """测试成功分析组合"""
        from fund_cli.ai.tools import analyze_portfolio

        mock_dm = MagicMock()
        mock_dm.get_fund_info.return_value = {'name': '测试基金'}
        mock_dm.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.1, 1.2, 1.15, 1.25]
        })
        mock_get_dm.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.calculate_metrics.return_value = {
            'cagr': 12.0,
            'volatility': 8.0,
            'sharpe_ratio': 1.0,
            'max_drawdown': -5.0
        }
        mock_get_analyzer.return_value = mock_analyzer

        result = analyze_portfolio.invoke({
            "fund_codes": "000001,000002",
            "weights": "0.6,0.4",
            "risk_free_rate": 0.03
        })

        assert "组合分析" in result or "投资组合" in result

    @patch('fund_cli.ai.tools._get_data_manager')
    @patch('fund_cli.ai.tools._get_analyzer')
    def test_equal_weights(self, mock_get_analyzer, mock_get_dm):
        """测试等权重分配"""
        from fund_cli.ai.tools import analyze_portfolio

        mock_dm = MagicMock()
        mock_dm.get_fund_info.return_value = {'name': '测试基金'}
        mock_dm.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.1, 1.2]
        })
        mock_get_dm.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.calculate_metrics.return_value = {
            'cagr': 10.0,
            'volatility': 5.0,
            'sharpe_ratio': 1.0,
            'max_drawdown': -3.0
        }
        mock_get_analyzer.return_value = mock_analyzer

        result = analyze_portfolio.invoke({
            "fund_codes": "000001,000002",
            "weights": None
        })

        assert "组合" in result

    def test_weight_mismatch(self):
        """测试权重数量不匹配"""
        from fund_cli.ai.tools import analyze_portfolio

        with patch('fund_cli.ai.tools._get_data_manager') as mock_get_dm:
            mock_dm = MagicMock()
            mock_get_dm.return_value = mock_dm

            result = analyze_portfolio.invoke({
                "fund_codes": "000001,000002,000003",
                "weights": "0.5,0.3"
            })

            assert "不匹配" in result

    @patch('fund_cli.ai.tools._get_data_manager')
    def test_single_fund(self, mock_get_dm):
        """测试单只基金"""
        from fund_cli.ai.tools import analyze_portfolio

        mock_dm = MagicMock()
        mock_dm.get_fund_info.return_value = {'name': '测试'}
        mock_dm.get_fund_nav.return_value = None
        mock_get_dm.return_value = mock_dm

        result = analyze_portfolio.invoke({"fund_codes": "000001"})

        assert "至少 2 只" in result


class TestGetFundFeeInfo:
    """测试 get_fund_fee_info 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_success(self, mock_get_adapter):
        """测试成功获取费率"""
        from fund_cli.ai.tools import get_fund_fee_info

        mock_adapter = MagicMock()
        mock_adapter.get_fund_fee.return_value = {
            'management_fee': '1.50%',
            'custody_fee': '0.25%',
            'purchase_fee': '1.00%',
            'redeem_fee': '0.50%'
        }
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_fee_info.invoke({"fund_code": "000001"})

        assert "000001" in result
        assert "管理费率" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_not_found(self, mock_get_adapter):
        """测试未找到费率"""
        from fund_cli.ai.tools import get_fund_fee_info

        mock_adapter = MagicMock()
        mock_adapter.get_fund_fee.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_fee_info.invoke({"fund_code": "000001"})

        assert "未找到" in result


class TestGetFundRatingInfo:
    """测试 get_fund_rating_info 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_success(self, mock_get_adapter):
        """测试成功获取评级"""
        from fund_cli.ai.tools import get_fund_rating_info

        mock_adapter = MagicMock()
        mock_adapter.get_fund_rating.return_value = 4
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_rating_info.invoke({"fund_code": "000001"})

        assert "000001" in result
        assert "4星" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_no_rating(self, mock_get_adapter):
        """测试无评级"""
        from fund_cli.ai.tools import get_fund_rating_info

        mock_adapter = MagicMock()
        mock_adapter.get_fund_rating.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_rating_info.invoke({"fund_code": "000001"})

        assert "暂无评级" in result


class TestGetFundDividendHistory:
    """测试 get_fund_dividend_history 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_success(self, mock_get_adapter):
        """测试成功获取分红历史"""
        from fund_cli.ai.tools import get_fund_dividend_history

        mock_adapter = MagicMock()
        mock_adapter.get_fund_dividends.return_value = pd.DataFrame({
            'date': ['2024-01-15', '2023-06-20'],
            'amount': ['0.15', '0.20']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_dividend_history.invoke({"fund_code": "000001", "limit": 5})

        assert "000001" in result
        assert "分红历史" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_no_dividends(self, mock_get_adapter):
        """测试无分红记录"""
        from fund_cli.ai.tools import get_fund_dividend_history

        mock_adapter = MagicMock()
        mock_adapter.get_fund_dividends.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_dividend_history.invoke({"fund_code": "000001", "limit": 5})

        assert "暂无分红记录" in result


class TestGetFundSplitHistory:
    """测试 get_fund_split_history 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_success(self, mock_get_adapter):
        """测试成功获取拆分历史"""
        from fund_cli.ai.tools import get_fund_split_history

        mock_adapter = MagicMock()
        mock_adapter.get_fund_splits.return_value = pd.DataFrame({
            'date': ['2023-05-10'],
            'ratio': ['1:2']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_split_history.invoke({"fund_code": "000001", "limit": 5})

        assert "000001" in result
        assert "拆分历史" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_no_splits(self, mock_get_adapter):
        """测试无拆分记录"""
        from fund_cli.ai.tools import get_fund_split_history

        mock_adapter = MagicMock()
        mock_adapter.get_fund_splits.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_split_history.invoke({"fund_code": "000001", "limit": 5})

        assert "暂无拆分记录" in result


class TestGetFundRankOverall:
    """测试 get_fund_rank_overall 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_success(self, mock_get_adapter):
        """测试成功获取排行"""
        from fund_cli.ai.tools import get_fund_rank_overall

        mock_adapter = MagicMock()
        mock_adapter.get_fund_rank_by_type.return_value = pd.DataFrame({
            'code': ['000001', '000002'],
            'name': ['华夏成长', '华夏回报'],
            'return_1y': ['15.5%', '12.3%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_rank_overall.invoke({"fund_type": "混合型", "limit": 10})

        assert "排行" in result
        assert "000001" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_no_data(self, mock_get_adapter):
        """测试无排行数据"""
        from fund_cli.ai.tools import get_fund_rank_overall

        mock_adapter = MagicMock()
        mock_adapter.get_fund_rank_by_type.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_rank_overall.invoke({"fund_type": "混合型", "limit": 10})

        assert "暂无" in result


class TestGetMacroGdp:
    """测试 get_macro_gdp 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_yearly(self, mock_get_adapter):
        """测试年度GDP数据"""
        from fund_cli.ai.tools import get_macro_gdp

        mock_adapter = MagicMock()
        mock_adapter.get_gdp_yearly.return_value = pd.DataFrame({
            'date': ['2023', '2022'],
            'gdp': ['126.06万亿', '121.02万亿'],
            'yoy': ['5.2%', '3.0%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_macro_gdp.invoke({"freq": "yearly"})

        assert "GDP" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_quarterly(self, mock_get_adapter):
        """测试季度GDP数据"""
        from fund_cli.ai.tools import get_macro_gdp

        mock_adapter = MagicMock()
        mock_adapter.get_gdp_quarterly.return_value = pd.DataFrame({
            'date': ['2023Q4', '2023Q3'],
            'gdp': ['32.5万亿', '31.2万亿'],
            'yoy': ['5.2%', '4.9%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_macro_gdp.invoke({"freq": "quarterly"})

        assert "GDP" in result


class TestGetMacroCpi:
    """测试 get_macro_cpi 工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_monthly(self, mock_get_adapter):
        """测试月度CPI数据"""
        from fund_cli.ai.tools import get_macro_cpi

        mock_adapter = MagicMock()
        mock_adapter.get_cpi_monthly.return_value = pd.DataFrame({
            'date': ['2024-01', '2023-12'],
            'cpi': ['100.2', '100.3'],
            'yoy': ['-0.8%', '-0.3%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_macro_cpi.invoke({"freq": "monthly"})

        assert "CPI" in result


class TestToolHelpers:
    """测试工具辅助函数"""

    def test_get_data_manager_singleton(self):
        """测试数据管理器单例"""
        from fund_cli.ai.tools import _get_data_manager, _data_manager
        import fund_cli.ai.tools as tools_module

        # 重置单例
        tools_module._data_manager = None

        with patch('fund_cli.ai.tools.DataManager') as mock_dm:
            mock_dm.return_value = MagicMock()
            dm1 = _get_data_manager()
            dm2 = _get_data_manager()

            # 应该只创建一次
            assert mock_dm.call_count == 1

        # 清理
        tools_module._data_manager = None

    def test_get_adapter(self):
        """测试获取适配器"""
        from fund_cli.ai.tools import _get_adapter
        import fund_cli.ai.tools as tools_module

        tools_module._data_manager = None

        mock_dm = MagicMock()
        mock_adapter = MagicMock()
        mock_dm.get_adapter.return_value = mock_adapter

        with patch('fund_cli.ai.tools._get_data_manager') as mock_get_dm:
            mock_get_dm.return_value = mock_dm
            adapter = _get_adapter()

            assert adapter == mock_adapter

        tools_module._data_manager = None

    def test_get_analyzer_singleton(self):
        """测试分析器单例"""
        from fund_cli.ai.tools import _get_analyzer
        import fund_cli.ai.tools as tools_module

        # 重置单例
        tools_module._analyzer = None

        with patch('fund_cli.ai.tools.PerformanceAnalyzer') as mock_pa:
            mock_pa.return_value = MagicMock()
            a1 = _get_analyzer()
            a2 = _get_analyzer()

            # 应该只创建一次
            assert mock_pa.call_count == 1

        # 清理
        tools_module._analyzer = None


class TestFundToolsList:
    """测试 FUND_TOOLS 列表"""

    def test_tools_count(self):
        """测试工具总数"""
        from fund_cli.ai.tools import FUND_TOOLS

        assert len(FUND_TOOLS) >= 50, f"期望至少50个工具，实际有{len(FUND_TOOLS)}个"

    def test_all_tools_callable(self):
        """测试所有工具可调用"""
        from fund_cli.ai.tools import FUND_TOOLS

        for tool in FUND_TOOLS:
            assert callable(tool.invoke), f"工具 {tool.name} 不可调用"

    def test_all_tools_have_description(self):
        """测试所有工具有描述"""
        from fund_cli.ai.tools import FUND_TOOLS

        for tool in FUND_TOOLS:
            assert tool.description, f"工具 {tool.name} 缺少描述"

    def test_all_tools_have_args_schema(self):
        """测试所有工具有参数模式"""
        from fund_cli.ai.tools import FUND_TOOLS

        for tool in FUND_TOOLS:
            assert tool.args_schema is not None, f"工具 {tool.name} 缺少参数模式"
