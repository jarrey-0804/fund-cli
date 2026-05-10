"""
MCP 模块 - Model Context Protocol 服务端

通过 FastMCP 将 fund-cli 的数据查询、基金筛选、组合分析、
宏观经济数据等能力暴露为 MCP 工具，供 AI Agent 或 MCP 客户端调用。

依赖:
    - mcp (可选): Model Context Protocol SDK，未安装时模块功能不可用
      安装方式: pip install "fund-cli[mcp]"

使用示例:
    >>> from fund_cli.mcp.server import create_fund_mcp_server
    >>> server = create_fund_mcp_server()
    >>> server.run(transport="stdio")
"""

__all__ = [
    "create_fund_mcp_server",
]


def __getattr__(name: str):
    """延迟导入，mcp 包未安装时给出友好提示。"""
    if name == "create_fund_mcp_server":
        try:
            from fund_cli.mcp.server import create_fund_mcp_server

            return create_fund_mcp_server
        except ImportError as exc:
            raise ImportError(
                'MCP 模块需要安装 mcp 包。请执行: pip install "fund-cli[mcp]"'
            ) from exc
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
