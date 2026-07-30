import pytest
from tracing import Tracer, TraceContext, TraceParent


class TestTraceContext:
    def test_generate_trace_context(self):
        context = TraceContext.generate()
        
        assert context.trace_id is not None
        assert len(context.trace_id) == 32
        assert context.span_id is not None
        assert len(context.span_id) == 16
        assert context.trace_flags == "00"
    
    def test_trace_context_to_traceparent(self):
        context = TraceContext(
            trace_id="1234567890abcdef1234567890abcdef",
            span_id="1234567890abcdef",
            trace_flags="01"
        )
        
        traceparent = context.to_traceparent()
        assert traceparent == "1234567890abcdef1234567890abcdef-1234567890abcdef-01"
    
    def test_trace_context_from_traceparent(self):
        traceparent = "1234567890abcdef1234567890abcdef-1234567890abcdef-01"
        context = TraceContext.from_traceparent(traceparent)
        
        assert context.trace_id == "1234567890abcdef1234567890abcdef"
        assert context.span_id == "1234567890abcdef"
        assert context.trace_flags == "01"
    
    def test_trace_context_from_traceparent_invalid(self):
        with pytest.raises(ValueError, match="Invalid traceparent format"):
            TraceContext.from_traceparent("invalid-format")
    
    def test_trace_context_from_traceparent_case_insensitive(self):
        traceparent = "ABCDEF1234567890ABCDEF1234567890-ABCDEF1234567890-01"
        context = TraceContext.from_traceparent(traceparent)
        
        assert context.trace_id == "abcdef1234567890abcdef1234567890"
        assert context.span_id == "abcdef1234567890"


class TestTraceParent:
    def test_trace_parent_to_dict(self):
        trace_context = TraceContext.generate()
        trace_parent = TraceParent(
            trace_context=trace_context,
            correlation_id="corr-123",
            causation_id="cause-123"
        )
        
        headers = trace_parent.to_dict()
        assert "traceparent" in headers
        assert headers["correlation_id"] == "corr-123"
        assert headers["causation_id"] == "cause-123"
    
    def test_trace_parent_from_dict(self):
        headers = {
            "traceparent": "1234567890abcdef1234567890abcdef-1234567890abcdef-00",
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "parent_span_id": "parent-123"
        }
        
        trace_parent = TraceParent.from_dict(headers)
        assert trace_parent.correlation_id == "corr-123"
        assert trace_parent.causation_id == "cause-123"
        assert trace_parent.parent_span_id == "parent-123"
    
    def test_trace_parent_from_dict_no_traceparent(self):
        headers = {"correlation_id": "corr-123"}
        
        trace_parent = TraceParent.from_dict(headers)
        assert trace_parent.trace_context is not None
        assert trace_parent.correlation_id == "corr-123"
    
    def test_trace_parent_create_child(self):
        trace_parent = TraceParent(
            trace_context=TraceContext.generate(),
            correlation_id="corr-123",
            causation_id="cause-123"
        )
        
        child = trace_parent.create_child()
        
        assert child.trace_context.trace_id == trace_parent.trace_context.trace_id
        assert child.trace_context.span_id != trace_parent.trace_context.span_id
        assert child.parent_span_id == trace_parent.trace_context.span_id
        assert child.causation_id == trace_parent.trace_context.span_id


class TestTracer:
    def test_tracer_start_span_new(self):
        tracer = Tracer("test-service")
        trace_parent = tracer.start_span("test_operation")
        
        assert trace_parent.trace_context is not None
        assert trace_parent.correlation_id is not None
    
    def test_tracer_start_span_with_parent(self):
        tracer = Tracer("test-service")
        parent = TraceParent(
            trace_context=TraceContext.generate(),
            correlation_id="corr-123"
        )
        
        child = tracer.start_span("child_operation", parent=parent)
        
        assert child.trace_context.trace_id == parent.trace_context.trace_id
        assert child.trace_context.span_id != parent.trace_context.span_id
        assert child.parent_span_id == parent.trace_context.span_id
    
    def test_tracer_start_span_with_headers(self):
        tracer = Tracer("test-service")
        headers = {
            "traceparent": "1234567890abcdef1234567890abcdef-1234567890abcdef-00",
            "correlation_id": "corr-123"
        }
        
        trace_parent = tracer.start_span("test_operation", headers=headers)
        
        assert trace_parent.trace_context.trace_id == "1234567890abcdef1234567890abcdef"
        assert trace_parent.correlation_id == "corr-123"
    
    def test_tracer_finish_span(self):
        tracer = Tracer("test-service")
        trace_parent = tracer.start_span("test_operation")
        
        # Should not raise exception
        tracer.finish_span(trace_parent, "test_operation", True, duration_ms=100.0)
    
    def test_tracer_inject_headers(self):
        tracer = Tracer("test-service")
        trace_parent = TraceParent(
            trace_context=TraceContext.generate(),
            correlation_id="corr-123"
        )
        
        headers = tracer.inject_headers(trace_parent)
        
        assert "traceparent" in headers
        assert headers["correlation_id"] == "corr-123"
    
    def test_tracer_extract_headers(self):
        tracer = Tracer("test-service")
        headers = {
            "traceparent": "1234567890abcdef1234567890abcdef-1234567890abcdef-00",
            "correlation_id": "corr-123"
        }
        
        trace_parent = tracer.extract_headers(headers)
        
        assert trace_parent is not None
        assert trace_parent.correlation_id == "corr-123"
    
    def test_tracer_extract_headers_no_traceparent(self):
        tracer = Tracer("test-service")
        headers = {"correlation_id": "corr-123"}
        
        trace_parent = tracer.extract_headers(headers)
        
        assert trace_parent is None
    
    def test_tracer_log_event(self):
        tracer = Tracer("test-service")
        trace_parent = TraceParent(
            trace_context=TraceContext.generate(),
            correlation_id="corr-123"
        )
        
        # Should not raise exception
        tracer.log_event(trace_parent, "test.event", {"key": "value"})
