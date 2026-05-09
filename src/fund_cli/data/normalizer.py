"""
数据标准化层.

统一不同数据源的输出格式，确保接口一致性。
"""

from datetime import date, datetime
from functools import lru_cache
from typing import Any

import pandas as pd


class DataNormalizer:
    """
    数据标准化器.

    功能：
    - 统一字段命名（snake_case）
    - 统一日期格式（YYYY-MM-DD）
    - 统一数据类型
    - 缺失值处理
    """

    # 字段映射规则
    FIELD_MAPPINGS = {
        # 基金代码
        "ts_code": "fund_code",
        "symbol": "fund_code",
        "code": "fund_code",
        # 基金名称
        "name": "fund_name",
        "fund_name": "fund_name",
        # 净值相关
        "end_date": "nav_date",
        "trade_date": "nav_date",
        "unit_nav": "unit_nav",
        "accum_nav": "accumulated_nav",
        # 持仓相关
        "stock_code": "stock_code",
        "stock_name": "stock_name",
        "vol": "volume",
        "volume": "volume",
        "proportions": "proportion",
        "proportion": "proportion",
    }

    # 日期字段
    DATE_FIELDS = [
        "nav_date",
        "start_date",
        "end_date",
        "found_date",
        "list_date",
        "establish_date",
    ]

    @classmethod
    def normalize_fund_info(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        标准化基金信息.

        Args:
            data: 原始基金信息

        Returns:
            标准化后的基金信息
        """
        result = {}

        for key, value in data.items():
            # 字段映射
            normalized_key = cls.FIELD_MAPPINGS.get(key, key)
            result[normalized_key] = value

        # 标准化日期格式
        for date_field in cls.DATE_FIELDS:
            if date_field in result and result[date_field]:
                result[date_field] = cls.normalize_date(result[date_field])

        # 标准化基金代码格式
        if "fund_code" in result and result["fund_code"]:
            result["fund_code"] = cls.normalize_fund_code(result["fund_code"])

        return result

    @classmethod
    def normalize_nav_data(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化净值数据.

        Args:
            df: 原始净值数据DataFrame

        Returns:
            标准化后的DataFrame
        """
        result = df.copy()

        # 重命名列
        rename_columns = {}
        for col in result.columns:
            if col in cls.FIELD_MAPPINGS:
                rename_columns[col] = cls.FIELD_MAPPINGS[col]
        result = result.rename(columns=rename_columns)

        # 确保必要列存在
        required_cols = ["fund_code", "nav_date", "unit_nav"]
        for col in required_cols:
            if col not in result.columns:
                raise ValueError(f"缺少必要列: {col}")

        # 标准化日期格式
        if "nav_date" in result.columns:
            result["nav_date"] = pd.to_datetime(result["nav_date"], errors="coerce").dt.strftime("%Y-%m-%d")

        # 标准化基金代码
        if "fund_code" in result.columns:
            result["fund_code"] = result["fund_code"].apply(cls.normalize_fund_code)

        # 确保数值类型
        numeric_cols = ["unit_nav", "accumulated_nav", "daily_return", "volume", "proportion"]
        for col in numeric_cols:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors="coerce")

        # 按日期排序
        result = result.sort_values("nav_date").reset_index(drop=True)

        return result

    @classmethod
    def normalize_fund_code(cls, code: str) -> str:
        """
        标准化基金代码.

        移除后缀（如.OF、.SH等），只保留纯数字代码

        Args:
            code: 原始基金代码

        Returns:
            标准化后的基金代码
        """
        if not code:
            return code

        # 移除常见后缀
        for suffix in [".OF", ".SH", ".SZ", ".BJ"]:
            code = code.replace(suffix, "")

        return code

    @staticmethod
    @lru_cache(maxsize=1024)
    def normalize_fund_code_cached(code: str) -> str:
        """带缓存的基金代码标准化."""
        return DataNormalizer.normalize_fund_code(code)

    @staticmethod
    @lru_cache(maxsize=1024)
    def normalize_date_cached(date_value: Any) -> str | None:
        """带缓存的日期标准化."""
        return DataNormalizer.normalize_date(date_value)

    @classmethod
    def normalize_date(cls, date_value: Any) -> str | None:
        """
        标准化日期格式.

        Args:
            date_value: 原始日期值

        Returns:
            YYYY-MM-DD格式的日期字符串
        """
        if not date_value:
            return None

        if isinstance(date_value, date):
            return date_value.strftime("%Y-%m-%d")

        if isinstance(date_value, datetime):
            return date_value.strftime("%Y-%m-%d")

        if isinstance(date_value, str):
            # 尝试多种格式
            formats = [
                "%Y%m%d",      # 20240101
                "%Y-%m-%d",    # 2024-01-01
                "%Y/%m/%d",    # 2024/01/01
                "%Y.%m.%d",    # 2024.01.01
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_value, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue

        return str(date_value)

    @classmethod
    def normalize_fund_holdings(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化基金持仓数据.

        Args:
            df: 原始持仓数据

        Returns:
            标准化后的DataFrame
        """
        result = df.copy()

        # 重命名列
        rename_columns = {}
        for col in result.columns:
            if col in cls.FIELD_MAPPINGS:
                rename_columns[col] = cls.FIELD_MAPPINGS[col]
        result = result.rename(columns=rename_columns)

        # 确保必要列存在
        required_cols = ["fund_code", "stock_code", "stock_name"]
        for col in required_cols:
            if col not in result.columns:
                raise ValueError(f"缺少必要列: {col}")

        # 标准化基金代码
        if "fund_code" in result.columns:
            result["fund_code"] = result["fund_code"].apply(cls.normalize_fund_code)

        # 确保数值类型
        if "volume" in result.columns:
            result["volume"] = pd.to_numeric(result["volume"], errors="coerce")
        if "proportion" in result.columns:
            result["proportion"] = pd.to_numeric(result["proportion"], errors="coerce")

        return result

    @classmethod
    def normalize_fund_manager(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化基金经理数据.

        Args:
            df: 原始基金经理数据

        Returns:
            标准化后的DataFrame
        """
        result = df.copy()

        # 标准化日期
        for date_field in ["start_date", "end_date"]:
            if date_field in result.columns:
                result[date_field] = result[date_field].apply(cls.normalize_date)

        return result

    @classmethod
    def normalize_asset_allocation(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        标准化资产配置数据.

        Args:
            data: 原始资产配置数据

        Returns:
            标准化后的字典
        """
        stock_ratio: float = float(data.get("stock_ratio", 0) or 0)
        bond_ratio: float = float(data.get("bond_ratio", 0) or 0)
        cash_ratio: float = float(data.get("cash_ratio", 0) or 0)
        total_asset: float = float(data.get("total_asset", 0) or 0)

        result = {
            "fund_code": cls.normalize_fund_code(data.get("fund_code", "")),
            "date": cls.normalize_date(data.get("date", "")),
            "stock_ratio": stock_ratio,
            "bond_ratio": bond_ratio,
            "cash_ratio": cash_ratio,
            "total_asset": total_asset,
        }

        # 验证比例总和（应该接近100%）
        total_ratio = stock_ratio + bond_ratio + cash_ratio
        if total_ratio > 0:
            # 归一化
            result["stock_ratio"] = round(stock_ratio / total_ratio * 100, 2)
            result["bond_ratio"] = round(bond_ratio / total_ratio * 100, 2)
            result["cash_ratio"] = round(cash_ratio / total_ratio * 100, 2)

        return result
