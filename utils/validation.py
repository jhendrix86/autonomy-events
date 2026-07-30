from typing import Dict, Any, Optional, List
from pydantic import ValidationError as PydanticValidationError
from envelope import EventEnvelope
from schemas.pydantic import (
    FunnelCreated, FunnelApproved, FunnelLaunched, FunnelMetrics,
    FunnelInsights, FunnelMutation, FunnelArchived,
    GovernanceRequest, GovernanceApproved, GovernanceRejected,
    GovernanceEmergencyStop, GovernanceOverride,
    KGEentityCreated, KGRelationshipCreated, KGPatternDetected,
    KGInsightGenerated, KGAnomalyDetected,
    SafetyViolationDetected, SafetyBlockedAction, SafetyRollbackTriggered,
    EngineHealthReport, EngineDegraded, EngineRecovered,
    FailureDetected, FailureRecovered, FailureRetryScheduled,
    DLQEventFailed, DLQEventReplayed,
    TemporalSnapshot, CausalChainDetected,
)


class ValidationError(Exception):
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class EventValidator:
    """Validates events against their schemas."""
    
    SCHEMA_MAPPING = {
        "funnel.created": FunnelCreated,
        "funnel.approved": FunnelApproved,
        "funnel.launched": FunnelLaunched,
        "funnel.metrics": FunnelMetrics,
        "funnel.insights": FunnelInsights,
        "funnel.mutation": FunnelMutation,
        "funnel.archived": FunnelArchived,
        "governance.request": GovernanceRequest,
        "governance.approved": GovernanceApproved,
        "governance.rejected": GovernanceRejected,
        "governance.emergency_stop": GovernanceEmergencyStop,
        "governance.override": GovernanceOverride,
        "kg.entity_created": KGEentityCreated,
        "kg.relationship_created": KGRelationshipCreated,
        "kg.pattern_detected": KGPatternDetected,
        "kg.insight_generated": KGInsightGenerated,
        "kg.anomaly_detected": KGAnomalyDetected,
        "safety.violation_detected": SafetyViolationDetected,
        "safety.blocked_action": SafetyBlockedAction,
        "safety.rollback_triggered": SafetyRollbackTriggered,
        "engine.health_report": EngineHealthReport,
        "engine.degraded": EngineDegraded,
        "engine.recovered": EngineRecovered,
        "failure.detected": FailureDetected,
        "failure.recovered": FailureRecovered,
        "failure.retry_scheduled": FailureRetryScheduled,
        "dlq.event_failed": DLQEventFailed,
        "dlq.event_replayed": DLQEventReplayed,
        "temporal.snapshot": TemporalSnapshot,
        "causal.chain_detected": CausalChainDetected,
    }
    
    @classmethod
    def validate_envelope(cls, envelope: EventEnvelope) -> List[ValidationError]:
        """Validate the event envelope structure."""
        errors = []
        
        if not envelope.event_id:
            errors.append(ValidationError("event_id is required"))
        
        if not envelope.event_type:
            errors.append(ValidationError("event_type is required"))
        elif "." not in envelope.event_type:
            errors.append(ValidationError("event_type must use dot notation"))
        
        if not envelope.version:
            errors.append(ValidationError("version is required"))
        
        if not envelope.engine_id:
            errors.append(ValidationError("engine_id is required"))
        
        if envelope.priority < 1 or envelope.priority > 4:
            errors.append(ValidationError("priority must be between 1 and 4"))
        
        if envelope.retry_count < 0:
            errors.append(ValidationError("retry_count cannot be negative"))
        
        return errors
    
    @classmethod
    def validate_payload(cls, event_type: str, payload: Dict[str, Any]) -> List[ValidationError]:
        """Validate the event payload against its schema."""
        errors = []
        
        schema_class = cls.SCHEMA_MAPPING.get(event_type)
        if not schema_class:
            errors.append(ValidationError(f"Unknown event type: {event_type}"))
            return errors
        
        try:
            schema_class(**payload)
        except PydanticValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append(ValidationError(error["msg"], field))
        
        return errors
    
    @classmethod
    def validate_event(cls, envelope: EventEnvelope) -> List[ValidationError]:
        """Validate both envelope and payload."""
        errors = cls.validate_envelope(envelope)
        
        if not errors:
            payload_errors = cls.validate_payload(envelope.event_type, envelope.payload)
            errors.extend(payload_errors)
        
        return errors
    
    @classmethod
    def is_valid(cls, envelope: EventEnvelope) -> bool:
        """Quick check if event is valid."""
        return len(cls.validate_event(envelope)) == 0
    
    @classmethod
    def get_schema_for_event(cls, event_type: str):
        """Get the Pydantic schema class for an event type."""
        return cls.SCHEMA_MAPPING.get(event_type)
