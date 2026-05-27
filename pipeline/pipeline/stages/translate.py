"""translate: fill English translation + transliteration for each song's free text.

Covers title, lyrics, and context (the human-readable fields a non-Bengali reader
needs). Citations are left in source form — they are large and frequently already carry
English. Resumable: songs that already have a translation record are skipped.
"""

import structlog
from core.domain import Song, SongTranslation
from core.ports import DocumentStore, TranslationProvider

logger = structlog.get_logger(__name__).bind(stage="translate")


def run_translate(
    store: DocumentStore, translator: TranslationProvider, overwrite: bool = False
) -> int:
    done = 0
    for song in store.iter("songs", Song):
        if not overwrite and store.exists("translations", song.id):
            continue
        context = song.metadata.get("context", "") or ""
        translation = SongTranslation(
            song_id=song.id,
            title_en=translator.translate(song.title),
            title_translit=translator.transliterate(song.title),
            lyrics_en=translator.translate(song.lyrics),
            lyrics_translit=translator.transliterate(song.lyrics),
            context_en=translator.translate(context) if context else None,
            context_translit=translator.transliterate(context) if context else None,
        )
        store.save("translations", song.id, translation)
        done += 1
        if done % 50 == 0:
            logger.info("translating", done=done)
    logger.info("translated", songs=done)
    return done
