from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from sqlalchemy import text

from app.db.postgres import PostgresStore
from app.schemas.incident import IncidentState


class PostgresIncidentRepository:
    """Operational persistence. The API can use LocalIncidentRepository when Postgres is unavailable."""

    def __init__(self, store: PostgresStore):
        self.store = store

    def initialize(self) -> None:
        self.store.initialize()

    def save(self, incident: IncidentState) -> IncidentState:
        payload = incident.model_dump(mode="json")
        query = text("""
            INSERT INTO incidents (incident_id, detected_at, resolved_at, severity, affected_table, incident_type, symptoms, root_cause, resolution, status)
            VALUES (:incident_id, :detected_at, :resolved_at, :severity, :affected_table, :incident_type, :symptoms, :root_cause, :resolution, :status)
            ON CONFLICT (incident_id) DO UPDATE SET resolved_at=:resolved_at, severity=:severity, root_cause=:root_cause, resolution=:resolution, status=:status
        """)
        with self.store.engine.begin() as connection:
            connection.execute(query, {**payload, "resolution": payload.get("proposed_fix", {}).get("description") if payload.get("proposed_fix") else None})
            connection.execute(text("INSERT INTO audit_logs (audit_id, incident_id, actor, action, target, timestamp, result, metadata) VALUES (:audit_id, :incident_id, 'workflow', 'STATE_SAVED', 'incident', now(), 'OK', CAST(:metadata AS jsonb))"), {"audit_id": str(uuid4()), "incident_id": incident.incident_id, "metadata": json.dumps({"status": incident.status})})
        return incident
