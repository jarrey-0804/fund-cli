"""
资产穿透分析器

按市值加权汇总，穿透基金持仓到大类资产、国家/地区、行业、重仓股等维度。
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class AssetLookthroughAnalyzer:
    """
    资产穿透分析器

    功能：
    - 大类资产穿透（权益/固收/商品/现金）
    - 国家/地区穿透（国内/QDII）
    - 行业穿透（跨基金合并）
    - 重仓股穿透（跨基金合并相同股票）
    - 管理人集中度分析
    """

    # 基金类型 → 默认资产结构估算
    _TYPE_DEFAULTS: dict[str, dict[str, float]] = {
        "股票型": {"权益": 0.90, "固收": 0.02, "现金": 0.08},
        "混合型": {"权益": 0.65, "固收": 0.15, "现金": 0.20},
        "债券型": {"权益": 0.05, "固收": 0.85, "现金": 0.10},
        "指数型": {"权益": 0.95, "固收": 0.01, "现金": 0.04},
        "QDII": {"权益": 0.85, "固收": 0.05, "现金": 0.10},
        "货币型": {"权益": 0.00, "固收": 0.05, "现金": 0.95},
        "FOF": {"权益": 0.60, "固收": 0.20, "现金": 0.20},
    }

    def __init__(self, data_manager=None):
        from fund_cli.core.data_manager import get_data_manager

        self._dm = data_manager or get_data_manager()

    def asset_allocation_lookthrough(
        self,
        fund_codes: list[str],
        market_values: dict[str, float],
    ) -> dict[str, float]:
        """
        大类资产穿透：按市值加权汇总

        Args:
            fund_codes: 基金代码列表
            market_values: {基金代码: 市值}

        Returns:
            {'权益': 0.65, '固收': 0.20, '商品': 0.0, '现金': 0.10, '其他': 0.05}
        """
        total_mv = sum(market_values.values())
        if total_mv == 0:
            return {"权益": 0, "固收": 0, "商品": 0, "现金": 0, "其他": 0}

        # 预加载基金信息（消除 N+1）
        fund_info_map = self._dm.batch_get_fund_info(fund_codes)

        allocation: dict[str, float] = {"权益": 0, "固收": 0, "商品": 0, "现金": 0, "其他": 0}

        for code in fund_codes:
            weight = market_values.get(code, 0) / total_mv
            if weight == 0:
                continue

            try:
                info = fund_info_map.get(code)
                fund_type = info.get("type", "") if info else ""
                structure = self._get_fund_asset_structure(code, fund_type)
            except Exception as e:
                logger.warning(f"获取基金 {code} 资产结构失败: {e}")
                fund_type = ""
                structure = self._estimate_asset_structure(fund_type)

            for asset_class, ratio in structure.items():
                if asset_class in allocation:
                    allocation[asset_class] += weight * ratio

        return {k: round(v, 4) for k, v in allocation.items()}

    def country_lookthrough(
        self,
        fund_codes: list[str],
        market_values: dict[str, float],
        fund_types: dict[str, str] | None = None,
    ) -> dict[str, float]:
        """
        国家/地区穿透

        Args:
            fund_codes: 基金代码列表
            market_values: {基金代码: 市值}
            fund_types: {基金代码: 类型}（可选，自动推断）

        Returns:
            {'国内': 0.70, '海外': 0.30}
        """
        total_mv = sum(market_values.values())
        if total_mv == 0:
            return {"国内": 0, "海外": 0}

        # 预加载基金信息（消除 N+1）
        fund_info_map = self._dm.batch_get_fund_info(fund_codes)

        domestic_ratio = 0.0
        for code in fund_codes:
            weight = market_values.get(code, 0) / total_mv
            if weight == 0:
                continue

            ftype = (fund_types or {}).get(code, "")
            if ftype == "":
                try:
                    info = fund_info_map.get(code)
                    ftype = info.get("type", "") if info else ""
                except Exception:
                    pass

            is_qdii = "QDII" in ftype.upper() or "海外" in ftype
            domestic_ratio += weight * (0.0 if is_qdii else 1.0)

        return {"国内": round(domestic_ratio, 4), "海外": round(1 - domestic_ratio, 4)}

    def domestic_industry_lookthrough(
        self,
        fund_codes: list[str],
        market_values: dict[str, float],
    ) -> dict[str, float]:
        """
        国内基金行业穿透

        Args:
            fund_codes: 基金代码列表
            market_values: {基金代码: 市值}

        Returns:
            {'医药生物': 0.15, '电子': 0.12, ...}
        """
        total_mv = sum(market_values.values())
        if total_mv == 0:
            return {}

        industry_exposure: dict[str, float] = {}

        for code in fund_codes:
            weight = market_values.get(code, 0) / total_mv
            if weight == 0:
                continue

            try:
                industry_df = self._dm.get_fund_industry_allocation(code)
                if industry_df is None or (isinstance(industry_df, pd.DataFrame) and industry_df.empty):
                    continue

                # 处理 DataFrame 格式
                if isinstance(industry_df, pd.DataFrame):
                    for _, row in industry_df.iterrows():
                        industry = row.get("industry", row.get("行业类别", ""))
                        ratio = row.get("weight", row.get("占净值比例", 0))
                        if isinstance(ratio, str):
                            ratio = float(ratio.replace("%", ""))
                        ratio = float(ratio)
                        # 如果 > 1，说明是百分比格式，需要除以100
                        if ratio > 1:
                            ratio = ratio / 100
                        industry_exposure[industry] = industry_exposure.get(industry, 0) + weight * ratio
                elif isinstance(industry_df, list):
                    for item in industry_df:
                        industry = item.get("行业", item.get("industry", ""))
                        ratio = item.get("占比", item.get("weight", 0))
                        industry_exposure[industry] = industry_exposure.get(industry, 0) + weight * float(ratio)
            except Exception as e:
                logger.warning(f"获取基金 {code} 行业分布失败: {e}")

        # 合并相似行业名（如"信息技术"和"信息传输、软件和信息技术服务业"）
        merged_industry = {}
        # 行业名映射表：短名 → 标准名
        INDUSTRY_ALIASES = {
            "信息技术": "信息技术",
            "信息传输、软件和信息技术服务业": "信息技术",
            "科技": "信息技术",
            "通讯": "通信",
            "通讯业务": "通信",
            "电信服务": "通信",
            "非必需消费品": "可选消费",
            "消费者非必需品": "可选消费",
            "非日常生活消费品": "可选消费",
            "非必须消费品": "可选消费",
            "必须消费品": "必选消费",
            "消费者常用品": "必选消费",
            "日常消费品": "必选消费",
            "必需消费品": "必选消费",
            "材料": "材料",
            "基础材料": "材料",
            "原材料": "材料",
            "金融": "金融",
            "金融业": "金融",
            "保健": "医疗保健",
            "医疗保健": "医疗保健",
            "制造业": "工业",
            "工业": "工业",
            "采矿业": "采矿业",
            "能源": "能源",
            "房地产": "房地产",
            "公用事业": "公用事业",
            "交通运输、仓储和邮政业": "交通运输",
        }

        for industry, ratio in industry_exposure.items():
            std_name = INDUSTRY_ALIASES.get(industry, industry)
            merged_industry[std_name] = merged_industry.get(std_name, 0) + ratio

        # 归一化：行业合计可能超过100%（因层级分类），归一化到100%
        total = sum(merged_industry.values())
        if total > 0:
            merged_industry = {k: v / total for k, v in merged_industry.items()}

        return dict(sorted(merged_industry.items(), key=lambda x: x[1], reverse=True))

    def stock_lookthrough(
        self,
        fund_codes: list[str],
        market_values: dict[str, float],
        top_n: int = 10,
    ) -> list[dict[str, Any]]:
        """
        重仓股穿透：跨基金合并相同股票

        Args:
            fund_codes: 基金代码列表
            market_values: {基金代码: 市值}
            top_n: 返回前N大重仓股

        Returns:
            [{'股票名称': str, '合并占比': float, '来源基金': list[str]}]
        """
        total_mv = sum(market_values.values())
        if total_mv == 0:
            return []

        stock_exposure: dict[str, dict[str, Any]] = {}

        for code in fund_codes:
            weight = market_values.get(code, 0) / total_mv
            if weight == 0:
                continue

            try:
                holdings = self._dm.get_fund_holdings(code, top_n=top_n)
                if holdings is None or (isinstance(holdings, pd.DataFrame) and holdings.empty):
                    continue

                # 处理 DataFrame 格式
                if isinstance(holdings, pd.DataFrame):
                    for _, row in holdings.iterrows():
                        name = row.get("stock_name", row.get("股票名称", ""))
                        ratio = row.get("weight", row.get("占净值比", 0))
                        if isinstance(ratio, str):
                            ratio = float(ratio.replace("%", ""))
                        ratio = float(ratio) / 100 if float(ratio) > 1 else float(ratio)

                        if name not in stock_exposure:
                            stock_exposure[name] = {"合并占比": 0.0, "来源基金": []}
                        stock_exposure[name]["合并占比"] += weight * ratio
                        # 去重：同一基金只添加一次
                        if code not in stock_exposure[name]["来源基金"]:
                            stock_exposure[name]["来源基金"].append(code)
                elif isinstance(holdings, list):
                    for stock in holdings:
                        name = stock.get("股票名称", stock.get("stock_name", ""))
                        ratio = float(stock.get("占净值比", stock.get("weight", 0)))

                        if name not in stock_exposure:
                            stock_exposure[name] = {"合并占比": 0.0, "来源基金": []}
                        stock_exposure[name]["合并占比"] += weight * ratio
                        if code not in stock_exposure[name]["来源基金"]:
                            stock_exposure[name]["来源基金"].append(code)
            except Exception as e:
                logger.warning(f"获取基金 {code} 持仓失败: {e}")

        sorted_stocks = sorted(stock_exposure.items(), key=lambda x: x[1]["合并占比"], reverse=True)

        # 合并中英文同名股票（如"苹果"和"APPLE INC"）
        # 常见中英文股票名映射
        STOCK_NAME_ALIASES = {
            "苹果": "APPLE",
            "微软": "MICROSOFT",
            "亚马逊": "AMAZON",
            "英伟达": "NVIDIA",
            "谷歌": "GOOGLE",
            "特斯拉": "TESLA",
            "脸书": "META",
            "阿里巴巴": "ALIBABA",
            "腾讯": "TENCENT",
            "贵州茅台": "MOUTAI",
        }

        merged_stocks = []
        seen_names = {}  # 标准化名 → 索引
        for name, data in sorted_stocks:
            # 尝试匹配中英文别名
            std_name = STOCK_NAME_ALIASES.get(name, "")
            if not std_name:
                std_name = name.upper().replace(" ", "").replace(".", "").replace(",", "").replace("-", "")
            # 反向匹配：检查标准化名是否包含某个英文别名
            for _cn, en in STOCK_NAME_ALIASES.items():
                if en in std_name:
                    std_name = en
                    break

            if std_name in seen_names:
                idx = seen_names[std_name]
                merged_stocks[idx]["合并占比"] += data["合并占比"]
                merged_stocks[idx]["来源基金"] = list(set(merged_stocks[idx]["来源基金"] + data["来源基金"]))
            else:
                seen_names[std_name] = len(merged_stocks)
                merged_stocks.append({"股票名称": name, "合并占比": data["合并占比"], "来源基金": data["来源基金"]})

        merged_stocks.sort(key=lambda x: x["合并占比"], reverse=True)
        return merged_stocks[:top_n]

    def manager_lookthrough(
        self,
        fund_codes: list[str],
        market_values: dict[str, float],
    ) -> list[dict[str, Any]]:
        """
        基金经理穿透

        Returns:
            [{'经理姓名': str, '管理基金数': int, '合计权重': float}]
        """
        total_mv = sum(market_values.values())
        if total_mv == 0:
            return []

        # 预加载基金信息（消除 N+1）
        fund_info_map = self._dm.batch_get_fund_info(fund_codes)

        manager_exposure: dict[str, dict[str, Any]] = {}

        for code in fund_codes:
            weight = market_values.get(code, 0) / total_mv
            if weight == 0:
                continue

            try:
                info = fund_info_map.get(code)
                if info is None:
                    continue
                manager_name = info.get("manager", info.get("基金经理", ""))
                if not manager_name:
                    continue

                if manager_name not in manager_exposure:
                    manager_exposure[manager_name] = {"管理基金数": 0, "合计权重": 0.0}
                manager_exposure[manager_name]["管理基金数"] += 1
                manager_exposure[manager_name]["合计权重"] += weight
            except Exception as e:
                logger.warning(f"获取基金 {code} 经理信息失败: {e}")

        return [
            {"经理姓名": name, **data}
            for name, data in sorted(
                manager_exposure.items(), key=lambda x: x[1]["合计权重"], reverse=True
            )
        ]

    def _get_fund_asset_structure(self, code: str, fund_type: str) -> dict[str, float]:
        """获取基金资产结构"""
        try:
            holdings = self._dm.get_fund_holdings(code, top_n=10)
            if holdings and isinstance(holdings, list):
                stock_ratio = 0.0
                bond_ratio = 0.0
                for h in holdings:
                    h_type = h.get("类型", h.get("type", ""))
                    ratio = float(h.get("占净值比", h.get("proportion", 0)))
                    if "股票" in str(h_type):
                        stock_ratio += ratio
                    elif "债券" in str(h_type):
                        bond_ratio += ratio

                if stock_ratio > 0 or bond_ratio > 0:
                    cash_ratio = max(0, 1 - stock_ratio - bond_ratio)
                    return {"权益": stock_ratio, "固收": bond_ratio, "现金": cash_ratio, "商品": 0, "其他": 0}
        except Exception:
            pass

        return self._estimate_asset_structure(fund_type)

    def _estimate_asset_structure(self, fund_type: str) -> dict[str, float]:
        """根据基金类型估算资产结构"""
        for key, defaults in self._TYPE_DEFAULTS.items():
            if key in fund_type:
                return dict(defaults)
        return {"权益": 0.5, "固收": 0.3, "现金": 0.2, "商品": 0, "其他": 0}
