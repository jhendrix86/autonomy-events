from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class EngineHealthReport(BaseModel):
    engine_id: str = Field(..., description="Engine identifier")
    engine_type: str = Field(..., description="Type of engine (core, intelligence, autonomous)")
    status: str = Field(..., description="Health status (healthy, degraded, unhealthy)")
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    uptime_seconds: int = Field(default=0, description="Engine uptime in seconds")
    cpu_usage: float = Field(default=0.0, description="CPU usage percentage")
    memory_usage: float = Field(default=0.0, description="Memory usage percentage")
    active_connections: int = Field(default=0, description="Number of active connections")
    queue_depth: int = Field(default=0, description="Message queue depth")
    error_rate: float = Field(default=0.0, description="Error rate percentage")
    latency_ms: float = Field(default=0.0, description="Average latency in milliseconds")
    throughput: float = Field(default=0.0, description="Throughput per second")
    custom_metrics: Dict[str, Any] = Field(default_factory=dict, description="Custom health metrics")
    dependencies: List[Dict[str, str]] = Field(default_factory=list, description="Dependency health status")


class EngineDegraded(BaseModel):
    engine_id: str = Field(..., description="Engine identifier")
    degradation_type: str = Field(..., description="Type of degradation (performance, connectivity, resource)")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    detected_by: str = Field(..., description="Monitoring system that detected degradation")
    affected_services: List[str] = Field(default_factory=list, description="Services affected by degradation")
    current_metrics: Dict[str, Any] = Field(default_factory=dict, description="Current metrics")
    baseline_metrics: Dict[str, Any] = Field(default_factory=dict, description="Baseline metrics for comparison")
    impact_assessment: Dict[str, Any] = Field(default_factory=dict, description="Assessment of impact")
    estimated_recovery_time: Optional[int] = Field(None, description="Estimated recovery time in seconds")
    auto_recovery_enabled: bool = Field(default=True, description="Whether auto-recovery is enabled")


class EngineRecovered(BaseModel):
    engine_id: str = Field(..., description="Engine identifier")
    recovery_type: str = Field(..., description="Type of recovery (auto, manual, failover)")
    recovered_at: datetime = Field(default_factory=datetime.utcnow)
    degradation_duration: int = Field(..., description="Duration of degradation in seconds")
    root_cause: Optional[str] = Field(None, description="Root cause of degradation if identified")
    recovery_actions: List[str] = Field(default_factory=list, description="Actions taken to recover")
    post_recovery_metrics: Dict[str, Any] = Field(default_factory=dict, description="Metrics after recovery")
    data_loss: bool = Field(default=False, description="Whether there was any data loss")
    requires_manual_verification: bool = Field(default=False, description="Whether manual verification is required")
