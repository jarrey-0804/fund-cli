"""
模板引擎.

基于 Jinja2 的报告模板引擎，支持模板继承和宏定义。
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


class TemplateEngine:
    """
    报告模板引擎.

    基于 Jinja2 的报告模板引擎，支持模板继承、宏定义和自定义过滤器。
    提供模板渲染、缓存和管理功能。

    Attributes:
        _env: Jinja2 Environment 实例
    """

    def __init__(self, template_dirs: list[str] | None = None):
        """
        初始化模板引擎.

        Args:
            template_dirs: 模板目录列表，默认使用内置 templates 目录
        """
        if template_dirs is None:
            # 默认模板目录
            base_dir = Path(__file__).parent.parent / "templates"
            template_dirs = [str(base_dir)]
        self._env = Environment(
            loader=FileSystemLoader(template_dirs),
            autoescape=select_autoescape(["html", "xml"]),
            cache_size=100,  # 启用模板缓存
        )
        self._register_filters()
        self._register_globals()

    def _register_filters(self):
        """
        注册自定义过滤器.

        注册以下过滤器:
        - percentage: 数值转百分比显示
        - format_number: 数值格式化
        - color_class: 根据正负返回 CSS 类名
        """

        def percentage(value, decimals=2):
            if value is None:
                return "N/A"
            return f"{float(value) * 100:.{decimals}f}%"

        def format_number(value, decimals=4):
            if value is None:
                return "N/A"
            return f"{float(value):.{decimals}f}"

        def color_class(value):
            if value is None:
                return ""
            return "positive" if float(value) > 0 else "negative" if float(value) < 0 else ""

        self._env.filters["percentage"] = percentage
        self._env.filters["format_number"] = format_number
        self._env.filters["color_class"] = color_class

    def _register_globals(self):
        """
        注册全局函数.

        注册以下全局变量:
        - today: 当前日期
        - now: 返回当前日期字符串的函数
        """
        from datetime import date

        self._env.globals["today"] = date.today()
        self._env.globals["now"] = lambda: date.today().strftime("%Y-%m-%d")

    def render(self, template_name: str, **context) -> str:
        """
        渲染模板.

        Args:
            template_name: 模板文件名（相对于模板目录）
            **context: 模板上下文变量

        Returns:
            渲染后的字符串
        """
        template = self._env.get_template(template_name)
        return template.render(**context)

    def render_string(self, template_string: str, **context) -> str:
        """
        从字符串渲染模板.

        Args:
            template_string: 模板字符串
            **context: 模板上下文变量

        Returns:
            渲染后的字符串
        """
        template = self._env.from_string(template_string)
        return template.render(**context)

    def get_template(self, template_name: str):
        """
        获取模板对象.

        Args:
            template_name: 模板文件名

        Returns:
            Jinja2 Template 对象
        """
        return self._env.get_template(template_name)

    def list_templates(self, directory: str = "") -> list[str]:
        """
        列出可用模板.

        Args:
            directory: 可选的目录前缀过滤

        Returns:
            模板文件名列表
        """
        return self._env.list_templates(
            filter_func=lambda x: x.startswith(directory) if directory else True
        )


# 全局模板引擎实例
_engine: TemplateEngine | None = None


def get_template_engine() -> TemplateEngine:
    global _engine
    if _engine is None:
        _engine = TemplateEngine()
    return _engine
