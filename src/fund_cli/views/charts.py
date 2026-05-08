"""
图表渲染模块

提供图表生成功能。
"""

import pandas as pd


class ChartRenderer:
    """
    图表渲染器

    使用 Plotly 生成交互式图表。
    """

    def __init__(self):
        """初始化图表渲染器"""
        self._plotly = None

    def _get_plotly(self):
        """延迟加载 Plotly"""
        if self._plotly is None:
            try:
                import plotly.graph_objects as go

                self._plotly = go
            except ImportError as e:
                raise ImportError("Plotly 未安装，请运行: pip install plotly") from e
        return self._plotly

    def render_nav_chart(
        self,
        nav_data: pd.DataFrame,
        title: str = "净值走势",
    ) -> dict:
        """
        渲染净值走势图

        Args:
            nav_data: 净值数据
            title: 图表标题

        Returns:
            Plotly Figure 字典
        """
        go = self._get_plotly()

        fig = go.Figure()

        # 单位净值
        fig.add_trace(
            go.Scatter(
                x=nav_data["nav_date"],
                y=nav_data["unit_nav"],
                mode="lines",
                name="单位净值",
                line={"color": "blue"},
            )
        )

        # 累计净值
        if "accumulated_nav" in nav_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=nav_data["nav_date"],
                    y=nav_data["accumulated_nav"],
                    mode="lines",
                    name="累计净值",
                    line={"color": "green", "dash": "dot"},
                )
            )

        fig.update_layout(
            title=title,
            xaxis_title="日期",
            yaxis_title="净值",
            hovermode="x unified",
        )

        return fig.to_dict()

    def render_drawdown_chart(
        self,
        drawdown: pd.Series,
        title: str = "回撤分析",
    ) -> dict:
        """
        渲染回撤图表

        Args:
            drawdown: 回撤序列
            title: 图表标题

        Returns:
            Plotly Figure 字典
        """
        go = self._get_plotly()

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown * 100,
                mode="lines",
                name="回撤",
                fill="tozeroy",
                line={"color": "red"},
            )
        )

        fig.update_layout(
            title=title,
            xaxis_title="日期",
            yaxis_title="回撤(%)",
            hovermode="x unified",
        )

        return fig.to_dict()
