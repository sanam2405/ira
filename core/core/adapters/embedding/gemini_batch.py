"""Gemini Batch-API EmbeddingProvider — 50% cheaper, async, high throughput.

Implements the same `EmbeddingProvider.embed` contract but routes through the Batch API:
write a JSONL of requests → upload → `batches.create_embeddings` → poll until the job
succeeds → download + reorder results. `embed()` blocks until the job finishes (minutes
to hours), which is fine for the offline embed stage.

NOTE: the exact batch request/response JSON shape is per Google's docs (May 2026) and
has not yet been validated against a live key — verify field names on first real run.
Selected via `use_batch_api=true`; the default path is the concurrent provider.
"""

import json
import tempfile
import time
from pathlib import Path

import structlog
from google import genai

from core.chunking import truncate_to_tokens
from core.config import settings
from core.domain import TaskType
from core.ports import EmbeddingProvider

_TASK_TYPE = {
    TaskType.DOCUMENT: "RETRIEVAL_DOCUMENT",
    TaskType.QUERY: "RETRIEVAL_QUERY",
}
_TERMINAL_OK = "JOB_STATE_SUCCEEDED"
_TERMINAL_BAD = {"JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}


class GeminiBatchEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str, dimensions: int):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._dims = dimensions
        self.logger = structlog.get_logger(__name__).bind(
            class_name="GeminiBatchEmbeddingProvider"
        )

    @property
    def model_id(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dims

    def embed(self, texts: list[str], task_type: TaskType) -> list[list[float]]:
        if not texts:
            return []
        src = self._upload_requests(texts, task_type)
        job = self._client.batches.create_embeddings(model=self._model, src=src)
        job = self._await(job)
        return self._collect(job, len(texts))

    def _upload_requests(self, texts: list[str], task_type: TaskType):
        lines = [
            json.dumps(
                {
                    "key": str(i),
                    "request": {
                        "content": {
                            "parts": [
                                {
                                    "text": truncate_to_tokens(
                                        text, settings.embedding_safe_tokens
                                    )
                                }
                            ]
                        },
                        "output_dimensionality": self._dims,
                        "task_type": _TASK_TYPE[task_type],
                    },
                }
            )
            for i, text in enumerate(texts)
        ]
        with tempfile.NamedTemporaryFile(
            "w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write("\n".join(lines))
            path = Path(f.name)
        uploaded = self._client.files.upload(
            file=path, config={"mime_type": "application/jsonl"}
        )
        path.unlink(missing_ok=True)
        return uploaded.name

    def _await(self, job):
        while job.state.name not in _TERMINAL_BAD and job.state.name != _TERMINAL_OK:
            self.logger.info("batch job", state=job.state.name)
            time.sleep(settings.batch_poll_seconds)
            job = self._client.batches.get(name=job.name)
        if job.state.name in _TERMINAL_BAD:
            raise RuntimeError(f"batch embedding job {job.state.name}")
        return job

    def _collect(self, job, n: int) -> list[list[float]]:
        raw = self._client.files.download(file=job.dest.file_name).decode("utf-8")
        vectors: list[list[float]] = [[]] * n
        for line in raw.splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            idx = int(record["key"])
            vectors[idx] = list(record["response"]["embedding"]["values"])
        return vectors
