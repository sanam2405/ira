"""SearchService — the hybrid-ranking brain.

Flow:
  1. embed the query (QUERY task type) with the same provider that built the index
  2. fetch top chunk-level hits from the SearchBackend (over-fetched, since one song
     contributes many multi-vectors)
  3. aggregate hits to song level: a song's semantic rank = its best matching chunk
  4. build the soft-metadata filter ranking — songs scoring 0 are *absent* (soft, never
     excluded; non-matchers just contribute nothing to the fused total)
  5. fuse via the injected FusionStrategy (default RRF) with config-driven weights
  6. hydrate top_k to SearchResult (titles in bn/en/translit + matched fields)

Depends only on ports — the search backend, embedder, document store, AND the fusion
strategy are all swappable.
"""

from collections.abc import Iterable

import structlog

from core.config import settings
from core.domain import Hit, Song, SongTranslation, TaskType
from core.ports import (
    DocumentStore,
    EmbeddingProvider,
    FusionStrategy,
    RankedList,
    SearchBackend,
)
from core.search.models import MatchedField, SearchResult, SongView

logger = structlog.get_logger(__name__).bind(class_name="SearchService")


# `state[song_id] = {"score": best_chunk_score, "matched": [MatchedField, ...]}`
_SemanticState = dict[str, dict]


class SearchService:
    def __init__(
        self,
        store: DocumentStore,
        backend: SearchBackend,
        embedder: EmbeddingProvider,
        fusion: FusionStrategy,
    ):
        self.store = store
        self.backend = backend
        self.embedder = embedder
        self.fusion = fusion

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, str] | None = None,
        fusion: FusionStrategy | None = None,
    ) -> list[SearchResult]:
        """Hybrid search. `fusion` overrides the default strategy for this call only
        (handy for A/B testing during tuning)."""
        query = query.strip()
        if not query:
            return []
        filters = filters or {}
        strategy = fusion or self.fusion

        qvec = self.embedder.embed([query], TaskType.QUERY)[0]
        chunk_hits = self.backend.search(qvec, top_k=top_k * settings.search_overfetch)

        semantic_rl, semantic_state = self._semantic_ranked_list(chunk_hits)
        filter_rl = self._filter_ranked_list(filters, semantic_rl.songs)

        fused = strategy.fuse(
            [semantic_rl, filter_rl],
            weights={
                "semantic": settings.fusion_w_semantic,
                "filter": settings.fusion_w_filter,
            },
        )

        results: list[SearchResult] = []
        for song_id, score in fused[:top_k]:
            result = self._hydrate(song_id, score, semantic_state)
            if result is not None:
                results.append(result)
        return results

    def get_song(self, song_id: str) -> SongView | None:
        song = self.store.load("songs", song_id, Song)
        if song is None:
            return None
        translation = self.store.load("translations", song_id, SongTranslation)
        return SongView.from_records(song, translation)

    # --- internal helpers (split out so each signal is independently testable) ---

    @staticmethod
    def _semantic_ranked_list(
        chunk_hits: Iterable[Hit],
    ) -> tuple[RankedList, _SemanticState]:
        """Aggregate chunk-level hits to song level: best chunk wins, collect matched
        (field, lang) pairs for hydration."""
        state: _SemanticState = {}
        for hit in chunk_hits:
            mf = MatchedField(field=hit.field, lang=hit.lang)
            if hit.song_id not in state:
                state[hit.song_id] = {"score": hit.score, "matched": [mf]}
            else:
                entry = state[hit.song_id]
                entry["score"] = max(entry["score"], hit.score)
                if mf not in entry["matched"]:
                    entry["matched"].append(mf)
        ordered = sorted(state.items(), key=lambda kv: kv[1]["score"], reverse=True)
        return (
            RankedList(
                name="semantic",
                songs=[sid for sid, _ in ordered],
                scores=[entry["score"] for _, entry in ordered],
            ),
            state,
        )

    def _filter_ranked_list(
        self, filters: dict[str, str], candidates: list[str]
    ) -> RankedList:
        """Rank candidate songs by fraction of filter terms matched.

        Songs scoring 0 (no terms matched) are **absent** from the list — they
        contribute 0 via RRF and thus aren't boosted, but they aren't excluded either
        (semantic ranking already placed them as candidates). This is the soft-filter
        semantics we want."""
        if not filters:
            return RankedList(name="filter", songs=[], scores=[])
        ranked: list[tuple[str, float]] = []
        for song_id in candidates:
            song = self.store.load("songs", song_id, Song)
            if song is None:
                continue
            matched = sum(
                1
                for key, value in filters.items()
                if value.lower() in str(song.metadata.get(key, "")).lower()
            )
            if matched > 0:
                ranked.append((song_id, matched / len(filters)))
        ranked.sort(key=lambda kv: kv[1], reverse=True)
        return RankedList(
            name="filter",
            songs=[sid for sid, _ in ranked],
            scores=[score for _, score in ranked],
        )

    def _hydrate(
        self, song_id: str, score: float, state: _SemanticState
    ) -> SearchResult | None:
        song = self.store.load("songs", song_id, Song)
        if song is None:
            return None
        translation = self.store.load("translations", song_id, SongTranslation)
        return SearchResult(
            song_id=song_id,
            score=score,
            title=song.title,
            title_en=translation.title_en if translation else None,
            title_translit=translation.title_translit if translation else None,
            raag=song.metadata.get("raag"),
            taal=song.metadata.get("taal"),
            matched=state.get(song_id, {}).get("matched", []),
        )
