"""
验证器模块

提供各类数据验证功能。
"""

import re


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
    验证日期格式

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

    return True


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
