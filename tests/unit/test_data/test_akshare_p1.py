"""
AKShare P1接口单元测试

P1 - 分析增强功能接口 (25个)
- 基金公司/规模 (5个)
- 基金评级 (4个)
- 基金分红/拆分 (3个)
- 基金排行 (5个)
- 基金业绩/分析 (3个)
- 基金资产配置 (1个)
- 市场指数扩展 (6个)
"""

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


class TestP1Interface:
    """P1分析增强接口测试类"""

    # =========================================================================
    # 基金公司/规模 (5个)
    # =========================================================================

    def test_get_fund_company_aum_success(self, adapter, mock_akshare):
        """测试成功获取基金公司管理规模排名"""
        mock_df = pd.DataFrame({
            "序号": [1, 2],
            "基金公司": ["易方达基金", "华夏基金"],
            "管理规模": ["15000亿", "12000亿"]
        })
        mock_akshare.fund_aum_em.return_value = mock_df

        result = adapter.get_fund_company_aum()

        assert len(result) == 2
        mock_akshare.fund_aum_em.assert_called_once()

    def test_get_fund_company_aum_error(self, adapter, mock_akshare):
        """测试获取基金公司规模API调用失败"""
        mock_akshare.fund_aum_em.side_effect = Exception("数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_company_aum()
        assert "获取基金公司规模排名失败" in str(exc_info.value)

    def test_get_fund_company_aum_not_found(self, adapter, mock_akshare):
        """测试基金公司规模数据不存在"""
        mock_akshare.fund_aum_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_company_aum()
        assert "基金公司规模数据不存在" in str(exc_info.value)

    def test_get_fund_aum_trend_success(self, adapter, mock_akshare):
        """测试成功获取基金市场管理规模走势"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02", "2024-03"],
            "规模": ["28万亿", "28.5万亿", "29万亿"]
        })
        mock_akshare.fund_aum_trend_em.return_value = mock_df

        result = adapter.get_fund_aum_trend()

        assert len(result) == 3
        mock_akshare.fund_aum_trend_em.assert_called_once()

    def test_get_fund_aum_trend_error(self, adapter, mock_akshare):
        """测试获取基金规模走势API调用失败"""
        mock_akshare.fund_aum_trend_em.side_effect = Exception("趋势数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_aum_trend()
        assert "获取基金规模走势失败" in str(exc_info.value)

    def test_get_fund_aum_trend_not_found(self, adapter, mock_akshare):
        """测试基金规模走势数据不存在"""
        mock_akshare.fund_aum_trend_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_aum_trend()
        assert "基金规模走势数据不存在" in str(exc_info.value)

    def test_get_fund_company_aum_history_success(self, adapter, mock_akshare):
        """测试成功获取基金公司历年管理规模"""
        mock_df = pd.DataFrame({
            "序号": [1, 2],
            "基金公司": ["易方达基金", "华夏基金"],
            "管理规模": ["15000亿", "12000亿"]
        })
        mock_akshare.fund_aum_hist_em.return_value = mock_df

        result = adapter.get_fund_company_aum_history(year=2023)

        assert len(result) == 2
        mock_akshare.fund_aum_hist_em.assert_called_once_with(year=2023)

    def test_get_fund_company_aum_history_error(self, adapter, mock_akshare):
        """测试获取基金公司历史规模API调用失败"""
        mock_akshare.fund_aum_hist_em.side_effect = Exception("历史数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_company_aum_history(year=2023)
        assert "获取基金公司历年规模失败" in str(exc_info.value)

    def test_get_fund_company_aum_history_not_found(self, adapter, mock_akshare):
        """测试基金公司历史规模数据不存在"""
        mock_akshare.fund_aum_hist_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_company_aum_history(year=2023)
        assert "2023年基金公司规模数据不存在" in str(exc_info.value)

    def test_get_fund_scale_change_success(self, adapter, mock_akshare):
        """测试成功获取规模变动(全市场汇总)"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "规模变动": ["500亿", "600亿"]
        })
        mock_akshare.fund_scale_change_em.return_value = mock_df

        result = adapter.get_fund_scale_change()

        assert len(result) == 2
        mock_akshare.fund_scale_change_em.assert_called_once()

    def test_get_fund_scale_change_error(self, adapter, mock_akshare):
        """测试获取规模变动API调用失败"""
        mock_akshare.fund_scale_change_em.side_effect = Exception("变动数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_scale_change()
        assert "获取基金规模变动失败" in str(exc_info.value)

    def test_get_fund_scale_change_not_found(self, adapter, mock_akshare):
        """测试规模变动数据不存在"""
        mock_akshare.fund_scale_change_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_scale_change()
        assert "基金规模变动数据不存在" in str(exc_info.value)

    def test_get_fund_holder_structure_success(self, adapter, mock_akshare):
        """测试成功获取持有人结构(全市场汇总)"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01", "2024-02"],
            "个人持有比例": ["60%", "61%"],
            "机构持有比例": ["40%", "39%"]
        })
        mock_akshare.fund_hold_structure_em.return_value = mock_df

        result = adapter.get_fund_holder_structure()

        assert len(result) == 2
        mock_akshare.fund_hold_structure_em.assert_called_once()

    def test_get_fund_holder_structure_error(self, adapter, mock_akshare):
        """测试获取持有人结构API调用失败"""
        mock_akshare.fund_hold_structure_em.side_effect = Exception("结构数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_holder_structure()
        assert "获取基金持有人结构失败" in str(exc_info.value)

    def test_get_fund_holder_structure_not_found(self, adapter, mock_akshare):
        """测试持有人结构数据不存在"""
        mock_akshare.fund_hold_structure_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_holder_structure()
        assert "基金持有人结构数据不存在" in str(exc_info.value)

    # =========================================================================
    # 基金评级 (4个)
    # =========================================================================

    def test_get_fund_ratings_success(self, adapter, mock_akshare):
        """测试成功获取基金评级总汇"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金简称": ["华夏成长", "华夏大盘"],
            "评级": ["5星", "4星"]
        })
        mock_akshare.fund_rating_all.return_value = mock_df

        result = adapter.get_fund_ratings()

        assert len(result) == 2
        mock_akshare.fund_rating_all.assert_called_once()

    def test_get_fund_ratings_error(self, adapter, mock_akshare):
        """测试获取基金评级API调用失败"""
        mock_akshare.fund_rating_all.side_effect = Exception("评级数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_ratings()
        assert "获取基金评级总汇失败" in str(exc_info.value)

    def test_get_fund_ratings_not_found(self, adapter, mock_akshare):
        """测试基金评级数据不存在"""
        mock_akshare.fund_rating_all.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_ratings()
        assert "基金评级数据不存在" in str(exc_info.value)

    def test_get_fund_rating_sh_success(self, adapter, mock_akshare):
        """测试成功获取上海证券评级"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金简称": ["华夏成长", "华夏大盘"],
            "上海证券评级": ["5星", "4星"]
        })
        mock_akshare.fund_rating_sh.return_value = mock_df

        result = adapter.get_fund_rating_sh(date="20240101")

        assert len(result) == 2
        mock_akshare.fund_rating_sh.assert_called_once_with(date="20240101")

    def test_get_fund_rating_sh_error(self, adapter, mock_akshare):
        """测试获取上海证券评级API调用失败"""
        mock_akshare.fund_rating_sh.side_effect = Exception("评级服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_rating_sh()
        assert "获取上海证券评级失败" in str(exc_info.value)

    def test_get_fund_rating_sh_not_found(self, adapter, mock_akshare):
        """测试上海证券评级数据不存在"""
        mock_akshare.fund_rating_sh.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_rating_sh(date="20240101")
        assert "上海证券评级数据不存在" in str(exc_info.value)

    def test_get_fund_rating_zs_success(self, adapter, mock_akshare):
        """测试成功获取招商证券评级"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金简称": ["华夏成长", "华夏大盘"],
            "招商证券评级": ["5星", "4星"]
        })
        mock_akshare.fund_rating_zs.return_value = mock_df

        result = adapter.get_fund_rating_zs(date="20240101")

        assert len(result) == 2
        mock_akshare.fund_rating_zs.assert_called_once_with(date="20240101")

    def test_get_fund_rating_zs_error(self, adapter, mock_akshare):
        """测试获取招商证券评级API调用失败"""
        mock_akshare.fund_rating_zs.side_effect = Exception("评级服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_rating_zs()
        assert "获取招商证券评级失败" in str(exc_info.value)

    def test_get_fund_rating_zs_not_found(self, adapter, mock_akshare):
        """测试招商证券评级数据不存在"""
        mock_akshare.fund_rating_zs.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_rating_zs(date="20240101")
        assert "招商证券评级数据不存在" in str(exc_info.value)

    def test_get_fund_rating_ja_success(self, adapter, mock_akshare):
        """测试成功获取济安金信评级"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金简称": ["华夏成长", "华夏大盘"],
            "济安金信评级": ["5星", "4星"]
        })
        mock_akshare.fund_rating_ja.return_value = mock_df

        result = adapter.get_fund_rating_ja(date="20240101")

        assert len(result) == 2
        mock_akshare.fund_rating_ja.assert_called_once_with(date="20240101")

    def test_get_fund_rating_ja_error(self, adapter, mock_akshare):
        """测试获取济安金信评级API调用失败"""
        mock_akshare.fund_rating_ja.side_effect = Exception("评级服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_rating_ja()
        assert "获取济安金信评级失败" in str(exc_info.value)

    def test_get_fund_rating_ja_not_found(self, adapter, mock_akshare):
        """测试济安金信评级数据不存在"""
        mock_akshare.fund_rating_ja.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_rating_ja(date="20240101")
        assert "济安金信评级数据不存在" in str(exc_info.value)

    # =========================================================================
    # 基金分红/拆分 (3个)
    # =========================================================================

    def test_get_fund_dividends_success(self, adapter, mock_akshare):
        """测试成功获取基金分红数据"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金简称": ["华夏成长", "华夏大盘"],
            "分红日期": ["2024-01-15", "2024-02-20"],
            "每份分红": ["0.5", "0.3"]
        })
        mock_akshare.fund_fh_em.return_value = mock_df

        result = adapter.get_fund_dividends(year=2024, fund_type="混合型")

        assert len(result) == 2
        mock_akshare.fund_fh_em.assert_called_once()

    def test_get_fund_dividends_error(self, adapter, mock_akshare):
        """测试获取基金分红API调用失败"""
        mock_akshare.fund_fh_em.side_effect = Exception("分红数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_dividends()
        assert "获取基金分红数据失败" in str(exc_info.value)

    def test_get_fund_dividends_not_found(self, adapter, mock_akshare):
        """测试基金分红数据不存在"""
        mock_akshare.fund_fh_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_dividends()
        assert "基金分红数据不存在" in str(exc_info.value)

    def test_get_fund_splits_success(self, adapter, mock_akshare):
        """测试成功获取基金拆分数据"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金简称": ["华夏成长", "华夏大盘"],
            "拆分日期": ["2024-01-15", "2024-02-20"],
            "拆分比例": ["1:10", "1:5"]
        })
        mock_akshare.fund_cf_em.return_value = mock_df

        result = adapter.get_fund_splits(year=2024, fund_type="混合型")

        assert len(result) == 2
        mock_akshare.fund_cf_em.assert_called_once()

    def test_get_fund_splits_error(self, adapter, mock_akshare):
        """测试获取基金拆分API调用失败"""
        mock_akshare.fund_cf_em.side_effect = Exception("拆分数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_splits()
        assert "获取基金拆分数据失败" in str(exc_info.value)

    def test_get_fund_splits_not_found(self, adapter, mock_akshare):
        """测试基金拆分数据不存在"""
        mock_akshare.fund_cf_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_splits()
        assert "基金拆分数据不存在" in str(exc_info.value)

    def test_get_fund_dividend_rank_success(self, adapter, mock_akshare):
        """测试成功获取基金累计分红排行"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金简称": ["华夏成长", "华夏大盘"],
            "累计分红": ["10元", "8元"]
        })
        mock_akshare.fund_fh_rank_em.return_value = mock_df

        result = adapter.get_fund_dividend_rank()

        assert len(result) == 2
        mock_akshare.fund_fh_rank_em.assert_called_once()

    def test_get_fund_dividend_rank_error(self, adapter, mock_akshare):
        """测试获取分红排行API调用失败"""
        mock_akshare.fund_fh_rank_em.side_effect = Exception("排行数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_dividend_rank()
        assert "获取基金累计分红排行失败" in str(exc_info.value)

    def test_get_fund_dividend_rank_not_found(self, adapter, mock_akshare):
        """测试基金累计分红排行数据不存在"""
        mock_akshare.fund_fh_rank_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_dividend_rank()
        assert "基金累计分红排行数据不存在" in str(exc_info.value)

    # =========================================================================
    # 基金排行 (5个)
    # =========================================================================

    def test_get_fund_rank_by_type_success(self, adapter, mock_akshare):
        """测试成功获取开放式基金排行"""
        mock_df = pd.DataFrame({
            "基金代码": ["000001", "000002"],
            "基金简称": ["华夏成长", "华夏大盘"],
            "近1年收益": ["25%", "20%"]
        })
        mock_akshare.fund_open_fund_rank_em.return_value = mock_df

        result = adapter.get_fund_rank_by_type(fund_type="混合型")

        assert len(result) == 2
        mock_akshare.fund_open_fund_rank_em.assert_called_once_with(symbol="混合型")

    def test_get_fund_rank_by_type_error(self, adapter, mock_akshare):
        """测试获取基金排行API调用失败"""
        mock_akshare.fund_open_fund_rank_em.side_effect = Exception("排行数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_rank_by_type()
        assert "获取基金排行失败" in str(exc_info.value)

    def test_get_fund_rank_by_type_not_found(self, adapter, mock_akshare):
        """测试基金排行数据不存在"""
        mock_akshare.fund_open_fund_rank_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_rank_by_type(fund_type="混合型")
        assert "混合型类型基金排行数据不存在" in str(exc_info.value)

    def test_get_exchange_fund_rank_success(self, adapter, mock_akshare):
        """测试成功获取场内交易基金排行"""
        mock_df = pd.DataFrame({
            "基金代码": ["510050", "510300"],
            "基金简称": ["华夏上证50ETF", "华泰柏瑞沪深300ETF"],
            "近1年收益": ["15%", "12%"]
        })
        mock_akshare.fund_exchange_rank_em.return_value = mock_df

        result = adapter.get_exchange_fund_rank()

        assert len(result) == 2
        mock_akshare.fund_exchange_rank_em.assert_called_once()

    def test_get_exchange_fund_rank_error(self, adapter, mock_akshare):
        """测试获取场内基金排行API调用失败"""
        mock_akshare.fund_exchange_rank_em.side_effect = Exception("排行数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_exchange_fund_rank()
        assert "获取场内基金排行失败" in str(exc_info.value)

    def test_get_exchange_fund_rank_not_found(self, adapter, mock_akshare):
        """测试场内基金排行数据不存在"""
        mock_akshare.fund_exchange_rank_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_exchange_fund_rank()
        assert "场内交易基金排行数据不存在" in str(exc_info.value)

    def test_get_money_fund_rank_success(self, adapter, mock_akshare):
        """测试成功获取货币型基金排行"""
        mock_df = pd.DataFrame({
            "基金代码": ["000003", "000004"],
            "基金简称": ["华夏现金", "易方达货币"],
            "7日年化": ["2.5%", "2.3%"]
        })
        mock_akshare.fund_money_rank_em.return_value = mock_df

        result = adapter.get_money_fund_rank()

        assert len(result) == 2
        mock_akshare.fund_money_rank_em.assert_called_once()

    def test_get_money_fund_rank_error(self, adapter, mock_akshare):
        """测试获取货币基金排行API调用失败"""
        mock_akshare.fund_money_rank_em.side_effect = Exception("排行数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_money_fund_rank()
        assert "获取货币基金排行失败" in str(exc_info.value)

    def test_get_money_fund_rank_not_found(self, adapter, mock_akshare):
        """测试货币基金排行数据不存在"""
        mock_akshare.fund_money_rank_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_money_fund_rank()
        assert "货币型基金排行数据不存在" in str(exc_info.value)

    def test_get_lcx_fund_rank_success(self, adapter, mock_akshare):
        """测试成功获取理财基金排行"""
        mock_df = pd.DataFrame({
            "基金代码": ["000005", "000006"],
            "基金简称": ["理财基金A", "理财基金B"],
            "7日年化": ["3.0%", "2.8%"]
        })
        mock_akshare.fund_lcx_rank_em.return_value = mock_df

        result = adapter.get_lcx_fund_rank()

        assert len(result) == 2
        mock_akshare.fund_lcx_rank_em.assert_called_once()

    def test_get_lcx_fund_rank_error(self, adapter, mock_akshare):
        """测试获取理财基金排行API调用失败"""
        mock_akshare.fund_lcx_rank_em.side_effect = Exception("排行数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_lcx_fund_rank()
        assert "获取理财基金排行失败" in str(exc_info.value)

    def test_get_lcx_fund_rank_not_found(self, adapter, mock_akshare):
        """测试理财基金排行数据不存在"""
        mock_akshare.fund_lcx_rank_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_lcx_fund_rank()
        assert "理财基金排行数据不存在" in str(exc_info.value)

    def test_get_hk_fund_rank_success(self, adapter, mock_akshare):
        """测试成功获取香港基金排行"""
        mock_df = pd.DataFrame({
            "基金代码": ["HK0001", "HK0002"],
            "基金简称": ["香港基金A", "香港基金B"],
            "近1年收益": ["10%", "8%"]
        })
        mock_akshare.fund_hk_rank_em.return_value = mock_df

        result = adapter.get_hk_fund_rank()

        assert len(result) == 2
        mock_akshare.fund_hk_rank_em.assert_called_once()

    def test_get_hk_fund_rank_error(self, adapter, mock_akshare):
        """测试获取香港基金排行API调用失败"""
        mock_akshare.fund_hk_rank_em.side_effect = Exception("排行数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_hk_fund_rank()
        assert "获取香港基金排行失败" in str(exc_info.value)

    def test_get_hk_fund_rank_not_found(self, adapter, mock_akshare):
        """测试香港基金排行数据不存在"""
        mock_akshare.fund_hk_rank_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_hk_fund_rank()
        assert "香港基金排行数据不存在" in str(exc_info.value)

    # =========================================================================
    # 基金业绩/分析 (3个)
    # =========================================================================

    def test_get_fund_achievement_success(self, adapter, mock_akshare):
        """测试成功获取基金业绩(年度+阶段)"""
        mock_df = pd.DataFrame({
            "年度": ["2023", "2022"],
            "收益率": ["25%", "-10%"]
        })
        mock_akshare.fund_individual_achievement_xq.return_value = mock_df

        result = adapter.get_fund_achievement("000001")

        assert len(result) == 2
        mock_akshare.fund_individual_achievement_xq.assert_called_once_with(symbol="000001")

    def test_get_fund_achievement_error(self, adapter, mock_akshare):
        """测试获取基金业绩API调用失败"""
        mock_akshare.fund_individual_achievement_xq.side_effect = Exception("业绩数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_achievement("000001")
        assert "获取基金业绩失败" in str(exc_info.value)

    def test_get_fund_achievement_not_found(self, adapter, mock_akshare):
        """测试基金业绩数据不存在"""
        mock_akshare.fund_individual_achievement_xq.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_achievement("999999")
        assert "基金 999999 业绩数据不存在" in str(exc_info.value)

    def test_get_fund_risk_analysis_success(self, adapter, mock_akshare):
        """测试成功获取基金数据分析(夏普/回撤)"""
        mock_df = pd.DataFrame({
            "指标": ["夏普比率", "最大回撤"],
            "数值": ["1.5", "-20%"]
        })
        mock_akshare.fund_individual_analysis_xq.return_value = mock_df

        result = adapter.get_fund_risk_analysis("000001")

        assert len(result) == 2
        mock_akshare.fund_individual_analysis_xq.assert_called_once_with(symbol="000001")

    def test_get_fund_risk_analysis_error(self, adapter, mock_akshare):
        """测试获取基金风险分析API调用失败"""
        mock_akshare.fund_individual_analysis_xq.side_effect = Exception("风险数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_risk_analysis("000001")
        assert "获取基金风险分析失败" in str(exc_info.value)

    def test_get_fund_risk_analysis_not_found(self, adapter, mock_akshare):
        """测试基金风险分析数据不存在"""
        mock_akshare.fund_individual_analysis_xq.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_risk_analysis("999999")
        assert "基金 999999 风险分析数据不存在" in str(exc_info.value)

    def test_get_fund_profit_probability_success(self, adapter, mock_akshare):
        """测试成功获取基金盈利概率"""
        mock_df = pd.DataFrame({
            "持有期": ["1年", "3年", "5年"],
            "盈利概率": ["70%", "85%", "95%"]
        })
        mock_akshare.fund_individual_profit_probability_xq.return_value = mock_df

        result = adapter.get_fund_profit_probability("000001")

        assert len(result) == 3
        mock_akshare.fund_individual_profit_probability_xq.assert_called_once_with(symbol="000001")

    def test_get_fund_profit_probability_error(self, adapter, mock_akshare):
        """测试获取基金盈利概率API调用失败"""
        mock_akshare.fund_individual_profit_probability_xq.side_effect = Exception("概率数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_profit_probability("000001")
        assert "获取基金盈利概率失败" in str(exc_info.value)

    def test_get_fund_profit_probability_not_found(self, adapter, mock_akshare):
        """测试基金盈利概率数据不存在"""
        mock_akshare.fund_individual_profit_probability_xq.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_profit_probability("999999")
        assert "基金 999999 盈利概率数据不存在" in str(exc_info.value)

    # =========================================================================
    # 基金资产配置 (1个)
    # =========================================================================

    def test_get_fund_asset_allocation_success(self, adapter, mock_akshare):
        """测试成功获取基金资产配置"""
        mock_df = pd.DataFrame({
            "资产类别": ["股票", "债券", "现金"],
            "占比": ["60%", "30%", "10%"]
        })
        mock_akshare.fund_individual_detail_hold_xq.return_value = mock_df

        result = adapter.get_fund_asset_allocation("000001")

        assert len(result) == 3
        mock_akshare.fund_individual_detail_hold_xq.assert_called_once()

    def test_get_fund_asset_allocation_error(self, adapter, mock_akshare):
        """测试获取基金资产配置API调用失败"""
        mock_akshare.fund_individual_detail_hold_xq.side_effect = Exception("配置数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_fund_asset_allocation("000001")
        assert "获取基金资产配置失败" in str(exc_info.value)

    def test_get_fund_asset_allocation_not_found(self, adapter, mock_akshare):
        """测试基金资产配置数据不存在"""
        mock_akshare.fund_individual_detail_hold_xq.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_fund_asset_allocation("999999")
        assert "基金 999999 资产配置数据不存在" in str(exc_info.value)

    # =========================================================================
    # 市场指数扩展 (6个)
    # =========================================================================

    def test_get_index_spot_em_success(self, adapter, mock_akshare):
        """测试成功获取东财指数实时行情"""
        mock_df = pd.DataFrame({
            "代码": ["000001", "000002"],
            "名称": ["上证指数", "深证成指"],
            "最新价": ["3000", "10000"]
        })
        mock_akshare.stock_zh_index_spot_em.return_value = mock_df

        result = adapter.get_index_spot_em(category="沪深重要指数")

        assert len(result) == 2
        mock_akshare.stock_zh_index_spot_em.assert_called_once_with(symbol="沪深重要指数")

    def test_get_index_spot_em_error(self, adapter, mock_akshare):
        """测试获取东财指数行情API调用失败"""
        mock_akshare.stock_zh_index_spot_em.side_effect = Exception("行情服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_index_spot_em()
        assert "获取东财指数实时行情失败" in str(exc_info.value)

    def test_get_index_spot_em_not_found(self, adapter, mock_akshare):
        """测试东财指数行情数据不存在"""
        mock_akshare.stock_zh_index_spot_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_index_spot_em(category="沪深重要指数")
        assert "沪深重要指数指数实时行情数据不存在" in str(exc_info.value)

    def test_get_index_spot_sina_success(self, adapter, mock_akshare):
        """测试成功获取新浪指数实时行情"""
        mock_df = pd.DataFrame({
            "代码": ["sh000001", "sz399001"],
            "名称": ["上证指数", "深证成指"],
            "最新价": ["3000", "10000"]
        })
        mock_akshare.stock_zh_index_spot_sina.return_value = mock_df

        result = adapter.get_index_spot_sina()

        assert len(result) == 2
        mock_akshare.stock_zh_index_spot_sina.assert_called_once()

    def test_get_index_spot_sina_error(self, adapter, mock_akshare):
        """测试获取新浪指数行情API调用失败"""
        mock_akshare.stock_zh_index_spot_sina.side_effect = Exception("行情服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_index_spot_sina()
        assert "获取新浪指数实时行情失败" in str(exc_info.value)

    def test_get_index_spot_sina_not_found(self, adapter, mock_akshare):
        """测试新浪指数行情数据不存在"""
        mock_akshare.stock_zh_index_spot_sina.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_index_spot_sina()
        assert "新浪指数实时行情数据不存在" in str(exc_info.value)

    def test_get_index_daily_tx_success(self, adapter, mock_akshare):
        """测试成功获取腾讯指数历史"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "开盘": ["2990", "3000"],
            "收盘": ["3000", "3010"]
        })
        mock_akshare.stock_zh_index_daily_tx.return_value = mock_df

        result = adapter.get_index_daily_tx("sh000001")

        assert len(result) == 2
        mock_akshare.stock_zh_index_daily_tx.assert_called_once()

    def test_get_index_daily_tx_error(self, adapter, mock_akshare):
        """测试获取腾讯指数历史API调用失败"""
        mock_akshare.stock_zh_index_daily_tx.side_effect = Exception("历史数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_index_daily_tx("sh000001")
        assert "获取腾讯指数历史失败" in str(exc_info.value)

    def test_get_index_daily_tx_not_found(self, adapter, mock_akshare):
        """测试腾讯指数历史数据不存在"""
        mock_akshare.stock_zh_index_daily_tx.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_index_daily_tx("sh999999")
        assert "指数 sh999999 历史数据不存在" in str(exc_info.value)

    def test_get_index_daily_em_success(self, adapter, mock_akshare):
        """测试成功获取东财指数历史"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "开盘": ["2990", "3000"],
            "收盘": ["3000", "3010"]
        })
        mock_akshare.stock_zh_index_daily_em.return_value = mock_df

        result = adapter.get_index_daily_em("sz399001")

        assert len(result) == 2
        mock_akshare.stock_zh_index_daily_em.assert_called_once()

    def test_get_index_daily_em_error(self, adapter, mock_akshare):
        """测试获取东财指数历史API调用失败"""
        mock_akshare.stock_zh_index_daily_em.side_effect = Exception("历史数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_index_daily_em("sz399001")
        assert "获取东财指数历史失败" in str(exc_info.value)

    def test_get_index_daily_em_not_found(self, adapter, mock_akshare):
        """测试东财指数历史数据不存在"""
        mock_akshare.stock_zh_index_daily_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_index_daily_em("sz999999")
        assert "指数 sz999999 历史数据不存在" in str(exc_info.value)

    def test_get_index_hist_success(self, adapter, mock_akshare):
        """测试成功获取指数通用历史"""
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01", "2024-01-02"],
            "开盘": ["2990", "3000"],
            "收盘": ["3000", "3010"]
        })
        mock_akshare.index_zh_a_hist.return_value = mock_df

        result = adapter.get_index_hist("000001", period="daily")

        assert len(result) == 2
        mock_akshare.index_zh_a_hist.assert_called_once()

    def test_get_index_hist_error(self, adapter, mock_akshare):
        """测试获取指数通用历史API调用失败"""
        mock_akshare.index_zh_a_hist.side_effect = Exception("历史数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_index_hist("000001")
        assert "获取指数通用历史失败" in str(exc_info.value)

    def test_get_index_hist_not_found(self, adapter, mock_akshare):
        """测试指数通用历史数据不存在"""
        mock_akshare.index_zh_a_hist.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_index_hist("999999")
        assert "指数 999999 历史数据不存在" in str(exc_info.value)

    def test_get_index_minute_success(self, adapter, mock_akshare):
        """测试成功获取指数分时"""
        mock_df = pd.DataFrame({
            "时间": ["09:30", "09:31"],
            "开盘": ["3000", "3001"],
            "收盘": ["3001", "3002"]
        })
        mock_akshare.index_zh_a_hist_min_em.return_value = mock_df

        result = adapter.get_index_minute("000001", period="1")

        assert len(result) == 2
        mock_akshare.index_zh_a_hist_min_em.assert_called_once()

    def test_get_index_minute_error(self, adapter, mock_akshare):
        """测试获取指数分时API调用失败"""
        mock_akshare.index_zh_a_hist_min_em.side_effect = Exception("分时数据服务异常")

        with pytest.raises(DataSourceError) as exc_info:
            adapter.get_index_minute("000001")
        assert "获取指数分时数据失败" in str(exc_info.value)

    def test_get_index_minute_not_found(self, adapter, mock_akshare):
        """测试指数分时数据不存在"""
        mock_akshare.index_zh_a_hist_min_em.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError) as exc_info:
            adapter.get_index_minute("999999")
        assert "指数 999999 分时数据不存在" in str(exc_info.value)
