"""
Wind 数据源适配器（占位）

Wind 是商业数据源，需要授权使用。
此文件为接口预留，实际实现需要 Wind Python API。
"""

from typing import Any

import pandas as pd

from fund_cli.data.base import (
    DataSourceAdapter,
    DataSourceError,
)
from fund_cli.data.cache import DataCache


class WindAdapter(DataSourceAdapter):
    """
    Wind 数据源适配器（占位实现）

    Wind 是商业数据源，需要授权和 Wind Python API。
    当前为接口预留，实际使用需要：
    1. 安装 Wind Python API
    2. 配置有效的 Wind 账号
    """

    def __init__(self, cache: DataCache | None = None):
        super().__init__("wind")
        self._cache = cache

    def is_available(self) -> bool:
        """检查 Wind 是否可用"""
        try:
            from WindPy import w  # noqa: F401

            return w.isconnected()
        except Exception:
            return False

    def get_fund_info(self, fund_code: str) -> dict[str, Any]:
        """获取基金基础信息"""
        raise DataSourceError("Wind 数据源暂未实现，请使用 AKShare 或 Tushare 数据源")

    def get_fund_nav(
        self,
        fund_code: str,
        start_date: Any | None = None,
        end_date: Any | None = None,
    ) -> pd.DataFrame:
        """获取基金净值数据"""
        raise DataSourceError("Wind 数据源暂未实现，请使用 AKShare 或 Tushare 数据源")

    def search_funds(
        self,
        fund_type: str | None = None,
        company: str | None = None,
        min_scale: float | None = None,
        max_scale: float | None = None,
        keyword: str | None = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """搜索基金"""
        raise DataSourceError("Wind 数据源暂未实现，请使用 AKShare 或 Tushare 数据源")

    def get_fund_list(self, fund_type: str | None = None) -> pd.DataFrame:
        """获取基金列表"""
        raise DataSourceError("Wind 数据源暂未实现，请使用 AKShare 或 Tushare 数据源")

    def get_benchmark_nav(
        self,
        benchmark_code: str,
        start_date: Any | None = None,
        end_date: Any | None = None,
    ) -> pd.DataFrame:
        """获取基准指数数据"""
        raise DataSourceError("Wind 数据源暂未实现，请使用 AKShare 或 Tushare 数据源")
