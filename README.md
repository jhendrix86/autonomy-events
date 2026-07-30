# autonomy-events

Production-grade shared event library for the Autonomous Company OS. This library provides the universal event language used across all engines and services in the autonomous system.

## Features

- **Universal Event Envelope** - Standardized wrapper for all events with metadata
- **Event Schemas** - Pydantic and Protobuf schemas for all event types
- **Schema Registry** - Version management with compatibility checking
- **Event Publisher** - Retry logic, DLQ fallback, tracing, metrics
- **Event Consumer** - Validation, tracing, DLQ routing, manual/auto ack
- **Distributed Tracing** - W3C traceparent support with correlation/causation IDs
- **DLQ Management** - Dead letter queue with replay capabilities
- **Metrics** - Built-in metrics emission for observability
- **Validation** - Pydantic-based event validation

## Installation

```bash
pip install autonomy-events
```

Or for development:

```bash
git clone https://github.com/autonomous-company/autonomy-events.git
cd autonomy-events
pip install -e ".[dev]"
```

## Quick Start

### Publishing Events

```python
import asyncio
from envelope import EventEnvelope, EventPriority
from publisher import EventPublisher
from tracing import Tracer

async def main():
    # Create publisher
    publisher = EventPublisher(
        rabbitmq_url="amqp://localhost:5672",
        exchange_name="autonomy.events"
    )
    
    # Create tracer
    tracer = Tracer("my-service")
    
    # Start trace
    trace_parent = tracer.start_span("create_funnel")
    
    # Create event envelope
    envelope = EventEnvelope(
        event_type="funnel.created",
        engine_id="autonomous-growth-engine",
        priority=EventPriority.HIGH,
        payload={
            "funnel_id": "funnel-123",
            "niche": "fitness",
            "strategy": "content_first",
            "created_by": "autonomous-engine"
        }
    )
    
    # Publish event
    async with publisher:
        result = await publisher.publish(
            envelope,
            routing_key="funnel.created",
            trace_parent=trace_parent
        )
        
        if result.success:
            print(f"Event published: {result.message_id}")
        else:
            print(f"Publish failed: {result.error}")

asyncio.run(main())
```

### Consuming Events

```python
import asyncio
from consumer import EventConsumer, ConsumeResult
from envelope import EventEnvelope
from tracing import Tracer

async def handle_funnel_created(
    envelope: EventEnvelope,
    trace_parent
) -> ConsumeResult:
    """Handle funnel.created events."""
    print(f"Processing funnel: {envelope.payload['funnel_id']}")
    
    # Process the event
    # ...
    
    return ConsumeResult(
        success=True,
        event_id=envelope.event_id,
        event_type=envelope.event_type,
        should_ack=True
    )

async def main():
    # Create consumer
    consumer = EventConsumer(
        rabbitmq_url="amqp://localhost:5672",
        queue_name="funnel-events",
        routing_keys=["funnel.*"],
        tracer=Tracer("my-service")
    )
    
    # Register handler
    consumer.register_handler("funnel.created", handle_funnel_created)
    
    # Start consuming
    async with consumer:
        await consumer.start_consuming()

asyncio.run(main())
```

## Event Types

### Core Funnel Events

- `funnel.created` - A new funnel has been created
- `funnel.approved` - Funnel approved by governance
- `funnel.launched` - Funnel has been launched
- `funnel.metrics` - Funnel performance metrics
- `funnel.insights` - AI-generated insights about funnel
- `funnel.mutation` - Funnel is being mutated
- `funnel.archived` - Funnel has been archived

### Governance Events

- `governance.request` - Request for governance approval
- `governance.approved` - Request approved
- `governance.rejected` - Request rejected
- `governance.emergency_stop` - Emergency stop triggered
- `governance.override` - Governance override

### Knowledge Graph Events

- `kg.entity_created` - Entity created in knowledge graph
- `kg.relationship_created` - Relationship created
- `kg.pattern_detected` - Pattern detected in data
- `kg.insight_generated` - Insight generated
- `kg.anomaly_detected` - Anomaly detected

### Safety Events

- `safety.violation_detected` - Safety rule violation
- `safety.blocked_action` - Action blocked by safety rules
- `safety.rollback_triggered` - Rollback triggered

### Health Events

- `engine.health_report` - Engine health status
- `engine.degraded` - Engine performance degraded
- `engine.recovered` - Engine recovered from degradation

### Failure Events

- `failure.detected` - Failure detected
- `failure.recovered` - Failure recovered
- `failure.retry_scheduled` - Retry scheduled

### DLQ Events

- `dlq.event_failed` - Event sent to DLQ
- `dlq.event_replayed` - Event replayed from DLQ

### Temporal Events

- `temporal.snapshot` - Temporal snapshot of state
- `causal.chain_detected` - Causal chain detected

## Configuration

Configuration can be set via environment variables or a Config object:

```python
from utils import Config

# From environment variables
config = Config.from_env()

# From dictionary
config = Config.from_dict({
    "rabbitmq_url": "amqp://localhost:5672",
    "max_retries": 5,
    "dlq_enabled": True
})

# Direct instantiation
config = Config(
    rabbitmq_url="amqp://localhost:5672",
    max_retries=5,
    retry_enabled=True
)
```

### Environment Variables

- `RABBITMQ_URL` - RabbitMQ connection URL (default: `amqp://localhost:5672`)
- `MAX_RETRIES` - Maximum retry attempts (default: `3`)
- `DLQ_ENABLED` - Enable dead letter queue (default: `true`)
- `TRACING_ENABLED` - Enable distributed tracing (default: `true`)
- `SCHEMA_VALIDATION_ENABLED` - Enable schema validation (default: `true`)
- `METRICS_ENABLED` - Enable metrics (default: `true`)

## Schema Registry

The schema registry manages event schema versions and compatibility:

```python
from registry import SchemaRegistry, CompatibilityMode

registry = SchemaRegistry(storage_path="./schemas/registry")

# Register a schema
registry.register_schema(
    event_type="funnel.created",
    version="1.0.0",
    schema_definition={
        "type": "object",
        "properties": {
            "funnel_id": {"type": "string"},
            "niche": {"type": "string"}
        },
        "required": ["funnel_id", "niche"]
    },
    compatibility_mode=CompatibilityMode.FULL
)

# Get a schema
schema = registry.get_schema("funnel.created", "1.0.0")

# Validate an event
is_valid = registry.validate_event("funnel.created", event_data)

# List versions
versions = registry.list_versions("funnel.created")

# Deprecate a schema
registry.deprecate_schema("funnel.created", "1.0.0")
```

## Distributed Tracing

Full W3C traceparent support for distributed tracing:

```python
from tracing import Tracer, TraceParent

tracer = Tracer("my-service")

# Start a new trace
trace_parent = tracer.start_span("operation_name")

# Create child span
child_trace = tracer.start_span("child_operation", parent=trace_parent)

# Extract from incoming headers
incoming_headers = {"traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"}
trace_parent = tracer.extract_headers(incoming_headers)

# Inject into outgoing headers
outgoing_headers = tracer.inject_headers(trace_parent)

# Finish span
tracer.finish_span(trace_parent, "operation_name", success=True, duration_ms=100.0)
```

## DLQ Management

Manage dead letter queue operations:

```python
from dlq import DLQManager

async def main():
    dlq = DLQManager(
        rabbitmq_url="amqp://localhost:5672",
        dlq_queue_name="funnel-events.dlq"
    )
    
    async with dlq:
        # Get message count
        count = await dlq.get_message_count()
        
        # Peek at messages
        messages = await dlq.peek_messages(limit=10)
        
        # Replay a specific message
        success = await dlq.replay_message(original_event_id="event-123")
        
        # Replay batch
        result = await dlq.replay_batch(limit=100, event_type_filter="funnel.created")
        
        # Purge old messages
        purged = await dlq.purge_old_messages(age_hours=24)
        
        # Get statistics
        stats = await dlq.get_statistics()

asyncio.run(main())
```

## Metrics

Built-in metrics for observability:

```python
from utils import MetricsEmitter, Timer

metrics = MetricsEmitter()

# Counters
metrics.increment("events.published", tags={"event_type": "funnel.created"})
metrics.decrement("queue.depth", tags={"queue": "funnel"})

# Gauges
metrics.gauge("cpu.usage", 75.5)

# Timing
with Timer(metrics, "operation.duration"):
    # Do work
    pass

# Histogram
metrics.histogram("response_time", 150.5)

# Get stats
stats = metrics.get_histogram_stats("response_time")
print(f"P95: {stats['p95']}ms")

# Get all metrics
all_metrics = metrics.get_all_metrics()
```

## Validation

Validate events against schemas:

```python
from utils import EventValidator
from envelope import EventEnvelope

validator = EventValidator()

# Validate envelope
envelope = EventEnvelope(event_type="funnel.created", engine_id="engine-1")
errors = validator.validate_envelope(envelope)

# Validate payload
payload = {"funnel_id": "test", "niche": "fitness"}
errors = validator.validate_payload("funnel.created", payload)

# Validate entire event
errors = validator.validate_event(envelope)

# Quick check
is_valid = validator.is_valid(envelope)
```

## Protobuf Schemas

Protobuf schemas are provided in `schemas/protobuf/events.proto`. To generate Python code:

```bash
protoc --python_out=. schemas/protobuf/events.proto
```

## Testing

Run tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=autonomy_events --cov-report=html
```

## Architecture

```
autonomy-events/
├── envelope/           # Event envelope implementation
├── schemas/
│   ├── pydantic/       # Pydantic event schemas
│   └── protobuf/       # Protobuf event schemas
├── publisher/          # Event publisher
├── consumer/           # Event consumer
├── registry/           # Schema registry
├── tracing/           # Distributed tracing
├── dlq/               # Dead letter queue management
├── utils/             # Validation, metrics, config
└── tests/             # Test suite
```

## Event Flow

```
┌─────────────┐    Publish    ┌──────────────┐    Consume    ┌─────────────┐
│   Engine    │ ────────────> │  RabbitMQ    │ ────────────> │   Engine    │
│  (Publisher)│               │  (Exchange)  │               │ (Consumer)  │
└─────────────┘               └──────────────┘               └─────────────┘
       │                           │                           │
       │                           ▼                           │
       │                    ┌──────────────┐                  │
       │                    │      DLQ     │                  │
       │                    │  (On Failure)│                  │
       │                    └──────────────┘                  │
       │                                                           │
       └───────────────────────────────────────────────────────────┘
                           Tracing Context
```

## Compatibility

- Python 3.9+
- RabbitMQ 3.8+
- Pydantic 2.0+

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions, please open an issue on GitHub.
