"""
单元测试 - 数据模块
"""

from datetime import date

import pandas as pd
import pytest

from fund_cli.data.cache import DataCache
from fund_cli.data.models import FundFilter, FundInfo, FundType, NavData
from fund_cli.utils.validators import validate_date, validate_fund_code


class TestFundInfo:
    """基金信息模型测试"""

    def test_create_fund_info(self, sample_fund_info):
        """测试创建基金信息"""
        fund = FundInfo(**sample_fund_info)

        assert fund.code == "000001"
        assert fund.name == "华夏成长混合"
        assert fund.type == FundType.MIXED
        assert fund.scale == 50.5

    def test_invalid_fund_code(self):
        """测试无效基金代码"""
        with pytest.raises(ValueError):
            FundInfo(
                code="123",  # 不是6位
                name="测试基金",
                type=FundType.EQUITY,
            )

        with pytest.raises(ValueError):
            FundInfo(
                code="abcdef",  # 不是数字
                name="测试基金",
                type=FundType.EQUITY,
            )

    def test_fund_type_enum(self):
        """测试基金类型枚举"""
        assert FundType.EQUITY.value == "股票型"
        assert FundType.BOND.value == "债券型"
        assert FundType.MIXED.value == "混合型"


class TestNavData:
    """净值数据模型测试"""

    def test_create_nav_data(self):
        """测试创建净值数据"""
        nav = NavData(
            fund_code="000001",
            nav_date=date(2024, 1, 1),
            unit_nav=1.5,
            accumulated_nav=2.0,
        )

        assert nav.fund_code == "000001"
        assert nav.unit_nav == 1.5
        assert nav.accumulated_nav == 2.0

    def test_nav_must_be_positive(self):
        """测试净值必须为正"""
        with pytest.raises(ValueError):
            NavData(
                fund_code="000001",
                nav_date=date(2024, 1, 1),
                unit_nav=-1.0,  # 负值
            )


class TestFundFilter:
    """基金筛选模型测试"""

    def test_create_filter(self):
        """测试创建筛选条件"""
        filter_obj = FundFilter(
            fund_type=FundType.EQUITY,
            min_scale=10.0,
            max_scale=100.0,
            limit=50,
        )

        assert filter_obj.fund_type == FundType.EQUITY
        assert filter_obj.min_scale == 10.0
        assert filter_obj.limit == 50

    def test_default_values(self):
        """测试默认值"""
        filter_obj = FundFilter()

        assert filter_obj.limit == 100
        assert filter_obj.sort_order == "desc"


class TestDataCache:
    """数据缓存测试"""

    def test_cache_set_get(self, temp_cache_dir):
        """测试缓存存取"""
        cache = DataCache(cache_dir=str(temp_cache_dir))

        cache.set("test_key", {"data": "test_value"})
        result = cache.get("test_key")

        assert result == {"data": "test_value"}

    def test_cache_exists(self, temp_cache_dir):
        """测试缓存存在检查"""
        cache = DataCache(cache_dir=str(temp_cache_dir))

        assert not cache.exists("non_existent")

        cache.set("test_key", "value")
        assert cache.exists("test_key")

    def test_cache_delete(self, temp_cache_dir):
        """测试缓存删除"""
        cache = DataCache(cache_dir=str(temp_cache_dir))

        cache.set("test_key", "value")
        assert cache.exists("test_key")

        cache.delete("test_key")
        assert not cache.exists("test_key")

    def test_cache_clear(self, temp_cache_dir):
        """测试清空缓存"""
        cache = DataCache(cache_dir=str(temp_cache_dir))

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert not cache.exists("key1")
        assert not cache.exists("key2")

    def test_cache_dataframe(self, temp_cache_dir, sample_nav_data):
        """测试缓存 DataFrame"""
        cache = DataCache(cache_dir=str(temp_cache_dir))

        cache.set("nav_data", sample_nav_data)
        result = cache.get("nav_data")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_nav_data)


class TestValidators:
    """验证器测试"""

    def test_validate_fund_code(self):
        """测试基金代码验证"""
        assert validate_fund_code("000001") is True
        assert validate_fund_code("123456") is True

        assert validate_fund_code("12345") is False  # 5位
        assert validate_fund_code("1234567") is False  # 7位
        assert validate_fund_code("abcdef") is False  # 非数字
        assert validate_fund_code("") is False  # 空

    def test_validate_date(self):
        """测试日期验证"""
        assert validate_date("2024-01-01") is True
        assert validate_date("2023-12-31") is True

        assert validate_date("2024/01/01") is False  # 错误格式
        assert validate_date("2024-1-1") is False  # 缺少前导零
        assert validate_date("") is False
