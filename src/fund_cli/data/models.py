"""
数据模型定义

使用 Pydantic 定义基金相关的数据模型。
"""

from datetime import date, datetime
from enum import Enum as PyEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FundType(str, PyEnum):
    """基金类型枚举"""

    EQUITY = "股票型"
    BOND = "债券型"
    MIXED = "混合型"
    INDEX = "指数型"
    QDII = "QDII"
    MONEY = "货币型"
    ETF = "ETF"
    LOF = "LOF"
    OTHER = "其他"


class FundInfo(BaseModel):
    """
    基金基础信息模型

    包含基金的基本属性信息。
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    # 基本信息
    code: str = Field(..., min_length=6, max_length=6, description="基金代码")
    name: str = Field(..., min_length=1, description="基金名称")
    type: FundType = Field(..., description="基金类型")

    # 详细信息
    establish_date: date | None = Field(None, description="成立日期")
    manager: str | None = Field(None, description="基金经理")
    company: str | None = Field(None, description="基金公司")
    scale: float | None = Field(None, ge=0, description="规模（亿元）")

    # 业绩信息
    return_1m: float | None = Field(None, description="近1月收益率(%)")
    return_3m: float | None = Field(None, description="近3月收益率(%)")
    return_6m: float | None = Field(None, description="近6月收益率(%)")
    return_1y: float | None = Field(None, description="近1年收益率(%)")
    return_3y: float | None = Field(None, description="近3年收益率(%)")
    return_this_year: float | None = Field(None, description="今年以来收益率(%)")

    # 风险指标
    max_drawdown: float | None = Field(None, description="最大回撤(%)")
    sharpe_ratio: float | None = Field(None, description="夏普比率")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """验证基金代码格式"""
        if not v.isdigit():
            raise ValueError("基金代码必须为6位数字")
        return v

    def __repr__(self) -> str:
        return f"FundInfo(code={self.code!r}, name={self.name!r}, type={self.type.value!r})"


class NavData(BaseModel):
    """
    单条净值数据模型
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    fund_code: str = Field(..., description="基金代码")
    nav_date: date = Field(..., description="净值日期")
    unit_nav: float = Field(..., gt=0, description="单位净值")
    accumulated_nav: float | None = Field(None, gt=0, description="累计净值")
    daily_return: float | None = Field(None, description="日收益率(%)")

    @field_validator("fund_code")
    @classmethod
    def validate_fund_code(cls, v: str) -> str:
        """验证基金代码格式"""
        if not v.isdigit() or len(v) != 6:
            raise ValueError("基金代码必须为6位数字")
        return v


class FundFilter(BaseModel):
    """
    基金筛选条件模型
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    # 基础筛选
    fund_type: FundType | None = Field(None, description="基金类型")
    company: str | None = Field(None, description="基金公司")
    manager: str | None = Field(None, description="基金经理")

    # 规模筛选
    min_scale: float | None = Field(None, ge=0, description="最小规模（亿元）")
    max_scale: float | None = Field(None, ge=0, description="最大规模（亿元）")

    # 业绩筛选
    min_return_1y: float | None = Field(None, description="近1年收益率下限(%)")
    max_return_1y: float | None = Field(None, description="近1年收益率上限(%)")

    # 风险筛选
    max_drawdown: float | None = Field(None, description="最大回撤上限(%)")
    min_sharpe: float | None = Field(None, description="夏普比率下限")

    # V1.0 新增筛选
    fee_rate_max: float | None = Field(None, ge=0, description="管理费率上限(%)")
    manager_name: str | None = Field(None, description="基金经理名称")
    min_rating: int | None = Field(None, ge=1, le=5, description="最低评级(星)")

    # 关键词搜索
    keyword: str | None = Field(None, description="关键词")

    # 排序
    sort_by: str | None = Field(None, description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向: asc/desc")

    # 分页
    limit: int = Field(default=100, ge=1, le=1000, description="返回数量限制")
    offset: int = Field(default=0, ge=0, description="偏移量")


class AnalysisResult(BaseModel):
    """
    分析结果模型
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    fund_code: str = Field(..., description="基金代码")
    fund_name: str = Field(..., description="基金名称")
    analysis_date: date = Field(default_factory=date.today, description="分析日期")
    start_date: date = Field(..., description="分析开始日期")
    end_date: date = Field(..., description="分析结束日期")

    # 收益指标
    total_return: float = Field(..., description="总收益率(%)")
    annualized_return: float = Field(..., description="年化收益率(%)")

    # 风险指标
    volatility: float = Field(..., description="年化波动率(%)")
    max_drawdown: float = Field(..., description="最大回撤(%)")
    var_95: float | None = Field(None, description="VaR(95%)")

    # 风险调整收益
    sharpe_ratio: float = Field(..., description="夏普比率")
    sortino_ratio: float | None = Field(None, description="索提诺比率")
    calmar_ratio: float | None = Field(None, description="卡玛比率")

    # 相对指标
    alpha: float | None = Field(None, description="Alpha")
    beta: float | None = Field(None, description="Beta")
    information_ratio: float | None = Field(None, description="信息比率")
    tracking_error: float | None = Field(None, description="跟踪误差(%)")

    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump()


class HoldingInfo(BaseModel):
    """持仓信息模型"""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    fund_code: str = Field(..., description="基金代码")
    report_date: date = Field(..., description="报告日期")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    weight: float = Field(..., ge=0, le=100, description="占净值比例(%)")
    market_value: float | None = Field(None, ge=0, description="持仓市值(万元)")
    industry: str | None = Field(None, description="所属行业")


class FundManager(BaseModel):
    """基金经理模型"""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    name: str = Field(..., min_length=1, description="经理姓名")
    fund_code: str = Field(..., description="基金代码")
    fund_name: str | None = Field(None, description="基金名称")
    start_date: date | None = Field(None, description="任职起始日")
    tenure_days: int | None = Field(None, ge=0, description="任职天数")
    total_return: float | None = Field(None, description="任期总收益率(%)")
    annual_return: float | None = Field(None, description="年化收益率(%)")


class HoldingSnapshot(BaseModel):
    """持仓快照模型"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    fund_code: str = Field(..., description="基金代码")
    report_date: date = Field(..., description="报告日期")
    total_stock_count: int = Field(..., ge=0, description="持股数量")
    top10_weight: float = Field(..., ge=0, le=100, description="前十大重仓股占比(%)")
    industry_distribution: dict[str, float] = Field(default_factory=dict, description="行业分布")


class OptimizationConstraint(BaseModel):
    """优化约束条件模型"""

    min_weight: float = Field(default=0.0, ge=0, le=1, description="最小权重")
    max_weight: float = Field(default=1.0, ge=0, le=1, description="最大权重")
    target_return: float | None = Field(None, description="目标收益率")
    max_volatility: float | None = Field(None, ge=0, description="最大波动率")
    max_drawdown: float | None = Field(None, le=0, description="最大回撤")


class MonitorRule(BaseModel):
    """监控规则模型"""

    fund_code: str = Field(..., description="基金代码")
    rule_type: str = Field(
        default="nav_change", description="规则类型: nav_change/threshold/drawdown"
    )
    threshold: float = Field(default=-2.0, description="阈值")
    enabled: bool = Field(default=True, description="是否启用")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class OutputConfig(BaseModel):
    """输出格式配置模型"""

    default_format: str = Field(default="table", description="默认输出格式: table/csv/json")
    csv_encoding: str = Field(default="utf-8-sig", description="CSV编码")
    csv_delimiter: str = Field(default=",", description="CSV分隔符")
    json_indent: int = Field(default=2, ge=0, description="JSON缩进")
    number_decimal: int = Field(default=2, ge=0, le=6, description="数字小数位")
    date_format: str = Field(default="%Y-%m-%d", description="日期格式")
