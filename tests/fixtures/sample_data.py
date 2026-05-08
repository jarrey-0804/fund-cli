"""
测试夹具数据

提供共享的测试数据文件。
"""

from pathlib import Path

import numpy as np
import pandas as pd

FIXTURES_DIR = Path(__file__).parent


def get_sample_nav_csv_path() -> Path:
    """获取示例净值CSV文件路径"""
    return FIXTURES_DIR / "sample_nav.csv"


def get_sample_fund_list_csv_path() -> Path:
    """获取示例基金列表CSV文件路径"""
    return FIXTURES_DIR / "sample_fund_list.csv"


def generate_sample_nav_csv() -> pd.DataFrame:
    """生成示例净值CSV数据"""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=252, freq="B")
    nav_values = 1.0 + np.cumsum(np.random.normal(0.001, 0.02, 252))

    df = pd.DataFrame(
        {
            "fund_code": "000001",
            "nav_date": dates.strftime("%Y-%m-%d"),
            "unit_nav": nav_values,
            "accumulated_nav": nav_values * 1.5,
            "daily_return": np.random.normal(0.001, 0.02, 252) * 100,
        }
    )
    return df


def generate_sample_fund_list_csv() -> pd.DataFrame:
    """生成示例基金列表CSV数据"""
    df = pd.DataFrame(
        {
            "code": ["000001", "000002", "000003"],
            "name": ["华夏成长混合", "易方达策略成长", "嘉实增长混合"],
            "type": ["混合型", "混合型", "混合型"],
            "company": ["华夏基金", "易方达基金", "嘉实基金"],
            "scale": [50.5, 120.3, 85.7],
        }
    )
    return df


def save_fixtures() -> None:
    """保存测试夹具文件"""
    nav_df = generate_sample_nav_csv()
    nav_df.to_csv(get_sample_nav_csv_path(), index=False)

    fund_df = generate_sample_fund_list_csv()
    fund_df.to_csv(get_sample_fund_list_csv_path(), index=False)


if __name__ == "__main__":
    save_fixtures()
    print(f"Fixtures saved to {FIXTURES_DIR}")
