from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from app.agents.provider import LLMProvider, MockLLMProvider
from app.schemas.incident import FixProposal, IncidentState


class EngineerAgent:
    """Produces proposals only. The control layer owns authorization and execution."""

    def __init__(self, provider: LLMProvider | None = None):
        self.provider = provider or MockLLMProvider()

    def propose(self, incident: IncidentState) -> FixProposal:
        scenario = incident.scenario_id or ""
        table = incident.affected_table
        statements: dict[str, tuple[str, str, str]] = {
            "SCN-01": (f"INSERT INTO {table}_sandbox SELECT * FROM {table}_source WHERE batch_id = :missing_batch", "Replay the missing source partition.", "Remove replayed partition rows by batch id."),
            "SCN-02": ("UPDATE raw_orders SET customer_id = customer_identifier WHERE customer_id IS NULL AND customer_identifier IS NOT NULL", "Map the renamed upstream customer_identifier back to customer_id and replay the transformation.", "Restore the pre-deployment mapping and rerun the affected partition."),
            "SCN-03": (f"UPDATE {table} SET customer_id = source_customer_id WHERE customer_id IS NULL AND source_customer_id IS NOT NULL", "Repair null customer mappings from the source identifier.", "Restore the previous transformation snapshot."),
            "SCN-04": (f"DELETE FROM {table} WHERE duplicate_rank > 1 AND duplicate_group_id = :group_id", "Keep the deterministic canonical record and remove replay duplicates.", "Restore deleted records from the captured sandbox snapshot."),
            "SCN-05": ("CALL resume_pipeline(:pipeline_id)", "Resume the stale scheduled aggregation job.", "Stop the resumed job and restore the previous checkpoint."),
            "SCN-06": ("UPDATE daily_revenue SET revenue = subtotal - discount + tax + shipping WHERE metric_date = :metric_date", "Restore the approved revenue calculation.", "Restore the prior daily metric snapshot."),
            "SCN-07": ("DELETE FROM clean_orders WHERE customer_id NOT IN (SELECT customer_id FROM customers)", "Quarantine orders with invalid customer references.", "Restore quarantined records from the snapshot after customer recovery."),
            "SCN-08": ("CALL replay_partition(:partition_id)", "Replay the incomplete source partition.", "Restore the partition checkpoint."),
            "SCN-09": ("DELETE FROM payments WHERE transaction_id = :transaction_id AND canonical = FALSE", "Remove duplicate successful payment transactions while retaining the canonical payment.", "Restore duplicate payments from the captured snapshot."),
            "SCN-10": ("CALL backfill_late_partition(:partition_id)", "Backfill late-arriving events and recompute downstream metrics.", "Restore downstream metrics from the pre-backfill snapshot."),
        }
        sql, description, rollback = statements.get(scenario, ("SELECT 1", "No mutation proposal is available for this scenario.", "No deployment."))
        deterministic_fix = FixProposal(
            fix_type="SQL" if sql.startswith(("UPDATE", "DELETE", "INSERT")) else "PIPELINE",
            sql=sql,
            description=description,
            expected_effect="Restore the scenario verification criteria without changing unrelated tables.",
            estimated_rows_affected=0,
            rollback_strategy=rollback,
            risk_factors=["requires sandbox execution", "must be verified after deployment"],
            idempotency_key=re.sub(r"[^A-Za-z0-9]+", "-", f"{incident.incident_id}-{scenario}-{uuid4()}")[:80],
        )
        if isinstance(self.provider, MockLLMProvider):
            return deterministic_fix

        try:
            model_fix = self.provider.structured(
                "You are a data reliability engineer. Propose a reversible, minimal fix. Return only structured JSON.",
                f"Incident: {incident.model_dump_json()}\nDeterministic candidate: {deterministic_fix.model_dump_json()}",
                FixProposal,
            )
            return model_fix.model_copy(update={"idempotency_key": deterministic_fix.idempotency_key})
        except Exception:
            return deterministic_fix
