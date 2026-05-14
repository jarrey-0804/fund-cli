"""
多时间维度收益风险分析器

计算近6个月、近1年、近2年的收益风险对比
"""

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from fund_cli.analysis.performance import PerformanceAnalyzer
from fund_cli.analysis.risk import RiskAnalyzer


class MultiPeriodAnalyzer:
    """
    多时间维度收益风险分析器
    
    分析维度：
    - 近6个月收益风险
    - 近1年收益风险  
    - 近2年收益风险
    """
    
    PERIODS = {
        "近6个月": 180,
        "近1年": 365,
        "近2年": 730,
    }
    
    def __init__(self, data_manager=None):
        from fund_cli.core.data_manager import get_data_manager
        self._dm = data_manager or get_data_manager()
        self._perf = PerformanceAnalyzer()
        self._risk = RiskAnalyzer()
    
    def analyze_portfolio_multi_period(
        self,
        fund_codes: list[str],
        weights: list[float],
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """
        组合多时间维度分析
        
        Args:
            fund_codes: 基金代码列表
            weights: 权重列表
            end_date: 结束日期
            
        Returns:
            {
                "近6个月": {"收益": x, "最大回撤": x, "波动率": x, "夏普": x},
                "近1年": {...},
                "近2年": {...},
                "对比结论": str
            }
        """
        results = {}
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
        
        for period_name, days in self.PERIODS.items():
            start = end - timedelta(days=days)
            try:
                metrics = self._analyze_period(fund_codes, weights, start, end)
                results[period_name] = metrics
            except Exception as e:
                results[period_name] = {"error": str(e)}
        
        # 生成对比结论
        results["对比结论"] = self._generate_comparison_conclusion(results)
        return results
    
    def analyze_fund_multi_period(
        self,
        fund_code: str,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """
        单只基金多时间维度分析
        
        Args:
            fund_code: 基金代码
            end_date: 结束日期
            
        Returns:
            各时间维度的收益风险指标
        """
        results = {}
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
        
        for period_name, days in self.PERIODS.items():
            start = end - timedelta(days=days)
            try:
                nav = self._dm.get_fund_nav(fund_code)
                if nav is not None and not nav.empty:
                    # 筛选时间范围
                    if 'nav_date' in nav.columns:
                        nav = nav[(nav['nav_date'] >= start.strftime('%Y-%m-%d')) & 
                                  (nav['nav_date'] <= end.strftime('%Y-%m-%d'))]
                    
                    if len(nav) > 10:
                        nav_col = "accumulated_nav" if "accumulated_nav" in nav.columns else "unit_nav"
                        returns = nav[nav_col].pct_change().dropna()
                        
                        perf_metrics = self._perf.analyze(returns)
                        risk_metrics = self._risk.analyze(returns)
                        
                        # 获取回撤时间段
                        dd_period = self._risk.max_drawdown_period(returns)
                        
                        results[period_name] = {
                            "累计收益": round(perf_metrics.get("total_return", 0), 2),
                            "年化收益": round(perf_metrics.get("cagr", 0), 2),
                            "最大回撤": round(risk_metrics.get("max_drawdown", 0), 2),
                            "回撤起始日": dd_period.get("peak_date", ""),
                            "回撤结束日": dd_period.get("trough_date", ""),
                            "波动率": round(perf_metrics.get("volatility", 0), 2),
                            "夏普比率": round(perf_metrics.get("sharpe", 0), 2),
                        }
            except Exception as e:
                results[period_name] = {"error": str(e)}
        
        return results
    
    def _analyze_period(
        self,
        fund_codes: list[str],
        weights: list[float],
        start: datetime,
        end: datetime,
    ) -> dict[str, Any]:
        """分析特定时间段"""
        from fund_cli.analysis.portfolio_nav import PortfolioNavCalculator
        
        calculator = PortfolioNavCalculator(self._dm)
        portfolio_nav = calculator.compute_portfolio_nav(
            fund_codes, weights,
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d"),
        )
        
        returns = calculator.compute_portfolio_returns(portfolio_nav)
        perf_metrics = self._perf.analyze(returns)
        risk_metrics = self._risk.analyze(returns)
        
        # 获取回撤时间段
        dd_period = self._risk.max_drawdown_period(returns)
        
        # 计算卡玛比率（年化收益/最大回撤绝对值）
        annual_return = perf_metrics.get("cagr", 0) / 100  # 转为小数
        max_dd = abs(risk_metrics.get("max_drawdown", 0)) / 100  # 转为小数
        calmar = annual_return / max_dd if max_dd > 0 else 0
        
        # 计算胜率（正收益天数/总交易天数）
        positive_days = (returns > 0).sum()
        total_days = len(returns)
        win_rate = (positive_days / total_days * 100) if total_days > 0 else 0
        
        return {
            "累计收益": round(perf_metrics.get("total_return", 0), 2),
            "年化收益": round(perf_metrics.get("cagr", 0), 2),
            "最大回撤": round(risk_metrics.get("max_drawdown", 0), 2),
            "回撤起始日": dd_period.get("peak_date", ""),
            "回撤结束日": dd_period.get("trough_date", ""),
            "波动率": round(perf_metrics.get("volatility", 0), 2),
            "夏普比率": round(perf_metrics.get("sharpe", 0), 2),
            "卡玛比率": round(calmar, 2),
            "胜率": round(win_rate, 2),
        }
    
    def _generate_comparison_conclusion(self, results: dict) -> str:
        """生成多时间维度对比结论"""
        conclusions = []
        
        # 分析收益趋势
        returns_6m = results.get("近6个月", {}).get("累计收益", 0)
        returns_1y = results.get("近1年", {}).get("累计收益", 0)
        returns_2y = results.get("近2年", {}).get("累计收益", 0)
        
        if returns_6m > returns_1y / 2:
            conclusions.append("近期收益表现较好")
        elif returns_6m < 0:
            conclusions.append("近期收益承压")
        
        # 分析回撤变化
        dd_6m = results.get("近6个月", {}).get("最大回撤", 0)
        dd_1y = results.get("近1年", {}).get("最大回撤", 0)
        
        if abs(dd_6m) < abs(dd_1y) * 0.5:
            conclusions.append("近期回撤控制改善")
        elif abs(dd_6m) > abs(dd_1y) * 0.8:
            conclusions.append("近期回撤有所扩大")
        
        # 分析夏普比率变化
        sharpe_6m = results.get("近6个月", {}).get("夏普比率", 0)
        sharpe_1y = results.get("近1年", {}).get("夏普比率", 0)
        
        if sharpe_6m > sharpe_1y:
            conclusions.append("风险调整收益改善")
        
        return "；".join(conclusions) if conclusions else "各时间段表现平稳"
    
    def generate_report_section(
        self,
        fund_codes: list[str],
        weights: list[float],
        end_date: str | None = None,
    ) -> str:
        """
        生成报告章节（Markdown格式）
        
        Args:
            fund_codes: 基金代码列表
            weights: 权重列表
            end_date: 结束日期
            
        Returns:
            Markdown格式的报告章节
        """
        results = self.analyze_portfolio_multi_period(fund_codes, weights, end_date)
        
        lines = []
        
        # 表格（增加卡玛比率和胜率列）
        lines.append("| 时间段 | 累计收益 | 年化收益 | 最大回撤 | 波动率 | 夏普比率 | 卡玛比率 | 胜率 |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        
        for period_name in ["近6个月", "近1年", "近2年"]:
            if period_name in results and "error" not in results[period_name]:
                data = results[period_name]
                lines.append(
                    f"| {period_name} | {data.get('累计收益', 'N/A')}% | "
                    f"{data.get('年化收益', 'N/A')}% | {data.get('最大回撤', 'N/A')}% | "
                    f"{data.get('波动率', 'N/A')}% | {data.get('夏普比率', 'N/A')} | "
                    f"{data.get('卡玛比率', 'N/A')} | {data.get('胜率', 'N/A')}% |"
                )
        
        lines.append("")
        
        # 结论
        if "对比结论" in results:
            lines.append(f"**结论**: {results['对比结论']}")
            lines.append("")
        
        # 回撤详情
        lines.append("**最大回撤时间段**:\n")
        for period_name in ["近6个月", "近1年", "近2年"]:
            if period_name in results and "error" not in results[period_name]:
                data = results[period_name]
                if data.get("回撤起始日") and data.get("回撤结束日"):
                    lines.append(
                        f"- {period_name}: {data['回撤起始日']} 至 {data['回撤结束日']}"
                    )
        
        return "\n".join(lines)
