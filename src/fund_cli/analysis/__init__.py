"""分析模块 - 业绩分析、风险分析、归因分析、组合分析、经理分析、持仓分析

V3.3 新增:
- StressTester: 压力测试
- ScenarioAnalyzer: 情景分析
- RiskBudgetAnalyzer: 风险预算分析
- MoneyFlowAnalyzer: 资金流向分析
- SectorRotationAnalyzer: 行业轮动分析
- MarketSentimentAnalyzer: 市场情绪分析

V3.5 新增:
- PortfolioNavCalculator: 组合净值计算
- FundScoringEngine: 综合评分引擎
- AllocationDeviationAnalyzer: 配置偏离度分析
- AssetLookthroughAnalyzer: 资产穿透分析
- IndustryRiskAnalyzer: 行业风险提示
- StockStyleTagger: 风格标签识别
- IndexFundValuator: 指数基金估值
- FundEvaluator: 双轨评价器
- GroupCorrelationAnalyzer: 分组相关分析
- RebalanceAdvisor: 调仓建议
"""

from fund_cli.analysis.allocation_deviation import (
    AllocationDeviationAnalyzer,
    compute_allocation_deviation,
)
from fund_cli.analysis.asset_lookthrough import AssetLookthroughAnalyzer
from fund_cli.analysis.attribution import AttributionAnalyzer
from fund_cli.analysis.fund_evaluation import FundEvaluator
from fund_cli.analysis.fund_scoring import FundScoringEngine, compute_fund_score
from fund_cli.analysis.group_correlation import GroupCorrelationAnalyzer
from fund_cli.analysis.holding import HoldingAnalyzer
from fund_cli.analysis.index_valuation import IndexFundValuator
from fund_cli.analysis.industry_risk import IndustryRiskAnalyzer
from fund_cli.analysis.manager import ManagerAnalyzer
from fund_cli.analysis.market_sentiment import (
    FearGreedIndex,
    MarketSentimentAnalyzer,
    MarketSentimentReport,
    SentimentLevel,
    analyze_market_sentiment,
)
from fund_cli.analysis.money_flow import (
    FundFlowReport,
    MoneyFlowAnalyzer,
    NorthboundFlowReport,
    SectorFlowReport,
    analyze_money_flow,
)
from fund_cli.analysis.performance import PerformanceAnalyzer
from fund_cli.analysis.portfolio import PortfolioAnalyzer
from fund_cli.analysis.portfolio_nav import PortfolioNavCalculator
from fund_cli.analysis.rebalance_advisor import RebalanceAdvisor
from fund_cli.analysis.risk import RiskAnalyzer
from fund_cli.analysis.risk_budget import (
    RiskBudgetAnalyzer,
    RiskBudgetReport,
    RiskContribution,
    analyze_risk_budget,
    optimize_risk_parity,
)
from fund_cli.analysis.scenario_analysis import (
    InvestmentStyle,
    MarketScenario,
    ScenarioAnalysisReport,
    ScenarioAnalyzer,
    analyze_scenarios,
)
from fund_cli.analysis.sector_rotation import (
    SectorPerformance,
    SectorRotationAnalyzer,
    SectorRotationReport,
    analyze_sector_rotation,
)
from fund_cli.analysis.stress_test import (
    StressScenario,
    StressTester,
    StressTestReport,
    StressTestResult,
    run_stress_test,
)
from fund_cli.analysis.style_tagging import StockStyleTagger

__all__ = [
    # V3.3 新增 - 市场分析能力
    "MoneyFlowAnalyzer",
    "FundFlowReport",
    "SectorFlowReport",
    "NorthboundFlowReport",
    "analyze_money_flow",
    "SectorRotationAnalyzer",
    "SectorRotationReport",
    "SectorPerformance",
    "analyze_sector_rotation",
    "MarketSentimentAnalyzer",
    "MarketSentimentReport",
    "FearGreedIndex",
    "SentimentLevel",
    "analyze_market_sentiment",
    # V3.3 新增 - 风险分析深度增强
    "StressTester",
    "StressTestReport",
    "StressTestResult",
    "StressScenario",
    "run_stress_test",
    "ScenarioAnalyzer",
    "ScenarioAnalysisReport",
    "MarketScenario",
    "InvestmentStyle",
    "analyze_scenarios",
    "RiskBudgetAnalyzer",
    "RiskBudgetReport",
    "RiskContribution",
    "analyze_risk_budget",
    "optimize_risk_parity",
    # 原有模块
    "PerformanceAnalyzer",
    "RiskAnalyzer",
    "AttributionAnalyzer",
    "PortfolioAnalyzer",
    "ManagerAnalyzer",
    "HoldingAnalyzer",
    # V3.5 新增 - 账户诊断系统
    "PortfolioNavCalculator",
    "FundScoringEngine",
    "compute_fund_score",
    "AllocationDeviationAnalyzer",
    "compute_allocation_deviation",
    "AssetLookthroughAnalyzer",
    "IndustryRiskAnalyzer",
    "StockStyleTagger",
    "IndexFundValuator",
    "FundEvaluator",
    "GroupCorrelationAnalyzer",
    "RebalanceAdvisor",
]
