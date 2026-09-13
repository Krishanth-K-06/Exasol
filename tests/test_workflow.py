from pathlib import Path

from app.core.platform import IncidentStore, LocalMemory, new_incident
from app.workflow import IncidentWorkflow


def test_scn02_closes_and_stores_memory(tmp_path: Path):
    memory = LocalMemory(tmp_path / "memory.json")
    incident = new_incident("SCHEMA_CHANGE", "orders", "schema changed")
    result = IncidentWorkflow(memory).run(incident)
    assert result.status == "RESOLVED"
    assert result.verification["status"] == "PASS"
    assert len(memory.search("schema customer_id")) == 1
