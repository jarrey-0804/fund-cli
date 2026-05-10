"""
PDF报告生成器.

使用 WeasyPrint 将 HTML 转换为 PDF。
"""

from typing import Any

from fund_cli.core.reporter import Reporter


class PdfReporter(Reporter):
    """PDF报告生成器."""

    def generate(
        self,
        fund_code: str,
        metrics: dict[str, Any],
        nav_data: Any = None,
        benchmark_data: Any = None,
        **kwargs,
    ) -> str:  # type: ignore[override]
        """生成HTML内容（PDF基于HTML转换）."""
        from datetime import date

        _ = kwargs.get("nav_data")  # 保留参数以保持接口兼容性

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{fund_code} 基金分析报告</title>
<style>
@page {{ size: A4; margin: 2cm; }}
body {{ font-family: "SimSun", "Noto Sans CJK SC", sans-serif; max-width: 100%; margin: 0; padding: 20px; color: #333; font-size: 12px; }}
h1 {{ color: #1a5276; border-bottom: 3px solid #2980b9; padding-bottom: 10px; font-size: 22px; }}
h2 {{ color: #2c3e50; margin-top: 25px; font-size: 16px; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 11px; }}
th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; }}
th {{ background: #2980b9; color: white; }}
tr:nth-child(even) {{ background: #f5f5f5; }}
.positive {{ color: #27ae60; font-weight: bold; }}
.negative {{ color: #e74c3c; font-weight: bold; }}
.summary-box {{ background: #eaf2f8; border-left: 4px solid #2980b9; padding: 15px; margin: 15px 0; }}
.footer {{ margin-top: 30px; font-size: 10px; color: #999; border-top: 1px solid #eee; padding-top: 10px; }}
.page-break {{ page-break-before: always; }}
</style>
</head>
<body>
<h1>{fund_code} 基金分析报告</h1>
<p>报告日期: {date.today().strftime("%Y年%m月%d日")}</p>

<div class="summary-box">
<strong>投资摘要：</strong>
总收益率 <span class="{"positive" if float(metrics.get("total_return", 0)) > 0 else "negative"}">{metrics.get("total_return", "N/A")}</span>，
夏普比率 {metrics.get("sharpe_ratio", "N/A")}，
最大回撤 <span class="negative">{metrics.get("max_drawdown", "N/A")}</span>
</div>

<h2>核心绩效指标</h2>
<table>
<tr><th>指标</th><th>值</th></tr>"""

        key_metrics = [
            ("总收益率", metrics.get("total_return", "N/A")),
            ("年化收益率", metrics.get("annualized_return", "N/A")),
            ("波动率", metrics.get("volatility", "N/A")),
            ("夏普比率", metrics.get("sharpe_ratio", "N/A")),
            ("最大回撤", metrics.get("max_drawdown", "N/A")),
            ("索提诺比率", metrics.get("sortino_ratio", "N/A")),
            ("Alpha", metrics.get("alpha", "N/A")),
            ("Beta", metrics.get("beta", "N/A")),
            ("信息比率", metrics.get("information_ratio", "N/A")),
            ("Calmar比率", metrics.get("calmar_ratio", "N/A")),
        ]
        for name, value in key_metrics:
            if isinstance(value, (int, float)):
                cls = "positive" if value > 0 else "negative" if value < 0 else ""
                html += f"<tr><td>{name}</td><td class='{cls}'>{value:.4f}</td></tr>"
            else:
                html += f"<tr><td>{name}</td><td>{value}</td></tr>"

        html += """</table>
<div class="footer">
<p>本报告由 Fund CLI v3.1 自动生成，仅供参考，不构成投资建议。</p>
</div>
</body></html>"""
        return html

    def save(self, content: str, output_path: str) -> None:
        """保存为PDF文件."""
        self.export_pdf(content, output_path)

    def get_formats(self) -> list[str]:
        return ["pdf"]
