"""
幂等性工具测试.

验证请求去重和幂等执行功能。
"""

import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fund_cli.utils.idempotency import (
    IdempotencyKey,
    RequestLock,
    IdempotentExecutor,
    get_idempotent_executor,
    idempotent,
)


class TestIdempotencyKey(unittest.TestCase):
    """测试幂等性键生成器."""

    def test_generate_same_args(self):
        """测试相同参数生成相同键."""
        key1 = IdempotencyKey.generate("arg1", "arg2", kwarg1="value1")
        key2 = IdempotencyKey.generate("arg1", "arg2", kwarg1="value1")
        self.assertEqual(key1, key2)

    def test_generate_different_args(self):
        """测试不同参数生成不同键."""
        key1 = IdempotencyKey.generate("arg1", "arg2")
        key2 = IdempotencyKey.generate("arg1", "arg3")
        self.assertNotEqual(key1, key2)

    def test_generate_length(self):
        """测试生成的键长度."""
        key = IdempotencyKey.generate("test")
        self.assertEqual(len(key), 16)


class TestRequestLock(unittest.TestCase):
    """测试请求锁."""

    def setUp(self):
        """设置测试环境."""
        self.temp_dir = TemporaryDirectory()
        self.lock = RequestLock(cache_dir=self.temp_dir.name)

    def tearDown(self):
        """清理测试环境."""
        self.temp_dir.cleanup()

    def test_acquire_and_release(self):
        """测试获取和释放锁."""
        key = "test_lock"

        # 获取锁
        result = self.lock.acquire(key, timeout=1.0)
        self.assertTrue(result)

        # 检查锁定状态
        self.assertTrue(self.lock.is_locked(key))

        # 释放锁
        self.lock.release(key)
        self.assertFalse(self.lock.is_locked(key))

    def test_acquire_already_locked(self):
        """测试已锁定时的获取."""
        key = "test_lock"

        # 第一次获取锁
        result1 = self.lock.acquire(key, timeout=1.0)
        self.assertTrue(result1)

        # 第二次获取锁（应失败）
        result2 = self.lock.acquire(key, timeout=0.1)
        self.assertFalse(result2)

        # 清理
        self.lock.release(key)

    def test_acquire_timeout(self):
        """测试锁超时."""
        key = "test_lock_timeout"

        # 获取锁（短超时）
        result = self.lock.acquire(key, timeout=0.5)
        self.assertTrue(result)

        # 释放锁
        self.lock.release(key)

        # 再次获取（应成功）
        result2 = self.lock.acquire(key, timeout=0.5)
        self.assertTrue(result2)

        self.lock.release(key)


class TestIdempotentExecutor(unittest.TestCase):
    """测试幂等执行器."""

    def setUp(self):
        """设置测试环境."""
        self.temp_dir = TemporaryDirectory()
        self.executor = IdempotentExecutor(cache_dir=self.temp_dir.name)

    def tearDown(self):
        """清理测试环境."""
        self.temp_dir.cleanup()

    def test_execute_caches_result(self):
        """测试执行结果缓存."""
        call_count = [0]

        def test_func(x):
            call_count[0] += 1
            return x * 2

        # 第一次执行
        result1 = self.executor.execute(test_func, 5, cache_ttl=3600)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count[0], 1)

        # 第二次执行（应使用缓存）
        result2 = self.executor.execute(test_func, 5, cache_ttl=3600)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count[0], 1)  # 不应增加

    def test_execute_different_args(self):
        """测试不同参数分别缓存."""
        call_count = [0]

        def test_func(x):
            call_count[0] += 1
            return x * 2

        result1 = self.executor.execute(test_func, 5, cache_ttl=3600)
        result2 = self.executor.execute(test_func, 10, cache_ttl=3600)

        self.assertEqual(result1, 10)
        self.assertEqual(result2, 20)
        self.assertEqual(call_count[0], 2)

    def test_clear_cache_all(self):
        """测试清除所有缓存."""
        def test_func(x):
            return x * 2

        self.executor.execute(test_func, 5, cache_ttl=3600)
        self.executor.clear_cache()

        # 再次执行（缓存已清除）
        call_count = [0]

        def test_func2(x):
            call_count[0] += 1
            return x * 2

        self.executor.execute(test_func2, 5, cache_ttl=3600)
        self.assertEqual(call_count[0], 1)

    def test_clear_cache_by_func_name(self):
        """测试按函数名清除缓存."""
        def func1(x):
            return x * 2

        def func2(x):
            return x * 3

        # 设置不同的 __name__
        func1.__name__ = "func1"
        func2.__name__ = "func2"

        self.executor.execute(func1, 5, cache_ttl=3600)
        self.executor.execute(func2, 5, cache_ttl=3600)

        # 只清除 func1 的缓存
        self.executor.clear_cache(func_name="func1")

        # func2 的缓存应该还在
        call_count = [0]

        def func2_new(x):
            call_count[0] += 1
            return x * 3

        func2_new.__name__ = "func2"
        self.executor.execute(func2_new, 5, cache_ttl=3600)
        self.assertEqual(call_count[0], 0)  # 使用了缓存


class TestGetIdempotentExecutor(unittest.TestCase):
    """测试全局执行器获取."""

    def test_get_executor_singleton(self):
        """测试全局单例."""
        executor1 = get_idempotent_executor()
        executor2 = get_idempotent_executor()
        self.assertIs(executor1, executor2)


class TestIdempotentDecorator(unittest.TestCase):
    """测试幂等装饰器."""

    def setUp(self):
        """设置测试环境."""
        self.temp_dir = TemporaryDirectory()
        # 创建新的执行器避免单例干扰
        self.executor = IdempotentExecutor(cache_dir=self.temp_dir.name)

    def tearDown(self):
        """清理测试环境."""
        self.temp_dir.cleanup()

    def test_decorator_caches_result(self):
        """测试装饰器缓存结果."""
        # 使用唯一参数避免与其他测试冲突
        import uuid
        unique_val = int(uuid.uuid4().int % 10000)
        call_count = [0]

        @idempotent(cache_ttl=3600)
        def test_func_decorated(x):
            call_count[0] += 1
            return x * 2

        # 第一次调用
        result1 = test_func_decorated(unique_val)
        self.assertEqual(result1, unique_val * 2)
        self.assertEqual(call_count[0], 1)  # 必须执行一次

        # 第二次调用（应使用缓存）
        result2 = test_func_decorated(unique_val)
        self.assertEqual(result2, unique_val * 2)
        self.assertEqual(call_count[0], 1)  # 不应增加


if __name__ == "__main__":
    unittest.main()
