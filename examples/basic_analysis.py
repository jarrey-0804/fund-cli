"""
Fund CLI 示例 - 基础分析

演示如何使用 Fund CLI 的 Python API 进行基金分析。
"""

from fund_cli.core.data_manager import DataManager
from fund_cli.analysis.performance import PerformanceAnalyzer
from fund_cli.analysis.risk import RiskAnalyzer


def basic_analysis(fund_code: str = "000001"):
    """
    基础基金分析示例

    Args:
        fund_code: 基金代码
    """
    # 1. 初始化
    dm = DataManager()
    perf_analyzer = PerformanceAnalyzer()
    risk_analyzer = RiskAnalyzer()

    # 2. 获取基金信息
    print(f"=== 基金 {fund_code} 分析 ===")
    info = dm.get_fund_info(fund_code)
    print(f"名称: {info.get('name')}")
    print(f"类型: {info.get('type')}")
    print(f"经理: {info.get('manager')}")

    # 3. 获取净值数据
    from datetime import date, timedelta

    end = date.today()
    start = end - timedelta(days=365)
    nav_df = dm.get_fund_nav(fund_code, start_date=start, end_date=end)

    if nav_df.empty:
        print("无净值数据")
        return

    # 4. 计算收益率
    nav_series = nav_df.set_index("nav_date")["unit_nav"]
    returns = nav_series.pct_change().dropna()

    # 5. 业绩分析
    perf_metrics = perf_analyzer.analyze(returns)
    print(f"\n总收益率: {perf_metrics.get('total_return', 0):.2f}%")
    print(f"夏普比率: {perf_metrics.get('sharpe', 0):.2f}")
    print(f"最大回撤: {perf_metrics.get('max_drawdown', 0):.2f}%")

    # 6. 风险分析
    risk_metrics = risk_analyzer.analyze(returns)
    print(f"\n年化波动率: {risk_metrics.get('volatility_annual', 0):.2f}%")
    print(f"VaR(95%): {risk_metrics.get('var_95', 0):.2f}%")
    print(f"VaR(99%): {risk_metrics.get('var_99', 0):.2f}%")


if __name__ == "__main__":
    basic_analysis()
