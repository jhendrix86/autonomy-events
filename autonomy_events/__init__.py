"""
autonomy_events

Production-grade shared event library for the Autonomous Company OS.

This package aggregates the top-level modules of the autonomy-events
distribution (envelope, publisher, consumer, registry, tracing, dlq,
utils, schemas) under the importable name `autonomy_events`, since the
project's distribution name (autonomy-events, with a hyphen) cannot
itself be a valid Python module name. Consumers (e.g. governance-engine,
global-state-manager) import from here as `from autonomy_events import ...`.
"""

__version__ = "1.0.0"

# Core components
from envelope import EventEnvelope, EventPriority
from publisher import EventPublisher, PublishResult
from consumer import EventConsumer, ConsumeResult, MessageHandler
from registry import SchemaRegistry, SchemaVersion, CompatibilityMode
from tracing import Tracer, TraceContext, TraceParent
from dlq import DLQManager, DLQMessage
from utils import EventValidator, ValidationError, MetricsEmitter, Timer, Config
from severity import Severity, severity_at_least, max_severity

# Event schemas
from schemas.pydantic import (
    # Funnel Events
    FunnelCreated,
    FunnelApproved,
    FunnelLaunched,
    FunnelMetrics,
    FunnelInsights,
    FunnelMutation,
    FunnelArchived,
    # Governance Events
    GovernanceRequest,
    GovernanceApproved,
    GovernanceRejected,
    GovernanceEmergencyStop,
    GovernanceOverride,
    # Knowledge Graph Events
    KGEentityCreated,
    KGRelationshipCreated,
    KGPatternDetected,
    KGInsightGenerated,
    KGAnomalyDetected,
    # Safety Events
    SafetyViolationDetected,
    SafetyBlockedAction,
    SafetyRollbackTriggered,
    # Health Events
    EngineHealthReport,
    EngineDegraded,
    EngineRecovered,
    # Failure Events
    FailureDetected,
    FailureRecovered,
    FailureRetryScheduled,
    # DLQ Events
    DLQEventFailed,
    DLQEventReplayed,
    # Temporal Events
    TemporalSnapshot,
    CausalChainDetected,
)

__all__ = [
    # Version
    "__version__",
    # Core components
    "EventEnvelope",
    "EventPriority",
    "EventPublisher",
    "PublishResult",
    "EventConsumer",
    "ConsumeResult",
    "MessageHandler",
    "SchemaRegistry",
    "SchemaVersion",
    "CompatibilityMode",
    "Tracer",
    "TraceContext",
    "TraceParent",
    "DLQManager",
    "DLQMessage",
    "EventValidator",
    "ValidationError",
    "MetricsEmitter",
    "Timer",
    "Config",
    "Severity",
    "severity_at_least",
    "max_severity",
    # Event schemas
    "FunnelCreated",
    "FunnelApproved",
    "FunnelLaunched",
    "FunnelMetrics",
    "FunnelInsights",
    "FunnelMutation",
    "FunnelArchived",
    "GovernanceRequest",
    "GovernanceApproved",
    "GovernanceRejected",
    "GovernanceEmergencyStop",
    "GovernanceOverride",
    "KGEentityCreated",
    "KGRelationshipCreated",
    "KGPatternDetected",
    "KGInsightGenerated",
    "KGAnomalyDetected",
    "SafetyViolationDetected",
    "SafetyBlockedAction",
    "SafetyRollbackTriggered",
    "EngineHealthReport",
    "EngineDegraded",
    "EngineRecovered",
    "FailureDetected",
    "FailureRecovered",
    "FailureRetryScheduled",
    "DLQEventFailed",
    "DLQEventReplayed",
    "TemporalSnapshot",
    "CausalChainDetected",
]
