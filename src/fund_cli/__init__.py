"""
Fund CLI - 专业基金分析CLI工具

面向机构客户的基金分析命令行工具，支持基金筛选、业绩分析、组合优化等功能。
"""

__version__ = "2.0.0"
__author__ = "Fund CLI Team"
__license__ = "MIT"

from fund_cli.cli import app

__all__ = ["app", "__version__"]
