from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas.incident import IncidentState


class DeploymentController:
    """Dry-run production boundary for the local MVP; every deploy has a snapshot and rollback record."""

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def deploy(self, incident: IncidentState) -> dict[str, Any]:
        snapshot = self.state_dir / f"snapshot-{incident.incident_id}.json"
        snapshot.write_text(json.dumps(incident.model_dump(mode="json"), indent=2))
        return {"status": "SUCCESS", "environment": "sandbox-backed-production-demo", "snapshot": str(snapshot), "rollback_available": True}

    def rollback(self, incident: IncidentState) -> dict[str, Any]:
        snapshot = self.state_dir / f"snapshot-{incident.incident_id}.json"
        return {"status": "SUCCESS" if snapshot.exists() else "FAILED", "snapshot": str(snapshot), "rollback_available": snapshot.exists()}
