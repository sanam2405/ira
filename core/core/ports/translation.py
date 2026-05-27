from abc import ABC, abstractmethod

from core.domain import Rendering


class TranslationProvider(ABC):
    """Renders Bengali source text into English for non-native readers.

    `render` returns BOTH forms per text in one shot (see CLAUDE.md):
      - translation:     meaning in English ("enchanted forest")
      - transliteration: same sounds in Latin script ("mayabon")

    Batch-oriented (takes a list) so implementations can parallelize or use a batch job.
    Implementations: Gemini (concurrent / batch), Sarvam, IndicTrans2, ...
    """

    @property
    @abstractmethod
    def model_id(self) -> str: ...

    @abstractmethod
    def render(self, texts: list[str]) -> list[Rendering]:
        """Render each text to {translation, transliteration}, in input order."""
