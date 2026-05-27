from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class DocumentStore(ABC):
    """Persists typed records, organized into named collections and keyed by id.

    Generic over pydantic models so every stage shares one storage contract:
    songs, translations, and embeddings are just different collections. Used for
    idempotency too — a stage can `exists()`-check before recomputing.

    Implementations: local files, Postgres, object storage, ...
    """

    @abstractmethod
    def save(self, collection: str, id: str, obj: BaseModel) -> None: ...

    @abstractmethod
    def load(self, collection: str, id: str, model: type[T]) -> T | None: ...

    @abstractmethod
    def exists(self, collection: str, id: str) -> bool: ...

    @abstractmethod
    def iter(self, collection: str, model: type[T]) -> Iterator[T]:
        """Iterate every record in a collection, parsed as `model`."""
