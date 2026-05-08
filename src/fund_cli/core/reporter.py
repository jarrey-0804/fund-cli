"""
报告生成器基类

定义报告生成的标准接口。
"""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class Reporter(ABC):
    """
    报告生成器基类

    所有报告生成器必须继承此类。
    """

    @abstractmethod
    def generate(
        self,
        fund_code: str,
        metrics: dict[str, Any],
        nav_data: pd.DataFrame | None = None,
        benchmark_data: pd.DataFrame | None = None,
        **kwargs,
    ) -> str:
        """
        生成报告

        Args:
            fund_code: 基金代码
            metrics: 分析指标字典
            nav_data: 净值数据
            benchmark_data: 基准数据
            **kwargs: 额外参数

        Returns:
            报告内容字符串
        """
        pass

    @abstractmethod
    def save(
        self,
        content: str,
        output_path: str,
    ) -> None:
        """
        保存报告到文件

        Args:
            content: 报告内容
            output_path: 输出文件路径
        """
        pass

    @abstractmethod
    def get_formats(self) -> list:
        """
        获取支持的报告格式

        Returns:
            格式列表（如 ['html', 'markdown', 'pdf']）
        """
        pass
