import asyncio
import json
import time
from typing import Optional, Dict, Any, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
import aio_pika
import structlog
from envelope import EventEnvelope
from tracing import Tracer, TraceParent
from utils import Config, MetricsEmitter, Timer, EventValidator, ValidationError


logger = structlog.get_logger()


class AckStrategy(Enum):
    MANUAL = "manual"
    AUTO = "auto"
    NONE = "none"


@dataclass
class ConsumeResult:
    """Result of a consume operation."""
    success: bool
    event_id: str
    event_type: str
    error: Optional[str] = None
    duration_ms: float = 0.0
    should_ack: bool = True
    should_requeue: bool = False


MessageHandler = Callable[[EventEnvelope, TraceParent], Awaitable[ConsumeResult]]


class EventConsumer:
    """Event consumer with validation, tracing, DLQ routing, and metrics."""
    
    def __init__(
        self,
        rabbitmq_url: str,
        queue_name: str,
        exchange_name: str = "autonomy.events",
        exchange_type: str = "topic",
        routing_keys: Optional[list[str]] = None,
        config: Optional[Config] = None,
        tracer: Optional[Tracer] = None,
        metrics: Optional[MetricsEmitter] = None
    ):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.routing_keys = routing_keys or ["#"]
        self.config = config or Config.from_env()
        self.tracer = tracer or Tracer("event-consumer")
        self.metrics = metrics or MetricsEmitter()
        self.validator = EventValidator()
        
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.RobustChannel] = None
        self._exchange: Optional[aio_pika.RobustExchange] = None
        self._queue: Optional[aio_pika.RobustQueue] = None
        self._dlq_queue: Optional[aio_pika.RobustQueue] = None
        
        self._handlers: Dict[str, MessageHandler] = {}
        self._default_handler: Optional[MessageHandler] = None
        self._consuming = False
    
    async def connect(self):
        """Connect to RabbitMQ and setup queues."""
        self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self._channel = await self._connection.channel()
        
        # Set prefetch count
        await self._channel.set_qos(prefetch_count=self.config.consumer_prefetch_count)
        
        # Declare exchange
        self._exchange = await self._channel.declare_exchange(
            self.exchange_name,
            self.exchange_type,
            durable=True
        )
        
        # Declare main queue
        self._queue = await self._channel.declare_queue(
            self.queue_name,
            durable=True
        )
        
        # Bind queue to routing keys
        for routing_key in self.routing_keys:
            await self._queue.bind(self._exchange, routing_key=routing_key)
        
        # Declare DLQ queue if enabled
        if self.config.dlq_enabled:
            dlq_queue_name = f"{self.queue_name}{self.config.dlq_queue_suffix}"
            self._dlq_queue = await self._channel.declare_queue(
                dlq_queue_name,
                durable=True
            )
            
            # Bind DLQ queue to DLQ exchange
            dlq_exchange = await self._channel.declare_exchange(
                f"{self.exchange_name}.dlq",
                self.exchange_type,
                durable=True
            )
            await self._dlq_queue.bind(dlq_exchange, routing_key=f"{self.queue_name}.dlq")
        
        logger.info(
            "consumer_connected",
            queue=self.queue_name,
            routing_keys=self.routing_keys
        )
    
    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        self._consuming = False
        if self._connection:
            await self._connection.close()
        logger.info("consumer_disconnected")
    
    def register_handler(self, event_type: str, handler: MessageHandler):
        """Register a handler for a specific event type."""
        self._handlers[event_type] = handler
        logger.info("handler_registered", event_type=event_type)
    
    def register_default_handler(self, handler: MessageHandler):
        """Register a default handler for unmatched events."""
        self._default_handler = handler
        logger.info("default_handler_registered")
    
    async def start_consuming(self):
        """Start consuming messages."""
        if not self._queue:
            raise RuntimeError("Consumer not connected. Call connect() first.")
        
        self._consuming = True
        
        async with self._queue.iterator() as queue_iterator:
            async for message in queue_iterator:
                if not self._consuming:
                    break
                
                await self._process_message(message)
    
    async def _process_message(self, message: aio_pika.IncomingMessage):
        """Process a single message."""
        start_time = time.time()
        
        try:
            # Parse message
            envelope_data = json.loads(message.body.decode())
            envelope = EventEnvelope.from_dict(envelope_data)
            
            # Extract tracing headers
            headers = dict(message.headers) if message.headers else {}
            trace_parent = self.tracer.extract_headers(headers)
            
            # Start tracing span
            if not trace_parent:
                trace_parent = self.tracer.start_span(f"consume.{envelope.event_type}")
            else:
                trace_parent = self.tracer.start_span(
                    f"consume.{envelope.event_type}",
                    parent=trace_parent
                )
            
            # Validate event
            if self.config.schema_validation_enabled:
                errors = self.validator.validate_event(envelope)
                if errors:
                    error_msg = "; ".join(e.message for e in errors)
                    self.metrics.increment("consume.validation_failed", tags={"event_type": envelope.event_type})
                    
                    self.tracer.finish_span(
                        trace_parent,
                        f"consume.{envelope.event_type}",
                        False,
                        error=error_msg,
                        duration_ms=(time.time() - start_time) * 1000
                    )
                    
                    if self.config.consumer_auto_ack:
                        await message.ack()
                    else:
                        await message.reject(requeue=False)
                    
                    logger.error(
                        "consume_validation_failed",
                        event_id=envelope.event_id,
                        event_type=envelope.event_type,
                        error=error_msg
                    )
                    return
            
            # Get handler
            handler = self._handlers.get(envelope.event_type, self._default_handler)
            
            if not handler:
                logger.warning(
                    "no_handler_found",
                    event_type=envelope.event_type,
                    event_id=envelope.event_id
                )
                
                if self.config.consumer_auto_ack:
                    await message.ack()
                else:
                    await message.ack()
                
                self.metrics.increment("consume.no_handler", tags={"event_type": envelope.event_type})
                return
            
            # Call handler
            result = await handler(envelope, trace_parent)
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms
            
            # Update metrics
            if result.success:
                self.metrics.increment(
                    "consume.success",
                    tags={"event_type": envelope.event_type}
                )
                self.metrics.timing(
                    "consume.duration",
                    duration_ms,
                    tags={"event_type": envelope.event_type}
                )
            else:
                self.metrics.increment(
                    "consume.failed",
                    tags={"event_type": envelope.event_type, "reason": result.error or "unknown"}
                )
            
            # Finish tracing
            self.tracer.finish_span(
                trace_parent,
                f"consume.{envelope.event_type}",
                result.success,
                error=result.error,
                duration_ms=duration_ms
            )
            
            # Ack/Nack based on result
            if self.config.consumer_auto_ack:
                # Already acked by aio_pika
                pass
            else:
                if result.should_ack:
                    await message.ack()
                elif result.should_requeue:
                    await message.reject(requeue=True)
                else:
                    await message.reject(requeue=False)
            
            logger.info(
                "message_processed",
                event_id=envelope.event_id,
                event_type=envelope.event_type,
                success=result.success,
                duration_ms=duration_ms
            )
            
        except json.JSONDecodeError as e:
            logger.error("consume_json_error", error=str(e))
            if not self.config.consumer_auto_ack:
                await message.reject(requeue=False)
            self.metrics.increment("consume.json_error")
            
        except Exception as e:
            logger.error(
                "consume_error",
                error=str(e),
                error_type=type(e).__name__
            )
            
            if not self.config.consumer_auto_ack:
                # Send to DLQ if configured
                if self.config.dlq_enabled and self._dlq_queue:
                    await self._send_to_dlq(message, str(e))
                else:
                    await message.reject(requeue=False)
            
            self.metrics.increment("consume.error")
    
    async def _send_to_dlq(self, message: aio_pika.IncomingMessage, error: str):
        """Send failed message to DLQ."""
        if not self._dlq_queue:
            return
        
        dlq_message = aio_pika.Message(
            message.body,
            content_type=message.content_type,
            headers={
                **(message.headers or {}),
                "original_queue": self.queue_name,
                "error": error,
                "failed_at": time.time()
            },
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        await self._dlq_queue.publish(dlq_message)
        
        self.metrics.increment("consume.dlq_sent")
        logger.warning("sent_to_dlq", error=error)
    
    async def replay_dlq(self, max_messages: int = 100):
        """Replay messages from DLQ."""
        if not self._dlq_queue:
            logger.warning("dlq_not_configured")
            return
        
        replayed = 0
        
        async with self._dlq_queue.iterator() as queue_iterator:
            async for message in queue_iterator:
                if replayed >= max_messages:
                    break
                
                try:
                    # Parse DLQ message
                    dlq_data = json.loads(message.body.decode())
                    
                    if "envelope" in dlq_data:
                        # Reconstruct original envelope
                        envelope = EventEnvelope.from_dict(dlq_data["envelope"])
                        original_routing_key = dlq_data.get("original_routing_key", self.queue_name)
                        
                        # Republish to original exchange
                        message_body = json.dumps(envelope.to_dict()).encode()
                        new_message = aio_pika.Message(
                            message_body,
                            content_type="application/json",
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                            headers=envelope.metadata
                        )
                        
                        await self._exchange.publish(new_message, routing_key=original_routing_key)
                        await message.ack()
                        replayed += 1
                        
                        self.metrics.increment("dlq.replayed")
                        logger.info("dlq_message_replayed", event_id=envelope.event_id)
                    
                except Exception as e:
                    logger.error("dlq_replay_error", error=str(e))
                    await message.reject(requeue=False)
        
        logger.info("dlq_replay_completed", replayed=replayed)
    
    def stop_consuming(self):
        """Stop consuming messages."""
        self._consuming = False
        logger.info("consuming_stopped")
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
