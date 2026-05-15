"""
计算链路追踪上下文.

实现分布式追踪功能，支持Trace ID贯穿全链路。
"""

import contextvars
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# 上下文变量
trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('trace_id')
span_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('span_id')
parent_span_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar('parent_span_id', default=None)


@dataclass
class TraceSpan:
    """追踪Span."""

    span_id: str
    trace_id: str
    name: str
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float = 0.0
    parent_span_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"  # ok, error
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "parent_span_id": self.parent_span_id,
            "attributes": self.attributes,
            "status": self.status,
            "error_message": self.error_message,
        }


@dataclass
class TraceContext:
    """追踪上下文."""

    trace_id: str
    spans: list[TraceSpan] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        return {
            "trace_id": self.trace_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "spans": [span.to_dict() for span in self.spans],
        }


class Tracer:
    """
    追踪器.

    管理Trace和Span的生命周期，支持嵌套Span。
    """

    def __init__(self):
        """初始化追踪器."""
        self._active_traces: dict[str, TraceContext] = {}
        self._current_spans: dict[str, TraceSpan] = {}

    def start_trace(self, trace_id: str | None = None) -> str:
        """
        开始新的追踪.

        Args:
            trace_id: 追踪ID，None则自动生成

        Returns:
            追踪ID
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())[:16]

        context = TraceContext(trace_id=trace_id)
        self._active_traces[trace_id] = context

        # 设置上下文变量
        trace_id_var.set(trace_id)

        logger.debug(f"开始追踪: {trace_id}")
        return trace_id

    def end_trace(self, trace_id: str | None = None) -> TraceContext:
        """
        结束追踪.

        Args:
            trace_id: 追踪ID，None则使用当前上下文

        Returns:
            追踪上下文
        """
        if trace_id is None:
            try:
                trace_id = trace_id_var.get()
            except LookupError:
                raise ValueError("没有活动的追踪") from None

        context = self._active_traces.pop(trace_id, None)
        if context:
            context.end_time = datetime.now()
            logger.debug(f"结束追踪: {trace_id}, 共{len(context.spans)}个span")
            return context

        raise ValueError(f"追踪不存在: {trace_id}")

    def start_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> str:
        """
        开始新的Span.

        Args:
            name: Span名称
            attributes: Span属性

        Returns:
            Span ID
        """
        try:
            trace_id = trace_id_var.get()
        except LookupError:
            # 如果没有活动trace，自动创建一个
            trace_id = self.start_trace()

        span_id = str(uuid.uuid4())[:16]

        # 获取父span
        try:
            parent_span_id = span_id_var.get()
        except LookupError:
            parent_span_id = None

        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            name=name,
            start_time=datetime.now(),
            parent_span_id=parent_span_id,
            attributes=attributes or {},
        )

        self._current_spans[span_id] = span

        # 更新上下文变量
        span_id_var.set(span_id)
        parent_span_id_var.set(parent_span_id)

        logger.debug(f"开始Span: {name} ({span_id})")
        return span_id

    def end_span(
        self,
        span_id: str | None = None,
        status: str = "ok",
        error_message: str = "",
    ) -> TraceSpan:
        """
        结束Span.

        Args:
            span_id: Span ID，None则使用当前上下文
            status: 状态
            error_message: 错误信息

        Returns:
            Span对象
        """
        if span_id is None:
            try:
                span_id = span_id_var.get()
            except LookupError:
                raise ValueError("没有活动的Span") from None

        span = self._current_spans.pop(span_id, None)
        if not span:
            raise ValueError(f"Span不存在: {span_id}")

        span.end_time = datetime.now()
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        span.status = status
        span.error_message = error_message

        # 添加到trace
        trace_id = span.trace_id
        if trace_id in self._active_traces:
            self._active_traces[trace_id].spans.append(span)

        # 恢复父span上下文
        if span.parent_span_id:
            span_id_var.set(span.parent_span_id)
        else:
            # 如果没有父span，清除span_id上下文
            try:
                span_id_var.set("")
            except LookupError:
                pass

        logger.debug(f"结束Span: {span.name}, 耗时{span.duration_ms:.2f}ms")
        return span

    def get_current_trace_id(self) -> str | None:
        """获取当前追踪ID."""
        try:
            return trace_id_var.get()
        except LookupError:
            return None

    def get_current_span_id(self) -> str | None:
        """获取当前Span ID."""
        try:
            return span_id_var.get()
        except LookupError:
            return None

    def add_span_attribute(self, key: str, value: Any) -> None:
        """
        添加Span属性.

        Args:
            key: 属性名
            value: 属性值
        """
        try:
            span_id = span_id_var.get()
            if span_id and span_id in self._current_spans:
                self._current_spans[span_id].attributes[key] = value
        except LookupError:
            pass


# 全局追踪器实例
_tracer: Tracer | None = None


def get_tracer() -> Tracer:
    """获取全局追踪器实例."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


class TraceContextManager:
    """
    追踪上下文管理器.

    支持with语句自动管理trace和span生命周期。
    """

    def __init__(self, name: str, attributes: dict[str, Any] | None = None):
        """
        初始化.

        Args:
            name: Span名称
            attributes: Span属性
        """
        self.name = name
        self.attributes = attributes or {}
        self.tracer = get_tracer()
        self.span_id: str | None = None
        self.trace_id: str | None = None

    def __enter__(self) -> 'TraceContextManager':
        """进入上下文."""
        # 检查是否已有trace
        current_trace = self.tracer.get_current_trace_id()
        if not current_trace:
            self.trace_id = self.tracer.start_trace()

        self.span_id = self.tracer.start_span(self.name, self.attributes)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文."""
        status = "error" if exc_type else "ok"
        error_message = str(exc_val) if exc_val else ""

        if self.span_id:
            self.tracer.end_span(self.span_id, status, error_message)

    def add_attribute(self, key: str, value: Any) -> None:
        """添加属性."""
        self.tracer.add_span_attribute(key, value)


def traced(name: str | None = None):
    """
    追踪装饰器.

    Args:
        name: Span名称，None则使用函数名

    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            span_name = name or func.__name__
            with TraceContextManager(span_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
