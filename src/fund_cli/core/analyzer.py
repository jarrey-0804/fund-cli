"""
分析引擎基类

定义分析引擎的标准接口。
"""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class Analyzer(ABC):
    """
    分析引擎基类

    所有分析引擎必须继承此类。
    """

    @abstractmethod
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs,
    ) -> dict[str, Any]:
        """
        执行分析

        Args:
            data: 输入数据
            **kwargs: 额外参数

        Returns:
            分析结果字典
        """
        pass

    @abstractmethod
    def get_metrics(self) -> list:
        """
        获取可计算的指标列表

        Returns:
            指标名称列表
        """
        pass
