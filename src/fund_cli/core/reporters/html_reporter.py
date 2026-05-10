"""HTML报告生成器"""

from datetime import date
from typing import Any

from fund_cli.core.reporter import Reporter


class HtmlReporter(Reporter):
    """HTML报告生成器 (FUND-ANALYZE-011)"""

    def generate(
        self,
        fund_code: str,
        metrics: dict[str, Any],
        nav_data: Any = None,
        benchmark_data: Any = None,
        **kwargs,
    ) -> str:  # type: ignore[override]
        kwargs.get("nav_data")
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>{fund_code} 分析报告</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }}
h1 {{ color: #1a5276; border-bottom: 2px solid #2980b9; padding-bottom: 10px; }}
h2 {{ color: #2c3e50; margin-top: 30px; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
th {{ background: #2980b9; color: white; }}
tr:nth-child(even) {{ background: #f2f2f2; }}
.positive {{ color: #27ae60; }}
.negative {{ color: #e74c3c; }}
.footer {{ margin-top: 30px; font-size: 12px; color: #999; border-top: 1px solid #eee; padding-top: 10px; }}
</style></head><body>
<h1>{fund_code} 基金分析报告</h1>
<p>报告日期: {date.today().strftime("%Y-%m-%d")}</p>
<h2>核心指标</h2>
<table><tr><th>指标</th><th>值</th></tr>"""

        key_metrics = [
            ("总收益率", metrics.get("total_return", "N/A")),
            ("年化收益率", metrics.get("annualized_return", "N/A")),
            ("波动率", metrics.get("volatility", "N/A")),
            ("夏普比率", metrics.get("sharpe_ratio", "N/A")),
            ("最大回撤", metrics.get("max_drawdown", "N/A")),
            ("索提诺比率", metrics.get("sortino_ratio", "N/A")),
            ("Alpha", metrics.get("alpha", "N/A")),
            ("Beta", metrics.get("beta", "N/A")),
        ]
        for name, value in key_metrics:
            if isinstance(value, float):
                cls = "positive" if value > 0 else "negative" if value < 0 else ""
                html += f"<tr><td>{name}</td><td class='{cls}'>{value:.4f}</td></tr>"
            else:
                html += f"<tr><td>{name}</td><td>{value}</td></tr>"

        html += "</table>"

        # Add quality score badge if provided in kwargs
        quality_score = kwargs.get("quality_score")
        quality_level = kwargs.get("quality_level")
        if quality_score is not None:
            badge_color = (
                "#27ae60"
                if quality_level == "good"
                else "#f39c12"
                if quality_level == "warning"
                else "#e74c3c"
            )
            html += f'<div style="margin: 10px 0; padding: 8px 12px; background: {badge_color}; color: white; border-radius: 4px; display: inline-block;">数据质量: {quality_score:.0f}/100 ({quality_level})</div>'

        html += "<div class='footer'>本报告由 Fund CLI 自动生成，仅供参考，不构成投资建议。</div>"
        html += "</body></html>"
        return html

    def save(self, content: str, output_path: str) -> None:
        from pathlib import Path

        Path(output_path).write_text(content, encoding="utf-8")

    def get_formats(self) -> list[str]:
        return ["html"]
