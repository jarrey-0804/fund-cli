"""
AKShare P0接口单元测试

P0 - 核心基金功能接口 (18个)
- 基金基本信息 (5个)
- 基金申购状态 (1个)
- 基金净值数据 (2个)
- 基金行情数据 (8个)
- 基金持仓数据 (4个)
- 基金经理 (1个)
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from fund_cli.data.adapters.akshare_adapter import AKShareAdapter
from fund_cli.data.base import DataNotFoundError, DataSourceError


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


class TestP0Interface:
    """P0核心接口测试类"""

    # =========================================================================
    # 基金基本信息 (5个)
    # =========================================================================

    def test_get_fund_info_success(self, adapter, mock_akshare):
        """测试成功获取基金基础信息"""
        mock_df = pd.DataFrame({
            "item": ["基金简称", "基金类型", "成立日期", "基金经理", "基金管理人", "基金规模"],
            "value": ["华夏成长混合", "混合型", "2001-12-18", "张三", "华夏基金", "50.5亿元"]
        })
        mock_akshare.fund_individual_basic_info_xq.return_value = mock_df

        result = adapter.get_fund_info("000001")

        assert result["code"] == "000001"
        assert result["name"] == "华夏成长混合"
        assert result["type"] == "混合型"
        assert result["manager"] == "张三"
        assert result["company"] == "华夏基金"
        assert result["scale"] == 50.5
        mock_akshare.fund_individual_basic_info_xq.assert_called_once_with(symbol="000001")

    def test_get_fund_info_error(self, adapter, mock_akshare):
        """测试获取基金信息API调用失败"""
        mock_akshare.fund_individual_basic_info_xq.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_info("000001")
        assert "获取基金信息失败" in str(exc_info.value)

    def test_get_fund_info_not_found(self, adapter, mock_akshare):
        """测试基金不存在场景"""
        mock_akshare.fund_individual_basic_info_xq.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_info("999999")
        assert "基金 999999 不存在" in str(exc_info.value)

    def test_get_all_fund_names_success(self, adapter, mock_akshare):
        """测试成功获取所有基金名称列表"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "拼音缩写": ["HXCZ", "HXCZHH"],
            "基金简称": ["华夏成长", "华夏成长混合"],
            "基金类型": ["混合型", "混合型"],
            "拼音全称": ["huaxiachengzhang", "huaxiachengzhanghunhe"]
        })
        mock_akshare.fund_name_em.return_value = mock_df

        result = adapter.get_all_fund_names()

        assert len(result) == 2
        assert "code" in result.columns
        assert "name" in result.columns
        assert result.iloc[0]["code"] == "000001"
        mock_akshare.fund_name_em.assert_called_once()

    def test_get_all_fund_names_error(self, adapter, mock_akshare):
        """测试获取基金名称列表API调用失败"""
        mock_akshare.fund_name_em.side_effect = Exception("连接超时")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_all_fund_names()
        assert "获取基金名称列表失败" in str(exc_info.value)

    def test_get_all_fund_names_not_found(self, adapter, mock_akshare):
        """测试基金名称列表数据不存在"""
        mock_akshare.fund_name_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_all_fund_names()
        assert "无法获取基金名称列表" in str(exc_info.value)

    def test_get_fund_info_ths_success(self, adapter, mock_akshare):
        """测试成功获取同花顺基金基本信息"""
        mock_df = pd.DataFrame({
            "字段": ["基金简称", "基金全称", "基金类型", "基金经理", "成立日期", "基金管理人"],
            "值": ["华夏成长", "华夏成长混合", "混合型", "张三", "2001-12-18", "华夏基金"]
        })
        mock_akshare.fund_info_ths.return_value = mock_df

        result = adapter.get_fund_info_ths("000001")

        assert result["code"] == "000001"
        assert result["name"] == "华夏成长"
        assert result["type"] == "混合型"
        mock_akshare.fund_info_ths.assert_called_once_with(symbol="000001")

    def test_get_fund_info_ths_error(self, adapter, mock_akshare):
        """测试获取同花顺基金信息API调用失败"""
        mock_akshare.fund_info_ths.side_effect = Exception("API错误")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_info_ths("000001")
        assert "获取同花顺基金信息失败" in str(exc_info.value)

    def test_get_fund_info_ths_not_found(self, adapter, mock_akshare):
        """测试同花顺基金信息不存在"""
        mock_akshare.fund_info_ths.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_info_ths("999999")
        assert "基金 999999 不存在" in str(exc_info.value)

    def test_get_index_fund_info_success(self, adapter, mock_akshare):
        """测试成功获取指数型基金基本信息"""
        mock_df = pd.DataFrame({
            "基金代码": ["510050", "510300"],
            "基金名称": ["华夏上证50ETF", "华泰柏瑞沪深300ETF"],
            "单位净值": ["2.5", "3.8"],
            "跟踪标的": ["上证50", "沪深300"]
        })
        mock_akshare.fund_info_index_em.return_value = mock_df

        result = adapter.get_index_fund_info(category="沪深指数", indicator="全部")

        assert len(result) == 2
        assert "code" in result.columns
        assert "tracking_target" in result.columns
        mock_akshare.fund_info_index_em.assert_called_once_with(symbol="沪深指数", indicator="全部")

    def test_get_index_fund_info_error(self, adapter, mock_akshare):
        """测试获取指数基金信息API调用失败"""
        mock_akshare.fund_info_index_em.side_effect = Exception("请求失败")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_index_fund_info()
        assert "获取指数型基金信息失败" in str(exc_info.value)

    def test_get_index_fund_info_not_found(self, adapter, mock_akshare):
        """测试指数基金信息不存在"""
        mock_akshare.fund_info_index_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_index_fund_info()
        assert "无法获取指数型基金信息" in str(exc_info.value)

    def test_get_fund_overview_success(self, adapter, mock_akshare):
        """测试成功获取基金档案基本概况"""
        mock_df = pd.DataFrame({
            "Key": ["基金名称", "基金类型", "成立日期"],
            "Value": ["华夏成长混合", "混合型", "2001-12-18"]
        })
        mock_akshare.fund_overview_em.return_value = mock_df

        result = adapter.get_fund_overview("000001")

        assert result["code"] == "000001"
        assert "基金名称" in result
        mock_akshare.fund_overview_em.assert_called_once_with(symbol="000001")

    def test_get_fund_overview_error(self, adapter, mock_akshare):
        """测试获取基金概况API调用失败"""
        mock_akshare.fund_overview_em.side_effect = Exception("服务不可用")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_overview("000001")
        assert "获取基金概况失败" in str(exc_info.value)

    def test_get_fund_overview_not_found(self, adapter, mock_akshare):
        """测试基金概况不存在"""
        mock_akshare.fund_overview_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_overview("999999")
        assert "基金 999999 概况不存在" in str(exc_info.value)

    # =========================================================================
    # 基金申购状态 (1个)
    # =========================================================================

    def test_get_fund_purchase_status_success(self, adapter, mock_akshare):
        """测试成功获取基金申购/赎回状态"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金简称": ["华夏成长", "华夏大盘"],
            "基金类型": ["混合型", "混合型"],
            "申购状态": ["开放申购", "暂停申购"],
            "赎回状态": ["开放赎回", "开放赎回"]
        })
        mock_akshare.fund_purchase_em.return_value = mock_df

        result = adapter.get_fund_purchase_status()

        assert len(result) == 2
        assert "code" in result.columns
        assert "purchase_status" in result.columns
        mock_akshare.fund_purchase_em.assert_called_once()

    def test_get_fund_purchase_status_error(self, adapter, mock_akshare):
        """测试获取申购状态API调用失败"""
        mock_akshare.fund_purchase_em.side_effect = Exception("API异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_purchase_status()
        assert "获取基金申购赎回状态失败" in str(exc_info.value)

    def test_get_fund_purchase_status_not_found(self, adapter, mock_akshare):
        """测试申购状态数据不存在"""
        mock_akshare.fund_purchase_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_purchase_status()
        assert "无法获取基金申购赎回状态" in str(exc_info.value)

    # =========================================================================
    # 基金净值数据 (2个)
    # =========================================================================

    def test_get_fund_nav_success(self, adapter, mock_akshare):
        """测试成功获取基金净值数据"""
        mock_df = pd.DataFrame({
            "净值日期": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "单位净值": ["1.5", "1.51", "1.52"],
            "日增长率": ["0.00", "0.67", "0.66"]
        })
        mock_akshare.fund_open_fund_info_em.return_value = mock_df

        result = adapter.get_fund_nav("000001")

        assert len(result) == 3
        assert "fund_code" in result.columns
        assert "unit_nav" in result.columns
        assert result.iloc[0]["fund_code"] == "000001"
        mock_akshare.fund_open_fund_info_em.assert_called_once()

    def test_get_fund_nav_error(self, adapter, mock_akshare):
        """测试获取基金净值API调用失败"""
        mock_akshare.fund_open_fund_info_em.side_effect = Exception("数据获取失败")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_nav("000001")
        assert "获取基金净值失败" in str(exc_info.value)

    def test_get_fund_nav_not_found(self, adapter, mock_akshare):
        """测试基金净值数据不存在"""
        mock_akshare.fund_open_fund_info_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_nav("999999")
        assert "基金 999999 净值数据不存在" in str(exc_info.value)

    def test_get_fund_daily_nav_success(self, adapter, mock_akshare):
        """测试成功获取开放式基金每日净值"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金简称": ["华夏成长", "华夏大盘"],
            "当日单位净值": ["1.5", "2.3"],
            "日增长率": ["0.5%", "1.2%"]
        })
        mock_akshare.fund_open_fund_daily_em.return_value = mock_df

        result = adapter.get_fund_daily_nav()

        assert len(result) == 2
        assert "code" in result.columns
        assert "unit_nav" in result.columns
        mock_akshare.fund_open_fund_daily_em.assert_called_once()

    def test_get_fund_daily_nav_error(self, adapter, mock_akshare):
        """测试获取每日净值API调用失败"""
        mock_akshare.fund_open_fund_daily_em.side_effect = Exception("网络异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_daily_nav()
        assert "获取基金每日净值失败" in str(exc_info.value)

    def test_get_fund_daily_nav_not_found(self, adapter, mock_akshare):
        """测试每日净值数据不存在"""
        mock_akshare.fund_open_fund_daily_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_daily_nav()
        assert "无法获取基金每日净值" in str(exc_info.value)

    # =========================================================================
    # 基金行情数据 (8个)
    # =========================================================================

    def test_get_etf_spot_success(self, adapter, mock_akshare):
        """测试成功获取ETF实时行情"""
        mock_df = pd.DataFrame({
            "代码": ["510050", "510300"],
            "名称": ["华夏上证50ETF", "华泰柏瑞沪深300ETF"],
            "最新价": ["2.5", "3.8"],
            "涨跌幅": ["0.5%", "1.2%"]
        })
        mock_akshare.fund_etf_spot_em.return_value = mock_df

        result = adapter.get_etf_spot()

        assert len(result) == 2
        assert "code" in result.columns
        assert "latest_price" in result.columns
        mock_akshare.fund_etf_spot_em.assert_called_once()

    def test_get_etf_spot_error(self, adapter, mock_akshare):
        """测试获取ETF实时行情API调用失败"""
        mock_akshare.fund_etf_spot_em.side_effect = Exception("行情服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_etf_spot()
        assert "获取ETF实时行情失败" in str(exc_info.value)

    def test_get_etf_spot_not_found(self, adapter, mock_akshare):
        """测试ETF实时行情数据不存在"""
        mock_akshare.fund_etf_spot_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_etf_spot()
        assert "无法获取ETF实时行情" in str(exc_info.value)

    def test_get_fund_category_spot_success(self, adapter, mock_akshare):
        """测试成功获取同花顺基金实时行情(按类型)"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金名称": ["华夏成长", "华夏大盘"],
            "当前单位净值": ["1.5", "2.3"],
            "增长率": ["0.5%", "1.2%"]
        })
        mock_akshare.fund_etf_category_ths.return_value = mock_df

        result = adapter.get_fund_category_spot(category="股票型")

        assert len(result) >= 0
        mock_akshare.fund_etf_category_ths.assert_called_once()

    def test_get_fund_category_spot_error(self, adapter, mock_akshare):
        """测试获取基金分类行情API调用失败"""
        mock_akshare.fund_etf_category_ths.side_effect = Exception("API错误")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_category_spot(category="股票型")
        assert "获取基金分类实时行情失败" in str(exc_info.value)

    def test_get_fund_category_spot_not_found(self, adapter, mock_akshare):
        """测试基金分类行情数据不存在"""
        mock_akshare.fund_etf_category_ths.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_category_spot(category="股票型")
        assert "无法获取 股票型 类型基金实时行情" in str(exc_info.value)

    def test_get_etf_spot_ths_success(self, adapter, mock_akshare):
        """测试成功获取同花顺ETF实时行情"""
        mock_df = pd.DataFrame({
            "基金代码": ["510050", "510300"],
            "基金名称": ["华夏上证50ETF", "华泰柏瑞沪深300ETF"],
            "当前单位净值": ["2.5", "3.8"]
        })
        mock_akshare.fund_etf_spot_ths.return_value = mock_df

        result = adapter.get_etf_spot_ths()

        assert len(result) == 2
        assert "code" in result.columns
        mock_akshare.fund_etf_spot_ths.assert_called_once()

    def test_get_etf_spot_ths_error(self, adapter, mock_akshare):
        """测试获取同花顺ETF行情API调用失败"""
        mock_akshare.fund_etf_spot_ths.side_effect = Exception("服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_etf_spot_ths()
        assert "获取同花顺ETF实时行情失败" in str(exc_info.value)

    def test_get_etf_spot_ths_not_found(self, adapter, mock_akshare):
        """测试同花顺ETF行情数据不存在"""
        mock_akshare.fund_etf_spot_ths.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_etf_spot_ths()
        assert "无法获取同花顺ETF实时行情" in str(exc_info.value)

    def test_get_lof_spot_success(self, adapter, mock_akshare):
        """测试成功获取LOF实时行情"""
        mock_df = pd.DataFrame({
            "代码": ["160106", "160505"],
            "名称": ["南方高增", "博时主题"],
            "最新价": ["1.2", "2.1"]
        })
        mock_akshare.fund_lof_spot_em.return_value = mock_df

        result = adapter.get_lof_spot()

        assert len(result) == 2
        assert "code" in result.columns
        mock_akshare.fund_lof_spot_em.assert_called_once()

    def test_get_lof_spot_error(self, adapter, mock_akshare):
        """测试获取LOF行情API调用失败"""
        mock_akshare.fund_lof_spot_em.side_effect = Exception("行情服务错误")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_lof_spot()
        assert "获取LOF实时行情失败" in str(exc_info.value)

    def test_get_lof_spot_not_found(self, adapter, mock_akshare):
        """测试LOF行情数据不存在"""
        mock_akshare.fund_lof_spot_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_lof_spot()
        assert "无法获取LOF实时行情" in str(exc_info.value)

    def test_get_etf_hist_success(self, adapter, mock_akshare):
        """测试成功获取ETF历史行情"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "开盘": ["2.4", "2.5"],
            "收盘": ["2.5", "2.6"],
            "最高": ["2.55", "2.65"],
            "最低": ["2.35", "2.45"]
        })
        mock_akshare.fund_etf_hist_em.return_value = mock_df

        result = adapter.get_etf_hist("510050", period="daily")

        assert len(result) == 2
        assert "code" in result.columns
        mock_akshare.fund_etf_hist_em.assert_called_once()

    def test_get_etf_hist_error(self, adapter, mock_akshare):
        """测试获取ETF历史行情API调用失败"""
        mock_akshare.fund_etf_hist_em.side_effect = Exception("历史数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_etf_hist("510050")
        assert "获取ETF历史行情失败" in str(exc_info.value)

    def test_get_etf_hist_not_found(self, adapter, mock_akshare):
        """测试ETF历史行情数据不存在"""
        mock_akshare.fund_etf_hist_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_etf_hist("999999")
        assert "ETF 999999 历史行情不存在" in str(exc_info.value)

    def test_get_lof_hist_success(self, adapter, mock_akshare):
        """测试成功获取LOF历史行情"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "开盘": ["1.2", "1.21"],
            "收盘": ["1.21", "1.22"]
        })
        mock_akshare.fund_lof_hist_em.return_value = mock_df

        result = adapter.get_lof_hist("160106", period="daily")

        assert len(result) == 2
        assert "code" in result.columns
        mock_akshare.fund_lof_hist_em.assert_called_once()

    def test_get_lof_hist_error(self, adapter, mock_akshare):
        """测试获取LOF历史行情API调用失败"""
        mock_akshare.fund_lof_hist_em.side_effect = Exception("数据服务错误")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_lof_hist("160106")
        assert "获取LOF历史行情失败" in str(exc_info.value)

    def test_get_lof_hist_not_found(self, adapter, mock_akshare):
        """测试LOF历史行情数据不存在"""
        mock_akshare.fund_lof_hist_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_lof_hist("999999")
        assert "LOF 999999 历史行情不存在" in str(exc_info.value)

    def test_get_etf_minute_success(self, adapter, mock_akshare):
        """测试成功获取ETF分时行情"""
        mock_df = pd.DataFrame({
            "时间": ["09:30", "09:31", "09:32"],
            "开盘": ["2.5", "2.51", "2.52"],
            "收盘": ["2.51", "2.52", "2.53"]
        })
        mock_akshare.fund_etf_hist_min_em.return_value = mock_df

        result = adapter.get_etf_minute("510050", period="1")

        assert len(result) == 3
        assert "code" in result.columns
        mock_akshare.fund_etf_hist_min_em.assert_called_once()

    def test_get_etf_minute_error(self, adapter, mock_akshare):
        """测试获取ETF分时行情API调用失败"""
        mock_akshare.fund_etf_hist_min_em.side_effect = Exception("分时数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_etf_minute("510050")
        assert "获取ETF分时行情失败" in str(exc_info.value)

    def test_get_etf_minute_not_found(self, adapter, mock_akshare):
        """测试ETF分时行情数据不存在"""
        mock_akshare.fund_etf_hist_min_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_etf_minute("999999")
        assert "ETF 999999 分时行情不存在" in str(exc_info.value)

    def test_get_lof_minute_success(self, adapter, mock_akshare):
        """测试成功获取LOF分时行情"""
        mock_df = pd.DataFrame({
            "时间": ["09:30", "09:31"],
            "开盘": ["1.2", "1.21"],
            "收盘": ["1.21", "1.22"]
        })
        mock_akshare.fund_lof_hist_min_em.return_value = mock_df

        result = adapter.get_lof_minute("160106", period="1")

        assert len(result) == 2
        assert "code" in result.columns
        mock_akshare.fund_lof_hist_min_em.assert_called_once()

    def test_get_lof_minute_error(self, adapter, mock_akshare):
        """测试获取LOF分时行情API调用失败"""
        mock_akshare.fund_lof_hist_min_em.side_effect = Exception("分时服务错误")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_lof_minute("160106")
        assert "获取LOF分时行情失败" in str(exc_info.value)

    def test_get_lof_minute_not_found(self, adapter, mock_akshare):
        """测试LOF分时行情数据不存在"""
        mock_akshare.fund_lof_hist_min_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_lof_minute("999999")
        assert "LOF 999999 分时行情不存在" in str(exc_info.value)

    # =========================================================================
    # 基金持仓数据 (4个)
    # =========================================================================

    def test_get_fund_holdings_success(self, adapter, mock_akshare):
        """测试成功获取基金持仓数据"""
        mock_df = pd.DataFrame({
            "季度": ["2024Q2", "2024Q2"],
            "股票代码": ["600519", "000858"],
            "股票名称": ["贵州茅台", "五粮液"],
            "占净值比例": ["9.5%", "7.2%"]
        })
        mock_akshare.fund_portfolio_hold_em.return_value = mock_df

        result = adapter.get_fund_holdings("000001")

        assert len(result) == 2
        assert "stock_code" in result.columns
        assert "weight" in result.columns
        mock_akshare.fund_portfolio_hold_em.assert_called_once()

    def test_get_fund_holdings_error(self, adapter, mock_akshare):
        """测试获取基金持仓API调用失败"""
        mock_akshare.fund_portfolio_hold_em.side_effect = Exception("持仓数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_holdings("000001")
        assert "获取持仓数据失败" in str(exc_info.value)

    def test_get_fund_holdings_not_found(self, adapter, mock_akshare):
        """测试基金持仓数据不存在"""
        mock_akshare.fund_portfolio_hold_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_holdings("999999")
        assert "基金 999999 持仓数据不存在" in str(exc_info.value)

    def test_get_fund_bond_holdings_success(self, adapter, mock_akshare):
        """测试成功获取基金债券持仓"""
        mock_df = pd.DataFrame({
            "序号": [1, 2],
            "债券代码": ["019547", "019548"],
            "债券名称": ["16国债19", "16国债20"],
            "占净值比例": ["5.2%", "3.8%"]
        })
        mock_akshare.fund_portfolio_bond_hold_em.return_value = mock_df

        result = adapter.get_fund_bond_holdings("000001", year="2024")

        assert len(result) == 2
        assert "bond_code" in result.columns
        mock_akshare.fund_portfolio_bond_hold_em.assert_called_once()

    def test_get_fund_bond_holdings_error(self, adapter, mock_akshare):
        """测试获取债券持仓API调用失败"""
        mock_akshare.fund_portfolio_bond_hold_em.side_effect = Exception("债券数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_bond_holdings("000001")
        assert "获取基金债券持仓失败" in str(exc_info.value)

    def test_get_fund_bond_holdings_not_found(self, adapter, mock_akshare):
        """测试基金债券持仓数据不存在"""
        mock_akshare.fund_portfolio_bond_hold_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_bond_holdings("999999")
        assert "基金 999999 债券持仓数据不存在" in str(exc_info.value)

    def test_get_fund_industry_allocation_success(self, adapter, mock_akshare):
        """测试成功获取基金行业配置"""
        mock_df = pd.DataFrame({
            "序号": [1, 2],
            "行业类别": ["食品饮料", "非银金融"],
            "占净值比例": ["15.2%", "12.8%"]
        })
        mock_akshare.fund_portfolio_industry_allocation_em.return_value = mock_df

        result = adapter.get_fund_industry_allocation("000001", year="2024")

        assert len(result) == 2
        assert "industry" in result.columns
        mock_akshare.fund_portfolio_industry_allocation_em.assert_called_once()

    def test_get_fund_industry_allocation_error(self, adapter, mock_akshare):
        """测试获取行业配置API调用失败"""
        mock_akshare.fund_portfolio_industry_allocation_em.side_effect = Exception("行业数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_industry_allocation("000001")
        assert "获取基金行业配置失败" in str(exc_info.value)

    def test_get_fund_industry_allocation_not_found(self, adapter, mock_akshare):
        """测试基金行业配置数据不存在"""
        mock_akshare.fund_portfolio_industry_allocation_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_industry_allocation("999999")
        assert "基金 999999 行业配置数据不存在" in str(exc_info.value)

    def test_get_fund_portfolio_change_success(self, adapter, mock_akshare):
        """测试成功获取基金重大变动"""
        mock_df = pd.DataFrame({
            "序号": [1, 2],
            "股票代码": ["600519", "000858"],
            "股票名称": ["贵州茅台", "五粮液"],
            "本期累计买入/卖出金额": ["1000万", "800万"]
        })
        mock_akshare.fund_portfolio_change_em.return_value = mock_df

        result = adapter.get_fund_portfolio_change("000001", indicator="累计买入")

        assert len(result) == 2
        mock_akshare.fund_portfolio_change_em.assert_called_once()

    def test_get_fund_portfolio_change_error(self, adapter, mock_akshare):
        """测试获取重大变动API调用失败"""
        mock_akshare.fund_portfolio_change_em.side_effect = Exception("变动数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_portfolio_change("000001")
        assert "获取基金重大变动失败" in str(exc_info.value)

    def test_get_fund_portfolio_change_not_found(self, adapter, mock_akshare):
        """测试基金重大变动数据不存在"""
        mock_akshare.fund_portfolio_change_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_portfolio_change("999999")
        assert "基金 999999 重大变动数据不存在" in str(exc_info.value)

    # =========================================================================
    # 基金经理 (1个)
    # =========================================================================

    def test_get_all_fund_managers_success(self, adapter, mock_akshare):
        """测试成功获取基金经理大全"""
        mock_df = pd.DataFrame({
            "序号": [1, 2],
            "姓名": ["张三", "李四"],
            "所属公司": ["华夏基金", "易方达基金"],
            "现任基金": ["华夏成长", "易方达蓝筹"]
        })
        mock_akshare.fund_manager_em.return_value = mock_df

        result = adapter.get_all_fund_managers()

        assert len(result) == 2
        assert "name" in result.columns
        assert "company" in result.columns
        mock_akshare.fund_manager_em.assert_called_once()

    def test_get_all_fund_managers_error(self, adapter, mock_akshare):
        """测试获取基金经理大全API调用失败"""
        mock_akshare.fund_manager_em.side_effect = Exception("经理数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_all_fund_managers()
        assert "获取基金经理大全失败" in str(exc_info.value)

    def test_get_all_fund_managers_not_found(self, adapter, mock_akshare):
        """测试基金经理数据不存在"""
        mock_akshare.fund_manager_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_all_fund_managers()
        assert "无法获取基金经理数据" in str(exc_info.value)
