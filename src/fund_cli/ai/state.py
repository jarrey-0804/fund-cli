"""
Agent 状态定义

定义 LangGraph StateGraph 的状态结构，
用于在 Agent 工作流节点间传递和共享数据。
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class FundAgentState(TypedDict):
    """
    基金分析 Agent 状态

    定义了 Agent 工作流中各节点共享的状态结构。
    使用 Annotated 类型配合 add_messages reducer 实现消息自动追加。
    """

    # 消息历史 - 使用 add_messages reducer 自动追加新消息
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # 用户标识 - 用于记忆隔离和多用户支持
    user_id: str

    # 会话标识 - 用于同一用户的多轮对话
    thread_id: str

    # 用户原始输入 - 保存用户的问题
    user_input: str

    # 当前步骤 - 跟踪执行进度
    current_step: str

    # 工具调用结果 - 存储工具执行的中间结果
    tool_results: list

    # 是否需要人工审核 - 用于关键决策的人工确认
    needs_human_review: bool

    # 人工审核结果 - 存储人工反馈
    human_feedback: str | None

    # 最终响应 - Agent 的最终输出
    final_response: str | None

    # 错误信息 - 记录执行过程中的错误
    error: str | None


class ChatState(TypedDict):
    """
    简化的对话状态

    用于简单的对话场景，不需要完整的 Agent 状态。
    """

    # 消息历史
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # 用户标识
    user_id: str


class AnalysisState(TypedDict):
    """
    分析任务状态

    用于执行特定的分析任务，如基金对比、组合分析等。
    """

    # 消息历史
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # 待分析的基金代码列表
    fund_codes: list[str]

    # 分析类型
    analysis_type: str

    # 分析参数
    parameters: dict

    # 分析结果
    results: dict | None

    # 错误信息
    error: str | None
