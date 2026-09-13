from __future__ import annotations

import csv
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.db.postgres import PostgresStore


ROOT = Path(os.getenv("DATA_ROOT", "/Users/admin/Downloads/autonomous_data_incident_platform"))
TABLES = {
    "pipeline_metadata": "metadata/pipeline_metadata.csv",
    "data_lineage": "metadata/data_lineage.csv",
    "schema_history": "metadata/schema_history.csv",
    "pipeline_logs": "metadata/pipeline_logs.csv",
}


def main() -> None:
    store = PostgresStore(os.getenv("POSTGRES_URL", "postgresql+psycopg://incident:mock-postgres-password@localhost:5432/incidents"))
    store.initialize()
    with store.engine.begin() as connection:
        for table, relative_path in TABLES.items():
            path = ROOT / relative_path
            if not path.exists():
                continue
            rows = list(csv.DictReader(path.open()))
            if not rows:
                continue
            columns = list(rows[0])
            for row in rows:
                row.setdefault("pipeline_id", row.get("pipeline_id") or str(uuid.uuid4()))
                row.setdefault("lineage_id", row.get("lineage_id") or str(uuid.uuid4()))
                row.setdefault("schema_version_id", row.get("schema_version_id") or str(uuid.uuid4()))
                row.setdefault("log_id", row.get("log_id") or str(uuid.uuid4()))
                placeholders = ", ".join(f":{column}" for column in columns)
                names = ", ".join(f'"{column}"' for column in columns)
                connection.execute(text(f'INSERT INTO {table} ({names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'), row)
            print(f"seeded {table}: {len(rows)}")


if __name__ == "__main__":
    main()
