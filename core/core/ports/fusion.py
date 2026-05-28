from abc import ABC, abstractmethod

from pydantic import BaseModel


class RankedList(BaseModel):
    """One signal's contribution to fusion: songs in descending preference.

    Colocated with FusionStrategy because it IS the contract — every adapter consumes
    a list of these. `scores` is optional: rank-based strategies (RRF) ignore it;
    score-based ones (WeightedSum) require it. `name` is the key the fusion's weight
    dict uses (e.g. "semantic", "filter", future "lexical").
    """

    name: str
    songs: list[str]
    scores: list[float] | None = None


class FusionStrategy(ABC):
    """Combines multiple ranked lists into one final ranking.

    Each input list (semantic / soft-filter / future lexical / future reranker) is a
    ranked sequence of song ids. Implementations may fuse by rank-only (RRF), by
    weighted score sum, by an external reranker, etc. — all swappable behind this port.
    The point of the abstraction is plug-and-play A/B during search tuning.
    """

    @abstractmethod
    def fuse(
        self,
        lists: list[RankedList],
        weights: dict[str, float],
    ) -> list[tuple[str, float]]:
        """Return `[(song_id, fused_score)]` sorted descending by fused_score."""
