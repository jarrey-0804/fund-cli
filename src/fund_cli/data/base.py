"""
数据源适配器基类

定义数据源适配器的标准接口，支持多数据源扩展。
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

import pandas as pd


class DataSourceAdapter(ABC):
    """
    数据源适配器基类

    所有数据源适配器必须继承此类并实现所有抽象方法。
    """

    def __init__(self, name: str):
        """
        初始化数据源适配器

        Args:
            name: 数据源名称
        """
        self._name = name

    @property
    def name(self) -> str:
        """数据源名称"""
        return self._name

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查数据源是否可用

        Returns:
            数据源是否可用
        """
        pass

    @abstractmethod
    def get_fund_info(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金基础信息

        Args:
            fund_code: 基金代码（6位数字）

        Returns:
            基金基础信息字典，包含：
            - code: 基金代码
            - name: 基金名称
            - type: 基金类型
            - establish_date: 成立日期
            - manager: 基金经理
            - company: 基金公司
            - scale: 规模（亿元）

        Raises:
            DataNotFoundError: 基金不存在
            DataSourceError: 数据源错误
        """
        pass

    @abstractmethod
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
            start_date: 开始日期，默认为基金成立日
            end_date: 结束日期，默认为最新日期

        Returns:
            净值数据DataFrame，包含列：
            - nav_date: 净值日期
            - unit_nav: 单位净值
            - accumulated_nav: 累计净值
            - daily_return: 日收益率（可选）

        Raises:
            DataNotFoundError: 基金不存在
            DataSourceError: 数据源错误
        """
        pass

    @abstractmethod
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
        搜索/筛选基金

        Args:
            fund_type: 基金类型
            company: 基金公司
            min_scale: 最小规模（亿元）
            max_scale: 最大规模（亿元）
            keyword: 关键词搜索
            limit: 返回数量限制

        Returns:
            基金列表DataFrame
        """
        pass

    @abstractmethod
    def get_fund_list(self, fund_type: str | None = None) -> pd.DataFrame:
        """
        获取基金列表

        Args:
            fund_type: 基金类型筛选

        Returns:
            基金列表DataFrame
        """
        pass

    @abstractmethod
    def get_benchmark_nav(
        self,
        benchmark_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基准指数净值数据

        Args:
            benchmark_code: 基准指数代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            基准净值数据DataFrame
        """
        pass

    @abstractmethod
    def get_fund_holdings(
        self,
        fund_code: str,
        report_date: date | None = None,
    ) -> pd.DataFrame:
        """获取基金持仓数据"""
        pass

    @abstractmethod
    def get_fund_manager(self, fund_code: str) -> dict[str, Any]:
        """获取基金经理信息"""
        pass

    @abstractmethod
    def get_fund_fee(self, fund_code: str) -> dict[str, Any]:
        """获取基金费率信息"""
        pass

    @abstractmethod
    def get_fund_rating(self, fund_code: str) -> int | None:
        """获取基金评级"""
        pass

    @abstractmethod
    def batch_get_fund_nav(
        self,
        fund_codes: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, pd.DataFrame]:
        """批量获取基金净值数据"""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self._name!r})"


class DataSourceError(Exception):
    """数据源错误"""

    pass


class DataNotFoundError(Exception):
    """数据未找到错误"""

    pass


class NetworkError(Exception):
    """网络错误"""

    pass
