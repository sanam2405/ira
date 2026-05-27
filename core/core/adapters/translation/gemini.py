"""Gemini TranslationProvider — translate + transliterate Bengali via a chat model.

A single model handles both; prompts pin it to "output only the result" so we can store
the response verbatim. Temperature 0 for stable, repeatable output.
"""

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from core.ports import TranslationProvider

_TRANSLATE_PROMPT = (
    "Translate the following Bengali text into natural English. "
    "Preserve line breaks. Output only the translation, with no preamble or notes.\n\n{text}"
)
_TRANSLITERATE_PROMPT = (
    "Transliterate the following Bengali text into Latin-script phonetic romanization "
    "(how it sounds, not its meaning). Preserve line breaks. Output only the "
    "transliteration, with no preamble or notes.\n\n{text}"
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
    def _generate(self, prompt: str) -> str:
        resp = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.0),
        )
        return (resp.text or "").strip()

    def translate(self, text: str) -> str:
        if not text.strip():
            return ""
        return self._generate(_TRANSLATE_PROMPT.format(text=text))

    def transliterate(self, text: str) -> str:
        if not text.strip():
            return ""
        return self._generate(_TRANSLITERATE_PROMPT.format(text=text))
