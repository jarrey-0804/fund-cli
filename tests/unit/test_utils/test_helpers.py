"""
单元测试 - 工具模块
"""

from datetime import date, datetime

import pytest

from fund_cli.utils.decorators import deprecated, retry, timer
from fund_cli.utils.helpers import (
    format_currency,
    format_date,
    format_number,
    format_percentage,
    safe_divide,
    truncate_string,
)


class TestFormatPercentage:
    """百分比格式化测试"""

    def test_positive(self):
        assert format_percentage(12.345) == "12.35%"

    def test_negative(self):
        assert format_percentage(-5.67) == "-5.67%"

    def test_none(self):
        assert format_percentage(None) == "-"

    def test_custom_decimal(self):
        assert format_percentage(12.3, decimal=1) == "12.3%"


class TestFormatCurrency:
    """货币格式化测试"""

    def test_normal(self):
        assert format_currency(100.5) == "100.50亿"

    def test_none(self):
        assert format_currency(None) == "-"

    def test_custom_unit(self):
        assert format_currency(50.0, unit="万") == "50.00万"


class TestFormatDate:
    """日期格式化测试"""

    def test_date(self):
        assert format_date(date(2024, 1, 15)) == "2024-01-15"

    def test_datetime(self):
        assert format_date(datetime(2024, 1, 15, 10, 30)) == "2024-01-15"

    def test_none(self):
        assert format_date(None) == "-"


class TestFormatNumber:
    """数字格式化测试"""

    def test_normal(self):
        assert format_number(3.14159) == "3.14"

    def test_none(self):
        assert format_number(None) == "-"


class TestSafeDivide:
    """安全除法测试"""

    def test_normal(self):
        assert safe_divide(10, 3) == pytest.approx(3.333, abs=0.01)

    def test_zero_divisor(self):
        assert safe_divide(10, 0) == 0.0

    def test_custom_default(self):
        assert safe_divide(10, 0, default=-1) == -1


class TestTruncateString:
    """字符串截断测试"""

    def test_short_string(self):
        assert truncate_string("hello") == "hello"

    def test_long_string(self):
        result = truncate_string("a" * 30, max_length=10)
        assert len(result) == 10

    def test_empty_string(self):
        assert truncate_string("") == ""


class TestDecorators:
    """装饰器测试"""

    def test_timer(self):
        @timer
        def slow_func():
            return 42

        result = slow_func()
        assert result == 42

    def test_retry_success(self):
        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("not ready")
            return "ok"

        result = flaky_func()
        assert result == "ok"
        assert call_count == 2

    def test_retry_exhausted(self):
        @retry(max_attempts=2, delay=0.01)
        def always_fail():
            raise ValueError("always fails")

        with pytest.raises(ValueError):
            always_fail()

    def test_deprecated(self):
        @deprecated("use new_func instead")
        def old_func():
            return 42

        with pytest.warns(DeprecationWarning):
            result = old_func()
        assert result == 42
