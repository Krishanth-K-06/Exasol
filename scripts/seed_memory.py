from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.memory.service import MemoryService


def main() -> None:
    root = Path(os.getenv("DATA_ROOT", "/Users/admin/Downloads/autonomous_data_incident_platform"))
    state_dir = Path(os.getenv("LOCAL_STATE_DIR", ".local-state"))
    qdrant_url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    incidents_path = root / "incidents" / "incidents.csv"
    fixes_path = root / "incidents" / "incident_fixes.csv"
    fixes = {}
    with fixes_path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            fixes.setdefault(row["incident_id"], []).append(row)
    memory = MemoryService(state_dir, qdrant_url, qdrant_api_key)
    count = 0
    with incidents_path.open(newline="") as handle:
        for incident in csv.DictReader(handle):
            record = {"incident_id": incident["incident_id"], "incident_type": incident["incident_type"], "affected_table": incident["affected_table"], "symptoms": incident["symptoms"], "root_cause": incident["root_cause"], "resolution": incident["resolution"], "outcome": incident["status"], "fixes": fixes.get(incident["incident_id"], [])}
            memory.store(record)
            count += 1
    print(f"seeded incident memory: {count}")


if __name__ == "__main__":
    main()