"""Pipeline CLI — the composition root that wires adapters to stages.

This is the *only* place that chooses concrete adapters; everything else depends on
ports. Run from anywhere in the workspace:

    uv run python -m pipeline.cli ingest
    uv run python -m pipeline.cli all                 # ingest -> translate -> embed -> index
    uv run python -m pipeline.cli all --fake          # no API key needed (plumbing test)
    uv run python -m pipeline.cli search "monsoon longing"

Uses Gemini when GEMINI_API_KEY is set, else falls back to the fake providers.
"""

import argparse

from core.adapters.document_store import LocalDocumentStore
from core.adapters.search_backend import LocalSearchBackend
from core.config import settings
from core.factory import build_embedding_provider, build_translation_provider
from core.search import SearchService

from pipeline.stages import run_embed, run_index, run_ingest, run_translate


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

    match args.command:
        case "ingest":
            run_ingest(store, settings.source_jsonl)
        case "translate":
            run_translate(store, build_translation_provider(args.fake))
        case "embed":
            run_embed(store, build_embedding_provider(args.fake))
        case "index":
            run_index(store, backend)
        case "all":
            run_ingest(store, settings.source_jsonl)
            run_translate(store, build_translation_provider(args.fake))
            run_embed(store, build_embedding_provider(args.fake))
            run_index(store, backend)
        case "search":
            _search(store, backend, args.query, args.top_k, args.fake)


def _search(
    store: LocalDocumentStore,
    backend: LocalSearchBackend,
    query: str | None,
    top_k: int,
    fake: bool,
) -> None:
    if not query:
        raise SystemExit("search requires a query argument")
    backend.load()
    service = SearchService(store, backend, build_embedding_provider(fake))
    for result in service.search(query, top_k=top_k):
        matched = ", ".join(f"{m.field}/{m.lang}" for m in result.matched[:3])
        print(f"{result.score:.3f}  {result.title}  ({matched})")


if __name__ == "__main__":
    main()
