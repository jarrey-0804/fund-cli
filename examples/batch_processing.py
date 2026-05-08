"""
Fund CLI 示例 - 批量处理

演示如何批量分析多只基金并导出结果。
"""

from datetime import date, timedelta

from fund_cli.core.data_manager import DataManager
from fund_cli.analysis.performance import PerformanceAnalyzer


def batch_analyze(fund_codes: list, output_file: str = None):
    """
    批量分析基金

    Args:
        fund_codes: 基金代码列表
        output_file: 输出CSV文件路径（可选）
    """
    dm = DataManager()
    analyzer = PerformanceAnalyzer()

    end = date.today()
    start = end - timedelta(days=365)

    results = []
    for code in fund_codes:
        try:
            info = dm.get_fund_info(code)
            nav_df = dm.get_fund_nav(code, start_date=start, end_date=end)

            if nav_df.empty:
                continue

            nav_series = nav_df.set_index("nav_date")["unit_nav"]
            returns = nav_series.pct_change().dropna()
            metrics = analyzer.analyze(returns)

            results.append(
                {
                    "code": code,
                    "name": info.get("name", ""),
                    "total_return": metrics.get("total_return", 0),
                    "sharpe": metrics.get("sharpe", 0),
                    "max_drawdown": metrics.get("max_drawdown", 0),
                    "volatility": metrics.get("volatility", 0),
                }
            )
            print(f"  {code} - {info.get('name', '')} 完成")

        except Exception as e:
            print(f"  {code} - 失败: {e}")

    if not results:
        print("无结果")
        return

    import pandas as pd

    df = pd.DataFrame(results)
    print(f"\n共分析 {len(results)} 只基金")
    print(df.to_string(index=False))

    if output_file:
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"\n已导出到: {output_file}")


if __name__ == "__main__":
    batch_analyze(["000001", "000002", "000003"], output_file="batch_result.csv")
