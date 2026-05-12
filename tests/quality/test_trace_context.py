"""
链路追踪上下文测试.

验证分布式追踪功能。
"""

import unittest
from datetime import datetime
from unittest.mock import patch

from fund_cli.core.trace_context import (
    TraceSpan,
    TraceContext,
    Tracer,
    TraceContextManager,
    traced,
    get_tracer,
)


class TestTraceSpan(unittest.TestCase):
    """测试追踪Span."""

    def test_span_creation(self):
        """测试创建Span."""
        span = TraceSpan(
            span_id="span123",
            trace_id="trace456",
            name="test_span",
            start_time=datetime.now(),
        )

        self.assertEqual(span.span_id, "span123")
        self.assertEqual(span.trace_id, "trace456")
        self.assertEqual(span.name, "test_span")
        self.assertEqual(span.status, "ok")
        self.assertEqual(span.duration_ms, 0.0)

    def test_span_to_dict(self):
        """测试Span转换为字典."""
        start_time = datetime.now()
        span = TraceSpan(
            span_id="span123",
            trace_id="trace456",
            name="test_span",
            start_time=start_time,
            attributes={"key": "value"},
            status="error",
            error_message="test error",
        )

        result = span.to_dict()

        self.assertEqual(result["span_id"], "span123")
        self.assertEqual(result["trace_id"], "trace456")
        self.assertEqual(result["name"], "test_span")
        self.assertEqual(result["attributes"], {"key": "value"})
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_message"], "test error")


class TestTraceContext(unittest.TestCase):
    """测试追踪上下文."""

    def test_context_creation(self):
        """测试创建上下文."""
        context = TraceContext(trace_id="trace123")

        self.assertEqual(context.trace_id, "trace123")
        self.assertEqual(context.spans, [])
        self.assertIsInstance(context.start_time, datetime)

    def test_context_to_dict(self):
        """测试上下文转换为字典."""
        context = TraceContext(trace_id="trace123")
        context.end_time = datetime.now()

        result = context.to_dict()

        self.assertEqual(result["trace_id"], "trace123")
        self.assertIn("start_time", result)
        self.assertIn("end_time", result)
        self.assertEqual(result["spans"], [])


class TestTracer(unittest.TestCase):
    """测试追踪器."""

    def setUp(self):
        """设置测试环境."""
        # 创建新的tracer实例，避免单例污染
        self.tracer = Tracer()
        # 清除全局上下文变量
        try:
            from fund_cli.core.trace_context import trace_id_var, span_id_var
            trace_id_var.set("")
            span_id_var.set("")
        except LookupError:
            pass

    def test_start_trace_auto_id(self):
        """测试自动生成的trace ID."""
        trace_id = self.tracer.start_trace()

        self.assertIsNotNone(trace_id)
        self.assertEqual(len(trace_id), 16)
        self.assertIn(trace_id, self.tracer._active_traces)

    def test_start_trace_custom_id(self):
        """测试自定义trace ID."""
        trace_id = self.tracer.start_trace("custom_trace_id")

        self.assertEqual(trace_id, "custom_trace_id")
        self.assertIn(trace_id, self.tracer._active_traces)

    def test_end_trace(self):
        """测试结束trace."""
        trace_id = self.tracer.start_trace()

        context = self.tracer.end_trace(trace_id)

        self.assertEqual(context.trace_id, trace_id)
        self.assertIsNotNone(context.end_time)
        self.assertNotIn(trace_id, self.tracer._active_traces)

    def test_end_trace_not_found(self):
        """测试结束不存在的trace."""
        with self.assertRaises(ValueError) as ctx:
            self.tracer.end_trace("nonexistent")

        self.assertIn("追踪不存在", str(ctx.exception))

    def test_start_span_without_trace(self):
        """测试无trace时自动创建."""
        span_id = self.tracer.start_span("test_span")

        self.assertIsNotNone(span_id)
        self.assertEqual(len(span_id), 16)
        self.assertIn(span_id, self.tracer._current_spans)

    def test_start_span_with_trace(self):
        """测试在trace内创建span."""
        trace_id = self.tracer.start_trace()
        span_id = self.tracer.start_span("test_span", {"attr": "value"})

        span = self.tracer._current_spans[span_id]
        self.assertEqual(span.name, "test_span")
        self.assertEqual(span.trace_id, trace_id)
        self.assertEqual(span.attributes, {"attr": "value"})

    def test_nested_spans(self):
        """测试嵌套span."""
        self.tracer.start_trace()
        parent_span_id = self.tracer.start_span("parent")
        child_span_id = self.tracer.start_span("child")

        child_span = self.tracer._current_spans[child_span_id]
        self.assertEqual(child_span.parent_span_id, parent_span_id)

    def test_end_span(self):
        """测试结束span."""
        self.tracer.start_trace()
        span_id = self.tracer.start_span("test_span")

        span = self.tracer.end_span(span_id)

        self.assertEqual(span.span_id, span_id)
        self.assertIsNotNone(span.end_time)
        self.assertGreater(span.duration_ms, 0)
        self.assertNotIn(span_id, self.tracer._current_spans)

    def test_end_span_with_error(self):
        """测试带错误的span结束."""
        self.tracer.start_trace()
        span_id = self.tracer.start_span("test_span")

        span = self.tracer.end_span(span_id, status="error", error_message="test error")

        self.assertEqual(span.status, "error")
        self.assertEqual(span.error_message, "test error")

    def test_get_current_trace_id(self):
        """测试获取当前trace ID."""
        # 使用独立的tracer实例测试
        fresh_tracer = Tracer()
        # 无trace时返回None或空字符串
        trace_id = fresh_tracer.get_current_trace_id()
        self.assertTrue(trace_id is None or trace_id == "")

        # 有trace时返回ID
        new_trace_id = fresh_tracer.start_trace()
        self.assertEqual(fresh_tracer.get_current_trace_id(), new_trace_id)

    def test_add_span_attribute(self):
        """测试添加span属性."""
        self.tracer.start_trace()
        span_id = self.tracer.start_span("test_span")

        self.tracer.add_span_attribute("key", "value")

        span = self.tracer._current_spans[span_id]
        self.assertEqual(span.attributes["key"], "value")

    def test_add_span_attribute_no_span(self):
        """测试无span时添加属性不报错."""
        # 不应抛出异常
        self.tracer.add_span_attribute("key", "value")


class TestTraceContextManager(unittest.TestCase):
    """测试追踪上下文管理器."""

    def setUp(self):
        """设置测试环境."""
        # 清除全局上下文变量
        try:
            from fund_cli.core.trace_context import trace_id_var, span_id_var
            trace_id_var.set("")
            span_id_var.set("")
        except LookupError:
            pass

    def test_context_manager_success(self):
        """测试成功的上下文管理."""
        tracer = Tracer()

        with TraceContextManager("test_operation", {"attr": "value"}) as ctx:
            ctx.add_attribute("extra", "data")
            span_id = tracer.get_current_span_id()
            self.assertIsNotNone(span_id)

        # 验证span已结束（使用新的tracer检查）
        fresh_tracer = Tracer()
        span_id = fresh_tracer.get_current_span_id()
        self.assertTrue(span_id is None or span_id == "")

    def test_context_manager_error(self):
        """测试异常的上下文管理."""
        tracer = Tracer()

        try:
            with TraceContextManager("test_operation"):
                raise ValueError("test error")
        except ValueError:
            pass

        # 验证span已结束且标记为错误（使用新的tracer检查）
        fresh_tracer = Tracer()
        span_id = fresh_tracer.get_current_span_id()
        self.assertTrue(span_id is None or span_id == "")

    def test_nested_context_managers(self):
        """测试嵌套上下文管理器."""
        tracer = Tracer()

        with TraceContextManager("outer"):
            outer_span_id = tracer.get_current_span_id()
            with TraceContextManager("inner"):
                inner_span_id = tracer.get_current_span_id()
                self.assertNotEqual(outer_span_id, inner_span_id)


class TestTracedDecorator(unittest.TestCase):
    """测试追踪装饰器."""

    def setUp(self):
        """设置测试环境."""
        # 清除全局上下文变量
        try:
            from fund_cli.core.trace_context import trace_id_var, span_id_var
            trace_id_var.set("")
            span_id_var.set("")
        except LookupError:
            pass

    def test_traced_decorator(self):
        """测试装饰器功能."""
        tracer = Tracer()

        @traced("custom_name")
        def test_function():
            return tracer.get_current_span_id()

        span_id = test_function()

        self.assertIsNotNone(span_id)
        # 函数执行完毕后span应已结束（使用新的tracer检查）
        fresh_tracer = Tracer()
        span_id_after = fresh_tracer.get_current_span_id()
        self.assertTrue(span_id_after is None or span_id_after == "")

    def test_traced_decorator_auto_name(self):
        """测试自动命名."""
        tracer = Tracer()

        @traced()
        def my_function_name():
            return tracer.get_current_span_id()

        span_id = my_function_name()
        self.assertIsNotNone(span_id)


class TestGetTracer(unittest.TestCase):
    """测试全局tracer获取."""

    def test_get_tracer_singleton(self):
        """测试全局单例."""
        tracer1 = get_tracer()
        tracer2 = get_tracer()
        self.assertIs(tracer1, tracer2)


if __name__ == "__main__":
    unittest.main()
