"""
AKShare 适配器补充测试

测试覆盖：
- 初始化
- 静态方法
- 错误处理分支
- 基本功能
"""

from datetime import date
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
def adapter_with_cache(mock_cache):
    """创建带缓存的适配器"""
    return AKShareAdapter(cache=mock_cache)


@pytest.fixture
def adapter_no_cache():
    """创建不带缓存的适配器"""
    return AKShareAdapter(cache=None)


class TestAKShareAdapterInit:
    """测试适配器初始化"""

    def test_init_with_cache(self, mock_cache):
        """测试带缓存初始化"""
        adapter = AKShareAdapter(cache=mock_cache)
        assert adapter._cache is mock_cache
        assert adapter._name == "akshare"
        assert adapter._ak is None

    def test_init_without_cache(self):
        """测试不带缓存初始化"""
        adapter = AKShareAdapter(cache=None)
        assert adapter._cache is None
        assert adapter._name == "akshare"

    def test_name_property(self, adapter_no_cache):
        """测试 name 属性"""
        assert adapter_no_cache.name == "akshare"


class TestGetAKShare:
    """测试 _get_akshare 延迟加载"""

    def test_get_akshare_lazy_load(self, adapter_no_cache):
        """测试延迟加载 AKShare"""
        mock_ak = MagicMock()
        with patch.dict("sys.modules", {"akshare": mock_ak}):
            result = adapter_no_cache._get_akshare()
            assert result is mock_ak

    def test_get_akshare_caches_result(self, adapter_no_cache):
        """测试缓存加载结果"""
        mock_ak = MagicMock()
        with patch.dict("sys.modules", {"akshare": mock_ak}):
            adapter_no_cache._get_akshare()
            adapter_no_cache._get_akshare()
            # 只加载一次

    def test_get_akshare_import_error(self, adapter_no_cache):
        """测试 AKShare 未安装"""
        with patch.dict("sys.modules", {"akshare": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                with pytest.raises(DataSourceError, match="AKShare 未安装"):
                    adapter_no_cache._get_akshare()


class TestIsAvailable:
    """测试 is_available 方法"""

    def test_is_available_true(self, adapter_no_cache):
        """测试 AKShare 可用"""
        mock_ak = MagicMock()
        with patch.object(adapter_no_cache, "_get_akshare", return_value=mock_ak):
            assert adapter_no_cache.is_available() is True

    def test_is_available_false(self, adapter_no_cache):
        """测试 AKShare 不可用"""
        with patch.object(adapter_no_cache, "_get_akshare", side_effect=Exception("error")):
            assert adapter_no_cache.is_available() is False


class TestCacheMechanism:
    """测试缓存机制"""

    def test_get_fund_info_with_cache_hit(self, adapter_with_cache, mock_cache):
        """测试基金信息缓存命中"""
        cached_info = {"code": "000001", "name": "测试基金"}
        mock_cache.get_fund_info.return_value = cached_info

        result = adapter_with_cache.get_fund_info("000001")

        assert result == cached_info
        mock_cache.get_fund_info.assert_called_once_with("000001")

    def test_get_fund_info_with_cache_miss(self, adapter_with_cache, mock_cache):
        """测试基金信息缓存未命中"""
        mock_cache.get_fund_info.return_value = None
        mock_ak = MagicMock()
        mock_df = pd.DataFrame({
            "item": ["基金简称", "基金类型", "成立日期", "基金经理", "基金管理人", "基金规模"],
            "value": ["华夏成长混合", "混合型", "2001-12-18", "张三", "华夏基金", "50.5亿元"]
        })
        mock_ak.fund_individual_basic_info_xq.return_value = mock_df

        with patch.object(adapter_with_cache, "_get_akshare", return_value=mock_ak):
            result = adapter_with_cache.get_fund_info("000001")

            assert result["code"] == "000001"
            mock_cache.set_fund_info.assert_called_once()

    def test_cache_exists_check(self, adapter_with_cache, mock_cache):
        """测试缓存存在检查"""
        mock_cache.exists.return_value = True
        mock_cache.get.return_value = pd.DataFrame({"test": [1]})

        adapter_with_cache.get_all_fund_names()

        mock_cache.exists.assert_called_once()
        mock_cache.get.assert_called_once()


class TestFundList:
    """测试基金列表功能"""

    def test_get_fund_list_calls_search_funds(self, adapter_no_cache):
        """测试 get_fund_list 调用 search_funds"""
        with patch.object(adapter_no_cache, "search_funds") as mock_search:
            mock_search.return_value = pd.DataFrame()
            adapter_no_cache.get_fund_list("股票型")
            mock_search.assert_called_once_with(fund_type="股票型")


class TestFundManager:
    """测试基金经理功能"""

    def test_get_fund_manager_success(self, adapter_no_cache):
        """测试成功获取基金经理"""
        with patch.object(adapter_no_cache, "get_fund_info") as mock_info:
            mock_info.return_value = {
                "manager": "张三",
                "name": "华夏成长",
                "company": "华夏基金",
            }

            result = adapter_no_cache.get_fund_manager("000001")

            assert result["name"] == "张三"
            assert result["fund_code"] == "000001"


class TestFundFee:
    """测试基金费率功能"""

    def test_get_fund_fee_success(self, adapter_no_cache):
        """测试成功获取费率"""
        mock_ak = MagicMock()
        mock_df = pd.DataFrame({
            "item": ["管理费率", "托管费率", "申购费率", "赎回费率"],
            "value": ["1.5%", "0.25%", "1.2%", "0.5%"],
        })
        mock_ak.fund_individual_detail_info_xq.return_value = mock_df

        with patch.object(adapter_no_cache, "_get_akshare", return_value=mock_ak):
            result = adapter_no_cache.get_fund_fee("000001")

            assert "management_fee" in result
            assert "custody_fee" in result

    def test_get_fund_fee_not_found(self, adapter_no_cache):
        """测试费率信息不存在"""
        mock_ak = MagicMock()
        mock_ak.fund_individual_detail_info_xq.return_value = pd.DataFrame()

        with patch.object(adapter_no_cache, "_get_akshare", return_value=mock_ak):
            with pytest.raises(DataNotFoundError, match="费率信息不存在"):
                adapter_no_cache.get_fund_fee("999999")

    def test_get_fund_fee_error(self, adapter_no_cache):
        """测试获取费率失败"""
        mock_ak = MagicMock()
        mock_ak.fund_individual_detail_info_xq.side_effect = Exception("API Error")

        with patch.object(adapter_no_cache, "_get_akshare", return_value=mock_ak):
            with pytest.raises(DataSourceError, match="获取费率信息失败"):
                adapter_no_cache.get_fund_fee("000001")


class TestFundRating:
    """测试基金评级功能"""

    def test_get_fund_rating_success(self, adapter_no_cache):
        """测试成功获取评级"""
        mock_ak = MagicMock()
        mock_df = pd.DataFrame({
            "item": ["基金评级"],
            "value": ["5星"],
        })
        mock_ak.fund_individual_detail_info_xq.return_value = mock_df

        with patch.object(adapter_no_cache, "_get_akshare", return_value=mock_ak):
            result = adapter_no_cache.get_fund_rating("000001")

            assert result == 5

    def test_get_fund_rating_no_rating(self, adapter_no_cache):
        """测试无评级"""
        mock_ak = MagicMock()
        mock_df = pd.DataFrame({
            "item": ["其他"],
            "value": ["其他值"],
        })
        mock_ak.fund_individual_detail_info_xq.return_value = mock_df

        with patch.object(adapter_no_cache, "_get_akshare", return_value=mock_ak):
            result = adapter_no_cache.get_fund_rating("000001")

            assert result is None

    def test_get_fund_rating_empty_df(self, adapter_no_cache):
        """测试空数据"""
        mock_ak = MagicMock()
        mock_ak.fund_individual_detail_info_xq.return_value = pd.DataFrame()

        with patch.object(adapter_no_cache, "_get_akshare", return_value=mock_ak):
            result = adapter_no_cache.get_fund_rating("000001")

            assert result is None

    def test_get_fund_rating_exception(self, adapter_no_cache):
        """测试异常情况"""
        mock_ak = MagicMock()
        mock_ak.fund_individual_detail_info_xq.side_effect = Exception("Error")

        with patch.object(adapter_no_cache, "_get_akshare", return_value=mock_ak):
            result = adapter_no_cache.get_fund_rating("000001")

            assert result is None


class TestBatchGetFundNav:
    """测试批量获取净值"""

    def test_batch_get_fund_nav_success(self, adapter_no_cache):
        """测试批量获取成功"""
        with patch.object(adapter_no_cache, "get_fund_nav") as mock_nav:
            mock_nav.return_value = pd.DataFrame({"unit_nav": [1.5]})

            result = adapter_no_cache.batch_get_fund_nav(["000001", "000002"])

            assert "000001" in result
            assert "000002" in result
            assert mock_nav.call_count == 2

    def test_batch_get_fund_nav_with_error(self, adapter_no_cache):
        """测试批量获取部分失败"""
        with patch.object(adapter_no_cache, "get_fund_nav") as mock_nav:
            mock_nav.side_effect = [
                pd.DataFrame({"unit_nav": [1.5]}),
                Exception("Error"),
            ]

            result = adapter_no_cache.batch_get_fund_nav(["000001", "000002"])

            assert len(result["000001"]) == 1
            assert result["000002"].empty


class TestStaticMethods:
    """测试静态方法"""

    def test_parse_date_valid(self):
        """测试有效日期解析"""
        result = AKShareAdapter._parse_date("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_parse_date_invalid(self):
        """测试无效日期解析"""
        result = AKShareAdapter._parse_date("invalid")
        assert result is None

    def test_parse_date_none(self):
        """测试空日期解析"""
        result = AKShareAdapter._parse_date(None)
        assert result is None

    def test_parse_date_empty_string(self):
        """测试空字符串日期解析"""
        result = AKShareAdapter._parse_date("")
        assert result is None

    def test_parse_scale_valid(self):
        """测试有效规模解析"""
        result = AKShareAdapter._parse_scale("50.5亿元")
        assert result == 50.5

    def test_parse_scale_with_unit(self):
        """测试带单位规模解析"""
        result = AKShareAdapter._parse_scale("100.0亿份")
        assert result == 100.0

    def test_parse_scale_invalid(self):
        """测试无效规模解析"""
        result = AKShareAdapter._parse_scale("invalid")
        assert result is None

    def test_parse_scale_none(self):
        """测试空规模解析"""
        result = AKShareAdapter._parse_scale(None)
        assert result is None

    def test_parse_scale_numeric(self):
        """测试纯数字规模解析"""
        result = AKShareAdapter._parse_scale("50.5")
        assert result == 50.5


class TestStandardizeColumns:
    """测试列名标准化"""

    def test_standardize_columns_basic(self, adapter_no_cache):
        """测试基本列名标准化"""
        df = pd.DataFrame({
            "日期": ["2024-01-01"],
            "股票代码": ["600519"],
            "收盘价": [1800.0],
        })

        result = adapter_no_cache._standardize_columns(df)

        assert "date" in result.columns
        assert "code" in result.columns
        assert "close" in result.columns

    def test_standardize_columns_no_change(self, adapter_no_cache):
        """测试无需标准化的列名"""
        df = pd.DataFrame({
            "existing_column": [1, 2, 3],
        })

        result = adapter_no_cache._standardize_columns(df)

        assert "existing_column" in result.columns

    def test_standardize_columns_partial(self, adapter_no_cache):
        """测试部分列名标准化"""
        df = pd.DataFrame({
            "日期": ["2024-01-01"],
            "custom_column": [100],
        })

        result = adapter_no_cache._standardize_columns(df)

        assert "date" in result.columns
        assert "custom_column" in result.columns


class TestRepr:
    """测试 __repr__ 方法"""

    def test_repr(self, adapter_no_cache):
        """测试字符串表示"""
        result = repr(adapter_no_cache)
        assert "AKShareAdapter" in result
        assert "akshare" in result


class TestEdgeCases:
    """测试边界条件"""

    def test_get_fund_info_with_missing_fields(self, adapter_no_cache):
        """测试缺少字段的基金信息"""
        mock_ak = MagicMock()
        mock_df = pd.DataFrame({
            "item": ["基金简称"],
            "value": ["测试基金"],
        })
        mock_ak.fund_individual_basic_info_xq.return_value = mock_df

        with patch.object(adapter_no_cache, "_get_akshare", return_value=mock_ak):
            result = adapter_no_cache.get_fund_info("000001")

            assert result["code"] == "000001"
            assert result["name"] == "测试基金"

    def test_search_funds_empty_result(self, adapter_no_cache):
        """测试搜索无结果"""
        mock_ak = MagicMock()
        # 返回空 DataFrame，但带有正确的列类型
        mock_ak.fund_open_fund_daily_em.return_value = pd.DataFrame(columns=["基金代码", "基金简称", "基金类型", "基金规模", "基金公司"])

        with patch.object(adapter_no_cache, "_get_akshare", return_value=mock_ak):
            result = adapter_no_cache.search_funds()

            assert len(result) == 0
