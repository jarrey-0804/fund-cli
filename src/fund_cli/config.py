"""
Fund CLI 配置管理

使用 Pydantic Settings 管理应用配置，支持环境变量和 .env 文件。
"""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataConfig(BaseSettings):
    """数据源配置"""

    model_config = SettingsConfigDict(env_prefix="FUND_DATA_")

    # AKShare 配置
    akshare_enabled: bool = Field(default=True, description="是否启用AKShare数据源")

    # Tushare 配置
    tushare_token: str | None = Field(default=None, description="Tushare API Token")

    # Wind 配置
    wind_enabled: bool = Field(default=False, description="是否启用Wind数据源")
    wind_username: str | None = Field(default=None, description="Wind用户名")
    wind_password: str | None = Field(default=None, description="Wind密码")

    # 缓存配置
    cache_ttl: int = Field(default=3600, description="缓存过期时间（秒）")
    cache_dir: str = Field(default="~/.fund_cli/cache", description="缓存目录")

    @field_validator("cache_dir")
    @classmethod
    def expand_cache_dir(cls, v: str) -> str:
        """展开缓存目录路径"""
        return str(Path(v).expanduser())


class AnalysisConfig(BaseSettings):
    """分析配置"""

    model_config = SettingsConfigDict(env_prefix="FUND_ANALYSIS_")

    risk_free_rate: float = Field(default=0.03, description="无风险利率")
    default_benchmark: str = Field(default="000300", description="默认基准指数代码")
    default_period: str = Field(default="1y", description="默认分析周期")

    @field_validator("risk_free_rate")
    @classmethod
    def validate_risk_free_rate(cls, v: float) -> float:
        """验证无风险利率范围"""
        if not 0 <= v <= 1:
            raise ValueError("无风险利率必须在 0-1 之间")
        return v


class AIConfig(BaseSettings):
    """AI配置（V2.0功能）"""

    model_config = SettingsConfigDict(env_prefix="FUND_AI_")

    provider: str = Field(default="openai", description="LLM提供商: openai/qwen/litellm")
    model: str = Field(default="gpt-4", description="模型名称")
    api_key: str | None = Field(default=None, description="API密钥")
    api_base: str | None = Field(default=None, description="API基础URL")
    temperature: float = Field(default=0.7, description="温度参数(0-2)")
    max_tokens: int = Field(default=2000, description="最大token数")
    timeout: int = Field(default=30, description="请求超时(秒)")
    retry_count: int = Field(default=3, description="重试次数")

    # Qwen专用配置
    qwen_api_key: str | None = Field(default=None, description="阿里云Qwen API Key")
    qwen_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/api/v1", description="Qwen API地址"
    )
    qwen_model: str = Field(
        default="qwen-max", description="Qwen模型: qwen-max/qwen-plus/qwen-turbo"
    )

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """验证温度参数范围"""
        if not 0 <= v <= 2:
            raise ValueError("温度参数必须在 0-2 之间")
        return v

    @field_validator("retry_count")
    @classmethod
    def validate_retry_count(cls, v: int) -> int:
        """验证重试次数"""
        if not 0 <= v <= 10:
            raise ValueError("重试次数必须在 0-10 之间")
        return v


class LogConfig(BaseSettings):
    """日志配置"""

    model_config = SettingsConfigDict(env_prefix="FUND_LOG_")

    level: str = Field(default="INFO", description="日志级别")
    file: str | None = Field(default=None, description="日志文件路径")


class OutputConfig(BaseSettings):
    """输出格式配置"""

    model_config = SettingsConfigDict(env_prefix="FUND_OUTPUT_")

    default_format: str = Field(default="table", description="默认输出格式")
    csv_encoding: str = Field(default="utf-8-sig", description="CSV编码")
    csv_delimiter: str = Field(default=",", description="CSV分隔符")
    json_indent: int = Field(default=2, description="JSON缩进")
    number_decimal: int = Field(default=2, description="数字小数位")
    date_format: str = Field(default="%Y-%m-%d", description="日期格式")


class DatabaseConfig(BaseSettings):
    """数据库配置（V3.0 - Agent 持久化）"""

    model_config = SettingsConfigDict(env_prefix="FUND_DB_")

    use_postgres: bool = Field(default=False, description="使用 PostgreSQL 持久化对话历史")
    host: str = Field(default="localhost", description="数据库主机")
    port: int = Field(default=5432, description="数据库端口")
    database: str = Field(default="fund_cli", description="数据库名")
    user: str = Field(default="fund_cli", description="用户名")
    password: str = Field(default="", description="密码")

    @property
    def connection_string(self) -> str:
        """获取 PostgreSQL 连接字符串"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class AgentConfig(BaseSettings):
    """Agent 配置（V3.0 - LangGraph Agent）"""

    model_config = SettingsConfigDict(env_prefix="FUND_AGENT_")

    enable_human_review: bool = Field(default=False, description="启用人工审核节点")
    human_review_timeout: int = Field(default=300, description="人工审核超时时间（秒）")
    max_tool_calls: int = Field(default=10, description="单次对话最大工具调用次数")
    use_chroma_memory: bool = Field(default=False, description="使用 ChromaDB 长期记忆")
    chroma_persist_dir: str = Field(default="~/.fund_cli/chroma", description="ChromaDB 持久化目录")


class AppConfig(BaseSettings):
    """应用主配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # 应用信息
    app_name: str = Field(default="Fund CLI", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    dev_mode: bool = Field(default=False, description="开发模式")

    # 嵌套配置
    data: DataConfig = Field(default_factory=DataConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)


# 全局配置实例
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """获取配置实例（单例模式）"""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """重新加载配置"""
    global _config
    _config = AppConfig()
    return _config


# 便捷访问
config = get_config()
