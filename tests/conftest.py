"""
Pytest 配置和共享 Fixtures
"""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_fund_info() -> dict:
    """示例基金信息"""
    return {
        "code": "000001",
        "name": "华夏成长混合",
        "type": "混合型",
        "establish_date": date(2001, 12, 18),
        "manager": "张三",
        "company": "华夏基金",
        "scale": 50.5,
    }


@pytest.fixture
def sample_nav_data() -> pd.DataFrame:
    """示例净值数据"""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=252, freq="B")
    nav_values = 1.0 + np.cumsum(np.random.normal(0.001, 0.02, 252))

    return pd.DataFrame(
        {
            "fund_code": "000001",
            "nav_date": dates,
            "unit_nav": nav_values,
            "accumulated_nav": nav_values * 1.5,
            "daily_return": np.random.normal(0.001, 0.02, 252) * 100,
        }
    )


@pytest.fixture
def sample_returns() -> pd.Series:
    """示例收益率序列"""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=252, freq="B")
    returns = pd.Series(np.random.normal(0.001, 0.02, 252), index=dates)
    returns.name = "daily_return"
    return returns


@pytest.fixture
def sample_benchmark_returns() -> pd.Series:
    """示例基准收益率序列"""
    np.random.seed(43)
    dates = pd.date_range("2023-01-01", periods=252, freq="B")
    returns = pd.Series(np.random.normal(0.0008, 0.015, 252), index=dates)
    returns.name = "benchmark_return"
    return returns


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """临时缓存目录"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def sample_holdings_data() -> pd.DataFrame:
    """示例持仓数据"""
    return pd.DataFrame(
        {
            "fund_code": "000001",
            "stock_code": ["600519", "000858", "601318", "600036", "000333"],
            "stock_name": ["贵州茅台", "五粮液", "中国平安", "招商银行", "美的集团"],
            "weight": [9.5, 7.2, 6.8, 5.5, 4.3],
            "market_value": [50000.0, 38000.0, 36000.0, 29000.0, 22000.0],
            "industry": ["食品饮料", "食品饮料", "非银金融", "银行", "家用电器"],
            "report_date": [date(2024, 6, 30)] * 5,
        }
    )


@pytest.fixture
def sample_multi_fund_returns() -> pd.DataFrame:
    """多基金收益率数据（用于优化测试）"""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=252, freq="B")
    return pd.DataFrame(
        {
            "000001": np.random.normal(0.001, 0.02, 252),
            "000002": np.random.normal(0.0008, 0.015, 252),
            "000003": np.random.normal(0.0012, 0.025, 252),
        },
        index=dates,
    )


@pytest.fixture
def sample_manager_info() -> dict:
    """示例基金经理信息"""
    return {
        "name": "张三",
        "fund_code": "000001",
        "fund_name": "华夏成长混合",
        "company": "华夏基金",
        "start_date": date(2020, 1, 15),
        "tenure_days": 1600,
        "total_return": 25.5,
        "annual_return": 8.2,
    }
