from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas.incident import IncidentState


class LocalIncidentRepository:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text())

    def save(self, incident: IncidentState) -> IncidentState:
        records = [record for record in self._read() if record["incident_id"] != incident.incident_id]
        records.append(incident.model_dump(mode="json"))
        self.path.write_text(json.dumps(records, indent=2, default=str))
        return incident

    def get(self, incident_id: str) -> IncidentState | None:
        record = next((item for item in self._read() if item["incident_id"] == incident_id), None)
        return IncidentState.model_validate(record) if record else None

    def list(self) -> list[IncidentState]:
        return [IncidentState.model_validate(item) for item in self._read()]

    def clear(self) -> None:
        self.path.write_text("[]")
