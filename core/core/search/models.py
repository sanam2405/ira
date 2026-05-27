"""Search-facing view models — what the API returns. Composed from Song + translation."""

from pydantic import BaseModel

from core.domain import Field, Lang, Song, SongTranslation


class MatchedField(BaseModel):
    """Which (field, language) of a song matched the query."""

    field: Field
    lang: Lang


class SearchResult(BaseModel):
    """One song in a ranked result list (lightweight — no full lyrics)."""

    song_id: str
    score: float
    title: str  # Bengali
    title_en: str | None = None
    title_translit: str | None = None
    raag: str | None = None
    taal: str | None = None
    matched: list[MatchedField] = []


class SongView(BaseModel):
    """Full song detail — original Bengali + English translation + transliteration."""

    song_id: str
    domain: str
    url: str
    title: str
    title_en: str | None = None
    title_translit: str | None = None
    lyrics: str
    lyrics_en: str | None = None
    lyrics_translit: str | None = None
    context: str | None = None
    context_en: str | None = None
    context_translit: str | None = None
    metadata: dict = {}
    citations: list[str] = []

    @classmethod
    def from_records(
        cls, song: Song, translation: SongTranslation | None
    ) -> "SongView":
        t = translation
        return cls(
            song_id=song.id,
            domain=song.domain,
            url=song.url,
            title=song.title,
            title_en=t.title_en if t else None,
            title_translit=t.title_translit if t else None,
            lyrics=song.lyrics,
            lyrics_en=t.lyrics_en if t else None,
            lyrics_translit=t.lyrics_translit if t else None,
            context=song.metadata.get("context"),
            context_en=t.context_en if t else None,
            context_translit=t.context_translit if t else None,
            metadata=song.metadata,
            citations=song.citations,
        )
