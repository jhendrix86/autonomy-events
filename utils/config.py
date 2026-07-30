import os
from typing import Optional
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Configuration for autonomy-events library."""
    
    # RabbitMQ Configuration
    rabbitmq_url: str = Field(default_factory=lambda: os.getenv("RABBITMQ_URL", "amqp://localhost:5672"))
    rabbitmq_exchange: str = Field(default="autonomy.events")
    rabbitmq_exchange_type: str = Field(default="topic")
    
    # DLQ Configuration
    dlq_enabled: bool = Field(default=True)
    dlq_queue_suffix: str = Field(default=".dlq")
    max_retries: int = Field(default=3)
    
    # Retry Configuration
    retry_enabled: bool = Field(default=True)
    retry_initial_delay_ms: int = Field(default=100)
    retry_max_delay_ms: int = Field(default=30000)
    retry_multiplier: float = Field(default=2.0)
    
    # Tracing Configuration
    tracing_enabled: bool = Field(default=True)
    traceparent_header: str = Field(default="traceparent")
    
    # Schema Registry Configuration
    schema_registry_path: Optional[str] = Field(default=None)
    schema_validation_enabled: bool = Field(default=True)
    
    # Metrics Configuration
    metrics_enabled: bool = Field(default=True)
    metrics_port: int = Field(default=9090)
    
    # Logging Configuration
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    # Publisher Configuration
    publisher_confirm_timeout_ms: int = Field(default=5000)
    publisher_mandatory: bool = Field(default=True)
    
    # Consumer Configuration
    consumer_prefetch_count: int = Field(default=10)
    consumer_auto_ack: bool = Field(default=False)
    consumer_timeout_ms: int = Field(default=30000)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls()
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> "Config":
        """Load configuration from dictionary."""
        return cls(**config_dict)
