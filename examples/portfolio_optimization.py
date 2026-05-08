"""
Fund CLI 示例 - 组合分析

演示如何使用组合分析引擎分析多资产组合。
"""

from datetime import date, timedelta

import pandas as pd
import numpy as np

from fund_cli.core.data_manager import DataManager
from fund_cli.analysis.portfolio import PortfolioAnalyzer


def portfolio_analysis(fund_codes: list = None):
    """
    组合分析示例

    Args:
        fund_codes: 基金代码列表
    """
    if fund_codes is None:
        fund_codes = ["000001", "000002"]

    dm = DataManager()
    analyzer = PortfolioAnalyzer()

    # 获取各基金净值数据
    end = date.today()
    start = end - timedelta(days=365)

    returns_dict = {}
    for code in fund_codes:
        nav_df = dm.get_fund_nav(code, start_date=start, end_date=end)
        if not nav_df.empty:
            nav_series = nav_df.set_index("nav_date")["unit_nav"]
            returns_dict[code] = nav_series.pct_change().dropna()

    if not returns_dict:
        print("无数据")
        return

    # 合并为 DataFrame
    returns_df = pd.DataFrame(returns_dict)

    # 等权分析
    print("=== 等权组合分析 ===")
    result = analyzer.analyze(returns_df)
    print(f"资产数量: {result['asset_count']}")
    print(f"组合收益: {result['portfolio_return']:.2f}%")
    print(f"组合波动: {result['portfolio_volatility']:.2f}%")
    print(f"夏普比率: {result['portfolio_sharpe']:.2f}")
    print(f"分散度: {result['diversification_ratio']:.2f}")
    print(f"平均相关性: {result['average_correlation']:.2f}")


if __name__ == "__main__":
    portfolio_analysis()
