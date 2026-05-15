"""
DataSourceGateway 数据源网关单元测试

测试覆盖：
- 适配器注册与获取
- 可用适配器列表（按优先级排序）
- 熔断机制（CLOSED -> OPEN -> HALF_OPEN -> CLOSED）
- 降级切换（主数据源失败时切换到备用）
- call 方法的 fallback 逻辑
- get_status 返回结构
- 便捷方法调用
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from fund_cli.core.data_gateway import (
    CircuitState,
    DataSourceGateway,
    get_data_gateway,
)
from fund_cli.data.base import DataNotFoundError, DataSourceError

# =============================================================================
# Fixtures
# =============================================================================


def _reset_config():
    """重置全局配置，确保测试隔离"""
    import fund_cli.config as config_module
    config_module._config = None


@pytest.fixture(autouse=True)
def reset_gateway_global():
    """每个测试前后重置全局网关实例"""
    import fund_cli.core.data_gateway as gw_module
    gw_module._gateway = None
    yield
    gw_module._gateway = None


@pytest.fixture
def mock_config():
    """创建模拟配置，设置数据源优先级"""
    _reset_config()
    config = MagicMock()
    config.data.source_priority_list = ["akshare", "tushare", "wind"]
    with patch("fund_cli.core.data_gateway.get_config", return_value=config):
        yield config


@pytest.fixture
def mock_adapter_akshare():
    """创建模拟的 akshare 适配器"""
    adapter = MagicMock()
    adapter.name = "akshare"
    adapter.is_available.return_value = True
    adapter.get_fund_info.return_value = {
        "fund_code": "000001",
        "fund_name": "华夏成长混合",
        "type": "混合型",
    }
    adapter.get_fund_nav.return_value = "nav_data"
    adapter.get_fund_manager.return_value = {"manager": "张三"}
    adapter.get_fund_holdings.return_value = "holdings_data"
    adapter.get_fund_asset_allocation.return_value = {
        "stock_ratio": 80.0,
        "bond_ratio": 10.0,
        "cash_ratio": 5.0,
    }
    adapter.get_etf_spot.return_value = "etf_spot_data"
    adapter.get_lof_spot.return_value = "lof_spot_data"
    return adapter


@pytest.fixture
def mock_adapter_tushare():
    """创建模拟的 tushare 适配器"""
    adapter = MagicMock()
    adapter.name = "tushare"
    adapter.is_available.return_value = True
    adapter.get_fund_info.return_value = {
        "fund_code": "000001",
        "fund_name": "华夏成长混合(T)",
        "type": "混合型",
    }
    adapter.get_fund_nav.return_value = "nav_data_tushare"
    adapter.get_fund_manager.return_value = {"manager": "李四"}
    adapter.get_fund_holdings.return_value = "holdings_data_tushare"
    adapter.get_fund_asset_allocation.return_value = {
        "stock_ratio": 75.0,
        "bond_ratio": 15.0,
        "cash_ratio": 5.0,
    }
    adapter.get_etf_spot.return_value = "etf_spot_tushare"
    adapter.get_lof_spot.return_value = "lof_spot_tushare"
    return adapter


@pytest.fixture
def mock_adapter_wind():
    """创建模拟的 wind 适配器"""
    adapter = MagicMock()
    adapter.name = "wind"
    adapter.is_available.return_value = True
    adapter.get_fund_info.return_value = {
        "fund_code": "000001",
        "fund_name": "华夏成长混合(W)",
        "type": "混合型",
    }
    return adapter


@pytest.fixture
def gateway(mock_config, mock_adapter_akshare, mock_adapter_tushare, mock_adapter_wind):
    """创建注册了三个适配器的网关实例"""
    gw = DataSourceGateway()
    gw.register_adapter("akshare", mock_adapter_akshare)
    gw.register_adapter("tushare", mock_adapter_tushare)
    gw.register_adapter("wind", mock_adapter_wind)
    return gw


# =============================================================================
# 测试类：适配器注册与获取
# =============================================================================


class TestAdapterRegistration:
    """测试适配器的注册、获取和列表功能"""

    def test_register_adapter(self, gateway, mock_adapter_akshare):
        """测试注册适配器后，可通过名称获取"""
        adapter = gateway.get_adapter("akshare")
        assert adapter is mock_adapter_akshare

    def test_register_adapter_initializes_circuit_state(self, gateway):
        """测试注册适配器时初始化熔断器状态为 CLOSED"""
        assert gateway._circuit_states["akshare"] == CircuitState.CLOSED
        assert gateway._failure_counts["akshare"] == 0
        assert gateway._success_counts["akshare"] == 0

    def test_get_adapter_not_found(self, gateway):
        """测试获取不存在的适配器返回 None"""
        assert gateway.get_adapter("nonexistent") is None

    def test_register_multiple_adapters(self, gateway):
        """测试注册多个适配器后均可获取"""
        assert gateway.get_adapter("akshare") is not None
        assert gateway.get_adapter("tushare") is not None
        assert gateway.get_adapter("wind") is not None

    def test_register_adapter_overwrite(self, gateway):
        """测试重复注册同名适配器会覆盖"""
        new_adapter = MagicMock()
        new_adapter.is_available.return_value = True
        gateway.register_adapter("akshare", new_adapter)
        assert gateway.get_adapter("akshare") is new_adapter


# =============================================================================
# 测试类：可用适配器列表
# =============================================================================


class TestAvailableAdapters:
    """测试可用适配器列表功能"""

    def test_get_available_adapters_returns_priority_order(self, gateway):
        """测试可用适配器按配置优先级排序返回"""
        available = gateway.get_available_adapters()
        assert available == ["akshare", "tushare", "wind"]

    def test_get_available_adapters_excludes_unavailable(self, gateway, mock_adapter_akshare):
        """测试不可用的适配器不出现在列表中"""
        mock_adapter_akshare.is_available.return_value = False
        available = gateway.get_available_adapters()
        assert "akshare" not in available
        assert "tushare" in available
        assert "wind" in available

    def test_get_available_adapters_excludes_open_circuit(self, gateway):
        """测试熔断打开的适配器不出现在列表中"""
        gateway._circuit_states["tushare"] = CircuitState.OPEN
        available = gateway.get_available_adapters()
        assert "tushare" not in available
        assert "akshare" in available
        assert "wind" in available

    def test_get_available_adapters_empty_when_all_unavailable(self, gateway):
        """测试所有适配器都不可用时返回空列表"""
        for name in ["akshare", "tushare", "wind"]:
            adapter = gateway.get_adapter(name)
            adapter.is_available.return_value = False
        available = gateway.get_available_adapters()
        assert available == []

    def test_get_available_adapters_only_registered(self, mock_config):
        """测试只返回已注册且在优先级列表中的适配器"""
        gw = DataSourceGateway()
        # 只注册 akshare
        adapter = MagicMock()
        adapter.is_available.return_value = True
        gw.register_adapter("akshare", adapter)
        available = gw.get_available_adapters()
        assert available == ["akshare"]


# =============================================================================
# 测试类：熔断机制
# =============================================================================


class TestCircuitBreaker:
    """测试熔断器状态转换机制"""

    def test_initial_state_is_closed(self, gateway):
        """测试初始熔断器状态为 CLOSED"""
        assert gateway._circuit_states["akshare"] == CircuitState.CLOSED

    def test_circuit_opens_after_threshold_failures(self, gateway):
        """测试连续失败达到阈值（5次）后熔断器打开"""
        for _i in range(5):
            gateway._update_circuit_state("akshare", success=False)
        assert gateway._circuit_states["akshare"] == CircuitState.OPEN
        assert gateway._failure_counts["akshare"] == 5

    def test_circuit_stays_closed_below_threshold(self, gateway):
        """测试失败次数未达阈值时熔断器保持关闭"""
        for _i in range(4):
            gateway._update_circuit_state("akshare", success=False)
        assert gateway._circuit_states["akshare"] == CircuitState.CLOSED
        assert gateway._failure_counts["akshare"] == 4

    def test_success_resets_failure_count(self, gateway):
        """测试成功调用后重置失败计数"""
        gateway._update_circuit_state("akshare", success=False)
        gateway._update_circuit_state("akshare", success=False)
        assert gateway._failure_counts["akshare"] == 2

        gateway._update_circuit_state("akshare", success=True)
        assert gateway._failure_counts["akshare"] == 0
        assert gateway._success_counts["akshare"] == 1

    def test_open_circuit_transitions_to_half_open_after_timeout(self, gateway):
        """测试熔断打开后超过恢复时间转为半开"""
        # 先打开熔断器
        for _i in range(5):
            gateway._update_circuit_state("akshare", success=False)
        assert gateway._circuit_states["akshare"] == CircuitState.OPEN

        # 模拟超过恢复时间
        gateway._last_failure_time["akshare"] = datetime.now() - timedelta(seconds=61)
        gateway._update_circuit_state("akshare", success=True)
        assert gateway._circuit_states["akshare"] == CircuitState.HALF_OPEN

    def test_half_open_success_closes_circuit(self, gateway):
        """测试半开状态连续成功后熔断器关闭"""
        # 打开熔断器
        for _i in range(5):
            gateway._update_circuit_state("akshare", success=False)
        assert gateway._circuit_states["akshare"] == CircuitState.OPEN

        # 超时后转为半开
        gateway._last_failure_time["akshare"] = datetime.now() - timedelta(seconds=61)
        gateway._update_circuit_state("akshare", success=True)
        assert gateway._circuit_states["akshare"] == CircuitState.HALF_OPEN

        # 半开状态连续成功3次后关闭（第1次成功已在上面的HALF_OPEN转换中计数）
        # success_counts 在转 HALF_OPEN 时被重置为0，需要再成功3次
        gateway._update_circuit_state("akshare", success=True)
        gateway._update_circuit_state("akshare", success=True)
        gateway._update_circuit_state("akshare", success=True)
        assert gateway._circuit_states["akshare"] == CircuitState.CLOSED
        assert gateway._failure_counts["akshare"] == 0

    def test_half_open_failure_reopens_circuit(self, gateway):
        """测试半开状态失败后重新打开熔断器"""
        # 打开熔断器
        for _i in range(5):
            gateway._update_circuit_state("akshare", success=False)

        # 超时后转为半开
        gateway._last_failure_time["akshare"] = datetime.now() - timedelta(seconds=61)
        gateway._update_circuit_state("akshare", success=True)
        assert gateway._circuit_states["akshare"] == CircuitState.HALF_OPEN

        # 半开状态失败后重新打开
        gateway._update_circuit_state("akshare", success=False)
        assert gateway._circuit_states["akshare"] == CircuitState.OPEN

    def test_open_circuit_no_transition_within_timeout(self, gateway):
        """测试熔断打开后在恢复时间内不转换状态"""
        for _i in range(5):
            gateway._update_circuit_state("akshare", success=False)
        assert gateway._circuit_states["akshare"] == CircuitState.OPEN

        # 未超过恢复时间
        gateway._last_failure_time["akshare"] = datetime.now() - timedelta(seconds=30)
        gateway._update_circuit_state("akshare", success=True)
        # 仍然保持 OPEN（因为未超时）
        assert gateway._circuit_states["akshare"] == CircuitState.OPEN


# =============================================================================
# 测试类：带重试调用
# =============================================================================


class TestCallWithRetry:
    """测试带重试的调用机制"""

    def test_call_succeeds_on_first_attempt(self, gateway, mock_adapter_akshare):
        """测试第一次调用即成功"""
        mock_adapter_akshare.get_fund_info.return_value = {"fund_code": "000001"}
        result = gateway._call_with_retry(
            "akshare", mock_adapter_akshare.get_fund_info, 3, "000001"
        )
        assert result == {"fund_code": "000001"}
        assert mock_adapter_akshare.get_fund_info.call_count == 1

    def test_call_retries_on_failure(self, gateway, mock_adapter_akshare):
        """测试失败后自动重试"""
        mock_adapter_akshare.get_fund_info.side_effect = [
            Exception("网络错误"),
            Exception("超时"),
            {"fund_code": "000001"},
        ]
        result = gateway._call_with_retry(
            "akshare", mock_adapter_akshare.get_fund_info, 3, "000001"
        )
        assert result == {"fund_code": "000001"}
        assert mock_adapter_akshare.get_fund_info.call_count == 3

    def test_call_raises_after_max_retries(self, gateway, mock_adapter_akshare):
        """测试达到最大重试次数后抛出 DataSourceError"""
        mock_adapter_akshare.get_fund_info.side_effect = Exception("持续失败")
        with pytest.raises(DataSourceError, match="调用失败，已重试 3 次"):
            gateway._call_with_retry(
                "akshare", mock_adapter_akshare.get_fund_info, 3, "000001"
            )

    def test_call_no_retry_on_data_not_found(self, gateway, mock_adapter_akshare):
        """测试 DataNotFoundError 不重试，直接抛出"""
        mock_adapter_akshare.get_fund_info.side_effect = DataNotFoundError("基金不存在")
        with pytest.raises(DataNotFoundError):
            gateway._call_with_retry(
                "akshare", mock_adapter_akshare.get_fund_info, 3, "999999"
            )
        assert mock_adapter_akshare.get_fund_info.call_count == 1

    def test_retry_updates_circuit_state(self, gateway, mock_adapter_akshare):
        """测试重试过程中正确更新熔断器状态"""
        mock_adapter_akshare.get_fund_info.side_effect = Exception("失败")
        with pytest.raises(DataSourceError):
            gateway._call_with_retry(
                "akshare", mock_adapter_akshare.get_fund_info, 3, "000001"
            )
        # 3次失败，未达到阈值5
        assert gateway._failure_counts["akshare"] == 3
        assert gateway._circuit_states["akshare"] == CircuitState.CLOSED


# =============================================================================
# 测试类：call 方法与降级逻辑
# =============================================================================


class TestCallWithFallback:
    """测试 call 方法的降级切换逻辑"""

    def test_call_uses_primary_adapter_first(self, gateway, mock_adapter_akshare):
        """测试 call 方法优先使用主数据源"""
        gateway.call("get_fund_info", "000001")
        mock_adapter_akshare.get_fund_info.assert_called_once_with("000001")

    def test_call_falls_back_to_secondary(self, gateway, mock_adapter_akshare, mock_adapter_tushare):
        """测试主数据源失败时降级到备用数据源"""
        mock_adapter_akshare.get_fund_info.side_effect = Exception("akshare故障")
        result = gateway.call("get_fund_info", "000001")
        # 应该调用了 tushare
        mock_adapter_tushare.get_fund_info.assert_called_once_with("000001")
        assert result == {
            "fund_code": "000001",
            "fund_name": "华夏成长混合(T)",
            "type": "混合型",
        }

    def test_call_falls_back_through_all_adapters(self, gateway):
        """测试逐级降级直到找到可用数据源"""
        gateway._adapters["akshare"].get_fund_info.side_effect = Exception("故障1")
        gateway._adapters["tushare"].get_fund_info.side_effect = Exception("故障2")
        gateway.call("get_fund_info", "000001")
        # 应该使用 wind
        gateway._adapters["wind"].get_fund_info.assert_called_once_with("000001")

    def test_call_raises_when_all_adapters_fail(self, gateway):
        """测试所有数据源都失败时抛出 DataSourceError"""
        gateway._adapters["akshare"].get_fund_info.side_effect = Exception("故障1")
        gateway._adapters["tushare"].get_fund_info.side_effect = Exception("故障2")
        gateway._adapters["wind"].get_fund_info.side_effect = Exception("故障3")
        with pytest.raises(DataSourceError, match="所有数据源都失败"):
            gateway.call("get_fund_info", "000001")

    def test_call_without_fallback_raises_immediately(self, gateway, mock_adapter_akshare):
        """测试 fallback=False 时主数据源失败立即抛出异常"""
        mock_adapter_akshare.get_fund_info.side_effect = Exception("主数据源故障")
        with pytest.raises(Exception, match="主数据源故障"):
            gateway.call("get_fund_info", "000001", fallback=False)

    def test_call_skips_data_not_found_and_continues(self, gateway, mock_adapter_akshare, mock_adapter_tushare):
        """测试 DataNotFoundError 时跳过当前数据源继续尝试下一个"""
        mock_adapter_akshare.get_fund_info.side_effect = DataNotFoundError("未找到")
        gateway.call("get_fund_info", "000001")
        mock_adapter_tushare.get_fund_info.assert_called_once_with("000001")

    def test_call_raises_when_no_available_adapters(self, mock_config):
        """测试没有可用适配器时抛出 DataSourceError"""
        gw = DataSourceGateway()
        with pytest.raises(DataSourceError, match="没有可用的数据源"):
            gw.call("get_fund_info", "000001")

    def test_call_skips_method_not_found(self, gateway, mock_adapter_akshare):
        """测试适配器没有对应方法时跳过该适配器"""
        # 删除 get_etf_spot 方法
        del mock_adapter_akshare.get_etf_spot
        # tushare 有此方法
        result = gateway.call("get_etf_spot")
        assert result == "etf_spot_tushare"

    def test_call_circuit_breaker_excludes_adapter(self, gateway, mock_adapter_akshare):
        """测试熔断打开的适配器被排除在调用之外"""
        # 打开 akshare 的熔断器
        for _i in range(5):
            gateway._update_circuit_state("akshare", success=False)
        assert gateway._circuit_states["akshare"] == CircuitState.OPEN

        # call 应该跳过 akshare，使用 tushare
        gateway.call("get_fund_info", "000001")
        mock_adapter_akshare.get_fund_info.assert_not_called()
        gateway._adapters["tushare"].get_fund_info.assert_called_once_with("000001")


# =============================================================================
# 测试类：get_status
# =============================================================================


class TestGetStatus:
    """测试网关状态返回结构"""

    def test_get_status_returns_dict(self, gateway):
        """测试 get_status 返回字典"""
        status = gateway.get_status()
        assert isinstance(status, dict)

    def test_get_status_contains_adapters_info(self, gateway):
        """测试状态包含所有适配器信息"""
        status = gateway.get_status()
        assert "adapters" in status
        assert "akshare" in status["adapters"]
        assert "tushare" in status["adapters"]
        assert "wind" in status["adapters"]

    def test_get_status_adapter_fields(self, gateway):
        """测试适配器状态字段完整"""
        status = gateway.get_status()
        adapter_status = status["adapters"]["akshare"]
        assert "available" in adapter_status
        assert "circuit_state" in adapter_status
        assert "failure_count" in adapter_status
        assert "success_count" in adapter_status

    def test_get_status_circuit_state_value(self, gateway):
        """测试熔断器状态值为字符串"""
        status = gateway.get_status()
        assert status["adapters"]["akshare"]["circuit_state"] == "closed"

    def test_get_status_contains_priority(self, gateway):
        """测试状态包含优先级列表"""
        status = gateway.get_status()
        assert status["priority"] == ["akshare", "tushare", "wind"]

    def test_get_status_contains_available_adapters(self, gateway):
        """测试状态包含可用适配器列表"""
        status = gateway.get_status()
        assert status["available_adapters"] == ["akshare", "tushare", "wind"]

    def test_get_status_reflects_failure_count(self, gateway):
        """测试状态反映失败计数"""
        gateway._update_circuit_state("akshare", success=False)
        gateway._update_circuit_state("akshare", success=False)
        status = gateway.get_status()
        assert status["adapters"]["akshare"]["failure_count"] == 2

    def test_get_status_reflects_circuit_open(self, gateway):
        """测试状态反映熔断打开"""
        for _i in range(5):
            gateway._update_circuit_state("akshare", success=False)
        status = gateway.get_status()
        assert status["adapters"]["akshare"]["circuit_state"] == "open"


# =============================================================================
# 测试类：便捷方法
# =============================================================================


class TestConvenienceMethods:
    """测试网关便捷方法"""

    def test_get_fund_info(self, gateway, mock_adapter_akshare):
        """测试 get_fund_info 便捷方法"""
        result = gateway.get_fund_info("000001")
        mock_adapter_akshare.get_fund_info.assert_called_once_with("000001")
        assert result["fund_code"] == "000001"

    def test_get_fund_nav(self, gateway, mock_adapter_akshare):
        """测试 get_fund_nav 便捷方法"""
        gateway.get_fund_nav("000001", "2024-01-01", "2024-12-31")
        mock_adapter_akshare.get_fund_nav.assert_called_once_with(
            "000001", "2024-01-01", "2024-12-31"
        )

    def test_get_fund_manager(self, gateway, mock_adapter_akshare):
        """测试 get_fund_manager 便捷方法"""
        gateway.get_fund_manager("000001")
        mock_adapter_akshare.get_fund_manager.assert_called_once_with("000001")

    def test_get_fund_holdings(self, gateway, mock_adapter_akshare):
        """测试 get_fund_holdings 便捷方法"""
        gateway.get_fund_holdings("000001", "2024-06-30")
        mock_adapter_akshare.get_fund_holdings.assert_called_once_with(
            "000001", "2024-06-30"
        )

    def test_get_fund_asset_allocation(self, gateway, mock_adapter_akshare):
        """测试 get_fund_asset_allocation 便捷方法"""
        gateway.get_fund_asset_allocation("000001")
        mock_adapter_akshare.get_fund_asset_allocation.assert_called_once_with("000001")

    def test_get_etf_spot(self, gateway, mock_adapter_akshare):
        """测试 get_etf_spot 便捷方法"""
        gateway.get_etf_spot()
        mock_adapter_akshare.get_etf_spot.assert_called_once()

    def test_get_lof_spot(self, gateway, mock_adapter_akshare):
        """测试 get_lof_spot 便捷方法"""
        gateway.get_lof_spot()
        mock_adapter_akshare.get_lof_spot.assert_called_once()


# =============================================================================
# 测试类：全局网关实例
# =============================================================================


class TestGlobalGateway:
    """测试全局网关实例管理"""

    def test_get_data_gateway_returns_singleton(self, mock_config):
        """测试 get_data_gateway 返回单例"""
        gw1 = get_data_gateway()
        gw2 = get_data_gateway()
        assert gw1 is gw2

    def test_get_data_gateway_returns_gateway_instance(self, mock_config):
        """测试 get_data_gateway 返回 DataSourceGateway 实例"""
        gw = get_data_gateway()
        assert isinstance(gw, DataSourceGateway)


# =============================================================================
# 测试类：网关缓存机制
# =============================================================================


class TestGatewayCache:
    """测试网关缓存机制"""

    def test_cache_set_and_get(self, gateway):
        """测试缓存设置和获取"""
        cache_key = gateway._get_cache_key("get_fund_info", ("000001",), {})
        gateway._set_cache(cache_key, {"code": "000001", "name": "测试"})
        result = gateway._get_from_cache(cache_key)
        assert result == {"code": "000001", "name": "测试"}

    def test_cache_hit(self, gateway):
        """测试缓存命中"""
        cache_key = gateway._get_cache_key("get_fund_info", ("000001",), {})
        gateway._set_cache(cache_key, {"code": "000001", "name": "测试"})
        result = gateway._get_from_cache(cache_key)
        assert result is not None
        assert result["code"] == "000001"

    def test_cache_miss(self, gateway):
        """测试缓存未命中"""
        cache_key = gateway._get_cache_key("get_fund_info", ("999999",), {})
        result = gateway._get_from_cache(cache_key)
        assert result is None

    def test_cache_miss_after_ttl(self, gateway):
        """测试缓存过期"""
        import time

        cache_key = gateway._get_cache_key("get_fund_info", ("000001",), {})
        gateway._set_cache(cache_key, {"code": "000001", "name": "测试"})
        # 修改 TTL 为 0 使缓存立即过期
        gateway._cache_ttl = 0
        time.sleep(0.1)
        result = gateway._get_from_cache(cache_key)
        assert result is None

    def test_cache_expired_entry_removed(self, gateway):
        """测试过期缓存条目被自动移除"""
        import time

        cache_key = gateway._get_cache_key("get_fund_info", ("000001",), {})
        gateway._set_cache(cache_key, {"code": "000001"})
        assert len(gateway._call_cache) == 1
        # 使缓存过期
        gateway._cache_ttl = 0
        time.sleep(0.1)
        gateway._get_from_cache(cache_key)
        # 过期条目应被删除
        assert len(gateway._call_cache) == 0

    def test_clear_cache(self, gateway):
        """测试清空缓存"""
        cache_key1 = gateway._get_cache_key("get_fund_info", ("000001",), {})
        cache_key2 = gateway._get_cache_key("get_fund_nav", ("000001", "2024-01-01", "2024-12-31"), {})
        gateway._set_cache(cache_key1, {"code": "000001"})
        gateway._set_cache(cache_key2, {"nav": 1.5})
        assert len(gateway._call_cache) == 2
        gateway.clear_cache()
        assert len(gateway._call_cache) == 0

    def test_cache_key_different_args(self, gateway):
        """测试不同参数生成不同缓存键"""
        key1 = gateway._get_cache_key("get_fund_info", ("000001",), {})
        key2 = gateway._get_cache_key("get_fund_info", ("000002",), {})
        assert key1 != key2

    def test_cache_key_different_methods(self, gateway):
        """测试不同方法名生成不同缓存键"""
        key1 = gateway._get_cache_key("get_fund_info", ("000001",), {})
        key2 = gateway._get_cache_key("get_fund_nav", ("000001",), {})
        assert key1 != key2

    def test_cache_key_with_kwargs(self, gateway):
        """测试带 kwargs 的缓存键"""
        key1 = gateway._get_cache_key("get_fund_nav", ("000001",), {"start_date": "2024-01-01"})
        key2 = gateway._get_cache_key("get_fund_nav", ("000001",), {"start_date": "2024-06-01"})
        assert key1 != key2

    def test_cache_overwrite(self, gateway):
        """测试缓存覆盖"""
        cache_key = gateway._get_cache_key("get_fund_info", ("000001",), {})
        gateway._set_cache(cache_key, {"name": "旧数据"})
        gateway._set_cache(cache_key, {"name": "新数据"})
        result = gateway._get_from_cache(cache_key)
        assert result["name"] == "新数据"

    def test_cache_size_in_status(self, gateway):
        """测试状态中包含缓存大小"""
        cache_key = gateway._get_cache_key("get_fund_info", ("000001",), {})
        gateway._set_cache(cache_key, {"code": "000001"})
        status = gateway.get_status()
        assert "cache_size" in status
        assert status["cache_size"] == 1

    def test_clear_cache_reflects_in_status(self, gateway):
        """测试清空缓存后状态中缓存大小为 0"""
        cache_key = gateway._get_cache_key("get_fund_info", ("000001",), {})
        gateway._set_cache(cache_key, {"code": "000001"})
        gateway.clear_cache()
        status = gateway.get_status()
        assert status["cache_size"] == 0


# =============================================================================
# 测试类：call 方法参数组合
# =============================================================================


class TestCallMethodParameters:
    """测试 call 方法的各种参数组合"""

    def test_call_with_positional_args_only(self, gateway, mock_adapter_akshare):
        """测试仅使用位置参数调用"""
        gateway.call("get_fund_info", "000001")
        mock_adapter_akshare.get_fund_info.assert_called_once_with("000001")

    def test_call_with_keyword_args(self, gateway, mock_adapter_akshare):
        """测试使用关键字参数调用"""
        mock_adapter_akshare.get_fund_nav.return_value = pd.DataFrame()
        gateway.call("get_fund_nav", "000001", start_date="2024-01-01", end_date="2024-12-31")
        mock_adapter_akshare.get_fund_nav.assert_called_once_with(
            "000001", start_date="2024-01-01", end_date="2024-12-31"
        )

    def test_call_with_mixed_args(self, gateway, mock_adapter_akshare):
        """测试混合位置参数和关键字参数"""
        mock_adapter_akshare.get_fund_nav.return_value = pd.DataFrame()
        gateway.call("get_fund_nav", "000001", "2024-01-01", end_date="2024-12-31")
        mock_adapter_akshare.get_fund_nav.assert_called_once()

    def test_call_with_no_args(self, gateway, mock_adapter_akshare):
        """测试无参数调用"""
        gateway.call("get_etf_spot")
        mock_adapter_akshare.get_etf_spot.assert_called_once_with()

    def test_call_with_complex_args(self, gateway, mock_adapter_akshare):
        """测试复杂参数调用"""
        mock_adapter_akshare.search_funds.return_value = pd.DataFrame()
        gateway.call(
            "search_funds",
            fund_type="混合型",
            company="华夏",
            min_scale=1.0,
            max_scale=100.0,
            keyword="成长",
            limit=50,
        )
        mock_adapter_akshare.search_funds.assert_called_once()

    def test_call_with_fallback_true(self, gateway, mock_adapter_akshare, mock_adapter_tushare):
        """测试 fallback=True 时降级行为"""
        mock_adapter_akshare.get_fund_info.side_effect = Exception("故障")
        gateway.call("get_fund_info", "000001", fallback=True)
        mock_adapter_tushare.get_fund_info.assert_called_once()

    def test_call_with_fallback_false_raises(self, gateway, mock_adapter_akshare):
        """测试 fallback=False 时立即抛出异常"""
        mock_adapter_akshare.get_fund_info.side_effect = Exception("主数据源故障")
        with pytest.raises(Exception, match="主数据源故障"):
            gateway.call("get_fund_info", "000001", fallback=False)


# =============================================================================
# 测试类：get_status 返回结构完整性
# =============================================================================


class TestGetStatusCompleteness:
    """测试 get_status 返回结构完整性"""

    def test_get_status_has_all_top_level_keys(self, gateway):
        """测试状态包含所有顶级键"""
        status = gateway.get_status()
        assert "adapters" in status
        assert "priority" in status
        assert "available_adapters" in status
        assert "cache_size" in status

    def test_get_status_adapter_has_all_keys(self, gateway):
        """测试每个适配器状态包含所有必需键"""
        status = gateway.get_status()
        required_keys = ["available", "circuit_state", "failure_count", "success_count"]
        for adapter_name, adapter_status in status["adapters"].items():
            for key in required_keys:
                assert key in adapter_status, f"适配器 {adapter_name} 缺少键 {key}"

    def test_get_status_available_is_boolean(self, gateway):
        """测试 available 字段为布尔值"""
        status = gateway.get_status()
        for _adapter_name, adapter_status in status["adapters"].items():
            assert isinstance(adapter_status["available"], bool)

    def test_get_status_circuit_state_is_string(self, gateway):
        """测试 circuit_state 字段为字符串"""
        status = gateway.get_status()
        valid_states = ["closed", "open", "half_open"]
        for _adapter_name, adapter_status in status["adapters"].items():
            assert adapter_status["circuit_state"] in valid_states

    def test_get_status_counts_are_integers(self, gateway):
        """测试计数器字段为整数"""
        status = gateway.get_status()
        for _adapter_name, adapter_status in status["adapters"].items():
            assert isinstance(adapter_status["failure_count"], int)
            assert isinstance(adapter_status["success_count"], int)

    def test_get_status_priority_is_list(self, gateway):
        """测试 priority 字段为列表"""
        status = gateway.get_status()
        assert isinstance(status["priority"], list)

    def test_get_status_available_adapters_is_list(self, gateway):
        """测试 available_adapters 字段为列表"""
        status = gateway.get_status()
        assert isinstance(status["available_adapters"], list)

    def test_get_status_cache_size_is_int(self, gateway):
        """测试 cache_size 字段为整数"""
        status = gateway.get_status()
        assert isinstance(status["cache_size"], int)

    def test_get_status_reflects_all_registered_adapters(self, gateway):
        """测试状态包含所有已注册的适配器"""
        status = gateway.get_status()
        assert len(status["adapters"]) == 3
        assert "akshare" in status["adapters"]
        assert "tushare" in status["adapters"]
        assert "wind" in status["adapters"]


# =============================================================================
# 测试类：熔断器完整状态转换
# =============================================================================


class TestCircuitBreakerCompleteTransitions:
    """测试熔断器完整状态转换流程"""

    def test_full_cycle_closed_to_open_to_half_open_to_closed(self, gateway):
        """测试完整熔断器状态循环：CLOSED -> OPEN -> HALF_OPEN -> CLOSED"""
        # 初始状态为 CLOSED
        assert gateway._circuit_states["akshare"] == CircuitState.CLOSED

        # 连续失败 5 次，转为 OPEN
        for _ in range(5):
            gateway._update_circuit_state("akshare", success=False)
        assert gateway._circuit_states["akshare"] == CircuitState.OPEN

        # 超时后转为 HALF_OPEN
        gateway._last_failure_time["akshare"] = datetime.now() - timedelta(seconds=61)
        gateway._update_circuit_state("akshare", success=True)
        assert gateway._circuit_states["akshare"] == CircuitState.HALF_OPEN

        # 连续成功 3 次，转为 CLOSED
        gateway._update_circuit_state("akshare", success=True)
        gateway._update_circuit_state("akshare", success=True)
        gateway._update_circuit_state("akshare", success=True)
        assert gateway._circuit_states["akshare"] == CircuitState.CLOSED

    def test_half_open_immediate_failure_reopens(self, gateway):
        """测试半开状态立即失败重新打开"""
        # 打开熔断器
        for _ in range(5):
            gateway._update_circuit_state("akshare", success=False)
        assert gateway._circuit_states["akshare"] == CircuitState.OPEN

        # 超时后转为 HALF_OPEN
        gateway._last_failure_time["akshare"] = datetime.now() - timedelta(seconds=61)
        gateway._update_circuit_state("akshare", success=True)
        assert gateway._circuit_states["akshare"] == CircuitState.HALF_OPEN

        # 立即失败，重新打开
        gateway._update_circuit_state("akshare", success=False)
        assert gateway._circuit_states["akshare"] == CircuitState.OPEN

    def test_multiple_half_open_success_before_close(self, gateway):
        """测试半开状态需要多次成功才能关闭"""
        # 打开熔断器
        for _ in range(5):
            gateway._update_circuit_state("akshare", success=False)
        assert gateway._circuit_states["akshare"] == CircuitState.OPEN

        # 超时后转为 HALF_OPEN
        gateway._last_failure_time["akshare"] = datetime.now() - timedelta(seconds=61)
        gateway._update_circuit_state("akshare", success=True)
        assert gateway._circuit_states["akshare"] == CircuitState.HALF_OPEN
        assert gateway._success_counts["akshare"] == 0  # 重置为0

        # 需要再成功 3 次
        gateway._update_circuit_state("akshare", success=True)
        assert gateway._circuit_states["akshare"] == CircuitState.HALF_OPEN
        gateway._update_circuit_state("akshare", success=True)
        assert gateway._circuit_states["akshare"] == CircuitState.HALF_OPEN
        gateway._update_circuit_state("akshare", success=True)
        assert gateway._circuit_states["akshare"] == CircuitState.CLOSED

    def test_success_count_increments_in_closed_state(self, gateway):
        """测试关闭状态下成功计数递增"""
        initial_count = gateway._success_counts["akshare"]
        gateway._update_circuit_state("akshare", success=True)
        assert gateway._success_counts["akshare"] == initial_count + 1

    def test_failure_count_increments_in_closed_state(self, gateway):
        """测试关闭状态下失败计数递增"""
        initial_count = gateway._failure_counts["akshare"]
        gateway._update_circuit_state("akshare", success=False)
        assert gateway._failure_counts["akshare"] == initial_count + 1


# =============================================================================
# 测试类：降级逻辑完整流程
# =============================================================================


class TestFallbackCompleteFlow:
    """测试降级逻辑完整流程"""

    def test_fallback_order_follows_priority(self, gateway):
        """测试降级顺序遵循优先级配置"""
        # 让 akshare 和 tushare 都失败
        gateway._adapters["akshare"].get_fund_info.side_effect = Exception("故障1")
        gateway._adapters["tushare"].get_fund_info.side_effect = Exception("故障2")

        gateway.call("get_fund_info", "000001")
        # 应该使用 wind（第三个优先级）
        gateway._adapters["wind"].get_fund_info.assert_called_once()

    def test_fallback_skips_open_circuit(self, gateway):
        """测试降级跳过熔断打开的适配器"""
        # 打开 akshare 熔断器
        for _ in range(5):
            gateway._update_circuit_state("akshare", success=False)

        gateway.call("get_fund_info", "000001")
        # 应该跳过 akshare，使用 tushare
        gateway._adapters["akshare"].get_fund_info.assert_not_called()
        gateway._adapters["tushare"].get_fund_info.assert_called_once()

    def test_fallback_skips_unavailable_adapter(self, gateway, mock_adapter_akshare):
        """测试降级跳过不可用的适配器"""
        mock_adapter_akshare.is_available.return_value = False

        gateway.call("get_fund_info", "000001")
        # 应该跳过 akshare，使用 tushare
        gateway._adapters["tushare"].get_fund_info.assert_called_once()

    def test_fallback_with_all_adapters_unavailable(self, gateway):
        """测试所有适配器都不可用时抛出异常"""
        for name in ["akshare", "tushare", "wind"]:
            gateway._adapters[name].is_available.return_value = False

        with pytest.raises(DataSourceError, match="没有可用的数据源"):
            gateway.call("get_fund_info", "000001")

    def test_fallback_with_all_adapters_open_circuit(self, gateway):
        """测试所有适配器熔断打开时抛出异常"""
        for name in ["akshare", "tushare", "wind"]:
            for _ in range(5):
                gateway._update_circuit_state(name, success=False)

        with pytest.raises(DataSourceError, match="没有可用的数据源"):
            gateway.call("get_fund_info", "000001")


# =============================================================================
# 测试类：重试机制边缘情况
# =============================================================================


class TestRetryMechanismEdgeCases:
    """测试重试机制边缘情况"""

    def test_retry_with_different_exception_types(self, gateway, mock_adapter_akshare):
        """测试不同异常类型的重试行为"""
        mock_adapter_akshare.get_fund_info.side_effect = [
            ValueError("错误1"),
            TypeError("错误2"),
            {"fund_code": "000001"},
        ]
        result = gateway._call_with_retry("akshare", mock_adapter_akshare.get_fund_info, 3, "000001")
        assert result == {"fund_code": "000001"}
        assert mock_adapter_akshare.get_fund_info.call_count == 3

    def test_retry_updates_failure_count_each_time(self, gateway, mock_adapter_akshare):
        """测试每次重试失败都更新失败计数"""
        mock_adapter_akshare.get_fund_info.side_effect = Exception("失败")
        with pytest.raises(DataSourceError):
            gateway._call_with_retry("akshare", mock_adapter_akshare.get_fund_info, 3, "000001")
        assert gateway._failure_counts["akshare"] == 3

    def test_retry_with_max_retries_one(self, gateway, mock_adapter_akshare):
        """测试最大重试次数为 1"""
        mock_adapter_akshare.get_fund_info.side_effect = Exception("失败")
        with pytest.raises(DataSourceError):
            gateway._call_with_retry("akshare", mock_adapter_akshare.get_fund_info, 1, "000001")
        assert mock_adapter_akshare.get_fund_info.call_count == 1

    def test_retry_success_on_last_attempt(self, gateway, mock_adapter_akshare):
        """测试最后一次重试成功"""
        mock_adapter_akshare.get_fund_info.side_effect = [
            Exception("失败1"),
            Exception("失败2"),
            {"fund_code": "000001"},
        ]
        result = gateway._call_with_retry("akshare", mock_adapter_akshare.get_fund_info, 3, "000001")
        assert result == {"fund_code": "000001"}
        assert mock_adapter_akshare.get_fund_info.call_count == 3


# =============================================================================
# 测试类：便捷方法额外测试
# =============================================================================


class TestConvenienceMethodsExtended:
    """测试便捷方法额外用例"""

    def test_get_fund_benchmark(self, mock_config, mock_adapter_akshare):
        """测试 get_fund_benchmark 便捷方法"""
        mock_adapter_akshare.get_fund_benchmark = MagicMock(return_value={"benchmark": "沪深300"})
        gw = DataSourceGateway()
        gw.register_adapter("akshare", mock_adapter_akshare)
        gw.get_fund_benchmark("000001")
        mock_adapter_akshare.get_fund_benchmark.assert_called_once_with("000001")

    def test_get_all_fund_names(self, mock_config, mock_adapter_akshare):
        """测试 get_all_fund_names 便捷方法"""
        mock_adapter_akshare.get_all_fund_names = MagicMock(return_value=pd.DataFrame())
        gw = DataSourceGateway()
        gw.register_adapter("akshare", mock_adapter_akshare)
        gw.get_all_fund_names()
        mock_adapter_akshare.get_all_fund_names.assert_called_once()

    def test_get_fund_daily_nav(self, mock_config, mock_adapter_akshare):
        """测试 get_fund_daily_nav 便捷方法"""
        mock_adapter_akshare.get_fund_daily_nav = MagicMock(return_value=pd.DataFrame())
        gw = DataSourceGateway()
        gw.register_adapter("akshare", mock_adapter_akshare)
        gw.get_fund_daily_nav()
        mock_adapter_akshare.get_fund_daily_nav.assert_called_once()

    def test_get_fund_purchase_status(self, mock_config, mock_adapter_akshare):
        """测试 get_fund_purchase_status 便捷方法"""
        mock_adapter_akshare.get_fund_purchase_status = MagicMock(return_value=pd.DataFrame())
        gw = DataSourceGateway()
        gw.register_adapter("akshare", mock_adapter_akshare)
        gw.get_fund_purchase_status()
        mock_adapter_akshare.get_fund_purchase_status.assert_called_once()
