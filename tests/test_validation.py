import pytest
from envelope import EventEnvelope
from utils import EventValidator, ValidationError


class TestEventValidator:
    def test_validate_envelope_valid(self):
        envelope = EventEnvelope(
            event_type="funnel.created",
            engine_id="engine-1",
            payload={"funnel_id": "test-123"}
        )
        
        errors = EventValidator.validate_envelope(envelope)
        assert len(errors) == 0
    
    def test_validate_envelope_missing_event_id(self):
        envelope = EventEnvelope(
            event_id="",
            event_type="funnel.created",
            engine_id="engine-1"
        )
        
        errors = EventValidator.validate_envelope(envelope)
        assert len(errors) > 0
        assert any("event_id" in e.message for e in errors)
    
    def test_validate_envelope_invalid_event_type_format(self):
        envelope = EventEnvelope(
            event_type="invalid",
            engine_id="engine-1"
        )
        
        errors = EventValidator.validate_envelope(envelope)
        assert len(errors) > 0
        assert any("dot notation" in e.message for e in errors)
    
    def test_validate_envelope_invalid_priority(self):
        envelope = EventEnvelope(
            event_type="funnel.created",
            engine_id="engine-1",
            priority=5
        )
        
        errors = EventValidator.validate_envelope(envelope)
        assert len(errors) > 0
        assert any("priority" in e.message for e in errors)
    
    def test_validate_payload_valid(self):
        payload = {
            "funnel_id": "test-123",
            "niche": "fitness",
            "strategy": "content_first",
            "created_by": "engine-1"
        }
        
        errors = EventValidator.validate_payload("funnel.created", payload)
        assert len(errors) == 0
    
    def test_validate_payload_missing_required_field(self):
        payload = {
            "funnel_id": "test-123",
            "niche": "fitness"
        }
        
        errors = EventValidator.validate_payload("funnel.created", payload)
        assert len(errors) > 0
    
    def test_validate_payload_unknown_event_type(self):
        payload = {"test": "data"}
        
        errors = EventValidator.validate_payload("unknown.event", payload)
        assert len(errors) > 0
        assert any("Unknown event type" in e.message for e in errors)
    
    def test_validate_event_valid(self):
        envelope = EventEnvelope(
            event_type="funnel.created",
            engine_id="engine-1",
            payload={
                "funnel_id": "test-123",
                "niche": "fitness",
                "strategy": "content_first",
                "created_by": "engine-1"
            }
        )
        
        errors = EventValidator.validate_event(envelope)
        assert len(errors) == 0
    
    def test_validate_event_invalid(self):
        envelope = EventEnvelope(
            event_type="funnel.created",
            engine_id="engine-1",
            payload={"invalid": "data"}
        )
        
        errors = EventValidator.validate_event(envelope)
        assert len(errors) > 0
    
    def test_is_valid_true(self):
        envelope = EventEnvelope(
            event_type="funnel.created",
            engine_id="engine-1",
            payload={
                "funnel_id": "test-123",
                "niche": "fitness",
                "strategy": "content_first",
                "created_by": "engine-1"
            }
        )
        
        assert EventValidator.is_valid(envelope) is True
    
    def test_is_valid_false(self):
        envelope = EventEnvelope(
            event_type="funnel.created",
            engine_id="engine-1",
            payload={"invalid": "data"}
        )
        
        assert EventValidator.is_valid(envelope) is False
    
    def test_get_schema_for_event(self):
        schema = EventValidator.get_schema_for_event("funnel.created")
        assert schema is not None
    
    def test_get_schema_for_unknown_event(self):
        schema = EventValidator.get_schema_for_event("unknown.event")
        assert schema is None
