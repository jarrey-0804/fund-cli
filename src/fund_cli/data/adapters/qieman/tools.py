"""
Qieman MCP 工具定义

定义所有73个 MCP 工具的名称、参数和描述。
"""

from typing import Any


class ToolDefinition:
    """工具定义"""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any] | None = None,
        category: str = "general",
        priority: str = "P2",
    ):
        """
        初始化工具定义
        
        Args:
            name: 工具名称
            description: 工具描述
            parameters: 参数定义
            category: 工具分类
            priority: 优先级 (P0/P1/P2)
        """
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        self.category = category
        self.priority = priority
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.parameters,
            },
            "category": self.category,
            "priority": self.priority,
        }


# =============================================================================
# P0 核心接口 (10个)
# =============================================================================

P0_TOOLS = [
    # 基金持仓穿透
    ToolDefinition(
        name="BatchGetFundsHolding",
        description="批量获取基金持仓数据，支持QDII基金持仓穿透分析",
        parameters={
            "fundCodes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "基金代码列表",
            },
            "reportDate": {
                "type": "string",
                "description": "报告日期 (YYYY-MM-DD)",
            },
        },
        category="fund_analysis",
        priority="P0",
    ),
    # Brinson归因分析
    ToolDefinition(
        name="getFundBrinsonIndicator",
        description="获取基金Brinson归因分析指标，分析超额收益来源",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
            "benchmarkCode": {
                "type": "string",
                "description": "基准代码",
            },
        },
        category="fund_indicator",
        priority="P0",
    ),
    # 组合诊断
    ToolDefinition(
        name="DiagnoseFundPortfolio",
        description="诊断基金组合，提供持仓分析、风险暴露、风格分析等",
        parameters={
            "fundCodes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "基金代码列表",
            },
            "weights": {
                "type": "array",
                "items": {"type": "number"},
                "description": "基金权重列表",
            },
            "analysisDate": {
                "type": "string",
                "description": "分析日期",
            },
        },
        category="fund_analysis",
        priority="P0",
    ),
    # 组合回测
    ToolDefinition(
        name="GetFundsBackTest",
        description="基金组合回测分析，计算历史收益、风险指标等",
        parameters={
            "fundCodes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "基金代码列表",
            },
            "weights": {
                "type": "array",
                "items": {"type": "number"},
                "description": "基金权重列表",
            },
            "startDate": {
                "type": "string",
                "description": "回测开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "回测结束日期",
            },
            "rebalanceFrequency": {
                "type": "string",
                "description": "再平衡频率",
            },
        },
        category="fund_analysis",
        priority="P0",
    ),
    # 历史净值
    ToolDefinition(
        name="BatchGetFundNavHistory",
        description="批量获取基金历史净值数据",
        parameters={
            "fundCodes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "基金代码列表",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="fund_analysis",
        priority="P0",
    ),
    # 业绩表现
    ToolDefinition(
        name="GetBatchFundPerformance",
        description="批量获取基金业绩表现数据，包含各阶段收益率",
        parameters={
            "fundCodes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "基金代码列表",
            },
            "indicators": {
                "type": "array",
                "items": {"type": "string"},
                "description": "业绩指标列表",
            },
        },
        category="fund_analysis",
        priority="P0",
    ),
    # 基金详情
    ToolDefinition(
        name="BatchGetFundsDetail",
        description="批量获取基金详细信息",
        parameters={
            "fundCodes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "基金代码列表",
            },
        },
        category="fund_analysis",
        priority="P0",
    ),
    # 基金搜索
    ToolDefinition(
        name="SearchFunds",
        description="搜索基金，支持关键词、类型、公司等筛选条件",
        parameters={
            "keyword": {
                "type": "string",
                "description": "搜索关键词",
            },
            "fundType": {
                "type": "string",
                "description": "基金类型",
            },
            "company": {
                "type": "string",
                "description": "基金公司",
            },
            "minScale": {
                "type": "number",
                "description": "最小规模（亿元）",
            },
            "maxScale": {
                "type": "number",
                "description": "最大规模（亿元）",
            },
            "limit": {
                "type": "integer",
                "description": "返回数量限制",
            },
        },
        category="fund_analysis",
        priority="P0",
    ),
    # 相关性分析
    ToolDefinition(
        name="GetFundsCorrelation",
        description="获取基金相关性分析矩阵",
        parameters={
            "fundCodes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "基金代码列表",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="fund_analysis",
        priority="P0",
    ),
    # 风险分析
    ToolDefinition(
        name="AnalyzeFundRisk",
        description="分析基金风险指标，包括波动率、最大回撤、夏普比率等",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="fund_analysis",
        priority="P0",
    ),
]


# =============================================================================
# P1 扩展接口 (20个)
# =============================================================================

P1_TOOLS = [
    # ----- 基金指标接口 (5个) -----
    ToolDefinition(
        name="getFundCampisiIndicator",
        description="获取基金Campisi归因分析指标，用于债券基金收益归因",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="fund_indicator",
        priority="P1",
    ),
    ToolDefinition(
        name="getBondIndicator",
        description="获取债券基金指标数据",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
        },
        category="fund_indicator",
        priority="P1",
    ),
    ToolDefinition(
        name="getMarketTimingIndicator",
        description="获取基金择时能力指标",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="fund_indicator",
        priority="P1",
    ),
    ToolDefinition(
        name="getFundTurnoverRate",
        description="获取基金换手率数据",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "year": {
                "type": "integer",
                "description": "年份",
            },
        },
        category="fund_indicator",
        priority="P1",
    ),
    ToolDefinition(
        name="AnalyzeFinancialIndicators",
        description="分析基金财务指标",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "indicators": {
                "type": "array",
                "items": {"type": "string"},
                "description": "指标列表",
            },
        },
        category="fund_indicator",
        priority="P1",
    ),
    
    # ----- 行业分析接口 (5个) -----
    ToolDefinition(
        name="getFundIndustryPreference",
        description="获取基金行业偏好分析",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "reportDate": {
                "type": "string",
                "description": "报告日期",
            },
        },
        category="fund_analysis",
        priority="P1",
    ),
    ToolDefinition(
        name="getFundIndustryReturns",
        description="获取基金行业收益贡献分析",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="fund_analysis",
        priority="P1",
    ),
    ToolDefinition(
        name="getFundIndustryAllocation",
        description="获取基金行业配置数据",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "reportDate": {
                "type": "string",
                "description": "报告日期",
            },
        },
        category="fund_analysis",
        priority="P1",
    ),
    ToolDefinition(
        name="getFundIndustryConcentration",
        description="获取基金行业集中度分析",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "topN": {
                "type": "integer",
                "description": "前N大行业",
            },
        },
        category="fund_analysis",
        priority="P1",
    ),
    ToolDefinition(
        name="getStockAllocationAndMetricsByFundCode",
        description="获取基金股票配置及相关指标",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "reportDate": {
                "type": "string",
                "description": "报告日期",
            },
        },
        category="fund_analysis",
        priority="P1",
    ),
    
    # ----- 债券基金接口 (3个) -----
    ToolDefinition(
        name="getBondAllocationByFundCode",
        description="获取基金债券配置数据",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "reportDate": {
                "type": "string",
                "description": "报告日期",
            },
        },
        category="bond_fund",
        priority="P1",
    ),
    ToolDefinition(
        name="getBondFundCreditRatingLevel",
        description="获取债券基金信用评级分布",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
        },
        category="bond_fund",
        priority="P1",
    ),
    ToolDefinition(
        name="getBondFundWithAlertRecord",
        description="获取有预警记录的债券基金列表",
        parameters={
            "alertType": {
                "type": "string",
                "description": "预警类型",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="bond_fund",
        priority="P1",
    ),
    
    # ----- 基金筛选接口 (3个) -----
    ToolDefinition(
        name="filterStockFundByStockTurnover",
        description="按股票换手率筛选股票型基金",
        parameters={
            "minTurnover": {
                "type": "number",
                "description": "最小换手率",
            },
            "maxTurnover": {
                "type": "number",
                "description": "最大换手率",
            },
            "year": {
                "type": "integer",
                "description": "年份",
            },
        },
        category="fund_filter",
        priority="P1",
    ),
    ToolDefinition(
        name="filterBondFundByBondType",
        description="按债券类型筛选债券型基金",
        parameters={
            "bondType": {
                "type": "string",
                "description": "债券类型",
            },
            "minRatio": {
                "type": "number",
                "description": "最小占比",
            },
        },
        category="fund_filter",
        priority="P1",
    ),
    ToolDefinition(
        name="filterBondFundByCreditRating",
        description="按信用评级筛选债券型基金",
        parameters={
            "ratingLevel": {
                "type": "string",
                "description": "评级等级",
            },
            "minRatio": {
                "type": "number",
                "description": "最小占比",
            },
        },
        category="fund_filter",
        priority="P1",
    ),
    
    # ----- 其他基金分析接口 (4个) -----
    ToolDefinition(
        name="getQdFundAreaAllocation",
        description="获取QDII基金区域配置数据",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "reportDate": {
                "type": "string",
                "description": "报告日期",
            },
        },
        category="fund_analysis",
        priority="P1",
    ),
    ToolDefinition(
        name="getFundBenchmarkInfo",
        description="获取基金基准信息",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
        },
        category="fund_analysis",
        priority="P1",
    ),
    ToolDefinition(
        name="GetFundDiagnosis",
        description="获取基金诊断报告",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "analysisType": {
                "type": "string",
                "description": "分析类型",
            },
        },
        category="fund_analysis",
        priority="P1",
    ),
    ToolDefinition(
        name="GetPopularFund",
        description="获取热门基金列表",
        parameters={
            "fundType": {
                "type": "string",
                "description": "基金类型",
            },
            "period": {
                "type": "string",
                "description": "统计周期",
            },
            "limit": {
                "type": "integer",
                "description": "返回数量",
            },
        },
        category="fund_analysis",
        priority="P1",
    ),
]


# =============================================================================
# P2 扩展接口 (43个)
# =============================================================================

P2_TOOLS = [
    # ----- 资产配置接口 (6个) -----
    ToolDefinition(
        name="GetAssetAllocation",
        description="获取资产配置建议",
        parameters={
            "riskLevel": {
                "type": "string",
                "description": "风险等级",
            },
            "investmentPeriod": {
                "type": "string",
                "description": "投资期限",
            },
        },
        category="asset_allocation",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundAssetClassAnalysis",
        description="获取基金资产类别分析",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
        },
        category="asset_allocation",
        priority="P2",
    ),
    ToolDefinition(
        name="MonteCarloSimulate",
        description="蒙特卡洛模拟分析",
        parameters={
            "fundCodes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "基金代码列表",
            },
            "weights": {
                "type": "array",
                "items": {"type": "number"},
                "description": "权重列表",
            },
            "simulationCount": {
                "type": "integer",
                "description": "模拟次数",
            },
            "years": {
                "type": "integer",
                "description": "模拟年数",
            },
        },
        category="asset_allocation",
        priority="P2",
    ),
    ToolDefinition(
        name="GetAssetAllocationPlan",
        description="获取资产配置方案",
        parameters={
            "planId": {
                "type": "string",
                "description": "方案ID",
            },
        },
        category="asset_allocation",
        priority="P2",
    ),
    ToolDefinition(
        name="GetCompositeModel",
        description="获取组合模型详情",
        parameters={
            "modelId": {
                "type": "string",
                "description": "模型ID",
            },
        },
        category="asset_allocation",
        priority="P2",
    ),
    ToolDefinition(
        name="AnalyzePortfolioRisk",
        description="分析组合风险",
        parameters={
            "fundCodes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "基金代码列表",
            },
            "weights": {
                "type": "array",
                "items": {"type": "number"},
                "description": "权重列表",
            },
        },
        category="asset_allocation",
        priority="P2",
    ),
    
    # ----- 行情资讯接口 (7个) -----
    ToolDefinition(
        name="GetLatestQuotations",
        description="获取最新行情数据",
        parameters={
            "symbols": {
                "type": "array",
                "items": {"type": "string"},
                "description": "证券代码列表",
            },
        },
        category="market_data",
        priority="P2",
    ),
    ToolDefinition(
        name="SearchHotTopic",
        description="搜索热门话题",
        parameters={
            "keyword": {
                "type": "string",
                "description": "搜索关键词",
            },
            "limit": {
                "type": "integer",
                "description": "返回数量",
            },
        },
        category="market_data",
        priority="P2",
    ),
    ToolDefinition(
        name="SearchFinancialNews",
        description="搜索财经新闻",
        parameters={
            "keyword": {
                "type": "string",
                "description": "搜索关键词",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
            "limit": {
                "type": "integer",
                "description": "返回数量",
            },
        },
        category="market_data",
        priority="P2",
    ),
    ToolDefinition(
        name="searchRealtimeAiAnalysis",
        description="搜索实时AI分析",
        parameters={
            "topic": {
                "type": "string",
                "description": "分析主题",
            },
        },
        category="market_data",
        priority="P2",
    ),
    ToolDefinition(
        name="SearchManagerViewpoint",
        description="搜索基金经理观点",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "managerName": {
                "type": "string",
                "description": "基金经理姓名",
            },
        },
        category="market_data",
        priority="P2",
    ),
    ToolDefinition(
        name="searchInvestAdvisorContent",
        description="搜索投顾内容",
        parameters={
            "keyword": {
                "type": "string",
                "description": "搜索关键词",
            },
            "contentType": {
                "type": "string",
                "description": "内容类型",
            },
        },
        category="market_data",
        priority="P2",
    ),
    ToolDefinition(
        name="GetCurrentTime",
        description="获取当前服务器时间",
        parameters={},
        category="market_data",
        priority="P2",
    ),
    
    # ----- 策略接口 (7个) -----
    ToolDefinition(
        name="GetStrategyDetails",
        description="获取策略详情",
        parameters={
            "strategyId": {
                "type": "string",
                "description": "策略ID",
            },
        },
        category="strategy",
        priority="P2",
    ),
    ToolDefinition(
        name="BatchGetStrategiesComposition",
        description="批量获取策略组合",
        parameters={
            "strategyIds": {
                "type": "array",
                "items": {"type": "string"},
                "description": "策略ID列表",
            },
        },
        category="strategy",
        priority="P2",
    ),
    ToolDefinition(
        name="GetStrategyAssetClassAnalysis",
        description="获取策略资产类别分析",
        parameters={
            "strategyId": {
                "type": "string",
                "description": "策略ID",
            },
        },
        category="strategy",
        priority="P2",
    ),
    ToolDefinition(
        name="GetStrategyBenchmark",
        description="获取策略基准",
        parameters={
            "strategyId": {
                "type": "string",
                "description": "策略ID",
            },
        },
        category="strategy",
        priority="P2",
    ),
    ToolDefinition(
        name="GetStrategyRiskInfo",
        description="获取策略风险信息",
        parameters={
            "strategyId": {
                "type": "string",
                "description": "策略ID",
            },
        },
        category="strategy",
        priority="P2",
    ),
    ToolDefinition(
        name="BatchGetPoTradeComposition",
        description="批量获取PO交易组合",
        parameters={
            "poIds": {
                "type": "array",
                "items": {"type": "string"},
                "description": "PO ID列表",
            },
        },
        category="strategy",
        priority="P2",
    ),
    ToolDefinition(
        name="StrategySearchByKeyword",
        description="按关键词搜索策略",
        parameters={
            "keyword": {
                "type": "string",
                "description": "搜索关键词",
            },
            "limit": {
                "type": "integer",
                "description": "返回数量",
            },
        },
        category="strategy",
        priority="P2",
    ),
    
    # ----- 其他接口 (23个) -----
    ToolDefinition(
        name="GetFundAnnouncement",
        description="获取基金公告",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "announcementType": {
                "type": "string",
                "description": "公告类型",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundDividend",
        description="获取基金分红信息",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "year": {
                "type": "integer",
                "description": "年份",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundSplit",
        description="获取基金拆分信息",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundTradeRules",
        description="获取基金交易规则",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundFeeInfo",
        description="获取基金费率信息",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundManagerInfo",
        description="获取基金经理信息",
        parameters={
            "managerId": {
                "type": "string",
                "description": "基金经理ID",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundManagerPerformance",
        description="获取基金经理业绩",
        parameters={
            "managerId": {
                "type": "string",
                "description": "基金经理ID",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundCompanyInfo",
        description="获取基金公司信息",
        parameters={
            "companyId": {
                "type": "string",
                "description": "基金公司ID",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundCompanyProducts",
        description="获取基金公司产品列表",
        parameters={
            "companyId": {
                "type": "string",
                "description": "基金公司ID",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundRating",
        description="获取基金评级",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "ratingAgency": {
                "type": "string",
                "description": "评级机构",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundScaleHistory",
        description="获取基金规模历史",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundHolderStructure",
        description="获取基金持有人结构",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "reportDate": {
                "type": "string",
                "description": "报告日期",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundStyleAnalysis",
        description="获取基金风格分析",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundFactorExposure",
        description="获取基金因子暴露",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetFundPerformanceAttribution",
        description="获取基金业绩归因",
        parameters={
            "fundCode": {
                "type": "string",
                "description": "基金代码",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetIndexConstituents",
        description="获取指数成分股",
        parameters={
            "indexCode": {
                "type": "string",
                "description": "指数代码",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetIndexWeights",
        description="获取指数权重",
        parameters={
            "indexCode": {
                "type": "string",
                "description": "指数代码",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetMarketIndexData",
        description="获取市场指数数据",
        parameters={
            "indexCode": {
                "type": "string",
                "description": "指数代码",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetBondYieldCurve",
        description="获取债券收益率曲线",
        parameters={
            "bondType": {
                "type": "string",
                "description": "债券类型",
            },
            "date": {
                "type": "string",
                "description": "日期",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetCreditSpread",
        description="获取信用利差数据",
        parameters={
            "ratingLevel": {
                "type": "string",
                "description": "评级等级",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetMacroEconomicData",
        description="获取宏观经济数据",
        parameters={
            "indicator": {
                "type": "string",
                "description": "经济指标",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="RenderPdfReport",
        description="渲染PDF报告",
        parameters={
            "templateId": {
                "type": "string",
                "description": "模板ID",
            },
            "data": {
                "type": "object",
                "description": "报告数据",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetUserPortfolio",
        description="获取用户组合",
        parameters={
            "portfolioId": {
                "type": "string",
                "description": "组合ID",
            },
        },
        category="other",
        priority="P2",
    ),
    ToolDefinition(
        name="GetUserTransactions",
        description="获取用户交易记录",
        parameters={
            "portfolioId": {
                "type": "string",
                "description": "组合ID",
            },
            "startDate": {
                "type": "string",
                "description": "开始日期",
            },
            "endDate": {
                "type": "string",
                "description": "结束日期",
            },
        },
        category="other",
        priority="P2",
    ),
]


# 合并所有工具
QIEMAN_TOOLS = P0_TOOLS + P1_TOOLS + P2_TOOLS

# 创建工具名称到定义的映射
TOOL_NAME_MAP = {tool.name: tool for tool in QIEMAN_TOOLS}


def get_tool_definition(tool_name: str) -> ToolDefinition | None:
    """
    获取工具定义
    
    Args:
        tool_name: 工具名称
        
    Returns:
        工具定义，不存在则返回 None
    """
    return TOOL_NAME_MAP.get(tool_name)


def get_tools_by_category(category: str) -> list[ToolDefinition]:
    """
    按分类获取工具列表
    
    Args:
        category: 分类名称
        
    Returns:
        该分类下的工具列表
    """
    return [tool for tool in QIEMAN_TOOLS if tool.category == category]


def get_tools_by_priority(priority: str) -> list[ToolDefinition]:
    """
    按优先级获取工具列表
    
    Args:
        priority: 优先级 (P0/P1/P2)
        
    Returns:
        该优先级下的工具列表
    """
    return [tool for tool in QIEMAN_TOOLS if tool.priority == priority]


def list_all_tools() -> list[str]:
    """
    列出所有工具名称
    
    Returns:
        工具名称列表
    """
    return [tool.name for tool in QIEMAN_TOOLS]


# 工具统计
TOOL_STATS = {
    "total": len(QIEMAN_TOOLS),
    "P0": len(P0_TOOLS),
    "P1": len(P1_TOOLS),
    "P2": len(P2_TOOLS),
    "by_category": {},
}

for tool in QIEMAN_TOOLS:
    cat = tool.category
    TOOL_STATS["by_category"][cat] = TOOL_STATS["by_category"].get(cat, 0) + 1
