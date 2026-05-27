"""translate: fill English translation + transliteration for each song's free text.

Covers title, lyrics, and context (the human-readable fields a non-Bengali reader
needs). Citations are left in source form — they are large and frequently already carry
English. Resumable: songs that already have a translation record are skipped.

All pending texts are collected into one `render` call so the provider can parallelize
(or run a single batch job) across the whole corpus rather than song-by-song.
"""

import structlog
from core.domain import Rendering, Song, SongTranslation
from core.ports import DocumentStore, TranslationProvider

logger = structlog.get_logger(__name__).bind(stage="translate")


def run_translate(
    store: DocumentStore, translator: TranslationProvider, overwrite: bool = False
) -> int:
    pending = [
        song
        for song in store.iter("songs", Song)
        if overwrite or not store.exists("translations", song.id)
    ]
    if not pending:
        logger.info("translated", songs=0, note="nothing pending")
        return 0

    # Flatten to (song_id, field, text) so one render pass covers everything.
    entries: list[tuple[str, str, str]] = []
    for song in pending:
        entries.append((song.id, "title", song.title))
        entries.append((song.id, "lyrics", song.lyrics))
        context = song.metadata.get("context", "") or ""
        if context:
            entries.append((song.id, "context", context))

    logger.info("rendering", songs=len(pending), texts=len(entries))
    renderings = translator.render([text for _, _, text in entries])

    by_song: dict[str, dict[str, Rendering]] = {}
    for (song_id, field, _), rendering in zip(entries, renderings, strict=True):
        by_song.setdefault(song_id, {})[field] = rendering

    for song in pending:
        fields = by_song.get(song.id, {})
        title = fields.get("title")
        lyrics = fields.get("lyrics")
        context = fields.get("context")
        store.save(
            "translations",
            song.id,
            SongTranslation(
                song_id=song.id,
                title_en=title.translation if title else None,
                title_translit=title.transliteration if title else None,
                lyrics_en=lyrics.translation if lyrics else None,
                lyrics_translit=lyrics.transliteration if lyrics else None,
                context_en=context.translation if context else None,
                context_translit=context.transliteration if context else None,
            ),
        )
    logger.info("translated", songs=len(pending))
    return len(pending)
