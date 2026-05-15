"""
数据源网关.

提供多数据源管理、降级切换、熔断与重试机制。
"""

import hashlib
import json
import logging
from collections import OrderedDict
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, TypeVar

from fund_cli.config import get_config
from fund_cli.core.rate_limiter import get_rate_limiter
from fund_cli.data.base import DataNotFoundError, DataSourceAdapter, DataSourceError

T = TypeVar("T")

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """熔断器状态."""

    CLOSED = "closed"  # 正常状态
    OPEN = "open"  # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


class DataSourceGateway:
    """
    数据源网关.

    功能：
    - 管理多个数据源适配器
    - 支持数据源优先级配置
    - 实现降级切换逻辑
    - 熔断与重试机制
    - 统一的错误处理
    """

    def __init__(self):
        """初始化数据源网关."""
        self._adapters: dict[str, DataSourceAdapter] = {}
        self._priority: list[str] = []
        self._circuit_states: dict[str, CircuitState] = {}
        self._failure_counts: dict[str, int] = {}
        self._last_failure_time: dict[str, datetime] = {}
        self._success_counts: dict[str, int] = {}

        # 熔断配置
        self._failure_threshold = 5  # 连续失败阈值
        self._recovery_timeout = 60  # 熔断恢复时间（秒）
        self._half_open_max_calls = 3  # 半开状态最大调用次数

        # 请求缓存配置（OrderedDict 实现 LRU）
        self._call_cache: OrderedDict[str, tuple[datetime, Any]] = OrderedDict()
        self._cache_ttl = 300  # 5分钟缓存
        self._cache_max_size = 500  # 最大缓存条目数

        # 缓存命中/未命中计数器
        self._cache_hit_count: int = 0
        self._cache_miss_count: int = 0

        self._load_config()

    def _load_config(self) -> None:
        """加载配置."""
        config = get_config()
        self._priority = config.data.source_priority_list

    def register_adapter(self, name: str, adapter: DataSourceAdapter) -> None:
        """
        注册数据源适配器.

        Args:
            name: 适配器名称
            adapter: 适配器实例
        """
        self._adapters[name] = adapter
        self._circuit_states[name] = CircuitState.CLOSED
        self._failure_counts[name] = 0
        self._success_counts[name] = 0

    def get_adapter(self, name: str) -> DataSourceAdapter | None:
        """
        获取指定适配器.

        Args:
            name: 适配器名称

        Returns:
            适配器实例或None
        """
        return self._adapters.get(name)

    def get_available_adapters(self) -> list[str]:
        """
        获取可用的适配器列表.

        Returns:
            按优先级排序的可用适配器名称列表
        """
        available = []
        for name in self._priority:
            if name in self._adapters:
                adapter = self._adapters[name]
                if adapter.is_available() and self._circuit_states.get(name) != CircuitState.OPEN:
                    available.append(name)
        return available

    def _update_circuit_state(self, name: str, success: bool) -> None:
        """更新熔断器状态."""
        state = self._circuit_states.get(name, CircuitState.CLOSED)

        if state == CircuitState.CLOSED:
            if success:
                self._failure_counts[name] = 0
                self._success_counts[name] += 1
            else:
                self._failure_counts[name] += 1
                self._last_failure_time[name] = datetime.now()

                if self._failure_counts[name] >= self._failure_threshold:
                    self._circuit_states[name] = CircuitState.OPEN
                    logger.warning("%s 熔断器打开", name)

        elif state == CircuitState.OPEN:
            # 检查是否到达恢复时间
            last_failure = self._last_failure_time.get(name)
            if last_failure and datetime.now() - last_failure > timedelta(
                seconds=self._recovery_timeout
            ):
                self._circuit_states[name] = CircuitState.HALF_OPEN
                self._success_counts[name] = 0
                logger.info("%s 熔断器半开", name)

        elif state == CircuitState.HALF_OPEN:
            if success:
                self._success_counts[name] += 1
                if self._success_counts[name] >= self._half_open_max_calls:
                    self._circuit_states[name] = CircuitState.CLOSED
                    self._failure_counts[name] = 0
                    logger.info("%s 熔断器关闭", name)
            else:
                self._circuit_states[name] = CircuitState.OPEN
                self._failure_counts[name] += 1
                self._last_failure_time[name] = datetime.now()
                logger.warning("%s 熔断器重新打开", name)

    def _call_with_retry(
        self,
        adapter_name: str,
        method: Callable[..., T],
        max_retries: int = 3,
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        带重试和限速的调用.

        Args:
            adapter_name: 适配器名称
            method: 要调用的方法
            max_retries: 最大重试次数
            *args, **kwargs: 方法参数

        Returns:
            方法返回值

        Raises:
            DataSourceError: 所有重试都失败
        """
        # 获取限速器并等待许可
        rate_limiter = get_rate_limiter()
        rate_limiter.acquire(adapter_name, blocking=True)

        last_error = None

        for attempt in range(max_retries):
            try:
                result = method(*args, **kwargs)
                self._update_circuit_state(adapter_name, True)
                return result
            except DataNotFoundError:
                # 数据不存在不重试
                raise
            except Exception as e:
                last_error = e
                self._update_circuit_state(adapter_name, False)
                logger.warning(
                    "%s 调用失败 (尝试 %d/%d): %s", adapter_name, attempt + 1, max_retries, e
                )

        raise DataSourceError(
            f"{adapter_name} 调用失败，已重试 {max_retries} 次: {last_error}"
        ) from last_error

    def call(self, method_name: str, *args: Any, fallback: bool = True, **kwargs: Any) -> Any:
        """
        调用数据源方法.

        Args:
            method_name: 方法名称
            args: 方法位置参数
            kwargs: 方法关键字参数
            fallback: 是否启用降级切换

        Returns:
            方法返回值

        Raises:
            DataSourceError: 所有数据源都失败
        """
        # Check cache first
        cache_key = self._get_cache_key(method_name, args, kwargs)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            logger.debug("Cache hit for %s", method_name)
            return cached

        available = self.get_available_adapters()

        if not available:
            raise DataSourceError("没有可用的数据源")

        last_error = None

        for adapter_name in available:
            adapter = self._adapters[adapter_name]
            method = getattr(adapter, method_name, None)

            if method is None:
                continue

            try:
                result = self._call_with_retry(adapter_name, method, 3, *args, **kwargs)
                self._set_cache(cache_key, result)
                return result
            except DataNotFoundError:
                # 数据不存在，尝试下一个数据源
                continue
            except Exception as e:
                last_error = e
                if not fallback:
                    raise
                # 继续尝试下一个数据源
                continue

        if last_error:
            raise DataSourceError(f"所有数据源都失败: {last_error}") from last_error
        raise DataSourceError(f"方法 {method_name} 在所有数据源都不可用")

    def get_fund_info(self, fund_code: str) -> dict[str, Any]:
        """获取基金信息."""
        return self.call("get_fund_info", fund_code)

    def get_fund_nav(self, fund_code: str, start_date=None, end_date=None) -> Any:
        """获取基金净值."""
        return self.call("get_fund_nav", fund_code, start_date, end_date)

    def get_fund_manager(self, fund_code: str) -> Any:
        """获取基金经理."""
        return self.call("get_fund_manager", fund_code)

    def get_fund_holdings(self, fund_code: str, date=None) -> Any:
        """获取基金持仓."""
        return self.call("get_fund_holdings", fund_code, date)

    def get_fund_asset_allocation(self, fund_code: str) -> dict[str, Any]:
        """获取基金资产配置."""
        return self.call("get_fund_asset_allocation", fund_code)

    def get_fund_benchmark(self, fund_code: str) -> dict[str, Any]:
        """获取基金业绩基准."""
        return self.call("get_fund_benchmark", fund_code)

    def get_etf_spot(self) -> Any:
        """获取ETF实时行情."""
        return self.call("get_etf_spot")

    def get_lof_spot(self) -> Any:
        """获取LOF实时行情."""
        return self.call("get_lof_spot")

    def get_fund_purchase_status(self) -> Any:
        """获取基金申购状态."""
        return self.call("get_fund_purchase_status")

    def get_all_fund_names(self) -> Any:
        """获取所有基金名称."""
        return self.call("get_all_fund_names")

    def get_fund_daily_nav(self) -> Any:
        """获取基金每日净值."""
        return self.call("get_fund_daily_nav")

    def _get_cache_key(self, method_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键."""
        raw = f"{method_name}:{json.dumps(args, default=str)}:{json.dumps(sorted(kwargs.items()), default=str)}"
        return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()[:16]

    def _get_from_cache(self, key: str) -> Any | None:
        """从缓存获取（LRU 命中时移到末尾）."""
        if key in self._call_cache:
            timestamp, value = self._call_cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                # 命中，移到末尾（标记为最近使用）
                self._call_cache.move_to_end(key)
                self._cache_hit_count += 1
                try:
                    from fund_cli.core.metrics_exporter import get_metrics_exporter
                    get_metrics_exporter().record_cache_hit("gateway_memory", True)
                except Exception:
                    pass
                return value
            # 过期，删除
            del self._call_cache[key]
        self._cache_miss_count += 1
        try:
            from fund_cli.core.metrics_exporter import get_metrics_exporter
            get_metrics_exporter().record_cache_hit("gateway_memory", False)
        except Exception:
            pass
        return None

    def _set_cache(self, key: str, value: Any) -> None:
        """设置缓存（LRU 淘汰）."""
        # 如果已存在，先移除（后续重新插入到末尾）
        if key in self._call_cache:
            del self._call_cache[key]
        self._call_cache[key] = (datetime.now(), value)
        # LRU 淘汰：超过最大条目数时移除最旧的
        while len(self._call_cache) > self._cache_max_size:
            self._call_cache.popitem(last=False)

    def clear_cache(self) -> None:
        """清空请求缓存."""
        self._call_cache.clear()

    def get_status(self) -> dict[str, Any]:
        """
        获取网关状态.

        Returns:
            状态信息字典
        """
        # 获取限速器状态
        rate_limiter = get_rate_limiter()
        rate_limit_status = rate_limiter.get_status()

        return {
            "adapters": {
                name: {
                    "available": adapter.is_available(),
                    "circuit_state": self._circuit_states.get(name, CircuitState.CLOSED).value,
                    "failure_count": self._failure_counts.get(name, 0),
                    "success_count": self._success_counts.get(name, 0),
                }
                for name, adapter in self._adapters.items()
            },
            "priority": self._priority,
            "available_adapters": self.get_available_adapters(),
            "cache_size": len(self._call_cache),
            "cache_max_size": self._cache_max_size,
            "cache_hit_rate": round(
                self._cache_hit_count
                / (self._cache_hit_count + self._cache_miss_count) * 100,
                2,
            )
            if (self._cache_hit_count + self._cache_miss_count) > 0
            else 0.0,
            "cache_hits": self._cache_hit_count,
            "cache_misses": self._cache_miss_count,
            "rate_limiter": rate_limit_status,
        }


# 全局网关实例
_gateway: DataSourceGateway | None = None


def get_data_gateway() -> DataSourceGateway:
    """获取全局数据源网关实例."""
    global _gateway
    if _gateway is None:
        _gateway = DataSourceGateway()
    return _gateway
