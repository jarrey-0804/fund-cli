"""
测试公共 fixtures
"""

import warnings

import numpy as np
import pandas as pd
import pytest

warnings.filterwarnings("ignore", message=r".*allowed_objects.*will change.*")


@pytest.fixture
def temp_cache_dir(tmp_path):
    """提供临时缓存目录"""
    return tmp_path / "cache"


@pytest.fixture
def sample_fund_info():
    """提供示例基金信息字典，用于创建 FundInfo 模型"""
    return {
        "code": "000001",
        "name": "华夏成长混合",
        "type": "混合型",
        "establish_date": "2005-01-12",
        "manager": "张三",
        "company": "华夏基金",
        "scale": 50.5,
        "return_1m": 2.3,
        "return_3m": 5.1,
        "return_6m": 8.7,
        "return_1y": 15.2,
        "return_3y": 32.6,
        "return_this_year": 12.0,
        "max_drawdown": -15.3,
        "sharpe_ratio": 1.2,
    }


@pytest.fixture
def sample_nav_data():
    """提供示例净值 DataFrame，用于缓存和报告测试"""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=30, freq="B")
    nav_values = 1.0 + np.cumsum(np.random.normal(0.001, 0.02, 30))
    return pd.DataFrame(
        {
            "nav_date": dates,
            "unit_nav": nav_values,
            "accumulated_nav": nav_values * 1.5,
        }
    )


@pytest.fixture
def sample_returns():
    """提供示例日收益率序列，用于业绩和风险分析测试"""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=252, freq="B")
    returns = np.random.normal(0.0005, 0.015, 252)
    return pd.Series(returns, index=dates, name="daily_return")


@pytest.fixture
def sample_benchmark_returns():
    """提供示例基准日收益率序列，用于相对指标分析测试"""
    np.random.seed(123)
    dates = pd.date_range("2024-01-01", periods=252, freq="B")
    returns = np.random.normal(0.0003, 0.012, 252)
    return pd.Series(returns, index=dates, name="benchmark_return")
