from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from severity import Severity


class SafetyViolationDetected(BaseModel):
    violation_type: str = Field(..., description="Type of safety violation")
    severity: Severity = Field(..., description="Severity level")
    violated_rule: str = Field(..., description="The rule that was violated")
    entity_type: str = Field(..., description="Type of entity that caused violation")
    entity_id: str = Field(..., description="ID of entity that caused violation")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    detected_by: str = Field(..., description="Engine or service that detected violation")
    violation_data: Dict[str, Any] = Field(default_factory=dict, description="Violation-specific data")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context of violation")
    requires_immediate_action: bool = Field(default=False, description="Whether immediate action is required")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested remediation actions")


class SafetyBlockedAction(BaseModel):
    action_type: str = Field(..., description="Type of action that was blocked")
    blocked_by: str = Field(..., description="Safety rule or engine that blocked the action")
    reason: str = Field(..., description="Reason for blocking")
    requester: str = Field(..., description="Engine or service that attempted the action")
    blocked_at: datetime = Field(default_factory=datetime.utcnow)
    action_payload: Dict[str, Any] = Field(default_factory=dict, description="Original action payload")
    violation_type: Optional[str] = Field(None, description="Type of violation if applicable")
    can_override: bool = Field(default=False, description="Whether action can be overridden")
    override_requirements: List[str] = Field(default_factory=list, description="Requirements for override")


class SafetyRollbackTriggered(BaseModel):
    rollback_type: str = Field(..., description="Type of rollback (full, partial, state)")
    triggered_by: str = Field(..., description="Engine or service that triggered rollback")
    reason: str = Field(..., description="Reason for rollback")
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    scope: Dict[str, Any] = Field(default_factory=dict, description="Rollback scope")
    rollback_plan: Dict[str, Any] = Field(default_factory=dict, description="Rollback execution plan")
    affected_entities: List[str] = Field(default_factory=list, description="List of affected entity IDs")
    previous_state: Optional[Dict[str, Any]] = Field(None, description="Previous state if available")
    estimated_duration: Optional[int] = Field(None, description="Estimated rollback duration in seconds")
    requires_manual_intervention: bool = Field(default=False, description="Whether manual intervention is required")
