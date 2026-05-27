"""SearchService — the hybrid-ranking brain.

Flow:
  1. embed the query (QUERY task type) with the same provider that built the index
  2. fetch top chunk-level hits from the SearchBackend (over-fetched, since one song
     contributes many multi-vectors)
  3. aggregate hits to song level: a song's semantic score = its best matching chunk
  4. apply *soft* metadata filters as a re-rank boost (never exclude):
        final = α·semantic + β·(fraction of filters that match the song's metadata)
  5. hydrate to SearchResult (titles in bn/en/translit + matched fields), sort, truncate

Depends only on ports — works against the local numpy index today, Typesense tomorrow.
"""

import structlog

from core.config import settings
from core.domain import Song, SongTranslation, TaskType
from core.ports import DocumentStore, EmbeddingProvider, SearchBackend
from core.search.models import MatchedField, SearchResult, SongView

logger = structlog.get_logger(__name__).bind(class_name="SearchService")


class SearchService:
    def __init__(
        self,
        store: DocumentStore,
        backend: SearchBackend,
        embedder: EmbeddingProvider,
    ):
        self.store = store
        self.backend = backend
        self.embedder = embedder

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, str] | None = None,
    ) -> list[SearchResult]:
        query = query.strip()
        if not query:
            return []
        filters = filters or {}

        qvec = self.embedder.embed([query], TaskType.QUERY)[0]
        hits = self.backend.search(qvec, top_k=top_k * settings.search_overfetch)

        # aggregate chunk hits -> song level (best score + the fields/langs that matched)
        semantic: dict[str, float] = {}
        matched: dict[str, list[MatchedField]] = {}
        for hit in hits:
            mf = MatchedField(field=hit.field, lang=hit.lang)
            if hit.song_id not in semantic:
                semantic[hit.song_id] = hit.score
                matched[hit.song_id] = [mf]
            else:
                semantic[hit.song_id] = max(semantic[hit.song_id], hit.score)
                if mf not in matched[hit.song_id]:
                    matched[hit.song_id].append(mf)

        results: list[SearchResult] = []
        for song_id, sem in semantic.items():
            song = self.store.load("songs", song_id, Song)
            if song is None:
                continue
            fused = settings.search_alpha * sem + settings.search_beta * _filter_match(
                song, filters
            )
            translation = self.store.load("translations", song_id, SongTranslation)
            results.append(
                SearchResult(
                    song_id=song_id,
                    score=fused,
                    title=song.title,
                    title_en=translation.title_en if translation else None,
                    title_translit=translation.title_translit if translation else None,
                    raag=song.metadata.get("raag"),
                    taal=song.metadata.get("taal"),
                    matched=matched[song_id],
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def get_song(self, song_id: str) -> SongView | None:
        song = self.store.load("songs", song_id, Song)
        if song is None:
            return None
        translation = self.store.load("translations", song_id, SongTranslation)
        return SongView.from_records(song, translation)


def _filter_match(song: Song, filters: dict[str, str]) -> float:
    """Fraction of filter terms found (case-insensitive substring) in song metadata."""
    if not filters:
        return 0.0
    hits = 0
    for key, value in filters.items():
        if value.lower() in str(song.metadata.get(key, "")).lower():
            hits += 1
    return hits / len(filters)
