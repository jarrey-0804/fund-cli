"""
分组相关性分析器

将基金按类型分组（QDII组/国内组），分别计算组内相关性并给出替换建议。
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from fund_cli.core.analyzer import Analyzer

logger = logging.getLogger(__name__)


class GroupCorrelationAnalyzer:
    """
    分组相关性分析器

    功能：
    - 按基金类型分组（QDII/国内）
    - 分别计算组内相关性
    - 识别高相关基金对
    - 生成替换方向建议
    """

    DEFAULT_THRESHOLD = 0.8

    def __init__(self, data_manager=None):
        from fund_cli.core.data_manager import get_data_manager
        self._dm = data_manager or get_data_manager()

    def analyze_groups(
        self,
        fund_codes: list[str],
        fund_types: dict[str, str] | None = None,
        returns_df: pd.DataFrame | None = None,
        threshold: float | None = None,
    ) -> dict[str, Any]:
        """
        分组相关性分析

        Args:
            fund_codes: 基金代码列表
            fund_types: {基金代码: 类型}（可选，自动推断）
            returns_df: 日收益率 DataFrame（可选，自动获取）
            threshold: 高相关阈值，默认 0.8

        Returns:
            {分组分析结果, 交叉组相关性, 总体建议}
        """
        if threshold is None:
            threshold = self.DEFAULT_THRESHOLD

        if fund_types is None:
            fund_types = self._infer_fund_types(fund_codes)

        if returns_df is None:
            returns_df = self._get_returns_data(fund_codes)

        if returns_df is None or returns_df.empty:
            return {"分组分析结果": {}, "交叉组相关性": {}, "总体建议": "数据不足"}

        qdii_funds = [c for c in fund_codes if "QDII" in fund_types.get(c, "").upper()]
        domestic_funds = [c for c in fund_codes if c not in qdii_funds]

        group_results: dict[str, dict[str, Any]] = {}

        for group_name, group_codes in [("QDII组", qdii_funds), ("国内组", domestic_funds)]:
            if len(group_codes) < 2:
                group_results[group_name] = {
                    "基金列表": group_codes,
                    "组内平均相关": 0.0,
                    "高相关对": [],
                    "建议": "基金数量不足，无法计算组内相关性",
                }
                continue

            available_codes = [c for c in group_codes if c in returns_df.columns]
            if len(available_codes) < 2:
                group_results[group_name] = {
                    "基金列表": group_codes,
                    "组内平均相关": 0.0,
                    "高相关对": [],
                    "建议": "可用数据不足",
                }
                continue

            sub_corr = returns_df[available_codes].corr()
            pairs = self._extract_high_corr_pairs(sub_corr, threshold)

            # 计算平均相关（排除自相关）
            mask = ~np.eye(len(available_codes), dtype=bool)
            avg_corr = sub_corr.values[mask].mean() if mask.any() else 0.0

            group_results[group_name] = {
                "基金列表": available_codes,
                "组内平均相关": round(float(avg_corr), 4),
                "高相关对": pairs,
                "建议": self._generate_group_advice(group_name, pairs, avg_corr),
            }

        # 交叉组相关性
        cross_corr = {}
        if qdii_funds and domestic_funds:
            available_qdii = [c for c in qdii_funds if c in returns_df.columns]
            available_domestic = [c for c in domestic_funds if c in returns_df.columns]
            if available_qdii and available_domestic:
                cross = returns_df[available_qdii].corrwith(returns_df[available_domestic].mean(axis=1))
                cross_corr = cross.to_dict()

        # 总体建议
        all_pairs = []
        for group_data in group_results.values():
            all_pairs.extend(group_data.get("高相关对", []))

        if len(all_pairs) > 3:
            overall_advice = f"组合内存在{len(all_pairs)}对高相关基金，分散化不足，建议替换部分高相关基金以降低组合风险"
        elif len(all_pairs) > 0:
            overall_advice = f"组合内存在{len(all_pairs)}对高相关基金，分散化尚可，可关注替换以进一步优化"
        else:
            overall_advice = "组合内基金相关性适中，分散化良好"

        return {
            "分组分析结果": group_results,
            "交叉组相关性": {k: round(v, 4) for k, v in cross_corr.items()} if cross_corr else {},
            "总体建议": overall_advice,
        }

    def _extract_high_corr_pairs(
        self,
        corr_matrix: pd.DataFrame,
        threshold: float,
    ) -> list[dict[str, Any]]:
        """提取高相关基金对"""
        pairs = []
        funds = corr_matrix.columns
        for i in range(len(funds)):
            for j in range(i + 1, len(funds)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > threshold:
                    pairs.append({
                        "基金A": funds[i],
                        "基金B": funds[j],
                        "相关系数": round(float(corr_val), 4),
                    })
        return sorted(pairs, key=lambda x: abs(x["相关系数"]), reverse=True)

    def _generate_group_advice(
        self,
        group_name: str,
        pairs: list[dict[str, Any]],
        avg_corr: float,
    ) -> str:
        """生成分组建议"""
        if not pairs:
            return f"{group_name}内基金相关性适中，配置合理"

        fund_names = "、".join(
            f"{p['基金A']}-{p['基金B']}({p['相关系数']:.2f})" for p in pairs[:3]
        )
        return f"{group_name}存在高相关基金对：{fund_names}，建议替换其中一只以降低集中度风险"

    def _infer_fund_types(self, fund_codes: list[str]) -> dict[str, str]:
        """推断基金类型"""
        types = {}
        for code in fund_codes:
            try:
                info = self._dm.get_fund_info(code)
                types[code] = info.get("type", "") if info else ""
            except Exception:
                types[code] = ""
        return types

    def _get_returns_data(self, fund_codes: list[str]) -> pd.DataFrame | None:
        """获取收益率数据"""
        try:
            returns_dict = {}
            for code in fund_codes:
                nav = self._dm.get_fund_nav(code)
                if nav is not None and not nav.empty:
                    # 兼容中英文列名
                    if "accumulated_nav" in nav.columns:
                        nav_col = "accumulated_nav"
                    elif "unit_nav" in nav.columns:
                        nav_col = "unit_nav"
                    elif "累计净值" in nav.columns:
                        nav_col = "累计净值"
                    elif "单位净值" in nav.columns:
                        nav_col = "单位净值"
                    else:
                        logger.warning(f"基金 {code} 净值数据无可用列: {nav.columns.tolist()}")
                        continue
                    returns_dict[code] = nav[nav_col].pct_change().dropna()

            if returns_dict:
                return pd.DataFrame(returns_dict)
        except Exception as e:
            logger.warning(f"获取收益率数据失败: {e}")
        return None
