"""
AI 提示词模板（V2.0 实现）

管理用于基金分析的提示词模板。
"""

from typing import Any


class PromptTemplates:
    """提示词模板管理"""

    FUND_SUMMARY = """
你是一位专业的基金分析师。请根据以下基金数据生成一份简洁的分析摘要。

基金信息：
- 代码：{fund_code}
- 名称：{fund_name}
- 类型：{fund_type}
- 基金经理：{manager}

业绩指标：
- 总收益率：{total_return}%
- 年化收益率：{cagr}%
- 夏普比率：{sharpe}
- 最大回撤：{max_drawdown}%
- 年化波动率：{volatility}%

请从以下维度分析：
1. 收益能力
2. 风险控制
3. 综合评价
"""

    FUND_COMPARE = """
你是一位专业的基金分析师。请对比分析以下基金。

{funds_data}

请从以下维度对比分析：
1. 收益对比
2. 风险对比
3. 风险调整收益对比
4. 综合推荐
"""

    RISK_ANALYSIS = """
你是一位专业的风险管理分析师。请分析以下基金的风险状况。

基金：{fund_name}（{fund_code}）

风险指标：
- 年化波动率：{volatility}%
- 最大回撤：{max_drawdown}%
- VaR(95%)：{var_95}%
- VaR(99%)：{var_99}%
- 偏度：{skewness}
- 峰度：{kurtosis}

请分析：
1. 整体风险水平
2. 尾部风险特征
3. 风险管理建议
"""

    INVESTMENT_ADVICE = """
你是一位专业的投资顾问。请基于以下基金数据给出投资建议。

基金：{fund_name}（{fund_code}）
类型：{fund_type}

业绩指标：
- 年化收益：{cagr}%
- 夏普比率：{sharpe}
- 最大回撤：{max_drawdown}%

投资者风险偏好：{risk_profile}

请给出：
1. 是否适合该投资者（是/否/谨慎考虑）
2. 建议配置比例（如适用）
3. 关键风险提示
4. 持有期建议

请以JSON格式输出结果，格式如下：
{{
    "suitability": "是/否/谨慎考虑",
    "allocation": "建议配置比例",
    "risk_warning": "关键风险提示",
    "holding_period": "持有期建议"
}}
"""

    MARKET_INSIGHT = """
你是一位市场分析师。请结合当前市场环境分析该基金表现。

基金：{fund_name}（{fund_code}）
近期收益：{recent_return}%
同类排名：{rank_in_category}

市场环境：{market_context}

请分析：
1. 基金表现与市场关系
2. 基金经理应对能力
3. 未来展望
"""

    PORTFOLIO_REVIEW = """
你是一位投资组合顾问。请对以下组合进行整体评估。

组合配置：
{portfolio_config}

组合指标：
- 预期收益：{expected_return}%
- 预期波动：{expected_volatility}%
- 夏普比率：{portfolio_sharpe}

请给出：
1. 组合整体评价
2. 配置优化建议
3. 风险分散度评估

请以JSON格式输出结果，格式如下：
{{
    "overall_assessment": "组合整体评价",
    "optimization_suggestions": "配置优化建议",
    "diversification": "风险分散度评估"
}}
"""

    RISK_ASSESSMENT = """
你是一位风险管理专家。请对以下基金进行深度风险评估。

基金：{fund_name}（{fund_code}）

风险指标：
- 最大回撤：{max_drawdown}%
- 波动率：{volatility}%
- 下行标准差：{downside_deviation}%
- 索提诺比率：{sortino_ratio}
- Beta系数：{beta}

历史风险事件：
{risk_events}

请给出：
1. 风险等级（低/中/高/极高）
2. 主要风险因素分析
3. 风险预警（如有）
4. 风险控制建议
{detail_section}

请以JSON格式输出结果，格式如下：
{{
    "risk_level": "风险等级",
    "main_risks": "主要风险因素",
    "warnings": "风险预警",
    "control_suggestions": "风险控制建议"
}}
"""

    @staticmethod
    def format_summary_prompt(data: dict[str, Any]) -> str:
        """格式化基金摘要提示词"""
        return PromptTemplates.FUND_SUMMARY.format(**data)

    @staticmethod
    def format_compare_prompt(funds_data: str) -> str:
        """格式化基金对比提示词"""
        return PromptTemplates.FUND_COMPARE.format(funds_data=funds_data)

    @staticmethod
    def format_risk_prompt(data: dict[str, Any]) -> str:
        """格式化风险分析提示词"""
        return PromptTemplates.RISK_ANALYSIS.format(**data)

    @staticmethod
    def format_investment_advice_prompt(fund_data: dict[str, Any], risk_profile: str) -> str:
        """格式化投资建议提示词"""
        return PromptTemplates.INVESTMENT_ADVICE.format(
            fund_name=fund_data.get("name", ""),
            fund_code=fund_data.get("code", ""),
            fund_type=fund_data.get("type", ""),
            cagr=fund_data.get("cagr", 0),
            sharpe=fund_data.get("sharpe", 0),
            max_drawdown=fund_data.get("max_drawdown", 0),
            risk_profile=risk_profile,
        )

    @staticmethod
    def format_market_insight_prompt(
        fund_data: dict[str, Any], market_context: str | None = None
    ) -> str:
        """格式化市场解读提示词"""
        return PromptTemplates.MARKET_INSIGHT.format(
            fund_name=fund_data.get("name", ""),
            fund_code=fund_data.get("code", ""),
            recent_return=fund_data.get("recent_return", 0),
            rank_in_category=fund_data.get("rank_in_category", "未知"),
            market_context=market_context or "当前市场环境正常",
        )

    @staticmethod
    def format_portfolio_review_prompt(portfolio_data: dict[str, Any]) -> str:
        """格式化组合分析提示词"""
        funds = portfolio_data.get("funds", [])
        weights = portfolio_data.get("weights", [])

        portfolio_config = ""
        for i, fund in enumerate(funds):
            weight = weights[i] if i < len(weights) else 0
            portfolio_config += f"- {fund.get('code', '')}: {weight * 100:.1f}%\n"

        return PromptTemplates.PORTFOLIO_REVIEW.format(
            portfolio_config=portfolio_config,
            expected_return=portfolio_data.get("expected_return", 0),
            expected_volatility=portfolio_data.get("expected_volatility", 0),
            portfolio_sharpe=portfolio_data.get("portfolio_sharpe", 0),
        )

    @staticmethod
    def format_risk_assessment_prompt(fund_data: dict[str, Any], detailed: bool = False) -> str:
        """格式化风险评估提示词"""
        detail_section = ""
        if detailed:
            detail_section = """
5. 详细风险分析报告
6. 历史风险事件回顾
7. 压力测试结果
"""

        return PromptTemplates.RISK_ASSESSMENT.format(
            fund_name=fund_data.get("name", ""),
            fund_code=fund_data.get("code", ""),
            max_drawdown=fund_data.get("max_drawdown", 0),
            volatility=fund_data.get("volatility", 0),
            downside_deviation=fund_data.get("downside_deviation", 0),
            sortino_ratio=fund_data.get("sortino_ratio", 0),
            beta=fund_data.get("beta", 0),
            risk_events=fund_data.get("risk_events", "无重大风险事件"),
            detail_section=detail_section,
        )
