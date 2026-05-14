"""
重仓股风格标签识别器

对重仓股进行风格标签识别和命名组追踪。
"""

from __future__ import annotations

import logging
from typing import Any

from fund_cli.core.analyzer import Analyzer

logger = logging.getLogger(__name__)


class StockStyleTagger:
    """
    重仓股风格标签识别器

    功能：
    - 风格标签识别（科技/消费/金融/医药/资源等）
    - 命名组追踪（美股科技七巨头、中国互联网巨头等）
    - 主导风格判断
    """

    # 预定义风格关键词
    STYLE_KEYWORDS: dict[str, list[str]] = {
        "科技": ["半导体", "芯片", "软件", "信息", "科技", "通信", "电子", "计算机", "互联网",
                "苹果", "微软", "谷歌", "亚马逊", "英伟达", "特斯拉", "Meta", "博通", "阿斯麦",
                "中际", "新易盛", "沪电", "深南", "东山", "闪迪", "美光", "智谱"],
        "消费": ["白酒", "食品", "饮料", "家电", "零售", "服装", "旅游", "餐饮"],
        "金融": ["银行", "保险", "证券", "信托", "期货"],
        "医药": ["药", "医疗", "生物", "健康", "诊断"],
        "资源": ["矿", "金属", "资源", "能源", "石油", "煤炭", "钢铁", "有色", "紫金", "钼业", "黄金", "赤峰"],
        "制造": ["汽车", "机械", "电气", "军工", "航空", "船舶"],
        "地产": ["地产", "房产", "建筑", "建材"],
    }

    # 预定义命名组
    NAMED_GROUPS: dict[str, list[str]] = {
        "美股科技七巨头": ["苹果", "微软", "谷歌", "亚马逊", "英伟达", "Meta", "特斯拉",
                           "Apple", "Microsoft", "Google", "Amazon", "NVIDIA", "Tesla"],
        "中国互联网巨头": ["腾讯", "阿里巴巴", "美团", "拼多多", "京东", "百度", "网易",
                          "Tencent", "Alibaba", "Meituan", "Pinduoduo", "JD", "Baidu"],
        "A股核心资产": ["贵州茅台", "宁德时代", "招商银行", "中国平安", "比亚迪",
                       "美的集团", "恒瑞医药", "海康威视"],
    }

    def tag_stocks(
        self,
        top_stocks: list[dict[str, Any]] | list[tuple[str, float]],
    ) -> dict[str, Any]:
        """
        对重仓股进行风格标签和命名组追踪

        Args:
            top_stocks: [{'股票名称': str, '合并占比': float}, ...]
                        或 [('股票名称', 占比), ...]

        Returns:
            {风格得分, 主导风格, 命名组追踪, 风格标签}
        """
        # 统一格式
        normalized = self._normalize_stocks(top_stocks)

        # 风格得分
        style_scores: dict[str, float] = {style: 0.0 for style in self.STYLE_KEYWORDS}
        for stock in normalized:
            name = stock["股票名称"]
            weight = stock.get("合并占比", stock.get("占比", 0))
            for style, keywords in self.STYLE_KEYWORDS.items():
                if any(kw in name for kw in keywords):
                    style_scores[style] += weight

        # 主导风格
        if any(style_scores.values()):
            dominant_style = max(style_scores, key=style_scores.get)
        else:
            dominant_style = "均衡"

        # 风格标签
        tags = []
        for style, score in sorted(style_scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0:
                tags.append(f"{style}({score:.2%})")

        # 命名组追踪
        group_tracking = self._track_named_groups(normalized)

        return {
            "风格得分": {k: round(v, 4) for k, v in style_scores.items()},
            "主导风格": dominant_style,
            "风格标签": tags,
            "命名组追踪": group_tracking,
        }

    def _track_named_groups(
        self,
        normalized_stocks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """命名组追踪"""
        results = []

        for group_name, group_keywords in self.NAMED_GROUPS.items():
            matched_stocks = []
            total_weight = 0.0

            for stock in normalized_stocks:
                name = stock["股票名称"]
                weight = stock.get("合并占比", stock.get("占比", 0))
                if any(kw in name for kw in group_keywords):
                    matched_stocks.append(name)
                    total_weight += weight

            if matched_stocks:
                results.append({
                    "命名组": group_name,
                    "匹配股票": matched_stocks,
                    "合计占比": round(total_weight, 4),
                })

        return sorted(results, key=lambda x: x["合计占比"], reverse=True)

    def _normalize_stocks(
        self,
        top_stocks: list[dict[str, Any]] | list[tuple[str, float]],
    ) -> list[dict[str, Any]]:
        """统一股票数据格式"""
        normalized = []
        for stock in top_stocks:
            if isinstance(stock, tuple):
                normalized.append({"股票名称": stock[0], "占比": stock[1]})
            elif isinstance(stock, dict):
                name = stock.get("股票名称", stock.get("name", ""))
                weight = stock.get("合并占比", stock.get("占比", stock.get("weight", 0)))
                normalized.append({"股票名称": name, "占比": float(weight)})
        return normalized
