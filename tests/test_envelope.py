import pytest
from datetime import datetime
from envelope import EventEnvelope, EventPriority


class TestEventEnvelope:
    def test_create_envelope(self):
        envelope = EventEnvelope(
            event_type="funnel.created",
            engine_id="engine-1",
            payload={"funnel_id": "test-123"}
        )
        
        assert envelope.event_type == "funnel.created"
        assert envelope.engine_id == "engine-1"
        assert envelope.payload == {"funnel_id": "test-123"}
        assert envelope.priority == EventPriority.NORMAL
        assert envelope.retry_count == 0
        assert envelope.event_id is not None
        assert isinstance(envelope.timestamp, datetime)
    
    def test_envelope_validation_invalid_event_type(self):
        with pytest.raises(ValueError, match="Event type must use dot notation"):
            EventEnvelope(
                event_type="invalid",
                engine_id="engine-1"
            )
    
    def test_envelope_validation_invalid_priority(self):
        with pytest.raises(ValueError, match="Priority must be between 1 and 4"):
            EventEnvelope(
                event_type="funnel.created",
                engine_id="engine-1",
                priority=5
            )
    
    def test_envelope_validation_invalid_retry_count(self):
        with pytest.raises(ValueError, match="Retry count cannot be negative"):
            EventEnvelope(
                event_type="funnel.created",
                engine_id="engine-1",
                retry_count=-1
            )
    
    def test_envelope_to_dict(self):
        envelope = EventEnvelope(
            event_type="funnel.created",
            engine_id="engine-1",
            payload={"test": "data"}
        )
        
        data = envelope.to_dict()
        assert data["event_type"] == "funnel.created"
        assert data["engine_id"] == "engine-1"
        assert data["payload"] == {"test": "data"}
    
    def test_envelope_from_dict(self):
        data = {
            "event_id": "test-id",
            "event_type": "funnel.created",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": None,
            "causation_id": None,
            "engine_id": "engine-1",
            "priority": 2,
            "retry_count": 0,
            "payload": {"test": "data"},
            "metadata": {}
        }
        
        envelope = EventEnvelope.from_dict(data)
        assert envelope.event_id == "test-id"
        assert envelope.event_type == "funnel.created"
    
    def test_increment_retry(self):
        envelope = EventEnvelope(
            event_type="funnel.created",
            engine_id="engine-1",
            retry_count=0
        )
        
        envelope.increment_retry()
        assert envelope.retry_count == 1
        
        envelope.increment_retry()
        assert envelope.retry_count == 2
    
    def test_with_correlation(self):
        envelope = EventEnvelope(
            event_type="funnel.created",
            engine_id="engine-1"
        )
        
        envelope.with_correlation("corr-123")
        assert envelope.correlation_id == "corr-123"
    
    def test_with_causation(self):
        envelope = EventEnvelope(
            event_type="funnel.created",
            engine_id="engine-1"
        )
        
        envelope.with_causation("cause-123")
        assert envelope.causation_id == "cause-123"
    
    def test_priority_enum(self):
        assert EventPriority.LOW == 1
        assert EventPriority.NORMAL == 2
        assert EventPriority.HIGH == 3
        assert EventPriority.CRITICAL == 4
