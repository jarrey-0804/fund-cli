"""AI模块 - LLM提供商、AI分析服务、提示词模板、Agent工具

V3.0 新增:
- FundAgent: LangGraph 驱动的智能 Agent
- 工具定义: 12+ 数据接口工具
- 状态管理: Agent 状态定义
- 记忆系统: ChromaDB 长期记忆（可选）

V3.3 新增:
- FundSelector: 智能选基助手
- PortfolioDoctor: 投资组合诊断
- MarketAnalyst: 市场解读助手

V3.4 新增:
- UserProfile: 用户画像与风险评估
- FundRecommender: 个性化基金推荐
- InvestmentAdvisor: 智能投资建议
"""

# 核心模块（不依赖 langchain）
from fund_cli.ai.portfolio_doctor import (
    PortfolioDoctor,
    PortfolioDiagnosis,
    DiagnosisItem,
    diagnose_portfolio,
)

# 可选导入 - 依赖 langchain 的模块
try:
    from fund_cli.ai.agent import FundAgent, get_fund_agent, reset_fund_agent
except ImportError:
    FundAgent = None  # type: ignore
    get_fund_agent = None  # type: ignore
    reset_fund_agent = None  # type: ignore

try:
    from fund_cli.ai.analyzer import AIAnalyzer
except ImportError:
    AIAnalyzer = None  # type: ignore

try:
    from fund_cli.ai.fund_selector import (
        FundSelector,
        FundRecommendation,
        InvestmentNeed,
        NeedParser,
        select_funds,
    )
except ImportError:
    FundSelector = None  # type: ignore
    FundRecommendation = None  # type: ignore
    InvestmentNeed = None  # type: ignore
    NeedParser = None  # type: ignore
    select_funds = None  # type: ignore

try:
    from fund_cli.ai.market_analyst import (
        MarketAnalyst,
        MarketSentimentReport,
        SectorRotationReport,
        HotspotReport,
        analyze_market_sentiment,
        analyze_sector_rotation,
        track_market_hotspots,
    )
except ImportError:
    MarketAnalyst = None  # type: ignore
    MarketSentimentReport = None  # type: ignore
    SectorRotationReport = None  # type: ignore
    HotspotReport = None  # type: ignore
    analyze_market_sentiment = None  # type: ignore
    analyze_sector_rotation = None  # type: ignore
    track_market_hotspots = None  # type: ignore

try:
    from fund_cli.ai.prompts import PromptTemplates
except ImportError:
    PromptTemplates = None  # type: ignore

try:
    from fund_cli.ai.providers import (
        LiteLLMProvider,
        LLMProvider,
        OpenAIProvider,
        QwenProvider,
        get_provider,
    )
except ImportError:
    LiteLLMProvider = None  # type: ignore
    LLMProvider = None  # type: ignore
    OpenAIProvider = None  # type: ignore
    QwenProvider = None  # type: ignore
    get_provider = None  # type: ignore

try:
    from fund_cli.ai.state import FundAgentState
except ImportError:
    FundAgentState = None  # type: ignore

try:
    from fund_cli.ai.advisor import (
        AdviceType,
        Priority,
        AdviceItem,
        RebalanceSuggestion,
        DCASuggestion,
        InvestmentAdviceReport,
        HoldingAnalyzer,
        RebalanceAdvisor,
        DCAAdvisor,
        RiskAlerter,
        InvestmentAdvisor,
        generate_investment_advice,
    )
except ImportError:
    AdviceType = None  # type: ignore
    Priority = None  # type: ignore
    AdviceItem = None  # type: ignore
    RebalanceSuggestion = None  # type: ignore
    DCASuggestion = None  # type: ignore
    InvestmentAdviceReport = None  # type: ignore
    HoldingAnalyzer = None  # type: ignore
    RebalanceAdvisor = None  # type: ignore
    DCAAdvisor = None  # type: ignore
    RiskAlerter = None  # type: ignore
    InvestmentAdvisor = None  # type: ignore
    generate_investment_advice = None  # type: ignore

try:
    from fund_cli.ai.recommender import (
        RecommendationType,
        FundScore,
        RecommendationItem,
        RecommendationReport,
        ContentBasedRecommender,
        CollaborativeRecommender,
        HybridRecommender,
        FundRecommender,
        recommend_funds,
    )
except ImportError:
    RecommendationType = None  # type: ignore
    FundScore = None  # type: ignore
    RecommendationItem = None  # type: ignore
    RecommendationReport = None  # type: ignore
    ContentBasedRecommender = None  # type: ignore
    CollaborativeRecommender = None  # type: ignore
    HybridRecommender = None  # type: ignore
    FundRecommender = None  # type: ignore
    recommend_funds = None  # type: ignore

try:
    from fund_cli.ai.user_profile import (
        RiskTolerance,
        InvestmentGoal,
        InvestmentHorizon,
        InvestmentStyle,
        RiskAssessment,
        InvestmentPreferences,
        UserProfile,
        RiskQuestionnaire,
        StyleAnalyzer,
        ProfileManager,
        create_user_profile,
    )
except ImportError:
    RiskTolerance = None  # type: ignore
    InvestmentGoal = None  # type: ignore
    InvestmentHorizon = None  # type: ignore
    InvestmentStyle = None  # type: ignore
    RiskAssessment = None  # type: ignore
    InvestmentPreferences = None  # type: ignore
    UserProfile = None  # type: ignore
    RiskQuestionnaire = None  # type: ignore
    StyleAnalyzer = None  # type: ignore
    ProfileManager = None  # type: ignore
    create_user_profile = None  # type: ignore

try:
    from fund_cli.ai.tools import FUND_TOOLS
except ImportError:
    FUND_TOOLS = []  # type: ignore

# 可选导入 - 记忆系统
try:
    from fund_cli.ai.memory import VectorMemory  # noqa: F401

    __all_extra = ["VectorMemory"]
except ImportError:
    __all_extra = []

__all__ = [
    # V3.4 新增 - 智能推荐系统
    "RiskTolerance",
    "InvestmentGoal",
    "InvestmentHorizon",
    "InvestmentStyle",
    "RiskAssessment",
    "InvestmentPreferences",
    "UserProfile",
    "RiskQuestionnaire",
    "StyleAnalyzer",
    "ProfileManager",
    "create_user_profile",
    "RecommendationType",
    "FundScore",
    "RecommendationItem",
    "RecommendationReport",
    "ContentBasedRecommender",
    "CollaborativeRecommender",
    "HybridRecommender",
    "FundRecommender",
    "recommend_funds",
    "AdviceType",
    "Priority",
    "AdviceItem",
    "RebalanceSuggestion",
    "DCASuggestion",
    "InvestmentAdviceReport",
    "HoldingAnalyzer",
    "RebalanceAdvisor",
    "DCAAdvisor",
    "RiskAlerter",
    "InvestmentAdvisor",
    "generate_investment_advice",
    # V3.3 新增 - AI 决策支持
    "FundSelector",
    "FundRecommendation",
    "InvestmentNeed",
    "NeedParser",
    "select_funds",
    "PortfolioDoctor",
    "PortfolioDiagnosis",
    "DiagnosisItem",
    "diagnose_portfolio",
    "MarketAnalyst",
    "MarketSentimentReport",
    "SectorRotationReport",
    "HotspotReport",
    "analyze_market_sentiment",
    "analyze_sector_rotation",
    "track_market_hotspots",
    # V3.0 新增 - Agent 相关
    "FundAgent",
    "get_fund_agent",
    "reset_fund_agent",
    "FundAgentState",
    "FUND_TOOLS",
    # V2.0 保留
    "LLMProvider",
    "OpenAIProvider",
    "QwenProvider",
    "LiteLLMProvider",
    "get_provider",
    "AIAnalyzer",
    "PromptTemplates",
] + __all_extra
