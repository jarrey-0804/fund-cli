"""
装饰器模块

提供常用装饰器。
"""

import functools
import logging
import random
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def timer(func: Callable) -> Callable:
    """
    计时装饰器

    记录函数执行时间。
    """

    @functools.wraps(func)
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
    backoff: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    重试装饰器，支持指数退避

    Args:
        max_attempts: 最大重试次数
        delay: 初始重试间隔（秒）
        backoff: 退避倍数
        jitter: 是否添加随机抖动
        exceptions: 需要重试的异常类型
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        actual_delay = current_delay + (
                            random.uniform(0, current_delay * 0.1) if jitter else 0
                        )
                        logger.warning(
                            "重试 %s (尝试 %d/%d), 等待 %.1fs: %s",
                            func.__name__,
                            attempt + 1,
                            max_attempts,
                            actual_delay,
                            e,
                        )
                        time.sleep(actual_delay)
                        current_delay *= backoff
            raise last_error  # type: ignore

        return wrapper

    return decorator


def deprecated(message: str = "") -> Callable:
    """
    废弃警告装饰器

    Args:
        message: 废弃说明
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
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


def validate_input(*validators):
    """输入验证装饰器"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i, validator in enumerate(validators):
                if i < len(args):
                    is_valid, msg = validator(args[i])
                    if not is_valid:
                        raise ValueError(f"参数 {i} 验证失败: {msg}")
            return func(*args, **kwargs)

        return wrapper

    return decorator
