import pytest
import time
from utils import MetricsEmitter, Timer


class TestMetricsEmitter:
    def test_increment(self):
        metrics = MetricsEmitter()
        metrics.increment("test.counter", 5, tags={"tag": "value"})
        
        assert metrics.get_counter("test.counter", tags={"tag": "value"}) == 5
    
    def test_increment_multiple(self):
        metrics = MetricsEmitter()
        metrics.increment("test.counter", 1)
        metrics.increment("test.counter", 2)
        metrics.increment("test.counter", 3)
        
        assert metrics.get_counter("test.counter") == 6
    
    def test_decrement(self):
        metrics = MetricsEmitter()
        metrics.increment("test.counter", 10)
        metrics.decrement("test.counter", 3)
        
        assert metrics.get_counter("test.counter") == 7
    
    def test_gauge(self):
        metrics = MetricsEmitter()
        metrics.gauge("test.gauge", 42.5)
        
        assert metrics.get_gauge("test.gauge") == 42.5
    
    def test_timing(self):
        metrics = MetricsEmitter()
        metrics.timing("test.timing", 100.5)
        
        stats = metrics.get_histogram_stats("test.timing")
        assert stats["count"] == 1
        assert stats["avg"] == 100.5
    
    def test_histogram(self):
        metrics = MetricsEmitter()
        metrics.histogram("test.histogram", 10.0)
        metrics.histogram("test.histogram", 20.0)
        metrics.histogram("test.histogram", 30.0)
        
        stats = metrics.get_histogram_stats("test.histogram")
        assert stats["count"] == 3
        assert stats["avg"] == 20.0
        assert stats["min"] == 10.0
        assert stats["max"] == 30.0
    
    def test_histogram_percentiles(self):
        metrics = MetricsEmitter()
        
        # Add 100 values
        for i in range(100):
            metrics.histogram("test.percentiles", float(i))
        
        stats = metrics.get_histogram_stats("test.percentiles")
        assert stats["count"] == 100
        assert stats["p50"] == 49.0
        assert stats["p95"] == 94.0
        assert stats["p99"] == 98.0
    
    def test_tags(self):
        metrics = MetricsEmitter()
        metrics.increment("test.counter", 1, tags={"service": "a"})
        metrics.increment("test.counter", 2, tags={"service": "b"})
        
        assert metrics.get_counter("test.counter", tags={"service": "a"}) == 1
        assert metrics.get_counter("test.counter", tags={"service": "b"}) == 2
    
    def test_reset(self):
        metrics = MetricsEmitter()
        metrics.increment("test.counter", 10)
        metrics.gauge("test.gauge", 42.0)
        
        metrics.reset()
        
        assert metrics.get_counter("test.counter") == 0
        assert metrics.get_gauge("test.gauge") is None
    
    def test_get_all_metrics(self):
        metrics = MetricsEmitter()
        metrics.increment("test.counter", 5)
        metrics.gauge("test.gauge", 42.0)
        metrics.timing("test.timing", 100.0)
        
        all_metrics = metrics.get_all_metrics()
        
        assert "counters" in all_metrics
        assert "gauges" in all_metrics
        assert "histograms" in all_metrics
        assert all_metrics["counters"]["test.counter"] == 5
        assert all_metrics["gauges"]["test.gauge"] == 42.0


class TestTimer:
    def test_timer_context_manager(self):
        metrics = MetricsEmitter()
        
        with Timer(metrics, "test.operation"):
            time.sleep(0.01)
        
        stats = metrics.get_histogram_stats("test.operation")
        assert stats["count"] == 1
        assert stats["avg"] > 0
    
    def test_timer_with_tags(self):
        metrics = MetricsEmitter()
        
        with Timer(metrics, "test.operation", tags={"service": "test"}):
            time.sleep(0.01)
        
        stats = metrics.get_histogram_stats("test.operation", tags={"service": "test"})
        assert stats["count"] == 1
