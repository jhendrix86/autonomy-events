import pytest
import os
from utils import Config


class TestConfig:
    def test_default_config(self):
        config = Config()
        
        assert config.rabbitmq_url == "amqp://localhost:5672"
        assert config.rabbitmq_exchange == "autonomy.events"
        assert config.dlq_enabled is True
        assert config.max_retries == 3
        assert config.retry_enabled is True
        assert config.tracing_enabled is True
        assert config.schema_validation_enabled is True
        assert config.metrics_enabled is True
    
    def test_config_from_env(self):
        os.environ["RABBITMQ_URL"] = "amqp://test:5672"
        os.environ["MAX_RETRIES"] = "5"
        
        try:
            config = Config.from_env()
            assert config.rabbitmq_url == "amqp://test:5672"
            assert config.max_retries == 5
        finally:
            del os.environ["RABBITMQ_URL"]
            del os.environ["MAX_RETRIES"]
    
    def test_config_from_dict(self):
        config_dict = {
            "rabbitmq_url": "amqp://custom:5672",
            "max_retries": 10,
            "dlq_enabled": False
        }
        
        config = Config.from_dict(config_dict)
        assert config.rabbitmq_url == "amqp://custom:5672"
        assert config.max_retries == 10
        assert config.dlq_enabled is False
    
    def test_config_validation(self):
        config = Config(
            rabbitmq_url="amqp://localhost:5672",
            priority=3
        )
        
        assert config.priority == 3
