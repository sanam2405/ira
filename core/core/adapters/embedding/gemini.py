"""Gemini EmbeddingProvider — gemini-embedding-001 by default (see config).

Truncates to `dimensions` via Matryoshka. Batches requests and retries transient
errors. Output is L2-normalized downstream by the SearchBackend (001 does not normalize
truncated vectors itself).
"""

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

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
        out: list[list[float]] = []
        for start in range(0, len(texts), _BATCH_SIZE):
            out.extend(self._embed_batch(texts[start : start + _BATCH_SIZE], task_type))
        return out
