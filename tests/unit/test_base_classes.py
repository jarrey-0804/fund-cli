"""
单元测试 - 核心模块
"""

import pytest

from fund_cli.core.optimizer import Optimizer
from fund_cli.core.reporter import Reporter


class TestOptimizer:
    """优化引擎基类测试"""

    def test_cannot_instantiate(self):
        """测试基类不能直接实例化"""
        with pytest.raises(TypeError):
            Optimizer()

    def test_subclass_must_implement(self):
        """测试子类必须实现抽象方法"""

        class IncompleteOptimizer(Optimizer):
            def optimize(self, data, **kwargs):
                pass

            # 缺少 get_methods

        with pytest.raises(TypeError):
            IncompleteOptimizer()

    def test_complete_subclass(self):
        """测试完整子类可以实例化"""

        class CompleteOptimizer(Optimizer):
            def optimize(self, data, **kwargs):
                return {"weights": {}, "expected_return": 0}

            def get_methods(self):
                return ["equal_weight"]

        optimizer = CompleteOptimizer()
        assert optimizer.get_methods() == ["equal_weight"]


class TestReporter:
    """报告生成器基类测试"""

    def test_cannot_instantiate(self):
        """测试基类不能直接实例化"""
        with pytest.raises(TypeError):
            Reporter()

    def test_complete_subclass(self):
        """测试完整子类可以实例化"""

        class CompleteReporter(Reporter):
            def generate(self, fund_code, metrics, nav_data=None, benchmark_data=None, **kwargs):
                return f"Report for {fund_code}"

            def save(self, content, output_path):
                with open(output_path, "w") as f:
                    f.write(content)

            def get_formats(self):
                return ["html", "markdown"]

        reporter = CompleteReporter()
        assert reporter.get_formats() == ["html", "markdown"]
        assert reporter.generate("000001", {}) == "Report for 000001"
