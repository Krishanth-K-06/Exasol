from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    project_root: Path = Path(__file__).resolve().parents[2]
    data_root: Path = Path(os.getenv("DATA_ROOT", "/Users/admin/Downloads/autonomous_data_incident_platform"))
    state_dir: Path = Path(os.getenv("LOCAL_STATE_DIR", ".local-state"))
    postgres_url: str = os.getenv("POSTGRES_URL", "postgresql+psycopg://incident:mock-postgres-password@localhost:5432/incidents")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str | None = os.getenv("QDRANT_API_KEY")
    exasol_dsn: str = os.getenv("EXASOL_DSN", "127.0.0.1:8563")
    exasol_user: str = os.getenv("EXASOL_USER", "sys")
    exasol_password: str = os.getenv("EXASOL_PASSWORD", "exasol")
    exasol_schema: str = os.getenv("EXASOL_SCHEMA", "INCIDENT_ANALYTICS")
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    observability_backend: str = os.getenv("OBSERVABILITY_BACKEND", "csv")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    max_rows_affected: int = Field(default=100_000, ge=1)

    def ensure_state_dir(self) -> Path:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        return self.state_dir


runtime = RuntimeConfig()
