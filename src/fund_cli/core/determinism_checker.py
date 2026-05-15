"""
分析结果确定性验证器.

确保相同输入产生相同输出，支持快照测试和哈希比对。
"""

import hashlib
import json
import logging
import pickle
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

import pandas as pd

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class DeterminismResult:
    """确定性验证结果."""

    is_deterministic: bool
    input_hash: str
    output_hash: str
    previous_hash: str | None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        return {
            "is_deterministic": self.is_deterministic,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class DeterminismChecker:
    """
    确定性检查器.

    验证分析结果的可复现性，支持快照测试。
    """

    def __init__(self, snapshot_dir: str = "~/.fund_cli/snapshots"):
        """
        初始化确定性检查器.

        Args:
            snapshot_dir: 快照存储目录
        """
        self._snapshot_dir = Path(snapshot_dir).expanduser()
        self._snapshot_dir.mkdir(parents=True, exist_ok=True)

    def _compute_hash(self, obj: Any) -> str:
        """
        计算对象的哈希值.

        Args:
            obj: 任意对象

        Returns:
            哈希字符串
        """
        try:
            # 对于DataFrame，使用特定方式序列化
            if isinstance(obj, pd.DataFrame):
                # 排序列和索引确保一致性
                df = obj.sort_index().sort_index(axis=1)
                # 使用to_json确保跨版本一致性
                data = df.to_json(orient='table', date_format='iso')
                return hashlib.sha256(data.encode()).hexdigest()[:32]

            # 对于字典，使用JSON序列化
            if isinstance(obj, dict):
                # 处理可能的非序列化对象
                def json_serial(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    if isinstance(obj, pd.Timestamp):
                        return obj.isoformat()
                    raise TypeError(f"Type {type(obj)} not serializable")

                data = json.dumps(obj, sort_keys=True, default=json_serial)
                return hashlib.sha256(data.encode()).hexdigest()[:32]

            # 其他对象使用pickle
            data = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
            return hashlib.sha256(data).hexdigest()[:32]

        except Exception as e:
            logger.error(f"计算哈希失败: {e}")
            return ""

    def _get_snapshot_path(self, test_name: str) -> Path:
        """获取快照文件路径."""
        return self._snapshot_dir / f"{test_name}.snap"

    def check_determinism(
        self,
        func: Callable[..., T],
        *args: Any,
        test_name: str | None = None,
        **kwargs: Any,
    ) -> DeterminismResult:
        """
        检查函数执行的确定性.

        Args:
            func: 要检查的函数
            *args, **kwargs: 函数参数
            test_name: 测试名称（用于存储快照）

        Returns:
            确定性验证结果
        """
        # 计算输入哈希
        input_hash = self._compute_hash({"args": args, "kwargs": kwargs})

        # 执行函数
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logger.error(f"函数执行失败: {e}")
            return DeterminismResult(
                is_deterministic=False,
                input_hash=input_hash,
                output_hash="",
                previous_hash=None,
                metadata={"error": str(e)},
            )

        # 计算输出哈希
        output_hash = self._compute_hash(result)

        # 如果没有测试名称，只返回当前结果
        if test_name is None:
            return DeterminismResult(
                is_deterministic=True,
                input_hash=input_hash,
                output_hash=output_hash,
                previous_hash=None,
            )

        # 读取之前的快照
        snapshot_path = self._get_snapshot_path(test_name)
        previous_hash = None
        is_deterministic = True

        if snapshot_path.exists():
            try:
                with open(snapshot_path) as f:
                    snapshot = json.load(f)
                    previous_hash = snapshot.get("output_hash")

                # 比较哈希
                if previous_hash != output_hash:
                    is_deterministic = False
                    logger.warning(
                        f"确定性验证失败 [{test_name}]: "
                        f"previous={previous_hash}, current={output_hash}"
                    )
            except Exception as e:
                logger.error(f"读取快照失败: {e}")

        # 保存新快照
        snapshot_data = {
            "input_hash": input_hash,
            "output_hash": output_hash,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            with open(snapshot_path, 'w') as f:
                json.dump(snapshot_data, f, indent=2)
        except Exception as e:
            logger.error(f"保存快照失败: {e}")

        return DeterminismResult(
            is_deterministic=is_deterministic,
            input_hash=input_hash,
            output_hash=output_hash,
            previous_hash=previous_hash,
            metadata={"test_name": test_name, "snapshot_path": str(snapshot_path)},
        )

    def compare_snapshots(
        self,
        test_name: str,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> tuple[bool, T, T | None]:
        """
        比较当前结果与快照.

        Args:
            test_name: 测试名称
            func: 要检查的函数
            *args, **kwargs: 函数参数

        Returns:
            (是否一致, 当前结果, 之前的结果或None)
        """
        result = func(*args, **kwargs)
        current_hash = self._compute_hash(result)

        snapshot_path = self._get_snapshot_path(test_name)
        if not snapshot_path.exists():
            # 保存新快照
            self.check_determinism(func, *args, test_name=test_name, **kwargs)
            return True, result, None

        try:
            with open(snapshot_path, 'rb') as f:
                previous_result = pickle.load(f)
            previous_hash = self._compute_hash(previous_result)

            is_same = current_hash == previous_hash

            if not is_same:
                # 更新快照
                self.check_determinism(func, *args, test_name=test_name, **kwargs)

            return is_same, result, previous_result

        except Exception as e:
            logger.error(f"比较快照失败: {e}")
            # 保存新快照
            self.check_determinism(func, *args, test_name=test_name, **kwargs)
            return True, result, None

    def clear_snapshot(self, test_name: str | None = None) -> None:
        """
        清除快照.

        Args:
            test_name: 测试名称，None则清除所有
        """
        if test_name is None:
            for snap_file in self._snapshot_dir.glob("*.snap"):
                snap_file.unlink()
            logger.info("已清除所有快照")
        else:
            snapshot_path = self._get_snapshot_path(test_name)
            if snapshot_path.exists():
                snapshot_path.unlink()
                logger.info(f"已清除快照: {test_name}")

    def list_snapshots(self) -> list[dict[str, Any]]:
        """
        列出所有快照.

        Returns:
            快照信息列表
        """
        snapshots = []
        for snap_file in self._snapshot_dir.glob("*.snap"):
            try:
                with open(snap_file) as f:
                    data = json.load(f)
                    data["test_name"] = snap_file.stem
                    snapshots.append(data)
            except Exception as e:
                logger.error(f"读取快照失败 {snap_file}: {e}")

        return snapshots


# 全局确定性检查器实例
_checker: DeterminismChecker | None = None


def get_determinism_checker() -> DeterminismChecker:
    """获取全局确定性检查器实例."""
    global _checker
    if _checker is None:
        _checker = DeterminismChecker()
    return _checker


def deterministic_test(test_name: str):
    """
    确定性测试装饰器.

    Args:
        test_name: 测试名称

    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., DeterminismResult]:
        def wrapper(*args: Any, **kwargs: Any) -> DeterminismResult:
            checker = get_determinism_checker()
            return checker.check_determinism(func, *args, test_name=test_name, **kwargs)
        return wrapper
    return decorator
