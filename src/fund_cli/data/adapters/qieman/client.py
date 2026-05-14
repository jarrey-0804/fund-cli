"""
Qieman MCP 客户端

实现与且慢 MCP 服务器的 JSON-RPC 2.0 通信。
"""

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class QiemanMCPError(Exception):
    """Qieman MCP 错误"""
    pass


class QiemanMCPClient:
    """
    Qieman MCP 客户端
    
    通过 JSON-RPC 2.0 协议与且慢 MCP 服务器通信。
    
    Attributes:
        api_key: API 密钥
        base_url: MCP 服务器 URL
        timeout: 请求超时时间（秒）
        max_retries: 最大重试次数
    """
    
    DEFAULT_BASE_URL = "https://stargate.yingmi.com/mcp/v2"
    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_RETRIES = 3
    
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ):
        """
        初始化 MCP 客户端
        
        Args:
            api_key: API 密钥
            base_url: MCP 服务器 URL，默认使用官方地址
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.api_key = api_key
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries or self.DEFAULT_MAX_RETRIES
        self._request_id = 0
        self._tools_cache: list[dict] | None = None
        
    def _get_request_id(self) -> int:
        """获取下一个请求 ID"""
        self._request_id += 1
        return self._request_id
    
    def _build_headers(self) -> dict[str, str]:
        """构建请求头"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "x-api-key": self.api_key,
        }
    
    def _build_payload(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        构建 JSON-RPC 2.0 请求体
        
        Args:
            method: RPC 方法名
            params: 方法参数
            
        Returns:
            JSON-RPC 请求体
        """
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._get_request_id(),
        }
    
    def _parse_response(self, response: httpx.Response) -> dict[str, Any]:
        """
        解析响应
        
        Args:
            response: HTTP 响应
            
        Returns:
            解析后的响应数据
            
        Raises:
            QiemanMCPError: 响应错误
        """
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise QiemanMCPError(f"响应解析失败: {e}") from e
        
        if "error" in data:
            error = data["error"]
            raise QiemanMCPError(
                f"MCP 错误: {error.get('message', str(error))}"
            )
        
        return data.get("result", {})
    
    def _request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        发送 JSON-RPC 请求
        
        Args:
            method: RPC 方法名
            params: 方法参数
            
        Returns:
            响应结果
            
        Raises:
            QiemanMCPError: 请求失败
        """
        payload = self._build_payload(method, params)
        headers = self._build_headers()
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        self.base_url,
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    return self._parse_response(response)
                    
            except httpx.HTTPStatusError as e:
                last_error = QiemanMCPError(
                    f"HTTP 错误: {e.response.status_code} - {e.response.text}"
                )
                logger.warning(
                    f"请求失败 (尝试 {attempt + 1}/{self.max_retries}): {last_error}"
                )
            except httpx.RequestError as e:
                last_error = QiemanMCPError(f"网络错误: {e}")
                logger.warning(
                    f"网络错误 (尝试 {attempt + 1}/{self.max_retries}): {e}"
                )
            except QiemanMCPError:
                raise
            except Exception as e:
                last_error = QiemanMCPError(f"未知错误: {e}")
                logger.error(f"未知错误: {e}")
        
        raise last_error or QiemanMCPError("请求失败")
    
    def list_tools(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """
        获取可用工具列表
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            工具列表
        """
        if self._tools_cache and not force_refresh:
            return self._tools_cache
        
        result = self._request("tools/list")
        self._tools_cache = result.get("tools", [])
        return self._tools_cache
    
    def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
            
        Raises:
            QiemanMCPError: 调用失败
        """
        params = {
            "name": tool_name,
            "arguments": arguments or {},
        }
        
        result = self._request("tools/call", params)
        
        # 解析 content 格式的响应
        if "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                first_content = content[0]
                if first_content.get("type") == "text":
                    text = first_content.get("text", "{}")
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return {"raw_text": text}
            return content
        
        return result
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            服务是否可用
        """
        try:
            self.list_tools(force_refresh=True)
            return True
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False
    
    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """
        获取工具信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具信息，不存在则返回 None
        """
        tools = self.list_tools()
        for tool in tools:
            if tool.get("name") == tool_name:
                return tool
        return None
