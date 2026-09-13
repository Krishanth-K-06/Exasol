from __future__ import annotations

from typing import Any

from app.schemas.incident import IncidentState, VerificationResult


class VerifierAgent:
    """Explains deterministic results; it cannot turn a failed check into a pass."""

    def verify(self, incident: IncidentState, checks: dict[str, str], before: dict[str, Any], after: dict[str, Any]) -> VerificationResult:
        failures = [name for name, status in checks.items() if status != "PASS"]
        return VerificationResult(status="FAIL" if failures else "PASS", checks=checks, before_metrics=before, after_metrics=after, failures=failures)
