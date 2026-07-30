from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class DLQEventFailed(BaseModel):
    original_event_id: str = Field(..., description="Original event ID")
    original_event_type: str = Field(..., description="Original event type")
    failure_reason: str = Field(..., description="Reason for failure")
    failure_type: str = Field(..., description="Type of failure (validation, processing, timeout)")
    failed_at: datetime = Field(default_factory=datetime.utcnow)
    failed_by: str = Field(..., description="Engine or service that failed to process")
    retry_count: int = Field(default=0, description="Number of retry attempts before DLQ")
    original_payload: Dict[str, Any] = Field(default_factory=dict, description="Original event payload")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed error information")
    queue_name: str = Field(..., description="Queue the event was on")
    priority: int = Field(default=2, description="Original event priority")
    can_replay: bool = Field(default=True, description="Whether event can be replayed")
    replay_conditions: List[str] = Field(default_factory=list, description="Conditions for replay")


class DLQEventReplayed(BaseModel):
    original_event_id: str = Field(..., description="Original event ID from DLQ")
    replayed_by: str = Field(..., description="Engine or service replaying the event")
    replayed_at: datetime = Field(default_factory=datetime.utcnow)
    replay_strategy: str = Field(..., description="Replay strategy (immediate, scheduled, manual)")
    replay_payload: Optional[Dict[str, Any]] = Field(None, description="Modified payload if any")
    replay_success: bool = Field(default=False, description="Whether replay was successful")
    replay_result: Optional[str] = Field(None, description="Result of replay")
    replay_duration_ms: Optional[int] = Field(None, description="Replay duration in milliseconds")
    error_if_failed: Optional[str] = Field(None, description="Error if replay failed")
