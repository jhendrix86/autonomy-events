import time
from typing import Dict, Any, Optional
from collections import defaultdict
from threading import Lock


class MetricsEmitter:
    """Simple metrics emitter for tracking event processing."""
    
    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = defaultdict(list)
        self._lock = Lock()
    
    def increment(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] += value
    
    def decrement(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Decrement a counter metric."""
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] -= value
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric."""
        with self._lock:
            key = self._make_key(name, tags)
            self._gauges[key] = value
    
    def timing(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record a timing metric."""
        with self._lock:
            key = self._make_key(name, tags)
            self._histograms[key].append(duration_ms)
    
    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram value."""
        with self._lock:
            key = self._make_key(name, tags)
            self._histograms[key].append(value)
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get a counter value."""
        key = self._make_key(name, tags)
        return self._counters.get(key, 0)
    
    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get a gauge value."""
        key = self._make_key(name, tags)
        return self._gauges.get(key)
    
    def get_histogram_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics (count, avg, min, max, p50, p95, p99)."""
        key = self._make_key(name, tags)
        values = self._histograms.get(key, [])
        
        if not values:
            return {}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "avg": sum(sorted_values) / count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": sorted_values[max(0, int(count * 0.5) - 1)],
            "p95": sorted_values[max(0, int(count * 0.95) - 1)],
            "p99": sorted_values[max(0, int(count * 0.99) - 1)],
        }

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    key: self._get_histogram_stats_from_values(values)
                    for key, values in self._histograms.items()
                }
            }
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Create a metric key from name and tags."""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}|{tag_str}"
    
    def _get_histogram_stats_from_values(self, values: list) -> Dict[str, float]:
        """Get histogram stats from raw values."""
        if not values:
            return {}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "avg": sum(sorted_values) / count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": sorted_values[max(0, int(count * 0.5) - 1)],
            "p95": sorted_values[max(0, int(count * 0.95) - 1)],
            "p99": sorted_values[max(0, int(count * 0.99) - 1)],
        }


class Timer:
    """Context manager for timing operations."""
    
    def __init__(self, metrics: MetricsEmitter, name: str, tags: Optional[Dict[str, str]] = None):
        self.metrics = metrics
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
            self.metrics.timing(self.name, duration_ms, self.tags)
