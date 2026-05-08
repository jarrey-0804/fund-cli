"""
优化引擎基类

定义组合优化引擎的标准接口。
"""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class Optimizer(ABC):
    """
    优化引擎基类

    所有优化引擎必须继承此类。
    """

    @abstractmethod
    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs,
    ) -> dict[str, Any]:
        """
        执行组合优化

        Args:
            returns: 多资产收益率 DataFrame，每列一个资产
            **kwargs: 额外参数（如目标收益率、最大回撤限制等）

        Returns:
            优化结果字典，包含：
            - weights: 各资产权重字典
            - expected_return: 预期收益率
            - expected_volatility: 预期波动率
            - sharpe_ratio: 夏普比率
        """
        pass

    @abstractmethod
    def get_methods(self) -> list[str]:
        """
        获取支持的优化方法列表

        Returns:
            方法名称列表
        """
        pass
