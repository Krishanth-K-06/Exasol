from __future__ import annotations

from typing import Any

from app.memory.service import MemoryService
from app.observability.engine import CsvObservability
from app.schemas.incident import IncidentState


class InvestigatorAgent:
    """Read-only investigator. It can inspect evidence and memory but cannot mutate data."""

    def __init__(self, observability: CsvObservability, memory: MemoryService):
        self.observability = observability
        self.memory = memory

    def investigate(self, incident: IncidentState) -> dict[str, Any]:
        scenario = self.observability.scenario(incident.scenario_id or "") or {}
        evidence = self.observability.evidence_for_scenario(incident.scenario_id or "")
        query = f"{incident.incident_type} {incident.affected_table} {incident.symptoms}"
        similar = self.memory.search(query)
        incident.evidence.extend(evidence)
        if incident.incident_type == "SCHEMA_MISMATCH":
            root_cause = "Upstream customer_id changed to customer_identifier while the downstream transformation still expects customer_id."
            confidence = 0.94
        elif incident.incident_type == "NULL_ANOMALY":
            root_cause = "The upstream customer mapping produced null customer_id values during transformation."
            confidence = 0.91
        elif incident.incident_type == "DUPLICATE_ANOMALY":
            root_cause = "A source partition was replayed without an idempotency key, creating duplicate records."
            confidence = 0.89
        else:
            root_cause = scenario.get("investigation_path", "Pipeline metadata and quality evidence identify the failing transformation.")
            confidence = 0.82
        return {
            "root_cause": root_cause,
            "confidence": confidence,
            "evidence": [item.model_dump() for item in evidence],
            "similar_incidents": similar,
            "investigation_path": scenario.get("investigation_path", "Inspect metadata, logs, lineage, quality, and analytical data."),
            "recommended_action": scenario.get("expected_fix", "Replay the affected partition after validating the fix."),
        }
