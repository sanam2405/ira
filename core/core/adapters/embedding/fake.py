"""Deterministic offline embedding — no API key, no network.

Lets the full ingest -> embed -> index -> search flow run and be tested without Gemini.
Vectors are seeded from a hash of the text, so the same text always maps to the same
vector (similarity is meaningless, but the plumbing is exercised faithfully).
"""

import hashlib

import numpy as np

from core.domain import TaskType
from core.ports import EmbeddingProvider


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimensions: int = 768):
        self._dims = dimensions

    @property
    def model_id(self) -> str:
        return f"fake-{self._dims}d"

    @property
    def dimensions(self) -> int:
        return self._dims

    def embed(self, texts: list[str], task_type: TaskType) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
            rng = np.random.default_rng(seed)
            out.append(rng.standard_normal(self._dims).astype(np.float32).tolist())
        return out
