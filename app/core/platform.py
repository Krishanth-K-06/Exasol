from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class Incident:
    incident_id: str
    incident_type: str
    severity: str
    affected_table: str
    symptoms: str
    status: str = "DETECTED"
    detected_at: str = ""
    resolved_at: str | None = None
    root_cause: str | None = None
    confidence: float = 0.0
    proposed_fix: dict[str, Any] | None = None
    simulation: dict[str, Any] | None = None
    verification: dict[str, Any] | None = None
    risk: dict[str, Any] | None = None
    approval_status: str = "NOT_REQUIRED"
    deployment_status: str = "NOT_STARTED"
    rollback_status: str = "NOT_REQUIRED"

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_incident(incident_type: str, table: str, symptoms: str, severity: str = "MEDIUM") -> Incident:
    return Incident(str(uuid.uuid4()), incident_type, severity, table, symptoms, detected_at=utc_now())


class LocalMemory:
    """Small deterministic memory backend used when Qdrant is unavailable."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text())

    def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        tokens = set(re.findall(r"[a-z0-9_]+", query.lower()))
        scored = []
        for item in self._read():
            text = json.dumps(item).lower()
            score = sum(token in text for token in tokens)
            if score:
                scored.append((score, item))
        return [item for _, item in sorted(scored, key=lambda pair: pair[0], reverse=True)[:limit]]

    def store(self, record: dict[str, Any]) -> None:
        records = self._read()
        records.append(record)
        self.path.write_text(json.dumps(records, indent=2, default=str))


class IncidentStore:
    """Operational store with a PostgreSQL implementation and JSON fallback for demo mode."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, incident: Incident) -> None:
        records = self.all()
        records = [record for record in records if record["incident_id"] != incident.incident_id]
        records.append(incident.as_dict())
        self.path.write_text(json.dumps(records, indent=2, default=str))

    def get(self, incident_id: str) -> Incident | None:
        for record in self.all():
            if record["incident_id"] == incident_id:
                return Incident(**record)
        return None

    def all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text())
