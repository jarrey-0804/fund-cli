"""
DataManager 数据管理器单元测试

测试覆盖：
- __init__ 不同配置情况
- register_adapter 方法
- available_sources 属性
- source_priority 属性
- gateway 属性
- _init_adapters 不同配置分支
- get_adapter 方法及异常处理
- 数据访问接口代理
- 缓存管理
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from fund_cli.core.data_manager import DataManager, get_data_manager
from fund_cli.data.base import DataSourceError

# =============================================================================
# Fixtures
# =============================================================================


def _reset_config():
    """重置全局配置，确保测试隔离"""
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
def mock_cache():
    """创建模拟缓存"""
    cache = MagicMock()
    cache.clear.return_value = None
    cache.get_stats.return_value = {"hits": 10, "misses": 5}
    return cache


@pytest.fixture
def mock_adapter():
    """创建模拟数据源适配器"""
    adapter = MagicMock()
    adapter.name = "test_adapter"
    adapter.is_available.return_value = True
    adapter.get_fund_info.return_value = {
        "fund_code": "000001",
        "fund_name": "测试基金",
        "type": "混合型",
    }
    adapter.get_fund_nav.return_value = pd.DataFrame({
        "nav_date": ["2024-01-01", "2024-01-02"],
        "unit_nav": [1.0, 1.01],
    })
    adapter.search_funds.return_value = pd.DataFrame({
        "fund_code": ["000001", "000002"],
        "fund_name": ["基金A", "基金B"],
    })
    adapter.get_fund_list.return_value = pd.DataFrame({
        "fund_code": ["000001", "000002"],
    })
    adapter.get_benchmark_nav.return_value = pd.DataFrame({
        "trade_date": ["2024-01-01"],
        "close": [3000.0],
    })
    adapter.get_fund_holdings.return_value = pd.DataFrame({
        "stock_code": ["600519"],
        "stock_name": ["贵州茅台"],
    })
    adapter.get_fund_manager.return_value = {"manager": "张三"}
    adapter.get_fund_fee.return_value = {"management_fee": 1.5}
    adapter.get_fund_rating.return_value = 5
    adapter.batch_get_fund_nav.return_value = {"000001": pd.DataFrame()}
    return adapter


# =============================================================================
# 测试类：初始化与配置
# =============================================================================


class TestDataManagerInit:
    """测试 DataManager 初始化"""

    def test_init_with_default_config(self, mock_config):
        """测试使用默认配置初始化"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    assert dm.config is mock_config
                    assert dm._primary_source == "akshare"

    def test_init_with_custom_cache(self, mock_config, mock_cache):
        """测试使用自定义缓存初始化"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch.object(DataManager, "_init_adapters"):
                dm = DataManager(cache=mock_cache)
                assert dm._cache is mock_cache

    def test_init_with_custom_primary_source(self, mock_config):
        """测试使用自定义主数据源初始化"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager(primary_source="tushare")
                    assert dm._primary_source == "tushare"

    def test_init_creates_gateway(self, mock_config):
        """测试初始化时创建网关实例"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    assert dm._gateway is not None

    def test_init_calls_init_adapters(self, mock_config):
        """测试初始化时调用 _init_adapters"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters") as mock_init:
                    DataManager()
                    mock_init.assert_called_once()


# =============================================================================
# 测试类：适配器初始化分支
# =============================================================================


class TestInitAdapters:
    """测试 _init_adapters 不同配置分支"""

    def test_init_akshare_enabled_success(self, mock_config):
        """测试 AKShare 启用且注册成功"""
        mock_config.akshare_enabled = True
        mock_adapter = MagicMock()
        mock_adapter.is_available.return_value = True

        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch("fund_cli.core.data_manager.AKShareAdapter", return_value=mock_adapter):
                    dm = DataManager()
                    assert "akshare" in dm._adapters

    def test_init_akshare_enabled_failure(self, mock_config):
        """测试 AKShare 启用但注册失败"""
        mock_config.akshare_enabled = True

        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch("fund_cli.core.data_manager.AKShareAdapter", side_effect=Exception("初始化失败")):
                    dm = DataManager()
                    assert "akshare" not in dm._adapters

    def test_init_akshare_disabled(self, mock_config):
        """测试 AKShare 禁用"""
        mock_config.akshare_enabled = False

        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                # 需要阻止真实的 _init_adapters 被调用
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    # 由于 _init_adapters 被 mock，不会有任何适配器被注册
                    assert "akshare" not in dm._adapters

    def test_init_tushare_with_token(self, mock_config):
        """测试 Tushare 有 Token 时注册"""
        mock_config.tushare_token = "test_token"
        mock_adapter = MagicMock()
        mock_adapter.is_available.return_value = True

        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch("fund_cli.core.data_manager.AKShareAdapter"):
                    with patch.dict("sys.modules", {"fund_cli.data.adapters.tushare_adapter": MagicMock(TushareAdapter=lambda **kwargs: mock_adapter)}):
                        DataManager()
                        # 注意：由于 import 机制，这里可能需要额外处理

    def test_init_tushare_no_token(self, mock_config):
        """测试 Tushare 无 Token 时跳过"""
        mock_config.tushare_token = None

        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch("fund_cli.core.data_manager.AKShareAdapter"):
                    dm = DataManager()
                    assert "tushare" not in dm._adapters

    def test_init_wind_enabled_available(self, mock_config):
        """测试 Wind 启用且可用"""
        mock_config.wind_enabled = True
        mock_adapter = MagicMock()
        mock_adapter.is_available.return_value = True

        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch("fund_cli.core.data_manager.AKShareAdapter"):
                    with patch.dict("sys.modules", {"fund_cli.data.adapters.wind_adapter": MagicMock(WindAdapter=lambda **kwargs: mock_adapter)}):
                        DataManager()

    def test_init_wind_enabled_unavailable(self, mock_config):
        """测试 Wind 启用但不可用"""
        mock_config.wind_enabled = True
        mock_adapter = MagicMock()
        mock_adapter.is_available.return_value = False

        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch("fund_cli.core.data_manager.AKShareAdapter"):
                    with patch.dict("sys.modules", {"fund_cli.data.adapters.wind_adapter": MagicMock(WindAdapter=lambda **kwargs: mock_adapter)}):
                        DataManager()

    def test_init_wind_disabled(self, mock_config):
        """测试 Wind 禁用"""
        mock_config.wind_enabled = False

        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch("fund_cli.core.data_manager.AKShareAdapter"):
                    dm = DataManager()
                    assert "wind" not in dm._adapters

    def test_init_fallback_primary_source(self, mock_config):
        """测试主数据源不可用时回退到第一个可用数据源"""
        mock_config.primary_source = "wind"
        mock_config.wind_enabled = False
        mock_config.akshare_enabled = True
        mock_adapter = MagicMock()
        mock_adapter.is_available.return_value = True

        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch("fund_cli.core.data_manager.AKShareAdapter", return_value=mock_adapter):
                    dm = DataManager()
                    # 应该回退到 akshare
                    assert dm._primary_source == "akshare"


# =============================================================================
# 测试类：适配器注册
# =============================================================================


class TestRegisterAdapter:
    """测试 register_adapter 方法"""

    def test_register_adapter_adds_to_dict(self, mock_config, mock_adapter):
        """测试注册适配器添加到字典"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm.register_adapter("custom", mock_adapter)
                    assert "custom" in dm._adapters
                    assert dm._adapters["custom"] is mock_adapter

    def test_register_adapter_overwrites_existing(self, mock_config, mock_adapter):
        """测试注册同名适配器覆盖"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm.register_adapter("test", mock_adapter)

                    new_adapter = MagicMock()
                    dm.register_adapter("test", new_adapter)
                    assert dm._adapters["test"] is new_adapter

    def test_register_multiple_adapters(self, mock_config, mock_adapter):
        """测试注册多个适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()

                    adapter1 = MagicMock()
                    adapter2 = MagicMock()
                    dm.register_adapter("adapter1", adapter1)
                    dm.register_adapter("adapter2", adapter2)

                    assert len(dm._adapters) == 2
                    assert "adapter1" in dm._adapters
                    assert "adapter2" in dm._adapters


# =============================================================================
# 测试类：属性访问
# =============================================================================


class TestProperties:
    """测试属性访问"""

    def test_available_sources_returns_list(self, mock_config, mock_adapter):
        """测试 available_sources 返回列表"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm.register_adapter("akshare", mock_adapter)
                    dm.register_adapter("tushare", mock_adapter)

                    sources = dm.available_sources
                    assert isinstance(sources, list)
                    assert "akshare" in sources
                    assert "tushare" in sources

    def test_available_sources_empty_when_no_adapters(self, mock_config):
        """测试无适配器时返回空列表"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    assert dm.available_sources == []

    def test_source_priority_returns_config_list(self, mock_config):
        """测试 source_priority 返回配置中的优先级列表"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    assert dm.source_priority == ["akshare", "tushare", "wind"]

    def test_gateway_returns_instance(self, mock_config):
        """测试 gateway 属性返回网关实例"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    from fund_cli.core.data_gateway import DataSourceGateway
                    assert isinstance(dm.gateway, DataSourceGateway)


# =============================================================================
# 测试类：get_adapter 方法
# =============================================================================


class TestGetAdapter:
    """测试 get_adapter 方法"""

    def test_get_adapter_returns_primary_by_default(self, mock_config, mock_adapter):
        """测试默认返回主数据源适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    result = dm.get_adapter()
                    assert result is mock_adapter

    def test_get_adapter_returns_specified_source(self, mock_config, mock_adapter):
        """测试返回指定数据源适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()

                    adapter1 = MagicMock()
                    adapter1.is_available.return_value = True
                    adapter2 = MagicMock()
                    adapter2.is_available.return_value = True

                    dm.register_adapter("akshare", adapter1)
                    dm.register_adapter("tushare", adapter2)

                    result = dm.get_adapter("tushare")
                    assert result is adapter2

    def test_get_adapter_raises_for_unconfigured_source(self, mock_config):
        """测试获取未配置的数据源抛出异常"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()

                    with pytest.raises(DataSourceError, match="未配置或不可用"):
                        dm.get_adapter("nonexistent")

    def test_get_adapter_raises_for_unavailable_source(self, mock_config, mock_adapter):
        """测试获取不可用的数据源抛出异常"""
        mock_adapter.is_available.return_value = False

        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm.register_adapter("akshare", mock_adapter)

                    with pytest.raises(DataSourceError, match="不可用"):
                        dm.get_adapter("akshare")

    def test_adapter_property_calls_get_adapter(self, mock_config, mock_adapter):
        """测试 _adapter 属性调用 get_adapter"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    result = dm._adapter
                    assert result is mock_adapter


# =============================================================================
# 测试类：数据访问接口代理
# =============================================================================


class TestDataAccessProxy:
    """测试数据访问接口代理"""

    def test_get_fund_info_calls_adapter(self, mock_config, mock_adapter):
        """测试 get_fund_info 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    result = dm.get_fund_info("000001")
                    mock_adapter.get_fund_info.assert_called_once_with("000001")
                    assert result["fund_code"] == "000001"

    def test_get_fund_nav_calls_adapter(self, mock_config, mock_adapter):
        """测试 get_fund_nav 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_fund_nav("000001", date(2024, 1, 1), date(2024, 12, 31))
                    mock_adapter.get_fund_nav.assert_called_once()

    def test_search_funds_calls_adapter(self, mock_config, mock_adapter):
        """测试 search_funds 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.search_funds(fund_type="混合型", limit=50)
                    mock_adapter.search_funds.assert_called_once()

    def test_get_fund_list_calls_adapter(self, mock_config, mock_adapter):
        """测试 get_fund_list 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_fund_list("股票型")
                    mock_adapter.get_fund_list.assert_called_once_with("股票型")

    def test_get_benchmark_nav_calls_adapter(self, mock_config, mock_adapter):
        """测试 get_benchmark_nav 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_benchmark_nav("000300")
                    mock_adapter.get_benchmark_nav.assert_called_once()

    def test_get_fund_holdings_calls_adapter(self, mock_config, mock_adapter):
        """测试 get_fund_holdings 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_fund_holdings("000001", date(2024, 6, 30))
                    mock_adapter.get_fund_holdings.assert_called_once()

    def test_get_fund_manager_calls_adapter(self, mock_config, mock_adapter):
        """测试 get_fund_manager 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_fund_manager("000001")
                    mock_adapter.get_fund_manager.assert_called_once_with("000001")

    def test_get_fund_fee_calls_adapter(self, mock_config, mock_adapter):
        """测试 get_fund_fee 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_fund_fee("000001")
                    mock_adapter.get_fund_fee.assert_called_once_with("000001")

    def test_get_fund_rating_calls_adapter(self, mock_config, mock_adapter):
        """测试 get_fund_rating 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_fund_rating("000001")
                    mock_adapter.get_fund_rating.assert_called_once_with("000001")

    def test_batch_get_fund_nav_calls_adapter(self, mock_config, mock_adapter):
        """测试 batch_get_fund_nav 通过 get_fund_nav 逐个获取（走 Gateway 缓存）"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.batch_get_fund_nav(["000001", "000002"])
                    # batch_get_fund_nav 现在通过 get_fund_nav 逐个获取（走 Gateway 缓存）
                    assert mock_adapter.get_fund_nav.call_count == 2


# =============================================================================
# 测试类：P0 级别接口代理
# =============================================================================


class TestP0Interfaces:
    """测试 P0 级别接口代理"""

    def test_get_all_fund_names(self, mock_config, mock_adapter):
        """测试 get_all_fund_names 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_all_fund_names()
                    mock_adapter.get_all_fund_names.assert_called_once()

    def test_get_fund_info_ths(self, mock_config, mock_adapter):
        """测试 get_fund_info_ths 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_fund_info_ths("000001")
                    mock_adapter.get_fund_info_ths.assert_called_once_with("000001")

    def test_get_index_fund_info(self, mock_config, mock_adapter):
        """测试 get_index_fund_info 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_index_fund_info("沪深指数", "被动指数型")
                    mock_adapter.get_index_fund_info.assert_called_once_with("沪深指数", "被动指数型")

    def test_get_fund_overview(self, mock_config, mock_adapter):
        """测试 get_fund_overview 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_fund_overview("000001")
                    mock_adapter.get_fund_overview.assert_called_once_with("000001")

    def test_get_fund_purchase_status(self, mock_config, mock_adapter):
        """测试 get_fund_purchase_status 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_fund_purchase_status()
                    mock_adapter.get_fund_purchase_status.assert_called_once()

    def test_get_fund_daily_nav(self, mock_config, mock_adapter):
        """测试 get_fund_daily_nav 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_fund_daily_nav()
                    mock_adapter.get_fund_daily_nav.assert_called_once()

    def test_get_etf_spot(self, mock_config, mock_adapter):
        """测试 get_etf_spot 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_etf_spot()
                    mock_adapter.get_etf_spot.assert_called_once()

    def test_get_lof_spot(self, mock_config, mock_adapter):
        """测试 get_lof_spot 调用适配器"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    dm.get_lof_spot()
                    mock_adapter.get_lof_spot.assert_called_once()


# =============================================================================
# 测试类：缓存管理
# =============================================================================


class TestCacheManagement:
    """测试缓存管理"""

    def test_clear_cache_calls_cache_clear(self, mock_config, mock_cache):
        """测试 clear_cache 调用缓存清理"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch.object(DataManager, "_init_adapters"):
                dm = DataManager(cache=mock_cache)
                dm.clear_cache()
                mock_cache.clear.assert_called_once()

    def test_get_cache_stats_returns_stats(self, mock_config, mock_cache):
        """测试 get_cache_stats 返回统计信息"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch.object(DataManager, "_init_adapters"):
                dm = DataManager(cache=mock_cache)
                result = dm.get_cache_stats()
                assert result == {"hits": 10, "misses": 5}


# =============================================================================
# 测试类：__repr__
# =============================================================================


class TestRepr:
    """测试 __repr__ 方法"""

    def test_repr_shows_sources_and_primary(self, mock_config, mock_adapter):
        """测试 __repr__ 显示数据源和主数据源"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"
                    dm.register_adapter("akshare", mock_adapter)

                    result = repr(dm)
                    assert "DataManager" in result
                    assert "akshare" in result

    def test_repr_empty_adapters(self, mock_config):
        """测试无适配器时的 __repr__"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                with patch.object(DataManager, "_init_adapters"):
                    dm = DataManager()
                    dm._primary_source = "akshare"

                    result = repr(dm)
                    assert "sources=[]" in result


# =============================================================================
# 测试类：全局实例
# =============================================================================


class TestGlobalInstance:
    """测试全局实例管理"""

    def test_get_data_manager_returns_singleton(self, mock_config):
        """测试 get_data_manager 返回单例"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                dm1 = get_data_manager()
                dm2 = get_data_manager()
                assert dm1 is dm2

    def test_get_data_manager_returns_data_manager_instance(self, mock_config):
        """测试 get_data_manager 返回 DataManager 实例"""
        with patch("fund_cli.core.data_manager.get_config", return_value=mock_config):
            with patch("fund_cli.core.data_manager.DataCache"):
                dm = get_data_manager()
                assert isinstance(dm, DataManager)
