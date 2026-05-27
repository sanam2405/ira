from abc import ABC, abstractmethod


class TranslationProvider(ABC):
    """Renders Bengali source text into English for non-native readers.

    Two distinct outputs (see CLAUDE.md):
      - translate:     meaning in English ("enchanted forest")
      - transliterate: same sounds in Latin script ("mayabon")

    Implementations: Gemini, Sarvam, IndicTrans2, ...
    """

    @property
    @abstractmethod
    def model_id(self) -> str: ...

    @abstractmethod
    def translate(self, text: str) -> str:
        """Bengali -> English meaning."""

    @abstractmethod
    def transliterate(self, text: str) -> str:
        """Bengali -> Latin-script phonetic rendering."""
