from __future__ import annotations

import hashlib
import json
from typing import Any


class QdrantMemory:
    """Optional Qdrant adapter; local JSON memory remains the deterministic fallback."""

    def __init__(self, url: str, api_key: str | None = None, collection: str = "incident_memory"):
        from qdrant_client import QdrantClient
        self.client = QdrantClient(url=url, api_key=api_key or None)
        self.collection = collection
        from qdrant_client.models import Distance, VectorParams
        if not self.client.collection_exists(collection):
            self.client.create_collection(collection_name=collection, vectors_config=VectorParams(size=32, distance=Distance.COSINE))

    @staticmethod
    def vector(text: str, size: int = 32) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [(byte / 255.0) for byte in (digest * ((size // len(digest)) + 1))[:size]]

    def store(self, record: dict[str, Any]) -> None:
        from qdrant_client.models import PointStruct
        payload = json.loads(json.dumps(record, default=str))
        vector = self.vector(json.dumps(payload, sort_keys=True))
        point_id = int(hashlib.sha256(payload.get("incident_id", json.dumps(payload)).encode()).hexdigest()[:16], 16)
        self.client.upsert(self.collection, [PointStruct(id=point_id, vector=vector, payload=payload)])

    def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        result = self.client.search(self.collection, query_vector=self.vector(query), limit=limit)
        return [hit.payload for hit in result]
