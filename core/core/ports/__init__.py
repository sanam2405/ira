"""Ports — the abstract interfaces every external dependency must implement.

Core and stage logic depends on these, never on a concrete adapter. Swapping a model,
provider, or store means writing a new adapter under `core.adapters`, not
editing anything here or in the stages.
"""

from core.ports.document_store import DocumentStore
from core.ports.embedding import EmbeddingProvider
from core.ports.search_backend import SearchBackend
from core.ports.translation import TranslationProvider

__all__ = [
    "DocumentStore",
    "EmbeddingProvider",
    "SearchBackend",
    "TranslationProvider",
]
