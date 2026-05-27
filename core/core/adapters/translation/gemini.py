"""Gemini TranslationProvider — translate + transliterate in one structured call.

One `generate_content` per text returns BOTH forms via a JSON response schema (half the
calls vs. doing them separately), and texts are rendered concurrently on a thread pool.
Temperature 0 for stable output; thinking disabled (`thinking_budget=0`) so we don't pay
for reasoning tokens on what is a straightforward translate/transliterate task. A Batch
API variant (50% cheaper) could follow the same pattern as the embedding batch provider.
"""

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from core.concurrency import parallel_map
from core.config import settings
from core.domain import Rendering
from core.ports import TranslationProvider

_PROMPT = (
    "You are translating Rabindra Sangeet (Bengali). For the text below, return JSON with:\n"
    "- translation: natural English meaning\n"
    "- transliteration: Latin-script phonetic romanization (how it sounds)\n"
    "Preserve line breaks within each value.\n\nText:\n{text}"
)


class GeminiTranslationProvider(TranslationProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiTranslationProvider")
        self._client = genai.Client(api_key=api_key)
        self._model = model

    @property
    def model_id(self) -> str:
        return self._model

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=30))
    def _render_one(self, text: str) -> Rendering:
        if not text.strip():
            return Rendering(translation="", transliteration="")
        resp = self._client.models.generate_content(
            model=self._model,
            contents=_PROMPT.format(text=text),
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=Rendering,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=settings.translation_thinking_budget
                ),
            ),
        )
        parsed = resp.parsed
        return (
            parsed
            if isinstance(parsed, Rendering)
            else Rendering(translation="", transliteration="")
        )

    def render(self, texts: list[str]) -> list[Rendering]:
        return parallel_map(
            self._render_one,
            texts,
            max_workers=settings.translation_concurrency,
            desc="render",
        )
