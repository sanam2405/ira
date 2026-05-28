"""Gemini TranslationProvider — translate + transliterate in one structured call.

One `generate_content` per text returns BOTH forms via a JSON response schema (half the
calls vs. doing them separately), and texts are rendered concurrently on a thread pool.
Temperature 0 for stable output; thinking disabled (`thinking_budget=0`) so we don't pay
for reasoning tokens on what is a straightforward translate/transliterate task.

The standing instruction (domain context, snippet types, transliteration scheme,
examples) lives in `templates/translate.md` and is loaded via the shared
`core.templates.get_jinja_template` util, then passed as `system_instruction`. This
keeps prompt content out of code AND lets Gemini's implicit prefix cache deduplicate the
shared instruction across all calls, so a longer/better prompt doesn't multiply cost.

A Batch API variant (50% cheaper) could follow the same pattern as the embedding batch
provider.
"""

from functools import cache

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from core.concurrency import parallel_map
from core.config import settings
from core.domain import Rendering, TextSnippet
from core.ports import TranslationProvider
from core.templates import get_jinja_template


@cache
def _system_instruction() -> str:
    """Loaded + rendered once per process; identical across all render() calls."""
    return get_jinja_template("templates/translate.md").render()


def _tag(item: TextSnippet) -> str:
    """Per-call user content: tag the snippet kind so the model treats it appropriately.

    The system_instruction explains each tag; only the tag + text vary across calls so
    Gemini's implicit prefix cache keeps doing its job.
    """
    return f"[{item.kind.value.upper()}]\n{item.text}"


class GeminiTranslationProvider(TranslationProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiTranslationProvider")
        self._client = genai.Client(api_key=api_key)
        self._model = model

    @property
    def model_id(self) -> str:
        return self._model

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential_jitter(initial=1, max=30, jitter=2),
    )
    def _render_one(self, item: TextSnippet) -> Rendering:
        if not item.text.strip():
            return Rendering(translation="", transliteration="")
        resp = self._client.models.generate_content(
            model=self._model,
            contents=_tag(item),
            config=types.GenerateContentConfig(
                system_instruction=_system_instruction(),
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

    def render(self, items: list[TextSnippet]) -> list[Rendering]:
        return parallel_map(
            self._render_one,
            items,
            max_workers=settings.translation_concurrency,
            desc="render",
        )
