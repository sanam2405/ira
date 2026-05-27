"""Pipeline CLI — the composition root that wires adapters to stages.

This is the *only* place that chooses concrete adapters; everything else depends on
ports. Run from `pipeline/`:

    uv run python -m pipeline.cli ingest
    uv run python -m pipeline.cli all                 # ingest -> translate -> embed -> index
    uv run python -m pipeline.cli all --fake          # no API key needed (plumbing test)
    uv run python -m pipeline.cli search "monsoon longing"

Uses Gemini when GEMINI_API_KEY is set, else falls back to the fake providers.
"""

import argparse

import structlog
from core.adapters.document_store import LocalDocumentStore
from core.adapters.embedding import (
    FakeEmbeddingProvider,
    GeminiEmbeddingProvider,
)
from core.adapters.search_backend import LocalSearchBackend
from core.adapters.translation import (
    FakeTranslationProvider,
    GeminiTranslationProvider,
)
from core.config import settings
from core.domain import Song, TaskType
from core.ports import EmbeddingProvider, TranslationProvider

from pipeline.stages import run_embed, run_index, run_ingest, run_translate

logger = structlog.get_logger(__name__).bind(context="cli")


def _providers(fake: bool) -> tuple[TranslationProvider, EmbeddingProvider]:
    if fake or not settings.gemini_api_key:
        if not fake:
            logger.warning("no GEMINI_API_KEY set — using fake providers")
        return FakeTranslationProvider(), FakeEmbeddingProvider(
            settings.embedding_dimensions
        )
    return (
        GeminiTranslationProvider(settings.gemini_api_key, settings.translation_model),
        GeminiEmbeddingProvider(
            settings.gemini_api_key,
            settings.embedding_model,
            settings.embedding_dimensions,
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="ira-pipeline")
    parser.add_argument(
        "command",
        choices=["ingest", "translate", "embed", "index", "all", "search"],
    )
    parser.add_argument("query", nargs="?", help="search query (for `search`)")
    parser.add_argument(
        "--fake", action="store_true", help="use offline fake providers"
    )
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    store = LocalDocumentStore(settings.data_dir)
    backend = LocalSearchBackend(settings.data_dir / "index")
    translator, embedder = _providers(args.fake)

    match args.command:
        case "ingest":
            run_ingest(store, settings.source_jsonl)
        case "translate":
            run_translate(store, translator)
        case "embed":
            run_embed(store, embedder)
        case "index":
            run_index(store, backend)
        case "all":
            run_ingest(store, settings.source_jsonl)
            run_translate(store, translator)
            run_embed(store, embedder)
            run_index(store, backend)
        case "search":
            _search(store, backend, embedder, args.query, args.top_k)


def _search(
    store: LocalDocumentStore,
    backend: LocalSearchBackend,
    embedder: EmbeddingProvider,
    query: str | None,
    top_k: int,
) -> None:
    if not query:
        raise SystemExit("search requires a query argument")
    backend.load()
    [qvec] = embedder.embed([query], TaskType.QUERY)
    hits = backend.search(qvec, top_k=top_k)
    seen: set[str] = set()
    for hit in hits:
        if hit.song_id in seen:
            continue
        seen.add(hit.song_id)
        song = store.load("songs", hit.song_id, Song)
        title = song.title if song else "?"
        print(f"{hit.score:.3f}  [{hit.field}/{hit.lang}]  {title}")


if __name__ == "__main__":
    main()
