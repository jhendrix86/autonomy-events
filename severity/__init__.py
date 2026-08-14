"""
Canonical severity scale for the OS42 fleet.

Added 2026-08-14 to fix a real, found problem (not a hypothetical one):
severity was represented at least four different, mutually incompatible
ways across the fleet before this -

- governance-engine's RuleSeverity: info/low/medium/high/critical (5 levels)
- monitoring-engine's AlertSeverity: info/warning/error/critical (4 levels,
  different vocabulary - "warning"/"error" don't map cleanly onto
  governance's "low"/"medium"/"high")
- priority-scheduler's raw numeric 0-10 priority score, bucketed ad hoc
  at >=8 / >=5 wherever it was read
- this very package's own schemas/pydantic/*.py event files: free-text
  `severity: str` fields with no validation at all, just a docstring
  convention ("low, medium, high, critical") - any string passed pydantic
  validation

None of these could be principledly compared against each other - there
was no way to answer "is this CRITICAL governance violation more urgent
than that ERROR-level monitoring alert" without inventing an answer on
the spot.

Deliberately separate from EventPriority (envelope.py): priority is about
how urgently an EVENT should be routed/processed through the message
system; severity is about how bad the underlying CONDITION is. A
LOW-severity condition can be HIGH priority to process quickly (e.g. a
minor-but-time-sensitive check), and vice versa - conflating the two
would lose real information, not simplify anything.

Consumers with their own local severity/priority concept should keep it
where it has real domain value (e.g. priority-scheduler's numeric
ordering is genuinely useful for scheduling math) rather than being
forced to replace it - but should provide a mapping function to Severity
at any boundary where they report outward to another system. See each
engine's own severity_mapping.py (or equivalent) for its specific
conversion.
"""

from enum import Enum


class Severity(str, Enum):
    """Canonical severity scale - 5 levels, matching governance-engine's
    real, already-live usage (the most fine-grained real scale already
    in the fleet before this, not invented fresh). str-based so it
    serializes as a readable value in real JSON events, not an opaque
    integer."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Explicit rank table for ordering comparisons. A str Enum doesn't get
# free ordering from Python, and an IntEnum would lose the readable
# string value on the wire - this is deliberately a separate lookup
# rather than mixing in int-ness.
_SEVERITY_RANK = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


def severity_at_least(severity: Severity, threshold: Severity) -> bool:
    """True if `severity` is at least as severe as `threshold`.

    e.g. severity_at_least(Severity.HIGH, Severity.MEDIUM) -> True
    """
    return _SEVERITY_RANK[severity] >= _SEVERITY_RANK[threshold]


def max_severity(*severities: Severity) -> Severity:
    """The most severe of the given severities - useful when a single
    outcome (e.g. one alert) is derived from multiple underlying
    signals, each with its own severity."""
    if not severities:
        raise ValueError("max_severity() requires at least one Severity")
    return max(severities, key=lambda s: _SEVERITY_RANK[s])
