"""
数据管理器

统一管理数据源，提供数据访问接口。
"""

from datetime import date
from typing import Any

import pandas as pd

from fund_cli.config import get_config
from fund_cli.data.adapters.akshare_adapter import AKShareAdapter
from fund_cli.data.base import DataSourceAdapter, DataSourceError
from fund_cli.data.cache import DataCache


class DataManager:
    """
    数据管理器

    统一管理多个数据源，提供：
    - 自动数据源选择
    - 数据缓存
    - 统一的数据访问接口
    """

    def __init__(
        self,
        cache: DataCache | None = None,
        primary_source: str = "akshare",
    ):
        """
        初始化数据管理器

        Args:
            cache: 缓存管理器
            primary_source: 主数据源名称
        """
        self.config = get_config()
        self._cache = cache or DataCache(
            cache_dir=self.config.data.cache_dir,
            default_ttl=self.config.data.cache_ttl,
        )
        self._primary_source = primary_source
        self._adapters: dict[str, DataSourceAdapter] = {}

        # 初始化数据源
        self._init_adapters()

    def _init_adapters(self) -> None:
        """初始化数据源适配器"""
        # AKShare（默认数据源）
        if self.config.data.akshare_enabled:
            self._adapters["akshare"] = AKShareAdapter(cache=self._cache)

    def get_adapter(self, source: str | None = None) -> DataSourceAdapter:
        """
        获取数据源适配器

        Args:
            source: 数据源名称，默认使用主数据源

        Returns:
            数据源适配器实例

        Raises:
            DataSourceError: 数据源不可用
        """
        source_name = source or self._primary_source

        if source_name not in self._adapters:
            raise DataSourceError(f"数据源 {source_name} 未配置或不可用")

        adapter = self._adapters[source_name]

        if not adapter.is_available():
            raise DataSourceError(f"数据源 {source_name} 不可用")

        return adapter

    # ========== 基金数据接口 ==========

    def get_fund_info(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金基础信息

        Args:
            fund_code: 基金代码

        Returns:
            基金信息字典
        """
        return self.get_adapter().get_fund_info(fund_code)

    def get_fund_nav(
        self,
        fund_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基金净值数据

        Args:
            fund_code: 基金代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            净值数据 DataFrame
        """
        return self.get_adapter().get_fund_nav(fund_code, start_date, end_date)

    def search_funds(
        self,
        fund_type: str | None = None,
        company: str | None = None,
        min_scale: float | None = None,
        max_scale: float | None = None,
        keyword: str | None = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        搜索基金

        Args:
            fund_type: 基金类型
            company: 基金公司
            min_scale: 最小规模
            max_scale: 最大规模
            keyword: 关键词
            limit: 返回数量限制

        Returns:
            基金列表 DataFrame
        """
        return self.get_adapter().search_funds(
            fund_type=fund_type,
            company=company,
            min_scale=min_scale,
            max_scale=max_scale,
            keyword=keyword,
            limit=limit,
        )

    def get_fund_list(self, fund_type: str | None = None) -> pd.DataFrame:
        """
        获取基金列表

        Args:
            fund_type: 基金类型筛选

        Returns:
            基金列表 DataFrame
        """
        return self.get_adapter().get_fund_list(fund_type)

    def get_benchmark_nav(
        self,
        benchmark_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基准指数数据

        Args:
            benchmark_code: 基准指数代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            基准数据 DataFrame
        """
        return self.get_adapter().get_benchmark_nav(benchmark_code, start_date, end_date)

    def get_fund_holdings(
        self,
        fund_code: str,
        report_date: date | None = None,
    ) -> pd.DataFrame:
        """获取基金持仓数据"""
        return self.get_adapter().get_fund_holdings(fund_code, report_date)

    def get_fund_manager(self, fund_code: str) -> dict[str, Any]:
        """获取基金经理信息"""
        return self.get_adapter().get_fund_manager(fund_code)

    def get_fund_fee(self, fund_code: str) -> dict[str, Any]:
        """获取基金费率信息"""
        return self.get_adapter().get_fund_fee(fund_code)

    def get_fund_rating(self, fund_code: str) -> int | None:
        """获取基金评级"""
        return self.get_adapter().get_fund_rating(fund_code)

    def batch_get_fund_nav(
        self,
        fund_codes: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, pd.DataFrame]:
        """批量获取基金净值"""
        return self.get_adapter().batch_get_fund_nav(fund_codes, start_date, end_date)

    # ========== 缓存管理 ==========

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()

    def get_cache_stats(self) -> dict:
        """获取缓存统计"""
        return self._cache.get_stats()

    def __repr__(self) -> str:
        sources = list(self._adapters.keys())
        return f"DataManager(sources={sources}, primary={self._primary_source})"


# 全局数据管理器实例
_data_manager: DataManager | None = None


def get_data_manager() -> DataManager:
    """获取数据管理器实例（单例）"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager
