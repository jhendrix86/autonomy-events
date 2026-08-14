from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from severity import Severity


class KGEentityCreated(BaseModel):
    entity_type: str = Field(..., description="Type of entity (user, product, funnel, niche, etc.)")
    entity_id: str = Field(..., description="Unique entity identifier")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Entity attributes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Engine or service that created the entity")
    source: str = Field(..., description="Data source")
    confidence: float = Field(default=1.0, description="Confidence score (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KGRelationshipCreated(BaseModel):
    from_entity_type: str = Field(..., description="Type of source entity")
    from_entity_id: str = Field(..., description="ID of source entity")
    to_entity_type: str = Field(..., description="Type of target entity")
    to_entity_id: str = Field(..., description="ID of target entity")
    relationship_type: str = Field(..., description="Type of relationship")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Relationship attributes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Engine or service that created the relationship")
    weight: float = Field(default=1.0, description="Relationship weight")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KGPatternDetected(BaseModel):
    pattern_type: str = Field(..., description="Type of pattern detected")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Entities involved in pattern")
    confidence: float = Field(..., description="Confidence score (0-1)")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    detected_by: str = Field(..., description="Engine or service that detected the pattern")
    pattern_data: Dict[str, Any] = Field(default_factory=dict, description="Pattern-specific data")
    actionable: bool = Field(default=True, description="Whether pattern is actionable")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested actions based on pattern")


class KGInsightGenerated(BaseModel):
    insight_type: str = Field(..., description="Type of insight (market, performance, risk, opportunity)")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Entities the insight relates to")
    value: str = Field(..., description="Insight description")
    source: str = Field(..., description="Source of insight (analysis, pattern, external)")
    confidence: float = Field(..., description="Confidence score (0-1)")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field(..., description="Engine or service that generated the insight")
    impact_assessment: Dict[str, Any] = Field(default_factory=dict, description="Assessment of potential impact")
    priority: str = Field(default="normal", description="Insight priority")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KGAnomalyDetected(BaseModel):
    anomaly_type: str = Field(..., description="Type of anomaly (performance, behavior, data)")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Entities affected by anomaly")
    severity: Severity = Field(..., description="Severity level")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    detected_by: str = Field(..., description="Engine or service that detected the anomaly")
    anomaly_data: Dict[str, Any] = Field(default_factory=dict, description="Anomaly-specific data")
    expected_value: Optional[Any] = Field(None, description="Expected value")
    actual_value: Optional[Any] = Field(None, description="Actual value")
    deviation: Optional[float] = Field(None, description="Deviation from expected")
    requires_investigation: bool = Field(default=True, description="Whether anomaly requires investigation")
