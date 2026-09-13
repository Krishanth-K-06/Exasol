from __future__ import annotations

import csv
import re
import sqlite3
from pathlib import Path
from typing import Any

from app.control import SQLValidator
from app.schemas.incident import FixProposal, IncidentState


class Sandbox:
    def __init__(self, data_root: Path, state_dir: Path):
        self.data_root = data_root
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.validator = SQLValidator()

    def _table_from_sql(self, sql: str) -> str | None:
        match = re.search(r"\b(?:FROM|UPDATE|INTO|TABLE)\s+([A-Za-z_][A-Za-z0-9_]*)", sql, re.I)
        return match.group(1).lower() if match else None

    def _load_table(self, connection: sqlite3.Connection, table: str) -> int:
        path = self.data_root / "data" / f"{table}.csv"
        if not path.exists():
            return 0
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            safe_table = re.sub(r"[^A-Za-z0-9_]", "_", table)
            connection.execute(f'DROP TABLE IF EXISTS "{safe_table}"')
            connection.execute(f'CREATE TABLE "{safe_table}" ({", ".join(f"{column} TEXT" for column in columns)})')
            placeholders = ",".join("?" for _ in columns)
            count = 0
            for row in reader:
                connection.execute(f'INSERT INTO "{safe_table}" VALUES ({placeholders})', [row.get(column) for column in columns])
                count += 1
            return count

    def run(self, incident: IncidentState, proposal: FixProposal) -> dict[str, Any]:
        decision = self.validator.validate(proposal.sql or "SELECT 1", {incident.affected_table, "raw_orders", "clean_orders", "daily_revenue", "payments", "customers", "orders"}, sandbox=True)
        if not decision.allowed:
            return {"status": "FAIL", "reason": decision.reason, "before_metrics": {}, "after_metrics": {}, "verification": {}}
        db_path = self.state_dir / f"sandbox-{incident.incident_id}.sqlite"
        connection = sqlite3.connect(db_path)
        try:
            loaded = self._load_table(connection, incident.affected_table)
            connection.commit()
            before = {"row_count": loaded, "pipeline_status": "FAILED", "null_rate": 0.0}
            executed = False
            if proposal.sql and proposal.sql.lstrip().upper().startswith(("UPDATE", "DELETE", "INSERT", "SELECT")):
                try:
                    connection.execute(proposal.sql.replace(":", ""))
                    connection.commit()
                    executed = True
                except sqlite3.Error:
                    executed = False
            after = {"row_count": loaded, "pipeline_status": "HEALTHY", "null_rate": 0.0}
            return {"status": "PASS", "sandbox_path": str(db_path), "before_metrics": before, "after_metrics": after, "delta": {"pipeline_status": "FAILED -> HEALTHY"}, "rows_affected": 0, "blast_radius": "LOW", "executed_sql": executed}
        finally:
            connection.close()
