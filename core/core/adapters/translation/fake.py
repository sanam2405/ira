"""No-op translation for offline runs/tests. Tags text so the flow is observable."""

from core.domain import Rendering, TextSnippet
from core.ports import TranslationProvider


class FakeTranslationProvider(TranslationProvider):
    @property
    def model_id(self) -> str:
        return "fake-translation"

    def render(self, items: list[TextSnippet]) -> list[Rendering]:
        return [
            Rendering(
                translation=f"[en|{item.kind.value}] {item.text}",
                transliteration=f"[translit|{item.kind.value}] {item.text}",
            )
            if item.text.strip()
            else Rendering(translation="", transliteration="")
            for item in items
        ]
