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


class TestOpenAIProviderAdvanced:
    """OpenAIProvider高级测试"""

    @patch("requests.post")
    def test_generate_with_custom_kwargs(self, mock_post):
        """测试生成时使用自定义参数"""
        mock_response = Mock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Custom response"}}]}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        config = AIConfig(api_key="test-key", model="gpt-4", retry_count=1)
        provider = OpenAIProvider(config)

        result = provider.generate(
            "test prompt",
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=1000
        )

        assert result == "Custom response"
        # 验证调用参数
        call_args = mock_post.call_args
        payload = call_args.kwargs['json']
        assert payload['model'] == "gpt-3.5-turbo"
        assert payload['temperature'] == 0.5
        assert payload['max_tokens'] == 1000

    @patch("requests.post")
    def test_generate_with_retry_success_on_second_attempt(self, mock_post):
        """测试重试成功-第二次成功"""
        from requests import RequestException

        # 第一次失败，第二次成功
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = RequestException("Connection error")

        mock_response_success = Mock()
        mock_response_success.json.return_value = {"choices": [{"message": {"content": "Success"}}]}
        mock_response_success.raise_for_status = Mock()

        mock_post.side_effect = [mock_response_fail, mock_response_success]

        config = AIConfig(api_key="test-key", retry_count=3)
        provider = OpenAIProvider(config)

        result = provider.generate("test prompt")

        assert result == "Success"
        assert mock_post.call_count == 2

    @patch("requests.post")
    def test_generate_retry_exhausted(self, mock_post):
        """测试重试耗尽"""
        from requests import RequestException

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = RequestException("Persistent error")
        mock_post.return_value = mock_response

        config = AIConfig(api_key="test-key", retry_count=2)
        provider = OpenAIProvider(config)

        with pytest.raises(RuntimeError):
            provider.generate("test prompt")

        assert mock_post.call_count == 2

    @patch("requests.post")
    def test_generate_invalid_response(self, mock_post):
        """测试无效响应"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid"}  # 缺少 choices
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        config = AIConfig(api_key="test-key", retry_count=1)
        provider = OpenAIProvider(config)

        with pytest.raises((RuntimeError, KeyError)):
            provider.generate("test prompt")

    @patch("requests.get")
    def test_is_available_with_exception(self, mock_get):
        """测试可用性检测-异常情况"""
        mock_get.side_effect = Exception("Network error")

        config = AIConfig(api_key="test-key")
        provider = OpenAIProvider(config)

        # 异常时返回 False
        assert provider.is_available() is False

    def test_is_available_without_api_key(self):
        """测试无API Key时不可用"""
        config = AIConfig(api_key=None)
        provider = OpenAIProvider(config)

        assert provider.is_available() is False

    def test_validate_config_with_empty_model(self):
        """测试配置验证-空模型"""
        config = AIConfig(api_key="test-key", model="")
        provider = OpenAIProvider(config)

        # 空字符串模型名被视为有效（因为 bool("") == False，但 model 属性会被设置为默认值）
        # 实际上 self.model = config.model or "gpt-4"，所以空字符串会使用默认值
        assert provider.model == "gpt-4"  # 使用了默认值
        assert provider.validate_config() is True

    def test_validate_config_with_empty_api_key(self):
        """测试配置验证-空API Key"""
        config = AIConfig(api_key="", model="gpt-4")
        provider = OpenAIProvider(config)

        # 空字符串被视为无效
        assert provider.validate_config() is False

    @patch("requests.post")
    def test_generate_empty_choices(self, mock_post):
        """测试空choices响应"""
        mock_response = Mock()
        mock_response.json.return_value = {"choices": []}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        config = AIConfig(api_key="test-key", retry_count=1)
        provider = OpenAIProvider(config)

        with pytest.raises((RuntimeError, IndexError)):
            provider.generate("test prompt")


class TestQwenProviderAdvanced:
    """QwenProvider高级测试"""

    @patch("requests.post")
    def test_generate_with_custom_kwargs(self, mock_post):
        """测试生成时使用自定义参数"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "output": {"choices": [{"message": {"content": "Custom Qwen response"}}]}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        config = AIConfig(qwen_api_key="test-key", retry_count=1)
        provider = QwenProvider(config)

        result = provider.generate(
            "test prompt",
            model="qwen-plus",
            temperature=0.8,
            max_tokens=2000
        )

        assert result == "Custom Qwen response"
        call_args = mock_post.call_args
        payload = call_args.kwargs['json']
        assert payload['model'] == "qwen-plus"
        assert payload['parameters']['temperature'] == 0.8
        assert payload['parameters']['max_tokens'] == 2000

    @patch("requests.post")
    def test_generate_retry_exhausted(self, mock_post):
        """测试重试耗尽"""
        from requests import RequestException

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = RequestException("Qwen API error")
        mock_post.return_value = mock_response

        config = AIConfig(qwen_api_key="test-key", retry_count=2)
        provider = QwenProvider(config)

        with pytest.raises(RuntimeError):
            provider.generate("test prompt")

        assert mock_post.call_count == 2

    @patch("requests.post")
    def test_generate_invalid_response(self, mock_post):
        """测试无效响应"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid"}  # 缺少 output
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        config = AIConfig(qwen_api_key="test-key", retry_count=1)
        provider = QwenProvider(config)

        with pytest.raises((RuntimeError, KeyError)):
            provider.generate("test prompt")

    @patch("requests.get")
    def test_is_available_with_exception(self, mock_get):
        """测试可用性检测-异常情况"""
        mock_get.side_effect = Exception("Network error")

        config = AIConfig(qwen_api_key="test-key")
        provider = QwenProvider(config)

        assert provider.is_available() is False

    @patch("requests.get")
    def test_is_available_true(self, mock_get):
        """测试可用性检测-可用"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        config = AIConfig(qwen_api_key="test-key")
        provider = QwenProvider(config)

        assert provider.is_available() is True

    @patch("requests.get")
    def test_is_available_false(self, mock_get):
        """测试可用性检测-不可用"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        config = AIConfig(qwen_api_key="test-key")
        provider = QwenProvider(config)

        assert provider.is_available() is False

    def test_is_available_without_api_key(self):
        """测试无API Key时不可用"""
        config = AIConfig(qwen_api_key=None, api_key=None)
        provider = QwenProvider(config)

        assert provider.is_available() is False

    def test_validate_config_with_empty_model(self):
        """测试配置验证-空模型"""
        config = AIConfig(qwen_api_key="test-key", qwen_model="")
        provider = QwenProvider(config)

        # 空字符串模型名会使用默认值
        assert provider.model == "qwen-max"  # 使用了默认值
        assert provider.validate_config() is True

    @patch("requests.post")
    def test_generate_empty_choices(self, mock_post):
        """测试空choices响应"""
        mock_response = Mock()
        mock_response.json.return_value = {"output": {"choices": []}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        config = AIConfig(qwen_api_key="test-key", retry_count=1)
        provider = QwenProvider(config)

        with pytest.raises((RuntimeError, IndexError)):
            provider.generate("test prompt")


class TestLiteLLMProviderAdvanced:
    """LiteLLMProvider高级测试"""

    def test_init_with_config(self):
        """测试配置初始化"""
        config = AIConfig(api_key="test-key", model="gpt-4")
        provider = LiteLLMProvider(config)

        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4"

    def test_init_with_defaults(self):
        """测试默认配置"""
        config = AIConfig()
        provider = LiteLLMProvider(config)

        assert provider.model == "gpt-4"

    def test_validate_config_invalid(self):
        """测试配置验证-无效"""
        config = AIConfig(api_key=None, model="gpt-4")
        provider = LiteLLMProvider(config)

        assert provider.validate_config() is False

    def test_validate_config_with_empty_model(self):
        """测试配置验证-空模型"""
        config = AIConfig(api_key="test-key", model="")
        provider = LiteLLMProvider(config)

        # 空字符串模型名会使用默认值
        assert provider.model == "gpt-4"  # 使用了默认值
        assert provider.validate_config() is True

    def test_generate_import_error(self):
        """测试litellm未安装时生成失败"""
        config = AIConfig(api_key="test-key")
        provider = LiteLLMProvider(config)

        with patch.dict("sys.modules", {"litellm": None}):
            with pytest.raises(RuntimeError, match="litellm not installed"):
                provider.generate("test prompt")

    def test_generate_success(self):
        """测试成功生成"""
        config = AIConfig(api_key="test-key", model="gpt-4")
        provider = LiteLLMProvider(config)

        # Mock litellm
        mock_litellm = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="LiteLLM response"))]
        mock_litellm.completion.return_value = mock_response

        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            result = provider.generate("test prompt")

        assert result == "LiteLLM response"

    def test_generate_with_custom_kwargs(self):
        """测试生成时使用自定义参数"""
        config = AIConfig(api_key="test-key", model="gpt-4", temperature=0.7, max_tokens=1000)
        provider = LiteLLMProvider(config)

        mock_litellm = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Custom response"))]
        mock_litellm.completion.return_value = mock_response

        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            result = provider.generate(
                "test prompt",
                temperature=0.5,
                max_tokens=500
            )

        assert result == "Custom response"
        # 验证调用参数
        call_kwargs = mock_litellm.completion.call_args.kwargs
        assert call_kwargs['temperature'] == 0.5
        assert call_kwargs['max_tokens'] == 500

    def test_generate_api_error(self):
        """测试API错误"""
        config = AIConfig(api_key="test-key")
        provider = LiteLLMProvider(config)

        mock_litellm = Mock()
        mock_litellm.completion.side_effect = Exception("API error")

        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            with pytest.raises(RuntimeError, match="LiteLLM API error"):
                provider.generate("test prompt")

    def test_is_available_with_api_key(self):
        """测试有API Key时可用"""
        config = AIConfig(api_key="test-key")
        provider = LiteLLMProvider(config)

        # 模拟litellm已安装
        mock_spec = Mock()
        assert mock_spec is not None

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = mock_spec
            assert provider.is_available() is True

    def test_is_available_without_api_key(self):
        """测试无API Key时不可用"""
        config = AIConfig(api_key=None)
        provider = LiteLLMProvider(config)

        assert provider.is_available() is False


class TestGetProviderAdvanced:
    """get_provider工厂函数高级测试"""

    def test_get_litellm_provider(self):
        """测试获取LiteLLM提供商"""
        config = AIConfig(provider="litellm", api_key="test-key")
        provider = get_provider(config)

        assert isinstance(provider, LiteLLMProvider)

    def test_get_provider_lowercase(self):
        """测试提供商名称小写"""
        config = AIConfig(provider="openai", api_key="test-key")
        provider = get_provider(config)

        assert isinstance(provider, OpenAIProvider)

    def test_get_provider_mixed_case(self):
        """测试提供商名称混合大小写"""
        config = AIConfig(provider="OpenAi", api_key="test-key")
        provider = get_provider(config)

        assert isinstance(provider, OpenAIProvider)

    def test_get_provider_whitespace(self):
        """测试提供商名称包含空格（应该失败）"""
        config = AIConfig(provider=" openai ")

        # 空格不会被自动去除，应该失败
        with pytest.raises(ValueError, match="不支持的提供商"):
            get_provider(config)


class TestProviderConfigInheritance:
    """测试提供商配置继承"""

    def test_openai_provider_config_attribute(self):
        """测试OpenAI提供商配置属性"""
        config = AIConfig(api_key="test-key", temperature=0.8, max_tokens=1500)
        provider = OpenAIProvider(config)

        assert provider.config == config
        assert provider.config.temperature == 0.8
        assert provider.config.max_tokens == 1500

    def test_qwen_provider_config_attribute(self):
        """测试Qwen提供商配置属性"""
        config = AIConfig(qwen_api_key="test-key", temperature=0.5)
        provider = QwenProvider(config)

        assert provider.config == config
        assert provider.config.temperature == 0.5

    def test_litellm_provider_config_attribute(self):
        """测试LiteLLM提供商配置属性"""
        config = AIConfig(api_key="test-key", model="gpt-4")
        provider = LiteLLMProvider(config)

        assert provider.config == config


class TestProviderTimeout:
    """测试提供商超时配置"""

    @patch("requests.post")
    def test_openai_timeout_config(self, mock_post):
        """测试OpenAI超时配置"""
        mock_response = Mock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "test"}}]}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        config = AIConfig(api_key="test-key", timeout=60, retry_count=1)
        provider = OpenAIProvider(config)

        provider.generate("test prompt")

        # 验证超时参数
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs['timeout'] == 60

    @patch("requests.get")
    def test_openai_is_available_timeout(self, mock_get):
        """测试OpenAI可用性检测超时"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        config = AIConfig(api_key="test-key", timeout=60)
        provider = OpenAIProvider(config)

        provider.is_available()

        # 验证超时参数
        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs['timeout'] == 60

    @patch("requests.post")
    def test_qwen_timeout_config(self, mock_post):
        """测试Qwen超时配置"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "output": {"choices": [{"message": {"content": "test"}}]}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        config = AIConfig(qwen_api_key="test-key", timeout=45, retry_count=1)
        provider = QwenProvider(config)

        provider.generate("test prompt")

        # 验证超时参数
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs['timeout'] == 45
