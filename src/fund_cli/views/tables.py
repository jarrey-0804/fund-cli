"""
表格渲染模块

提供 Rich 表格渲染功能。
"""

import pandas as pd
from rich.console import Console
from rich.table import Table


class TableRenderer:
    """
    表格渲染器

    使用 Rich 库渲染美观的表格输出。
    """

    def __init__(self, console: Console | None = None):
        """
        初始化表格渲染器

        Args:
            console: Rich Console 实例
        """
        self.console = console or Console()

    def render_fund_list(
        self,
        df: pd.DataFrame,
        title: str = "基金列表",
    ) -> Table:
        """
        渲染基金列表表格

        Args:
            df: 基金数据 DataFrame
            title: 表格标题

        Returns:
            Rich Table 对象
        """
        table = Table(title=title)

        # 定义列
        columns = [
            ("code", "基金代码", "cyan"),
            ("name", "基金名称", "white"),
            ("type", "基金类型", "blue"),
            ("scale", "规模(亿)", "green"),
            ("company", "基金公司", "yellow"),
        ]

        for col_name, col_title, col_style in columns:
            if col_name in df.columns:
                table.add_column(col_title, style=col_style)

        # 添加行
        for _, row in df.iterrows():
            values = []
            for col_name, _, _ in columns:
                if col_name in row:
                    val = row[col_name]
                    if pd.isna(val):
                        values.append("-")
                    elif col_name == "scale":
                        values.append(f"{val:.2f}" if val else "-")
                    else:
                        values.append(str(val)[:20])
            if values:
                table.add_row(*values)

        return table

    def render_analysis_result(
        self,
        metrics: dict,
        title: str = "分析结果",
    ) -> Table:
        """
        渲染分析结果表格

        Args:
            metrics: 指标字典
            title: 表格标题

        Returns:
            Rich Table 对象
        """
        table = Table(title=title)

        table.add_column("指标", style="cyan")
        table.add_column("值", style="green")

        # 指标名称映射
        metric_names = {
            "total_return": "总收益率",
            "cagr": "年化收益率",
            "volatility": "年化波动率",
            "max_drawdown": "最大回撤",
            "sharpe": "夏普比率",
            "sortino": "索提诺比率",
            "calmar": "卡玛比率",
            "alpha": "Alpha",
            "beta": "Beta",
            "var_95": "VaR(95%)",
        }

        for key, name in metric_names.items():
            if key in metrics:
                value = metrics[key]
                if value is not None:
                    if isinstance(value, float):
                        if "return" in key or "drawdown" in key or "volatility" in key:
                            value_str = f"{value:.2f}%"
                        else:
                            value_str = f"{value:.2f}"
                    else:
                        value_str = str(value)
                else:
                    value_str = "-"
                table.add_row(name, value_str)

        return table
