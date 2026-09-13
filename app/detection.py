from __future__ import annotations

from typing import Any


def null_rate_check(table: str, column: str, current_value: float, expected_max: float = 0.01) -> dict[str, Any]:
    return {"metric": "null_rate", "table": table, "column": column, "current_value": current_value, "expected_max": expected_max, "status": "FAIL" if current_value > expected_max else "PASS"}


def row_count_check(table: str, current_value: int, expected_min: int) -> dict[str, Any]:
    return {"metric": "row_count", "table": table, "current_value": current_value, "expected_min": expected_min, "status": "FAIL" if current_value < expected_min else "PASS"}


def duplicate_check(table: str, duplicate_count: int) -> dict[str, Any]:
    return {"metric": "duplicates", "table": table, "current_value": duplicate_count, "status": "FAIL" if duplicate_count else "PASS"}
