import asyncio
import json
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
import aio_pika
import structlog
from envelope import EventEnvelope, EventPriority
from tracing import Tracer, TraceParent
from utils import Config, MetricsEmitter, Timer, EventValidator, ValidationError


logger = structlog.get_logger()


@dataclass
class PublishResult:
    """Result of a publish operation."""
    success: bool
    event_id: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    duration_ms: float = 0.0


class EventPublisher:
    """Event publisher with retry, DLQ, tracing, and metrics."""
    
    def __init__(
        self,
        rabbitmq_url: str,
        exchange_name: str = "autonomy.events",
        exchange_type: str = "topic",
        config: Optional[Config] = None,
        tracer: Optional[Tracer] = None,
        metrics: Optional[MetricsEmitter] = None
    ):
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.config = config or Config.from_env()
        self.tracer = tracer or Tracer("event-publisher")
        self.metrics = metrics or MetricsEmitter()
        self.validator = EventValidator()
        
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.RobustChannel] = None
        self._exchange: Optional[aio_pika.RobustExchange] = None
        self._dlq_exchange: Optional[aio_pika.RobustExchange] = None
    
    async def connect(self):
        """Connect to RabbitMQ."""
        self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self._channel = await self._connection.channel()
        
        # Declare main exchange
        self._exchange = await self._channel.declare_exchange(
            self.exchange_name,
            self.exchange_type,
            durable=True
        )
        
        # Declare DLQ exchange if enabled
        if self.config.dlq_enabled:
            self._dlq_exchange = await self._channel.declare_exchange(
                f"{self.exchange_name}.dlq",
                self.exchange_type,
                durable=True
            )
        
        logger.info("publisher_connected", exchange=self.exchange_name)
    
    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        if self._connection:
            await self._connection.close()
        logger.info("publisher_disconnected")
    
    async def publish(
        self,
        envelope: EventEnvelope,
        routing_key: str,
        trace_parent: Optional[TraceParent] = None,
        validate: bool = True
    ) -> PublishResult:
        """Publish an event with retry logic."""
        start_time = time.time()
        
        # Validate event if enabled
        if validate and self.config.schema_validation_enabled:
            errors = self.validator.validate_event(envelope)
            if errors:
                error_msg = "; ".join(e.message for e in errors)
                self.metrics.increment("publish.validation_failed", tags={"event_type": envelope.event_type})
                return PublishResult(
                    success=False,
                    event_id=envelope.event_id,
                    error=f"Validation failed: {error_msg}",
                    duration_ms=(time.time() - start_time) * 1000
                )
        
        # Start tracing span
        if trace_parent:
            trace_parent = self.tracer.start_span(
                f"publish.{envelope.event_type}",
                parent=trace_parent
            )
        else:
            trace_parent = self.tracer.start_span(f"publish.{envelope.event_type}")
        
        # Inject tracing into envelope
        envelope.correlation_id = trace_parent.correlation_id
        envelope.causation_id = trace_parent.causation_id
        envelope.metadata["traceparent"] = trace_parent.trace_context.to_traceparent()
        
        # Attempt to publish with retry
        retry_count = 0
        last_error = None
        
        while retry_count <= self.config.max_retries:
            try:
                result = await self._publish_single(envelope, routing_key)
                
                duration_ms = (time.time() - start_time) * 1000
                
                if result.success:
                    self.metrics.increment(
                        "publish.success",
                        tags={"event_type": envelope.event_type, "priority": str(envelope.priority)}
                    )
                    self.metrics.timing("publish.duration", duration_ms, tags={"event_type": envelope.event_type})
                    
                    self.tracer.finish_span(trace_parent, f"publish.{envelope.event_type}", True, duration_ms=duration_ms)
                    
                    return PublishResult(
                        success=True,
                        event_id=envelope.event_id,
                        message_id=result.message_id,
                        retry_count=retry_count,
                        duration_ms=duration_ms
                    )
                else:
                    last_error = result.error
                    
            except Exception as e:
                last_error = str(e)
                logger.error(
                    "publish_error",
                    event_id=envelope.event_id,
                    event_type=envelope.event_type,
                    retry_count=retry_count,
                    error=str(e)
                )
            
            # Retry logic
            if retry_count < self.config.max_retries and self.config.retry_enabled:
                retry_count += 1
                envelope.increment_retry()
                delay_ms = self._calculate_backoff(retry_count)
                await asyncio.sleep(delay_ms / 1000)
            else:
                break
        
        # All retries failed, send to DLQ
        if self.config.dlq_enabled:
            await self._send_to_dlq(envelope, routing_key, last_error)
        
        duration_ms = (time.time() - start_time) * 1000
        
        self.metrics.increment(
            "publish.failed",
            tags={"event_type": envelope.event_type, "reason": "max_retries_exceeded"}
        )
        
        self.tracer.finish_span(
            trace_parent,
            f"publish.{envelope.event_type}",
            False,
            error=last_error,
            duration_ms=duration_ms
        )
        
        return PublishResult(
            success=False,
            event_id=envelope.event_id,
            error=last_error or "Max retries exceeded",
            retry_count=retry_count,
            duration_ms=duration_ms
        )
    
    async def _publish_single(self, envelope: EventEnvelope, routing_key: str) -> PublishResult:
        """Publish a single message."""
        if not self._exchange:
            raise RuntimeError("Publisher not connected. Call connect() first.")
        
        message_body = json.dumps(envelope.to_dict()).encode()
        
        message = aio_pika.Message(
            message_body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            priority=envelope.priority,
            headers={
                "event_type": envelope.event_type,
                "event_version": envelope.version,
                "correlation_id": envelope.correlation_id,
                "causation_id": envelope.causation_id,
                "engine_id": envelope.engine_id,
            }
        )
        
        result = await self._exchange.publish(
            message,
            routing_key=routing_key,
            mandatory=self.config.publisher_mandatory
        )
        
        return PublishResult(
            success=True,
            event_id=envelope.event_id,
            message_id=result.message_id if hasattr(result, 'message_id') else None
        )
    
    async def _send_to_dlq(self, envelope: EventEnvelope, routing_key: str, error: str):
        """Send failed event to DLQ."""
        if not self._dlq_exchange:
            return
        
        dlq_routing_key = f"{routing_key}.dlq"
        
        message_body = json.dumps({
            "envelope": envelope.to_dict(),
            "original_routing_key": routing_key,
            "error": error,
            "failed_at": time.time()
        }).encode()
        
        message = aio_pika.Message(
            message_body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        await self._dlq_exchange.publish(message, routing_key=dlq_routing_key)
        
        self.metrics.increment("dlq.published", tags={"event_type": envelope.event_type})
        logger.warning(
            "sent_to_dlq",
            event_id=envelope.event_id,
            event_type=envelope.event_type,
            error=error
        )
    
    def _calculate_backoff(self, retry_count: int) -> int:
        """Calculate exponential backoff delay."""
        delay = self.config.retry_initial_delay_ms * (
            self.config.retry_multiplier ** (retry_count - 1)
        )
        return min(int(delay), self.config.retry_max_delay_ms)
    
    async def publish_batch(
        self,
        envelopes: list[EventEnvelope],
        routing_key_prefix: str,
        trace_parent: Optional[TraceParent] = None
    ) -> list[PublishResult]:
        """Publish multiple events."""
        results = []
        
        for envelope in envelopes:
            routing_key = f"{routing_key_prefix}.{envelope.event_type}"
            result = await self.publish(envelope, routing_key, trace_parent)
            results.append(result)
        
        return results
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
