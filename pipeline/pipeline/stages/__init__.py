"""Pipeline stages: ingest -> translate -> embed -> index.

Each stage reads/writes through ports, keys everything by stable song id, and is
idempotent/resumable (re-running skips work already done).
"""

from pipeline.stages.embed import run_embed
from pipeline.stages.index import run_index
from pipeline.stages.ingest import run_ingest
from pipeline.stages.translate import run_translate

__all__ = ["run_embed", "run_index", "run_ingest", "run_translate"]
