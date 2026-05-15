"""
单只基金双轨评价器

根据基金类型自动选择评价路径：
- 主动型基金：产品评分 + 经理评分 + 百分位排名
- 指数型基金：超额收益 + PE分位 + 估值判断
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class FundEvaluator:
    """
    单只基金双轨评价器

    评价路径：
    - 主动型 → FundScoringEngine + ManagerAnalyzer
    - 指数型 → IndexFundValuator

    输出：
    - 三档建议：继续持有 / 观察 / 替换
    """

    # 指数型基金关键词
    INDEX_KEYWORDS = ["指数", "ETF", "跟踪", "联接", "LOF"]

    def __init__(self, data_manager=None):
        from fund_cli.core.data_manager import get_data_manager

        self._dm = data_manager or get_data_manager()

    def evaluate(
        self,
        fund_code: str,
        fund_info: dict[str, Any] | None = None,
        nav_series: pd.Series | None = None,
        peer_returns_list: list[pd.Series] | None = None,
        benchmark_nav: pd.Series | None = None,
        portfolio_codes: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        统一评价入口

        Args:
            fund_code: 基金代码
            fund_info: 基金信息（可选，自动获取）
            nav_series: 净值序列（可选，自动获取）
            peer_returns_list: 同类基金收益率（可选）
            benchmark_nav: 基准净值（可选）
            portfolio_codes: 组合中所有基金代码（用于获取同类收益率，默认使用持仓基金）

        Returns:
            {基金代码, 基金名称, 基金类型, 评价路径, 评分, 建议}
        """
        # 获取基础信息
        if fund_info is None:
            fund_info = self._dm.get_fund_info(fund_code) or {}

        # 获取基金名称（优先用 fund_name 字段）
        fund_name = fund_info.get("fund_name") or fund_info.get("name") or fund_code
        fund_type = fund_info.get("type", "")

        is_index = self._is_index_fund(fund_type, fund_name)

        if is_index:
            return self._evaluate_index_fund(fund_code, fund_name, fund_type, nav_series, benchmark_nav, portfolio_codes)
        else:
            return self._evaluate_active_fund(fund_code, fund_name, fund_type, nav_series, peer_returns_list, portfolio_codes)

    def three_tier_advice(self, composite_score: float) -> str:
        """
        三档操作建议

        Args:
            composite_score: 综合得分 (0-1)

        Returns:
            继续持有 / 观察 / 替换
        """
        if composite_score >= 0.60:
            return "继续持有"
        elif composite_score >= 0.35:
            return "观察"
        else:
            return "替换"

    def compute_detailed_scores(
        self,
        fund_code: str,
        nav_series: pd.Series | None = None,
        peer_returns_list: list[pd.Series] | None = None,
    ) -> dict[str, Any]:
        """
        计算基金细分得分

        Args:
            fund_code: 基金代码
            nav_series: 净值序列
            peer_returns_list: 同类基金收益率列表

        Returns:
            {
                "最大回撤得分": float,
                "区间收益得分": float,
                "规模得分": float,
                "创新高得分": float,
                "择股得分": float,
                "择时得分": float,
                "近1年排名": float,
                "近2年排名": float,
            }
        """
        from datetime import datetime, timedelta

        result = {
            "最大回撤得分": 0.5,
            "区间收益得分": 0.5,
            "规模得分": 0.5,
            "创新高得分": 0.5,
            "择股得分": 0.5,
            "择时得分": 0.5,
            "近1年排名": 50.0,
            "近2年排名": 50.0,
        }

        # 自动获取净值数据
        if nav_series is None:
            nav_series = self._auto_fetch_nav(fund_code)

        if nav_series is None or nav_series.empty or len(nav_series) < 30:
            return result

        try:
            returns = nav_series.pct_change().dropna()

            # 1. 最大回撤得分（回撤越小得分越高）
            cum_returns = (1 + returns).cumprod()
            rolling_max = cum_returns.cummax()
            drawdown = (cum_returns - rolling_max) / rolling_max
            max_dd = abs(drawdown.min())
            # 回撤0%得1分，回撤50%得0分
            result["最大回撤得分"] = max(0, min(1, 1 - max_dd * 2))

            # 2. 区间收益得分
            total_return = cum_returns.iloc[-1] / cum_returns.iloc[0] - 1
            # 年化收益映射到得分
            years = len(returns) / 252
            annual_return = (1 + total_return) ** (1 / max(years, 0.1)) - 1 if total_return > -1 else -1
            if annual_return > 0.3:
                result["区间收益得分"] = 0.9
            elif annual_return > 0.2:
                result["区间收益得分"] = 0.8
            elif annual_return > 0.1:
                result["区间收益得分"] = 0.7
            elif annual_return > 0.05:
                result["区间收益得分"] = 0.6
            elif annual_return > 0:
                result["区间收益得分"] = 0.5
            else:
                result["区间收益得分"] = max(0.2, 0.5 + annual_return)

            # 3. 规模得分（基于基金信息估算）
            try:
                info = self._dm.get_fund_info(fund_code)
                if info:
                    scale = info.get("scale", info.get("fund_scale", 0))
                    if isinstance(scale, (int, float)):
                        # 规模2-50亿为最佳区间
                        if 2 <= scale <= 50:
                            result["规模得分"] = 0.9
                        elif 50 < scale <= 100:
                            result["规模得分"] = 0.7
                        elif scale > 100:
                            result["规模得分"] = 0.5  # 规模过大
                        else:
                            result["规模得分"] = 0.6  # 规模较小
            except Exception:
                pass

            # 4. 创新高得分（统计创新高次数）
            new_high_count = 0
            for i in range(1, len(cum_returns)):
                if cum_returns.iloc[i] > cum_returns.iloc[:i].max():
                    new_high_count += 1
            new_high_ratio = new_high_count / len(cum_returns)
            result["创新高得分"] = min(1, new_high_ratio * 5)  # 20%创新高率即为满分

            # 5. 择股得分（基于超额收益估算）
            if peer_returns_list and len(peer_returns_list) > 0:
                # 计算相对同类的超额收益
                peer_avg_returns = pd.concat(peer_returns_list, axis=1).mean(axis=1)
                excess = returns.mean() - peer_avg_returns.mean()
                if excess > 0.001:
                    result["择股得分"] = min(1, 0.6 + excess * 100)
                else:
                    result["择股得分"] = max(0.3, 0.5 + excess * 50)

            # 6. 择时得分（基于下行捕获比率估算）
            negative_returns = returns[returns < 0]
            if len(negative_returns) > 5 and peer_returns_list:
                peer_avg = pd.concat(peer_returns_list, axis=1).mean(axis=1)
                peer_negative = peer_avg[peer_avg < 0]
                if len(peer_negative) > 5:
                    # 下行捕获比率
                    fund_down = negative_returns.mean()
                    peer_down = peer_negative.mean()
                    if peer_down != 0:
                        capture_ratio = abs(fund_down / peer_down)
                        # 捕获比率越小越好（跌得少）
                        result["择时得分"] = min(1, max(0.3, 1 - capture_ratio * 0.5))

            # 7. 近1年/近2年排名（基于收益率估算百分位）
            end_date = datetime.now()
            for years, key in [(1, "近1年排名"), (2, "近2年排名")]:
                start_date = end_date - timedelta(days=365 * years)
                try:
                    if isinstance(nav_series.index, pd.DatetimeIndex):
                        period_nav = nav_series[(nav_series.index >= start_date) & (nav_series.index <= end_date)]
                    else:
                        period_nav = nav_series  # 无法筛选日期时使用全部数据

                    if len(period_nav) > 20:
                        period_return = period_nav.iloc[-1] / period_nav.iloc[0] - 1
                        annual_ret = period_return / years
                        # 基于年化收益估算排名百分位
                        if annual_ret > 0.3:
                            result[key] = 10.0  # 前10%
                        elif annual_ret > 0.2:
                            result[key] = 25.0  # 前25%
                        elif annual_ret > 0.1:
                            result[key] = 40.0  # 前40%
                        elif annual_ret > 0.05:
                            result[key] = 50.0  # 中位数
                        elif annual_ret > 0:
                            result[key] = 60.0  # 后40%
                        else:
                            result[key] = 80.0  # 后20%
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"计算细分得分失败: {e}")

        return result

    def _is_index_fund(self, fund_type: str, fund_name: str) -> bool:
        """判断是否为指数型基金"""
        combined = fund_type + fund_name
        return any(kw in combined for kw in self.INDEX_KEYWORDS)

    def _auto_fetch_nav(self, fund_code: str) -> pd.Series | None:
        """自动获取基金净值序列"""
        try:
            nav_df = self._dm.get_fund_nav(fund_code)
            if nav_df is not None and not nav_df.empty:
                # 兼容中英文列名
                if "accumulated_nav" in nav_df.columns:
                    nav_col = "accumulated_nav"
                elif "unit_nav" in nav_df.columns:
                    nav_col = "unit_nav"
                elif "累计净值" in nav_df.columns:
                    nav_col = "累计净值"
                elif "单位净值" in nav_df.columns:
                    nav_col = "单位净值"
                else:
                    logger.warning(f"基金 {fund_code} 净值数据无可用列: {nav_df.columns.tolist()}")
                    return None
                # 返回以日期为索引的净值序列
                return nav_df.set_index("nav_date")[nav_col].squeeze()
        except Exception as e:
            logger.warning(f"基金 {fund_code} 净值获取失败: {e}")
        return None

    def _auto_fetch_peer_returns(self, fund_codes: list[str]) -> list[pd.Series]:
        """获取同类基金收益率（使用批量接口）."""
        if not fund_codes:
            return []

        # 批量获取净值
        nav_map = self._dm.batch_get_fund_nav(fund_codes)

        peer_returns = []
        for code in fund_codes:
            nav_df = nav_map.get(code)
            if nav_df is None or nav_df.empty:
                continue
            # 提取净值列
            nav_col = None
            for col in ["accumulated_nav", "累计净值", "unit_nav", "单位净值"]:
                if col in nav_df.columns:
                    nav_col = col
                    break
            if nav_col is None:
                continue
            nav_series = nav_df.set_index("nav_date")[nav_col].squeeze()
            if len(nav_series) > 10:
                peer_returns.append(nav_series.pct_change().dropna())

        return peer_returns

    def _evaluate_active_fund(
        self,
        fund_code: str,
        fund_name: str,
        fund_type: str,
        nav_series: pd.Series | None,
        peer_returns_list: list[pd.Series] | None,
        portfolio_codes: list[str] | None = None,
    ) -> dict[str, Any]:
        """主动型基金评价"""
        from fund_cli.analysis.fund_scoring import FundScoringEngine

        # 自动获取净值数据
        if nav_series is None:
            nav_series = self._auto_fetch_nav(fund_code)

        score = {"综合得分": 0.5, "收益得分": 0.0, "风险得分": 0.0}

        if nav_series is not None and not nav_series.empty:
            returns = nav_series.pct_change().dropna()

            # 自动获取同类基金收益率（如果没有提供）
            if not peer_returns_list and portfolio_codes:
                # 使用组合中的所有基金作为同类（排除当前基金）
                peer_codes = [c for c in portfolio_codes if c != fund_code]
                peer_returns_list = self._auto_fetch_peer_returns(peer_codes)
                logger.info(f"基金 {fund_code}: 自动获取 {len(peer_returns_list)} 只同类基金用于评分")

            engine = FundScoringEngine()
            try:
                score = engine.compute_fund_score(returns, peer_returns_list or [])
            except Exception as e:
                logger.warning(f"基金 {fund_code} 评分失败: {e}")

        composite = score.get("综合得分", 0.5)
        grade = FundScoringEngine().score_to_grade(composite)
        advice = self.three_tier_advice(composite)

        return {
            "基金代码": fund_code,
            "基金名称": fund_name,
            "基金类型": fund_type,
            "评价路径": "主动型",
            "收益得分": score.get("收益得分", 0),
            "风险得分": score.get("风险得分", 0),
            "综合得分": composite,
            "等级": grade,
            "建议": advice,
        }

    def _evaluate_index_fund(
        self,
        fund_code: str,
        fund_name: str,
        fund_type: str,
        nav_series: pd.Series | None,
        benchmark_nav: pd.Series | None,
        portfolio_codes: list[str] | None = None,
    ) -> dict[str, Any]:
        """指数型基金评价"""
        from fund_cli.analysis.index_valuation import IndexFundValuator

        # 自动获取净值数据
        if nav_series is None:
            nav_series = self._auto_fetch_nav(fund_code)

        valuation = {
            "超额收益": 0.0,
            "估值判断": "数据不足",
            "综合建议": "数据不足，建议进一步分析",
        }

        if nav_series is not None and not nav_series.empty:
            valuator = IndexFundValuator(self._dm)
            # 获取同类基金收益率（用于 QDII 指数无 PE 数据时的替代评价）
            peer_returns_list = None
            if portfolio_codes:
                peer_codes = [c for c in portfolio_codes if c != fund_code]
                peer_returns_list = self._auto_fetch_peer_returns(peer_codes)
            try:
                valuation = valuator.evaluate(fund_code, nav_series, benchmark_nav, peer_returns_list)
            except Exception as e:
                logger.warning(f"基金 {fund_code} 估值分析失败: {e}")

        # 将估值判断映射为得分
        pe_verdict = valuation.get("估值判断", "数据不足")
        pe_percentile = valuation.get("近五年PE分位", 0.5)
        score_map = {"估值较低": 0.8, "不算贵": 0.6, "偏贵": 0.3, "数据不足": 0.5}
        composite = score_map.get(pe_verdict, 0.5)

        # 对于指数基金，收益得分基于超额收益和PE分位综合计算
        # 如果 PE 分位是 None 或 0（数据不足），使用超额收益计算
        excess_return = valuation.get("超额收益", 0)
        if pe_percentile is not None and pe_percentile > 0:
            return_score = pe_percentile
        else:
            # 无PE分位时，用超额收益计算收益得分
            # 超额收益 > 10% -> 0.8, > 0% -> 0.6, < 0% -> 0.4
            if excess_return > 0.1:
                return_score = 0.8
            elif excess_return > 0:
                return_score = 0.6
            else:
                return_score = 0.4
        # 风险得分：超额收益为正则风险得分高，为负则风险得分低
        risk_score = 0.7 if excess_return >= 0 else 0.3

        advice = self.three_tier_advice(composite)

        return {
            "基金代码": fund_code,
            "基金名称": fund_name,
            "基金类型": fund_type,
            "评价路径": "指数型",
            "收益得分": round(return_score, 2),
            "风险得分": round(risk_score, 2),
            "综合得分": composite,
            "超额收益": valuation.get("超额收益", 0),
            "当前PE": valuation.get("当前PE"),
            "PE分位": pe_percentile,
            "估值判断": pe_verdict,
            "等级": pe_verdict if pe_verdict in ("估值较低", "不算贵") else ("偏贵" if pe_verdict == "偏贵" else "一般"),
            "建议": advice,
        }
