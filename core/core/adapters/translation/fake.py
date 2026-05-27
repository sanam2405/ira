"""No-op translation for offline runs/tests. Tags text so the flow is observable."""

from core.domain import Rendering
from core.ports import TranslationProvider


class FakeTranslationProvider(TranslationProvider):
    @property
    def model_id(self) -> str:
        return "fake-translation"

    def render(self, texts: list[str]) -> list[Rendering]:
        return [
            Rendering(translation=f"[en] {t}", transliteration=f"[translit] {t}")
            if t.strip()
            else Rendering(translation="", transliteration="")
            for t in texts
        ]
