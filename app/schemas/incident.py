from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
IncidentStatus = Literal[
    "DETECTED", "INVESTIGATING", "FIX_PROPOSED", "SIMULATING", "WAITING_APPROVAL",
    "DEPLOYING", "RESOLVED", "ROLLED_BACK", "BLOCKED", "FAILED",
]


class Evidence(BaseModel):
    metric: str
    table: str | None = None
    column: str | None = None
    current_value: float | int | str | None = None
    expected_value: float | int | str | None = None
    status: Literal["PASS", "FAIL", "INFO"] = "INFO"
    details: str = ""


class FixProposal(BaseModel):
    fix_type: Literal["SQL", "PYTHON", "PIPELINE"]
    sql: str | None = None
    description: str
    expected_effect: str
    estimated_rows_affected: int = 0
    rollback_strategy: str
    risk_factors: list[str] = Field(default_factory=list)
    idempotency_key: str


class VerificationResult(BaseModel):
    status: Literal["PASS", "FAIL"]
    checks: dict[str, str]
    before_metrics: dict[str, Any] = Field(default_factory=dict)
    after_metrics: dict[str, Any] = Field(default_factory=dict)
    failures: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    level: Severity
    reasons: list[str] = Field(default_factory=list)
    requires_approval: bool
    rollback_available: bool


class IncidentState(BaseModel):
    incident_id: str = Field(default_factory=lambda: str(uuid4()))
    scenario_id: str | None = None
    incident_type: str
    severity: Severity
    affected_table: str
    symptoms: str
    evidence: list[Evidence] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None
    status: IncidentStatus = "DETECTED"
    investigation: dict[str, Any] = Field(default_factory=dict)
    root_cause: str | None = None
    confidence: float = 0.0
    similar_incidents: list[dict[str, Any]] = Field(default_factory=list)
    proposed_fix: FixProposal | None = None
    control_decision: dict[str, Any] | None = None
    simulation_result: dict[str, Any] | None = None
    verification_result: VerificationResult | None = None
    risk_assessment: RiskAssessment | None = None
    approval_status: str = "NOT_REQUIRED"
    deployment_status: str = "NOT_STARTED"
    rollback_status: str = "NOT_REQUIRED"
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None

    def event(self, action: str, result: str = "OK", **metadata: Any) -> None:
        self.timeline.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "result": result,
            "metadata": metadata,
        })


class IncidentCreate(BaseModel):
    incident_type: str
    affected_table: str = "orders"
    symptoms: str
    severity: Severity = "MEDIUM"
    scenario_id: str | None = None


class ApprovalRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=120)
    decision: Literal["APPROVE", "REJECT"]
    reason: str = Field(min_length=1, max_length=2000)
