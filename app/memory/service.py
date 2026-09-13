from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.platform import LocalMemory


class MemoryService:
    def __init__(self, state_dir: Path, qdrant_url: str | None = None, qdrant_api_key: str | None = None):
        self.local = LocalMemory(state_dir / "incident_memory.json")
        self.qdrant = None
        if qdrant_url:
            try:
                from app.memory_qdrant import QdrantMemory
                self.qdrant = QdrantMemory(qdrant_url, qdrant_api_key)
            except Exception:
                self.qdrant = None

    def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        if self.qdrant:
            try:
                return self.qdrant.search(query, limit)
            except Exception:
                pass
        return self.local.search(query, limit)

    def store(self, record: dict[str, Any]) -> None:
        self.local.store(record)
        if self.qdrant:
            try:
                self.qdrant.store(record)
            except Exception:
                pass
