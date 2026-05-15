"""
情景分析模块

帮助用户评估不同市场环境下的预期收益和风险。
支持牛熊市分析、利率敏感度分析、风格轮动分析等。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

from fund_cli.core.data_manager import DataManager

logger = logging.getLogger(__name__)


class MarketScenario(str, Enum):
    """市场情景"""

    BULL_MARKET = "牛市"
    BEAR_MARKET = "熊市"
    SIDEWAYS = "震荡市"
    RATE_RISE = "利率上行"
    RATE_FALL = "利率下行"
    INFLATION_RISE = "通胀上行"
    DEFLATION = "通缩"


class InvestmentStyle(str, Enum):
    """投资风格"""

    VALUE = "价值"
    GROWTH = "成长"
    BALANCED = "平衡"
    SMALL_CAP = "小盘"
    LARGE_CAP = "大盘"


@dataclass
class ScenarioMetrics:
    """情景指标"""

    expected_return: float  # 预期收益 (%)
    expected_volatility: float  # 预期波动率 (%)
    expected_drawdown: float  # 预期最大回撤 (%)
    sharpe_ratio: float  # 预期夏普比率
    win_rate: float  # 胜率 (%)
    probability: float  # 情景发生概率 (%)


@dataclass
class ScenarioResult:
    """情景分析结果"""

    scenario: MarketScenario
    metrics: ScenarioMetrics
    performance_rank: int  # 在该情景下的表现排名
    style_fit: str  # 风格匹配度
    analysis: str  # 分析说明
    suggestions: list[str] = field(default_factory=list)


@dataclass
class ScenarioAnalysisReport:
    """情景分析报告"""

    fund_code: str
    fund_name: str
    fund_type: str
    # 各情景分析结果
    results: list[ScenarioResult]
    # 最佳情景
    best_scenario: MarketScenario
    # 最差情景
    worst_scenario: MarketScenario
    # 综合评估
    overall_score: float
    risk_adjusted_return: float
    # 投资建议
    investment_advice: str


class BullBearAnalyzer:
    """牛熊市分析器"""

    # 牛熊市特征参数
    BULL_CHARACTERISTICS = {
        "market_return": 30.0,  # 牛市平均收益
        "volatility": 18.0,
        "duration_months": 24,
    }

    BEAR_CHARACTERISTICS = {
        "market_return": -25.0,  # 熊市平均跌幅
        "volatility": 25.0,
        "duration_months": 12,
    }

    SIDEWAYS_CHARACTERISTICS = {
        "market_return": 5.0,
        "volatility": 15.0,
        "duration_months": 18,
    }

    def analyze(
        self,
        beta: float = 1.0,
        alpha: float = 0.0,
        fund_type: str = "股票型",
    ) -> dict[MarketScenario, ScenarioMetrics]:
        """
        分析基金在不同牛熊市情景下的表现

        Args:
            beta: 基金Beta值
            alpha: 基金Alpha值
            fund_type: 基金类型

        Returns:
            各情景下的预期指标
        """
        results = {}

        # 牛市情景
        bull_return = self.BULL_CHARACTERISTICS["market_return"] * beta + alpha
        bull_vol = self.BULL_CHARACTERISTICS["volatility"] * abs(beta)
        results[MarketScenario.BULL_MARKET] = ScenarioMetrics(
            expected_return=round(bull_return, 2),
            expected_volatility=round(bull_vol, 2),
            expected_drawdown=round(-bull_vol * 0.5, 2),
            sharpe_ratio=round(bull_return / bull_vol, 2) if bull_vol > 0 else 0,
            win_rate=70.0,
            probability=35.0,
        )

        # 熊市情景
        bear_return = self.BEAR_CHARACTERISTICS["market_return"] * beta + alpha
        bear_vol = self.BEAR_CHARACTERISTICS["volatility"] * abs(beta)
        results[MarketScenario.BEAR_MARKET] = ScenarioMetrics(
            expected_return=round(bear_return, 2),
            expected_volatility=round(bear_vol, 2),
            expected_drawdown=round(bear_return * 0.8, 2),
            sharpe_ratio=round(bear_return / bear_vol, 2) if bear_vol > 0 else 0,
            win_rate=30.0,
            probability=25.0,
        )

        # 震荡市情景
        sideways_return = self.SIDEWAYS_CHARACTERISTICS["market_return"] * beta + alpha
        sideways_vol = self.SIDEWAYS_CHARACTERISTICS["volatility"] * abs(beta)
        results[MarketScenario.SIDEWAYS] = ScenarioMetrics(
            expected_return=round(sideways_return, 2),
            expected_volatility=round(sideways_vol, 2),
            expected_drawdown=round(-sideways_vol * 0.3, 2),
            sharpe_ratio=round(sideways_return / sideways_vol, 2) if sideways_vol > 0 else 0,
            win_rate=50.0,
            probability=40.0,
        )

        return results


class RateSensitivityAnalyzer:
    """利率敏感度分析器"""

    def analyze(
        self,
        duration: float = 5.0,  # 久期（年）
        fund_type: str = "债券型",
    ) -> dict[MarketScenario, ScenarioMetrics]:
        """
        分析基金对利率变动的敏感度

        Args:
            duration: 组合久期
            fund_type: 基金类型

        Returns:
            各利率情景下的预期指标
        """
        results = {}

        # 利率上行情景（利率上升1%）
        # 债券价格变动 ≈ -久期 × 利率变动
        rate_rise_impact = -duration * 1.0

        results[MarketScenario.RATE_RISE] = ScenarioMetrics(
            expected_return=round(rate_rise_impact, 2),
            expected_volatility=round(abs(duration) * 0.5, 2),
            expected_drawdown=round(rate_rise_impact * 0.8, 2),
            sharpe_ratio=round(rate_rise_impact / (abs(duration) * 0.5), 2) if duration > 0 else 0,
            win_rate=20.0,
            probability=40.0,
        )

        # 利率下行情景（利率下降1%）
        rate_fall_impact = -duration * (-1.0)  # 利率下降，债券价格上涨

        results[MarketScenario.RATE_FALL] = ScenarioMetrics(
            expected_return=round(rate_fall_impact, 2),
            expected_volatility=round(abs(duration) * 0.3, 2),
            expected_drawdown=round(-abs(duration) * 0.2, 2),
            sharpe_ratio=round(rate_fall_impact / (abs(duration) * 0.3), 2) if duration > 0 else 0,
            win_rate=80.0,
            probability=30.0,
        )

        return results


class StyleRotationAnalyzer:
    """风格轮动分析器"""

    # 风格在不同市场环境下的表现
    STYLE_PERFORMANCE = {
        InvestmentStyle.VALUE: {
            "bull": 0.8,  # 相对市场表现
            "bear": 1.2,
            "sideways": 1.0,
        },
        InvestmentStyle.GROWTH: {
            "bull": 1.3,
            "bear": 0.7,
            "sideways": 0.9,
        },
        InvestmentStyle.BALANCED: {
            "bull": 1.0,
            "bear": 1.0,
            "sideways": 1.0,
        },
        InvestmentStyle.SMALL_CAP: {
            "bull": 1.4,
            "bear": 0.6,
            "sideways": 0.8,
        },
        InvestmentStyle.LARGE_CAP: {
            "bull": 0.9,
            "bear": 1.1,
            "sideways": 1.1,
        },
    }

    def analyze(
        self,
        style: InvestmentStyle = InvestmentStyle.BALANCED,
        market_return: float = 10.0,
    ) -> dict[str, float]:
        """
        分析基金在不同风格环境下的表现

        Args:
            style: 基金投资风格
            market_return: 市场基准收益

        Returns:
            各环境下的预期收益
        """
        style_perf = self.STYLE_PERFORMANCE.get(style, self.STYLE_PERFORMANCE[InvestmentStyle.BALANCED])

        return {
            "牛市预期收益": round(market_return * style_perf["bull"], 2),
            "熊市预期收益": round(-abs(market_return) * style_perf["bear"], 2),
            "震荡市预期收益": round(market_return * 0.3 * style_perf["sideways"], 2),
            "风格优势": self._get_style_advantage(style),
        }

    def _get_style_advantage(self, style: InvestmentStyle) -> str:
        """获取风格优势说明"""
        advantages = {
            InvestmentStyle.VALUE: "在熊市和震荡市中表现较好，防御性强",
            InvestmentStyle.GROWTH: "在牛市中表现突出，但波动较大",
            InvestmentStyle.BALANCED: "各市场环境下表现均衡，风险可控",
            InvestmentStyle.SMALL_CAP: "牛市弹性大，但熊市跌幅也大",
            InvestmentStyle.LARGE_CAP: "稳定性好，适合长期配置",
        }
        return advantages.get(style, "风格特征不明显")


class ProbabilityWeightedAnalyzer:
    """概率加权分析器"""

    def analyze(
        self,
        scenario_results: dict[MarketScenario, ScenarioMetrics],
        custom_probabilities: dict[MarketScenario, float] | None = None,
    ) -> dict[str, float]:
        """
        基于概率加权计算预期收益和风险

        Args:
            scenario_results: 各情景分析结果
            custom_probabilities: 自定义概率（可选）

        Returns:
            概率加权后的综合指标
        """
        # 使用自定义概率或默认概率
        probabilities = {}
        for scenario, metrics in scenario_results.items():
            if custom_probabilities and scenario in custom_probabilities:
                probabilities[scenario] = custom_probabilities[scenario]
            else:
                probabilities[scenario] = metrics.probability

        # 归一化概率
        total_prob = sum(probabilities.values())
        if total_prob > 0:
            probabilities = {k: v / total_prob for k, v in probabilities.items()}

        # 计算加权预期收益
        expected_return = sum(
            metrics.expected_return * probabilities.get(scenario, 0)
            for scenario, metrics in scenario_results.items()
        )

        # 计算加权波动率
        expected_volatility = sum(
            metrics.expected_volatility * probabilities.get(scenario, 0)
            for scenario, metrics in scenario_results.items()
        )

        # 计算综合夏普比率
        risk_free_rate = 2.0  # 无风险利率
        sharpe_ratio = (expected_return - risk_free_rate) / expected_volatility if expected_volatility > 0 else 0

        return {
            "加权预期收益": round(expected_return, 2),
            "加权预期波动率": round(expected_volatility, 2),
            "综合夏普比率": round(sharpe_ratio, 2),
            "情景覆盖数": len(scenario_results),
        }


class ScenarioAnalyzer:
    """
    情景分析主类

    整合牛熊市分析、利率敏感度分析、风格轮动分析等功能。
    """

    def __init__(self, data_manager: DataManager | None = None):
        """
        初始化情景分析器

        Args:
            data_manager: 数据管理器实例
        """
        self._dm = data_manager or DataManager()
        self._bull_bear_analyzer = BullBearAnalyzer()
        self._rate_analyzer = RateSensitivityAnalyzer()
        self._style_analyzer = StyleRotationAnalyzer()
        self._probability_analyzer = ProbabilityWeightedAnalyzer()

    def analyze(
        self,
        fund_code: str,
        fund_name: str = "",
        fund_type: str = "股票型",
        beta: float = 1.0,
        alpha: float = 0.0,
        duration: float = 5.0,
        style: InvestmentStyle = InvestmentStyle.BALANCED,
    ) -> ScenarioAnalysisReport:
        """
        执行完整情景分析

        Args:
            fund_code: 基金代码
            fund_name: 基金名称
            fund_type: 基金类型
            beta: 基金Beta值
            alpha: 基金Alpha值
            duration: 久期（债券基金）
            style: 投资风格

        Returns:
            情景分析报告
        """
        results = []

        # 牛熊市分析
        bull_bear_results = self._bull_bear_analyzer.analyze(beta, alpha, fund_type)
        for scenario, metrics in bull_bear_results.items():
            result = ScenarioResult(
                scenario=scenario,
                metrics=metrics,
                performance_rank=self._calculate_rank(metrics.expected_return),
                style_fit=self._get_style_fit(scenario, style),
                analysis=self._generate_analysis(scenario, metrics, fund_type),
                suggestions=self._generate_suggestions(scenario, metrics),
            )
            results.append(result)

        # 利率敏感度分析（债券基金）
        if "债" in fund_type or duration > 0:
            rate_results = self._rate_analyzer.analyze(duration, fund_type)
            for scenario, metrics in rate_results.items():
                result = ScenarioResult(
                    scenario=scenario,
                    metrics=metrics,
                    performance_rank=self._calculate_rank(metrics.expected_return),
                    style_fit="利率敏感型",
                    analysis=self._generate_rate_analysis(scenario, metrics, duration),
                    suggestions=self._generate_rate_suggestions(scenario, metrics, duration),
                )
                results.append(result)

        # 找出最佳和最差情景
        sorted_results = sorted(results, key=lambda x: x.metrics.expected_return, reverse=True)
        best_scenario = sorted_results[0].scenario if sorted_results else MarketScenario.SIDEWAYS
        worst_scenario = sorted_results[-1].scenario if sorted_results else MarketScenario.BEAR_MARKET

        # 计算综合评分
        scenario_dict = {r.scenario: r.metrics for r in results}
        weighted_metrics = self._probability_analyzer.analyze(scenario_dict)
        overall_score = weighted_metrics["综合夏普比率"] * 20 + weighted_metrics["加权预期收益"]
        risk_adjusted_return = weighted_metrics["综合夏普比率"]

        # 生成投资建议
        investment_advice = self._generate_investment_advice(
            best_scenario, worst_scenario, overall_score, style
        )

        return ScenarioAnalysisReport(
            fund_code=fund_code,
            fund_name=fund_name or fund_code,
            fund_type=fund_type,
            results=results,
            best_scenario=best_scenario,
            worst_scenario=worst_scenario,
            overall_score=round(overall_score, 2),
            risk_adjusted_return=round(risk_adjusted_return, 2),
            investment_advice=investment_advice,
        )

    def _calculate_rank(self, expected_return: float) -> int:
        """计算表现排名"""
        if expected_return > 20:
            return 1
        elif expected_return > 10:
            return 2
        elif expected_return > 0:
            return 3
        elif expected_return > -10:
            return 4
        else:
            return 5

    def _get_style_fit(self, scenario: MarketScenario, style: InvestmentStyle) -> str:
        """获取风格匹配度"""
        fit_matrix = {
            MarketScenario.BULL_MARKET: {
                InvestmentStyle.GROWTH: "高度匹配",
                InvestmentStyle.VALUE: "中度匹配",
                InvestmentStyle.BALANCED: "中度匹配",
            },
            MarketScenario.BEAR_MARKET: {
                InvestmentStyle.VALUE: "高度匹配",
                InvestmentStyle.BALANCED: "中度匹配",
                InvestmentStyle.GROWTH: "低度匹配",
            },
            MarketScenario.SIDEWAYS: {
                InvestmentStyle.BALANCED: "高度匹配",
                InvestmentStyle.VALUE: "中度匹配",
                InvestmentStyle.GROWTH: "低度匹配",
            },
        }
        return fit_matrix.get(scenario, {}).get(style, "中度匹配")

    def _generate_analysis(
        self,
        scenario: MarketScenario,
        metrics: ScenarioMetrics,
        fund_type: str,
    ) -> str:
        """生成分析说明"""
        if scenario == MarketScenario.BULL_MARKET:
            return f"在牛市环境下，{fund_type}预期收益{metrics.expected_return:.1f}%，表现{'优异' if metrics.expected_return > 20 else '良好'}"
        elif scenario == MarketScenario.BEAR_MARKET:
            return f"在熊市环境下，{fund_type}预期损失{abs(metrics.expected_return):.1f}%，{'需要关注风险' if metrics.expected_return < -20 else '风险可控'}"
        else:
            return f"在震荡市环境下，{fund_type}预期收益{metrics.expected_return:.1f}%，表现平稳"

    def _generate_suggestions(
        self,
        scenario: MarketScenario,
        metrics: ScenarioMetrics,
    ) -> list[str]:
        """生成投资建议"""
        suggestions = []

        if scenario == MarketScenario.BULL_MARKET:
            if metrics.expected_return > 20:
                suggestions.append("牛市环境下表现优异，可适当增加仓位")
            suggestions.append("注意设置止盈点，锁定收益")
        elif scenario == MarketScenario.BEAR_MARKET:
            if metrics.expected_return < -20:
                suggestions.append("熊市风险较大，建议降低仓位")
            suggestions.append("可考虑配置防御性资产")
        else:
            suggestions.append("震荡市建议保持耐心，逢低布局")

        return suggestions

    def _generate_rate_analysis(
        self,
        scenario: MarketScenario,
        metrics: ScenarioMetrics,
        duration: float,
    ) -> str:
        """生成利率分析说明"""
        if scenario == MarketScenario.RATE_RISE:
            return f"利率上行1%时，久期{duration:.1f}年的组合预计损失{abs(metrics.expected_return):.1f}%"
        else:
            return f"利率下行1%时，久期{duration:.1f}年的组合预计收益{metrics.expected_return:.1f}%"

    def _generate_rate_suggestions(
        self,
        scenario: MarketScenario,
        metrics: ScenarioMetrics,
        duration: float,
    ) -> list[str]:
        """生成利率相关建议"""
        suggestions = []

        if scenario == MarketScenario.RATE_RISE:
            if duration > 5:
                suggestions.append("久期较长，利率上行风险较大，建议缩短久期")
            suggestions.append("可考虑配置浮动利率债券")
        else:
            suggestions.append("利率下行利好债券，可适当拉长久期")

        return suggestions

    def _generate_investment_advice(
        self,
        best_scenario: MarketScenario,
        worst_scenario: MarketScenario,
        overall_score: float,
        style: InvestmentStyle,
    ) -> str:
        """生成综合投资建议"""
        lines = []

        lines.append(f"该基金在【{best_scenario.value}】环境下表现最佳")
        lines.append(f"在【{worst_scenario.value}】环境下风险较大")

        if overall_score > 30:
            lines.append("综合评分较高，适合作为核心配置")
        elif overall_score > 15:
            lines.append("综合评分中等，可作为卫星配置")
        else:
            lines.append("综合评分较低，建议谨慎配置")

        lines.append(f"投资风格【{style.value}】，适合{self._get_target_investor(style)}")

        return "；".join(lines)

    def _get_target_investor(self, style: InvestmentStyle) -> str:
        """获取目标投资者"""
        targets = {
            InvestmentStyle.VALUE: "稳健型投资者",
            InvestmentStyle.GROWTH: "进取型投资者",
            InvestmentStyle.BALANCED: "平衡型投资者",
            InvestmentStyle.SMALL_CAP: "高风险偏好投资者",
            InvestmentStyle.LARGE_CAP: "稳健型投资者",
        }
        return targets.get(style, "一般投资者")

    def format_report(self, report: ScenarioAnalysisReport) -> str:
        """
        格式化情景分析报告

        Args:
            report: 情景分析报告

        Returns:
            格式化的报告文本
        """
        lines = ["# 情景分析报告\n"]

        lines.append("## 基本信息")
        lines.append(f"- 基金代码: {report.fund_code}")
        lines.append(f"- 基金名称: {report.fund_name}")
        lines.append(f"- 基金类型: {report.fund_type}")
        lines.append("")

        lines.append("## 综合评估")
        lines.append(f"- 最佳情景: {report.best_scenario.value}")
        lines.append(f"- 最差情景: {report.worst_scenario.value}")
        lines.append(f"- 综合评分: {report.overall_score:.2f}")
        lines.append(f"- 风险调整收益: {report.risk_adjusted_return:.2f}")
        lines.append("")

        lines.append("## 各情景分析结果")
        for result in report.results:
            lines.append(f"### {result.scenario.value}")
            lines.append(f"- 预期收益: {result.metrics.expected_return:.2f}%")
            lines.append(f"- 预期波动率: {result.metrics.expected_volatility:.2f}%")
            lines.append(f"- 预期最大回撤: {result.metrics.expected_drawdown:.2f}%")
            lines.append(f"- 夏普比率: {result.metrics.sharpe_ratio:.2f}")
            lines.append(f"- 胜率: {result.metrics.win_rate:.1f}%")
            lines.append(f"- 发生概率: {result.metrics.probability:.1f}%")
            lines.append(f"- 风格匹配: {result.style_fit}")
            lines.append(f"- 分析: {result.analysis}")
            if result.suggestions:
                lines.append("- 建议:")
                for s in result.suggestions:
                    lines.append(f"  - {s}")
            lines.append("")

        lines.append("## 投资建议")
        lines.append(report.investment_advice)

        return "\n".join(lines)


def analyze_scenarios(
    fund_code: str,
    fund_type: str = "股票型",
    beta: float = 1.0,
    data_manager: DataManager | None = None,
) -> ScenarioAnalysisReport:
    """
    情景分析便捷函数

    Args:
        fund_code: 基金代码
        fund_type: 基金类型
        beta: 基金Beta值
        data_manager: 数据管理器实例

    Returns:
        情景分析报告
    """
    analyzer = ScenarioAnalyzer(data_manager)
    return analyzer.analyze(fund_code, fund_type=fund_type, beta=beta)
