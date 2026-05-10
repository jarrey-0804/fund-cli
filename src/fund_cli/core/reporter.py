"""
报告生成器基类.

定义报告生成的标准接口，提供模板渲染和多格式导出能力。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd


class Reporter(ABC):
    """
    报告生成器基类.

    所有报告生成器必须继承此类。
    """

    @abstractmethod
    def generate(
        self,
        fund_code: str,
        metrics: dict[str, Any],
        nav_data: pd.DataFrame | None = None,
        benchmark_data: pd.DataFrame | None = None,
        **kwargs: Any,
    ) -> str:
        """
        生成报告.

        Args:
            fund_code: 基金代码
            metrics: 分析指标字典
            nav_data: 净值数据
            benchmark_data: 基准数据
            **kwargs: 额外参数

        Returns:
            报告内容字符串
        """
        pass

    @abstractmethod
    def save(
        self,
        content: str,
        output_path: str,
    ) -> None:
        """
        保存报告到文件.

        Args:
            content: 报告内容
            output_path: 输出文件路径
        """
        pass

    @abstractmethod
    def get_formats(self) -> list:
        """
        获取支持的报告格式.

        Returns:
            格式列表（如 ['html', 'markdown', 'pdf']）
        """
        pass

    def render_to_template(self, data: dict[str, Any], template_path: str) -> str:
        """使用模板渲染报告内容（子类可覆盖以支持不同模板引擎）."""
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        template_dir = str(Path(template_path).parent)
        template_name = Path(template_path).name
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template(template_name)
        return template.render(**data)

    def export_pdf(self, content: str, output_path: str) -> Path:
        """导出为PDF（需要weasyprint）."""
        try:
            from weasyprint import HTML

            HTML(string=content).write_pdf(output_path)
            return Path(output_path)
        except ImportError as exc:
            raise RuntimeError("weasyprint 未安装，请运行: pip install weasyprint") from exc

    def export_docx(self, content: str, output_path: str) -> Path:
        """导出为Word（需要python-docx）."""
        raise NotImplementedError("Word导出将在阶段三实现")

    def export_pptx(self, content: str, output_path: str) -> Path:
        """导出为PPT（需要python-pptx）."""
        raise NotImplementedError("PPT导出将在阶段三实现")

    def get_supported_formats(self) -> list[str]:
        """获取支持的导出格式."""
        formats = list(self.get_formats())
        try:
            import weasyprint  # noqa: F401

            formats.append("pdf")
        except ImportError:
            # weasyprint 未安装，不支持 PDF 格式
            pass
        return formats
