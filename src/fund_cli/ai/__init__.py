"""AI模块 - LLM提供商、AI分析服务、提示词模板、Agent工具

V3.0 新增:
- FundAgent: LangGraph 驱动的智能 Agent
- 工具定义: 12+ 数据接口工具
- 状态管理: Agent 状态定义
- 记忆系统: ChromaDB 长期记忆（可选）
"""

from fund_cli.ai.agent import FundAgent, get_fund_agent, reset_fund_agent
from fund_cli.ai.analyzer import AIAnalyzer
from fund_cli.ai.prompts import PromptTemplates
from fund_cli.ai.providers import (
    LiteLLMProvider,
    LLMProvider,
    OpenAIProvider,
    QwenProvider,
    get_provider,
)
from fund_cli.ai.state import FundAgentState
from fund_cli.ai.tools import FUND_TOOLS

# 可选导入 - 记忆系统
try:
    from fund_cli.ai.memory import VectorMemory  # noqa: F401

    __all_extra = ["VectorMemory"]
except ImportError:
    __all_extra = []

__all__ = [
    # V3.0 新增 - Agent 相关
    "FundAgent",
    "get_fund_agent",
    "reset_fund_agent",
    "FundAgentState",
    "FUND_TOOLS",
    # V2.0 保留
    "LLMProvider",
    "OpenAIProvider",
    "QwenProvider",
    "LiteLLMProvider",
    "get_provider",
    "AIAnalyzer",
    "PromptTemplates",
] + __all_extra
