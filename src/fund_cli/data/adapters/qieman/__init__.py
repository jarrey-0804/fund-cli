"""
Qieman MCP 适配器子模块

提供与且慢 MCP 服务器的集成能力。
"""

from fund_cli.data.adapters.qieman.client import QiemanMCPClient
from fund_cli.data.adapters.qieman.models import (
    FundDetail,
    FundNavHistory,
    FundPerformance,
    FundHolding,
    BrinsonIndicator,
    CampisiIndicator,
    PortfolioDiagnosis,
    BacktestResult,
    CorrelationResult,
    RiskAnalysis,
)
from fund_cli.data.adapters.qieman.tools import QIEMAN_TOOLS, get_tool_definition

__all__ = [
    "QiemanMCPClient",
    "FundDetail",
    "FundNavHistory",
    "FundPerformance",
    "FundHolding",
    "BrinsonIndicator",
    "CampisiIndicator",
    "PortfolioDiagnosis",
    "BacktestResult",
    "CorrelationResult",
    "RiskAnalysis",
    "QIEMAN_TOOLS",
    "get_tool_definition",
]
