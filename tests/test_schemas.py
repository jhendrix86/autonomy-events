import pytest
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


class TestFunnelEvents:
    def test_funnel_created(self):
        event = FunnelCreated(
            funnel_id="test-123",
            niche="fitness",
            strategy="content_first",
            created_by="autonomous-engine"
        )
        
        assert event.funnel_id == "test-123"
        assert event.niche == "fitness"
        assert event.governance_status == "pending"
    
    def test_funnel_approved(self):
        event = FunnelApproved(
            funnel_id="test-123",
            approved_by="governance-engine",
            approval_reason="Meets all quality standards"
        )
        
        assert event.funnel_id == "test-123"
        assert event.approved_by == "governance-engine"
    
    def test_funnel_metrics(self):
        event = FunnelMetrics(
            funnel_id="test-123",
            period_start="2024-01-01T00:00:00",
            period_end="2024-01-02T00:00:00",
            visitors=1000,
            leads=100,
            conversions=10,
            revenue=1000.0
        )
        
        assert event.conversion_rate == 0.01
        assert event.roi == 0.0


class TestGovernanceEvents:
    def test_governance_request(self):
        event = GovernanceRequest(
            request_id="req-123",
            action_type="create_funnel",
            requester="autonomous-engine",
            payload={"funnel_config": {}}
        )
        
        assert event.request_id == "req-123"
        assert event.action_type == "create_funnel"
    
    def test_governance_approved(self):
        event = GovernanceApproved(
            request_id="req-123",
            approved_by="governance-engine",
            approval_token="token-123"
        )
        
        assert event.request_id == "req-123"
        assert event.approved_by == "governance-engine"
    
    def test_governance_rejected(self):
        event = GovernanceRejected(
            request_id="req-123",
            rejected_by="governance-engine",
            reason="Violates brand guidelines"
        )
        
        assert event.can_retry is True


class TestKGEvents:
    def test_kg_entity_created(self):
        event = KGEentityCreated(
            entity_type="user",
            entity_id="user-123",
            created_by="orchestrator",
            source="gumroad"
        )
        
        assert event.entity_type == "user"
        assert event.confidence == 1.0
    
    def test_kg_pattern_detected(self):
        event = KGPatternDetected(
            pattern_type="high_conversion",
            entities=[{"type": "funnel", "id": "funnel-1"}],
            confidence=0.85,
            detected_by="intelligence-engine"
        )
        
        assert event.actionable is True
        assert len(event.suggested_actions) == 0


class TestSafetyEvents:
    def test_safety_violation_detected(self):
        event = SafetyViolationDetected(
            violation_type="brand_guideline",
            severity="high",
            violated_rule="no_profanity",
            entity_type="content",
            entity_id="content-123",
            detected_by="governance-engine"
        )
        
        assert event.requires_immediate_action is False
    
    def test_safety_blocked_action(self):
        event = SafetyBlockedAction(
            action_type="publish_content",
            blocked_by="governance-engine",
            reason="Violates compliance rules",
            requester="autonomous-engine"
        )
        
        assert event.can_override is False


class TestHealthEvents:
    def test_engine_health_report(self):
        event = EngineHealthReport(
            engine_id="engine-1",
            engine_type="core",
            status="healthy"
        )
        
        assert event.status == "healthy"
        assert event.uptime_seconds == 0
    
    def test_engine_degraded(self):
        event = EngineDegraded(
            engine_id="engine-1",
            degradation_type="performance",
            severity="medium",
            detected_by="monitoring"
        )
        
        assert event.auto_recovery_enabled is True


class TestFailureEvents:
    def test_failure_detected(self):
        event = FailureDetected(
            failure_id="fail-123",
            failure_type="processing",
            severity="high",
            component="orchestrator",
            error_message="Timeout error"
        )
        
        assert event.is_retriable is True
        assert event.requires_manual_intervention is False
    
    def test_failure_retry_scheduled(self):
        event = FailureRetryScheduled(
            failure_id="fail-123",
            retry_attempt=1,
            max_retries=3,
            retry_strategy="exponential"
        )
        
        assert event.retry_attempt == 1


class TestDLQEvents:
    def test_dlq_event_failed(self):
        event = DLQEventFailed(
            original_event_id="event-123",
            original_event_type="funnel.created",
            failure_reason="Validation failed",
            failure_type="validation",
            failed_by="consumer",
            queue_name="funnel-queue"
        )
        
        assert event.can_replay is True
        assert event.retry_count == 0


class TestTemporalEvents:
    def test_temporal_snapshot(self):
        event = TemporalSnapshot(
            snapshot_id="snap-123",
            entity_type="funnel",
            entity_id="funnel-123",
            snapshot_type="state",
            captured_by="orchestrator",
            version="1.0.0"
        )
        
        assert event.snapshot_type == "state"
    
    def test_causal_chain_detected(self):
        event = CausalChainDetected(
            chain_id="chain-123",
            chain_type="success",
            events=["event-1", "event-2"],
            root_event_id="event-1",
            leaf_event_id="event-2",
            chain_length=2,
            confidence=0.9,
            detected_by="intelligence-engine"
        )
        
        assert event.actionable is True
