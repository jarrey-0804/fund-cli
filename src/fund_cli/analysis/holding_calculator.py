"""
持仓计算器

基于交易记录计算当前持仓，支持所有业务类型：
- 申购/定期定额申购：增加份额
- 赎回/强行赎回/T+0快速赎回：减少份额
- 分红（红利再投）：增加份额
- 分红（现金分红）：不影响份额
- 基金转换：源基金减少份额，目标基金增加份额
- 强行调增：增加份额
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class HoldingCalculator:
    """
    持仓计算器

    基于交易记录逐笔计算每只基金的持仓份额和成本。
    """

    def calculate_holdings(
        self,
        transactions: pd.DataFrame,
        min_weight_pct: float = 0.0,
    ) -> pd.DataFrame:
        """
        计算当前持仓

        Args:
            transactions: TransactionParser.parse_excel() 的输出
            min_weight_pct: 最小权重百分比阈值，低于此值的持仓将被过滤（0表示不过滤）

        Returns:
            持仓明细 DataFrame，列：
            - fund_code: 基金代码
            - fund_name: 基金名称
            - total_shares: 当前持仓份额
            - total_cost: 总成本（申购金额 - 赎回金额）
            - weight: 权重（占总市值比例）
            - fund_type: 基金类型
            - first_buy_date: 首次买入日期
            - last_transaction_date: 最后交易日期
            - transaction_count: 交易笔数
        """
        if transactions.empty:
            return pd.DataFrame()

        # 逐笔计算持仓份额
        holdings: dict[str, dict] = {}

        for _, row in transactions.iterrows():
            code = row["fund_code"]
            name = row["fund_name"]
            bt = row["business_type"]
            shares = row["confirmed_shares"]
            amount = row["confirmed_amount"]
            confirm_date = row["confirm_date"]

            if code not in holdings:
                holdings[code] = {
                    "fund_code": code,
                    "fund_name": name,
                    "total_shares": 0.0,
                    "total_cost": 0.0,
                    "fund_type": row.get("fund_type", ""),
                    "first_buy_date": None,
                    "last_transaction_date": None,
                    "transaction_count": 0,
                }

            h = holdings[code]

            if bt == "purchase":
                h["total_shares"] += shares
                h["total_cost"] += amount
            elif bt == "redemption":
                # 赎回时，按比例减少成本
                # 先计算当前每股成本
                if h["total_shares"] > shares:
                    # 避免除以接近0的数
                    if h["total_shares"] > 0.001:
                        cost_per_share = h["total_cost"] / h["total_shares"]
                    else:
                        cost_per_share = 0.0
                    h["total_cost"] -= cost_per_share * shares
                    h["total_shares"] -= shares
                else:
                    # 如果赎回份额超过当前份额，成本归零，份额清零
                    h["total_cost"] = 0.0
                    h["total_shares"] = 0.0
            elif bt == "dividend":
                # 红利再投：确认份额 > 0 表示再投资份额
                if shares > 0:
                    h["total_shares"] += shares
                # 现金分红：不影响份额
            elif bt == "transfer":
                # 源基金减少份额
                h["total_shares"] -= shares
                # 目标基金增加份额（通过 target_fund_code）
                target_code = row.get("target_fund_code", "")
                target_shares = row.get("target_shares", 0.0)
                if target_code and target_shares > 0:
                    if target_code not in holdings:
                        target_name = row.get("target_fund_name", "")
                        holdings[target_code] = {
                            "fund_code": target_code,
                            "fund_name": target_name,
                            "total_shares": 0.0,
                            "total_cost": 0.0,
                            "fund_type": row.get("fund_type", ""),
                            "first_buy_date": None,
                            "last_transaction_date": None,
                            "transaction_count": 0,
                        }
                    holdings[target_code]["total_shares"] += target_shares
            elif bt == "adjustment":
                # 强行调增：增加份额
                h["total_shares"] += shares

            # 更新日期和计数
            if confirm_date:
                if h["first_buy_date"] is None and bt in ("purchase", "adjustment"):
                    h["first_buy_date"] = confirm_date
                h["last_transaction_date"] = confirm_date
            h["transaction_count"] += 1

        # 转为DataFrame
        result = pd.DataFrame(list(holdings.values()))

        # 过滤份额 <= 0 的记录（已全部赎回），使用微小阈值避免浮点精度问题
        MIN_SHARES_THRESHOLD = 0.01
        result = result[result["total_shares"] > MIN_SHARES_THRESHOLD].copy()

        if result.empty:
            logger.warning("所有基金持仓份额为0，无有效持仓")
            return result

        # 计算权重（基于成本，后续可用净值更新为市值权重）
        total_cost = result["total_cost"].sum()
        if total_cost > 0:
            result["weight"] = result["total_cost"] / total_cost
        else:
            # 如果成本为0（如纯分红再投），按份额均分
            result["weight"] = 1.0 / len(result)

        # 按权重降序排列
        result = result.sort_values("weight", ascending=False).reset_index(drop=True)

        # 应用最小权重过滤
        if min_weight_pct > 0:
            before = len(result)
            result = result[result["weight"] >= min_weight_pct / 100.0].copy()
            # 重新归一化权重
            result["weight"] = result["weight"] / result["weight"].sum()
            after = len(result)
            if before != after:
                logger.info(f"权重过滤: {before} → {after} 只基金（阈值 {min_weight_pct}%）")

        logger.info(f"计算完成: {len(result)} 只有效持仓")
        return result

    def calculate_holdings_with_nav(
        self,
        transactions: pd.DataFrame,
        nav_dict: dict[str, float],
        min_weight_pct: float = 0.0,
    ) -> pd.DataFrame:
        """
        使用最新净值计算持仓市值和权重

        Args:
            transactions: 交易记录
            nav_dict: {基金代码: 最新净值}
            min_weight_pct: 最小权重阈值

        Returns:
            持仓明细，额外包含 market_value 和基于市值的 weight 列
        """
        holdings = self.calculate_holdings(transactions, min_weight_pct=0.0)

        if holdings.empty:
            return holdings

        # 计算市值
        holdings["nav"] = holdings["fund_code"].map(nav_dict)
        holdings["market_value"] = holdings["total_shares"] * holdings["nav"].fillna(0)

        # 过滤市值为0的（无净值数据）
        has_nav = holdings["market_value"] > 0
        no_nav = holdings[~has_nav]
        if not no_nav.empty:
            logger.warning(f"以下基金无净值数据，按成本估算: {no_nav['fund_code'].tolist()}")
            holdings.loc[~has_nav, "market_value"] = holdings.loc[~has_nav, "total_cost"]

        total_mv = holdings["market_value"].sum()
        holdings["weight"] = holdings["market_value"] / total_mv

        # 应用最小权重过滤
        if min_weight_pct > 0:
            before = len(holdings)
            holdings = holdings[holdings["weight"] >= min_weight_pct / 100.0].copy()
            holdings["weight"] = holdings["weight"] / holdings["weight"].sum()
            after = len(holdings)
            if before != after:
                logger.info(f"权重过滤: {before} → {after} 只基金（阈值 {min_weight_pct}%）")

        holdings = holdings.sort_values("weight", ascending=False).reset_index(drop=True)
        return holdings
