"""Gemini EmbeddingProvider — gemini-embedding-001 by default (see config).

Truncates to `dimensions` via Matryoshka. Splits inputs into request-sized batches and
runs them **concurrently** on a thread pool, retrying transient errors. Output is
L2-normalized downstream by the SearchBackend (001 does not normalize truncated vectors
itself). For the one-time full corpus run prefer `GeminiBatchEmbeddingProvider` (50%
cheaper via the Batch API).
"""

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from core.concurrency import parallel_map
from core.config import settings
from core.domain import TaskType
from core.ports import EmbeddingProvider

# embed_content accepts multiple inputs per call; keep batches modest to respect
# per-request token limits on long fields.
_BATCH_SIZE = 50

_TASK_TYPE = {
    TaskType.DOCUMENT: "RETRIEVAL_DOCUMENT",
    TaskType.QUERY: "RETRIEVAL_QUERY",
}


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str, dimensions: int):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiEmbeddingProvider")
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._dims = dimensions

    @property
    def model_id(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dims

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=30))
    def _embed_batch(self, batch: list[str], task_type: TaskType) -> list[list[float]]:
        resp = self._client.models.embed_content(
            model=self._model,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=_TASK_TYPE[task_type],
                output_dimensionality=self._dims,
            ),
        )
        return [list(e.values) for e in resp.embeddings]

    def embed(self, texts: list[str], task_type: TaskType) -> list[list[float]]:
        batches = [
            texts[i : i + _BATCH_SIZE] for i in range(0, len(texts), _BATCH_SIZE)
        ]
        results = parallel_map(
            lambda b: self._embed_batch(b, task_type),
            batches,
            max_workers=settings.embedding_concurrency,
            log_every=20,
            desc="embed",
        )
        out: list[list[float]] = []
        for batch_vectors in results:
            out.extend(batch_vectors)
        return out
