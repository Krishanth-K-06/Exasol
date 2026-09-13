from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

from app.schemas.incident import Evidence


class CsvObservability:
    """Deterministic quality checks over the supplied clean CSV dataset."""

    def __init__(self, data_root: Path):
        self.root = data_root
        self.data_dir = data_root / "data"
        self.metadata_dir = data_root / "metadata"
        self.quality_dir = data_root / "quality"

    def rows(self, table: str) -> list[dict[str, str]]:
        path = self.data_dir / f"{table}.csv"
        if not path.exists():
            return []
        with path.open(newline="") as handle:
            return list(csv.DictReader(handle))

    def quality_rows(self) -> list[dict[str, str]]:
        path = self.quality_dir / "data_quality_metrics.csv"
        if not path.exists():
            return []
        with path.open(newline="") as handle:
            return list(csv.DictReader(handle))

    def scenarios(self) -> list[dict[str, str]]:
        path = self.root / "failure_scenarios" / "failure_scenarios.csv"
        if not path.exists():
            return []
        with path.open(newline="") as handle:
            return list(csv.DictReader(handle))

    def row_count(self, table: str, expected_min: int | None = None) -> Evidence:
        actual = len(self.rows(table))
        return Evidence(metric="row_count", table=table, current_value=actual, expected_value=expected_min, status="FAIL" if expected_min and actual < expected_min else "PASS", details=f"{actual} rows observed")

    def null_rate(self, table: str, column: str, max_rate: float = 0.01) -> Evidence:
        records = self.rows(table)
        nulls = sum(1 for record in records if not record.get(column, "").strip())
        rate = nulls / len(records) if records else 0.0
        return Evidence(metric="null_rate", table=table, column=column, current_value=rate, expected_value=max_rate, status="FAIL" if rate > max_rate else "PASS", details=f"{nulls}/{len(records)} values are null")

    def duplicates(self, table: str, column: str) -> Evidence:
        values = [row.get(column, "") for row in self.rows(table)]
        counts = Counter(value for value in values if value)
        duplicate_count = sum(count - 1 for count in counts.values() if count > 1)
        return Evidence(metric="duplicates", table=table, column=column, current_value=duplicate_count, expected_value=0, status="FAIL" if duplicate_count else "PASS", details=f"{duplicate_count} duplicate records")

    def foreign_key(self, child_table: str, child_column: str, parent_table: str, parent_column: str) -> Evidence:
        parent_values = {row.get(parent_column) for row in self.rows(parent_table)}
        missing = sum(1 for row in self.rows(child_table) if row.get(child_column) not in parent_values)
        return Evidence(metric="foreign_key", table=child_table, column=child_column, current_value=missing, expected_value=0, status="FAIL" if missing else "PASS", details=f"{missing} references missing from {parent_table}")

    def freshness(self, table: str, timestamp_column: str, expected_date: str) -> Evidence:
        records = self.rows(table)
        latest = max((row.get(timestamp_column, "") for row in records), default="")
        return Evidence(metric="freshness", table=table, column=timestamp_column, current_value=latest, expected_value=expected_date, status="PASS" if latest[:10] >= expected_date else "FAIL", details=f"latest value: {latest}")

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

    def scenario(self, scenario_id: str) -> dict[str, str] | None:
        return next((row for row in self.scenarios() if row.get("scenario_id") == scenario_id), None)

    def evidence_for_scenario(self, scenario_id: str) -> list[Evidence]:
        scenario = self.scenario(scenario_id)
        if not scenario:
            return []
        table = scenario.get("affected_table", "orders")
        incident_type = scenario.get("incident_type", "DATA_QUALITY")
        if incident_type in {"NULL_SPIKE", "NULL_EXPLOSION"}:
            return [self.null_rate(table, "customer_id", 0.01)]
        if incident_type in {"DUPLICATE_RECORDS", "DUPLICATE_PAYMENTS"}:
            column = "payment_id" if "PAYMENT" in incident_type else "order_id"
            return [self.duplicates(table, column)]
        if incident_type in {"REFERENTIAL_INTEGRITY", "FOREIGN_KEY_CORRUPTION"}:
            return [self.foreign_key("orders", "customer_id", "customers", "customer_id")]
        if incident_type in {"VOLUME_ANOMALY", "PARTIAL_INGESTION", "ROW_COUNT_COLLAPSE"}:
            return [self.row_count(table, max(1, len(self.rows(table))))]
        return [Evidence(metric="schema", table=table, status="FAIL", details=scenario.get("symptoms", "schema validation failed"))]

    def report(self) -> dict[str, Any]:
        checks = self.run_baseline_checks()
        return {"checks": [check.model_dump() for check in checks], "failed": sum(check.status == "FAIL" for check in checks)}
