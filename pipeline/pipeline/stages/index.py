"""index: load all stored embeddings into the SearchBackend and persist it."""

import structlog
from core.adapters.search_backend import LocalSearchBackend
from core.domain import SongEmbeddings
from core.ports import DocumentStore, SearchBackend

logger = structlog.get_logger(__name__).bind(stage="index")


def run_index(store: DocumentStore, backend: SearchBackend) -> int:
    count = 0

    def all_embeddings():
        nonlocal count
        for song_emb in store.iter("embeddings", SongEmbeddings):
            for item in song_emb.items:
                count += 1
                yield item

    backend.index(all_embeddings())
    # Local backend persists to disk so the api can load it; other backends self-persist.
    if isinstance(backend, LocalSearchBackend):
        backend.save()
    logger.info("indexed", vectors=count)
    return count
