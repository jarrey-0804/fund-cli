"""
数据缓存管理

使用 DiskCache 实现数据缓存，支持过期时间和持久化。
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
from diskcache import Cache

logger = logging.getLogger(__name__)

# 缓存数据版本号，用于数据模型变更时自动失效旧缓存
CACHE_VERSION = "1.0"


class DataCache:
    """
    数据缓存管理器

    使用 DiskCache 实现数据缓存，支持：
    - 过期时间设置
    - 持久化存储
    - 自动序列化/反序列化
    - 版本控制
    - 容量限制
    """

    def __init__(
        self,
        cache_dir: str = "~/.fund_cli/cache",
        default_ttl: int = 3600,
        size_limit: int = 2**30,  # 1GB 默认容量限制
    ):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录
            default_ttl: 默认过期时间（秒）
            size_limit: 缓存容量限制（字节），默认 1GB
        """
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self.size_limit = size_limit
        self._cache = Cache(str(self.cache_dir), size_limit=size_limit)

        # 版本检查：如果版本不匹配，清空缓存
        self._check_version()

    def _check_version(self) -> None:
        """检查缓存版本，不匹配则清空缓存."""
        version_key = "__cache_version__"
        cached_version = self._cache.get(version_key)

        if cached_version != CACHE_VERSION:
            if cached_version is not None:
                logger.info(f"缓存版本变更: {cached_version} -> {CACHE_VERSION}，清空旧缓存")
                self._cache.clear()
            else:
                logger.debug(f"初始化缓存版本: {CACHE_VERSION}")

            self._cache.set(version_key, CACHE_VERSION)

    def get_cache_version(self) -> str:
        """获取当前缓存版本."""
        return CACHE_VERSION

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        生成缓存键

        Args:
            prefix: 键前缀
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            缓存键字符串
        """
        # 将参数序列化为字符串
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"{prefix}:{key_hash}"

    def get(self, key: str) -> Any | None:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回 None
        """
        return self._cache.get(key)

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认使用 default_ttl
        """
        expire = ttl if ttl is not None else self.default_ttl
        self._cache.set(key, value, expire=expire)

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        return self._cache.delete(key)

    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            缓存是否存在
        """
        return key in self._cache

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()

    def get_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        volume = self._cache.volume()
        size_limit_mb = self.size_limit / (1024 * 1024)
        volume_mb = volume / (1024 * 1024)

        return {
            "size": len(self._cache),
            "volume": volume,
            "volume_mb": round(volume_mb, 2),
            "size_limit_mb": round(size_limit_mb, 2),
            "usage_percent": round(volume / self.size_limit * 100, 2) if self.size_limit > 0 else 0,
            "directory": str(self.cache_dir),
            "version": CACHE_VERSION,
            "hit_count": getattr(self._cache, "hit_count", 0),
            "miss_count": getattr(self._cache, "miss_count", 0),
        }

    # ========== 便捷方法 ==========

    def get_fund_info(self, fund_code: str) -> dict | None:
        """获取缓存的基金信息"""
        key = f"fund_info:{fund_code}"
        return self.get(key)

    def set_fund_info(self, fund_code: str, info: dict, ttl: int | None = None) -> None:
        """缓存基金信息"""
        key = f"fund_info:{fund_code}"
        self.set(key, info, ttl)

    def get_fund_nav(self, fund_code: str, start_date: str, end_date: str) -> pd.DataFrame | None:
        """获取缓存的净值数据"""
        key = f"fund_nav:{fund_code}:{start_date}:{end_date}"
        return self.get(key)

    def set_fund_nav(
        self,
        fund_code: str,
        start_date: str,
        end_date: str,
        nav_data: pd.DataFrame,
        ttl: int | None = None,
    ) -> None:
        """缓存净值数据"""
        key = f"fund_nav:{fund_code}:{start_date}:{end_date}"
        self.set(key, nav_data, ttl)

    def get_fund_holdings(self, fund_code: str, report_date: str = "latest") -> pd.DataFrame | None:
        """获取缓存的持仓数据"""
        key = f"fund_holdings:{fund_code}:{report_date}"
        return self.get(key)

    def set_fund_holdings(
        self,
        fund_code: str,
        report_date: str,
        data: pd.DataFrame,
        ttl: int | None = None,
    ) -> None:
        """缓存持仓数据"""
        key = f"fund_holdings:{fund_code}:{report_date}"
        self.set(key, data, ttl)

    def get_fund_manager(self, fund_code: str) -> dict | None:
        """获取缓存的经理信息"""
        key = f"fund_manager:{fund_code}"
        return self.get(key)

    def set_fund_manager(self, fund_code: str, info: dict, ttl: int | None = None) -> None:
        """缓存经理信息"""
        key = f"fund_manager:{fund_code}"
        self.set(key, info, ttl)

    def __enter__(self) -> "DataCache":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文时关闭缓存连接."""
        try:
            self._cache.close()
        except Exception:
            pass

    def __repr__(self) -> str:
        return f"DataCache(directory={self.cache_dir}, size={len(self._cache)})"
