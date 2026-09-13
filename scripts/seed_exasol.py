from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.exasol import ExasolAdapter


root = Path(os.getenv("DATA_ROOT", "/Users/admin/Downloads/autonomous_data_incident_platform"))
adapter = ExasolAdapter(
	os.getenv("EXASOL_DSN", "127.0.0.1:8563"),
	os.getenv("EXASOL_USER", "sys"),
	os.getenv("EXASOL_PASSWORD", "exasol"),
	os.getenv("EXASOL_SCHEMA", "INCIDENT_ANALYTICS"),
	os.getenv("EXASOL_ENCRYPTION", "True").lower() in {"1", "true", "yes"},
)
adapter.create_schema()
print(adapter.seed_csv(root / "data"))
