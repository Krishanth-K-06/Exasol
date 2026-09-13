from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from app.db.exasol import ExasolAdapter
from app.schemas.incident import Evidence


class ExasolObservability:
    """Observability checks executed against the seeded Exasol analytical schema."""

    TABLE_MAP = {
        "clean_orders": "orders",
        "raw_orders": "orders",
        "daily_revenue": "daily_business_metrics",
    }

    def __init__(self, data_root: Path, adapter: ExasolAdapter):
        self.root = data_root
        self.adapter = adapter

    def _physical_table(self, table: str) -> str:
        return self.TABLE_MAP.get(table, table)

    def _query(self, sql: str) -> list[dict[str, Any]]:
        connection = self.adapter.connect()
        try:
            connection.execute(f'OPEN SCHEMA "{self.adapter.schema}"')
            statement = connection.execute(sql)
            columns = list(statement.columns().keys())
            return [dict(zip(columns, row)) for row in statement.fetchall()]
        finally:
            connection.close()

    def scenarios(self) -> list[dict[str, str]]:
        path = self.root / "failure_scenarios" / "failure_scenarios.csv"
        if not path.exists():
            return []
        with path.open(newline="") as handle:
            return list(csv.DictReader(handle))

    def scenario(self, scenario_id: str) -> dict[str, str] | None:
        return next((row for row in self.scenarios() if row.get("scenario_id") == scenario_id), None)

    def row_count(self, table: str, expected_min: int | None = None) -> Evidence:
        physical = self._physical_table(table)
        result = self._query(f'SELECT COUNT(*) AS row_count FROM "{physical}"')[0]
        actual = int(result["ROW_COUNT"])
        return Evidence(metric="row_count", table=table, current_value=actual, expected_value=expected_min, status="FAIL" if expected_min and actual < expected_min else "PASS", details=f"{actual} rows observed in Exasol")

    def null_rate(self, table: str, column: str, max_rate: float = 0.01) -> Evidence:
        physical = self._physical_table(table)
        result = self._query(f'SELECT COUNT(*) AS total_rows, SUM(CASE WHEN "{column}" IS NULL THEN 1 ELSE 0 END) AS null_rows FROM "{physical}"')[0]
        total = int(result["TOTAL_ROWS"])
        nulls = int(result["NULL_ROWS"] or 0)
        rate = nulls / total if total else 0.0
        return Evidence(metric="null_rate", table=table, column=column, current_value=rate, expected_value=max_rate, status="FAIL" if rate > max_rate else "PASS", details=f"{nulls}/{total} values are null in Exasol")

    def duplicates(self, table: str, column: str) -> Evidence:
        physical = self._physical_table(table)
        result = self._query(f'SELECT COUNT(*) - COUNT(DISTINCT "{column}") AS duplicate_count FROM "{physical}" WHERE "{column}" IS NOT NULL')[0]
        duplicate_count = int(result["DUPLICATE_COUNT"] or 0)
        return Evidence(metric="duplicates", table=table, column=column, current_value=duplicate_count, expected_value=0, status="FAIL" if duplicate_count else "PASS", details=f"{duplicate_count} duplicate records observed in Exasol")

    def foreign_key(self, child_table: str, child_column: str, parent_table: str, parent_column: str) -> Evidence:
        child = self._physical_table(child_table)
        parent = self._physical_table(parent_table)
        result = self._query(f'SELECT COUNT(*) AS missing_count FROM "{child}" child LEFT JOIN "{parent}" parent ON child."{child_column}" = parent."{parent_column}" WHERE child."{child_column}" IS NOT NULL AND parent."{parent_column}" IS NULL')[0]
        missing = int(result["MISSING_COUNT"] or 0)
        return Evidence(metric="foreign_key", table=child_table, column=child_column, current_value=missing, expected_value=0, status="FAIL" if missing else "PASS", details=f"{missing} references missing from {parent_table} in Exasol")

    def evidence_for_scenario(self, scenario_id: str) -> list[Evidence]:
        scenario = self.scenario(scenario_id)
        if not scenario:
            return []
        table = scenario.get("affected_table", "orders")
        incident_type = scenario.get("incident_type", "DATA_QUALITY")
        if incident_type in {"NULL_SPIKE", "NULL_EXPLOSION", "NULL_ANOMALY"}:
            return [self.null_rate(table, "customer_id", 0.01)]
        if incident_type in {"DUPLICATE_RECORDS", "DUPLICATE_PAYMENTS", "DUPLICATE_ANOMALY"}:
            column = "payment_id" if "PAYMENT" in incident_type else "order_id"
            return [self.duplicates(table, column)]
        if incident_type in {"REFERENTIAL_INTEGRITY", "FOREIGN_KEY_CORRUPTION"}:
            return [self.foreign_key(table, "customer_id", "customers", "customer_id")]
        return [self.row_count(table, 1)]

    def run_baseline_checks(self) -> list[Evidence]:
        return [
            self.row_count("customers", 1),
            self.row_count("orders", 1),
            self.null_rate("orders", "customer_id"),
            self.duplicates("orders", "order_id"),
            self.foreign_key("orders", "customer_id", "customers", "customer_id"),
            self.foreign_key("order_items", "order_id", "orders", "order_id"),
            self.foreign_key("order_items", "product_id", "products", "product_id"),
        ]

    def report(self) -> dict[str, Any]:
        checks = self.run_baseline_checks()
        return {"checks": [check.model_dump() for check in checks], "failed": sum(check.status == "FAIL" for check in checks), "source": "exasol"}