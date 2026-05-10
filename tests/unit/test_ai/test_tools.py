"""
AI 工具测试.

测试 fund_cli.ai.tools 模块。
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

from fund_cli.ai.tools import (
    _period_to_dates,
)


class TestPeriodToDates:
    """测试 _period_to_dates 函数."""

    def test_period_1m(self):
        """测试 1 个月周期."""
        start, end = _period_to_dates("1m")
        assert start is not None
        assert end is None

    def test_period_3m(self):
        """测试 3 个月周期."""
        start, end = _period_to_dates("3m")
        assert start is not None
        assert end is None

    def test_period_1y(self):
        """测试 1 年周期."""
        start, end = _period_to_dates("1y")
        assert start is not None
        assert end is None

    def test_period_ytd(self):
        """测试 YTD 周期."""
        start, end = _period_to_dates("ytd")
        assert start is not None
        assert end is None
        # YTD 应该从年初开始
        from datetime import date
        assert start.year == date.today().year
        assert start.month == 1
        assert start.day == 1

    def test_period_invalid(self):
        """测试无效周期."""
        start, end = _period_to_dates("invalid")
        # 应该返回默认值（1年）
        assert start is not None


class TestToolsExist:
    """测试工具存在."""

    def test_tools_import(self):
        """测试工具可以导入."""
        from fund_cli.ai.tools import (
            get_fund_basic_info,
            get_fund_nav_history,
            get_fund_performance,
            search_funds,
        )
        # 工具使用 @tool 装饰器，返回 StructuredTool 对象
        assert get_fund_basic_info is not None
        assert get_fund_nav_history is not None
        assert get_fund_performance is not None
        assert search_funds is not None
