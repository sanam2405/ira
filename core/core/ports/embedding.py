from abc import ABC, abstractmethod

from core.domain import TaskType


class EmbeddingProvider(ABC):
    """Maps text to dense vectors. Implementations: Gemini, BGE-m3, OpenAI, ..."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Identifies the model + space these vectors live in (for provenance)."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Output vector dimensionality."""

    @abstractmethod
    def embed(self, texts: list[str], task_type: TaskType) -> list[list[float]]:
        """Embed a batch of texts. Returns one vector per input, in order.

        Implementations handle provider batch limits internally; callers may pass a
        large list.
        """
