import pytest
import tempfile
import shutil
from pathlib import Path
from registry import SchemaRegistry, SchemaVersion, CompatibilityMode


class TestSchemaRegistry:
    def test_register_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(storage_path=tmpdir)
            
            schema_def = {
                "type": "object",
                "properties": {
                    "funnel_id": {"type": "string"},
                    "niche": {"type": "string"}
                },
                "required": ["funnel_id", "niche"]
            }
            
            result = registry.register_schema(
                "funnel.created",
                "1.0.0",
                schema_def,
                CompatibilityMode.FULL
            )
            
            assert result is True
    
    def test_register_schema_duplicate_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(storage_path=tmpdir)
            
            schema_def = {
                "type": "object",
                "properties": {"funnel_id": {"type": "string"}},
                "required": ["funnel_id"]
            }
            
            registry.register_schema("funnel.created", "1.0.0", schema_def)
            
            with pytest.raises(ValueError, match="already exists"):
                registry.register_schema("funnel.created", "1.0.0", schema_def)
    
    def test_get_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(storage_path=tmpdir)
            
            schema_def = {
                "type": "object",
                "properties": {"funnel_id": {"type": "string"}},
                "required": ["funnel_id"]
            }
            
            registry.register_schema("funnel.created", "1.0.0", schema_def)
            
            schema = registry.get_schema("funnel.created", "1.0.0")
            assert schema is not None
            assert schema.version == "1.0.0"
    
    def test_get_schema_latest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(storage_path=tmpdir)
            
            schema_def = {
                "type": "object",
                "properties": {"funnel_id": {"type": "string"}},
                "required": ["funnel_id"]
            }
            
            registry.register_schema("funnel.created", "1.0.0", schema_def)
            registry.register_schema("funnel.created", "1.1.0", schema_def)
            registry.register_schema("funnel.created", "2.0.0", schema_def)
            
            schema = registry.get_schema("funnel.created")
            assert schema.version == "2.0.0"
    
    def test_get_schema_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(storage_path=tmpdir)
            
            schema = registry.get_schema("unknown.event", "1.0.0")
            assert schema is None
    
    def test_get_latest_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(storage_path=tmpdir)
            
            schema_def = {
                "type": "object",
                "properties": {"funnel_id": {"type": "string"}},
                "required": ["funnel_id"]
            }
            
            registry.register_schema("funnel.created", "1.0.0", schema_def)
            registry.register_schema("funnel.created", "1.1.0", schema_def)
            
            version = registry.get_latest_version("funnel.created")
            assert version == "1.1.0"
    
    def test_deprecate_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(storage_path=tmpdir)
            
            schema_def = {
                "type": "object",
                "properties": {"funnel_id": {"type": "string"}},
                "required": ["funnel_id"]
            }
            
            registry.register_schema("funnel.created", "1.0.0", schema_def)
            
            result = registry.deprecate_schema("funnel.created", "1.0.0")
            assert result is True
            
            schema = registry.get_schema("funnel.created", "1.0.0")
            assert schema.deprecated is True
    
    def test_list_versions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(storage_path=tmpdir)
            
            schema_def = {
                "type": "object",
                "properties": {"funnel_id": {"type": "string"}},
                "required": ["funnel_id"]
            }
            
            registry.register_schema("funnel.created", "1.0.0", schema_def)
            registry.register_schema("funnel.created", "1.1.0", schema_def)
            
            versions = registry.list_versions("funnel.created")
            assert len(versions) == 2
            assert "1.0.0" in versions
            assert "1.1.0" in versions
    
    def test_list_event_types(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(storage_path=tmpdir)
            
            schema_def = {
                "type": "object",
                "properties": {"funnel_id": {"type": "string"}},
                "required": ["funnel_id"]
            }
            
            registry.register_schema("funnel.created", "1.0.0", schema_def)
            registry.register_schema("governance.request", "1.0.0", schema_def)
            
            event_types = registry.list_event_types()
            assert len(event_types) == 2
            assert "funnel.created" in event_types
            assert "governance.request" in event_types
    
    def test_validate_event_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(storage_path=tmpdir)
            
            schema_def = {
                "type": "object",
                "properties": {
                    "funnel_id": {"type": "string"},
                    "niche": {"type": "string"}
                },
                "required": ["funnel_id", "niche"]
            }
            
            registry.register_schema("funnel.created", "1.0.0", schema_def)
            
            event_data = {
                "funnel_id": "test-123",
                "niche": "fitness"
            }
            
            result = registry.validate_event("funnel.created", event_data)
            assert result is True
    
    def test_validate_event_missing_required(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(storage_path=tmpdir)
            
            schema_def = {
                "type": "object",
                "properties": {
                    "funnel_id": {"type": "string"},
                    "niche": {"type": "string"}
                },
                "required": ["funnel_id", "niche"]
            }
            
            registry.register_schema("funnel.created", "1.0.0", schema_def)
            
            event_data = {
                "funnel_id": "test-123"
            }
            
            result = registry.validate_event("funnel.created", event_data)
            assert result is False
    
    def test_backward_compatibility(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(storage_path=tmpdir)
            
            old_schema = {
                "type": "object",
                "properties": {
                    "funnel_id": {"type": "string"},
                    "niche": {"type": "string"}
                },
                "required": ["funnel_id", "niche"]
            }
            
            new_schema = {
                "type": "object",
                "properties": {
                    "funnel_id": {"type": "string"},
                    "niche": {"type": "string"},
                    "new_field": {"type": "string"}
                },
                "required": ["funnel_id", "niche"]
            }
            
            registry.register_schema("funnel.created", "1.0.0", old_schema)
            result = registry.register_schema(
                "funnel.created",
                "2.0.0",
                new_schema,
                CompatibilityMode.BACKWARD
            )
            
            assert result is True
    
    def test_backward_compatibility_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(storage_path=tmpdir)
            
            old_schema = {
                "type": "object",
                "properties": {
                    "funnel_id": {"type": "string"},
                    "niche": {"type": "string"}
                },
                "required": ["funnel_id", "niche"]
            }
            
            new_schema = {
                "type": "object",
                "properties": {
                    "funnel_id": {"type": "string"}
                },
                "required": ["funnel_id"]
            }
            
            registry.register_schema("funnel.created", "1.0.0", old_schema)
            
            with pytest.raises(ValueError, match="not compatible"):
                registry.register_schema(
                    "funnel.created",
                    "2.0.0",
                    new_schema,
                    CompatibilityMode.BACKWARD
                )
