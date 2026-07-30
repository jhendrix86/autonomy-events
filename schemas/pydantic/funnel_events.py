from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class FunnelCreated(BaseModel):
    funnel_id: str = Field(..., description="Unique funnel identifier")
    niche: str = Field(..., description="Target niche")
    strategy: str = Field(..., description="Funnel strategy type")
    governance_status: str = Field(default="pending", description="Governance approval status")
    product_id: Optional[str] = Field(None, description="Associated product ID")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    channels: List[str] = Field(default_factory=list, description="Traffic channels")
    created_by: str = Field(..., description="Engine or user that created the funnel")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FunnelApproved(BaseModel):
    funnel_id: str = Field(..., description="Funnel identifier")
    approved_by: str = Field(..., description="Governance engine ID")
    conditions: List[str] = Field(default_factory=list, description="Approval conditions")
    expires_at: Optional[datetime] = Field(None, description="Approval expiration")
    approval_reason: str = Field(..., description="Reason for approval")


class FunnelLaunched(BaseModel):
    funnel_id: str = Field(..., description="Funnel identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    channels: List[str] = Field(..., description="Active traffic channels")
    launch_config: Dict[str, Any] = Field(default_factory=dict, description="Launch configuration")
    launched_by: str = Field(..., description="Engine that launched the funnel")


class FunnelMetrics(BaseModel):
    funnel_id: str = Field(..., description="Funnel identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    period_start: datetime = Field(..., description="Metrics period start")
    period_end: datetime = Field(..., description="Metrics period end")
    visitors: int = Field(default=0, description="Unique visitors")
    leads: int = Field(default=0, description="Leads captured")
    conversions: int = Field(default=0, description="Conversions")
    revenue: float = Field(default=0.0, description="Revenue generated")
    conversion_rate: float = Field(default=0.0, description="Conversion rate")
    cost: float = Field(default=0.0, description="Total cost")
    roi: float = Field(default=0.0, description="Return on investment")
    channel_metrics: Dict[str, Any] = Field(default_factory=dict, description="Per-channel metrics")
    custom_metrics: Dict[str, Any] = Field(default_factory=dict, description="Custom metrics")


class FunnelInsights(BaseModel):
    funnel_id: str = Field(..., description="Funnel identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    patterns: List[Dict[str, Any]] = Field(default_factory=list, description="Detected patterns")
    predictions: Dict[str, Any] = Field(default_factory=dict, description="Predictive insights")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    confidence: float = Field(default=0.0, description="Confidence score (0-1)")
    insight_type: str = Field(..., description="Type of insight (performance, optimization, risk)")


class FunnelMutation(BaseModel):
    funnel_id: str = Field(..., description="Funnel identifier")
    mutation_type: str = Field(..., description="Type of mutation (optimize, replicate, transform)")
    reason: str = Field(..., description="Reason for mutation")
    expected_impact: Dict[str, Any] = Field(default_factory=dict, description="Expected impact metrics")
    mutation_config: Dict[str, Any] = Field(default_factory=dict, description="Mutation configuration")
    requested_by: str = Field(..., description="Engine requesting mutation")
    source_funnel_id: Optional[str] = Field(None, description="Source funnel if replicating")


class FunnelArchived(BaseModel):
    funnel_id: str = Field(..., description="Funnel identifier")
    reason: str = Field(..., description="Reason for archiving")
    final_metrics: Dict[str, Any] = Field(default_factory=dict, description="Final performance metrics")
    archived_at: datetime = Field(default_factory=datetime.utcnow)
    archived_by: str = Field(..., description="Engine that archived the funnel")
    retention_period: Optional[int] = Field(None, description="Retention period in days")
