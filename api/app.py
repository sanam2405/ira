"""ira search API — a thin FastAPI shell over core's SearchService.

Composition root for the read side: builds the document store, loads the persisted
index, and picks the query embedder (must match the one that built the index — handled
by core.factory). All ranking logic lives in core; this module only does HTTP.

Run:  uv run fastapi dev app.py   (from api/)
"""

from contextlib import asynccontextmanager
from typing import Literal

import structlog
from core.adapters.document_store import LocalDocumentStore
from core.adapters.search_backend import LocalSearchBackend
from core.config import settings
from core.factory import build_embedding_provider, build_fusion_strategy
from core.search import SearchResult, SearchService, SongView
from fastapi import FastAPI, HTTPException, Query

logger = structlog.get_logger(__name__).bind(context="api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the SearchService once at startup; load the index into memory."""
    store = LocalDocumentStore(settings.data_dir)
    backend = LocalSearchBackend(settings.data_dir / "index")
    try:
        backend.load()
        app.state.search = SearchService(
            store, backend, build_embedding_provider(), build_fusion_strategy()
        )
        logger.info("search ready", model=app.state.search.embedder.model_id)
    except FileNotFoundError:
        app.state.search = None
        logger.warning(
            "no index found — run `pipeline.cli all` first; /search disabled"
        )
    yield


app = FastAPI(title="ira", lifespan=lifespan)


def _service(app: FastAPI) -> SearchService:
    if app.state.search is None:
        raise HTTPException(status_code=503, detail="search index not built yet")
    return app.state.search


@app.get("/health", description="Check the health of the API service")
def health() -> Literal["IRA"]:
    return "IRA"


@app.get("/search", description="Hybrid semantic search over the songs")
def search(
    q: str = Query(..., min_length=1, description="search query (English or Bengali)"),
    top_k: int = Query(10, ge=1, le=50),
    fusion: Literal["rrf", "weighted_sum"] | None = Query(
        None, description="override the fusion strategy for this call only"
    ),
) -> list[SearchResult]:
    override = build_fusion_strategy(fusion) if fusion else None
    return _service(app).search(q, top_k=top_k, fusion=override)


@app.get("/songs/{song_id}", description="Full song detail (Bengali + en + translit)")
def get_song(song_id: str) -> SongView:
    song = _service(app).get_song(song_id)
    if song is None:
        raise HTTPException(status_code=404, detail="song not found")
    return song
