"""
LLM 提供商管理（V2.0 实现）

管理多个 LLM 提供商的连接和调用，支持OpenAI、阿里云Qwen等。
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

import requests

from fund_cli.config import AIConfig


class LLMProvider(ABC):
    """LLM 提供商抽象基类"""

    def __init__(self, config: AIConfig):
        self.config = config

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """生成文本

        Args:
            prompt: 输入提示词
            **kwargs: 额外参数

        Returns:
            生成的文本
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查提供商是否可用

        Returns:
            是否可用
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否有效

        Returns:
            配置是否有效
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI 提供商"""

    def __init__(self, config: AIConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model or "gpt-4"
        self.base_url = config.api_base or "https://api.openai.com/v1"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """使用 OpenAI API 生成文本"""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        response = self._call_with_retry(f"{self.base_url}/chat/completions", headers, payload)

        if response and "choices" in response:
            return response["choices"][0]["message"]["content"]
        raise RuntimeError("Invalid response from OpenAI API")

    def is_available(self) -> bool:
        """检查OpenAI API是否可用"""
        if not self.api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=self.config.timeout,
            )
            return response.status_code == 200
        except Exception:
            return False

    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.api_key and self.model)

    def _call_with_retry(self, url: str, headers: dict, payload: dict) -> dict | None:
        """带重试的API调用"""
        last_error = None
        for attempt in range(self.config.retry_count):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout,
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                last_error = e
                if attempt < self.config.retry_count - 1:
                    time.sleep(2**attempt)  # 指数退避
        raise RuntimeError(
            f"API call failed after {self.config.retry_count} attempts: {last_error}"
        )


class QwenProvider(LLMProvider):
    """阿里云Qwen 提供商"""

    def __init__(self, config: AIConfig):
        super().__init__(config)
        self.api_key = config.qwen_api_key or config.api_key
        self.model = config.qwen_model or "qwen-max"
        self.base_url = config.qwen_base_url or "https://dashscope.aliyuncs.com/api/v1"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """使用 Qwen API 生成文本"""
        if not self.api_key:
            raise ValueError("Qwen API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": kwargs.get("model", self.model),
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "parameters": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "result_format": "message",
            },
        }

        response = self._call_with_retry(
            f"{self.base_url}/services/aigc/text-generation/generation",
            headers,
            payload,
        )

        if response and "output" in response:
            return response["output"]["choices"][0]["message"]["content"]
        raise RuntimeError("Invalid response from Qwen API")

    def is_available(self) -> bool:
        """检查Qwen API是否可用"""
        if not self.api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            # 使用简单的模型列表接口测试
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=self.config.timeout,
            )
            return response.status_code == 200
        except Exception:
            return False

    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.api_key and self.model)

    def _call_with_retry(self, url: str, headers: dict, payload: dict) -> dict | None:
        """带重试的API调用"""
        last_error = None
        for attempt in range(self.config.retry_count):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout,
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                last_error = e
                if attempt < self.config.retry_count - 1:
                    time.sleep(2**attempt)  # 指数退避
        raise RuntimeError(
            f"API call failed after {self.config.retry_count} attempts: {last_error}"
        )


class LiteLLMProvider(LLMProvider):
    """LiteLLM 统一封装提供商"""

    def __init__(self, config: AIConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model or "gpt-4"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """使用 LiteLLM 生成文本"""
        try:
            import litellm

            litellm.api_key = self.api_key

            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            )
            return response.choices[0].message.content
        except ImportError as err:
            raise RuntimeError("litellm not installed. Install with: pip install litellm") from err
        except Exception as e:
            raise RuntimeError(f"LiteLLM API error: {e}") from e

    def is_available(self) -> bool:
        """检查LiteLLM是否可用"""
        try:
            import importlib.util

            spec = importlib.util.find_spec("litellm")
            if spec is None:
                return False
            return bool(self.api_key)
        except ImportError:
            return False

    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.api_key and self.model)


def get_provider(config: AIConfig | None = None) -> LLMProvider:
    """
    获取 LLM 提供商实例

    Args:
        config: AI配置，如果为None则使用默认配置

    Returns:
        LLM 提供商实例

    Raises:
        ValueError: 如果提供商类型不支持
    """
    if config is None:
        from fund_cli.config import get_config

        config = get_config().ai

    providers = {
        "openai": OpenAIProvider,
        "qwen": QwenProvider,
        "litellm": LiteLLMProvider,
    }

    provider_name = config.provider.lower()
    provider_class = providers.get(provider_name)

    if provider_class is None:
        raise ValueError(
            f"不支持的提供商: {provider_name}. " f"支持的提供商: {', '.join(providers.keys())}"
        )

    return provider_class(config)
