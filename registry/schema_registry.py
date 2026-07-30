from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List, Any
from pydantic import BaseModel
import json
from pathlib import Path


class CompatibilityMode(Enum):
    NONE = "none"
    BACKWARD = "backward"
    FORWARD = "forward"
    FULL = "full"


class SchemaVersion(BaseModel):
    version: str
    schema_definition: Dict[str, Any]
    created_at: datetime
    deprecated: bool = False
    deprecated_at: Optional[datetime] = None
    migration_path: Optional[str] = None


class SchemaRegistry:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "schemas/registry"
        self._schemas: Dict[str, Dict[str, SchemaVersion]] = {}
        self._load_schemas()

    def _load_schemas(self):
        """Load schemas from storage if available."""
        storage = Path(self.storage_path)
        if storage.exists():
            for schema_file in storage.glob("*.json"):
                with open(schema_file) as f:
                    data = json.load(f)
                    event_type = data["event_type"]
                    versions = {
                        v: SchemaVersion(**version_data)
                        for v, version_data in data["versions"].items()
                    }
                    self._schemas[event_type] = versions

    def _save_schemas(self):
        """Save schemas to storage."""
        storage = Path(self.storage_path)
        storage.mkdir(parents=True, exist_ok=True)
        
        for event_type, versions in self._schemas.items():
            data = {
                "event_type": event_type,
                "versions": {
                    v: version.dict()
                    for v, version in versions.items()
                }
            }
            with open(storage / f"{event_type}.json", "w") as f:
                json.dump(data, f, indent=2, default=str)

    def register_schema(
        self,
        event_type: str,
        version: str,
        schema_definition: Dict[str, Any],
        compatibility_mode: CompatibilityMode = CompatibilityMode.FULL
    ) -> bool:
        """Register a new schema version."""
        if event_type not in self._schemas:
            self._schemas[event_type] = {}
        
        if version in self._schemas[event_type]:
            raise ValueError(f"Schema version {version} already exists for {event_type}")
        
        # Check compatibility if there are existing versions
        if self._schemas[event_type]:
            latest_version = self._get_latest_version(event_type)
            if not self._check_compatibility(
                self._schemas[event_type][latest_version].schema_definition,
                schema_definition,
                compatibility_mode
            ):
                raise ValueError(f"Schema version {version} is not compatible with {latest_version}")
        
        self._schemas[event_type][version] = SchemaVersion(
            version=version,
            schema_definition=schema_definition,
            created_at=datetime.utcnow()
        )
        self._save_schemas()
        return True

    def get_schema(self, event_type: str, version: Optional[str] = None) -> Optional[SchemaVersion]:
        """Get a schema version. If version is None, returns latest."""
        if event_type not in self._schemas:
            return None
        
        if version is None:
            version = self._get_latest_version(event_type)
        
        return self._schemas[event_type].get(version)

    def get_latest_version(self, event_type: str) -> Optional[str]:
        """Get the latest schema version for an event type."""
        if event_type not in self._schemas:
            return None
        return self._get_latest_version(event_type)

    def _get_latest_version(self, event_type: str) -> str:
        """Internal method to get latest version."""
        versions = list(self._schemas[event_type].keys())
        # Sort by version number (assuming semantic versioning)
        versions.sort(key=lambda v: [int(x) for x in v.split(".")])
        return versions[-1]

    def _check_compatibility(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        mode: CompatibilityMode
    ) -> bool:
        """Check schema compatibility based on mode."""
        if mode == CompatibilityMode.NONE:
            return True
        
        old_fields = set(old_schema.get("properties", {}).keys())
        new_fields = set(new_schema.get("properties", {}).keys())
        
        if mode == CompatibilityMode.BACKWARD:
            # New schema must not remove required fields
            old_required = set(old_schema.get("required", []))
            new_required = set(new_schema.get("required", []))
            return old_required.issubset(new_fields)
        
        if mode == CompatibilityMode.FORWARD:
            # Old schema must be able to read new schema
            return old_fields.issubset(new_fields)
        
        if mode == CompatibilityMode.FULL:
            # Both backward and forward compatible
            old_required = set(old_schema.get("required", []))
            new_required = set(new_schema.get("required", []))
            return (
                old_required.issubset(new_fields) and
                old_fields.issubset(new_fields)
            )
        
        return True

    def deprecate_schema(self, event_type: str, version: str) -> bool:
        """Deprecate a schema version."""
        if event_type not in self._schemas or version not in self._schemas[event_type]:
            return False
        
        self._schemas[event_type][version].deprecated = True
        self._schemas[event_type][version].deprecated_at = datetime.utcnow()
        self._save_schemas()
        return True

    def list_versions(self, event_type: str) -> List[str]:
        """List all versions for an event type."""
        if event_type not in self._schemas:
            return []
        return list(self._schemas[event_type].keys())

    def list_event_types(self) -> List[str]:
        """List all registered event types."""
        return list(self._schemas.keys())

    def validate_event(self, event_type: str, event_data: Dict[str, Any], version: Optional[str] = None) -> bool:
        """Validate event data against schema."""
        schema = self.get_schema(event_type, version)
        if not schema:
            return False
        
        # Basic validation - check required fields
        required = schema.schema_definition.get("required", [])
        properties = schema.schema_definition.get("properties", {})
        
        for field in required:
            if field not in event_data:
                return False
        
        # Check field types
        for field, value in event_data.items():
            if field in properties:
                field_type = properties[field].get("type")
                if field_type == "string" and not isinstance(value, str):
                    return False
                elif field_type == "integer" and not isinstance(value, int):
                    return False
                elif field_type == "number" and not isinstance(value, (int, float)):
                    return False
                elif field_type == "boolean" and not isinstance(value, bool):
                    return False
                elif field_type == "array" and not isinstance(value, list):
                    return False
                elif field_type == "object" and not isinstance(value, dict):
                    return False
        
        return True
