"""CLI命令模块 - 筛选、分析、对比、优化、监控、数据、配置、AI、报告"""

from fund_cli.commands.ai_cmd import app as ai_app  # v3.1 新增
from fund_cli.commands.analyze_cmd import app as analyze_app
from fund_cli.commands.compare_cmd import app as compare_app
from fund_cli.commands.config_cmd import app as config_app
from fund_cli.commands.data_cmd import app as data_app
from fund_cli.commands.filter_cmd import app as filter_app
from fund_cli.commands.holding_cmd import app as holding_app  # v3.1 新增
from fund_cli.commands.interactive_cmd import app as interactive_app  # v3.1 新增
from fund_cli.commands.manager_cmd import app as manager_app  # v3.1 新增
from fund_cli.commands.monitor_cmd import app as monitor_app  # v3.1 新增
from fund_cli.commands.optimize_cmd import app as optimize_app  # v3.1 新增
from fund_cli.commands.report_cmd import app as report_app  # v3.1 新增

__all__ = [
    "filter_app",
    "analyze_app",
    "compare_app",
    "data_app",
    "config_app",
    "ai_app",  # v3.1 新增
    "holding_app",  # v3.1 新增
    "interactive_app",  # v3.1 新增
    "manager_app",  # v3.1 新增
    "monitor_app",  # v3.1 新增
    "optimize_app",  # v3.1 新增
    "report_app",  # v3.1 新增
]
