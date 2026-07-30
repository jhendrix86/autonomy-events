from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class FailureDetected(BaseModel):
    failure_id: str = Field(..., description="Unique failure identifier")
    failure_type: str = Field(..., description="Type of failure (processing, network, validation, system)")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    component: str = Field(..., description="Component where failure occurred")
    error_message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code if available")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    detected_by: str = Field(..., description="Engine or service that detected failure")
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")
    context: Dict[str, Any] = Field(default_factory=dict, description="Failure context")
    affected_operations: List[str] = Field(default_factory=list, description="Operations affected by failure")
    is_retriable: bool = Field(default=True, description="Whether failure is retriable")
    requires_manual_intervention: bool = Field(default=False, description="Whether manual intervention is required")


class FailureRecovered(BaseModel):
    failure_id: str = Field(..., description="Original failure identifier")
    recovery_type: str = Field(..., description="Type of recovery (retry, fallback, manual, fix)")
    recovered_at: datetime = Field(default_factory=datetime.utcnow)
    recovered_by: str = Field(..., description="Engine or service that recovered from failure")
    recovery_actions: List[str] = Field(default_factory=list, description="Actions taken to recover")
    downtime_seconds: int = Field(default=0, description="Total downtime in seconds")
    data_loss: bool = Field(default=False, description="Whether there was data loss")
    root_cause: Optional[str] = Field(None, description="Root cause if identified")
    preventive_measures: List[str] = Field(default_factory=list, description="Preventive measures implemented")
    requires_monitoring: bool = Field(default=True, description="Whether continued monitoring is required")


class FailureRetryScheduled(BaseModel):
    failure_id: str = Field(..., description="Original failure identifier")
    retry_attempt: int = Field(..., description="Retry attempt number")
    max_retries: int = Field(..., description="Maximum retry attempts")
    scheduled_at: datetime = Field(default_factory=datetime.utcnow)
    retry_at: datetime = Field(..., description="When retry is scheduled")
    retry_strategy: str = Field(..., description="Retry strategy (exponential, linear, fixed)")
    backoff_seconds: int = Field(default=0, description="Backoff duration in seconds")
    scheduled_by: str = Field(..., description="Engine or service scheduling retry")
    original_payload: Dict[str, Any] = Field(default_factory=dict, description="Original payload to retry")
    retry_context: Dict[str, Any] = Field(default_factory=dict, description="Retry-specific context")
