"""
AI Agent 模块测试

测试 LangGraph Agent 的核心功能：
- 工具定义和调用
- Agent 状态管理
- 工作流执行
"""

import pytest
from unittest.mock import MagicMock, patch


class TestTools:
    """测试工具定义"""

    def test_fund_tools_list(self):
        """测试工具列表定义"""
        from fund_cli.ai.tools import FUND_TOOLS

        assert len(FUND_TOOLS) >= 12, "应该有至少12个工具"

        # 检查工具名称
        tool_names = [t.name for t in FUND_TOOLS]
        expected_tools = [
            "get_fund_basic_info",
            "get_fund_nav_history",
            "get_fund_performance",
            "get_fund_holdings",
            "get_fund_manager",
            "search_funds",
            "get_market_index",
            "get_etf_spot",
            "compare_funds",
            "analyze_investment_advice",
            "filter_funds_by_performance",
            "analyze_portfolio",
        ]

        for expected in expected_tools:
            assert expected in tool_names, f"缺少工具: {expected}"

    def test_tool_has_description(self):
        """测试工具描述"""
        from fund_cli.ai.tools import get_fund_basic_info

        assert get_fund_basic_info.description
        assert "基金" in get_fund_basic_info.description

    def test_tool_has_args_schema(self):
        """测试工具参数模式"""
        from fund_cli.ai.tools import get_fund_basic_info

        assert get_fund_basic_info.args_schema is not None

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_basic_info_success(self, mock_get_adapter):
        """测试获取基金基本信息"""
        from fund_cli.ai.tools import get_fund_basic_info

        # Mock 适配器
        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {
            'name': '华夏成长混合',
            'type': '混合型',
            'manager': '张三',
            'establish_date': '2020-01-01',
            'company': '华夏基金',
            'scale': '50亿'
        }
        mock_get_adapter.return_value = mock_adapter

        # 调用工具
        result = get_fund_basic_info.invoke({"fund_code": "000001"})

        assert "000001" in result
        assert "华夏成长混合" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_basic_info_error(self, mock_get_adapter):
        """测试获取基金信息失败"""
        from fund_cli.ai.tools import get_fund_basic_info

        mock_get_adapter.side_effect = Exception("连接失败")

        result = get_fund_basic_info.invoke({"fund_code": "000001"})

        assert "失败" in result

    @patch('fund_cli.ai.tools._get_adapter')
    @patch('fund_cli.ai.tools._get_analyzer')
    def test_get_fund_performance(self, mock_get_analyzer, mock_get_adapter):
        """测试获取基金业绩"""
        from fund_cli.ai.tools import get_fund_performance

        # Mock 数据
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.1, 1.2],
            'date': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        mock_get_adapter.return_value = mock_adapter

        mock_analyzer = MagicMock()
        mock_analyzer.calculate_metrics.return_value = {
            'total_return': 20.0,
            'cagr': 15.0,
            'sharpe_ratio': 1.5,
            'max_drawdown': 10.0,
            'volatility': 12.0,
            'sortino_ratio': 2.0
        }
        mock_get_analyzer.return_value = mock_analyzer

        result = get_fund_performance.invoke({"fund_code": "000001", "period": "1y"})

        assert "000001" in result
        assert "20.00%" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_search_funds(self, mock_get_adapter):
        """测试基金搜索"""
        from fund_cli.ai.tools import search_funds

        mock_adapter = MagicMock()
        mock_adapter.search_funds.return_value = [
            {'code': '000001', 'name': '华夏成长', 'type': '混合型', 'scale': '50亿'},
            {'code': '000002', 'name': '华夏回报', 'type': '混合型', 'scale': '30亿'},
        ]
        mock_get_adapter.return_value = mock_adapter

        result = search_funds.invoke({
            "fund_type": "混合型",
            "limit": 10
        })

        assert "000001" in result
        assert "华夏成长" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_compare_funds(self, mock_get_adapter):
        """测试基金对比"""
        from fund_cli.ai.tools import compare_funds

        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {'name': '测试基金'}
        
        import pandas as pd
        mock_adapter.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.1, 1.2]
        })
        mock_get_adapter.return_value = mock_adapter

        result = compare_funds.invoke({"fund_codes": "000001,000002"})

        assert "对比" in result or "000001" in result


class TestState:
    """测试状态定义"""

    def test_fund_agent_state_structure(self):
        """测试 Agent 状态结构"""
        from fund_cli.ai.state import FundAgentState
        from typing import get_type_hints

        hints = get_type_hints(FundAgentState)

        assert 'messages' in hints
        assert 'user_id' in hints
        assert 'thread_id' in hints
        assert 'user_input' in hints
        assert 'final_response' in hints

    def test_chat_state_structure(self):
        """测试对话状态结构"""
        from fund_cli.ai.state import ChatState
        from typing import get_type_hints

        hints = get_type_hints(ChatState)

        assert 'messages' in hints
        assert 'user_id' in hints


class TestNodes:
    """测试节点实现"""

    def test_system_node_creation(self):
        """测试系统节点创建"""
        from fund_cli.ai.nodes import create_system_node

        node = create_system_node()
        assert callable(node)

    def test_system_node_execution(self):
        """测试系统节点执行"""
        from fund_cli.ai.nodes import create_system_node
        from langchain_core.messages import HumanMessage

        node = create_system_node()
        state = {
            "messages": [HumanMessage(content="测试")],
            "user_id": "test"
        }

        result = node(state)

        assert "messages" in result
        # 应该添加了系统消息
        assert len(result["messages"]) > 0

    def test_router_node_with_tools(self):
        """测试路由节点 - 有工具调用"""
        from fund_cli.ai.nodes import router_node
        from langchain_core.messages import AIMessage

        # 创建带有工具调用的消息
        state = {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[{
                        "name": "get_fund_info",
                        "args": {"fund_code": "000001"},
                        "id": "call_123",
                        "type": "tool_call"
                    }]
                )
            ]
        }

        result = router_node(state)
        assert result == "tools"

    def test_router_node_without_tools(self):
        """测试路由节点 - 无工具调用"""
        from fund_cli.ai.nodes import router_node
        from langchain_core.messages import AIMessage

        state = {
            "messages": [
                AIMessage(content="这是回复")
            ]
        }

        result = router_node(state)
        assert result == "end"


class TestAgent:
    """测试 Agent 类"""

    @patch('fund_cli.ai.agent.ChatOpenAI')
    @patch('fund_cli.ai.agent.get_config')
    def test_agent_initialization(self, mock_get_config, mock_chat_openai):
        """测试 Agent 初始化"""
        from fund_cli.ai.agent import FundAgent

        # Mock 配置
        mock_config = MagicMock()
        mock_config.ai.provider = "openai"
        mock_config.ai.model = "gpt-4"
        mock_config.ai.temperature = 0.7
        mock_config.ai.max_tokens = 2000
        mock_config.ai.api_key = "test-key"
        mock_get_config.return_value = mock_config

        # Mock LLM
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_chat_openai.return_value = mock_llm

        agent = FundAgent()

        assert agent.llm is not None
        assert agent.checkpointer is not None
        assert agent.workflow is not None

    def test_get_fund_agent_singleton(self):
        """测试 Agent 单例"""
        from fund_cli.ai.agent import get_fund_agent, reset_fund_agent

        # 重置
        reset_fund_agent()


class TestPeriodToDateFix:
    """测试 P1 修复: _period_to_dates 参数转换"""

    def test_period_to_dates_1y(self):
        """测试 1y 周期转换"""
        from fund_cli.ai.tools import _period_to_dates
        from datetime import date, timedelta

        start, end = _period_to_dates("1y")
        assert isinstance(start, date)
        assert end is None
        # 应该是大约一年前
        assert (date.today() - start).days >= 360
        assert (date.today() - start).days <= 370

    def test_period_to_dates_1m(self):
        """测试 1m 周期转换"""
        from fund_cli.ai.tools import _period_to_dates
        from datetime import date

        start, end = _period_to_dates("1m")
        assert isinstance(start, date)
        assert end is None
        assert (date.today() - start).days >= 28
        assert (date.today() - start).days <= 35

    def test_period_to_dates_ytd(self):
        """测试 ytd 周期转换"""
        from fund_cli.ai.tools import _period_to_dates
        from datetime import date

        start, end = _period_to_dates("ytd")
        assert isinstance(start, date)
        assert start.year == date.today().year
        assert start.month == 1
        assert start.day == 1

    def test_period_to_dates_default(self):
        """测试未知周期默认为 1y"""
        from fund_cli.ai.tools import _period_to_dates

        start, end = _period_to_dates("unknown")
        assert start is not None
        assert end is None

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_nav_passes_date_not_string(self, mock_get_adapter):
        """验证 get_fund_nav_history 传递 date 而非 str"""
        from fund_cli.ai.tools import get_fund_nav_history

        mock_adapter = MagicMock()
        mock_adapter.get_fund_nav.return_value = None
        mock_get_adapter.return_value = mock_adapter

        get_fund_nav_history.invoke({"fund_code": "000001", "period": "1y"})

        # 验证 get_fund_nav 被调用时传递的是 date 类型
        call_args = mock_adapter.get_fund_nav.call_args
        assert call_args is not None
        # 应该通过关键字参数传递 start_date
        assert 'start_date' in call_args.kwargs
        assert isinstance(call_args.kwargs['start_date'], type(call_args.kwargs['start_date']))


class TestHoldingsFix:
    """测试 P2 修复: get_fund_holdings 返回值适配"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_holdings_dataframe_format(self, mock_get_adapter):
        """测试 DataFrame 格式的持仓数据"""
        from fund_cli.ai.tools import get_fund_holdings
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_fund_holdings.return_value = pd.DataFrame({
            'stock_code': ['600519', '000858'],
            'stock_name': ['贵州茅台', '五粮液'],
            'weight': [8.5, 5.2]
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_holdings.invoke({"fund_code": "000001"})
        assert "贵州茅台" in result
        assert "五粮液" in result
        assert "8.50%" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_holdings_empty(self, mock_get_adapter):
        """测试空持仓数据"""
        from fund_cli.ai.tools import get_fund_holdings
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_fund_holdings.return_value = pd.DataFrame()
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_holdings.invoke({"fund_code": "000001"})
        assert "未找到" in result


class TestFundListFix:
    """测试 P3 修复: get_fund_list 返回值处理"""

    @patch('fund_cli.ai.tools._get_data_manager')
    @patch('fund_cli.ai.tools._get_analyzer')
    def test_filter_with_dataframe_fund_list(self, mock_get_analyzer, mock_get_dm):
        """测试 DataFrame 格式的基金列表"""
        from fund_cli.ai.tools import filter_funds_by_performance
        import pandas as pd

        mock_dm = MagicMock()
        # 返回 DataFrame 格式的基金列表
        mock_dm.get_fund_list.return_value = pd.DataFrame({
            '基金代码': ['000001', '000002', '000003'],
            '基金简称': ['华夏成长', '华夏回报', '华夏优势']
        })
        mock_dm.get_fund_info.return_value = {'name': '测试基金'}
        mock_dm.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.1, 1.2]
        })
        mock_get_dm.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.calculate_metrics.return_value = {
            'cagr': 15.0, 'max_drawdown': -10.0, 'sharpe_ratio': 1.2
        }
        mock_get_analyzer.return_value = mock_analyzer

        result = filter_funds_by_performance.invoke({"limit": 5})
        assert "筛选结果" in result or "未找到" in result or "失败" in result


class TestKeyFallbackFix:
    """测试 M1 修复: get_fund_info key 兜底"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_basic_info_chinese_keys(self, mock_get_adapter):
        """测试中文 key 的基金信息"""
        from fund_cli.ai.tools import get_fund_basic_info

        mock_adapter = MagicMock()
        # 返回中文 key 的 dict
        mock_adapter.get_fund_info.return_value = {
            '基金简称': '华夏成长',
            '基金类型': '混合型',
            '基金经理': '张三',
        }
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_basic_info.invoke({"fund_code": "000001"})
        assert "华夏成长" in result
        assert "混合型" in result
        assert "张三" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_basic_info_mixed_keys(self, mock_get_adapter):
        """测试混合 key 的基金信息"""
        from fund_cli.ai.tools import get_fund_basic_info

        mock_adapter = MagicMock()
        mock_adapter.get_fund_info.return_value = {
            'name': '华夏成长',
            '基金类型': '混合型',
            'manager': '张三',
        }
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_basic_info.invoke({"fund_code": "000001"})
        assert "华夏成长" in result
        assert "混合型" in result
        assert "张三" in result


class TestAgentLegacy:
    """原有 Agent 测试"""

    def test_get_fund_agent_singleton(self):
        """测试 Agent 单例"""
        from fund_cli.ai.agent import get_fund_agent, reset_fund_agent

        reset_fund_agent()

        with patch('fund_cli.ai.agent.ChatOpenAI') as mock_chat:
            mock_llm = MagicMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_chat.return_value = mock_llm

            with patch('fund_cli.ai.agent.get_config') as mock_config:
                mock_cfg = MagicMock()
                mock_cfg.ai.provider = "openai"
                mock_cfg.ai.model = "gpt-4"
                mock_cfg.ai.temperature = 0.7
                mock_cfg.ai.max_tokens = 2000
                mock_cfg.ai.api_key = "test"
                mock_config.return_value = mock_cfg

                agent1 = get_fund_agent()
                agent2 = get_fund_agent()

                assert agent1 is agent2

        reset_fund_agent()

    def test_reset_fund_agent(self):
        """测试重置 Agent"""
        from fund_cli.ai.agent import get_fund_agent, reset_fund_agent, _fund_agent

        reset_fund_agent()

        with patch('fund_cli.ai.agent.ChatOpenAI') as mock_chat:
            mock_llm = MagicMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_chat.return_value = mock_llm

            with patch('fund_cli.ai.agent.get_config') as mock_config:
                mock_cfg = MagicMock()
                mock_cfg.ai.provider = "openai"
                mock_cfg.ai.model = "gpt-4"
                mock_cfg.ai.temperature = 0.7
                mock_cfg.ai.max_tokens = 2000
                mock_cfg.ai.api_key = "test"
                mock_config.return_value = mock_cfg

                get_fund_agent()

        reset_fund_agent()


class TestAgentIntegration:
    """Agent 集成测试"""

    @patch('fund_cli.ai.agent.ChatOpenAI')
    @patch('fund_cli.ai.agent.get_config')
    def test_agent_methods_exist(self, mock_get_config, mock_chat_openai):
        """测试 Agent 方法存在"""
        from fund_cli.ai.agent import FundAgent, reset_fund_agent

        reset_fund_agent()

        # Mock 配置
        mock_config = MagicMock()
        mock_config.ai.provider = "openai"
        mock_config.ai.model = "gpt-4"
        mock_config.ai.temperature = 0.7
        mock_config.ai.max_tokens = 2000
        mock_config.ai.api_key = "test-key"
        mock_get_config.return_value = mock_config

        # Mock LLM 响应
        from langchain_core.messages import AIMessage
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = AIMessage(content="这是测试回复")
        mock_chat_openai.return_value = mock_llm

        agent = FundAgent()

        # 验证方法存在
        assert hasattr(agent, 'ainvoke')
        assert hasattr(agent, 'invoke')
        assert hasattr(agent, 'get_history')
        assert hasattr(agent, 'clear_history')

        reset_fund_agent()


class TestModuleImports:
    """测试模块导入"""

    def test_ai_module_imports(self):
        """测试 AI 模块导入"""
        from fund_cli.ai import (
            FundAgent,
            get_fund_agent,
            reset_fund_agent,
            FundAgentState,
            FUND_TOOLS,
            AIAnalyzer,
            PromptTemplates,
        )

        assert FundAgent is not None
        assert get_fund_agent is not None
        assert reset_fund_agent is not None
        assert FundAgentState is not None
        assert FUND_TOOLS is not None
        assert AIAnalyzer is not None
        assert PromptTemplates is not None

    def test_tools_module_imports(self):
        """测试工具模块导入"""
        from fund_cli.ai.tools import (
            get_fund_basic_info,
            get_fund_performance,
            get_fund_holdings,
            search_funds,
            compare_funds,
            FUND_TOOLS,
        )

        assert get_fund_basic_info is not None
        assert get_fund_performance is not None
        assert get_fund_holdings is not None
        assert search_funds is not None
        assert compare_funds is not None
        assert len(FUND_TOOLS) >= 12


class TestNewTools:
    """测试新增工具"""

    @patch('fund_cli.ai.tools._get_data_manager')
    @patch('fund_cli.ai.tools._get_analyzer')
    def test_filter_funds_by_performance(self, mock_get_analyzer, mock_get_dm):
        """测试业绩筛选工具"""
        from fund_cli.ai.tools import filter_funds_by_performance

        mock_dm = MagicMock()
        mock_dm.get_fund_list.return_value = ['000001', '000002']
        mock_dm.get_fund_info.return_value = {'name': '测试基金'}
        import pandas as pd
        mock_dm.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.1, 1.2]
        })
        mock_get_dm.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.calculate_metrics.return_value = {
            'cagr': 15.0, 'max_drawdown': -10.0, 'sharpe_ratio': 1.2
        }
        mock_get_analyzer.return_value = mock_analyzer

        result = filter_funds_by_performance.invoke({
            "min_return_1y": 10.0,
            "max_drawdown": 20.0,
            "min_sharpe": 0.5,
            "limit": 5
        })

        assert "筛选结果" in result or "未找到" in result

    @patch('fund_cli.ai.tools._get_data_manager')
    @patch('fund_cli.ai.tools._get_analyzer')
    def test_analyze_portfolio(self, mock_get_analyzer, mock_get_dm):
        """测试组合分析工具"""
        from fund_cli.ai.tools import analyze_portfolio

        mock_dm = MagicMock()
        mock_dm.get_fund_info.return_value = {'name': '测试基金A'}
        import pandas as pd
        mock_dm.get_fund_nav.return_value = pd.DataFrame({
            'unit_nav': [1.0, 1.1, 1.2, 1.15, 1.25]
        })
        mock_get_dm.return_value = mock_dm

        mock_analyzer = MagicMock()
        mock_analyzer.calculate_metrics.return_value = {
            'cagr': 12.0, 'volatility': 8.0,
            'sharpe_ratio': 1.0, 'max_drawdown': -5.0
        }
        mock_get_analyzer.return_value = mock_analyzer

        result = analyze_portfolio.invoke({
            "fund_codes": "000001,000002",
            "weights": "0.6,0.4",
            "risk_free_rate": 0.03
        })

        assert "组合分析" in result or "投资组合" in result

    def test_filter_funds_by_performance_error(self):
        """测试业绩筛选工具异常处理"""
        from fund_cli.ai.tools import filter_funds_by_performance

        with patch('fund_cli.ai.tools._get_data_manager') as mock_get_dm:
            mock_get_dm.side_effect = Exception("数据错误")
            result = filter_funds_by_performance.invoke({"limit": 5})
            assert "失败" in result

    def test_analyze_portfolio_single_fund(self):
        """测试组合分析 - 单只基金"""
        from fund_cli.ai.tools import analyze_portfolio

        with patch('fund_cli.ai.tools._get_data_manager') as mock_get_dm:
            mock_dm = MagicMock()
            mock_dm.get_fund_info.return_value = {'name': '测试'}
            mock_dm.get_fund_nav.return_value = None
            mock_get_dm.return_value = mock_dm

            result = analyze_portfolio.invoke({"fund_codes": "000001"})
            assert "至少 2 只" in result


class TestConfig:
    """测试新增配置"""

    def test_database_config(self):
        """测试数据库配置"""
        from fund_cli.config import DatabaseConfig

        config = DatabaseConfig()
        assert config.use_postgres is False
        assert config.host == "localhost"
        assert config.port == 5432
        assert "postgresql://" in config.connection_string

    def test_agent_config(self):
        """测试 Agent 配置"""
        from fund_cli.config import AgentConfig

        config = AgentConfig()
        assert config.enable_human_review is False
        assert config.max_tool_calls == 10
        assert config.use_chroma_memory is False

    def test_app_config_has_new_fields(self):
        """测试应用配置包含新字段"""
        from fund_cli.config import get_config

        config = get_config()
        assert hasattr(config, 'database')
        assert hasattr(config, 'agent')
        assert hasattr(config.database, 'use_postgres')
        assert hasattr(config.agent, 'enable_human_review')


class TestMCPModule:
    """测试 MCP 模块"""

    def test_mcp_module_import(self):
        """测试 MCP 模块导入"""
        try:
            from fund_cli.mcp import create_fund_mcp_server
            assert callable(create_fund_mcp_server)
        except ImportError:
            # mcp 未安装时跳过
            pass

    def test_mcp_server_module_exists(self):
        """测试 MCP Server 文件存在"""
        from pathlib import Path

        server_path = Path(__file__).parent.parent.parent.parent / "src" / "fund_cli" / "mcp" / "server.py"
        assert server_path.exists(), "MCP Server 文件应存在"


class TestMemoryModule:
    """测试记忆模块"""

    def test_memory_module_import(self):
        """测试记忆模块导入"""
        try:
            from fund_cli.ai.memory import VectorMemory
            assert VectorMemory is not None
        except ImportError:
            # chromadb 未安装时跳过
            pass

    def test_memory_module_exists(self):
        """测试记忆模块文件存在"""
        import importlib.util
        spec = importlib.util.find_spec("fund_cli.ai.memory")
        assert spec is not None, "记忆模块应存在"


class TestAgentWithHumanReview:
    """测试 Agent 人工审核功能"""

    @patch('fund_cli.ai.agent.ChatOpenAI')
    @patch('fund_cli.ai.agent.get_config')
    def test_agent_with_human_review_enabled(self, mock_get_config, mock_chat_openai):
        """测试启用人工审核"""
        from fund_cli.ai.agent import FundAgent, reset_fund_agent

        reset_fund_agent()

        mock_config = MagicMock()
        mock_config.ai.provider = "openai"
        mock_config.ai.model = "gpt-4"
        mock_config.ai.temperature = 0.7
        mock_config.ai.max_tokens = 2000
        mock_config.ai.api_key = "test-key"
        mock_config.database.use_postgres = False
        mock_config.agent.enable_human_review = True
        mock_get_config.return_value = mock_config

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_chat_openai.return_value = mock_llm

        agent = FundAgent()
        assert agent.enable_human_review is True

        reset_fund_agent()

    @patch('fund_cli.ai.agent.ChatOpenAI')
    @patch('fund_cli.ai.agent.get_config')
    def test_agent_with_human_review_disabled(self, mock_get_config, mock_chat_openai):
        """测试禁用人工审核"""
        from fund_cli.ai.agent import FundAgent, reset_fund_agent

        reset_fund_agent()

        mock_config = MagicMock()
        mock_config.ai.provider = "openai"
        mock_config.ai.model = "gpt-4"
        mock_config.ai.temperature = 0.7
        mock_config.ai.max_tokens = 2000
        mock_config.ai.api_key = "test-key"
        mock_config.database.use_postgres = False
        mock_config.agent.enable_human_review = False
        mock_get_config.return_value = mock_config

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_chat_openai.return_value = mock_llm

        agent = FundAgent(enable_human_review=False)
        assert agent.enable_human_review is False

        reset_fund_agent()


class TestCheckpointer:
    """测试 Checkpointer 选择"""

    @patch('fund_cli.ai.agent.ChatOpenAI')
    @patch('fund_cli.ai.agent.get_config')
    def test_memory_saver_default(self, mock_get_config, mock_chat_openai):
        """测试默认使用 MemorySaver"""
        from fund_cli.ai.agent import FundAgent, reset_fund_agent
        from langgraph.checkpoint.memory import MemorySaver

        reset_fund_agent()

        mock_config = MagicMock()
        mock_config.ai.provider = "openai"
        mock_config.ai.model = "gpt-4"
        mock_config.ai.temperature = 0.7
        mock_config.ai.max_tokens = 2000
        mock_config.ai.api_key = "test-key"
        mock_config.database.use_postgres = False
        mock_get_config.return_value = mock_config

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_chat_openai.return_value = mock_llm

        agent = FundAgent()
        assert isinstance(agent.checkpointer, MemorySaver)

        reset_fund_agent()

    @patch('fund_cli.ai.agent.ChatOpenAI')
    @patch('fund_cli.ai.agent.get_config')
    def test_postgres_config_true(self, mock_get_config, mock_chat_openai):
        """测试 Postgres 配置为 True 时尝试加载"""
        from fund_cli.ai.agent import FundAgent, reset_fund_agent

        reset_fund_agent()

        mock_config = MagicMock()
        mock_config.ai.provider = "openai"
        mock_config.ai.model = "gpt-4"
        mock_config.ai.temperature = 0.7
        mock_config.ai.max_tokens = 2000
        mock_config.ai.api_key = "test-key"
        mock_config.database.use_postgres = True
        mock_config.database.connection_string = "postgresql://test:test@localhost/fund_cli"
        mock_get_config.return_value = mock_config

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_chat_openai.return_value = mock_llm

        # PostgresSaver 未安装时应回退到 MemorySaver
        agent = FundAgent()
        from langgraph.checkpoint.memory import MemorySaver
        assert isinstance(agent.checkpointer, MemorySaver)

        reset_fund_agent()


# ============================================
# 阶段一: 核心功能完善 - 新增工具测试
# ============================================


class TestPhaseOneTools:
    """测试阶段一新增的12个核心功能工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_fee_info(self, mock_get_adapter):
        """测试基金费率工具"""
        from fund_cli.ai.tools import get_fund_fee_info

        mock_adapter = MagicMock()
        mock_adapter.get_fund_fee.return_value = {
            'management_fee': '1.50%',
            'custody_fee': '0.25%',
            'purchase_fee': '1.00%',
            'redeem_fee': '0.50%'
        }
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_fee_info.invoke({"fund_code": "000001"})

        assert "000001" in result
        assert "管理费率" in result
        assert "1.50%" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_fee_info_empty(self, mock_get_adapter):
        """测试基金费率工具 - 空数据"""
        from fund_cli.ai.tools import get_fund_fee_info

        mock_adapter = MagicMock()
        mock_adapter.get_fund_fee.return_value = {}
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_fee_info.invoke({"fund_code": "000001"})

        assert "未找到" in result or "管理费率" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_rating_info(self, mock_get_adapter):
        """测试基金评级工具"""
        from fund_cli.ai.tools import get_fund_rating_info

        mock_adapter = MagicMock()
        mock_adapter.get_fund_rating.return_value = 4
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_rating_info.invoke({"fund_code": "000001"})

        assert "000001" in result
        assert "★★★★" in result
        assert "4星" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_rating_info_none(self, mock_get_adapter):
        """测试基金评级工具 - 无评级"""
        from fund_cli.ai.tools import get_fund_rating_info

        mock_adapter = MagicMock()
        mock_adapter.get_fund_rating.return_value = None
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_rating_info.invoke({"fund_code": "000001"})

        assert "暂无评级" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_ratings_list(self, mock_get_adapter):
        """测试基金评级列表工具"""
        from fund_cli.ai.tools import get_fund_ratings_list
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_fund_ratings.return_value = pd.DataFrame({
            'code': ['000001', '000002'],
            'name': ['华夏成长', '华夏回报'],
            'rating': [5, 4]
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_ratings_list.invoke({"limit": 10})

        assert "基金评级列表" in result
        assert "000001" in result
        assert "华夏成长" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_dividend_history(self, mock_get_adapter):
        """测试基金分红历史工具"""
        from fund_cli.ai.tools import get_fund_dividend_history
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_fund_dividends.return_value = pd.DataFrame({
            'date': ['2024-01-15', '2023-06-20'],
            'amount': ['0.15元', '0.20元']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_dividend_history.invoke({"fund_code": "000001", "limit": 5})

        assert "000001" in result
        assert "分红历史" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_split_history(self, mock_get_adapter):
        """测试基金拆分历史工具"""
        from fund_cli.ai.tools import get_fund_split_history
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_fund_splits.return_value = pd.DataFrame({
            'date': ['2023-05-10'],
            'ratio': ['1:2']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_split_history.invoke({"fund_code": "000001", "limit": 5})

        assert "000001" in result
        assert "拆分历史" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_rank_overall(self, mock_get_adapter):
        """测试基金综合排行工具"""
        from fund_cli.ai.tools import get_fund_rank_overall
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_fund_rank_by_type.return_value = pd.DataFrame({
            'code': ['000001', '000002'],
            'name': ['华夏成长', '华夏回报'],
            'return_1y': ['15.5%', '12.3%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_rank_overall.invoke({"fund_type": "混合型", "limit": 10})

        assert "排行" in result
        assert "000001" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_rank_by_etf(self, mock_get_adapter):
        """测试ETF排行工具"""
        from fund_cli.ai.tools import get_fund_rank_by_etf
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_exchange_fund_rank.return_value = pd.DataFrame({
            'code': ['510050', '510300'],
            'name': ['50ETF', '300ETF'],
            'return': ['5.2%', '3.8%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_rank_by_etf.invoke({"limit": 10})

        assert "ETF" in result
        assert "510050" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_rank_by_money(self, mock_get_adapter):
        """测试货币基金排行工具"""
        from fund_cli.ai.tools import get_fund_rank_by_money
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_money_fund_rank.return_value = pd.DataFrame({
            'code': ['000001', '000002'],
            'name': ['华夏货币A', '华夏货币B'],
            'yield_7d': ['2.5%', '2.3%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_rank_by_money.invoke({"limit": 10})

        assert "货币" in result
        assert "7日年化" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_achievement_analysis(self, mock_get_adapter):
        """测试基金业绩评价工具"""
        from fund_cli.ai.tools import get_fund_achievement_analysis
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_fund_achievement.return_value = pd.DataFrame({
            'return_1m': ['2.5%'],
            'return_3m': ['5.2%'],
            'return_1y': ['15.5%'],
            'rank': ['前10%'],
            'grade': ['优秀']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_achievement_analysis.invoke({"fund_code": "000001"})

        assert "000001" in result
        assert "业绩评价" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_risk_metrics(self, mock_get_adapter):
        """测试基金风险指标工具"""
        from fund_cli.ai.tools import get_fund_risk_metrics
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_fund_risk_analysis.return_value = pd.DataFrame({
            'sharpe': ['1.25'],
            'max_drawdown': ['-15.2%'],
            'volatility': ['18.5%'],
            'risk_level': ['中高风险']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_risk_metrics.invoke({"fund_code": "000001"})

        assert "000001" in result
        assert "风险指标" in result
        assert "夏普比率" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_profit_stats(self, mock_get_adapter):
        """测试基金盈利概率工具"""
        from fund_cli.ai.tools import get_fund_profit_stats
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_fund_profit_probability.return_value = pd.DataFrame({
            'prob_1m': ['65%'],
            'prob_3m': ['72%'],
            'prob_1y': ['85%'],
            'avg_return': ['12.5%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_profit_stats.invoke({"fund_code": "000001"})

        assert "000001" in result
        assert "盈利概率" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_asset_allocation_info(self, mock_get_adapter):
        """测试基金资产配置工具"""
        from fund_cli.ai.tools import get_fund_asset_allocation_info
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_fund_asset_allocation.return_value = pd.DataFrame({
            'stock_ratio': ['65%'],
            'bond_ratio': ['25%'],
            'cash_ratio': ['8%'],
            'other_ratio': ['2%'],
            'report_date': ['2024-03-31']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_fund_asset_allocation_info.invoke({"fund_code": "000001"})

        assert "000001" in result
        assert "资产配置" in result
        assert "股票占比" in result

    def test_fund_tools_count(self):
        """测试工具总数是否正确（含所有阶段工具）"""
        from fund_cli.ai.tools import FUND_TOOLS

        assert len(FUND_TOOLS) == 86, f"期望86个工具，实际有{len(FUND_TOOLS)}个"

    def test_new_tools_in_list(self):
        """测试新增工具都在FUND_TOOLS列表中"""
        from fund_cli.ai.tools import (
            FUND_TOOLS,
            get_fund_fee_info,
            get_fund_rating_info,
            get_fund_ratings_list,
            get_fund_dividend_history,
            get_fund_split_history,
            get_fund_rank_overall,
            get_fund_rank_by_etf,
            get_fund_rank_by_money,
            get_fund_achievement_analysis,
            get_fund_risk_metrics,
            get_fund_profit_stats,
            get_fund_asset_allocation_info,
        )

        new_tools = [
            get_fund_fee_info,
            get_fund_rating_info,
            get_fund_ratings_list,
            get_fund_dividend_history,
            get_fund_split_history,
            get_fund_rank_overall,
            get_fund_rank_by_etf,
            get_fund_rank_by_money,
            get_fund_achievement_analysis,
            get_fund_risk_metrics,
            get_fund_profit_stats,
            get_fund_asset_allocation_info,
        ]

        for tool in new_tools:
            assert tool in FUND_TOOLS, f"工具 {tool.name} 不在FUND_TOOLS列表中"


# ============================================
# 阶段二: 宏观数据增强 - 新增工具测试
# ============================================


class TestPhaseTwoTools:
    """测试阶段二新增的15个宏观数据工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_macro_gdp(self, mock_get_adapter):
        """测试GDP工具"""
        from fund_cli.ai.tools import get_macro_gdp
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_gdp_yearly.return_value = pd.DataFrame({
            'date': ['2023', '2022'],
            'gdp': ['126.06万亿', '121.02万亿'],
            'yoy': ['5.2%', '3.0%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_macro_gdp.invoke({"freq": "yearly"})
        assert "GDP" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_macro_cpi(self, mock_get_adapter):
        """测试CPI工具"""
        from fund_cli.ai.tools import get_macro_cpi
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_cpi_monthly.return_value = pd.DataFrame({
            'date': ['2024-01', '2023-12'],
            'cpi': ['100.2', '100.3'],
            'yoy': ['-0.8%', '-0.3%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_macro_cpi.invoke({"freq": "monthly"})
        assert "CPI" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_macro_ppi(self, mock_get_adapter):
        """测试PPI工具"""
        from fund_cli.ai.tools import get_macro_ppi
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_ppi_yearly.return_value = pd.DataFrame({
            'date': ['2023', '2022'],
            'ppi': ['98.5', '99.8'],
            'yoy': ['-1.5%', '-0.2%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_macro_ppi.invoke({"freq": "yearly"})
        assert "PPI" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_macro_trade(self, mock_get_adapter):
        """测试进出口贸易工具"""
        from fund_cli.ai.tools import get_macro_trade
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_exports_yearly.return_value = pd.DataFrame({
            'date': ['2023-12'], 'value': ['3038亿美元']
        })
        mock_adapter.get_imports_yearly.return_value = pd.DataFrame({
            'date': ['2023-12'], 'value': ['2282亿美元']
        })
        mock_adapter.get_trade_balance.return_value = pd.DataFrame({
            'date': ['2023-12'], 'value': ['756亿美元']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_macro_trade.invoke({})
        assert "进出口" in result or "贸易" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_macro_pmi(self, mock_get_adapter):
        """测试PMI工具"""
        from fund_cli.ai.tools import get_macro_pmi
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_pmi_official.return_value = pd.DataFrame({
            'date': ['2024-01', '2023-12'],
            'pmi': ['49.2', '47.0']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_macro_pmi.invoke({"source": "official"})
        assert "PMI" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_macro_interest_rate(self, mock_get_adapter):
        """测试利率工具"""
        from fund_cli.ai.tools import get_macro_interest_rate
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_china_interest_rate.return_value = pd.DataFrame({
            'date': ['2024-01'], 'rate': ['3.45%']
        })
        mock_adapter.get_lpr_data.return_value = pd.DataFrame({
            'date': ['2024-01'], 'lpr_1y': ['3.45%'], 'lpr_5y': ['3.95%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_macro_interest_rate.invoke({})
        assert "利率" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_macro_money_supply(self, mock_get_adapter):
        """测试货币供应量工具"""
        from fund_cli.ai.tools import get_macro_money_supply
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_m2_yearly.return_value = pd.DataFrame({
            'date': ['2023-12'], 'value': ['292.27万亿'], 'yoy': ['9.7%']
        })
        mock_adapter.get_new_loan.return_value = pd.DataFrame({
            'date': ['2023-12'], 'value': ['1.17万亿']
        })
        mock_adapter.get_social_financing.return_value = pd.DataFrame({
            'date': ['2023-12'], 'value': ['1.94万亿']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_macro_money_supply.invoke({})
        assert "货币供应量" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_macro_industrial(self, mock_get_adapter):
        """测试工业数据工具"""
        from fund_cli.ai.tools import get_macro_industrial
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_industrial_production.return_value = pd.DataFrame({
            'date': ['2023-12'], 'value': ['7.0%'], 'yoy': ['7.0%']
        })
        mock_adapter.get_fixed_asset_investment.return_value = pd.DataFrame({
            'date': ['2023-12'], 'value': ['3.0%'], 'yoy': ['3.0%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_macro_industrial.invoke({})
        assert "工业" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_macro_retail(self, mock_get_adapter):
        """测试零售数据工具"""
        from fund_cli.ai.tools import get_macro_retail
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_retail_sales_yearly.return_value = pd.DataFrame({
            'date': ['2023-12'], 'value': ['43550亿'], 'yoy': ['7.4%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_macro_retail.invoke({})
        assert "零售" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_macro_unemployment(self, mock_get_adapter):
        """测试失业率工具"""
        from fund_cli.ai.tools import get_macro_unemployment
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_urban_unemployment.return_value = pd.DataFrame({
            'date': ['2023-12'], 'rate': ['5.1%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_macro_unemployment.invoke({})
        assert "失业率" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_market_sector_flow(self, mock_get_adapter):
        """测试行业资金流向工具"""
        from fund_cli.ai.tools import get_market_sector_flow
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_sector_fund_flow.return_value = pd.DataFrame({
            'name': ['银行', '电子'],
            'main_net_inflow': ['15.2亿', '8.5亿']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_market_sector_flow.invoke({"period": "今日"})
        assert "行业" in result or "资金" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_market_north_flow(self, mock_get_adapter):
        """测试北向资金工具"""
        from fund_cli.ai.tools import get_market_north_flow
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_north_fund_flow.return_value = pd.DataFrame({
            'date': ['2024-01-15'], 'value': ['50.2亿']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_market_north_flow.invoke({"market": "北向资金"})
        assert "北向" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_market_overall_flow(self, mock_get_adapter):
        """测试市场整体资金流向工具"""
        from fund_cli.ai.tools import get_market_overall_flow
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_market_fund_flow.return_value = pd.DataFrame({
            'date': ['2024-01-15'], 'main_net_inflow': ['-120.5亿']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_market_overall_flow.invoke({})
        assert "资金" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_industry_boards_info(self, mock_get_adapter):
        """测试行业板块工具"""
        from fund_cli.ai.tools import get_industry_boards_info
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_industry_boards.return_value = pd.DataFrame({
            'name': ['银行', '电子', '医药'],
            'change_pct': ['+1.5%', '+0.8%', '-0.3%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_industry_boards_info.invoke({"limit": 10})
        assert "行业板块" in result
        assert "银行" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_concept_boards_info(self, mock_get_adapter):
        """测试概念板块工具"""
        from fund_cli.ai.tools import get_concept_boards_info
        import pandas as pd

        mock_adapter = MagicMock()
        mock_adapter.get_concept_boards.return_value = pd.DataFrame({
            'name': ['人工智能', '新能源', '芯片'],
            'change_pct': ['+2.5%', '+1.2%', '-0.5%']
        })
        mock_get_adapter.return_value = mock_adapter

        result = get_concept_boards_info.invoke({"limit": 10})
        assert "概念板块" in result
        assert "人工智能" in result

    def test_phase_two_tools_count(self):
        """测试工具总数是否正确（含所有阶段工具）"""
        from fund_cli.ai.tools import FUND_TOOLS

        assert len(FUND_TOOLS) == 86, f"期望86个工具，实际有{len(FUND_TOOLS)}个"

    def test_phase_two_tools_in_list(self):
        """测试阶段二新增工具都在FUND_TOOLS列表中"""
        from fund_cli.ai.tools import (
            FUND_TOOLS,
            get_macro_gdp, get_macro_cpi, get_macro_ppi,
            get_macro_trade, get_macro_pmi, get_macro_interest_rate,
            get_macro_money_supply, get_macro_industrial,
            get_macro_retail, get_macro_unemployment,
            get_market_sector_flow, get_market_north_flow,
            get_market_overall_flow, get_industry_boards_info,
            get_concept_boards_info,
        )

        phase2_tools = [
            get_macro_gdp, get_macro_cpi, get_macro_ppi,
            get_macro_trade, get_macro_pmi, get_macro_interest_rate,
            get_macro_money_supply, get_macro_industrial,
            get_macro_retail, get_macro_unemployment,
            get_market_sector_flow, get_market_north_flow,
            get_market_overall_flow, get_industry_boards_info,
            get_concept_boards_info,
        ]

        for tool in phase2_tools:
            assert tool in FUND_TOOLS, f"工具 {tool.name} 不在FUND_TOOLS列表中"


# ============================================
# 阶段三+四: 专业数据与边缘功能 - 新增工具测试
# ============================================


class TestPhaseThreeFourTools:
    """测试阶段三(18个)和阶段四(20个)新增工具"""

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_bond_yield_curve_info(self, mock_get_adapter):
        """测试债券收益率曲线工具"""
        from fund_cli.ai.tools import get_bond_yield_curve_info
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_bond_yield_curve.return_value = pd.DataFrame({
            'date': ['2024-01'], 'yield_1y': ['2.1%'], 'yield_10y': ['2.8%']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_bond_yield_curve_info.invoke({})
        assert "债券" in result or "收益率" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_convertible_bonds_list(self, mock_get_adapter):
        """测试可转债列表工具"""
        from fund_cli.ai.tools import get_convertible_bonds_list
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_convertible_bonds.return_value = pd.DataFrame({
            'code': ['110001'], 'name': ['中行转债'], 'price': ['105.5']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_convertible_bonds_list.invoke({"limit": 5})
        assert "可转债" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_market_valuation_info(self, mock_get_adapter):
        """测试A股估值工具"""
        from fund_cli.ai.tools import get_market_valuation_info
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_a_share_valuation.return_value = pd.DataFrame({
            'index': ['上证指数'], 'pe': ['15.2'], 'pb': ['1.3']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_market_valuation_info.invoke({})
        assert "估值" in result or "PE" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_stock_fund_flow_detail(self, mock_get_adapter):
        """测试个股资金流向工具"""
        from fund_cli.ai.tools import get_stock_fund_flow_detail
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_stock_fund_flow.return_value = pd.DataFrame({
            'date': ['2024-01-15'], 'main_net_inflow': ['5.2亿']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_stock_fund_flow_detail.invoke({"code": "600519", "market": "sh"})
        assert "资金" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_company_aum_rank(self, mock_get_adapter):
        """测试基金公司规模排行工具"""
        from fund_cli.ai.tools import get_fund_company_aum_rank
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_fund_company_aum.return_value = pd.DataFrame({
            'name': ['华夏基金', '易方达基金'], 'aum': ['15000亿', '12000亿']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_fund_company_aum_rank.invoke({"limit": 5})
        assert "基金公司" in result or "规模" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_holder_structure_info(self, mock_get_adapter):
        """测试持有人结构工具"""
        from fund_cli.ai.tools import get_fund_holder_structure_info
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_fund_holder_structure.return_value = pd.DataFrame({
            'holder_type': ['个人', '机构'], 'ratio': ['45.2%', '54.8%']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_fund_holder_structure_info.invoke({"fund_code": "000001"})
        assert "持有人" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_all_fund_managers_list(self, mock_get_adapter):
        """测试基金经理列表工具"""
        from fund_cli.ai.tools import get_all_fund_managers_list
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_all_fund_managers.return_value = pd.DataFrame({
            'name': ['张三', '李四'], 'fund_code': ['000001', '000002']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_all_fund_managers_list.invoke({"limit": 5})
        assert "基金经理" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_bond_holdings_info(self, mock_get_adapter):
        """测试基金债券持仓工具"""
        from fund_cli.ai.tools import get_fund_bond_holdings_info
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_fund_bond_holdings.return_value = pd.DataFrame({
            'bond_name': ['国债2301'], 'ratio': ['5.2%']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_fund_bond_holdings_info.invoke({"fund_code": "000001"})
        assert "债券" in result or "持仓" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_industry_allocation_info(self, mock_get_adapter):
        """测试基金行业配置工具"""
        from fund_cli.ai.tools import get_fund_industry_allocation_info
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_fund_industry_allocation.return_value = pd.DataFrame({
            'industry': ['银行', '电子'], 'ratio': ['15.2%', '12.5%']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_fund_industry_allocation_info.invoke({"fund_code": "000001"})
        assert "行业" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_china_us_bond_spread(self, mock_get_adapter):
        """测试中美利差工具"""
        from fund_cli.ai.tools import get_china_us_bond_spread
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_china_us_bond_yield.return_value = pd.DataFrame({
            'date': ['2024-01'], 'china_10y': ['2.8%'], 'us_10y': ['4.2%']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_china_us_bond_spread.invoke({})
        assert "利差" in result or "中美" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_etf_hist_data(self, mock_get_adapter):
        """测试ETF历史行情工具"""
        from fund_cli.ai.tools import get_etf_hist_data
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_etf_hist.return_value = pd.DataFrame({
            'date': ['2024-01-15'], 'close': ['3.5'], 'volume': ['1000万']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_etf_hist_data.invoke({"code": "510050", "period": "1m"})
        assert "ETF" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_lof_spot_info(self, mock_get_adapter):
        """测试LOF实时行情工具"""
        from fund_cli.ai.tools import get_lof_spot_info
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_lof_spot.return_value = pd.DataFrame({
            'code': ['163001'], 'name': ['兴业趋势'], 'price': ['1.5']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_lof_spot_info.invoke({})
        assert "LOF" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_purchase_status_info(self, mock_get_adapter):
        """测试基金申赎状态工具"""
        from fund_cli.ai.tools import get_fund_purchase_status_info
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_fund_purchase_status.return_value = pd.DataFrame({
            'code': ['000001'], 'name': ['华夏成长'], 'purchase_status': ['开放申购']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_fund_purchase_status_info.invoke({})
        assert "申购" in result or "赎回" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_index_spot_em_info(self, mock_get_adapter):
        """测试东方财富指数行情工具"""
        from fund_cli.ai.tools import get_index_spot_em_info
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_index_spot_em.return_value = pd.DataFrame({
            'code': ['000001'], 'name': ['上证指数'], 'price': ['3000']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_index_spot_em_info.invoke({"category": "沪深重要指数"})
        assert "指数" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_dividend_ranking(self, mock_get_adapter):
        """测试基金分红排行工具"""
        from fund_cli.ai.tools import get_fund_dividend_ranking
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_fund_dividend_rank.return_value = pd.DataFrame({
            'code': ['000001'], 'name': ['华夏成长'], 'dividend': ['5.2亿']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_fund_dividend_ranking.invoke({"limit": 5})
        assert "分红" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_fund_rating_sh_detail(self, mock_get_adapter):
        """测试上海证券评级工具"""
        from fund_cli.ai.tools import get_fund_rating_sh_detail
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_fund_rating_sh.return_value = pd.DataFrame({
            'code': ['000001'], 'name': ['华夏成长'], 'rating': ['5星']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_fund_rating_sh_detail.invoke({})
        assert "评级" in result or "上海" in result

    @patch('fund_cli.ai.tools._get_adapter')
    def test_get_index_fund_info_detail(self, mock_get_adapter):
        """测试指数基金信息工具"""
        from fund_cli.ai.tools import get_index_fund_info_detail
        import pandas as pd
        mock_adapter = MagicMock()
        mock_adapter.get_index_fund_info.return_value = pd.DataFrame({
            'code': ['510050'], 'name': ['50ETF'], 'return_1y': ['10.5%']
        })
        mock_get_adapter.return_value = mock_adapter
        result = get_index_fund_info_detail.invoke({"category": "全部"})
        assert "指数" in result

    def test_all_phase_tools_in_list(self):
        """测试所有阶段三+四工具都在FUND_TOOLS列表中"""
        from fund_cli.ai.tools import FUND_TOOLS

        phase34_tool_names = [
            # 阶段三
            'get_bond_yield_curve_info', 'get_bond_spot_market_info',
            'get_convertible_bonds_list', 'get_convertible_bond_detail_info',
            'get_bond_info', 'get_market_valuation_info',
            'get_index_valuation_info', 'get_market_pe_pb_info',
            'get_stock_fund_flow_detail', 'get_fund_company_aum_rank',
            'get_fund_aum_trend_analysis', 'get_fund_scale_change_analysis',
            'get_fund_holder_structure_info', 'get_all_fund_managers_list',
            'get_fund_bond_holdings_info', 'get_fund_industry_allocation_info',
            'get_fund_portfolio_change_info', 'get_china_us_bond_spread',
            # 阶段四
            'get_etf_hist_data', 'get_lof_hist_data',
            'get_etf_minute_data', 'get_lof_minute_data',
            'get_lof_spot_info', 'get_fund_purchase_status_info',
            'get_fund_daily_nav_overview', 'get_fund_category_spot_info',
            'get_etf_spot_ths_info', 'get_index_spot_em_info',
            'get_index_spot_sina_info', 'get_index_hist_data',
            'get_index_minute_data', 'get_fund_dividend_ranking',
            'get_fund_rating_sh_detail', 'get_fund_rating_zs_detail',
            'get_fund_rating_ja_detail', 'get_lcx_fund_ranking',
            'get_hk_fund_ranking', 'get_index_fund_info_detail',
        ]

        actual_names = [t.name for t in FUND_TOOLS]
        for name in phase34_tool_names:
            assert name in actual_names, f"工具 {name} 不在FUND_TOOLS列表中"
