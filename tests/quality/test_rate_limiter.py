"""
限速器测试.

验证全局限速器功能，防止数据源被封禁。
"""

import time
import unittest
from unittest.mock import MagicMock, patch

import pytest

from fund_cli.core.rate_limiter import RateLimiter, TokenBucket, get_rate_limiter


class TestTokenBucket(unittest.TestCase):
    """测试令牌桶."""

    def test_initial_tokens(self):
        """测试初始令牌数."""
        bucket = TokenBucket(rate=10.0, capacity=5)
        self.assertEqual(bucket.tokens, 5)

    def test_acquire_success(self):
        """测试成功获取令牌."""
        bucket = TokenBucket(rate=10.0, capacity=5)
        result = bucket.acquire(tokens=1, blocking=False)
        self.assertTrue(result)
        # 令牌数可能因时间流逝而略有变化，使用近似比较
        self.assertAlmostEqual(bucket.tokens, 4, delta=0.5)

    def test_acquire_fail_when_empty(self):
        """测试令牌不足时获取失败."""
        bucket = TokenBucket(rate=10.0, capacity=1)
        bucket.acquire(tokens=1, blocking=False)
        result = bucket.acquire(tokens=1, blocking=False)
        self.assertFalse(result)

    def test_token_refill(self):
        """测试令牌自动补充."""
        bucket = TokenBucket(rate=10.0, capacity=5)
        bucket.acquire(tokens=5, blocking=False)  # 消耗所有令牌

        # 等待令牌补充
        time.sleep(0.3)  # 等待 0.3 秒，应该补充 3 个令牌
        self.assertGreaterEqual(bucket.tokens, 2)

    def test_acquire_blocking(self):
        """测试阻塞获取令牌."""
        bucket = TokenBucket(rate=10.0, capacity=1)
        bucket.acquire(tokens=1, blocking=False)  # 消耗所有令牌

        start = time.monotonic()
        result = bucket.acquire(tokens=1, blocking=True)  # 阻塞等待
        elapsed = time.monotonic() - start

        self.assertTrue(result)
        self.assertGreaterEqual(elapsed, 0.08)  # 至少等待 0.1 秒（1/10）


class TestRateLimiter(unittest.TestCase):
    """测试限速器."""

    def setUp(self):
        """设置测试环境."""
        self.limiter = RateLimiter()

    def test_get_rate_limiter_singleton(self):
        """测试全局单例."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        self.assertIs(limiter1, limiter2)

    def test_acquire_with_configured_source(self):
        """测试已配置数据源的限速."""
        # akshare 是默认配置的数据源
        result = self.limiter.acquire("akshare", tokens=1, blocking=False)
        self.assertTrue(result)

    def test_acquire_with_unknown_source(self):
        """测试未知数据源使用默认配置."""
        result = self.limiter.acquire("unknown_source", tokens=1, blocking=False)
        self.assertTrue(result)

    def test_call_with_rate_limit(self):
        """测试在限速控制下执行函数."""
        mock_func = MagicMock(return_value="result")

        result = self.limiter.call_with_rate_limit(
            "akshare",
            mock_func,
            "arg1",
            kwarg1="value1"
        )

        self.assertEqual(result, "result")
        mock_func.assert_called_once_with("arg1", kwarg1="value1")

    def test_get_status(self):
        """测试获取限速器状态."""
        status = self.limiter.get_status()

        self.assertIn("akshare", status)
        self.assertIn("tushare", status)
        self.assertIn("wind", status)
        self.assertIn("default", status)

        for source_status in status.values():
            self.assertIn("enabled", source_status)
            self.assertIn("requests_per_second", source_status)
            self.assertIn("bucket_size", source_status)


class TestRateLimiterIntegration(unittest.TestCase):
    """限速器集成测试."""

    def test_rate_limiting_prevents_burst(self):
        """测试限速防止突发流量."""
        limiter = RateLimiter()

        # 先消耗桶内所有令牌
        for _ in range(10):
            limiter.acquire("akshare", blocking=False)

        # 快速连续请求应该被限速
        start = time.monotonic()
        for _ in range(3):
            limiter.acquire("akshare", blocking=True)
        elapsed = time.monotonic() - start

        # 3个请求，限速 5 req/s，至少应该花费 0.4 秒（考虑桶内可能有剩余令牌）
        self.assertGreaterEqual(elapsed, 0.3)


if __name__ == "__main__":
    unittest.main()
