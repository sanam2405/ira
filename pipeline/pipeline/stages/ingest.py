"""ingest: scraped JSONL -> typed Song records in the DocumentStore."""

import json
from pathlib import Path

import structlog
from core.domain import Song
from core.ports import DocumentStore

logger = structlog.get_logger(__name__).bind(stage="ingest")


def run_ingest(store: DocumentStore, source_jsonl: Path) -> int:
    """Load every song from the JSONL into the `songs` collection. Returns count."""
    count = 0
    with open(source_jsonl, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            song = Song.from_scraped(json.loads(line))
            store.save("songs", song.id, song)
            count += 1
    logger.info("ingested", songs=count, source=str(source_jsonl))
    return count
