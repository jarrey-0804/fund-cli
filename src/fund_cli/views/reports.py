"""
报告视图模块

提供报告生成功能。
"""

from datetime import datetime

import pandas as pd


class ReportRenderer:
    """
    报告渲染器

    生成各类分析报告。
    """

    def generate_html_report(
        self,
        fund_code: str,
        fund_name: str,
        metrics: dict,
        nav_data: pd.DataFrame | None = None,
    ) -> str:
        """
        生成 HTML 分析报告

        Args:
            fund_code: 基金代码
            fund_name: 基金名称
            metrics: 分析指标
            nav_data: 净值数据

        Returns:
            HTML 字符串
        """
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>基金分析报告 - {fund_code}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f5f5f5; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                .footer {{ margin-top: 40px; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <h1>基金分析报告</h1>
            <p><strong>基金代码:</strong> {fund_code}</p>
            <p><strong>基金名称:</strong> {fund_name}</p>
            <p><strong>报告日期:</strong> {report_date}</p>

            <h2>业绩指标</h2>
            <table>
                <tr><th>指标</th><th>值</th></tr>
                <tr><td>总收益率</td><td>{metrics.get("total_return", 0):.2f}%</td></tr>
                <tr><td>年化收益率</td><td>{metrics.get("cagr", 0):.2f}%</td></tr>
                <tr><td>年化波动率</td><td>{metrics.get("volatility", 0):.2f}%</td></tr>
                <tr><td>最大回撤</td><td>{metrics.get("max_drawdown", 0):.2f}%</td></tr>
                <tr><td>夏普比率</td><td>{metrics.get("sharpe", 0):.2f}</td></tr>
                <tr><td>索提诺比率</td><td>{metrics.get("sortino", 0):.2f}</td></tr>
            </table>

            <div class="footer">
                <p>本报告由 Fund CLI 自动生成，仅供参考。</p>
            </div>
        </body>
        </html>
        """

        return html
