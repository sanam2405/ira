"""No-op translation for offline runs/tests. Tags text so the flow is observable."""

from core.ports import TranslationProvider


class FakeTranslationProvider(TranslationProvider):
    @property
    def model_id(self) -> str:
        return "fake-translation"

    def translate(self, text: str) -> str:
        return f"[en] {text}"

    def transliterate(self, text: str) -> str:
        return f"[translit] {text}"
