"""Local filesystem DocumentStore: one JSON file per record.

Layout: `{data_dir}/{collection}/{safe_id}.json`. Zero infra, trivially inspectable —
the right default at 2.3k songs. Swap for Postgres/object-storage behind the same port
when scale demands.
"""

import re
from collections.abc import Iterator
from pathlib import Path

import structlog
from pydantic import BaseModel

from core.ports.document_store import DocumentStore, T

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]")


class LocalDocumentStore(DocumentStore):
    def __init__(self, data_dir: Path):
        self.root = Path(data_dir)
        self.logger = structlog.get_logger(__name__).bind(
            class_name="LocalDocumentStore"
        )

    def _path(self, collection: str, id: str) -> Path:
        safe = _UNSAFE.sub("_", id)
        return self.root / collection / f"{safe}.json"

    def save(self, collection: str, id: str, obj: BaseModel) -> None:
        path = self._path(collection, id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(obj.model_dump_json(indent=2), encoding="utf-8")

    def load(self, collection: str, id: str, model: type[T]) -> T | None:
        path = self._path(collection, id)
        if not path.exists():
            return None
        return model.model_validate_json(path.read_text(encoding="utf-8"))

    def exists(self, collection: str, id: str) -> bool:
        return self._path(collection, id).exists()

    def iter(self, collection: str, model: type[T]) -> Iterator[T]:
        directory = self.root / collection
        if not directory.exists():
            return
        for path in sorted(directory.glob("*.json")):
            yield model.model_validate_json(path.read_text(encoding="utf-8"))
