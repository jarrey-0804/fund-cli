"""
AKShare P2接口单元测试

P2 - 辅助分析功能接口 (57个)
- 宏观经济数据 (22个)
- 利率数据 (8个)
- 行业板块数据 (5个)
- 债券数据 (7个)
- 估值指标 (5个)
- 资金流向 (3个)
- 其他 (2个)
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


class TestP2Interface:
    """P2辅助分析接口测试类"""

    # =========================================================================
    # 宏观经济数据 (22个)
    # =========================================================================

    def test_get_macro_leverage_ratio_success(self, adapter, mock_akshare):
        """测试成功获取中国宏观杠杆率"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "杠杆率": ["280%", "282%"]
        })
        mock_akshare.macro_cnbs.return_value = mock_df

        result = adapter.get_macro_leverage_ratio()

        assert len(result) == 2
        mock_akshare.macro_cnbs.assert_called_once()

    def test_get_macro_leverage_ratio_error(self, adapter, mock_akshare):
        """测试获取宏观杠杆率API调用失败"""
        mock_akshare.macro_cnbs.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_macro_leverage_ratio()
        assert "获取宏观杠杆率失败" in str(exc_info.value)

    def test_get_enterprise_price_index_success(self, adapter, mock_akshare):
        """测试成功获取企业商品价格指数"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "指数": ["105", "106"]
        })
        mock_akshare.macro_china_qyspjg.return_value = mock_df

        result = adapter.get_enterprise_price_index()

        assert len(result) == 2
        mock_akshare.macro_china_qyspjg.assert_called_once()

    def test_get_enterprise_price_index_error(self, adapter, mock_akshare):
        """测试获取企业商品价格指数API调用失败"""
        mock_akshare.macro_china_qyspjg.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_enterprise_price_index()
        assert "获取企业商品价格指数失败" in str(exc_info.value)

    def test_get_fdi_data_success(self, adapter, mock_akshare):
        """测试成功获取外商直接投资数据"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "FDI": ["100亿", "120亿"]
        })
        mock_akshare.macro_china_fdi.return_value = mock_df

        result = adapter.get_fdi_data()

        assert len(result) == 2
        mock_akshare.macro_china_fdi.assert_called_once()

    def test_get_fdi_data_error(self, adapter, mock_akshare):
        """测试获取FDI数据API调用失败"""
        mock_akshare.macro_china_fdi.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fdi_data()
        assert "获取FDI数据失败" in str(exc_info.value)

    def test_get_lpr_data_success(self, adapter, mock_akshare):
        """测试成功获取LPR品种数据"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "1年期LPR": ["3.45%", "3.45%"],
            "5年期LPR": ["4.20%", "4.20%"]
        })
        mock_akshare.macro_china_lpr.return_value = mock_df

        result = adapter.get_lpr_data()

        assert len(result) == 2
        mock_akshare.macro_china_lpr.assert_called_once()

    def test_get_lpr_data_error(self, adapter, mock_akshare):
        """测试获取LPR数据API调用失败"""
        mock_akshare.macro_china_lpr.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_lpr_data()
        assert "获取LPR数据失败" in str(exc_info.value)

    def test_get_urban_unemployment_success(self, adapter, mock_akshare):
        """测试成功获取城镇调查失业率"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "失业率": ["5.2%", "5.1%"]
        })
        mock_akshare.macro_china_urban_unemployment.return_value = mock_df

        result = adapter.get_urban_unemployment()

        assert len(result) == 2
        mock_akshare.macro_china_urban_unemployment.assert_called_once()

    def test_get_urban_unemployment_error(self, adapter, mock_akshare):
        """测试获取失业率API调用失败"""
        mock_akshare.macro_china_urban_unemployment.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_urban_unemployment()
        assert "获取城镇失业率失败" in str(exc_info.value)

    def test_get_social_financing_success(self, adapter, mock_akshare):
        """测试成功获取社会融资规模增量"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "社融规模": ["4万亿", "3万亿"]
        })
        mock_akshare.macro_china_shrzgm.return_value = mock_df

        result = adapter.get_social_financing()

        assert len(result) == 2
        mock_akshare.macro_china_shrzgm.assert_called_once()

    def test_get_social_financing_error(self, adapter, mock_akshare):
        """测试获取社融数据API调用失败"""
        mock_akshare.macro_china_shrzgm.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_social_financing()
        assert "获取社会融资规模失败" in str(exc_info.value)

    def test_get_gdp_yearly_success(self, adapter, mock_akshare):
        """测试成功获取中国GDP年率"""
        mock_df = pd.DataFrame({
            "日期": ["2023", "2024"],
            "GDP年率": ["5.2%", "5.0%"]
        })
        mock_akshare.macro_china_gdp_yearly.return_value = mock_df

        result = adapter.get_gdp_yearly()

        assert len(result) == 2
        mock_akshare.macro_china_gdp_yearly.assert_called_once()

    def test_get_gdp_yearly_error(self, adapter, mock_akshare):
        """测试获取GDP年率API调用失败"""
        mock_akshare.macro_china_gdp_yearly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_gdp_yearly()
        assert "获取GDP年率失败" in str(exc_info.value)

    def test_get_gdp_quarterly_success(self, adapter, mock_akshare):
        """测试成功获取中国GDP季度数据"""
        mock_df = pd.DataFrame({
            "季度": ["2023Q4", "2024Q1"],
            "GDP": [["30万亿"], "31万亿"]
        })
        mock_akshare.macro_china_gdp_quarterly.return_value = mock_df

        result = adapter.get_gdp_quarterly()

        assert len(result) == 2
        mock_akshare.macro_china_gdp_quarterly.assert_called_once()

    def test_get_gdp_quarterly_error(self, adapter, mock_akshare):
        """测试获取GDP季度数据API调用失败"""
        mock_akshare.macro_china_gdp_quarterly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_gdp_quarterly()
        assert "获取GDP季度数据失败" in str(exc_info.value)

    def test_get_cpi_yearly_success(self, adapter, mock_akshare):
        """测试成功获取中国CPI年率"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "CPI年率": ["2.1%", "2.0%"]
        })
        mock_akshare.macro_china_cpi_yearly.return_value = mock_df

        result = adapter.get_cpi_yearly()

        assert len(result) == 2
        mock_akshare.macro_china_cpi_yearly.assert_called_once()

    def test_get_cpi_yearly_error(self, adapter, mock_akshare):
        """测试获取CPI年率API调用失败"""
        mock_akshare.macro_china_cpi_yearly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_cpi_yearly()
        assert "获取CPI年率失败" in str(exc_info.value)

    def test_get_cpi_monthly_success(self, adapter, mock_akshare):
        """测试成功获取中国CPI月率"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "CPI月率": ["0.3%", "0.2%"]
        })
        mock_akshare.macro_china_cpi_monthly.return_value = mock_df

        result = adapter.get_cpi_monthly()

        assert len(result) == 2
        mock_akshare.macro_china_cpi_monthly.assert_called_once()

    def test_get_cpi_monthly_error(self, adapter, mock_akshare):
        """测试获取CPI月率API调用失败"""
        mock_akshare.macro_china_cpi_monthly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_cpi_monthly()
        assert "获取CPI月率失败" in str(exc_info.value)

    def test_get_ppi_yearly_success(self, adapter, mock_akshare):
        """测试成功获取中国PPI年率"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "PPI年率": ["-2.5%", "-2.3%"]
        })
        mock_akshare.macro_china_ppi_yearly.return_value = mock_df

        result = adapter.get_ppi_yearly()

        assert len(result) == 2
        mock_akshare.macro_china_ppi_yearly.assert_called_once()

    def test_get_ppi_yearly_error(self, adapter, mock_akshare):
        """测试获取PPI年率API调用失败"""
        mock_akshare.macro_china_ppi_yearly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_ppi_yearly()
        assert "获取PPI年率失败" in str(exc_info.value)

    def test_get_ppi_monthly_success(self, adapter, mock_akshare):
        """测试成功获取中国PPI月率"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "PPI月率": ["0.1%", "0.2%"]
        })
        mock_akshare.macro_china_ppi_monthly.return_value = mock_df

        result = adapter.get_ppi_monthly()

        assert len(result) == 2
        mock_akshare.macro_china_ppi_monthly.assert_called_once()

    def test_get_ppi_monthly_error(self, adapter, mock_akshare):
        """测试获取PPI月率API调用失败"""
        mock_akshare.macro_china_ppi_monthly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_ppi_monthly()
        assert "获取PPI月率失败" in str(exc_info.value)

    def test_get_exports_yearly_success(self, adapter, mock_akshare):
        """测试成功获取出口年率"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "出口年率": ["7.1%", "5.6%"]
        })
        mock_akshare.macro_china_exports_yearly.return_value = mock_df

        result = adapter.get_exports_yearly()

        assert len(result) == 2
        mock_akshare.macro_china_exports_yearly.assert_called_once()

    def test_get_exports_yearly_error(self, adapter, mock_akshare):
        """测试获取出口年率API调用失败"""
        mock_akshare.macro_china_exports_yearly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_exports_yearly()
        assert "获取出口年率失败" in str(exc_info.value)

    def test_get_imports_yearly_success(self, adapter, mock_akshare):
        """测试成功获取进口年率"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "进口年率": ["3.5%", "4.2%"]
        })
        mock_akshare.macro_china_imports_yearly.return_value = mock_df

        result = adapter.get_imports_yearly()

        assert len(result) == 2
        mock_akshare.macro_china_imports_yearly.assert_called_once()

    def test_get_imports_yearly_error(self, adapter, mock_akshare):
        """测试获取进口年率API调用失败"""
        mock_akshare.macro_china_imports_yearly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_imports_yearly()
        assert "获取进口年率失败" in str(exc_info.value)

    def test_get_trade_balance_success(self, adapter, mock_akshare):
        """测试成功获取贸易帐"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "贸易帐": ["5000亿", "4800亿"]
        })
        mock_akshare.macro_china_trade_balance.return_value = mock_df

        result = adapter.get_trade_balance()

        assert len(result) == 2
        mock_akshare.macro_china_trade_balance.assert_called_once()

    def test_get_trade_balance_error(self, adapter, mock_akshare):
        """测试获取贸易帐API调用失败"""
        mock_akshare.macro_china_trade_balance.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_trade_balance()
        assert "获取贸易帐失败" in str(exc_info.value)

    def test_get_industrial_production_success(self, adapter, mock_akshare):
        """测试成功获取工业增加值增长"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "工业增加值": ["6.8%", "7.0%"]
        })
        mock_akshare.macro_china_industrial_production_yearly.return_value = mock_df

        result = adapter.get_industrial_production()

        assert len(result) == 2
        mock_akshare.macro_china_industrial_production_yearly.assert_called_once()

    def test_get_industrial_production_error(self, adapter, mock_akshare):
        """测试获取工业增加值API调用失败"""
        mock_akshare.macro_china_industrial_production_yearly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_industrial_production()
        assert "获取工业增加值失败" in str(exc_info.value)

    def test_get_pmi_official_success(self, adapter, mock_akshare):
        """测试成功获取官方制造业PMI"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "PMI": ["49.2", "50.8"]
        })
        mock_akshare.macro_china_pmi_yearly.return_value = mock_df

        result = adapter.get_pmi_official()

        assert len(result) == 2
        mock_akshare.macro_china_pmi_yearly.assert_called_once()

    def test_get_pmi_official_error(self, adapter, mock_akshare):
        """测试获取官方PMI API调用失败"""
        mock_akshare.macro_china_pmi_yearly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_pmi_official()
        assert "获取官方PMI失败" in str(exc_info.value)

    def test_get_pmi_caixin_success(self, adapter, mock_akshare):
        """测试成功获取财新制造业PMI"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "PMI": [["50.8"], "51.0"]
        })
        mock_akshare.macro_china_cx_pmi_yearly.return_value = mock_df

        result = adapter.get_pmi_caixin()

        assert len(result) == 2
        mock_akshare.macro_china_cx_pmi_yearly.assert_called_once()

    def test_get_pmi_caixin_error(self, adapter, mock_akshare):
        """测试获取财新PMI API调用失败"""
        mock_akshare.macro_china_cx_pmi_yearly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_pmi_caixin()
        assert "获取财新PMI失败" in str(exc_info.value)

    def test_get_services_pmi_success(self, adapter, mock_akshare):
        """测试成功获取财新服务业PMI"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "PMI": ["52.5", "53.0"]
        })
        mock_akshare.macro_china_cx_services_pmi.return_value = mock_df

        result = adapter.get_services_pmi()

        assert len(result) == 2
        mock_akshare.macro_china_cx_services_pmi.assert_called_once()

    def test_get_services_pmi_error(self, adapter, mock_akshare):
        """测试获取服务业PMI API调用失败"""
        mock_akshare.macro_china_cx_services_pmi.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_services_pmi()
        assert "获取服务业PMI失败" in str(exc_info.value)

    def test_get_non_manufacturing_pmi_success(self, adapter, mock_akshare):
        """测试成功获取官方非制造业PMI"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "PMI": ["50.7", "51.0"]
        })
        mock_akshare.macro_china_non_man_pmi.return_value = mock_df

        result = adapter.get_non_manufacturing_pmi()

        assert len(result) == 2
        mock_akshare.macro_china_non_man_pmi.assert_called_once()

    def test_get_non_manufacturing_pmi_error(self, adapter, mock_akshare):
        """测试获取非制造业PMI API调用失败"""
        mock_akshare.macro_china_non_man_pmi.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_non_manufacturing_pmi()
        assert "获取非制造业PMI失败" in str(exc_info.value)

    def test_get_m2_yearly_success(self, adapter, mock_akshare):
        """测试成功获取M2货币供应年率"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "M2": ["8.7%", "8.8%"]
        })
        mock_akshare.macro_china_m2_yearly.return_value = mock_df

        result = adapter.get_m2_yearly()

        assert len(result) == 2
        mock_akshare.macro_china_m2_yearly.assert_called_once()

    def test_get_m2_yearly_error(self, adapter, mock_akshare):
        """测试获取M2数据API调用失败"""
        mock_akshare.macro_china_m2_yearly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_m2_yearly()
        assert "获取M2数据失败" in str(exc_info.value)

    def test_get_new_loan_success(self, adapter, mock_akshare):
        """测试成功获取新增人民币贷款"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "新增贷款": ["4.9万亿", "1.5万亿"]
        })
        mock_akshare.macro_china_new_loan.return_value = mock_df

        result = adapter.get_new_loan()

        assert len(result) == 2
        mock_akshare.macro_china_new_loan.assert_called_once()

    def test_get_new_loan_error(self, adapter, mock_akshare):
        """测试获取新增贷款API调用失败"""
        mock_akshare.macro_china_new_loan.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_new_loan()
        assert "获取新增贷款失败" in str(exc_info.value)

    def test_get_retail_sales_yearly_success(self, adapter, mock_akshare):
        """测试成功获取社会消费品零售总额"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "零售总额": ["7.4%", "5.5%"]
        })
        mock_akshare.macro_china_retail_sales_yearly.return_value = mock_df

        result = adapter.get_retail_sales_yearly()

        assert len(result) == 2
        mock_akshare.macro_china_retail_sales_yearly.assert_called_once()

    def test_get_retail_sales_yearly_error(self, adapter, mock_akshare):
        """测试获取零售销售API调用失败"""
        mock_akshare.macro_china_retail_sales_yearly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_retail_sales_yearly()
        assert "获取零售销售失败" in str(exc_info.value)

    def test_get_fixed_asset_investment_success(self, adapter, mock_akshare):
        """测试成功获取固定资产投资"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "投资增速": ["3.0%", "4.2%"]
        })
        mock_akshare.macro_china_fixed_asset_investment_yearly.return_value = mock_df

        result = adapter.get_fixed_asset_investment()

        assert len(result) == 2
        mock_akshare.macro_china_fixed_asset_investment_yearly.assert_called_once()

    def test_get_fixed_asset_investment_error(self, adapter, mock_akshare):
        """测试获取固定资产投资API调用失败"""
        mock_akshare.macro_china_fixed_asset_investment_yearly.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fixed_asset_investment()
        assert "获取固定资产投资失败" in str(exc_info.value)

    # =========================================================================
    # 利率数据 (8个)
    # =========================================================================

    def test_get_china_interest_rate_success(self, adapter, mock_akshare):
        """测试成功获取中国央行利率决议"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "利率": ["3.45%", "3.45%"]
        })
        mock_akshare.macro_bank_china_interest_rate.return_value = mock_df

        result = adapter.get_china_interest_rate()

        assert len(result) == 2
        mock_akshare.macro_bank_china_interest_rate.assert_called_once()

    def test_get_china_interest_rate_error(self, adapter, mock_akshare):
        """测试获取中国利率API调用失败"""
        mock_akshare.macro_bank_china_interest_rate.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_china_interest_rate()
        assert "获取中国利率失败" in str(exc_info.value)

    def test_get_usa_interest_rate_success(self, adapter, mock_akshare):
        """测试成功获取美联储利率决议"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "利率": ["5.25%", "5.50%"]
        })
        mock_akshare.macro_bank_usa_interest_rate.return_value = mock_df

        result = adapter.get_usa_interest_rate()

        assert len(result) == 2
        mock_akshare.macro_bank_usa_interest_rate.assert_called_once()

    def test_get_usa_interest_rate_error(self, adapter, mock_akshare):
        """测试获取美国利率API调用失败"""
        mock_akshare.macro_bank_usa_interest_rate.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_usa_interest_rate()
        assert "获取美国利率失败" in str(exc_info.value)

    def test_get_euro_interest_rate_success(self, adapter, mock_akshare):
        """测试成功获取欧洲央行利率决议"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "利率": ["4.0%", "4.5%"]
        })
        mock_akshare.macro_bank_euro_interest_rate.return_value = mock_df

        result = adapter.get_euro_interest_rate()

        assert len(result) == 2
        mock_akshare.macro_bank_euro_interest_rate.assert_called_once()

    def test_get_euro_interest_rate_error(self, adapter, mock_akshare):
        """测试获取欧元区利率API调用失败"""
        mock_akshare.macro_bank_euro_interest_rate.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_euro_interest_rate()
        assert "获取欧元区利率失败" in str(exc_info.value)

    def test_get_japan_interest_rate_success(self, adapter, mock_akshare):
        """测试成功获取日本央行利率决议"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "利率": ["-0.1%", "0.0%"]
        })
        mock_akshare.macro_bank_japan_interest_rate.return_value = mock_df

        result = adapter.get_japan_interest_rate()

        assert len(result) == 2
        mock_akshare.macro_bank_japan_interest_rate.assert_called_once()

    def test_get_japan_interest_rate_error(self, adapter, mock_akshare):
        """测试获取日本利率API调用失败"""
        mock_akshare.macro_bank_japan_interest_rate.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_japan_interest_rate()
        assert "获取日本利率失败" in str(exc_info.value)

    def test_get_uk_interest_rate_success(self, adapter, mock_akshare):
        """测试成功获取英国央行利率决议"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "利率": ["5.25%", "5.25%"]
        })
        mock_akshare.macro_bank_uk_interest_rate.return_value = mock_df

        result = adapter.get_uk_interest_rate()

        assert len(result) == 2
        mock_akshare.macro_bank_uk_interest_rate.assert_called_once()

    def test_get_uk_interest_rate_error(self, adapter, mock_akshare):
        """测试获取英国利率API调用失败"""
        mock_akshare.macro_bank_uk_interest_rate.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_uk_interest_rate()
        assert "获取英国利率失败" in str(exc_info.value)

    def test_get_shibor_success(self, adapter, mock_akshare):
        """测试成功获取SHIBOR利率"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "隔夜": ["1.5%", "1.6%"],
            "1周": ["1.8%", "1.9%"]
        })
        mock_akshare.macro_china_shibor.return_value = mock_df

        result = adapter.get_shibor()

        assert len(result) == 2
        mock_akshare.macro_china_shibor.assert_called_once()

    def test_get_shibor_error(self, adapter, mock_akshare):
        """测试获取SHIBOR API调用失败"""
        mock_akshare.macro_china_shibor.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_shibor()
        assert "获取SHIBOR失败" in str(exc_info.value)

    def test_get_shibor_lpr_success(self, adapter, mock_akshare):
        """测试成功获取SHIBOR-LPR"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "LPR": ["3.45%", "3.45%"]
        })
        mock_akshare.macro_china_shibor_lpr.return_value = mock_df

        result = adapter.get_shibor_lpr()

        assert len(result) == 2
        mock_akshare.macro_china_shibor_lpr.assert_called_once()

    def test_get_shibor_lpr_error(self, adapter, mock_akshare):
        """测试获取SHIBOR-LPR API调用失败"""
        mock_akshare.macro_china_shibor_lpr.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_shibor_lpr()
        assert "获取SHIBOR-LPR失败" in str(exc_info.value)

    def test_get_hibor_success(self, adapter, mock_akshare):
        """测试成功获取HIBOR利率"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "隔夜": ["2.5%", "2.6%"]
        })
        mock_akshare.macro_china_hibor.return_value = mock_df

        result = adapter.get_hibor()

        assert len(result) == 2
        mock_akshare.macro_china_hibor.assert_called_once()

    def test_get_hibor_error(self, adapter, mock_akshare):
        """测试获取HIBOR API调用失败"""
        mock_akshare.macro_china_hibor.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_hibor()
        assert "获取HIBOR失败" in str(exc_info.value)

    # =========================================================================
    # 行业板块数据 (5个)
    # =========================================================================

    def test_get_industry_boards_success(self, adapter, mock_akshare):
        """测试成功获取行业板块列表"""
        mock_df = pd.DataFrame({
            "板块代码": ["BK01", "BK02"],
            "板块名称": ["银行", "证券"]
        })
        mock_akshare.stock_board_industry_name_em.return_value = mock_df

        result = adapter.get_industry_boards()

        assert len(result) == 2
        mock_akshare.stock_board_industry_name_em.assert_called_once()

    def test_get_industry_boards_error(self, adapter, mock_akshare):
        """测试获取行业板块列表API调用失败"""
        mock_akshare.stock_board_industry_name_em.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_industry_boards()
        assert "获取行业板块列表失败" in str(exc_info.value)

    def test_get_industry_board_hist_success(self, adapter, mock_akshare):
        """测试成功获取行业板块历史行情"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "收盘": ["1000", "1020"]
        })
        mock_akshare.stock_board_industry_hist_em.return_value = mock_df

        result = adapter.get_industry_board_hist("银行")

        assert len(result) == 2
        mock_akshare.stock_board_industry_hist_em.assert_called_once()

    def test_get_industry_board_hist_error(self, adapter, mock_akshare):
        """测试获取行业板块历史API调用失败"""
        mock_akshare.stock_board_industry_hist_em.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_industry_board_hist("银行")
        assert "获取行业板块历史数据失败" in str(exc_info.value)

    def test_get_concept_boards_success(self, adapter, mock_akshare):
        """测试成功获取概念板块列表"""
        mock_df = pd.DataFrame({
            "板块代码": ["GN01", "GN02"],
            "板块名称": ["人工智能", "新能源"]
        })
        mock_akshare.stock_board_concept_name_em.return_value = mock_df

        result = adapter.get_concept_boards()

        assert len(result) == 2
        mock_akshare.stock_board_concept_name_em.assert_called_once()

    def test_get_concept_boards_error(self, adapter, mock_akshare):
        """测试获取概念板块列表API调用失败"""
        mock_akshare.stock_board_concept_name_em.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_concept_boards()
        assert "获取概念板块列表失败" in str(exc_info.value)

    def test_get_concept_board_hist_success(self, adapter, mock_akshare):
        """测试成功获取概念板块历史行情"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "收盘": ["1500", "1520"]
        })
        mock_akshare.stock_board_concept_hist_em.return_value = mock_df

        result = adapter.get_concept_board_hist("人工智能")

        assert len(result) == 2
        mock_akshare.stock_board_concept_hist_em.assert_called_once()

    def test_get_concept_board_hist_error(self, adapter, mock_akshare):
        """测试获取概念板块历史API调用失败"""
        mock_akshare.stock_board_concept_hist_em.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_concept_board_hist("人工智能")
        assert "获取概念板块历史数据失败" in str(exc_info.value)

    def test_get_sector_fund_flow_success(self, adapter, mock_akshare):
        """测试成功获取板块资金流向"""
        mock_df = pd.DataFrame({
            "板块": ["银行", "证券"],
            "净流入": ["10亿", "5亿"]
        })
        mock_akshare.stock_sector_spot.return_value = mock_df

        result = adapter.get_sector_fund_flow(period="今日")

        assert len(result) == 2
        mock_akshare.stock_sector_spot.assert_called_once()

    def test_get_sector_fund_flow_error(self, adapter, mock_akshare):
        """测试获取板块资金流向API调用失败"""
        mock_akshare.stock_sector_spot.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_sector_fund_flow()
        assert "获取板块资金流向失败" in str(exc_info.value)

    # =========================================================================
    # 债券数据 (7个)
    # =========================================================================

    def test_get_china_us_bond_yield_success(self, adapter, mock_akshare):
        """测试成功获取中美国债收益率"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "中国10年": ["2.5%", "2.6%"],
            "美国10年": [["4.0%"], "4.1%"]
        })
        mock_akshare.bond_zh_us_rate.return_value = mock_df

        result = adapter.get_china_us_bond_yield()

        assert len(result) == 2
        mock_akshare.bond_zh_us_rate.assert_called_once()

    def test_get_china_us_bond_yield_error(self, adapter, mock_akshare):
        """测试获取中美国债收益率API调用失败"""
        mock_akshare.bond_zh_us_rate.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_china_us_bond_yield()
        assert "获取中美国债收益率失败" in str(exc_info.value)

    def test_get_bond_yield_curve_success(self, adapter, mock_akshare):
        """测试成功获取收盘收益率曲线"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "1年": ["2.0%", "2.1%"],
            "10年": ["2.5%", "2.6%"]
        })
        mock_akshare.bond_china_close_return.return_value = mock_df

        result = adapter.get_bond_yield_curve(bond_type="国债")

        assert len(result) == 2
        mock_akshare.bond_china_close_return.assert_called_once()

    def test_get_bond_yield_curve_error(self, adapter, mock_akshare):
        """测试获取债券收益率曲线API调用失败"""
        mock_akshare.bond_china_close_return.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_bond_yield_curve()
        assert "获取债券收益率曲线失败" in str(exc_info.value)

    def test_get_bond_spot_quote_success(self, adapter, mock_akshare):
        """测试成功获取现券市场做市报价"""
        mock_df = pd.DataFrame({
            "债券代码": ["019547", "019548"],
            "买入价": ["100", "101"]
        })
        mock_akshare.bond_spot_quote.return_value = mock_df

        result = adapter.get_bond_spot_quote()

        assert len(result) == 2
        mock_akshare.bond_spot_quote.assert_called_once()

    def test_get_bond_spot_quote_error(self, adapter, mock_akshare):
        """测试获取现券报价API调用失败"""
        mock_akshare.bond_spot_quote.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_bond_spot_quote()
        assert "获取现券报价失败" in str(exc_info.value)

    def test_get_convertible_bonds_success(self, adapter, mock_akshare):
        """测试成功获取可转债数据一览"""
        mock_df = pd.DataFrame({
            "代码": ["110001", "110002"],
            "名称": ["浦发转债", "兴业转债"]
        })
        mock_akshare.bond_cb_info_jsl.return_value = mock_df

        result = adapter.get_convertible_bonds()

        assert len(result) == 2
        mock_akshare.bond_cb_info_jsl.assert_called_once()

    def test_get_convertible_bonds_error(self, adapter, mock_akshare):
        """测试获取可转债列表API调用失败"""
        mock_akshare.bond_cb_info_jsl.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_convertible_bonds()
        assert "获取可转债列表失败" in str(exc_info.value)

    def test_get_convertible_bond_detail_success(self, adapter, mock_akshare):
        """测试成功获取可转债详情"""
        mock_df = pd.DataFrame({
            "项目": ["转股价", "转股价值"],
            "数值": ["10元", "105元"]
        })
        mock_akshare.bond_cb_detail_jsl.return_value = mock_df

        result = adapter.get_convertible_bond_detail("110001")

        assert len(result) == 2
        mock_akshare.bond_cb_detail_jsl.assert_called_once()

    def test_get_convertible_bond_detail_error(self, adapter, mock_akshare):
        """测试获取可转债详情API调用失败"""
        mock_akshare.bond_cb_detail_jsl.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_convertible_bond_detail("110001")
        assert "获取可转债详情失败" in str(exc_info.value)

    def test_get_bond_spot_success(self, adapter, mock_akshare):
        """测试成功获取沪深债券实时行情"""
        mock_df = pd.DataFrame({
            "代码": ["019547", "019548"],
            "最新价": ["100", "101"]
        })
        mock_akshare.bond_zh_hs_cov_spot.return_value = mock_df

        result = adapter.get_bond_spot("sh019547")

        assert len(result) == 2
        mock_akshare.bond_zh_hs_cov_spot.assert_called_once()

    def test_get_bond_spot_error(self, adapter, mock_akshare):
        """测试获取债券实时行情API调用失败"""
        mock_akshare.bond_zh_hs_cov_spot.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_bond_spot("sh019547")
        assert "获取债券实时行情失败" in str(exc_info.value)

    def test_get_bond_hist_success(self, adapter, mock_akshare):
        """测试成功获取沪深债券历史行情"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "收盘": ["100", "101"]
        })
        mock_akshare.bond_zh_hs_cov_hist.return_value = mock_df

        result = adapter.get_bond_hist("sh019547")

        assert len(result) == 2
        mock_akshare.bond_zh_hs_cov_hist.assert_called_once()

    def test_get_bond_hist_error(self, adapter, mock_akshare):
        """测试获取债券历史行情API调用失败"""
        mock_akshare.bond_zh_hs_cov_hist.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_bond_hist("sh019547")
        assert "获取债券历史数据失败" in str(exc_info.value)

    # =========================================================================
    # 估值指标 (5个)
    # =========================================================================

    def test_get_a_share_valuation_success(self, adapter, mock_akshare):
        """测试成功获取A股等权重与中位数PE/PB"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "等权PE": ["25", "26"],
            "中位数PE": ["30", "31"]
        })
        mock_akshare.stock_a_pe_and_pb.return_value = mock_df

        result = adapter.get_a_share_valuation()

        assert len(result) == 2
        mock_akshare.stock_a_pe_and_pb.assert_called_once()

    def test_get_a_share_valuation_error(self, adapter, mock_akshare):
        """测试获取A股估值API调用失败"""
        mock_akshare.stock_a_pe_and_pb.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_a_share_valuation()
        assert "获取A股估值失败" in str(exc_info.value)

    def test_get_stock_valuation_lg_success(self, adapter, mock_akshare):
        """测试成功获取个股估值-乐咕乐股"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "PE": ["15", "16"],
            "PB": ["2.5", "2.6"]
        })
        mock_akshare.stock_a_indicator_lg.return_value = mock_df

        result = adapter.get_stock_valuation_lg("000001")

        assert len(result) == 2
        mock_akshare.stock_a_indicator_lg.assert_called_once()

    def test_get_stock_valuation_lg_error(self, adapter, mock_akshare):
        """测试获取个股估值API调用失败"""
        mock_akshare.stock_a_indicator_lg.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_stock_valuation_lg("000001")
        assert "获取个股估值失败" in str(exc_info.value)

    def test_get_index_valuation_success(self, adapter, mock_akshare):
        """测试成功获取指数估值-乐咕乐股"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "PE": ["12", "13"]
        })
        mock_akshare.index_value_hist_funddb.return_value = mock_df

        result = adapter.get_index_valuation("000001", indicator="pe")

        assert len(result) == 2
        mock_akshare.index_value_hist_funddb.assert_called_once()

    def test_get_index_valuation_error(self, adapter, mock_akshare):
        """测试获取指数估值API调用失败"""
        mock_akshare.index_value_hist_funddb.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_index_valuation("000001")
        assert "获取指数估值失败" in str(exc_info.value)

    def test_get_market_pe_lg_success(self, adapter, mock_akshare):
        """测试成功获取指数市盈率-乐咕乐股"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "PE": ["12", "13"]
        })
        mock_akshare.stock_market_pe_lg.return_value = mock_df

        result = adapter.get_market_pe_lg("sh")

        assert len(result) == 2
        mock_akshare.stock_market_pe_lg.assert_called_once()

    def test_get_market_pe_lg_error(self, adapter, mock_akshare):
        """测试获取市场PE API调用失败"""
        mock_akshare.stock_market_pe_lg.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_market_pe_lg("sh")
        assert "获取市场PE失败" in str(exc_info.value)

    def test_get_market_pb_lg_success(self, adapter, mock_akshare):
        """测试成功获取指数市净率-乐咕乐股"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "PB": ["1.5", "1.6"]
        })
        mock_akshare.stock_market_pb_lg.return_value = mock_df

        result = adapter.get_market_pb_lg("sh")

        assert len(result) == 2
        mock_akshare.stock_market_pb_lg.assert_called_once()

    def test_get_market_pb_lg_error(self, adapter, mock_akshare):
        """测试获取市场PB API调用失败"""
        mock_akshare.stock_market_pb_lg.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_market_pb_lg("sh")
        assert "获取市场PB失败" in str(exc_info.value)

    # =========================================================================
    # 资金流向 (3个)
    # =========================================================================

    def test_get_market_fund_flow_success(self, adapter, mock_akshare):
        """测试成功获取大盘资金流向"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "净流入": ["100亿", "-50亿"]
        })
        mock_akshare.stock_market_fund_flow.return_value = mock_df

        result = adapter.get_market_fund_flow()

        assert len(result) == 2
        mock_akshare.stock_market_fund_flow.assert_called_once()

    def test_get_market_fund_flow_error(self, adapter, mock_akshare):
        """测试获取大盘资金流向API调用失败"""
        mock_akshare.stock_market_fund_flow.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_market_fund_flow()
        assert "获取大盘资金流向失败" in str(exc_info.value)

    def test_get_stock_fund_flow_success(self, adapter, mock_akshare):
        """测试成功获取个股资金流向"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "净流入": ["1亿", "-5000万"]
        })
        mock_akshare.stock_individual_fund_flow.return_value = mock_df

        result = adapter.get_stock_fund_flow("600519", market="sh")

        assert len(result) == 2
        mock_akshare.stock_individual_fund_flow.assert_called_once()

    def test_get_stock_fund_flow_error(self, adapter, mock_akshare):
        """测试获取个股资金流向API调用失败"""
        mock_akshare.stock_individual_fund_flow.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_stock_fund_flow("600519")
        assert "获取个股资金流向失败" in str(exc_info.value)

    def test_get_north_fund_flow_success(self, adapter, mock_akshare):
        """测试成功获取北向资金流向"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "净流入": ["50亿", "30亿"]
        })
        mock_akshare.stock_hsgt_north_net_flow_in_em.return_value = mock_df

        result = adapter.get_north_fund_flow(market="北向资金")

        assert len(result) == 2
        mock_akshare.stock_hsgt_north_net_flow_in_em.assert_called_once()

    def test_get_north_fund_flow_error(self, adapter, mock_akshare):
        """测试获取北向资金流向API调用失败"""
        mock_akshare.stock_hsgt_north_net_flow_in_em.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_north_fund_flow()
        assert "获取北向资金流向失败" in str(exc_info.value)
