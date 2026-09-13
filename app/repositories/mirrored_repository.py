from __future__ import annotations

from app.repositories.local_store import LocalIncidentRepository
from app.repositories.postgres_repository import PostgresIncidentRepository
from app.schemas.incident import IncidentState


class MirroredIncidentRepository:
    """Local state keeps the API available; PostgreSQL receives the operational mirror when reachable."""

    def __init__(self, local: LocalIncidentRepository, postgres: PostgresIncidentRepository | None = None):
        self.local = local
        self.postgres = postgres
        if self.postgres:
            try:
                self.postgres.initialize()
            except Exception:
                self.postgres = None

    def save(self, incident: IncidentState) -> IncidentState:
        self.local.save(incident)
        if self.postgres:
            try:
                self.postgres.save(incident)
            except Exception:
                pass
        return incident

    def get(self, incident_id: str) -> IncidentState | None:
        return self.local.get(incident_id)

    def list(self) -> list[IncidentState]:
        return self.local.list()

    def clear(self) -> None:
        self.local.clear()
