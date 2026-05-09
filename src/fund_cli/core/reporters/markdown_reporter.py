"""Markdown报告生成器"""

from datetime import date
from typing import Any

from fund_cli.core.reporter import Reporter


class MarkdownReporter(Reporter):
    """Markdown报告生成器"""

    def generate(self, fund_code: str, metrics: dict[str, Any], nav_data: Any = None, benchmark_data: Any = None, **kwargs) -> str:  # type: ignore[override]
        md = f"# {fund_code} 基金分析报告\n\n"
        md += f"报告日期: {date.today().strftime('%Y-%m-%d')}\n\n"
        md += "## 核心指标\n\n"
        md += "| 指标 | 值 |\n|------|-----|\n"

        key_metrics = [
            ("总收益率", metrics.get("total_return")),
            ("年化收益率", metrics.get("annualized_return")),
            ("波动率", metrics.get("volatility")),
            ("夏普比率", metrics.get("sharpe_ratio")),
            ("最大回撤", metrics.get("max_drawdown")),
        ]
        for name, value in key_metrics:
            if isinstance(value, float):
                md += f"| {name} | {value:.4f} |\n"
            else:
                md += f"| {name} | {value or 'N/A'} |\n"

        md += "\n---\n*本报告由 Fund CLI 自动生成，仅供参考。*\n"
        return md

    def save(self, content: str, output_path: str) -> None:
        from pathlib import Path

        Path(output_path).write_text(content, encoding="utf-8")

    def get_formats(self) -> list[str]:
        return ["markdown"]
