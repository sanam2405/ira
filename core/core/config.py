"""Typed settings, loaded from environment / `.env`.

Kept provider-agnostic where possible; provider-specific knobs (model ids, dims) live
here so adapters read config rather than hard-coding. Override any field via env, e.g.
`EMBEDDING_MODEL=gemini-embedding-2` once it reaches GA.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Workspace root (core/core/config.py -> ../../.. == ira/). Shared artifacts and the
# .env live here so pipeline (writer) and api (reader) agree on locations.
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=WORKSPACE_ROOT / ".env",
        extra="ignore",
    )

    # --- paths ---
    source_jsonl: Path = WORKSPACE_ROOT / "pipeline" / "scrapy" / "metacite.jsonl"
    data_dir: Path = WORKSPACE_ROOT / "data"
    """Root for the local DocumentStore + SearchBackend artifacts."""

    # --- gemini ---
    gemini_api_key: str = ""

    # --- embedding ---
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768  # Matryoshka-truncated sweet spot
    embedding_max_tokens: int = (
        2048  # gemini-embedding-001 input cap -> drives chunking
    )

    # --- translation ---
    translation_model: str = "gemini-2.5-flash"

    # --- chunking ---
    chunk_target_tokens: int = 1200  # well under embedding_max_tokens, leaves headroom
    chunk_overlap_tokens: int = 100

    # --- search (hybrid ranking) ---
    search_alpha: float = 1.0  # weight on semantic similarity
    search_beta: float = (
        0.3  # weight on soft metadata-filter matches (re-rank, not exclude)
    )
    search_overfetch: int = (
        10  # chunk hits per requested song (multi-vector aggregation)
    )

    # --- concurrency (Gemini calls are blocking HTTP -> threads help) ---
    embedding_concurrency: int = 8  # parallel embed batches
    translation_concurrency: int = 8  # parallel render calls

    # --- batch api (50% cheaper, async; for the one-time full run) ---
    use_batch_api: bool = (
        False  # if true, use Gemini Batch API instead of concurrent calls
    )
    batch_poll_seconds: int = 30  # how often to poll a batch job for completion


settings = Settings()
