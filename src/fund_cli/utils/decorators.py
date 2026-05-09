"""
装饰器模块

提供常用装饰器。
"""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any


def timer(func: Callable) -> Callable:
    """
    计时装饰器

    记录函数执行时间。
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"[{func.__name__}] 执行时间: {elapsed:.2f}秒")
        return result

    return wrapper


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    重试装饰器

    Args:
        max_attempts: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 需要重试的异常类型
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)

            if last_exception is not None:
                raise last_exception
            raise RuntimeError(f"{func.__name__} 在 {max_attempts} 次尝试后仍失败")

        return wrapper

    return decorator


def deprecated(message: str = "") -> Callable:
    """
    废弃警告装饰器

    Args:
        message: 废弃说明
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import warnings

            warnings.warn(
                f"{func.__name__} 已废弃。{message}",
                DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator
