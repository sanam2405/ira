"""Weighted-sum fusion — preserves the legacy α/β formula behind the same port.

    score[song] = Σ_list  weight[list.name] · raw_score_in_list

Sensitive to score-scale differences between signals, but useful as:
  - a deliberate fallback when RRF behaves worse on some queries (flip
    `FUSION_STRATEGY=weighted_sum` in env, no rebuild)
  - a validation that the FusionStrategy port abstraction is real (two adapters from day one)

Requires `scores` populated on each RankedList — RRF doesn't, so this adapter is
strictly less flexible. Use RRF unless you have a reason.
"""

from core.ports.fusion import FusionStrategy, RankedList


class WeightedSumFusion(FusionStrategy):
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
            if ranked.scores is None:
                raise ValueError(
                    f"WeightedSumFusion needs `scores` on RankedList '{ranked.name}'"
                )
            for song_id, score in zip(ranked.songs, ranked.scores, strict=True):
                scores[song_id] = scores.get(song_id, 0.0) + w * score
        return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
