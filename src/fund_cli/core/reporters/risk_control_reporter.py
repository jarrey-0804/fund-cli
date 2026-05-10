"""
合规风控报告生成器.
"""

from datetime import date
from typing import Any

import pandas as pd

from fund_cli.core.reporter import Reporter


class RiskControlReporter(Reporter):
    """合规风控报告生成器 - 填充风控模板数据."""

    def generate(
        self,
        fund_code: str,
        metrics: dict[str, Any],
        nav_data: pd.DataFrame | None = None,
        benchmark_data: pd.DataFrame | None = None,
        **kwargs: Any,
    ) -> str:
        """生成风控报告，填充模板所需数据."""
        # 构建风控报告数据
        data = {
            "fund_code": fund_code,
            "report_date": date.today().strftime("%Y-%m-%d"),
            # 一、组合风险概览
            "risk_overview": self._build_risk_overview(metrics),
            # 二、集中度分析
            "concentration": self._build_concentration(metrics),
            # 三、合规检查
            "compliance_checks": self._build_compliance_checks(metrics, nav_data),
        }

        template_path = kwargs.get("template_path")
        if template_path:
            return self.render_to_template(data, template_path)

        # 默认使用内置模板
        from fund_cli.core.template_engine import get_template_engine

        engine = get_template_engine()
        return engine.render("risk_control/report.html", **data)

    def _build_risk_overview(self, metrics: dict[str, Any]) -> list[dict]:
        """构建风险概览数据."""
        items = []

        # 波动率
        vol = metrics.get("volatility")
        if vol is not None:
            status = "正常" if vol < 0.3 else "警告" if vol < 0.5 else "异常"
            items.append(
                {
                    "name": "年化波动率",
                    "value": vol,
                    "threshold": 0.3,
                    "status": status,
                }
            )

        # 最大回撤
        mdd = metrics.get("max_drawdown")
        if mdd is not None:
            status = "正常" if mdd > -0.2 else "警告" if mdd > -0.3 else "异常"
            items.append(
                {
                    "name": "最大回撤",
                    "value": mdd,
                    "threshold": -0.2,
                    "status": status,
                }
            )

        # 夏普比率
        sharpe = metrics.get("sharpe_ratio")
        if sharpe is not None:
            status = "正常" if sharpe > 0 else "警告" if sharpe > -0.5 else "异常"
            items.append(
                {
                    "name": "夏普比率",
                    "value": sharpe,
                    "threshold": 0.0,
                    "status": status,
                }
            )

        # Beta
        beta = metrics.get("beta")
        if beta is not None:
            status = "正常" if 0.8 <= beta <= 1.2 else "警告"
            items.append(
                {
                    "name": "Beta系数",
                    "value": beta,
                    "threshold": 1.0,
                    "status": status,
                }
            )

        # VaR
        var_95 = metrics.get("var_95")
        if var_95 is not None:
            status = "正常" if var_95 > -0.1 else "警告" if var_95 > -0.2 else "异常"
            items.append(
                {
                    "name": "VaR(95%)",
                    "value": var_95,
                    "threshold": -0.1,
                    "status": status,
                }
            )

        return items

    def _build_concentration(self, metrics: dict[str, Any]) -> list[dict]:
        """构建集中度分析数据."""
        items = []

        # 这里可以从持仓数据计算，目前用占位
        # 单行业集中度
        items.append(
            {
                "name": "单一行业集中度",
                "value": 0.25,  # 示例值，实际应从持仓计算
                "threshold": 0.30,
                "status": "正常",
            }
        )

        # 前十大持仓集中度
        items.append(
            {
                "name": "前十大持仓集中度",
                "value": 0.45,  # 示例值
                "threshold": 0.50,
                "status": "正常",
            }
        )

        # 股票仓位
        stock_ratio = metrics.get("stock_ratio", 0.6)
        status = "正常" if stock_ratio < 0.8 else "警告"
        items.append(
            {
                "name": "股票仓位",
                "value": stock_ratio,
                "threshold": 0.80,
                "status": status,
            }
        )

        return items

    def _build_compliance_checks(
        self, metrics: dict[str, Any], nav_data: pd.DataFrame | None = None
    ) -> list[dict]:
        """构建合规检查数据."""
        checks = []

        # 检查1: 数据完整性
        data_complete = nav_data is not None and not nav_data.empty
        checks.append(
            {
                "name": "数据完整性",
                "passed": data_complete,
                "detail": "数据完整" if data_complete else "缺少净值数据",
            }
        )

        # 检查2: 数据时效性
        if nav_data is not None and not nav_data.empty and "nav_date" in nav_data.columns:
            latest = pd.to_datetime(nav_data["nav_date"].max())
            days_since = (pd.Timestamp.now() - latest).days
            timely = days_since <= 7
            checks.append(
                {
                    "name": "数据时效性",
                    "passed": timely,
                    "detail": f"最新数据 {latest.strftime('%Y-%m-%d')} ({days_since}天前)"
                    if timely
                    else f"数据过时 ({days_since}天前)",
                }
            )
        else:
            checks.append(
                {
                    "name": "数据时效性",
                    "passed": False,
                    "detail": "无法判断时效性",
                }
            )

        # 检查3: 波动率合规
        vol = metrics.get("volatility")
        if vol is not None:
            vol_ok = vol < 0.5
            checks.append(
                {
                    "name": "波动率合规",
                    "passed": vol_ok,
                    "detail": f"年化波动率 {vol:.1%} {'合规' if vol_ok else '超出阈值50%'}",
                }
            )
        else:
            checks.append(
                {
                    "name": "波动率合规",
                    "passed": False,
                    "detail": "无法计算波动率",
                }
            )

        # 检查4: 最大回撤合规
        mdd = metrics.get("max_drawdown")
        if mdd is not None:
            mdd_ok = mdd > -0.3
            checks.append(
                {
                    "name": "最大回撤合规",
                    "passed": mdd_ok,
                    "detail": f"最大回撤 {mdd:.1%} {'合规' if mdd_ok else '超出阈值-30%'}",
                }
            )
        else:
            checks.append(
                {
                    "name": "最大回撤合规",
                    "passed": False,
                    "detail": "无法计算最大回撤",
                }
            )

        # 检查5: 夏普比率合理性
        sharpe = metrics.get("sharpe_ratio")
        if sharpe is not None:
            sharpe_ok = -3 < sharpe < 5
            checks.append(
                {
                    "name": "夏普比率合理性",
                    "passed": sharpe_ok,
                    "detail": f"夏普比率 {sharpe:.2f} {'合理' if sharpe_ok else '异常'}",
                }
            )
        else:
            checks.append(
                {
                    "name": "夏普比率合理性",
                    "passed": False,
                    "detail": "无法计算夏普比率",
                }
            )

        return checks

    def save(self, content: str, output_path: str) -> None:
        from pathlib import Path

        Path(output_path).write_text(content, encoding="utf-8")

    def get_formats(self) -> list[str]:
        return ["html"]
