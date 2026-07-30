import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
import aio_pika
import structlog
from envelope import EventEnvelope
from utils import Config, MetricsEmitter


logger = structlog.get_logger()


@dataclass
class DLQMessage:
    """Dead letter queue message."""
    original_event_id: str
    original_event_type: str
    failure_reason: str
    failure_type: str
    failed_at: float
    retry_count: int
    original_payload: Dict[str, Any]
    error_details: Dict[str, Any]
    queue_name: str
    priority: int
    can_replay: bool
    replay_conditions: List[str]
    raw_message: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DLQMessage":
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DLQManager:
    """Manage dead letter queue operations."""
    
    def __init__(
        self,
        rabbitmq_url: str,
        dlq_queue_name: str,
        exchange_name: str = "autonomy.events",
        config: Optional[Config] = None,
        metrics: Optional[MetricsEmitter] = None
    ):
        self.rabbitmq_url = rabbitmq_url
        self.dlq_queue_name = dlq_queue_name
        self.exchange_name = exchange_name
        self.config = config or Config.from_env()
        self.metrics = metrics or MetricsEmitter()
        
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.RobustChannel] = None
        self._dlq_queue: Optional[aio_pika.RobustQueue] = None
        self._dlq_exchange: Optional[aio_pika.RobustExchange] = None
        self._main_exchange: Optional[aio_pika.RobustExchange] = None
    
    async def connect(self):
        """Connect to RabbitMQ."""
        self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self._channel = await self._connection.channel()
        
        # Declare main exchange
        self._main_exchange = await self._channel.declare_exchange(
            self.exchange_name,
            "topic",
            durable=True
        )
        
        # Declare DLQ exchange
        self._dlq_exchange = await self._channel.declare_exchange(
            f"{self.exchange_name}.dlq",
            "topic",
            durable=True
        )
        
        # Declare DLQ queue
        self._dlq_queue = await self._channel.declare_queue(
            self.dlq_queue_name,
            durable=True
        )
        
        # Bind DLQ queue
        await self._dlq_queue.bind(self._dlq_exchange, routing_key=f"{self.dlq_queue_name}.dlq")
        
        logger.info("dlq_manager_connected", queue=self.dlq_queue_name)
    
    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        if self._connection:
            await self._connection.close()
        logger.info("dlq_manager_disconnected")
    
    async def get_message_count(self) -> int:
        """Get the number of messages in DLQ."""
        if not self._dlq_queue:
            raise RuntimeError("DLQ manager not connected")
        
        queue_info = await self._dlq_queue.queue_declare(passive=True)
        return queue_info.message_count
    
    async def peek_messages(self, limit: int = 10) -> List[DLQMessage]:
        """Peek at messages in DLQ without consuming them."""
        messages = []
        
        if not self._dlq_queue:
            raise RuntimeError("DLQ manager not connected")
        
        async with self._dlq_queue.iterator() as queue_iterator:
            async for message in queue_iterator:
                if len(messages) >= limit:
                    break
                
                try:
                    data = json.loads(message.body.decode())
                    
                    # Handle both envelope format and direct DLQ format
                    if "envelope" in data:
                        envelope_data = data["envelope"]
                        dlq_message = DLQMessage(
                            original_event_id=envelope_data.get("event_id"),
                            original_event_type=envelope_data.get("event_type"),
                            failure_reason=data.get("error", "Unknown"),
                            failure_type="processing",
                            failed_at=data.get("failed_at", time.time()),
                            retry_count=envelope_data.get("retry_count", 0),
                            original_payload=envelope_data.get("payload", {}),
                            error_details={},
                            queue_name=data.get("original_queue", "unknown"),
                            priority=envelope_data.get("priority", 2),
                            can_replay=True,
                            replay_conditions=[],
                            raw_message=data
                        )
                    else:
                        dlq_message = DLQMessage.from_dict(data)
                    
                    messages.append(dlq_message)
                    
                    # Reject to keep message in queue
                    await message.reject(requeue=True)
                    
                except Exception as e:
                    logger.error("dlq_peek_error", error=str(e))
                    await message.reject(requeue=True)
        
        return messages
    
    async def replay_message(
        self,
        original_event_id: str,
        target_routing_key: Optional[str] = None
    ) -> bool:
        """Replay a specific message from DLQ."""
        if not self._dlq_queue or not self._main_exchange:
            raise RuntimeError("DLQ manager not connected")
        
        async with self._dlq_queue.iterator() as queue_iterator:
            async for message in queue_iterator:
                try:
                    data = json.loads(message.body.decode())
                    
                    # Find the message
                    event_id = None
                    if "envelope" in data:
                        event_id = data["envelope"].get("event_id")
                    else:
                        event_id = data.get("original_event_id")
                    
                    if event_id == original_event_id:
                        # Reconstruct envelope
                        if "envelope" in data:
                            envelope = EventEnvelope.from_dict(data["envelope"])
                        else:
                            envelope = EventEnvelope(
                                event_id=data["original_event_id"],
                                event_type=data["original_event_type"],
                                engine_id="dlq-replay",
                                payload=data["original_payload"]
                            )
                        
                        # Publish back to main exchange
                        routing_key = target_routing_key or data.get("original_routing_key", envelope.event_type)
                        message_body = json.dumps(envelope.to_dict()).encode()
                        
                        new_message = aio_pika.Message(
                            message_body,
                            content_type="application/json",
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                            headers={
                                "event_type": envelope.event_type,
                                "event_version": envelope.version,
                                "correlation_id": envelope.correlation_id,
                                "causation_id": envelope.causation_id,
                                "engine_id": envelope.engine_id,
                                "dlq_replay": "true",
                            }
                        )
                        
                        await self._main_exchange.publish(new_message, routing_key=routing_key)
                        await message.ack()
                        
                        self.metrics.increment("dlq.replay_success")
                        logger.info("dlq_message_replayed", event_id=original_event_id)
                        return True
                    
                except Exception as e:
                    logger.error("dlq_replay_error", error=str(e))
                    await message.reject(requeue=False)
        
        return False
    
    async def replay_batch(
        self,
        limit: int = 100,
        event_type_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Replay a batch of messages from DLQ."""
        replayed = 0
        failed = 0
        skipped = 0
        
        if not self._dlq_queue or not self._main_exchange:
            raise RuntimeError("DLQ manager not connected")
        
        async with self._dlq_queue.iterator() as queue_iterator:
            async for message in queue_iterator:
                if replayed + failed >= limit:
                    break
                
                try:
                    data = json.loads(message.body.decode())
                    
                    # Filter by event type if specified
                    if event_type_filter:
                        current_event_type = None
                        if "envelope" in data:
                            current_event_type = data["envelope"].get("event_type")
                        else:
                            current_event_type = data.get("original_event_type")
                        
                        if current_event_type != event_type_filter:
                            await message.reject(requeue=True)
                            skipped += 1
                            continue
                    
                    # Reconstruct envelope
                    if "envelope" in data:
                        envelope = EventEnvelope.from_dict(data["envelope"])
                    else:
                        envelope = EventEnvelope(
                            event_id=data["original_event_id"],
                            event_type=data["original_event_type"],
                            engine_id="dlq-replay",
                            payload=data["original_payload"]
                        )
                    
                    # Publish back to main exchange
                    routing_key = data.get("original_routing_key", envelope.event_type)
                    message_body = json.dumps(envelope.to_dict()).encode()
                    
                    new_message = aio_pika.Message(
                        message_body,
                        content_type="application/json",
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        headers={
                            "event_type": envelope.event_type,
                            "event_version": envelope.version,
                            "correlation_id": envelope.correlation_id,
                            "causation_id": envelope.causation_id,
                            "engine_id": envelope.engine_id,
                            "dlq_replay": "true",
                        }
                    )
                    
                    await self._main_exchange.publish(new_message, routing_key=routing_key)
                    await message.ack()
                    replayed += 1
                    
                    self.metrics.increment("dlq.replay_success")
                    
                except Exception as e:
                    logger.error("dlq_batch_replay_error", error=str(e))
                    await message.reject(requeue=False)
                    failed += 1
                    self.metrics.increment("dlq.replay_failed")
        
        logger.info(
            "dlq_batch_replay_completed",
            replayed=replayed,
            failed=failed,
            skipped=skipped
        )
        
        return {
            "replayed": replayed,
            "failed": failed,
            "skipped": skipped
        }
    
    async def purge_old_messages(self, age_hours: int = 24) -> int:
        """Purge messages older than specified age."""
        purged = 0
        cutoff_time = time.time() - (age_hours * 3600)
        
        if not self._dlq_queue:
            raise RuntimeError("DLQ manager not connected")
        
        async with self._dlq_queue.iterator() as queue_iterator:
            async for message in queue_iterator:
                try:
                    data = json.loads(message.body.decode())
                    
                    failed_at = data.get("failed_at", time.time())
                    if "envelope" in data:
                        failed_at = data.get("failed_at", time.time())
                    
                    if failed_at < cutoff_time:
                        await message.ack()
                        purged += 1
                        self.metrics.increment("dlq.purged")
                    else:
                        await message.reject(requeue=True)
                        
                except Exception as e:
                    logger.error("dlq_purge_error", error=str(e))
                    await message.reject(requeue=True)
        
        logger.info("dlq_purge_completed", purged=purged, age_hours=age_hours)
        return purged
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get DLQ statistics."""
        message_count = await self.get_message_count()
        messages = await self.peek_messages(limit=100)
        
        # Calculate stats
        event_type_counts: Dict[str, int] = {}
        failure_type_counts: Dict[str, int] = {}
        
        for msg in messages:
            event_type_counts[msg.original_event_type] = event_type_counts.get(msg.original_event_type, 0) + 1
            failure_type_counts[msg.failure_type] = failure_type_counts.get(msg.failure_type, 0) + 1
        
        return {
            "total_messages": message_count,
            "sample_size": len(messages),
            "event_type_distribution": event_type_counts,
            "failure_type_distribution": failure_type_counts,
        }
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
