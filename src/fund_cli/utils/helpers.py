"""
辅助函数模块

提供通用辅助函数。
"""

from datetime import date, datetime


def format_percentage(value: float | None, decimal: int = 2) -> str:
    """
    格式化百分比显示

    Args:
        value: 数值
        decimal: 小数位数

    Returns:
        格式化后的字符串
    """
    if value is None:
        return "-"

    return f"{value:.{decimal}f}%"


def format_currency(
    value: float | None,
    unit: str = "亿",
    decimal: int = 2,
) -> str:
    """
    格式化货币显示

    Args:
        value: 数值
        unit: 单位
        decimal: 小数位数

    Returns:
        格式化后的字符串
    """
    if value is None:
        return "-"

    return f"{value:.{decimal}f}{unit}"


def format_date(value: date | datetime | None, fmt: str = "%Y-%m-%d") -> str:
    """
    格式化日期显示

    Args:
        value: 日期值
        fmt: 格式字符串

    Returns:
        格式化后的字符串
    """
    if value is None:
        return "-"

    if isinstance(value, datetime):
        return value.strftime(fmt)
    elif isinstance(value, date):
        return value.strftime(fmt)

    return str(value)


def format_number(value: float | None, decimal: int = 2) -> str:
    """
    格式化数字显示

    Args:
        value: 数值
        decimal: 小数位数

    Returns:
        格式化后的字符串
    """
    if value is None:
        return "-"

    return f"{value:.{decimal}f}"


def safe_divide(
    numerator: float,
    denominator: float,
    default: float = 0.0,
) -> float:
    """
    安全除法

    Args:
        numerator: 分子
        denominator: 分母
        default: 默认值（分母为0时）

    Returns:
        计算结果
    """
    if denominator == 0:
        return default
    return numerator / denominator


def truncate_string(s: str, max_length: int = 20, suffix: str = "...") -> str:
    """
    截断字符串

    Args:
        s: 原字符串
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的字符串
    """
    if not s:
        return ""

    if len(s) <= max_length:
        return s

    return s[: max_length - len(suffix)] + suffix
