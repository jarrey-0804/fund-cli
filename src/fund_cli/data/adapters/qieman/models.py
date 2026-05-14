"""
Qieman MCP 数据模型

定义与且慢 MCP 服务交互的数据模型。
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# 基础模型
# =============================================================================

class QiemanBaseModel(BaseModel):
    """Qieman 基础模型"""
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


# =============================================================================
# 基金详情模型
# =============================================================================

class FundDetail(QiemanBaseModel):
    """基金详情"""
    
    fund_code: str = Field(..., description="基金代码")
    fund_name: str = Field(..., description="基金名称")
    fund_type: str = Field(..., description="基金类型")
    fund_company: str | None = Field(None, description="基金公司")
    establish_date: date | None = Field(None, description="成立日期")
    manager: str | None = Field(None, description="基金经理")
    scale: float | None = Field(None, description="基金规模（亿元）")
    benchmark: str | None = Field(None, description="业绩比较基准")
    risk_level: int | None = Field(None, description="风险等级")
    min_purchase: float | None = Field(None, description="最低申购金额")
    purchase_status: str | None = Field(None, description="申购状态")
    redeem_status: str | None = Field(None, description="赎回状态")


class FundDetailBatch(QiemanBaseModel):
    """批量基金详情响应"""
    
    funds: list[FundDetail] = Field(default_factory=list, description="基金详情列表")
    total: int = Field(0, description="总数")


# =============================================================================
# 基金净值模型
# =============================================================================

class FundNavRecord(QiemanBaseModel):
    """基金净值记录"""
    
    fund_code: str = Field(..., description="基金代码")
    nav_date: date = Field(..., description="净值日期")
    unit_nav: float = Field(..., description="单位净值")
    accumulated_nav: float | None = Field(None, description="累计净值")
    daily_return: float | None = Field(None, description="日收益率")


class FundNavHistory(QiemanBaseModel):
    """基金历史净值"""
    
    fund_code: str = Field(..., description="基金代码")
    nav_records: list[FundNavRecord] = Field(default_factory=list, description="净值记录")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")


class BatchFundNavHistory(QiemanBaseModel):
    """批量基金历史净值"""
    
    nav_histories: dict[str, FundNavHistory] = Field(
        default_factory=dict, description="基金净值历史映射"
    )


# =============================================================================
# 基金业绩模型
# =============================================================================

class FundPerformance(QiemanBaseModel):
    """基金业绩"""
    
    fund_code: str = Field(..., description="基金代码")
    fund_name: str | None = Field(None, description="基金名称")
    return_1d: float | None = Field(None, description="1日收益率")
    return_1w: float | None = Field(None, description="1周收益率")
    return_1m: float | None = Field(None, description="1月收益率")
    return_3m: float | None = Field(None, description="3月收益率")
    return_6m: float | None = Field(None, description="6月收益率")
    return_1y: float | None = Field(None, description="1年收益率")
    return_2y: float | None = Field(None, description="2年收益率")
    return_3y: float | None = Field(None, description="3年收益率")
    return_ytd: float | None = Field(None, description="年初至今收益率")
    return_inception: float | None = Field(None, description="成立以来收益率")
    annualized_return: float | None = Field(None, description="年化收益率")


class BatchFundPerformance(QiemanBaseModel):
    """批量基金业绩"""
    
    performances: list[FundPerformance] = Field(default_factory=list, description="业绩列表")


# =============================================================================
# 基金持仓模型
# =============================================================================

class HoldingPosition(QiemanBaseModel):
    """持仓明细"""
    
    stock_code: str | None = Field(None, description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    holding_ratio: float = Field(..., description="持仓比例")
    holding_value: float | None = Field(None, description="持仓市值")
    change_ratio: float | None = Field(None, description="变动比例")


class FundHolding(QiemanBaseModel):
    """基金持仓"""
    
    fund_code: str = Field(..., description="基金代码")
    report_date: date | None = Field(None, description="报告日期")
    stock_holdings: list[HoldingPosition] = Field(
        default_factory=list, description="股票持仓"
    )
    bond_holdings: list[HoldingPosition] = Field(
        default_factory=list, description="债券持仓"
    )
    cash_ratio: float | None = Field(None, description="现金比例")
    other_ratio: float | None = Field(None, description="其他资产比例")


class BatchFundHolding(QiemanBaseModel):
    """批量基金持仓"""
    
    holdings: dict[str, FundHolding] = Field(
        default_factory=dict, description="基金持仓映射"
    )


# =============================================================================
# 归因分析模型
# =============================================================================

class BrinsonAttribution(QiemanBaseModel):
    """Brinson归因明细"""
    
    category: str = Field(..., description="行业/类别")
    allocation_effect: float = Field(..., description="配置效应")
    selection_effect: float = Field(..., description="选择效应")
    interaction_effect: float = Field(..., description="交互效应")
    total_effect: float = Field(..., description="总效应")


class BrinsonIndicator(QiemanBaseModel):
    """Brinson归因指标"""
    
    fund_code: str = Field(..., description="基金代码")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    benchmark_code: str | None = Field(None, description="基准代码")
    total_excess_return: float = Field(..., description="总超额收益")
    allocation_return: float = Field(..., description="配置收益")
    selection_return: float = Field(..., description="选择收益")
    interaction_return: float = Field(..., description="交互收益")
    attributions: list[BrinsonAttribution] = Field(
        default_factory=list, description="归因明细"
    )


class CampisiAttribution(QiemanBaseModel):
    """Campisi归因明细"""
    
    factor: str = Field(..., description="因子名称")
    contribution: float = Field(..., description="贡献值")


class CampisiIndicator(QiemanBaseModel):
    """Campisi归因指标"""
    
    fund_code: str = Field(..., description="基金代码")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    total_return: float = Field(..., description="总收益")
    coupon_effect: float | None = Field(None, description="票息效应")
    treasury_effect: float | None = Field(None, description="国债效应")
    spread_effect: float | None = Field(None, description="利差效应")
    selection_effect: float | None = Field(None, description="选择效应")
    attributions: list[CampisiAttribution] = Field(
        default_factory=list, description="归因明细"
    )


# =============================================================================
# 组合诊断模型
# =============================================================================

class PortfolioExposure(QiemanBaseModel):
    """组合暴露"""
    
    factor: str = Field(..., description="因子名称")
    exposure: float = Field(..., description="暴露值")
    benchmark_exposure: float | None = Field(None, description="基准暴露")


class PortfolioDiagnosis(QiemanBaseModel):
    """组合诊断结果"""
    
    portfolio_id: str | None = Field(None, description="组合ID")
    analysis_date: date = Field(..., description="分析日期")
    total_value: float | None = Field(None, description="组合总市值")
    
    # 风险指标
    volatility: float | None = Field(None, description="波动率")
    max_drawdown: float | None = Field(None, description="最大回撤")
    sharpe_ratio: float | None = Field(None, description="夏普比率")
    sortino_ratio: float | None = Field(None, description="索提诺比率")
    
    # 风格暴露
    style_exposures: list[PortfolioExposure] = Field(
        default_factory=list, description="风格暴露"
    )
    
    # 行业配置
    industry_allocation: dict[str, float] = Field(
        default_factory=dict, description="行业配置"
    )
    
    # 资产配置
    asset_allocation: dict[str, float] = Field(
        default_factory=dict, description="资产配置"
    )
    
    # 风险提示
    risk_alerts: list[str] = Field(default_factory=list, description="风险提示")


# =============================================================================
# 回测模型
# =============================================================================

class BacktestMetrics(QiemanBaseModel):
    """回测指标"""
    
    total_return: float = Field(..., description="总收益率")
    annualized_return: float = Field(..., description="年化收益率")
    volatility: float = Field(..., description="波动率")
    max_drawdown: float = Field(..., description="最大回撤")
    sharpe_ratio: float = Field(..., description="夏普比率")
    calmar_ratio: float | None = Field(None, description="卡玛比率")
    win_rate: float | None = Field(None, description="胜率")
    profit_loss_ratio: float | None = Field(None, description="盈亏比")


class BacktestResult(QiemanBaseModel):
    """回测结果"""
    
    portfolio_id: str | None = Field(None, description="组合ID")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    initial_value: float = Field(..., description="初始金额")
    final_value: float = Field(..., description="最终金额")
    
    metrics: BacktestMetrics = Field(..., description="回测指标")
    
    # 净值曲线
    nav_curve: list[dict[str, Any]] = Field(
        default_factory=list, description="净值曲线"
    )
    
    # 回撤曲线
    drawdown_curve: list[dict[str, Any]] = Field(
        default_factory=list, description="回撤曲线"
    )


# =============================================================================
# 相关性模型
# =============================================================================

class CorrelationResult(QiemanBaseModel):
    """相关性分析结果"""
    
    fund_codes: list[str] = Field(..., description="基金代码列表")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    correlation_matrix: dict[str, dict[str, float]] = Field(
        ..., description="相关性矩阵"
    )
    avg_correlation: float | None = Field(None, description="平均相关性")


# =============================================================================
# 风险分析模型
# =============================================================================

class RiskMetrics(QiemanBaseModel):
    """风险指标"""
    
    volatility: float = Field(..., description="波动率")
    downside_volatility: float | None = Field(None, description="下行波动率")
    max_drawdown: float = Field(..., description="最大回撤")
    var_95: float | None = Field(None, description="95% VaR")
    cvar_95: float | None = Field(None, description="95% CVaR")


class RiskAnalysis(QiemanBaseModel):
    """风险分析结果"""
    
    fund_code: str = Field(..., description="基金代码")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    
    risk_metrics: RiskMetrics = Field(..., description="风险指标")
    
    sharpe_ratio: float | None = Field(None, description="夏普比率")
    sortino_ratio: float | None = Field(None, description="索提诺比率")
    information_ratio: float | None = Field(None, description="信息比率")
    treynor_ratio: float | None = Field(None, description="特雷诺比率")
    
    beta: float | None = Field(None, description="Beta")
    alpha: float | None = Field(None, description="Alpha")
    tracking_error: float | None = Field(None, description="跟踪误差")


# =============================================================================
# 行业配置模型
# =============================================================================

class IndustryAllocation(QiemanBaseModel):
    """行业配置"""
    
    industry_name: str = Field(..., description="行业名称")
    allocation_ratio: float = Field(..., description="配置比例")
    benchmark_ratio: float | None = Field(None, description="基准比例")
    over_weight: float | None = Field(None, description="超配比例")


class FundIndustryAllocation(QiemanBaseModel):
    """基金行业配置"""
    
    fund_code: str = Field(..., description="基金代码")
    report_date: date | None = Field(None, description="报告日期")
    allocations: list[IndustryAllocation] = Field(
        default_factory=list, description="行业配置明细"
    )


# =============================================================================
# 债券基金模型
# =============================================================================

class BondAllocation(QiemanBaseModel):
    """债券配置"""
    
    bond_type: str = Field(..., description="债券类型")
    allocation_ratio: float = Field(..., description="配置比例")
    avg_duration: float | None = Field(None, description="平均久期")
    avg_yield: float | None = Field(None, description="平均收益率")


class BondCreditRating(QiemanBaseModel):
    """债券信用评级分布"""
    
    rating_level: str = Field(..., description="评级等级")
    allocation_ratio: float = Field(..., description="配置比例")


class BondFundAnalysis(QiemanBaseModel):
    """债券基金分析"""
    
    fund_code: str = Field(..., description="基金代码")
    report_date: date | None = Field(None, description="报告日期")
    bond_allocations: list[BondAllocation] = Field(
        default_factory=list, description="债券配置"
    )
    credit_ratings: list[BondCreditRating] = Field(
        default_factory=list, description="信用评级分布"
    )
    avg_duration: float | None = Field(None, description="平均久期")
    avg_credit_rating: str | None = Field(None, description="平均信用评级")


# =============================================================================
# QDII基金模型
# =============================================================================

class AreaAllocation(QiemanBaseModel):
    """区域配置"""
    
    area_name: str = Field(..., description="区域名称")
    allocation_ratio: float = Field(..., description="配置比例")


class QDIIFundAnalysis(QiemanBaseModel):
    """QDII基金分析"""
    
    fund_code: str = Field(..., description="基金代码")
    report_date: date | None = Field(None, description="报告日期")
    area_allocations: list[AreaAllocation] = Field(
        default_factory=list, description="区域配置"
    )


# =============================================================================
# 搜索结果模型
# =============================================================================

class FundSearchResult(QiemanBaseModel):
    """基金搜索结果"""
    
    fund_code: str = Field(..., description="基金代码")
    fund_name: str = Field(..., description="基金名称")
    fund_type: str | None = Field(None, description="基金类型")
    fund_company: str | None = Field(None, description="基金公司")
    scale: float | None = Field(None, description="规模")
    return_1y: float | None = Field(None, description="1年收益率")
    establish_date: date | None = Field(None, description="成立日期")


class FundSearchResponse(QiemanBaseModel):
    """基金搜索响应"""
    
    results: list[FundSearchResult] = Field(
        default_factory=list, description="搜索结果"
    )
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页数量")


# =============================================================================
# 策略模型
# =============================================================================

class StrategyDetail(QiemanBaseModel):
    """策略详情"""
    
    strategy_id: str = Field(..., description="策略ID")
    strategy_name: str = Field(..., description="策略名称")
    strategy_type: str | None = Field(None, description="策略类型")
    description: str | None = Field(None, description="策略描述")
    risk_level: int | None = Field(None, description="风险等级")
    expected_return: float | None = Field(None, description="预期收益")
    expected_volatility: float | None = Field(None, description="预期波动率")
    inception_date: date | None = Field(None, description="成立日期")


class StrategyComposition(QiemanBaseModel):
    """策略组合"""
    
    strategy_id: str = Field(..., description="策略ID")
    fund_codes: list[str] = Field(default_factory=list, description="基金代码")
    weights: list[float] = Field(default_factory=list, description="权重")


# =============================================================================
# 资产配置模型
# =============================================================================

class AssetClassAllocation(QiemanBaseModel):
    """资产类别配置"""
    
    asset_class: str = Field(..., description="资产类别")
    target_weight: float = Field(..., description="目标权重")
    current_weight: float | None = Field(None, description="当前权重")
    drift: float | None = Field(None, description="偏离度")


class AssetAllocationPlan(QiemanBaseModel):
    """资产配置方案"""
    
    plan_id: str = Field(..., description="方案ID")
    plan_name: str = Field(..., description="方案名称")
    risk_level: str | None = Field(None, description="风险等级")
    allocations: list[AssetClassAllocation] = Field(
        default_factory=list, description="资产配置"
    )


# =============================================================================
# 市场数据模型
# =============================================================================

class MarketQuotation(QiemanBaseModel):
    """市场行情"""
    
    symbol: str = Field(..., description="证券代码")
    name: str | None = Field(None, description="证券名称")
    price: float | None = Field(None, description="当前价格")
    change: float | None = Field(None, description="涨跌额")
    change_pct: float | None = Field(None, description="涨跌幅")
    volume: float | None = Field(None, description="成交量")
    amount: float | None = Field(None, description="成交额")


class FinancialNews(QiemanBaseModel):
    """财经新闻"""
    
    title: str = Field(..., description="标题")
    content: str | None = Field(None, description="内容")
    source: str | None = Field(None, description="来源")
    publish_time: datetime | None = Field(None, description="发布时间")
    url: str | None = Field(None, description="链接")


# =============================================================================
# 通用响应模型
# =============================================================================

class QiemanResponse(QiemanBaseModel):
    """通用响应"""
    
    success: bool = Field(True, description="是否成功")
    data: Any | None = Field(None, description="响应数据")
    message: str | None = Field(None, description="消息")
    error_code: str | None = Field(None, description="错误码")


class PaginatedResponse(QiemanBaseModel):
    """分页响应"""
    
    items: list[Any] = Field(default_factory=list, description="数据列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页数量")
    total_pages: int = Field(1, description="总页数")
