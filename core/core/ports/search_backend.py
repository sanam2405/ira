from abc import ABC, abstractmethod
from collections.abc import Iterable

from core.domain import Embedding, Field, Hit, Lang


class SearchBackend(ABC):
    """Stores embeddings and retrieves nearest neighbours for a query vector.

    Pure vector retrieval only — soft metadata filtering / score fusion lives in the
    higher-level SearchService (api), which has access to song metadata. This keeps the
    backend swappable: local numpy, Typesense, Turbopuffer, ...
    """

    @abstractmethod
    def index(self, embeddings: Iterable[Embedding]) -> None:
        """Add/replace embeddings in the index (must have non-None vectors)."""

    @abstractmethod
    def search(
        self,
        vector: list[float],
        top_k: int = 20,
        fields: Iterable[Field] | None = None,
        langs: Iterable[Lang] | None = None,
    ) -> list[Hit]:
        """Return the top_k nearest embeddings as Hits, optionally restricted to
        certain fields/languages."""
