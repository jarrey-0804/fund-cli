"""
幂等性保证工具.

提供请求去重和幂等执行机制，防止重复数据处理。
"""

import hashlib
import logging
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

from diskcache import Cache

logger = logging.getLogger(__name__)

T = TypeVar("T")


class IdempotencyKey:
    """幂等性键生成器."""

    @staticmethod
    def generate(*args, **kwargs) -> str:
        """
        生成幂等性键.

        Args:
            *args, **kwargs: 函数参数

        Returns:
            幂等性键
        """
        import json

        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]


class RequestLock:
    """
    请求锁.

    防止相同参数的并发请求同时执行。
    """

    def __init__(self, cache_dir: str = "~/.fund_cli/locks"):
        """
        初始化请求锁.

        Args:
            cache_dir: 锁文件目录
        """
        from pathlib import Path

        self._cache_dir = Path(cache_dir).expanduser()
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = Cache(str(self._cache_dir))
        self._memory_locks: dict[str, threading.Lock] = {}
        self._lock = threading.Lock()

    def _get_memory_lock(self, key: str) -> threading.Lock:
        """获取内存锁."""
        with self._lock:
            if key not in self._memory_locks:
                self._memory_locks[key] = threading.Lock()
            return self._memory_locks[key]

    def acquire(self, key: str, timeout: float = 30.0) -> bool:
        """
        获取锁.

        Args:
            key: 锁键
            timeout: 超时时间（秒）

        Returns:
            是否成功获取锁
        """
        memory_lock = self._get_memory_lock(key)

        # 先获取内存锁
        if not memory_lock.acquire(timeout=timeout):
            return False

        try:
            # 检查是否有其他进程持有锁
            lock_key = f"lock:{key}"
            existing_lock = self._cache.get(lock_key)

            if existing_lock:
                # 检查锁是否过期
                if time.time() - existing_lock.get("timestamp", 0) < timeout:
                    memory_lock.release()
                    return False

            # 设置锁
            self._cache.set(
                lock_key,
                {"timestamp": time.time(), "thread_id": threading.current_thread().ident},
                expire=int(timeout) + 10,  # 稍微长一点的过期时间
            )

            return True

        except Exception as e:
            logger.error("获取锁失败: %s", e)
            memory_lock.release()
            return False

    def release(self, key: str) -> None:
        """
        释放锁.

        Args:
            key: 锁键
        """
        try:
            lock_key = f"lock:{key}"
            self._cache.delete(lock_key)
        except Exception as e:
            logger.error("释放磁盘锁失败: %s", e)

        try:
            memory_lock = self._get_memory_lock(key)
            memory_lock.release()
        except Exception as e:
            logger.error("释放内存锁失败: %s", e)

    def is_locked(self, key: str) -> bool:
        """
        检查是否被锁定.

        Args:
            key: 锁键

        Returns:
            是否被锁定
        """
        lock_key = f"lock:{key}"
        return self._cache.get(lock_key) is not None


class IdempotentExecutor:
    """
    幂等执行器.

    确保相同输入的函数只执行一次，支持缓存结果。
    """

    def __init__(self, cache_dir: str = "~/.fund_cli/idempotency"):
        """
        初始化幂等执行器.

        Args:
            cache_dir: 缓存目录
        """
        from pathlib import Path

        self._cache_dir = Path(cache_dir).expanduser()
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = Cache(str(self._cache_dir))
        self._request_lock = RequestLock()

    def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        cache_ttl: int = 3600,
        lock_timeout: float = 30.0,
        **kwargs: Any,
    ) -> T:
        """
        幂等执行函数.

        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
            cache_ttl: 结果缓存时间（秒）
            lock_timeout: 锁超时时间（秒）

        Returns:
            函数返回值
        """
        # 生成幂等性键
        idempotency_key = IdempotencyKey.generate(func.__name__, *args, **kwargs)
        cache_key = f"result:{idempotency_key}"

        # 先检查缓存
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            logger.debug("命中幂等性缓存: %s", func.__name__)
            return cached_result["result"]

        # 获取锁
        lock_key = f"exec:{idempotency_key}"
        if not self._request_lock.acquire(lock_key, timeout=lock_timeout):
            # 获取锁失败，等待其他线程完成并获取结果
            for _ in range(int(lock_timeout * 10)):
                cached_result = self._cache.get(cache_key)
                if cached_result is not None:
                    return cached_result["result"]
                time.sleep(0.1)

            raise TimeoutError(f"等待幂等执行结果超时: {func.__name__}")

        try:
            # 双重检查缓存
            cached_result = self._cache.get(cache_key)
            if cached_result is not None:
                return cached_result["result"]

            # 执行函数
            logger.debug("执行幂等函数: %s", func.__name__)
            result = func(*args, **kwargs)

            # 缓存结果
            self._cache.set(
                cache_key,
                {"result": result, "timestamp": time.time()},
                expire=cache_ttl,
            )

            return result

        finally:
            self._request_lock.release(lock_key)

    def clear_cache(self, func_name: str | None = None) -> None:
        """
        清除幂等性缓存.

        Args:
            func_name: 函数名称，None则清除所有
        """
        if func_name is None:
            self._cache.clear()
        else:
            # 清除特定函数的缓存
            for key in list(self._cache.iterkeys()):
                if key.startswith(f"result:{func_name}:"):
                    self._cache.delete(key)


# 全局幂等执行器实例
_executor: IdempotentExecutor | None = None


def get_idempotent_executor() -> IdempotentExecutor:
    """获取全局幂等执行器实例."""
    global _executor
    if _executor is None:
        _executor = IdempotentExecutor()
    return _executor


def idempotent(
    cache_ttl: int = 3600,
    lock_timeout: float = 30.0,
):
    """
    幂等装饰器.

    Args:
        cache_ttl: 结果缓存时间（秒）
        lock_timeout: 锁超时时间（秒）

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            executor = get_idempotent_executor()
            return executor.execute(func, *args, cache_ttl=cache_ttl, lock_timeout=lock_timeout, **kwargs)

        return wrapper

    return decorator
