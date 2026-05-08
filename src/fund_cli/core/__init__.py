"""核心模块 - 数据管理器、分析引擎、优化引擎、报告生成器"""

from fund_cli.core.analyzer import Analyzer
from fund_cli.core.data_manager import DataManager
from fund_cli.core.optimizer import Optimizer
from fund_cli.core.reporter import Reporter

__all__ = ["DataManager", "Analyzer", "Optimizer", "Reporter"]
