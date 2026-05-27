"""In-memory numpy SearchBackend.

At 2.3k songs (~14k multi-vectors) the whole index is a few tens of MB; brute-force
cosine over a normalized matrix is sub-millisecond. Persists to disk so the api can
mmap-load it at startup. Swap for Typesense/Turbopuffer behind the same port later.

Vectors are L2-normalized on index and query, so cosine similarity == dot product.
(gemini-embedding-001 does not auto-normalize truncated outputs, so we do it here.)
"""

import json
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import structlog

from core.domain import Embedding, Field, Hit, Lang
from core.ports import SearchBackend

_VECTORS_FILE = "vectors.npy"
_META_FILE = "meta.json"


def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class LocalSearchBackend(SearchBackend):
    def __init__(self, index_dir: Path):
        self.dir = Path(index_dir)
        self.logger = structlog.get_logger(__name__).bind(
            class_name="LocalSearchBackend"
        )
        self._vectors: np.ndarray = np.empty((0, 0), dtype=np.float32)
        self._meta: list[
            dict
        ] = []  # parallel to rows: song_id, field, lang, chunk_index
        self._fields: np.ndarray = np.empty(0, dtype=object)
        self._langs: np.ndarray = np.empty(0, dtype=object)

    def index(self, embeddings: Iterable[Embedding]) -> None:
        vectors: list[list[float]] = []
        meta: list[dict] = []
        for e in embeddings:
            if e.vector is None:
                raise ValueError(f"embedding {e.id} has no vector")
            vectors.append(e.vector)
            meta.append(
                {
                    "song_id": e.song_id,
                    "field": e.field.value,
                    "lang": e.lang.value,
                    "chunk_index": e.chunk_index,
                }
            )
        self._vectors = _normalize(np.asarray(vectors, dtype=np.float32))
        self._meta = meta
        self._refresh_masks()
        self.logger.info("indexed", rows=len(meta), dims=self._vectors.shape[1])

    def search(
        self,
        vector: list[float],
        top_k: int = 20,
        fields: Iterable[Field] | None = None,
        langs: Iterable[Lang] | None = None,
    ) -> list[Hit]:
        if self._vectors.shape[0] == 0:
            return []
        q = np.asarray(vector, dtype=np.float32)
        q = q / (np.linalg.norm(q) or 1.0)
        scores = self._vectors @ q  # cosine, since both normalized

        mask = np.ones(scores.shape[0], dtype=bool)
        if fields is not None:
            mask &= np.isin(self._fields, [f.value for f in fields])
        if langs is not None:
            mask &= np.isin(self._langs, [lang.value for lang in langs])
        candidate_idx = np.flatnonzero(mask)
        if candidate_idx.size == 0:
            return []

        cand_scores = scores[candidate_idx]
        k = min(top_k, candidate_idx.size)
        top = candidate_idx[np.argpartition(-cand_scores, k - 1)[:k]]
        top = top[np.argsort(-scores[top])]
        return [
            Hit(
                song_id=self._meta[i]["song_id"],
                score=float(scores[i]),
                field=Field(self._meta[i]["field"]),
                lang=Lang(self._meta[i]["lang"]),
                chunk_index=self._meta[i]["chunk_index"],
            )
            for i in top
        ]

    # --- persistence (used by index stage to write, api to read) ---

    def save(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        np.save(self.dir / _VECTORS_FILE, self._vectors)
        (self.dir / _META_FILE).write_text(json.dumps(self._meta), encoding="utf-8")
        self.logger.info("saved", dir=str(self.dir), rows=len(self._meta))

    def load(self) -> "LocalSearchBackend":
        self._vectors = np.load(self.dir / _VECTORS_FILE)
        self._meta = json.loads((self.dir / _META_FILE).read_text(encoding="utf-8"))
        self._refresh_masks()
        return self

    def _refresh_masks(self) -> None:
        self._fields = np.array([m["field"] for m in self._meta], dtype=object)
        self._langs = np.array([m["lang"] for m in self._meta], dtype=object)
