"""核心模块 - 数据管理器、分析引擎、优化引擎、报告生成器"""

from fund_cli.core.ai_analyzer import AIAnalyzer  # v3.1 新增
from fund_cli.core.analyzer import Analyzer
from fund_cli.core.data_gateway import DataSourceGateway, get_data_gateway  # v3.1 新增
from fund_cli.core.data_manager import DataManager
from fund_cli.core.optimizer import Optimizer
from fund_cli.core.reporter import Reporter
from fund_cli.core.template_engine import TemplateEngine, get_template_engine  # v3.1 新增

__all__ = [
    "DataManager",
    "Analyzer",
    "Optimizer",
    "Reporter",
    "AIAnalyzer",  # v3.1 新增
    "TemplateEngine",  # v3.1 新增
    "get_template_engine",  # v3.1 新增
    "DataSourceGateway",  # v3.1 新增
    "get_data_gateway",  # v3.1 新增
]
