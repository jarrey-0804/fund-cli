"""
验证器模块

提供各类数据验证功能。
"""

import re
from datetime import datetime

import pandas as pd


def validate_fund_code(fund_code: str) -> bool:
    """
    验证基金代码格式

    Args:
        fund_code: 基金代码

    Returns:
        是否有效
    """
    if not fund_code:
        return False

    # 基金代码应为6位数字
    if not re.match(r"^\d{6}$", fund_code):
        return False

    return True


def validate_date(date_str: str) -> bool:
    """
    验证日期格式和语义有效性

    Args:
        date_str: 日期字符串 (YYYY-MM-DD)

    Returns:
        是否有效
    """
    if not date_str:
        return False

    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date_str):
        return False

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return False

    return True


def validate_date_strict(date_str: str) -> tuple[bool, str]:
    """
    验证日期格式和语义有效性（带错误信息）

    Args:
        date_str: 日期字符串 (YYYY-MM-DD)

    Returns:
        (是否有效, 错误信息)
    """
    if not date_str:
        return False, "日期为空"

    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date_str):
        return False, f"日期格式错误，应为 YYYY-MM-DD: {date_str}"

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return False, f"日期不存在: {date_str}"

    return True, ""


def validate_positive_number(value: float | None) -> bool:
    """
    验证正数

    Args:
        value: 数值

    Returns:
        是否为正数
    """
    if value is None:
        return False
    return value > 0


def validate_percentage(value: float | None) -> bool:
    """
    验证百分比范围

    Args:
        value: 百分比值

    Returns:
        是否在有效范围内
    """
    if value is None:
        return False
    return -100 <= value <= 100


def validate_nav_value(value: float | None) -> tuple[bool, str]:
    """验证净值合理性 (0 < nav <= 10000)"""
    if value is None:
        return False, "净值为空"
    if value <= 0:
        return False, f"净值必须大于0，当前值: {value}"
    if value > 10000:
        return False, f"净值异常偏高: {value}"
    return True, ""


def validate_daily_return(value: float | None) -> tuple[bool, str]:
    """验证日收益率合理性 (-20% <= return <= 20%)"""
    if value is None:
        return True, ""  # None is acceptable (missing data)
    if value < -0.2 or value > 0.2:
        return False, f"日收益率超出合理范围 [-20%, 20%]: {value:.2%}"
    return True, ""


def validate_data_min_rows(df: pd.DataFrame, min_rows: int = 30) -> tuple[bool, str]:
    """验证DataFrame最少行数"""
    if df is None or df.empty:
        return False, "数据为空"
    if len(df) < min_rows:
        return False, f"数据量不足: {len(df)} 行，最低要求 {min_rows} 行"
    return True, ""
