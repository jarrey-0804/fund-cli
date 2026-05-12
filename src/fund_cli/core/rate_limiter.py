"""
全局限速器.

实现令牌桶算法，用于控制数据源请求速率，防止被封禁。
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from fund_cli.config import get_config

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RateLimitConfig:
    """限速配置."""

    # 每秒允许的请求数
    requests_per_second: float = 10.0
    # 桶容量（突发请求缓冲）
    bucket_size: int = 20
    # 是否启用限速
    enabled: bool = True


class TokenBucket:
    """
    令牌桶实现.

    令牌桶算法允许一定程度的突发流量，同时保持长期平均速率。
    """

    def __init__(self, rate: float, capacity: int):
        """
        初始化令牌桶.

        Args:
            rate: 令牌生成速率（每秒）
            capacity: 桶容量（最大令牌数）
        """
        self._rate = rate
        self._capacity = capacity
        self._tokens = capacity
        self._last_update = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: int = 1, blocking: bool = True, timeout: float | None = None) -> bool:
        """
        获取令牌.

        Args:
            tokens: 需要的令牌数
            blocking: 是否阻塞等待
            timeout: 阻塞超时时间（秒）

        Returns:
            是否成功获取令牌
        """
        with self._lock:
            self._add_tokens()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            if not blocking:
                return False

            if timeout is not None and timeout <= 0:
                return False

        # 需要等待，在锁外计算等待时间
        if blocking:
            needed = tokens - self._tokens
            wait_time = needed / self._rate

            if timeout is not None and wait_time > timeout:
                wait_time = timeout

            time.sleep(wait_time)

            with self._lock:
                self._add_tokens()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                return False

        return False

    def _add_tokens(self) -> None:
        """根据时间流逝添加令牌."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._last_update = now

        # 计算新产生的令牌
        new_tokens = elapsed * self._rate
        self._tokens = min(self._capacity, self._tokens + new_tokens)

    @property
    def tokens(self) -> float:
        """当前令牌数."""
        with self._lock:
            self._add_tokens()
            return self._tokens


class RateLimiter:
    """
    全局限速器.

    管理多个数据源的限速配置，提供统一的请求限速接口。
    """

    # 默认配置：不同数据源的限速策略
    DEFAULT_CONFIGS: dict[str, RateLimitConfig] = {
        # AKShare: 免费开源，限制较宽松
        "akshare": RateLimitConfig(requests_per_second=5.0, bucket_size=10),
        # Tushare: 付费API，限制较严格
        "tushare": RateLimitConfig(requests_per_second=1.0, bucket_size=3),
        # Wind: 商业授权，限制较宽松
        "wind": RateLimitConfig(requests_per_second=10.0, bucket_size=20),
        # 默认配置
        "default": RateLimitConfig(requests_per_second=5.0, bucket_size=10),
    }

    def __init__(self):
        """初始化限速器."""
        self._buckets: dict[str, TokenBucket] = {}
        self._configs: dict[str, RateLimitConfig] = {}
        self._lock = threading.Lock()
        self._load_config()

    def _load_config(self) -> None:
        """加载配置."""
        config = get_config()

        # 从配置中读取限速设置
        rate_limit_config = getattr(config, "rate_limit", {})

        for name, default_config in self.DEFAULT_CONFIGS.items():
            # 检查是否有自定义配置
            custom_config = rate_limit_config.get(name, {})

            self._configs[name] = RateLimitConfig(
                requests_per_second=custom_config.get(
                    "requests_per_second", default_config.requests_per_second
                ),
                bucket_size=custom_config.get("bucket_size", default_config.bucket_size),
                enabled=custom_config.get("enabled", default_config.enabled),
            )

            if self._configs[name].enabled:
                self._buckets[name] = TokenBucket(
                    rate=self._configs[name].requests_per_second,
                    capacity=self._configs[name].bucket_size,
                )

    def acquire(self, source_name: str, tokens: int = 1, blocking: bool = True) -> bool:
        """
        获取指定数据源的请求许可.

        Args:
            source_name: 数据源名称
            tokens: 消耗的令牌数（默认为1）
            blocking: 是否阻塞等待

        Returns:
            是否成功获取许可
        """
        # 标准化名称
        normalized_name = source_name.lower()

        # 查找配置
        config = self._configs.get(normalized_name) or self._configs.get("default")

        if not config or not config.enabled:
            return True

        # 获取或创建令牌桶
        with self._lock:
            if normalized_name not in self._buckets:
                self._buckets[normalized_name] = TokenBucket(
                    rate=config.requests_per_second,
                    capacity=config.bucket_size,
                )
            bucket = self._buckets[normalized_name]

        result = bucket.acquire(tokens, blocking=blocking)

        if not result:
            logger.warning("限速器阻止了 %s 的请求", source_name)

        return result

    def call_with_rate_limit(
        self,
        source_name: str,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        在限速控制下执行函数.

        Args:
            source_name: 数据源名称
            func: 要执行的函数
            *args, **kwargs: 函数参数

        Returns:
            函数返回值
        """
        self.acquire(source_name, blocking=True)
        return func(*args, **kwargs)

    def get_status(self) -> dict[str, Any]:
        """
        获取限速器状态.

        Returns:
            状态信息字典
        """
        status = {}
        for name, config in self._configs.items():
            bucket = self._buckets.get(name)
            status[name] = {
                "enabled": config.enabled,
                "requests_per_second": config.requests_per_second,
                "bucket_size": config.bucket_size,
                "current_tokens": bucket.tokens if bucket else None,
            }
        return status


# 全局限速器实例
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """获取全局限速器实例."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
