from abc import ABC, abstractmethod

from core.domain import Rendering, TextSnippet


class TranslationProvider(ABC):
    """Renders Bengali source text into English for non-native readers.

    `render` returns BOTH forms per snippet in one shot (see CLAUDE.md):
      - translation:     meaning in English ("enchanted forest")
      - transliteration: same sounds in Latin script ("mayabon")

    Each input carries a `kind` (title / lyrics / context) so implementations can hint
    the model — a lyric line wants poetic rendering, scholarly context wants faithful
    prose. Batch-oriented (takes a list) so implementations can parallelize or use a
    batch job. Implementations: Gemini (concurrent / batch), Sarvam, IndicTrans2, ...
    """

    @property
    @abstractmethod
    def model_id(self) -> str: ...

    @abstractmethod
    def render(self, items: list[TextSnippet]) -> list[Rendering]:
        """Render each snippet to {translation, transliteration}, in input order."""
