from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class GovernanceRequest(BaseModel):
    request_id: str = Field(..., description="Unique request identifier")
    action_type: str = Field(..., description="Type of action being requested")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Action payload")
    requester: str = Field(..., description="Engine or service making the request")
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    priority: str = Field(default="normal", description="Request priority")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    resource_type: Optional[str] = Field(None, description="Type of resource being acted upon")
    resource_id: Optional[str] = Field(None, description="ID of resource being acted upon")


class GovernanceApproved(BaseModel):
    request_id: str = Field(..., description="Original request ID")
    approved_by: str = Field(..., description="Governance engine ID")
    conditions: List[str] = Field(default_factory=list, description="Approval conditions")
    expires_at: Optional[datetime] = Field(None, description="Approval expiration time")
    approved_at: datetime = Field(default_factory=datetime.utcnow)
    approval_token: str = Field(..., description="Token for executing approved action")
    scope: Dict[str, Any] = Field(default_factory=dict, description="Approved scope limits")


class GovernanceRejected(BaseModel):
    request_id: str = Field(..., description="Original request ID")
    rejected_by: str = Field(..., description="Governance engine ID")
    reason: str = Field(..., description="Reason for rejection")
    rejected_at: datetime = Field(default_factory=datetime.utcnow)
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for modification")
    violation_type: Optional[str] = Field(None, description="Type of governance rule violated")
    can_retry: bool = Field(default=True, description="Whether the request can be retried")


class GovernanceEmergencyStop(BaseModel):
    scope: str = Field(..., description="Scope of stop (all, engine, funnel, action)")
    scope_id: Optional[str] = Field(None, description="ID of scoped entity")
    reason: str = Field(..., description="Reason for emergency stop")
    triggered_by: str = Field(..., description="Engine or user that triggered stop")
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    rollback_plan: Dict[str, Any] = Field(default_factory=dict, description="Rollback plan")
    severity: str = Field(default="critical", description="Severity level")
    affected_entities: List[str] = Field(default_factory=list, description="List of affected entity IDs")


class GovernanceOverride(BaseModel):
    original_request_id: str = Field(..., description="Original request ID that was rejected")
    override_by: str = Field(..., description="Engine or user overriding the decision")
    override_reason: str = Field(..., description="Reason for override")
    override_at: datetime = Field(default_factory=datetime.utcnow)
    override_token: str = Field(..., description="Token for executing overridden action")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Risk assessment")
    requires_approval: bool = Field(default=True, description="Whether override requires additional approval")
