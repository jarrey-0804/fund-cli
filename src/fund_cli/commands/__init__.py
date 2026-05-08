"""CLI命令模块 - 筛选、分析、对比、优化、监控、数据、配置、AI"""

from fund_cli.commands.analyze_cmd import app as analyze_app
from fund_cli.commands.compare_cmd import app as compare_app
from fund_cli.commands.config_cmd import app as config_app
from fund_cli.commands.data_cmd import app as data_app
from fund_cli.commands.filter_cmd import app as filter_app

__all__ = ["filter_app", "analyze_app", "compare_app", "data_app", "config_app"]
