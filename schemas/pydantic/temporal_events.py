from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TemporalSnapshot(BaseModel):
    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    entity_type: str = Field(..., description="Type of entity being snapshotted")
    entity_id: str = Field(..., description="ID of entity being snapshotted")
    snapshot_type: str = Field(..., description="Type of snapshot (state, metrics, configuration)")
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    captured_by: str = Field(..., description="Engine or service that captured snapshot")
    state_data: Dict[str, Any] = Field(default_factory=dict, description="State data at snapshot time")
    metrics_data: Dict[str, Any] = Field(default_factory=dict, description="Metrics data at snapshot time")
    config_data: Dict[str, Any] = Field(default_factory=dict, description="Configuration data at snapshot time")
    version: str = Field(..., description="Version of the entity at snapshot time")
    checksum: Optional[str] = Field(None, description="Checksum for data integrity")
    retention_period: Optional[int] = Field(None, description="Retention period in days")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CausalChainDetected(BaseModel):
    chain_id: str = Field(..., description="Unique chain identifier")
    chain_type: str = Field(..., description="Type of causal chain (success, failure, optimization)")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    detected_by: str = Field(..., description="Engine or service that detected the chain")
    events: List[Dict[str, Any]] = Field(default_factory=list, description="Events in the causal chain")
    root_event_id: str = Field(..., description="ID of the root event")
    leaf_event_id: str = Field(..., description="ID of the leaf event")
    chain_length: int = Field(..., description="Number of events in chain")
    confidence: float = Field(..., description="Confidence score (0-1)")
    impact_assessment: Dict[str, Any] = Field(default_factory=dict, description="Assessment of chain impact")
    actionable: bool = Field(default=True, description="Whether chain is actionable")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested actions based on chain")
    metadata: Dict[str, Any] = Field(default_factory=dict)
