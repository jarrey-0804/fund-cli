"""
LangGraph 节点实现

定义 Agent 工作流的各个处理节点，包括：
- LLM 调用节点
- 工具执行节点
- 路由节点
- 错误处理节点
"""

from __future__ import annotations

from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from fund_cli.ai.state import FundAgentState
from fund_cli.ai.tools import FUND_TOOLS

# 系统提示词
SYSTEM_PROMPT = """你是 Fund-CLI 智能基金分析助手，专业的基金投资顾问。

你的能力包括:
1. 查询基金基本信息、业绩、持仓、经理等数据
2. 对比分析多只基金
3. 分析投资组合风险收益特征
4. 提供客观的投资建议

使用规则:
- 优先使用工具获取实时数据，不要依赖训练数据中的过时信息
- 基金代码通常是6位数字，如 000001
- 分析时要考虑风险因素，给出客观建议
- 如果不确定，坦诚告知用户
- 对于复杂问题，可以分步骤调用多个工具

记住用户偏好:
- 记录用户关注的基金
- 记住用户的风险偏好
- 保持对话的连续性

请用中文回复用户。"""


def create_system_node():
    """
    创建系统消息节点

    确保消息列表以系统消息开头，设定 Agent 的行为准则。
    """

    def system_node(state: FundAgentState) -> dict:
        messages = state.get("messages", [])

        # 检查是否已有系统消息
        has_system = any(isinstance(m, SystemMessage) for m in messages)

        if not has_system:
            # 添加系统消息到开头
            new_messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
            return {"messages": new_messages}

        return {}

    return system_node


def create_llm_node(llm):
    """
    创建 LLM 调用节点

    Args:
        llm: 语言模型实例

    Returns:
        LLM 节点函数
    """
    # 绑定工具到 LLM
    llm_with_tools = llm.bind_tools(FUND_TOOLS)

    def llm_node(state: FundAgentState, config: RunnableConfig) -> dict:
        """调用 LLM 生成响应"""
        messages = state.get("messages", [])

        # 确保有系统消息
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

        # 调用 LLM
        response = llm_with_tools.invoke(messages, config)

        return {
            "messages": [response],
            "current_step": "llm_response"
        }

    return llm_node


def create_tool_node():
    """
    创建工具执行节点

    使用 LangGraph 内置的 ToolNode 执行工具调用。
    """
    from langgraph.prebuilt import ToolNode

    return ToolNode(FUND_TOOLS)


def router_node(state: FundAgentState) -> Literal["tools", "end"]:
    """
    路由节点：决定下一步走向

    检查最后一条消息是否有工具调用，决定是否执行工具或结束。

    Args:
        state: 当前状态

    Returns:
        下一个节点名称
    """
    messages = state.get("messages", [])

    if not messages:
        return "end"

    last_message = messages[-1]

    # 检查是否有工具调用
    if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"

    return "end"


def create_error_handler_node():
    """
    创建错误处理节点

    处理执行过程中的错误，生成友好的错误消息。
    """

    def error_handler_node(state: FundAgentState) -> dict:
        error = state.get("error")

        if error:
            error_message = f"执行过程中出现错误: {error}"
            return {
                "messages": [AIMessage(content=error_message)],
                "final_response": error_message
            }

        return {}

    return error_handler_node


def create_human_input_node():
    """
    创建人工输入节点

    用于需要人工确认或输入的场景。
    """

    def human_input_node(state: FundAgentState) -> dict:
        """等待人工输入"""
        # 在实际实现中，这里可以集成 CLI 的交互式输入
        # 目前返回一个提示消息
        prompt = "请提供更多信息以继续分析..."

        return {
            "messages": [AIMessage(content=prompt)],
            "current_step": "waiting_for_input"
        }

    return human_input_node


def create_summary_node():
    """
    创建总结节点

    在对话结束时生成总结。
    """

    def summary_node(state: FundAgentState) -> dict:
        """生成对话总结"""
        messages = state.get("messages", [])

        # 提取 AI 的最后一条消息作为最终响应
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and not getattr(msg, 'tool_calls', None):
                return {
                    "final_response": msg.content
                }

        return {"final_response": "分析完成。"}

    return summary_node
