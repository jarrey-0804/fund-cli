"""
交易记录解析器

解析用户基金交易记录Excel文件，标准化输出可用于持仓计算的DataFrame。
支持的业务类型：申购、赎回、分红、转换、定投、强行调增等。
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Excel中可能的列名映射（兼容不同导出格式）
_COLUMN_MAPPING: dict[str, list[str]] = {
    "确认结果": ["确认结果"],
    "业务名称": ["业务名称"],
    "基金代码": ["基金代码"],
    "基金名称": ["基金名称"],
    "确认金额": ["确认金额"],
    "确认份额": ["确认份额"],
    "确认日期": ["确认日期"],
    "手续费": ["手续费"],
    "目标基金代码": ["目标基金代码"],
    "目标基金名称": ["目标基金名称"],
    "目标产品确认份额": ["目标产品确认份额"],
    "默认分红方式": ["默认分红方式"],
    "分红基数": ["分红基数"],
    "基金类型": ["基金类型"],
}

# 业务类型 → 标准化分类
_BUSINESS_TYPE_MAP: dict[str, str] = {
    "申购": "purchase",
    "认购": "purchase",
    "定期定额申购": "purchase",
    "赎回": "redemption",
    "强行赎回": "redemption",
    "T+0快速赎回": "redemption",
    "分红": "dividend",
    "基金转换": "transfer",
    "强行调增": "adjustment",
    "设置分红方式": "info_only",
    "定投协议开通": "info_only",
}


def _parse_amount(val: str | float | int | None) -> float:
    """清洗金额/份额字段：去除逗号，转为float"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return 0.0
    s = str(val).replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_date_int(val: int | float | None) -> Optional[date]:
    """
    将整数日期（如 20190102）转为 date 对象。
    如果是Excel序列号（< 100000），则按Excel日期系统转换。
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    v = int(val)
    if v < 100000:
        # 可能是Excel序列号（1900日期系统）
        from datetime import timedelta

        base = datetime(1899, 12, 30)
        return (base + timedelta(days=v)).date()
    # 整数格式 YYYYMMDD
    s = str(v)
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except ValueError:
        logger.warning(f"无法解析日期: {val}")
        return None


def _normalize_fund_code(code: int | float | str) -> str:
    """
    标准化基金代码为6位字符串。
    Excel中可能存储为 380.0 → "000380"
    """
    s = str(int(float(code))) if isinstance(code, (int, float)) else str(code).strip()
    return s.zfill(6)


class TransactionParser:
    """
    交易记录解析器

    功能：
    - 读取Excel交易记录文件
    - 标准化列名和数据格式
    - 分类业务类型
    - 过滤无效记录（如"设置分红方式"等仅信息类记录）
    """

    def parse_excel(self, file_path: str) -> pd.DataFrame:
        """
        解析交易记录Excel文件

        Args:
            file_path: Excel文件路径

        Returns:
            标准化后的交易记录DataFrame，包含以下列：
            - fund_code: 基金代码（6位字符串）
            - fund_name: 基金名称
            - business_type: 业务类型（标准化英文）
            - business_name: 业务名称（原始中文）
            - confirmed_amount: 确认金额（float）
            - confirmed_shares: 确认份额（float）
            - fee: 手续费（float）
            - confirm_date: 确认日期（date）
            - target_fund_code: 目标基金代码（转换时）
            - target_fund_name: 目标基金名称（转换时）
            - target_shares: 目标产品确认份额（转换时）
            - dividend_method: 分红方式
            - fund_type: 基金类型
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"交易记录文件不存在: {file_path}")

        df = pd.read_excel(file_path)

        # 只保留确认成功的记录
        if "确认结果" in df.columns:
            df = df[df["确认结果"] == "确认成功"].copy()
            logger.info(f"确认成功记录: {len(df)} 条")

        # 标准化业务类型
        df["business_type"] = df["业务名称"].map(_BUSINESS_TYPE_MAP)
        unknown = df[df["business_type"].isna()]["业务名称"].unique()
        if len(unknown) > 0:
            logger.warning(f"未知业务类型: {unknown}")

        # 过滤仅信息类记录
        df = df[df["business_type"] != "info_only"].copy()
        logger.info(f"过滤后有效交易记录: {len(df)} 条")

        # 映射标准列名
        df["fund_name"] = df["基金名称"].astype(str) if "基金名称" in df.columns else ""
        df["business_name"] = df["业务名称"].astype(str) if "业务名称" in df.columns else ""

        # 清洗数值字段
        df["confirmed_amount"] = df["确认金额"].apply(_parse_amount)
        df["confirmed_shares"] = df["确认份额"].apply(_parse_amount)
        df["fee"] = df["手续费"].apply(_parse_amount) if "手续费" in df.columns else 0.0

        # 标准化基金代码
        df["fund_code"] = df["基金代码"].apply(_normalize_fund_code)

        # 解析日期
        df["confirm_date"] = df["确认日期"].apply(_parse_date_int)

        # 目标基金（转换业务）
        df["target_fund_code"] = (
            df["目标基金代码"].apply(lambda x: _normalize_fund_code(x) if pd.notna(x) else "")
            if "目标基金代码" in df.columns
            else ""
        )
        df["target_fund_name"] = (
            df["目标基金名称"].fillna("").astype(str) if "目标基金名称" in df.columns else ""
        )
        df["target_shares"] = (
            df["目标产品确认份额"].apply(_parse_amount) if "目标产品确认份额" in df.columns else 0.0
        )

        # 分红方式
        df["dividend_method"] = (
            df["默认分红方式"].fillna("").astype(str) if "默认分红方式" in df.columns else ""
        )

        # 基金类型
        df["fund_type"] = (
            df["基金类型"].fillna("").astype(str) if "基金类型" in df.columns else ""
        )

        # 按日期排序
        df = df.sort_values("confirm_date").reset_index(drop=True)

        # 输出统计
        self._log_stats(df)

        return df

    def _log_stats(self, df: pd.DataFrame) -> None:
        """输出解析统计信息"""
        stats = df["business_type"].value_counts()
        logger.info("业务类型分布:")
        for bt, count in stats.items():
            logger.info(f"  {bt}: {count}")

        fund_count = df["fund_code"].nunique()
        logger.info(f"涉及基金数量: {fund_count}")

        date_range = f"{df['confirm_date'].min()} ~ {df['confirm_date'].max()}"
        logger.info(f"交易日期范围: {date_range}")
