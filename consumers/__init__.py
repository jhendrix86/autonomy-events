"""
Ready-to-use event consumers built on top of autonomy_events' EventConsumer.

Not exported from the top-level autonomy_events package (that package is
the transport/schema library; these are opinionated handlers a specific
service wires in) - import directly as
`from consumers.dlq_remediation_consumer import DLQRemediationConsumer`.

This __init__.py itself is what makes `consumers` a real installable
package - it had none until 2026-08-10, meaning DLQRemediationConsumer was
never actually part of the autonomy-events distribution (find_packages()
in setup.py silently excludes directories with no __init__.py), so no
editable-install consumer of this repo could import it via any package
mechanism. See OS42_REPAIR_PLAN.md's Stage 3 reconciliation notes.
"""

from .dlq_remediation_consumer import DLQRemediationConsumer, RetryStrategy

__all__ = ["DLQRemediationConsumer", "RetryStrategy"]
