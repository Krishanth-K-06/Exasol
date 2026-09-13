from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text


SCHEMA_SQL = Path(__file__).with_name("postgres_schema.sql")


class PostgresStore:
    def __init__(self, url: str):
        self.engine = create_engine(url, pool_pre_ping=True)

    def initialize(self) -> None:
        statements = SCHEMA_SQL.read_text().split(";")
        with self.engine.begin() as connection:
            for statement in statements:
                if statement.strip():
                    connection.execute(text(statement))

    def execute(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.engine.begin() as connection:
            result = connection.execute(text(query), params or {})
            return [dict(row._mapping) for row in result]
