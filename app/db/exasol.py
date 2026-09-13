from __future__ import annotations

import csv
import ssl
from pathlib import Path
from typing import Any

import pyexasol


TABLE_DEFINITIONS = {
    "customers": "customer_id VARCHAR(36), first_name VARCHAR(100), last_name VARCHAR(100), email VARCHAR(255), phone VARCHAR(40), country VARCHAR(80), state VARCHAR(80), city VARCHAR(100), signup_date DATE, segment VARCHAR(40), status VARCHAR(40), created_at TIMESTAMP, updated_at TIMESTAMP",
    "products": "product_id VARCHAR(36), product_name VARCHAR(255), category VARCHAR(100), brand VARCHAR(100), price DECIMAL(18,2), cost DECIMAL(18,2), stock DECIMAL(18,0), supplier VARCHAR(150), status VARCHAR(40), created_at TIMESTAMP, updated_at TIMESTAMP",
    "orders": "order_id VARCHAR(36), customer_id VARCHAR(36), order_date DATE, status VARCHAR(40), currency VARCHAR(10), subtotal DECIMAL(18,2), discount DECIMAL(18,2), tax DECIMAL(18,2), shipping DECIMAL(18,2), total DECIMAL(18,2), payment_id VARCHAR(36), shipping_address_id VARCHAR(36), created_at TIMESTAMP, updated_at TIMESTAMP",
    "order_items": "order_item_id VARCHAR(36), order_id VARCHAR(36), product_id VARCHAR(36), quantity DECIMAL(18,0), unit_price DECIMAL(18,2), discount DECIMAL(18,2), line_total DECIMAL(18,2), created_at TIMESTAMP",
    "payments": "payment_id VARCHAR(36), order_id VARCHAR(36), method VARCHAR(40), status VARCHAR(40), amount DECIMAL(18,2), currency VARCHAR(10), transaction_timestamp TIMESTAMP, gateway VARCHAR(80), failure_reason VARCHAR(255)",
    "shipments": "shipment_id VARCHAR(36), order_id VARCHAR(36), carrier VARCHAR(80), method VARCHAR(80), status VARCHAR(40), shipped_at TIMESTAMP, delivered_at TIMESTAMP, estimated_delivery_date DATE, actual_delivery_date DATE, warehouse VARCHAR(100)",
    "daily_business_metrics": "metric_date DATE, total_orders DECIMAL(18,0), revenue DECIMAL(18,2), average_order_value DECIMAL(18,2), conversion_rate DECIMAL(10,6), refund_rate DECIMAL(10,6), payment_failure_rate DECIMAL(10,6), average_delivery_days DECIMAL(10,2)",
    "data_quality_metrics": "metric_id VARCHAR(36), metric_date DATE, table_name VARCHAR(100), column_name VARCHAR(100), metric VARCHAR(80), current_value DECIMAL(24,8), expected_max DECIMAL(24,8), status VARCHAR(20)",
}


class ExasolAdapter:
    def __init__(self, dsn: str, user: str, password: str, schema: str = "INCIDENT_ANALYTICS", encryption: bool = True):
        self.dsn, self.user, self.password, self.schema, self.encryption = dsn, user, password, schema, encryption

    def connect(self) -> Any:
        return pyexasol.connect(
            dsn=self.dsn,
            user=self.user,
            password=self.password,
            encryption=self.encryption,
            websocket_sslopt={"cert_reqs": ssl.CERT_NONE},
        )

    def create_schema(self) -> None:
        connection = self.connect()
        try:
            connection.execute(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"')
            connection.execute(f'OPEN SCHEMA "{self.schema}"')
            for table, definition in TABLE_DEFINITIONS.items():
                connection.execute(f'CREATE OR REPLACE TABLE "{table}" ({definition})')
        finally:
            connection.close()

    def seed_csv(self, data_dir: Path) -> dict[str, int]:
        connection = self.connect()
        counts: dict[str, int] = {}
        try:
            connection.execute(f'OPEN SCHEMA "{self.schema}"')
            for table in TABLE_DEFINITIONS:
                path = data_dir / f"{table}.csv"
                if not path.exists():
                    continue
                connection.execute(f'TRUNCATE TABLE "{table}"')
                connection.import_from_file(str(path), table, import_params={"skip": 1, "with_column_names": False})
                counts[table] = sum(1 for _ in csv.DictReader(path.open()))
        finally:
            connection.close()
        return counts
