"""
AI提供商单元测试
"""

from unittest.mock import Mock, patch

import pytest

from fund_cli.ai.providers import (
    LiteLLMProvider,
    LLMProvider,
    OpenAIProvider,
    QwenProvider,
    get_provider,
)
from fund_cli.config import AIConfig


class MockLLMProvider(LLMProvider):
    """测试用Mock提供商"""

    def __init__(self, config):
        super().__init__(config)
        self.mock_response = "Mock response"

    def generate(self, prompt, **kwargs):
        return self.mock_response

    def is_available(self):
        return True

    def validate_config(self):
        return True


class TestLLMProvider:
    """LLMProvider基类测试"""

    def test_abstract_methods(self):
        """测试抽象方法"""
        config = AIConfig()

        # 不能直接实例化抽象类
        with pytest.raises(TypeError):
            LLMProvider(config)


class TestOpenAIProvider:
    """OpenAIProvider测试"""

    def test_init_with_config(self):
        """测试配置初始化"""
        config = AIConfig(api_key="test-key", model="gpt-4", api_base="https://api.openai.com/v1")
        provider = OpenAIProvider(config)

        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4"
        assert provider.base_url == "https://api.openai.com/v1"

    def test_init_with_defaults(self):
        """测试默认配置"""
        config = AIConfig()
        provider = OpenAIProvider(config)

        assert provider.model == "gpt-4"
        assert provider.base_url == "https://api.openai.com/v1"

    def test_validate_config_valid(self):
        """测试配置验证-有效"""
        config = AIConfig(api_key="test-key", model="gpt-4")
        provider = OpenAIProvider(config)

        assert provider.validate_config() is True

    def test_validate_config_invalid(self):
        """测试配置验证-无效"""
        config = AIConfig(api_key=None, model="gpt-4")
        provider = OpenAIProvider(config)

        assert provider.validate_config() is False

    def test_generate_without_api_key(self):
        """测试无API Key时生成失败"""
        config = AIConfig(api_key=None)
        provider = OpenAIProvider(config)

        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            provider.generate("test prompt")

    @patch("requests.post")
    def test_generate_success(self, mock_post):
        """测试成功生成"""
        mock_response = Mock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Generated text"}}]}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        config = AIConfig(api_key="test-key", retry_count=1)
        provider = OpenAIProvider(config)

        result = provider.generate("test prompt")

        assert result == "Generated text"
        mock_post.assert_called_once()

    @patch("requests.get")
    def test_is_available_true(self, mock_get):
        """测试可用性检测-可用"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        config = AIConfig(api_key="test-key")
        provider = OpenAIProvider(config)

        assert provider.is_available() is True

    @patch("requests.get")
    def test_is_available_false(self, mock_get):
        """测试可用性检测-不可用"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        config = AIConfig(api_key="test-key")
        provider = OpenAIProvider(config)

        assert provider.is_available() is False


class TestQwenProvider:
    """QwenProvider测试"""

    def test_init_with_config(self):
        """测试配置初始化"""
        config = AIConfig(
            qwen_api_key="test-key",
            qwen_model="qwen-max",
            qwen_base_url="https://dashscope.aliyuncs.com/api/v1",
        )
        provider = QwenProvider(config)

        assert provider.api_key == "test-key"
        assert provider.model == "qwen-max"
        assert provider.base_url == "https://dashscope.aliyuncs.com/api/v1"

    def test_init_fallback_to_api_key(self):
        """测试使用通用api_key作为fallback"""
        config = AIConfig(api_key="fallback-key", qwen_api_key=None, qwen_model="qwen-plus")
        provider = QwenProvider(config)

        assert provider.api_key == "fallback-key"
        assert provider.model == "qwen-plus"

    def test_validate_config_valid(self):
        """测试配置验证-有效"""
        config = AIConfig(qwen_api_key="test-key", qwen_model="qwen-max")
        provider = QwenProvider(config)

        assert provider.validate_config() is True

    def test_validate_config_invalid(self):
        """测试配置验证-无效"""
        config = AIConfig(qwen_api_key=None, qwen_model="qwen-max")
        provider = QwenProvider(config)

        assert provider.validate_config() is False

    @patch("requests.post")
    def test_generate_success(self, mock_post):
        """测试成功生成"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "output": {"choices": [{"message": {"content": "Qwen generated text"}}]}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        config = AIConfig(qwen_api_key="test-key", retry_count=1)
        provider = QwenProvider(config)

        result = provider.generate("test prompt")

        assert result == "Qwen generated text"
        mock_post.assert_called_once()

    def test_generate_without_api_key(self):
        """测试无API Key时生成失败"""
        config = AIConfig(qwen_api_key=None)
        provider = QwenProvider(config)

        with pytest.raises(ValueError, match="Qwen API key not configured"):
            provider.generate("test prompt")


class TestLiteLLMProvider:
    """LiteLLMProvider测试"""

    def test_validate_config_valid(self):
        """测试配置验证-有效"""
        config = AIConfig(api_key="test-key", model="gpt-4")
        provider = LiteLLMProvider(config)

        assert provider.validate_config() is True

    def test_is_available_without_litellm(self):
        """测试未安装litellm时不可用"""
        config = AIConfig(api_key="test-key")
        provider = LiteLLMProvider(config)

        # 模拟litellm未安装
        with patch.dict("sys.modules", {"litellm": None}):
            assert provider.is_available() is False


class TestGetProvider:
    """get_provider工厂函数测试"""

    def test_get_openai_provider(self):
        """测试获取OpenAI提供商"""
        config = AIConfig(provider="openai", api_key="test-key")
        provider = get_provider(config)

        assert isinstance(provider, OpenAIProvider)

    def test_get_qwen_provider(self):
        """测试获取Qwen提供商"""
        config = AIConfig(provider="qwen", qwen_api_key="test-key")
        provider = get_provider(config)

        assert isinstance(provider, QwenProvider)

    def test_get_provider_case_insensitive(self):
        """测试提供商名称大小写不敏感"""
        config = AIConfig(provider="QWEN", qwen_api_key="test-key")
        provider = get_provider(config)

        assert isinstance(provider, QwenProvider)

    def test_get_provider_invalid(self):
        """测试无效提供商"""
        config = AIConfig(provider="invalid")

        with pytest.raises(ValueError, match="不支持的提供商"):
            get_provider(config)

    def test_get_provider_default_config(self):
        """测试使用默认配置"""
        with patch("fund_cli.config.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.ai = AIConfig(provider="openai", api_key="test-key")
            mock_get_config.return_value = mock_config

            provider = get_provider()

            assert isinstance(provider, OpenAIProvider)
