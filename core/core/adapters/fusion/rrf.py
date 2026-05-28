"""Reciprocal Rank Fusion — rank-based, scale-agnostic combination of ranked lists.

    score[song] = Σ_list  weight[list.name] · 1 / (k + rank_in_list)

Only ranks matter (raw scores are ignored), so signals with different score scales
(cosine similarities vs. filter-match fractions vs. future BM25 scores) combine cleanly.
`k = 60` is the canonical constant — it damps the long tail without overwhelming the
top of each list. Default fusion strategy.
"""

from core.ports.fusion import FusionStrategy, RankedList


class RRFFusion(FusionStrategy):
    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        lists: list[RankedList],
        weights: dict[str, float],
    ) -> list[tuple[str, float]]:
        scores: dict[str, float] = {}
        for ranked in lists:
            w = weights.get(ranked.name, 1.0)
            if w == 0:
                continue
            for rank, song_id in enumerate(ranked.songs, start=1):
                scores[song_id] = scores.get(song_id, 0.0) + w / (self.k + rank)
        return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
