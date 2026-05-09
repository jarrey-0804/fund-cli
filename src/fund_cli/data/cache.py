"""
数据缓存管理

使用 DiskCache 实现数据缓存，支持过期时间和持久化。
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
from diskcache import Cache


class DataCache:
    """
    数据缓存管理器

    使用 DiskCache 实现数据缓存，支持：
    - 过期时间设置
    - 持久化存储
    - 自动序列化/反序列化
    """

    def __init__(
        self,
        cache_dir: str = "~/.fund_cli/cache",
        default_ttl: int = 3600,
    ):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录
            default_ttl: 默认过期时间（秒）
        """
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self._cache = Cache(str(self.cache_dir))

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
        return {
            "size": len(self._cache),
            "volume": self._cache.volume(),
            "directory": str(self.cache_dir),
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
        pass

    def __repr__(self) -> str:
        return f"DataCache(directory={self.cache_dir}, size={len(self._cache)})"
