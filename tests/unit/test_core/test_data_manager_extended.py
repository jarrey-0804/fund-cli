# -*- coding: utf-8 -*-
"""
DataManager 数据管理器补充测试

测试覆盖：
- P1 级别接口代理
- P2 级别接口代理
- 更多初始化分支
- 异常处理路径
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from fund_cli.core.data_manager import DataManager, get_data_manager
from fund_cli.data.base import DataSourceError


def _reset_config():
    """重置全局配置"""
    import fund_cli.config as config_module
    config_module._config = None


@pytest.fixture(autouse=True)
def reset_global_instances():
    """每个测试前后重置全局实例"""
    _reset_config()
    import fund_cli.core.data_manager as dm_module
    dm_module._data_manager = None
    yield
    dm_module._data_manager = None
    _reset_config()


@pytest.fixture
def mock_config():
    """创建模拟配置"""
    config = MagicMock()
    config.data.cache_dir = "/tmp/test_cache"
    config.data.cache_ttl = 3600
    config.data.primary_source = "akshare"
    config.data.akshare_enabled = True
    config.data.tushare_token = None
    config.data.wind_enabled = False
    config.data.source_priority_list = ["akshare", "tushare", "wind"]
    return config


@pytest.fixture
def mock_adapter():
    """创建模拟数据源适配器"""
    adapter = MagicMock()
    adapter.name = "test_adapter"
    adapter.is_available.return_value = True
    # P0 方法
    adapter.get_all_fund_names.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_fund_info_ths.return_value = {"code": "000001", "name": "测试基金"}
    adapter.get_index_fund_info.return_value = pd.DataFrame({"code": ["510050"]})
    adapter.get_fund_overview.return_value = {"code": "000001"}
    adapter.get_fund_purchase_status.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_fund_daily_nav.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_etf_spot.return_value = pd.DataFrame({"code": ["510050"]})
    adapter.get_fund_category_spot.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_etf_spot_ths.return_value = pd.DataFrame({"code": ["510050"]})
    adapter.get_lof_spot.return_value = pd.DataFrame({"code": ["160106"]})
    adapter.get_etf_hist.return_value = pd.DataFrame({"code": ["510050"]})
    adapter.get_lof_hist.return_value = pd.DataFrame({"code": ["160106"]})
    adapter.get_etf_minute.return_value = pd.DataFrame({"code": ["510050"]})
    adapter.get_lof_minute.return_value = pd.DataFrame({"code": ["160106"]})
    adapter.get_fund_bond_holdings.return_value = pd.DataFrame({"bond_code": ["019547"]})
    adapter.get_fund_industry_allocation.return_value = pd.DataFrame({"industry": ["食品饮料"]})
    adapter.get_fund_portfolio_change.return_value = pd.DataFrame({"stock_code": ["600519"]})
    adapter.get_all_fund_managers.return_value = pd.DataFrame({"name": ["张三"]})
    # P1 方法
    adapter.get_fund_company_aum.return_value = pd.DataFrame({"company": ["华夏基金"]})
    adapter.get_fund_aum_trend.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_fund_company_aum_history.return_value = pd.DataFrame({"company": ["华夏基金"]})
    adapter.get_fund_scale_change.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_fund_holder_structure.return_value = pd.DataFrame({"holder_type": ["个人"]})
    adapter.get_fund_ratings.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_fund_rating_sh.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_fund_rating_zs.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_fund_rating_ja.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_fund_dividends.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_fund_splits.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_fund_dividend_rank.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_fund_rank_by_type.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_exchange_fund_rank.return_value = pd.DataFrame({"code": ["510050"]})
    adapter.get_money_fund_rank.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_lcx_fund_rank.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_hk_fund_rank.return_value = pd.DataFrame({"code": ["000001"]})
    adapter.get_fund_achievement.return_value = pd.DataFrame({"year": ["2024"]})
    adapter.get_fund_risk_analysis.return_value = pd.DataFrame({"sharpe": [1.5]})
    adapter.get_fund_profit_probability.return_value = pd.DataFrame({"period": ["1年"]})
    adapter.get_fund_asset_allocation.return_value = pd.DataFrame({"asset": ["股票"]})
    adapter.get_index_spot_em.return_value = pd.DataFrame({"code": ["000300"]})
    adapter.get_index_spot_sina.return_value = pd.DataFrame({"code": ["000300"]})
    adapter.get_index_daily_tx.return_value = pd.DataFrame({"code": ["000300"]})
    adapter.get_index_daily_em.return_value = pd.DataFrame({"code": ["000300"]})
    adapter.get_index_hist.return_value = pd.DataFrame({"code": ["000300"]})
    adapter.get_index_minute.return_value = pd.DataFrame({"code": ["000300"]})
    # P2 方法
    adapter.get_macro_leverage_ratio.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_enterprise_price_index.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_fdi_data.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_lpr_data.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_urban_unemployment.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_social_financing.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_gdp_yearly.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_gdp_quarterly.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_cpi_yearly.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_cpi_monthly.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_ppi_yearly.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_ppi_monthly.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_exports_yearly.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_imports_yearly.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_trade_balance.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_industrial_production.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_pmi_official.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_pmi_caixin.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_services_pmi.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_non_manufacturing_pmi.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_m2_yearly.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_new_loan.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_retail_sales_yearly.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_fixed_asset_investment.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_china_interest_rate.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_usa_interest_rate.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_euro_interest_rate.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_japan_interest_rate.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_uk_interest_rate.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_shibor.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_shibor_lpr.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_hibor.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_industry_boards.return_value = pd.DataFrame({"code": ["BK0001"]})
    adapter.get_industry_board_hist.return_value = pd.DataFrame({"code": ["BK0001"]})
    adapter.get_concept_boards.return_value = pd.DataFrame({"code": ["BK0001"]})
    adapter.get_concept_board_hist.return_value = pd.DataFrame({"code": ["BK0001"]})
    adapter.get_sector_fund_flow.return_value = pd.DataFrame({"sector": ["电子"]})
    adapter.get_china_us_bond_yield.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_bond_yield_curve.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_bond_spot_quote.return_value = pd.DataFrame({"code": ["019547"]})
    adapter.get_convertible_bonds.return_value = pd.DataFrame({"code": ["110001"]})
    adapter.get_convertible_bond_detail.return_value = pd.DataFrame({"code": ["110001"]})
    adapter.get_bond_spot.return_value = pd.DataFrame({"code": ["019547"]})
    adapter.get_bond_hist.return_value = pd.DataFrame({"code": ["019547"]})
    adapter.get_a_share_valuation.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_stock_valuation_lg.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_index_valuation.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_market_pe_lg.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_market_pb_lg.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_market_fund_flow.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    adapter.get_stock_fund_flow.return_value = pd.DataFrame({"code": ["600519"]})
    adapter.get_north_fund_flow.return_value = pd.DataFrame({"date": ["2024-01-01"]})
    return adapter


# =============================================================================
# P1 级别接口测试
# =============================================================================


class TestP1Interfaces:
    """测试 P1 级别接口代理"""

    def test_get_fund_company_aum(self, mock_config, mock_adapter):
        """测试获取基金公司管理规模排名"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_company_aum()
                    mock_adapter.get_fund_company_aum.assert_called_once()

    def test_get_fund_aum_trend(self, mock_config, mock_adapter):
        """测试获取基金市场管理规模走势"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_aum_trend()
                    mock_adapter.get_fund_aum_trend.assert_called_once()

    def test_get_fund_company_aum_history(self, mock_config, mock_adapter):
        """测试获取基金公司历年管理规模"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_company_aum_history(year=2024)
                    mock_adapter.get_fund_company_aum_history.assert_called_once_with(2024)

    def test_get_fund_scale_change(self, mock_config, mock_adapter):
        """测试获取规模变动"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_scale_change()
                    mock_adapter.get_fund_scale_change.assert_called_once()

    def test_get_fund_holder_structure(self, mock_config, mock_adapter):
        """测试获取持有人结构"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_holder_structure()
                    mock_adapter.get_fund_holder_structure.assert_called_once()

    def test_get_fund_ratings(self, mock_config, mock_adapter):
        """测试获取基金评级总汇"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_ratings()
                    mock_adapter.get_fund_ratings.assert_called_once()

    def test_get_fund_rating_sh(self, mock_config, mock_adapter):
        """测试获取上海证券评级"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_rating_sh(date="20240101")
                    mock_adapter.get_fund_rating_sh.assert_called_once_with("20240101")

    def test_get_fund_rating_zs(self, mock_config, mock_adapter):
        """测试获取招商证券评级"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_rating_zs()
                    mock_adapter.get_fund_rating_zs.assert_called_once()

    def test_get_fund_rating_ja(self, mock_config, mock_adapter):
        """测试获取济安金信评级"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_rating_ja()
                    mock_adapter.get_fund_rating_ja.assert_called_once()

    def test_get_fund_dividends(self, mock_config, mock_adapter):
        """测试获取基金分红"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_dividends(year=2024, fund_type="股票型", page=1)
                    mock_adapter.get_fund_dividends.assert_called_once()

    def test_get_fund_splits(self, mock_config, mock_adapter):
        """测试获取基金拆分"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_splits()
                    mock_adapter.get_fund_splits.assert_called_once()

    def test_get_fund_dividend_rank(self, mock_config, mock_adapter):
        """测试获取累计分红排行"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_dividend_rank()
                    mock_adapter.get_fund_dividend_rank.assert_called_once()

    def test_get_fund_rank_by_type(self, mock_config, mock_adapter):
        """测试获取开放式基金排行"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_rank_by_type(fund_type="股票型")
                    mock_adapter.get_fund_rank_by_type.assert_called_once_with("股票型")

    def test_get_exchange_fund_rank(self, mock_config, mock_adapter):
        """测试获取场内交易基金排行"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_exchange_fund_rank()
                    mock_adapter.get_exchange_fund_rank.assert_called_once()

    def test_get_money_fund_rank(self, mock_config, mock_adapter):
        """测试获取货币型基金排行"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_money_fund_rank()
                    mock_adapter.get_money_fund_rank.assert_called_once()

    def test_get_lcx_fund_rank(self, mock_config, mock_adapter):
        """测试获取理财基金排行"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_lcx_fund_rank()
                    mock_adapter.get_lcx_fund_rank.assert_called_once()

    def test_get_hk_fund_rank(self, mock_config, mock_adapter):
        """测试获取香港基金排行"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_hk_fund_rank()
                    mock_adapter.get_hk_fund_rank.assert_called_once()

    def test_get_fund_achievement(self, mock_config, mock_adapter):
        """测试获取基金业绩"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_achievement("000001")
                    mock_adapter.get_fund_achievement.assert_called_once_with("000001")

    def test_get_fund_risk_analysis(self, mock_config, mock_adapter):
        """测试获取基金风险分析"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_risk_analysis("000001")
                    mock_adapter.get_fund_risk_analysis.assert_called_once_with("000001")

    def test_get_fund_profit_probability(self, mock_config, mock_adapter):
        """测试获取盈利概率"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_profit_probability("000001")
                    mock_adapter.get_fund_profit_probability.assert_called_once_with("000001")

    def test_get_fund_asset_allocation(self, mock_config, mock_adapter):
        """测试获取基金资产配置"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_fund_asset_allocation("000001", date="20240101")
                    mock_adapter.get_fund_asset_allocation.assert_called_once_with("000001", "20240101")

    def test_get_index_spot_em(self, mock_config, mock_adapter):
        """测试获取东财指数实时行情"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_index_spot_em(category="沪深重要指数")
                    mock_adapter.get_index_spot_em.assert_called_once_with("沪深重要指数")

    def test_get_index_spot_sina(self, mock_config, mock_adapter):
        """测试获取新浪指数实时行情"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_index_spot_sina()
                    mock_adapter.get_index_spot_sina.assert_called_once()

    def test_get_index_daily_tx(self, mock_config, mock_adapter):
        """测试获取腾讯指数历史"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_index_daily_tx("000300", start="20240101", end="20241231")
                    mock_adapter.get_index_daily_tx.assert_called_once()

    def test_get_index_daily_em(self, mock_config, mock_adapter):
        """测试获取东财指数历史"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_index_daily_em("000300")
                    mock_adapter.get_index_daily_em.assert_called_once_with("000300", None, None)

    def test_get_index_hist(self, mock_config, mock_adapter):
        """测试获取指数通用历史"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_index_hist("000300", period="weekly")
                    mock_adapter.get_index_hist.assert_called_once()

    def test_get_index_minute(self, mock_config, mock_adapter):
        """测试获取指数分时"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_index_minute("000300", period="5")
                    mock_adapter.get_index_minute.assert_called_once()


# =============================================================================
# P2 级别接口测试 - 宏观经济数据
# =============================================================================


class TestP2MacroEconomicInterfaces:
    """测试 P2 级别宏观经济数据接口"""

    def test_get_macro_leverage_ratio(self, mock_config, mock_adapter):
        """测试获取宏观杠杆率"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_macro_leverage_ratio()
                    mock_adapter.get_macro_leverage_ratio.assert_called_once()

    def test_get_enterprise_price_index(self, mock_config, mock_adapter):
        """测试获取企业商品价格指数"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_enterprise_price_index()
                    mock_adapter.get_enterprise_price_index.assert_called_once()

    def test_get_gdp_yearly(self, mock_config, mock_adapter):
        """测试获取GDP年率"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_gdp_yearly()
                    mock_adapter.get_gdp_yearly.assert_called_once()

    def test_get_cpi_yearly(self, mock_config, mock_adapter):
        """测试获取CPI年率"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_cpi_yearly()
                    mock_adapter.get_cpi_yearly.assert_called_once()

    def test_get_pmi_official(self, mock_config, mock_adapter):
        """测试获取官方PMI"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_pmi_official()
                    mock_adapter.get_pmi_official.assert_called_once()


# =============================================================================
# P2 级别接口测试 - 利率数据
# =============================================================================


class TestP2InterestRateInterfaces:
    """测试 P2 级别利率数据接口"""

    def test_get_china_interest_rate(self, mock_config, mock_adapter):
        """测试获取中国央行利率决议"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_china_interest_rate()
                    mock_adapter.get_china_interest_rate.assert_called_once()

    def test_get_usa_interest_rate(self, mock_config, mock_adapter):
        """测试获取美联储利率决议"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_usa_interest_rate()
                    mock_adapter.get_usa_interest_rate.assert_called_once()

    def test_get_shibor(self, mock_config, mock_adapter):
        """测试获取SHIBOR利率"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_shibor()
                    mock_adapter.get_shibor.assert_called_once()


# =============================================================================
# P2 级别接口测试 - 行业板块
# =============================================================================


class TestP2IndustryBoardInterfaces:
    """测试 P2 级别行业板块接口"""

    def test_get_industry_boards(self, mock_config, mock_adapter):
        """测试获取行业板块列表"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_industry_boards()
                    mock_adapter.get_industry_boards.assert_called_once()

    def test_get_industry_board_hist(self, mock_config, mock_adapter):
        """测试获取行业板块历史行情"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_industry_board_hist("BK0001", period="daily")
                    mock_adapter.get_industry_board_hist.assert_called_once()

    def test_get_concept_boards(self, mock_config, mock_adapter):
        """测试获取概念板块列表"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_concept_boards()
                    mock_adapter.get_concept_boards.assert_called_once()

    def test_get_sector_fund_flow(self, mock_config, mock_adapter):
        """测试获取板块资金流向"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_sector_fund_flow(period="今日")
                    mock_adapter.get_sector_fund_flow.assert_called_once_with("今日")


# =============================================================================
# P2 级别接口测试 - 债券数据
# =============================================================================


class TestP2BondInterfaces:
    """测试 P2 级别债券数据接口"""

    def test_get_china_us_bond_yield(self, mock_config, mock_adapter):
        """测试获取中美国债收益率"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_china_us_bond_yield()
                    mock_adapter.get_china_us_bond_yield.assert_called_once()

    def test_get_bond_yield_curve(self, mock_config, mock_adapter):
        """测试获取收益率曲线"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_bond_yield_curve(bond_type="国债", period="daily")
                    mock_adapter.get_bond_yield_curve.assert_called_once()

    def test_get_convertible_bonds(self, mock_config, mock_adapter):
        """测试获取可转债数据"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_convertible_bonds()
                    mock_adapter.get_convertible_bonds.assert_called_once()

    def test_get_bond_hist(self, mock_config, mock_adapter):
        """测试获取债券历史行情"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_bond_hist("019547", period="daily")
                    mock_adapter.get_bond_hist.assert_called_once()


# =============================================================================
# P2 级别接口测试 - 估值指标
# =============================================================================


class TestP2ValuationInterfaces:
    """测试 P2 级别估值指标接口"""

    def test_get_a_share_valuation(self, mock_config, mock_adapter):
        """测试获取A股估值"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_a_share_valuation()
                    mock_adapter.get_a_share_valuation.assert_called_once()

    def test_get_stock_valuation_lg(self, mock_config, mock_adapter):
        """测试获取个股估值"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_stock_valuation_lg("600519")
                    mock_adapter.get_stock_valuation_lg.assert_called_once_with("600519")

    def test_get_market_pe_lg(self, mock_config, mock_adapter):
        """测试获取指数市盈率"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_market_pe_lg("000300")
                    mock_adapter.get_market_pe_lg.assert_called_once_with("000300")


# =============================================================================
# P2 级别接口测试 - 资金流向
# =============================================================================


class TestP2FundFlowInterfaces:
    """测试 P2 级别资金流向接口"""

    def test_get_market_fund_flow(self, mock_config, mock_adapter):
        """测试获取大盘资金流向"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_market_fund_flow()
                    mock_adapter.get_market_fund_flow.assert_called_once()

    def test_get_stock_fund_flow(self, mock_config, mock_adapter):
        """测试获取个股资金流向"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_stock_fund_flow("600519", market="sh")
                    mock_adapter.get_stock_fund_flow.assert_called_once_with("600519", "sh")

    def test_get_north_fund_flow(self, mock_config, mock_adapter):
        """测试获取北向资金流向"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)
                    
                    dm.get_north_fund_flow(market="北向资金")
                    mock_adapter.get_north_fund_flow.assert_called_once_with("北向资金")


# =============================================================================
# 更多初始化分支测试
# =============================================================================


class TestMoreInitBranches:
    """测试更多初始化分支"""

    def test_init_with_no_available_adapters(self, mock_config):
        """测试无可用适配器时的初始化"""
        mock_config.data.akshare_enabled = False
        mock_config.data.tushare_token = None
        mock_config.data.wind_enabled = False

        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                dm = DataManager()
                assert len(dm._adapters) == 0

    def test_init_tushare_import_error(self, mock_config):
        """测试 Tushare 导入失败"""
        mock_config.tushare_token = "test_token"

        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch("fund_cli.core.data_manager.AKShareAdapter"):
                    with patch.dict("sys.modules", {"fund_cli.data.adapters.tushare_adapter": None}):
                        dm = DataManager()
                        # 应该不会崩溃

    def test_init_wind_import_error(self, mock_config):
        """测试 Wind 导入失败"""
        mock_config.wind_enabled = True

        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch("fund_cli.core.data_manager.AKShareAdapter"):
                    with patch.dict("sys.modules", {"fund_cli.data.adapters.wind_adapter": None}):
                        dm = DataManager()
                        # 应该不会崩溃


# =============================================================================
# 异常处理测试
# =============================================================================


class TestExceptionHandling:
    """测试异常处理"""

    def test_get_adapter_with_no_primary_source(self, mock_config):
        """测试无主数据源时获取适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "nonexistent"
                    
                    with pytest.raises(DataSourceError, match="未配置或不可用"):
                        dm.get_adapter()

    def test_data_access_with_no_adapter(self, mock_config):
        """测试无适配器时访问数据"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    # 无注册适配器
                    
                    with pytest.raises(DataSourceError):
                        dm.get_fund_info("000001")
