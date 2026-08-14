"""
Tests for the canonical Severity scale (severity.py) added 2026-08-14.

Covers both the standalone comparison helpers and that the 5 previously
free-text `severity` fields across schemas/pydantic/*.py now actually
reject invalid values - proving the real bug (any string was accepted
before) is fixed, not just that the enum exists in isolation.
"""

import pytest
from pydantic import ValidationError

from severity import Severity, severity_at_least, max_severity
from schemas.pydantic.failure_events import FailureDetected
from schemas.pydantic.health_events import EngineDegraded
from schemas.pydantic.safety_events import SafetyViolationDetected
from schemas.pydantic.kg_events import KGAnomalyDetected
from schemas.pydantic.governance_events import GovernanceEmergencyStop


class TestSeverityOrdering:
    def test_severity_at_least_true_for_equal_or_higher(self):
        assert severity_at_least(Severity.HIGH, Severity.HIGH)
        assert severity_at_least(Severity.CRITICAL, Severity.LOW)

    def test_severity_at_least_false_for_lower(self):
        assert not severity_at_least(Severity.LOW, Severity.HIGH)
        assert not severity_at_least(Severity.INFO, Severity.MEDIUM)

    def test_max_severity_picks_the_worst(self):
        assert max_severity(Severity.LOW, Severity.CRITICAL, Severity.MEDIUM) == Severity.CRITICAL
        assert max_severity(Severity.INFO) == Severity.INFO

    def test_max_severity_requires_at_least_one_argument(self):
        with pytest.raises(ValueError):
            max_severity()

    def test_all_five_levels_present_in_expected_order(self):
        # Locks in the actual rank order the comparison helpers rely on -
        # a future accidental reordering of the enum would break silently
        # otherwise, since Python enum members don't have inherent order.
        ordered = [Severity.INFO, Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        for lower, higher in zip(ordered, ordered[1:]):
            assert severity_at_least(higher, lower)
            assert not severity_at_least(lower, higher)


class TestSchemaFieldsActuallyValidate:
    """The real bug being fixed: these 5 fields were free-text `str` with
    no validation - any string passed. Prove that's no longer true, not
    just that a valid Severity can be assigned."""

    def test_failure_detected_accepts_real_severity(self):
        event = FailureDetected(
            failure_id="f1", failure_type="network", severity=Severity.HIGH,
            component="c", error_message="m", detected_by="d",
        )
        assert event.severity == Severity.HIGH

    def test_failure_detected_accepts_the_raw_string_value(self):
        # str Enum should coerce a plain string too - existing callers
        # passing "high" as a literal string (not Severity.HIGH) must
        # keep working.
        event = FailureDetected(
            failure_id="f1", failure_type="network", severity="high",
            component="c", error_message="m", detected_by="d",
        )
        assert event.severity == Severity.HIGH

    def test_failure_detected_rejects_invalid_severity(self):
        with pytest.raises(ValidationError):
            FailureDetected(
                failure_id="f1", failure_type="network", severity="sort of bad",
                component="c", error_message="m", detected_by="d",
            )

    def test_engine_degraded_rejects_invalid_severity(self):
        with pytest.raises(ValidationError):
            EngineDegraded(
                engine_id="e1", degradation_type="performance", severity="meh",
                detected_by="monitor",
            )

    def test_safety_violation_detected_rejects_invalid_severity(self):
        with pytest.raises(ValidationError):
            SafetyViolationDetected(
                violation_type="t", severity="bad", violated_rule="r",
                entity_type="e", entity_id="1", detected_by="d",
            )

    def test_kg_anomaly_detected_rejects_invalid_severity(self):
        with pytest.raises(ValidationError):
            KGAnomalyDetected(anomaly_type="t", severity="whoa", detected_by="d")

    def test_governance_emergency_stop_default_is_a_real_severity(self):
        event = GovernanceEmergencyStop(
            scope="engine", reason="r", triggered_by="t",
        )
        assert event.severity == Severity.CRITICAL

    def test_governance_emergency_stop_rejects_invalid_severity(self):
        with pytest.raises(ValidationError):
            GovernanceEmergencyStop(
                scope="engine", reason="r", triggered_by="t", severity="nah",
            )
