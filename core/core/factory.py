"""Provider factories — one place that decides Gemini vs. fake.

Both pipeline (CLI) and api use these so they always pick the *same* embedder; a query
must be embedded by the same model that built the index, or similarity is meaningless.
Falls back to fake providers when no API key is set (offline/dev), or when forced.
"""

import structlog

from core.adapters.embedding import (
    FakeEmbeddingProvider,
    GeminiBatchEmbeddingProvider,
    GeminiEmbeddingProvider,
)
from core.adapters.translation import (
    FakeTranslationProvider,
    GeminiTranslationProvider,
)
from core.config import settings
from core.ports import EmbeddingProvider, TranslationProvider

logger = structlog.get_logger(__name__).bind(context="factory")


def build_embedding_provider(fake: bool = False) -> EmbeddingProvider:
    if fake or not settings.gemini_api_key:
        if not fake:
            logger.warning("no GEMINI_API_KEY — using fake embedding provider")
        return FakeEmbeddingProvider(settings.embedding_dimensions)
    cls = (
        GeminiBatchEmbeddingProvider
        if settings.use_batch_api
        else GeminiEmbeddingProvider
    )
    return cls(
        settings.gemini_api_key, settings.embedding_model, settings.embedding_dimensions
    )


def build_translation_provider(fake: bool = False) -> TranslationProvider:
    if fake or not settings.gemini_api_key:
        if not fake:
            logger.warning("no GEMINI_API_KEY — using fake translation provider")
        return FakeTranslationProvider()
    return GeminiTranslationProvider(
        settings.gemini_api_key, settings.translation_model
    )
