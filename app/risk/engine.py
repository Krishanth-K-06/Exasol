from __future__ import annotations

from app.schemas.incident import IncidentState, RiskAssessment


class RiskEngine:
    def assess(self, incident: IncidentState) -> RiskAssessment:
        score = 0
        reasons: list[str] = []
        proposal = incident.proposed_fix
        if proposal and proposal.sql and "DELETE" in proposal.sql.upper():
            score += 35
            reasons.append("destructive SQL is proposed")
        if incident.incident_type in {"DUPLICATE_ANOMALY", "BUSINESS_METRIC_DRIFT"}:
            score += 25
            reasons.append("business or financial metrics may be affected")
        if incident.incident_type == "SCHEMA_MISMATCH":
            score += 10
            reasons.append("mapping change has downstream dependencies")
        if incident.simulation_result and incident.simulation_result.get("blast_radius") == "LOW":
            reasons.append("sandbox blast radius is low")
        else:
            score += 20
        if incident.confidence < 0.85:
            score += 20
            reasons.append("root-cause confidence is below 0.85")
        if proposal and proposal.rollback_strategy:
            reasons.append("rollback strategy is available")
        else:
            score += 30
            reasons.append("rollback strategy is missing")
        score = min(score, 100)
        level = "LOW" if score < 25 else "MEDIUM" if score < 50 else "HIGH" if score < 75 else "CRITICAL"
        return RiskAssessment(score=score, level=level, reasons=reasons, requires_approval=level in {"HIGH", "CRITICAL"}, rollback_available=bool(proposal and proposal.rollback_strategy))
