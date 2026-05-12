"""
确定性验证器测试.

验证分析结果的可复现性检查功能。
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from fund_cli.core.determinism_checker import (
    DeterminismResult,
    DeterminismChecker,
    get_determinism_checker,
    deterministic_test,
)


class TestDeterminismResult(unittest.TestCase):
    """测试确定性验证结果."""

    def test_result_creation(self):
        """测试结果创建."""
        result = DeterminismResult(
            is_deterministic=True,
            input_hash="abc123",
            output_hash="def456",
            previous_hash=None,
        )

        self.assertTrue(result.is_deterministic)
        self.assertEqual(result.input_hash, "abc123")
        self.assertEqual(result.output_hash, "def456")
        self.assertIsNone(result.previous_hash)

    def test_result_to_dict(self):
        """测试结果转字典."""
        result = DeterminismResult(
            is_deterministic=True,
            input_hash="abc123",
            output_hash="def456",
            previous_hash="old789",
            metadata={"test": "data"},
        )

        d = result.to_dict()

        self.assertEqual(d["is_deterministic"], True)
        self.assertEqual(d["input_hash"], "abc123")
        self.assertEqual(d["output_hash"], "def456")
        self.assertEqual(d["previous_hash"], "old789")
        self.assertEqual(d["metadata"], {"test": "data"})


class TestDeterminismChecker(unittest.TestCase):
    """测试确定性检查器."""

    def setUp(self):
        """设置测试环境."""
        self.temp_dir = TemporaryDirectory()
        self.checker = DeterminismChecker(snapshot_dir=self.temp_dir.name)

    def tearDown(self):
        """清理测试环境."""
        self.temp_dir.cleanup()

    def test_compute_hash_dataframe(self):
        """测试DataFrame哈希计算."""
        df1 = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df2 = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df3 = pd.DataFrame({"a": [1, 2, 4], "b": [4, 5, 6]})

        hash1 = self.checker._compute_hash(df1)
        hash2 = self.checker._compute_hash(df2)
        hash3 = self.checker._compute_hash(df3)

        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)

    def test_compute_hash_dict(self):
        """测试字典哈希计算."""
        dict1 = {"a": 1, "b": [2, 3], "c": {"d": 4}}
        dict2 = {"b": [2, 3], "a": 1, "c": {"d": 4}}
        dict3 = {"a": 1, "b": [2, 3], "c": {"d": 5}}

        hash1 = self.checker._compute_hash(dict1)
        hash2 = self.checker._compute_hash(dict2)
        hash3 = self.checker._compute_hash(dict3)

        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)

    def test_check_determinism_no_test_name(self):
        """测试无测试名称的确定性检查."""
        def test_func(x, y):
            return x + y

        result = self.checker.check_determinism(test_func, 1, 2)

        self.assertTrue(result.is_deterministic)
        self.assertIsNotNone(result.input_hash)
        self.assertIsNotNone(result.output_hash)
        self.assertIsNone(result.previous_hash)

    def test_check_determinism_first_run(self):
        """测试首次运行（创建快照）."""
        def test_func(x):
            return x * 2

        result = self.checker.check_determinism(test_func, 5, test_name="test_multiply")

        self.assertTrue(result.is_deterministic)
        self.assertIsNotNone(result.output_hash)

        # 验证快照文件已创建
        snapshot_path = Path(self.temp_dir.name) / "test_multiply.snap"
        self.assertTrue(snapshot_path.exists())

    def test_check_determinism_consistent(self):
        """测试一致的确定性."""
        def test_func(x):
            return x + 10

        # 第一次运行
        result1 = self.checker.check_determinism(test_func, 5, test_name="test_add")

        # 第二次运行（相同输入）
        result2 = self.checker.check_determinism(test_func, 5, test_name="test_add")

        self.assertTrue(result1.is_deterministic)
        self.assertTrue(result2.is_deterministic)
        self.assertEqual(result1.output_hash, result2.output_hash)

    def test_check_determinism_inconsistent(self):
        """测试不一致的确定性."""
        call_count = [0]

        def non_deterministic_func():
            call_count[0] += 1
            return call_count[0]

        # 第一次运行
        result1 = self.checker.check_determinism(
            non_deterministic_func, test_name="test_nondet"
        )
        first_hash = result1.output_hash

        # 第二次运行（不同输出）
        result2 = self.checker.check_determinism(
            non_deterministic_func, test_name="test_nondet"
        )

        self.assertTrue(result1.is_deterministic)  # 首次运行总是True
        self.assertFalse(result2.is_deterministic)  # 第二次检测到不一致
        self.assertEqual(result2.previous_hash, first_hash)

    def test_check_determinism_with_error(self):
        """测试函数执行失败."""
        def failing_func():
            raise ValueError("test error")

        result = self.checker.check_determinism(failing_func, test_name="test_error")

        self.assertFalse(result.is_deterministic)
        self.assertEqual(result.output_hash, "")
        self.assertIn("error", result.metadata)

    def test_clear_snapshot_single(self):
        """测试清除单个快照."""
        # 创建快照
        def test_func():
            return 42

        self.checker.check_determinism(test_func, test_name="test_clear")

        snapshot_path = Path(self.temp_dir.name) / "test_clear.snap"
        self.assertTrue(snapshot_path.exists())

        # 清除快照
        self.checker.clear_snapshot("test_clear")
        self.assertFalse(snapshot_path.exists())

    def test_clear_snapshot_all(self):
        """测试清除所有快照."""
        def test_func():
            return 42

        self.checker.check_determinism(test_func, test_name="test1")
        self.checker.check_determinism(test_func, test_name="test2")

        self.assertEqual(len(list(Path(self.temp_dir.name).glob("*.snap"))), 2)

        self.checker.clear_snapshot()

        self.assertEqual(len(list(Path(self.temp_dir.name).glob("*.snap"))), 0)

    def test_list_snapshots(self):
        """测试列出快照."""
        def test_func():
            return 42

        self.checker.check_determinism(test_func, test_name="test_list")

        snapshots = self.checker.list_snapshots()

        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0]["test_name"], "test_list")
        self.assertIn("input_hash", snapshots[0])
        self.assertIn("output_hash", snapshots[0])


class TestGetDeterminismChecker(unittest.TestCase):
    """测试全局检查器获取."""

    def test_get_checker_singleton(self):
        """测试全局单例."""
        checker1 = get_determinism_checker()
        checker2 = get_determinism_checker()
        self.assertIs(checker1, checker2)


class TestDeterministicTestDecorator(unittest.TestCase):
    """测试确定性测试装饰器."""

    def setUp(self):
        """设置测试环境."""
        self.temp_dir = TemporaryDirectory()
        self.checker = DeterminismChecker(snapshot_dir=self.temp_dir.name)

    def tearDown(self):
        """清理测试环境."""
        self.temp_dir.cleanup()

    def test_decorator(self):
        """测试装饰器功能."""

        @deterministic_test("decorated_test")
        def test_func(x, y):
            return x + y

        result = test_func(1, 2)

        self.assertIsInstance(result, DeterminismResult)
        self.assertTrue(result.is_deterministic)


if __name__ == "__main__":
    unittest.main()
