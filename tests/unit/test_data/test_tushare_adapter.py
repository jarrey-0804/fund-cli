"""
TushareAdapter 单元测试
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from fund_cli.data.adapters.tushare_adapter import TushareAdapter
from fund_cli.data.base import DataNotFoundError, DataSourceError


def reload_config():
    """重新加载配置"""
    import fund_cli.config as config_module
    config_module._config = None


@pytest.fixture
def mock_tushare():
    """Mock Tushare Pro API"""
    with patch("tushare.pro_api") as mock_api:
        mock_ts = MagicMock()
        mock_api.return_value = mock_ts
        yield mock_ts


@pytest.fixture
def adapter(monkeypatch):
    """创建 TushareAdapter 实例"""
    # 设置测试用的 Token - 使用 monkeypatch 设置环境变量
    monkeypatch.setenv("FUND_DATA_TUSHARE_TOKEN", "test_token")
    # 清除配置缓存，强制重新加载
    reload_config()
    return TushareAdapter()


class TestTushareAdapterInit:
    """测试初始化"""

    def test_init(self, adapter):
        """测试初始化"""
        assert adapter.name == "tushare"
        assert adapter._ts is None
        assert adapter._request_count == 0

    def test_init_with_cache(self, monkeypatch):
        """测试带缓存初始化"""
        monkeypatch.setenv("FUND_DATA_TUSHARE_TOKEN", "test_token")
        reload_config()
        mock_cache = MagicMock()
        adapter = TushareAdapter(cache=mock_cache)
        assert adapter._cache == mock_cache

    def test_is_available_with_token(self, monkeypatch):
        """测试 Token 存在时可用"""
        monkeypatch.setenv("FUND_DATA_TUSHARE_TOKEN", "test_token")
        # 清除配置缓存
        reload_config()
        adapter = TushareAdapter()
        assert adapter.is_available() is True

    def test_is_available_without_token(self, monkeypatch):
        """测试 Token 不存在时不可用"""
        # 清除 Token
        monkeypatch.delenv("FUND_DATA_TUSHARE_TOKEN", raising=False)
        # 清除配置缓存
        reload_config()
        adapter = TushareAdapter()
        assert adapter.is_available() is False

    def test_is_available_with_exception(self, monkeypatch):
        """测试配置异常时返回 False"""
        monkeypatch.delenv("FUND_DATA_TUSHARE_TOKEN", raising=False)
        reload_config()
        adapter = TushareAdapter()
        # 即使配置加载失败，也应该返回 False
        result = adapter.is_available()
        assert result is False


class TestTushareAdapterGetTushare:
    """测试 _get_tushare 方法"""

    def test_get_tushare_token_not_configured(self, monkeypatch):
        """测试 Token 未配置时抛出异常"""
        monkeypatch.delenv("FUND_DATA_TUSHARE_TOKEN", raising=False)
        reload_config()
        adapter = TushareAdapter()
        
        with pytest.raises(DataSourceError, match="Tushare Token 未配置"):
            adapter._get_tushare()

    def test_get_tushare_import_error(self, monkeypatch):
        """测试 Tushare 未安装时抛出异常"""
        monkeypatch.setenv("FUND_DATA_TUSHARE_TOKEN", "test_token")
        reload_config()
        adapter = TushareAdapter()
        
        with patch.dict('sys.modules', {'tushare': None}):
            with pytest.raises(DataSourceError, match="Tushare 未安装"):
                adapter._get_tushare()

    def test_get_tushare_lazy_loading(self, monkeypatch, mock_tushare):
        """测试延迟加载"""
        monkeypatch.setenv("FUND_DATA_TUSHARE_TOKEN", "test_token")
        reload_config()
        adapter = TushareAdapter()
        
        # 第一次调用
        ts1 = adapter._get_tushare()
        # 第二次调用应该返回同一个实例
        ts2 = adapter._get_tushare()
        
        assert ts1 is ts2


class TestTushareAdapterFundInfo:
    """测试基金信息接口"""

    def test_get_fund_info(self, adapter, mock_tushare):
        """测试获取基金信息"""
        # Mock 返回数据
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF"],
            "name": ["华夏成长混合"],
            "fund_type": ["混合型"],
            "found_date": ["20011218"],
            "manager": ["王泽实"],
            "management": ["华夏基金"],
        })

        result = adapter.get_fund_info("000001")

        assert result["code"] == "000001"
        assert result["name"] == "华夏成长混合"
        assert result["type"] == "混合型"
        assert result["company"] == "华夏基金"

    def test_get_fund_info_not_found(self, adapter, mock_tushare):
        """测试基金不存在"""
        mock_tushare.fund_basic.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError):
            adapter.get_fund_info("999999")

    def test_get_fund_info_with_cache(self, monkeypatch, mock_tushare):
        """测试带缓存的获取基金信息"""
        monkeypatch.setenv("FUND_DATA_TUSHARE_TOKEN", "test_token")
        reload_config()
        
        mock_cache = MagicMock()
        mock_cache.get_fund_info.return_value = None  # 缓存未命中
        
        adapter = TushareAdapter(cache=mock_cache)
        
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF"],
            "name": ["华夏成长混合"],
            "fund_type": ["混合型"],
            "found_date": ["20011218"],
            "manager": ["王泽实"],
            "management": ["华夏基金"],
        })

        result = adapter.get_fund_info("000001")
        
        # 验证缓存被设置
        mock_cache.set_fund_info.assert_called_once()

    def test_get_fund_info_cache_hit(self, monkeypatch, mock_tushare):
        """测试缓存命中"""
        monkeypatch.setenv("FUND_DATA_TUSHARE_TOKEN", "test_token")
        reload_config()
        
        mock_cache = MagicMock()
        cached_data = {"code": "000001", "name": "缓存数据"}
        mock_cache.get_fund_info.return_value = cached_data
        
        adapter = TushareAdapter(cache=mock_cache)
        
        result = adapter.get_fund_info("000001")
        
        assert result == cached_data
        # 不应该调用 API
        mock_tushare.fund_basic.assert_not_called()

    def test_get_fund_info_data_source_error(self, adapter, mock_tushare):
        """测试获取基金信息时的数据源错误"""
        mock_tushare.fund_basic.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取基金信息失败"):
            adapter.get_fund_info("000001")

    def test_get_all_fund_names(self, adapter, mock_tushare):
        """测试获取所有基金名称"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF", "000002.OF"],
            "name": ["华夏成长混合", "华夏大盘精选"],
            "fullname": ["华夏成长证券投资基金", "华夏大盘精选证券投资基金"],
            "symbol": ["HXCZ", "HXDP"],
            "fund_type": ["混合型", "混合型"],
        })

        result = adapter.get_all_fund_names()

        assert len(result) == 2
        assert "code" in result.columns
        assert "name" in result.columns

    def test_get_all_fund_names_error(self, adapter, mock_tushare):
        """测试获取所有基金名称时的错误"""
        mock_tushare.fund_basic.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取基金名称列表失败"):
            adapter.get_all_fund_names()

    def test_get_fund_info_ths(self, adapter, mock_tushare):
        """测试获取同花顺基金信息"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF"],
            "name": ["华夏成长混合"],
            "fullname": ["华夏成长证券投资基金"],
            "fund_type": ["混合型"],
            "management": ["华夏基金"],
            "trustee": ["中国建设银行"],
            "found_date": ["20011218"],
            "due_date": [""],
            "list_date": ["20011218"],
            "issue_date": ["20011101"],
            "delist_date": [""],
            "status": ["L"],
        })

        result = adapter.get_fund_info_ths("000001")

        assert result["code"] == "000001"
        assert result["name"] == "华夏成长混合"
        assert result["full_name"] == "华夏成长证券投资基金"
        assert result["management"] == "华夏基金"

    def test_get_fund_info_ths_not_found(self, adapter, mock_tushare):
        """测试同花顺基金信息不存在"""
        mock_tushare.fund_basic.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError):
            adapter.get_fund_info_ths("999999")

    def test_get_fund_info_ths_error(self, adapter, mock_tushare):
        """测试获取同花顺基金信息时的错误"""
        mock_tushare.fund_basic.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取同花顺基金信息失败"):
            adapter.get_fund_info_ths("000001")

    def test_get_index_fund_info(self, adapter, mock_tushare):
        """测试获取指数型基金信息"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["510050.SH", "510300.SH"],
            "name": ["50ETF", "300ETF"],
            "fund_type": ["ETF", "ETF"],
            "invest_type": ["被动指数型", "被动指数型"],
            "management": ["华夏基金", "华泰柏瑞基金"],
            "found_date": ["20040101", "20120101"],
        })

        result = adapter.get_index_fund_info()

        assert len(result) == 2
        assert "code" in result.columns
        assert "invest_type" in result.columns

    def test_get_index_fund_info_with_category(self, adapter, mock_tushare):
        """测试带分类的指数型基金信息"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["510050.SH"],
            "name": ["50ETF"],
            "fund_type": ["ETF"],
            "invest_type": ["被动指数型"],
            "management": ["华夏基金"],
            "found_date": ["20040101"],
        })

        result = adapter.get_index_fund_info(category="沪深指数")

        assert len(result) == 1

    def test_get_index_fund_info_error(self, adapter, mock_tushare):
        """测试获取指数型基金信息时的错误"""
        mock_tushare.fund_basic.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取指数基金信息失败"):
            adapter.get_index_fund_info()

    def test_get_fund_overview(self, adapter, mock_tushare):
        """测试获取基金概况"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF"],
            "name": ["华夏成长混合"],
            "fund_type": ["混合型"],
            "management": ["华夏基金"],
            "trustee": ["中国建设银行"],
            "found_date": ["20011218"],
            "status": ["L"],
        })

        result = adapter.get_fund_overview("000001")

        assert result["code"] == "000001"
        assert result["name"] == "华夏成长混合"
        assert result["management"] == "华夏基金"

    def test_get_fund_overview_not_found(self, adapter, mock_tushare):
        """测试基金概况不存在"""
        mock_tushare.fund_basic.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError):
            adapter.get_fund_overview("999999")

    def test_get_fund_overview_error(self, adapter, mock_tushare):
        """测试获取基金概况时的错误"""
        mock_tushare.fund_basic.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取基金概况失败"):
            adapter.get_fund_overview("000001")


class TestTushareAdapterPurchaseStatus:
    """测试申购状态接口"""

    def test_get_fund_purchase_status(self, adapter, mock_tushare):
        """测试获取基金申购状态"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF", "000002.OF"],
            "name": ["华夏成长混合", "华夏大盘精选"],
            "status": ["L", "L"],
        })

        result = adapter.get_fund_purchase_status()

        assert len(result) == 2
        assert "code" in result.columns
        assert "purchase_status" in result.columns

    def test_get_fund_purchase_status_error(self, adapter, mock_tushare):
        """测试获取基金申购状态时的错误"""
        mock_tushare.fund_basic.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取基金申购状态失败"):
            adapter.get_fund_purchase_status()


class TestTushareAdapterNav:
    """测试净值数据接口"""

    def test_get_fund_nav(self, adapter, mock_tushare):
        """测试获取基金净值"""
        mock_tushare.fund_nav.return_value = pd.DataFrame({
            "ts_code": ["000001.OF", "000001.OF"],
            "end_date": ["20240101", "20240102"],
            "unit_nav": [1.2345, 1.2456],
            "accum_nav": [2.3456, 2.3567],
        })

        result = adapter.get_fund_nav("000001")

        assert len(result) == 2
        assert "fund_code" in result.columns
        assert "nav_date" in result.columns
        assert "unit_nav" in result.columns
        assert "daily_return" in result.columns

    def test_get_fund_nav_with_dates(self, adapter, mock_tushare):
        """测试带日期范围的基金净值获取"""
        mock_tushare.fund_nav.return_value = pd.DataFrame({
            "ts_code": ["000001.OF"],
            "end_date": ["20240101"],
            "unit_nav": [1.2345],
            "accum_nav": [2.3456],
        })

        result = adapter.get_fund_nav(
            "000001",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )

        assert len(result) == 1

    def test_get_fund_nav_not_found(self, adapter, mock_tushare):
        """测试净值不存在"""
        mock_tushare.fund_nav.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError):
            adapter.get_fund_nav("999999")

    def test_get_fund_nav_error(self, adapter, mock_tushare):
        """测试获取净值时的错误"""
        mock_tushare.fund_nav.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取基金净值失败"):
            adapter.get_fund_nav("000001")

    def test_get_fund_nav_date_format(self, adapter, mock_tushare):
        """测试日期格式转换"""
        mock_tushare.fund_nav.return_value = pd.DataFrame({
            "ts_code": ["000001.OF"],
            "end_date": ["20240101"],
            "unit_nav": [1.2345],
            "accum_nav": [2.3456],
        })

        result = adapter.get_fund_nav("000001")

        # 日期应该转换为 YYYY-MM-DD 格式
        assert result["nav_date"].iloc[0] == "2024-01-01"

    def test_get_fund_daily_nav(self, adapter, mock_tushare):
        """测试获取每日净值"""
        mock_tushare.fund_nav.return_value = pd.DataFrame({
            "ts_code": ["000001.OF", "000002.OF"],
            "end_date": ["20240101", "20240101"],
            "unit_nav": [1.2345, 1.3456],
            "accum_nav": [2.3456, 2.4567],
        })

        result = adapter.get_fund_daily_nav()

        assert len(result) == 2
        assert "fund_code" in result.columns
        assert "nav_date" in result.columns

    def test_get_fund_daily_nav_not_found(self, adapter, mock_tushare):
        """测试每日净值不存在"""
        mock_tushare.fund_nav.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError):
            adapter.get_fund_daily_nav()

    def test_get_fund_daily_nav_error(self, adapter, mock_tushare):
        """测试获取每日净值时的错误"""
        mock_tushare.fund_nav.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取基金每日净值失败"):
            adapter.get_fund_daily_nav()


class TestTushareAdapterETF:
    """测试ETF相关接口"""

    def test_get_etf_spot(self, adapter, mock_tushare):
        """测试获取ETF实时行情"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["510050.SH", "510300.SH"],
            "name": ["50ETF", "300ETF"],
            "fund_type": ["ETF", "ETF"],
            "management": ["华夏基金", "华泰柏瑞基金"],
            "status": ["L", "L"],
        })

        result = adapter.get_etf_spot()

        assert len(result) == 2
        assert "code" in result.columns

    def test_get_etf_spot_error(self, adapter, mock_tushare):
        """测试获取ETF实时行情时的错误"""
        mock_tushare.fund_basic.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取ETF实时行情失败"):
            adapter.get_etf_spot()

    def test_get_lof_spot(self, adapter, mock_tushare):
        """测试获取LOF实时行情"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["160106.SZ", "160505.SZ"],
            "name": ["南方高增", "博时主题"],
            "fund_type": ["LOF", "LOF"],
            "management": ["南方基金", "博时基金"],
            "status": ["L", "L"],
        })

        result = adapter.get_lof_spot()

        assert len(result) == 2

    def test_get_lof_spot_error(self, adapter, mock_tushare):
        """测试获取LOF实时行情时的错误"""
        mock_tushare.fund_basic.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取LOF实时行情失败"):
            adapter.get_lof_spot()

    def test_get_fund_category_spot(self, adapter, mock_tushare):
        """测试获取基金分类行情"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF", "000002.OF"],
            "name": ["华夏成长混合", "华夏大盘精选"],
            "fund_type": ["混合型", "混合型"],
            "status": ["L", "L"],
        })

        result = adapter.get_fund_category_spot(category="混合型")

        assert len(result) == 2
        assert "code" in result.columns

    def test_get_fund_category_spot_without_category(self, adapter, mock_tushare):
        """测试不带分类的基金行情"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF"],
            "name": ["华夏成长混合"],
            "fund_type": ["混合型"],
            "status": ["L"],
        })

        result = adapter.get_fund_category_spot()

        assert len(result) == 1

    def test_get_fund_category_spot_error(self, adapter, mock_tushare):
        """测试获取基金分类行情时的错误"""
        mock_tushare.fund_basic.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取基金分类行情失败"):
            adapter.get_fund_category_spot()

    def test_get_etf_spot_ths(self, adapter, mock_tushare):
        """测试获取同花顺ETF实时行情"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["510050.SH"],
            "name": ["50ETF"],
            "fund_type": ["ETF"],
            "management": ["华夏基金"],
            "status": ["L"],
        })

        result = adapter.get_etf_spot_ths()

        assert len(result) == 1

    def test_get_etf_hist(self, adapter, mock_tushare):
        """测试获取ETF历史行情"""
        mock_tushare.fund_nav.return_value = pd.DataFrame({
            "ts_code": ["510050.SH", "510050.SH"],
            "end_date": ["20240101", "20240102"],
            "unit_nav": [2.5, 2.51],
            "accum_nav": [2.5, 2.51],
        })

        result = adapter.get_etf_hist("510050")

        assert len(result) == 2
        assert "fund_code" in result.columns
        assert "close" in result.columns
        assert "volume" in result.columns

    def test_get_etf_hist_with_dates(self, adapter, mock_tushare):
        """测试带日期的ETF历史行情"""
        mock_tushare.fund_nav.return_value = pd.DataFrame({
            "ts_code": ["510050.SH"],
            "end_date": ["20240101"],
            "unit_nav": [2.5],
            "accum_nav": [2.5],
        })

        result = adapter.get_etf_hist(
            "510050",
            period="daily",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        assert len(result) == 1

    def test_get_etf_hist_not_found(self, adapter, mock_tushare):
        """测试ETF历史行情不存在"""
        mock_tushare.fund_nav.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError):
            adapter.get_etf_hist("999999")

    def test_get_etf_hist_error(self, adapter, mock_tushare):
        """测试获取ETF历史行情时的错误"""
        mock_tushare.fund_nav.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取ETF历史行情失败"):
            adapter.get_etf_hist("510050")

    def test_get_lof_hist(self, adapter, mock_tushare):
        """测试获取LOF历史行情"""
        mock_tushare.fund_nav.return_value = pd.DataFrame({
            "ts_code": ["160106.SZ"],
            "end_date": ["20240101"],
            "unit_nav": [1.5],
            "accum_nav": [2.0],
        })

        result = adapter.get_lof_hist("160106")

        assert len(result) == 1


class TestTushareAdapterManager:
    """测试基金经理接口"""

    def test_get_fund_manager(self, adapter, mock_tushare):
        """测试获取基金经理信息"""
        mock_tushare.fund_manager.return_value = pd.DataFrame({
            "ts_code": ["000001.OF"],
            "name": ["王泽实"],
            "start_date": ["20220101"],
            "end_date": [None],
        })

        result = adapter.get_fund_manager("000001")

        assert len(result) == 1
        assert "fund_code" in result.columns
        assert "manager_name" in result.columns

    def test_get_fund_manager_not_found(self, adapter, mock_tushare):
        """测试基金经理信息不存在"""
        mock_tushare.fund_manager.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError):
            adapter.get_fund_manager("999999")

    def test_get_fund_manager_error(self, adapter, mock_tushare):
        """测试获取基金经理信息时的错误"""
        mock_tushare.fund_manager.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取基金经理信息失败"):
            adapter.get_fund_manager("000001")


class TestTushareAdapterHoldings:
    """测试持仓数据接口"""

    def test_get_fund_holdings(self, adapter, mock_tushare):
        """测试获取基金持仓"""
        mock_tushare.fund_portfolio.return_value = pd.DataFrame({
            "ts_code": ["000001.OF", "000001.OF"],
            "symbol": ["600519", "000858"],
            "name": ["贵州茅台", "五粮液"],
            "vol": ["10000", "20000"],
            "proportions": ["5.5", "4.2"],
        })

        result = adapter.get_fund_holdings("000001")

        assert len(result) == 2
        assert "fund_code" in result.columns
        assert "stock_code" in result.columns
        assert "proportion" in result.columns

    def test_get_fund_holdings_not_found(self, adapter, mock_tushare):
        """测试持仓数据不存在"""
        mock_tushare.fund_portfolio.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError):
            adapter.get_fund_holdings("999999")

    def test_get_fund_holdings_error(self, adapter, mock_tushare):
        """测试获取基金持仓时的错误"""
        mock_tushare.fund_portfolio.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取基金持仓失败"):
            adapter.get_fund_holdings("000001")


class TestTushareAdapterAssetAllocation:
    """测试资产配置接口"""

    def test_get_fund_asset_allocation(self, adapter, mock_tushare):
        """测试获取基金资产配置"""
        mock_tushare.fund_asset.return_value = pd.DataFrame({
            "ts_code": ["000001.OF"],
            "report_date": ["20240331"],
            "stock_ratio": ["60.5"],
            "bond_ratio": ["30.2"],
            "cash_ratio": ["9.3"],
            "total_asset": ["50.5"],
        })

        result = adapter.get_fund_asset_allocation("000001")

        assert result["fund_code"] == "000001"
        assert "stock_ratio" in result
        assert "bond_ratio" in result

    def test_get_fund_asset_allocation_not_found(self, adapter, mock_tushare):
        """测试资产配置数据不存在"""
        mock_tushare.fund_asset.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError):
            adapter.get_fund_asset_allocation("999999")

    def test_get_fund_asset_allocation_fund_not_in_result(self, adapter, mock_tushare):
        """测试基金不在资产配置结果中"""
        mock_tushare.fund_asset.return_value = pd.DataFrame({
            "ts_code": ["000002.OF"],
            "report_date": ["20240331"],
            "stock_ratio": ["60.5"],
            "bond_ratio": ["30.2"],
            "cash_ratio": ["9.3"],
            "total_asset": ["50.5"],
        })

        with pytest.raises(DataNotFoundError):
            adapter.get_fund_asset_allocation("000001")

    def test_get_fund_asset_allocation_error(self, adapter, mock_tushare):
        """测试获取基金资产配置时的错误"""
        mock_tushare.fund_asset.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取基金资产配置失败"):
            adapter.get_fund_asset_allocation("000001")


class TestTushareAdapterBenchmark:
    """测试基准相关接口"""

    def test_get_fund_benchmark(self, adapter, mock_tushare):
        """测试获取基金业绩比较基准"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF"],
            "name": ["华夏成长混合"],
            "fund_type": ["混合型"],
            "found_date": ["20011218"],
            "manager": ["王泽实"],
            "management": ["华夏基金"],
        })

        result = adapter.get_fund_benchmark("000001")

        assert result["fund_code"] == "000001"
        assert "benchmark" in result

    def test_get_benchmark_nav_sh_index(self, adapter, mock_tushare):
        """测试获取上证指数数据"""
        mock_tushare.index_daily.return_value = pd.DataFrame({
            "ts_code": ["000001.SH", "000001.SH"],
            "trade_date": ["20240101", "20240102"],
            "close": [3000.0, 3010.0],
        })

        result = adapter.get_benchmark_nav("000001")

        assert len(result) == 2
        assert "fund_code" in result.columns
        assert "daily_return" in result.columns

    def test_get_benchmark_nav_sz_index(self, adapter, mock_tushare):
        """测试获取深证指数数据"""
        mock_tushare.index_daily.return_value = pd.DataFrame({
            "ts_code": ["399001.SZ"],
            "trade_date": ["20240101"],
            "close": [10000.0],
        })

        result = adapter.get_benchmark_nav("399001")

        assert len(result) == 1

    def test_get_benchmark_nav_with_dates(self, adapter, mock_tushare):
        """测试带日期的基准指数数据"""
        mock_tushare.index_daily.return_value = pd.DataFrame({
            "ts_code": ["000001.SH"],
            "trade_date": ["20240101"],
            "close": [3000.0],
        })

        result = adapter.get_benchmark_nav(
            "000001",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )

        assert len(result) == 1

    def test_get_benchmark_nav_not_found(self, adapter, mock_tushare):
        """测试基准指数不存在"""
        mock_tushare.index_daily.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError):
            adapter.get_benchmark_nav("999999")

    def test_get_benchmark_nav_error(self, adapter, mock_tushare):
        """测试获取基准数据时的错误"""
        mock_tushare.index_daily.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="获取基准数据失败"):
            adapter.get_benchmark_nav("000001")


class TestTushareAdapterSearchFunds:
    """测试基金搜索接口"""

    def test_search_funds(self, adapter, mock_tushare):
        """测试搜索基金"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF", "000002.OF"],
            "name": ["华夏成长混合", "华夏大盘精选"],
            "fund_type": ["混合型", "混合型"],
            "management": ["华夏基金", "华夏基金"],
        })

        result = adapter.search_funds(keyword="华夏")

        assert len(result) == 2
        assert "code" in result.columns

    def test_search_funds_with_type(self, adapter, mock_tushare):
        """测试按类型搜索基金"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF"],
            "name": ["华夏成长混合"],
            "fund_type": ["混合型"],
            "management": ["华夏基金"],
        })

        result = adapter.search_funds(fund_type="混合型")

        assert len(result) == 1

    def test_search_funds_with_company(self, adapter, mock_tushare):
        """测试按公司搜索基金"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF", "000002.OF"],
            "name": ["华夏成长混合", "华夏大盘精选"],
            "fund_type": ["混合型", "混合型"],
            "management": ["华夏基金", "华夏基金"],
        })

        result = adapter.search_funds(company="华夏")

        assert len(result) == 2

    def test_search_funds_with_limit(self, adapter, mock_tushare):
        """测试带限制的基金搜索"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF", "000002.OF", "000003.OF"],
            "name": ["基金1", "基金2", "基金3"],
            "fund_type": ["混合型", "混合型", "混合型"],
            "management": ["公司1", "公司2", "公司3"],
        })

        result = adapter.search_funds(limit=2)

        assert len(result) == 2

    def test_search_funds_error(self, adapter, mock_tushare):
        """测试搜索基金时的错误"""
        mock_tushare.fund_basic.side_effect = Exception("网络错误")

        with pytest.raises(DataSourceError, match="搜索基金失败"):
            adapter.search_funds()

    def test_get_fund_list(self, adapter, mock_tushare):
        """测试获取基金列表"""
        mock_tushare.fund_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.OF"],
            "name": ["华夏成长混合"],
            "fund_type": ["混合型"],
            "management": ["华夏基金"],
        })

        result = adapter.get_fund_list()

        assert len(result) == 1


class TestTushareAdapterRateLimit:
    """测试限流机制"""

    def test_rate_limit(self, adapter):
        """测试请求频率限制"""
        import time

        start_time = time.time()

        # 模拟多次调用
        for _ in range(3):
            adapter._rate_limit()

        elapsed = time.time() - start_time

        # 至少应该有2次间隔（每次1秒）
        assert elapsed >= 2.0

    def test_rate_limit_updates_request_count(self, adapter):
        """测试限流更新请求计数"""
        initial_count = adapter._request_count
        
        adapter._rate_limit()
        
        assert adapter._request_count == initial_count + 1


class TestTushareAdapterDateConversion:
    """测试日期格式转换"""

    def test_convert_date_format_string(self, adapter):
        """测试字符串日期格式转换"""
        df = pd.DataFrame({
            "date": ["20240101", "20240102"],
            "value": [1, 2],
        })

        result = adapter._convert_date_format(df, ["date"])

        assert result["date"].iloc[0] == "2024-01-01"
        assert result["date"].iloc[1] == "2024-01-02"

    def test_convert_date_format_datetime(self, adapter):
        """测试 datetime 类型日期格式转换"""
        df = pd.DataFrame({
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "value": [1, 2],
        })

        result = adapter._convert_date_format(df, ["date"])

        assert result["date"].iloc[0] == "2024-01-01"
        assert result["date"].iloc[1] == "2024-01-02"

    def test_convert_date_format_missing_column(self, adapter):
        """测试缺失列的日期格式转换"""
        df = pd.DataFrame({
            "value": [1, 2],
        })

        result = adapter._convert_date_format(df, ["date"])

        # 不应该报错，只是不转换
        assert "value" in result.columns

    def test_convert_date_format_multiple_columns(self, adapter):
        """测试多列日期格式转换"""
        df = pd.DataFrame({
            "start_date": ["20240101", "20240102"],
            "end_date": ["20240110", "20240111"],
            "value": [1, 2],
        })

        result = adapter._convert_date_format(df, ["start_date", "end_date"])

        assert result["start_date"].iloc[0] == "2024-01-01"
        assert result["end_date"].iloc[0] == "2024-01-10"


class TestTushareAdapterMixinMethods:
    """测试 Mixin 提供的占位方法"""

    def test_unsupported_methods_raise_error(self, adapter):
        """测试未实现的方法抛出 DataSourceError"""
        # 测试几个 P1/P2 级别的方法
        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_company_aum()
        assert "不支持" in str(exc_info.value)

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_ratings()
        assert "不支持" in str(exc_info.value)

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_macro_leverage_ratio()
        assert "不支持" in str(exc_info.value)
