"""Core domain models — the vocabulary every port and stage speaks.

These are vendor-neutral: nothing here knows about Gemini, numpy, or Typesense.
"""

from __future__ import annotations

import uuid
from enum import StrEnum

from pydantic import BaseModel
from pydantic import Field as PydField

# Stable namespace so a song's id is a deterministic function of its source url.
# Re-running ingest never changes ids -> stages stay idempotent.
_IRA_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "ira.gitabitan")


def song_id_for(url: str) -> str:
    return str(uuid.uuid5(_IRA_NAMESPACE, url))


class Lang(StrEnum):
    BN = "bn"  # original Bengali (authoritative)
    EN = "en"  # English translation


class Field(StrEnum):
    """Which part of a song an embedding/translation belongs to."""

    TITLE = "title"
    LYRICS = "lyrics"
    CONTEXT = "context"
    CITATION = "citation"


class TaskType(StrEnum):
    """Embedding intent. Adapters map these to provider-specific task types."""

    DOCUMENT = "document"  # indexing corpus text
    QUERY = "query"  # a user search query


class Song(BaseModel):
    """A song as scraped — original Bengali plus structured metadata."""

    id: str
    domain: str = "gitabitan"
    title: str
    url: str
    lyrics: str
    metadata: dict = PydField(default_factory=dict)
    citations: list[str] = PydField(default_factory=list)

    @classmethod
    def from_scraped(cls, raw: dict) -> "Song":
        return cls(
            id=song_id_for(raw["url"]),
            domain=raw.get("domain", "gitabitan"),
            title=raw["title"],
            url=raw["url"],
            lyrics=raw.get("lyrics", ""),
            metadata=raw.get("metadata", {}) or {},
            citations=raw.get("citations", []) or [],
        )


class Rendering(BaseModel):
    """English rendering of one Bengali text — both forms from a single model call."""

    translation: str  # meaning in English
    transliteration: str  # Latin-script phonetic


class TextSnippet(BaseModel):
    """A text to render plus its `kind` (which part of a song it is).

    The kind reuses `Field` so callers don't invent a parallel enum; in translation
    contexts only TITLE/LYRICS/CONTEXT are meaningful (citations are not translated).
    The kind is sent to the model as a per-call hint so it treats e.g. a lyric line
    differently from scholarly prose.
    """

    text: str
    kind: Field


class SongTranslation(BaseModel):
    """English translation + transliteration of a song's free-text fields.

    Stored per song, keyed by the same id. Fields are optional so the translate stage
    can fill them incrementally.
    """

    song_id: str
    title_en: str | None = None
    title_translit: str | None = None
    lyrics_en: str | None = None
    lyrics_translit: str | None = None
    context_en: str | None = None
    context_translit: str | None = None


class Embedding(BaseModel):
    """One embeddable unit: a (song, field, language, chunk) slice of text and its vector.

    `vector` is None until the embed stage fills it.
    """

    id: str
    song_id: str
    field: Field
    lang: Lang
    chunk_index: int = 0
    text: str
    vector: list[float] | None = None

    @staticmethod
    def make_id(song_id: str, field: Field, lang: Lang, chunk_index: int) -> str:
        return f"{song_id}:{field}:{lang}:{chunk_index}"


class SongEmbeddings(BaseModel):
    """All embeddings for one song, grouped for one-file idempotency.

    `model_id` records which model produced them — the marker that tells a future GA
    re-embed which records are stale.
    """

    song_id: str
    model_id: str
    items: list[Embedding]


class Hit(BaseModel):
    """A single search match, before aggregation to song level."""

    song_id: str
    score: float
    field: Field
    lang: Lang
    chunk_index: int = 0
