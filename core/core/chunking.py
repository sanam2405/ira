"""Token-aware chunking, so no single embed input exceeds the model's input cap.

gemini-embedding-001 caps input at 2,048 tokens, but `context` and `citations` can be
far larger — hence multi-vector. We pack whole lines/paragraphs up to a token budget
(with a little overlap for continuity) using tiktoken's cl100k as a cheap proxy for the
Gemini tokenizer. Splitting on line boundaries keeps lyric lines and sentences intact.
"""

import tiktoken

_ENC = tiktoken.get_encoding("cl100k_base")


def _ntokens(text: str) -> int:
    return len(_ENC.encode(text))


def chunk_text(text: str, target_tokens: int, overlap_tokens: int = 0) -> list[str]:
    """Split `text` into chunks of <= ~target_tokens, breaking on line boundaries.

    Short text returns a single chunk. A line longer than the budget is emitted on its
    own (we never split mid-line). Returns [] for empty text.
    """
    text = text.strip()
    if not text:
        return []
    if _ntokens(text) <= target_tokens:
        return [text]

    lines = text.split("\n")
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for line in lines:
        line_tokens = _ntokens(line)
        if current and current_tokens + line_tokens > target_tokens:
            chunks.append("\n".join(current))
            # carry a tail of the previous chunk forward for context continuity
            current, current_tokens = _overlap_tail(current, overlap_tokens)
        current.append(line)
        current_tokens += line_tokens

    if current:
        chunks.append("\n".join(current))
    return chunks


def _overlap_tail(lines: list[str], overlap_tokens: int) -> tuple[list[str], int]:
    if overlap_tokens <= 0:
        return [], 0
    tail: list[str] = []
    tokens = 0
    for line in reversed(lines):
        t = _ntokens(line)
        if tokens + t > overlap_tokens:
            break
        tail.insert(0, line)
        tokens += t
    return tail, tokens
