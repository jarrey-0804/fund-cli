"""
Fund-CLI AI Agent

基于 LangGraph 的基金分析智能体，支持：
- 工具调用：自主调用数据接口获取实时数据
- 对话记忆：多轮对话和上下文保持
- ReAct 推理：思考-行动-观察循环
- Postgres 持久化：生产环境对话历史存储
- Human Review：关键决策人工审核
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from fund_cli.ai.nodes import (
    create_error_handler_node,
    create_human_input_node,
    create_llm_node,
    create_summary_node,
    create_system_node,
    create_tool_node,
    router_node,
)
from fund_cli.ai.state import FundAgentState
from fund_cli.config import get_config

logger = logging.getLogger(__name__)


class FundAgent:
    """
    Fund-CLI 智能分析 Agent

    基于 LangGraph 构建的基金分析智能体，能够：
    1. 理解用户的自然语言查询
    2. 自主调用数据工具获取实时数据
    3. 进行多轮对话并保持上下文
    4. 提供专业的基金分析建议

    使用示例:
        agent = FundAgent()
        response = await agent.ainvoke("分析基金000001的投资价值")
    """

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        checkpointer=None,
        enable_human_review: Optional[bool] = None,
    ):
        """
        初始化 Fund Agent

        Args:
            llm: 语言模型实例，不传则使用配置创建
            checkpointer: 状态检查点存储，用于持久化对话记忆
            enable_human_review: 是否启用人工审核，不传则读取配置
        """
        self.llm = llm or self._create_default_llm()
        self.checkpointer = checkpointer or self._create_checkpointer()

        # 人工审核配置
        if enable_human_review is None:
            try:
                config = get_config()
                self.enable_human_review = config.agent.enable_human_review
            except Exception:
                self.enable_human_review = False
        else:
            self.enable_human_review = enable_human_review

        # 构建工作流
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)

    def _create_checkpointer(self):
        """根据配置创建 checkpointer"""
        try:
            config = get_config()
            if config.database.use_postgres:
                try:
                    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

                    logger.info("使用 PostgreSQL 持久化存储")
                    return AsyncPostgresSaver.from_conn_string(
                        config.database.connection_string
                    )
                except ImportError:
                    logger.warning("langgraph-checkpoint-postgres 未安装，回退到 MemorySaver")
                    return MemorySaver()
        except Exception:
            pass

        return MemorySaver()

    def _create_default_llm(self) -> BaseChatModel:
        """创建默认 LLM"""
        config = get_config().ai

        # 使用 OpenAI 兼容接口
        if config.provider == "openai":
            return ChatOpenAI(
                model=config.model or "gpt-4",
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=config.api_key,
            )
        elif config.provider == "qwen":
            # Qwen 使用 OpenAI 兼容接口
            return ChatOpenAI(
                model=config.qwen_model or "qwen-max",
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=config.qwen_api_key or config.api_key,
                base_url=config.qwen_base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        else:
            # 默认使用 OpenAI
            return ChatOpenAI(
                model=config.model or "gpt-4",
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=config.api_key,
            )

    def _build_workflow(self) -> StateGraph:
        """构建 Agent 工作流"""

        # 创建工作流图
        workflow = StateGraph(FundAgentState)

        # 添加节点
        workflow.add_node("system", create_system_node())
        workflow.add_node("llm", create_llm_node(self.llm))
        workflow.add_node("tools", create_tool_node())
        workflow.add_node("error_handler", create_error_handler_node())
        workflow.add_node("summary", create_summary_node())

        # 添加边 - 定义工作流
        workflow.add_edge(START, "system")
        workflow.add_edge("system", "llm")

        # 条件路由：根据 LLM 输出决定下一步
        if self.enable_human_review:
            # 启用人工审核时，增加 human_review 分支
            workflow.add_node("human_review", create_human_input_node())
            workflow.add_conditional_edges(
                "llm",
                router_node,
                {
                    "tools": "tools",
                    "end": "summary"
                }
            )
            workflow.add_edge("tools", "llm")
            workflow.add_edge("summary", "human_review")
            workflow.add_edge("human_review", END)
        else:
            workflow.add_conditional_edges(
                "llm",
                router_node,
                {
                    "tools": "tools",
                    "end": "summary"
                }
            )
            workflow.add_edge("tools", "llm")
            workflow.add_edge("summary", END)

        # 错误处理
        workflow.add_edge("error_handler", END)

        return workflow

    async def ainvoke(
        self,
        user_input: str,
        user_id: str = "default",
        thread_id: Optional[str] = None
    ) -> str:
        """
        异步调用 Agent

        Args:
            user_input: 用户输入
            user_id: 用户标识，用于记忆隔离
            thread_id: 会话标识，用于多轮对话。不传则自动生成新会话

        Returns:
            Agent 响应文本
        """
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        config = {
            "configurable": {
                "user_id": user_id,
                "thread_id": thread_id
            }
        }

        # 准备初始状态
        initial_state: FundAgentState = {
            "messages": [HumanMessage(content=user_input)],
            "user_id": user_id,
            "thread_id": thread_id,
            "user_input": user_input,
            "current_step": "start",
            "tool_results": [],
            "needs_human_review": False,
            "human_feedback": None,
            "final_response": None,
            "error": None
        }

        try:
            # 执行工作流
            result = await self.app.ainvoke(initial_state, config)

            # 提取最终响应
            if result.get("final_response"):
                return result["final_response"]

            # 从消息中提取
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    return last_message.content

            return "抱歉，我无法处理您的请求。"

        except Exception as e:
            return f"执行过程中出现错误: {str(e)}"

    def invoke(
        self,
        user_input: str,
        user_id: str = "default",
        thread_id: Optional[str] = None
    ) -> str:
        """
        同步调用 Agent

        Args:
            user_input: 用户输入
            user_id: 用户标识
            thread_id: 会话标识

        Returns:
            Agent 响应文本
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.ainvoke(user_input, user_id, thread_id)
        )

    def get_history(self, user_id: str, thread_id: str) -> list:
        """
        获取对话历史

        Args:
            user_id: 用户标识
            thread_id: 会话标识

        Returns:
            对话历史列表
        """
        config = {
            "configurable": {
                "user_id": user_id,
                "thread_id": thread_id
            }
        }

        try:
            history = list(self.app.get_state_history(config))
            return history
        except Exception:
            return []

    def clear_history(self, user_id: str, thread_id: str) -> bool:
        """
        清除对话历史

        Args:
            user_id: 用户标识
            thread_id: 会话标识

        Returns:
            是否成功清除
        """
        # MemorySaver 不支持清除，这里返回 True 表示操作接受
        # 实际生产环境应使用 PostgresSaver 等持久化存储
        return True


# 全局 Agent 实例（单例模式）
_fund_agent: Optional[FundAgent] = None


def get_fund_agent(
    llm: Optional[BaseChatModel] = None,
    checkpointer=None,
    force_new: bool = False
) -> FundAgent:
    """
    获取 Fund Agent 实例（单例）

    Args:
        llm: 语言模型实例
        checkpointer: 状态检查点存储
        force_new: 是否强制创建新实例

    Returns:
        FundAgent 实例
    """
    global _fund_agent

    if _fund_agent is None or force_new:
        _fund_agent = FundAgent(llm, checkpointer)

    return _fund_agent


def reset_fund_agent():
    """重置 Agent 实例（用于测试或重新初始化）"""
    global _fund_agent
    _fund_agent = None
