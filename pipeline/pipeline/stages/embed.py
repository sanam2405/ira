"""embed: turn each song (+ its translation) into multi-vector embeddings.

One vector per (field, language, chunk):
  - title / lyrics / context  -> Bengali (authoritative) AND English (sharper for
    English queries)
  - citations                 -> Bengali source only, chunked (large, often already
    contain English)

Long fields are chunked under the model's input cap. Resumable: songs that already have
an embeddings record for the current model are skipped.
"""

import structlog
from core.chunking import chunk_text
from core.config import settings
from core.domain import (
    Embedding,
    Field,
    Lang,
    Song,
    SongEmbeddings,
    SongTranslation,
    TaskType,
)
from core.ports import DocumentStore, EmbeddingProvider

logger = structlog.get_logger(__name__).bind(stage="embed")


def _units_for(song: Song, translation: SongTranslation | None) -> list[Embedding]:
    """Build the (vector-less) embeddable units for one song."""
    target = settings.chunk_target_tokens
    overlap = settings.chunk_overlap_tokens

    # (field, lang, text) sources. None text is skipped.
    sources: list[tuple[Field, Lang, str | None]] = [
        (Field.TITLE, Lang.BN, song.title),
        (Field.TITLE, Lang.EN, translation.title_en if translation else None),
        (Field.LYRICS, Lang.BN, song.lyrics),
        (Field.LYRICS, Lang.EN, translation.lyrics_en if translation else None),
        (Field.CONTEXT, Lang.BN, song.metadata.get("context")),
        (Field.CONTEXT, Lang.EN, translation.context_en if translation else None),
    ]

    units: list[Embedding] = []

    def add(field: Field, lang: Lang, text: str | None, start: int) -> int:
        idx = start
        for chunk in chunk_text(text or "", target, overlap):
            units.append(
                Embedding(
                    id=Embedding.make_id(song.id, field, lang, idx),
                    song_id=song.id,
                    field=field,
                    lang=lang,
                    chunk_index=idx,
                    text=chunk,
                )
            )
            idx += 1
        return idx

    for field, lang, text in sources:
        add(field, lang, text, 0)

    # citations: multiple source strings, chunk each, running index across all of them
    cit_idx = 0
    for citation in song.citations:
        cit_idx = add(Field.CITATION, Lang.BN, citation, cit_idx)

    return units


def run_embed(
    store: DocumentStore, embedder: EmbeddingProvider, overwrite: bool = False
) -> int:
    done = 0
    for song in store.iter("songs", Song):
        if not overwrite and store.exists("embeddings", song.id):
            continue
        translation = store.load("translations", song.id, SongTranslation)
        units = _units_for(song, translation)
        if not units:
            continue
        vectors = embedder.embed([u.text for u in units], TaskType.DOCUMENT)
        for unit, vector in zip(units, vectors, strict=True):
            unit.vector = vector
        store.save(
            "embeddings",
            song.id,
            SongEmbeddings(song_id=song.id, model_id=embedder.model_id, items=units),
        )
        done += 1
        if done % 50 == 0:
            logger.info("embedding", done=done)
    logger.info("embedded", songs=done)
    return done
