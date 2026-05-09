# -*- coding: utf-8 -*-
"""
AKShare 适配器增强测试

补充测试覆盖：
- 缓存命中/未命中场景
- 错误处理分支
- 数据格式转换
- 边界条件
"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from fund_cli.data.adapters.akshare_adapter import AKShareAdapter
from fund_cli.data.base import DataNotFoundError, DataSourceError


@pytest.fixture
def mock_cache():
    """创建模拟缓存"""
    cache = MagicMock()
    cache.exists.return_value = False
    cache.get.return_value = None
    return cache


@pytest.fixture
def mock_akshare():
    """模拟AKShare模块"""
    mock_ak = MagicMock()
    with patch.object(AKShareAdapter, '_get_akshare', return_value=mock_ak):
        yield mock_ak


@pytest.fixture
def adapter():
    """创建适配器实例"""
    return AKShareAdapter(cache=None)


@pytest.fixture
def adapter_with_cache(mock_cache):
    """创建带缓存的适配器"""
    return AKShareAdapter(cache=mock_cache)


class TestCacheHitScenarios:
    """测试缓存命中场景"""

    def test_get_fund_nav_cache_hit(self, adapter_with_cache, mock_cache):
        """测试基金净值缓存命中"""
        cached_df = pd.DataFrame({
            "fund_code": ["000001"],
            "nav_date": [pd.Timestamp("2024-01-01")],
            "unit_nav": [1.5],
            "accumulated_nav": [1.5],
            "daily_return": [0.0],
        })
        mock_cache.get_fund_nav.return_value = cached_df

        result = adapter_with_cache.get_fund_nav("000001")

        assert len(result) == 1
        mock_cache.get_fund_nav.assert_called_once()

    def test_get_fund_holdings_cache_hit(self, adapter_with_cache, mock_cache):
        """测试基金持仓缓存命中"""
        cached_df = pd.DataFrame({
            "stock_code": ["600519"],
            "stock_name": ["贵州茅台"],
        })
        mock_cache.exists.return_value = True
        mock_cache.get.return_value = cached_df

        result = adapter_with_cache.get_fund_holdings("000001")

        assert len(result) == 1

    def test_get_all_fund_names_cache_hit(self, adapter_with_cache, mock_cache):
        """测试基金名称列表缓存命中"""
        cached_df = pd.DataFrame({
            "code": ["000001"],
            "name": ["华夏成长"],
        })
        mock_cache.exists.return_value = True
        mock_cache.get.return_value = cached_df

        result = adapter_with_cache.get_all_fund_names()

        assert len(result) == 1

    def test_get_etf_spot_cache_hit(self, adapter_with_cache, mock_cache):
        """测试ETF实时行情缓存命中"""
        cached_df = pd.DataFrame({
            "code": ["510050"],
            "name": ["华夏上证50ETF"],
        })
        mock_cache.exists.return_value = True
        mock_cache.get.return_value = cached_df

        result = adapter_with_cache.get_etf_spot()

        assert len(result) == 1

    def test_get_lof_spot_cache_hit(self, adapter_with_cache, mock_cache):
        """测试LOF实时行情缓存命中"""
        cached_df = pd.DataFrame({
            "code": ["160106"],
            "name": ["南方高增"],
        })
        mock_cache.exists.return_value = True
        mock_cache.get.return_value = cached_df

        result = adapter_with_cache.get_lof_spot()

        assert len(result) == 1


class TestErrorHandling:
    """测试错误处理"""

    def test_get_fund_info_api_error(self, adapter, mock_akshare):
        """测试基金信息API错误"""
        mock_akshare.fund_individual_basic_info_xq.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取基金信息失败"):
            adapter.get_fund_info("000001")

    def test_get_fund_nav_api_error(self, adapter, mock_akshare):
        """测试基金净值API错误"""
        mock_akshare.fund_open_fund_info_em.side_effect = Exception("API错误")

        with pytest.raises(DataSourceError, match="获取基金净值失败"):
            adapter.get_fund_nav("000001")

    def test_get_benchmark_nav_api_error(self, adapter, mock_akshare):
        """测试基准净值API错误"""
        mock_akshare.stock_zh_index_daily.side_effect = Exception("指数不存在")

        with pytest.raises(DataSourceError, match="获取基准数据失败"):
            adapter.get_benchmark_nav("999999")

    def test_search_funds_api_error(self, adapter, mock_akshare):
        """测试搜索基金API错误"""
        mock_akshare.fund_open_fund_daily_em.side_effect = Exception("服务不可用")

        with pytest.raises(DataSourceError, match="搜索基金失败"):
            adapter.search_funds()


class TestColumnStandardization:
    """测试列名标准化"""

    def test_etf_spot_column_mapping(self, adapter, mock_akshare):
        """测试ETF实时行情列名映射"""
        mock_df = pd.DataFrame({
            "代码": ["510050"],
            "名称": ["华夏上证50ETF"],
            "最新价": [2.5],
            "涨跌幅": [1.0],
            "成交量": [1000000],
            "成交额": [2500000],
            "开盘价": [2.48],
            "最高价": [2.52],
            "最低价": [2.47],
            "昨收": [2.47],
        })
        mock_akshare.fund_etf_spot_em.return_value = mock_df

        result = adapter.get_etf_spot()

        assert "code" in result.columns
        assert "name" in result.columns
        assert "latest_price" in result.columns
        assert "change_pct" in result.columns
        assert "volume" in result.columns

    def test_lof_spot_column_mapping(self, adapter, mock_akshare):
        """测试LOF实时行情列名映射"""
        mock_df = pd.DataFrame({
            "代码": ["160106"],
            "名称": ["南方高增"],
            "最新价": [1.5],
            "涨跌幅": [0.5],
            "成交量": [500000],
            "成交额": [750000],
            "开盘价": [1.49],
            "最高价": [1.51],
            "最低价": [1.48],
            "昨收": [1.49],
        })
        mock_akshare.fund_lof_spot_em.return_value = mock_df

        result = adapter.get_lof_spot()

        assert "code" in result.columns
        assert "name" in result.columns
        assert "latest_price" in result.columns

    def test_etf_hist_column_mapping(self, adapter, mock_akshare):
        """测试ETF历史行情列名映射"""
        mock_df = pd.DataFrame({
            "日期": pd.to_datetime(["2024-01-01"]),
            "开盘": [2.5],
            "收盘": [2.55],
            "最高": [2.58],
            "最低": [2.48],
            "成交量": [1000000],
            "成交额": [2500000],
            "振幅": [4.0],
            "涨跌幅": [2.0],
            "涨跌额": [0.05],
            "换手率": [1.5],
        })
        mock_akshare.fund_etf_hist_em.return_value = mock_df

        result = adapter.get_etf_hist("510050")

        assert "date" in result.columns
        assert "open" in result.columns
        assert "close" in result.columns
        assert "high" in result.columns
        assert "low" in result.columns
        assert "volume" in result.columns
        assert "code" in result.columns


class TestDefaultDateHandling:
    """测试默认日期处理"""

    def test_etf_hist_default_dates(self, adapter, mock_akshare):
        """测试ETF历史行情默认日期"""
        mock_df = pd.DataFrame({
            "日期": pd.to_datetime(["2024-01-01"]),
            "开盘": [2.5],
            "收盘": [2.55],
            "最高": [2.58],
            "最低": [2.48],
            "成交量": [1000000],
            "成交额": [2500000],
            "振幅": [4.0],
            "涨跌幅": [2.0],
            "涨跌额": [0.05],
            "换手率": [1.5],
        })
        mock_akshare.fund_etf_hist_em.return_value = mock_df

        # 不传入日期参数
        result = adapter.get_etf_hist("510050")

        assert len(result) == 1
        # 验证调用时传入了日期参数
        call_args = mock_akshare.fund_etf_hist_em.call_args
        assert call_args is not None

    def test_lof_hist_default_dates(self, adapter, mock_akshare):
        """测试LOF历史行情默认日期"""
        mock_df = pd.DataFrame({
            "日期": pd.to_datetime(["2024-01-01"]),
            "开盘": [1.5],
            "收盘": [1.52],
            "最高": [1.53],
            "最低": [1.49],
            "成交量": [500000],
            "成交额": [750000],
            "振幅": [2.67],
            "涨跌幅": [1.33],
            "涨跌额": [0.02],
            "换手率": [1.0],
        })
        mock_akshare.fund_lof_hist_em.return_value = mock_df

        result = adapter.get_lof_hist("160106")

        assert len(result) == 1

    def test_etf_minute_default_dates(self, adapter, mock_akshare):
        """测试ETF分时行情默认日期"""
        mock_df = pd.DataFrame({
            "时间": ["09:30", "09:31"],
            "开盘": [2.5, 2.51],
            "收盘": [2.51, 2.52],
            "最高": [2.51, 2.52],
            "最低": [2.5, 2.51],
            "成交量": [10000, 12000],
            "成交额": [25000, 30000],
            "均价": [2.505, 2.515],
        })
        mock_akshare.fund_etf_hist_min_em.return_value = mock_df

        result = adapter.get_etf_minute("510050")

        assert len(result) == 2

    def test_lof_minute_default_dates(self, adapter, mock_akshare):
        """测试LOF分时行情默认日期"""
        mock_df = pd.DataFrame({
            "时间": ["09:30", "09:31"],
            "开盘": [1.5, 1.51],
            "收盘": [1.51, 1.52],
            "最高": [1.51, 1.52],
            "最低": [1.5, 1.51],
            "成交量": [5000, 6000],
            "成交额": [7500, 9000],
            "均价": [1.505, 1.515],
        })
        mock_akshare.fund_lof_hist_min_em.return_value = mock_df

        result = adapter.get_lof_minute("160106")

        assert len(result) == 2


class TestFundCategorySpot:
    """测试基金分类实时行情"""

    def test_get_fund_category_spot_with_category(self, adapter, mock_akshare):
        """测试按类型获取基金实时行情"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金名称": ["华夏成长", "华夏大盘"],
            "当前单位净值": [1.5, 2.3],
            "增长率": ["0.5%", "1.2%"],
        })
        mock_akshare.fund_etf_category_ths.return_value = mock_df

        result = adapter.get_fund_category_spot(category="股票型")

        assert len(result) == 2
        mock_akshare.fund_etf_category_ths.assert_called_once()

    def test_get_fund_category_spot_with_date(self, adapter, mock_akshare):
        """测试指定日期获取基金实时行情"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001"],
            "基金名称": ["华夏成长"],
            "当前单位净值": [1.5],
        })
        mock_akshare.fund_etf_category_ths.return_value = mock_df

        result = adapter.get_fund_category_spot(category="股票型", date="20240101")

        assert len(result) == 1


class TestETFSpotThs:
    """测试同花顺ETF实时行情"""

    def test_get_etf_spot_ths_success(self, adapter, mock_akshare):
        """测试成功获取同花顺ETF实时行情"""
        mock_df = pd.DataFrame({
            "基金代码": ["510050", "510300"],
            "基金名称": ["华夏上证50ETF", "华泰柏瑞沪深300ETF"],
            "当前单位净值": [2.5, 3.8],
        })
        mock_akshare.fund_etf_spot_ths.return_value = mock_df

        result = adapter.get_etf_spot_ths()

        assert len(result) == 2
        assert "code" in result.columns

    def test_get_etf_spot_ths_with_date(self, adapter, mock_akshare):
        """测试指定日期获取同花顺ETF实时行情"""
        mock_df = pd.DataFrame({
            "基金代码": ["510050"],
            "基金名称": ["华夏上证50ETF"],
            "当前单位净值": [2.5],
        })
        mock_akshare.fund_etf_spot_ths.return_value = mock_df

        result = adapter.get_etf_spot_ths(date="20240101")

        assert len(result) == 1


class TestFundHoldingsExtended:
    """测试基金持仓扩展功能"""

    def test_get_fund_holdings_with_report_date(self, adapter, mock_akshare):
        """测试指定报告日期获取持仓"""
        mock_df = pd.DataFrame({
            "季度": ["2024Q2"],
            "股票代码": ["600519"],
            "股票名称": ["贵州茅台"],
            "占净值比例": ["9.5%"],
            "持股数": ["1000000"],
            "持仓市值": ["1800000000"],
        })
        mock_akshare.fund_portfolio_hold_em.return_value = mock_df

        result = adapter.get_fund_holdings("000001", report_date=date(2024, 6, 30))

        assert len(result) == 1
        assert "stock_code" in result.columns
        assert "weight" in result.columns

    def test_get_fund_bond_holdings_with_year(self, adapter, mock_akshare):
        """测试指定年份获取债券持仓"""
        mock_df = pd.DataFrame({
            "序号": [1],
            "债券代码": ["019547"],
            "债券名称": ["16国债19"],
            "占净值比例": ["5.2%"],
            "持仓市值(万元)": ["5200"],
            "季度": ["2024Q2"],
        })
        mock_akshare.fund_portfolio_bond_hold_em.return_value = mock_df

        result = adapter.get_fund_bond_holdings("000001", year=2024)

        assert len(result) == 1
        assert "bond_code" in result.columns

    def test_get_fund_industry_allocation_with_year(self, adapter, mock_akshare):
        """测试指定年份获取行业配置"""
        mock_df = pd.DataFrame({
            "序号": [1, 2],
            "行业类别": ["食品饮料", "非银金融"],
            "占净值比例": ["15.2%", "12.8%"],
            "市值": ["152000000", "128000000"],
            "截止时间": ["2024-06-30", "2024-06-30"],
        })
        mock_akshare.fund_portfolio_industry_allocation_em.return_value = mock_df

        result = adapter.get_fund_industry_allocation("000001", year=2024)

        assert len(result) == 2
        assert "industry" in result.columns

    def test_get_fund_portfolio_change_with_indicator(self, adapter, mock_akshare):
        """测试指定指标获取持仓变动"""
        mock_df = pd.DataFrame({
            "序号": [1],
            "股票代码": ["600519"],
            "股票名称": ["贵州茅台"],
            "本期累计买入/卖出金额": ["100000000"],
            "占期初基金资产净值比例": ["5.0%"],
            "季度": ["2024Q2"],
        })
        mock_akshare.fund_portfolio_change_em.return_value = mock_df

        result = adapter.get_fund_portfolio_change("000001", indicator="累计买入", year=2024)

        assert len(result) == 1
        assert "stock_code" in result.columns


class TestAllFundManagers:
    """测试基金经理大全"""

    def test_get_all_fund_managers_success(self, adapter, mock_akshare):
        """测试成功获取基金经理大全"""
        mock_df = pd.DataFrame({
            "序号": [1, 2],
            "姓名": ["张三", "李四"],
            "所属公司": ["华夏基金", "易方达基金"],
            "现任基金代码": ["000001,000002", "000003,000004"],
            "现任基金": ["华夏成长,华夏大盘", "易方达蓝筹,易方达消费"],
            "累计从业时间": ["10年", "8年"],
            "现任基金资产总规模": ["100亿", "200亿"],
            "现任基金最佳回报": ["150%", "120%"],
        })
        mock_akshare.fund_manager_em.return_value = mock_df

        result = adapter.get_all_fund_managers()

        assert len(result) == 2
        assert "name" in result.columns
        assert "company" in result.columns


class TestFundOverview:
    """测试基金概况"""

    def test_get_fund_overview_success(self, adapter, mock_akshare):
        """测试成功获取基金概况"""
        mock_df = pd.DataFrame({
            "Key": ["基金名称", "基金类型", "成立日期", "基金经理"],
            "Value": ["华夏成长混合", "混合型", "2001-12-18", "张三"],
        })
        mock_akshare.fund_overview_em.return_value = mock_df

        result = adapter.get_fund_overview("000001")

        assert result["code"] == "000001"
        assert "基金名称" in result


class TestFundPurchaseStatus:
    """测试基金申购状态"""

    def test_get_fund_purchase_status_success(self, adapter, mock_akshare):
        """测试成功获取基金申购状态"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金简称": ["华夏成长", "华夏大盘"],
            "基金类型": ["混合型", "混合型"],
            "最新净值/万份收益": [1.5, 2.3],
            "报告时间": ["2024-01-01", "2024-01-01"],
            "申购状态": ["开放申购", "暂停申购"],
            "赎回状态": ["开放赎回", "开放赎回"],
            "下一开放日": ["", ""],
            "购买起点": ["10", "100"],
            "日累计限定金额": ["100000", "50000"],
            "手续费": ["1.5%", "1.2%"],
        })
        mock_akshare.fund_purchase_em.return_value = mock_df

        result = adapter.get_fund_purchase_status()

        assert len(result) == 2
        assert "code" in result.columns
        assert "purchase_status" in result.columns


class TestFundDailyNav:
    """测试基金每日净值"""

    def test_get_fund_daily_nav_success(self, adapter, mock_akshare):
        """测试成功获取基金每日净值"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金简称": ["华夏成长", "华夏大盘"],
            "当日单位净值": [1.5, 2.3],
            "当日累计净值": [2.0, 3.0],
            "前日单位净值": [1.49, 2.28],
            "前日累计净值": [1.99, 2.98],
            "日增长值": [0.01, 0.02],
            "日增长率": ["0.67%", "0.88%"],
            "申购状态": ["开放", "开放"],
            "赎回状态": ["开放", "开放"],
            "手续费": ["1.5%", "1.2%"],
        })
        mock_akshare.fund_open_fund_daily_em.return_value = mock_df

        result = adapter.get_fund_daily_nav()

        assert len(result) == 2
        assert "code" in result.columns
        assert "unit_nav" in result.columns


class TestIndexFundInfo:
    """测试指数基金信息"""

    def test_get_index_fund_info_success(self, adapter, mock_akshare):
        """测试成功获取指数基金信息"""
        mock_df = pd.DataFrame({
            "基金代码": ["510050", "510300"],
            "基金名称": ["华夏上证50ETF", "华泰柏瑞沪深300ETF"],
            "单位净值": [2.5, 3.8],
            "日期": ["2024-01-01", "2024-01-01"],
            "日增长率": ["0.5%", "1.2%"],
            "近1周": ["1.0%", "1.5%"],
            "近1月": ["2.0%", "3.0%"],
            "近3月": ["5.0%", "6.0%"],
            "近6月": ["10.0%", "12.0%"],
            "近1年": ["15.0%", "18.0%"],
            "近2年": ["20.0%", "25.0%"],
            "近3年": ["30.0%", "35.0%"],
            "今年来": ["5.0%", "6.0%"],
            "成立来": ["100.0%", "150.0%"],
            "手续费": ["0.5%", "0.6%"],
            "起购金额": ["1", "1"],
            "跟踪标的": ["上证50", "沪深300"],
            "跟踪方式": ["完全复制", "完全复制"],
        })
        mock_akshare.fund_info_index_em.return_value = mock_df

        result = adapter.get_index_fund_info(category="沪深指数", indicator="被动指数型")

        assert len(result) == 2
        assert "code" in result.columns
        assert "tracking_target" in result.columns


class TestFundInfoThs:
    """测试同花顺基金信息"""

    def test_get_fund_info_ths_success(self, adapter, mock_akshare):
        """测试成功获取同花顺基金信息"""
        mock_df = pd.DataFrame({
            "字段": ["基金简称", "基金全称", "基金类型", "投资类型", "基金经理", "成立日期", "成立规模", "基金管理人", "基金托管人", "管理费", "托管费", "认购费", "申购费", "赎回费", "业绩比较基准", "份额规模"],
            "值": ["华夏成长", "华夏成长混合型证券投资基金", "混合型", "偏股混合型", "张三", "2001-12-18", "50亿份", "华夏基金管理有限公司", "中国建设银行股份有限公司", "1.5%", "0.25%", "1.2%", "1.5%", "0.5%", "沪深300指数收益率×70%+上证国债指数收益率×30%", "100亿份"],
        })
        mock_akshare.fund_info_ths.return_value = mock_df

        result = adapter.get_fund_info_ths("000001")

        assert result["code"] == "000001"
        assert result["name"] == "华夏成长"
        assert result["type"] == "混合型"
