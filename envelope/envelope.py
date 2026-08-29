from datetime import datetime
from enum import IntEnum
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, validator
from uuid import uuid4


class EventPriority(IntEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(..., description="Type of the event (e.g., funnel.created)")
    version: str = Field(default="1.0.0", description="Event schema version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")
    causation_id: Optional[str] = Field(None, description="Causation ID for event chain")
    engine_id: str = Field(..., description="ID of the engine producing the event")
    priority: int = Field(default=EventPriority.NORMAL, description="Event priority")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator("priority")
    def validate_priority(cls, v):
        if not isinstance(v, int) or v < 1 or v > 4:
            raise ValueError("Priority must be between 1 (LOW) and 4 (CRITICAL)")
        return v

    @validator("retry_count")
    def validate_retry_count(cls, v):
        if v < 0:
            raise ValueError("Retry count cannot be negative")
        return v

    @validator("event_type")
    def validate_event_type(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Event type must be a non-empty string")
        if "." not in v:
            raise ValueError("Event type must use dot notation (e.g., funnel.created)")
        return v.lower()

    def to_dict(self) -> Dict[str, Any]:
        # mode="json" so datetime -> ISO string, UUID -> str, Enum -> value:
        # every caller of this immediately json.dumps() the result (publisher,
        # consumer, dlq_manager), and a bare .dict() keeps datetime objects
        # that json.dumps can't encode - which broke real (non-mocked)
        # publishing entirely. from_dict() re-parses the ISO strings fine.
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventEnvelope":
        return cls(**data)

    def increment_retry(self) -> "EventEnvelope":
        self.retry_count += 1
        return self

    def with_correlation(self, correlation_id: str) -> "EventEnvelope":
        self.correlation_id = correlation_id
        return self

    def with_causation(self, causation_id: str) -> "EventEnvelope":
        self.causation_id = causation_id
        return self
