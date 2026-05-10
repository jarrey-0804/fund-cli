"""
AI 分析服务（V2.0 实现）

使用 LLM 进行基金分析、报告生成等功能。
"""

from __future__ import annotations

import json
import re
from typing import Any

from fund_cli.ai.prompts import PromptTemplates
from fund_cli.ai.providers import LLMProvider, get_provider


class AIAnalyzer:
    """
    AI 分析服务

    使用 LLM 进行基金分析、报告生成等功能。
    """

    def __init__(self, provider: LLMProvider | None = None):
        """
        初始化 AI 分析服务

        Args:
            provider: LLM 提供商实例，如果为None则使用默认配置创建
        """
        self.provider = provider or get_provider()
        self.prompts = PromptTemplates()

    def summarize_fund(self, fund_code: str, fund_data: dict[str, Any]) -> str:
        """
        生成基金分析摘要

        Args:
            fund_code: 基金代码
            fund_data: 基金数据字典，包含info、nav、metrics等

        Returns:
            AI生成的基金摘要文本
        """
        info = fund_data.get("info", {})
        metrics = fund_data.get("metrics", {})

        prompt_data = {
            "fund_code": fund_code,
            "fund_name": info.get("name", "未知"),
            "fund_type": info.get("type", "未知"),
            "manager": info.get("manager", "未知"),
            "total_return": metrics.get("total_return", 0),
            "cagr": metrics.get("cagr", 0),
            "sharpe": metrics.get("sharpe_ratio", 0),
            "max_drawdown": metrics.get("max_drawdown", 0),
            "volatility": metrics.get("volatility", 0),
        }

        prompt = self.prompts.format_summary_prompt(prompt_data)
        return self.provider.generate(prompt)

    def compare_funds(self, fund_codes: list[str], funds_data: list[dict]) -> str:
        """
        对比分析多只基金

        Args:
            fund_codes: 基金代码列表
            funds_data: 基金数据列表

        Returns:
            AI生成的对比分析报告
        """
        funds_text = []
        for i, data in enumerate(funds_data):
            code = fund_codes[i] if i < len(fund_codes) else data.get("code", "")
            info = data.get("info", {})
            metrics = data.get("metrics", {})

            fund_text = f"""
基金 {i + 1}: {code}
- 名称: {info.get("name", "未知")}
- 类型: {info.get("type", "未知")}
- 年化收益: {metrics.get("cagr", 0)}%
- 夏普比率: {metrics.get("sharpe_ratio", 0)}
- 最大回撤: {metrics.get("max_drawdown", 0)}%
- 波动率: {metrics.get("volatility", 0)}%
"""
            funds_text.append(fund_text)

        prompt = self.prompts.format_compare_prompt("\n".join(funds_text))
        return self.provider.generate(prompt)

    def investment_advice(
        self, fund_code: str, fund_data: dict[str, Any], risk_profile: str
    ) -> dict[str, str]:
        """
        生成投资建议

        Args:
            fund_code: 基金代码
            fund_data: 基金数据
            risk_profile: 风险偏好 (conservative/moderate/aggressive)

        Returns:
            结构化投资建议字典
        """
        info = fund_data.get("info", {})
        metrics = fund_data.get("metrics", {})

        fund_info = {
            "name": info.get("name", "未知"),
            "code": fund_code,
            "type": info.get("type", "未知"),
            "cagr": metrics.get("cagr", 0),
            "sharpe": metrics.get("sharpe_ratio", 0),
            "max_drawdown": metrics.get("max_drawdown", 0),
        }

        prompt = self.prompts.format_investment_advice_prompt(fund_info, risk_profile)
        response = self.provider.generate(prompt)

        return self._parse_json_response(response)

    def risk_assessment(
        self, fund_code: str, fund_data: dict[str, Any], detailed: bool = False
    ) -> dict[str, str]:
        """
        深度风险评估

        Args:
            fund_code: 基金代码
            fund_data: 基金数据
            detailed: 是否生成详细分析

        Returns:
            风险评估结果字典
        """
        info = fund_data.get("info", {})
        nav_data = fund_data.get("nav", [])

        # 计算风险指标
        risk_metrics = self._calculate_risk_metrics(nav_data)

        fund_info = {
            "name": info.get("name", "未知"),
            "code": fund_code,
            "max_drawdown": risk_metrics.get("max_drawdown", 0),
            "volatility": risk_metrics.get("volatility", 0),
            "downside_deviation": risk_metrics.get("downside_deviation", 0),
            "sortino_ratio": risk_metrics.get("sortino_ratio", 0),
            "beta": risk_metrics.get("beta", 0),
            "risk_events": "无重大风险事件",  # 可从历史数据中提取
        }

        prompt = self.prompts.format_risk_assessment_prompt(fund_info, detailed)
        response = self.provider.generate(prompt)

        return self._parse_json_response(response)

    def market_insight(
        self, fund_code: str, fund_data: dict[str, Any], market_context: str | None = None
    ) -> str:
        """
        市场解读分析

        Args:
            fund_code: 基金代码
            fund_data: 基金数据
            market_context: 市场环境描述（可选）

        Returns:
            市场解读文本
        """
        info = fund_data.get("info", {})
        nav_data = fund_data.get("nav", [])

        # 计算近期收益
        recent_return = 0
        if len(nav_data) >= 2:
            recent_return = (nav_data[-1] - nav_data[0]) / nav_data[0] * 100

        fund_info = {
            "name": info.get("name", "未知"),
            "code": fund_code,
            "recent_return": recent_return,
            "rank_in_category": "前30%",  # 可从数据中获取
        }

        prompt = self.prompts.format_market_insight_prompt(fund_info, market_context)
        return self.provider.generate(prompt)

    def portfolio_review(self, portfolio_data: dict[str, Any]) -> dict[str, str]:
        """
        投资组合分析

        Args:
            portfolio_data: 组合数据，包含持仓、权重、历史收益等

        Returns:
            组合分析结果
        """
        # 计算组合指标
        portfolio_metrics = self._calculate_portfolio_metrics(portfolio_data)

        portfolio_info = {
            "funds": portfolio_data.get("funds", []),
            "weights": portfolio_data.get("weights", []),
            "expected_return": portfolio_metrics.get("expected_return", 0),
            "expected_volatility": portfolio_metrics.get("expected_volatility", 0),
            "portfolio_sharpe": portfolio_metrics.get("portfolio_sharpe", 0),
        }

        prompt = self.prompts.format_portfolio_review_prompt(portfolio_info)
        response = self.provider.generate(prompt)

        return self._parse_json_response(response)

    def generate_report(
        self, fund_code: str, fund_info: dict[str, Any], metrics: dict[str, Any]
    ) -> str:
        """
        生成分析报告

        Args:
            fund_code: 基金代码
            fund_info: 基金信息
            metrics: 分析指标

        Returns:
            报告文本
        """
        prompt_data = {
            "fund_code": fund_code,
            "fund_name": fund_info.get("name", "未知"),
            "fund_type": fund_info.get("type", "未知"),
            "manager": fund_info.get("manager", "未知"),
            "total_return": metrics.get("total_return", 0),
            "cagr": metrics.get("cagr", 0),
            "sharpe": metrics.get("sharpe_ratio", 0),
            "max_drawdown": metrics.get("max_drawdown", 0),
            "volatility": metrics.get("volatility", 0),
        }

        prompt = self.prompts.format_summary_prompt(prompt_data)
        return self.provider.generate(prompt)

    def _parse_json_response(self, response: str) -> dict[str, str]:
        """
        解析JSON格式的AI响应

        Args:
            response: AI响应文本

        Returns:
            解析后的字典
        """
        # 尝试提取JSON内容
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # 如果JSON解析失败，返回结构化文本
        return {"raw_response": response}

    def _calculate_risk_metrics(self, nav_data: list) -> dict[str, float]:
        """
        计算风险指标

        Args:
            nav_data: 净值数据列表

        Returns:
            风险指标字典
        """
        if not nav_data or len(nav_data) < 2:
            return {
                "max_drawdown": 0,
                "volatility": 0,
                "downside_deviation": 0,
                "sortino_ratio": 0,
                "beta": 0,
            }

        import numpy as np

        # 计算收益率
        returns = np.diff(nav_data) / nav_data[:-1]

        # 最大回撤
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown) * 100 if len(drawdown) > 0 else 0

        # 波动率
        volatility = np.std(returns) * np.sqrt(252) * 100 if len(returns) > 0 else 0

        # 下行标准差
        downside_returns = returns[returns < 0]
        downside_deviation = (
            np.std(downside_returns) * np.sqrt(252) * 100 if len(downside_returns) > 0 else 0
        )

        # 索提诺比率
        avg_return = np.mean(returns) * 252 * 100 if len(returns) > 0 else 0
        sortino_ratio = avg_return / downside_deviation if downside_deviation > 0 else 0

        # Beta (简化计算，假设市场收益率为0)
        beta = 1.0

        return {
            "max_drawdown": abs(max_drawdown),
            "volatility": volatility,
            "downside_deviation": downside_deviation,
            "sortino_ratio": sortino_ratio,  # type: ignore[dict-item]
            "beta": beta,
        }

    def _calculate_portfolio_metrics(self, portfolio_data: dict) -> dict[str, float]:
        """
        计算组合指标

        Args:
            portfolio_data: 组合数据

        Returns:
            组合指标字典
        """
        funds = portfolio_data.get("funds", [])
        weights = portfolio_data.get("weights", [])

        if not funds or not weights:
            return {
                "expected_return": 0,
                "expected_volatility": 0,
                "portfolio_sharpe": 0,
            }

        # 计算加权平均收益
        total_return = 0
        total_sharpe = 0

        for i, fund in enumerate(funds):
            weight = weights[i] if i < len(weights) else 0
            metrics = fund.get("metrics", {})
            total_return += metrics.get("cagr", 0) * weight
            total_sharpe += metrics.get("sharpe_ratio", 0) * weight

        # 简化计算，假设波动率为10%
        volatility = 10.0

        return {
            "expected_return": total_return,
            "expected_volatility": volatility,
            "portfolio_sharpe": total_sharpe,
        }
