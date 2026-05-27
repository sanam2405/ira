"""Shared concurrency helper — used across adapters and stages.

`parallel_map` runs a blocking function over many items on a thread pool (the Gemini
SDK calls are blocking HTTP, so threads give real speedup), preserves input order, and
logs progress. Exceptions propagate from the first failing item (per-item retries belong
inside `fn`, e.g. via tenacity).
"""

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypeVar

import structlog

logger = structlog.get_logger(__name__).bind(context="parallel_map")

T = TypeVar("T")
R = TypeVar("R")


def parallel_map(
    fn: Callable[[T], R],
    items: Iterable[T],
    *,
    max_workers: int = 8,
    log_every: int = 200,
    desc: str = "parallel_map",
) -> list[R]:
    """Apply `fn` to each item concurrently; return results in input order."""
    items = list(items)
    if not items:
        return []
    if max_workers <= 1 or len(items) == 1:
        return [fn(item) for item in items]

    results: list[R | None] = [None] * len(items)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fn, item): i for i, item in enumerate(items)}
        done = 0
        for future in as_completed(futures):
            results[futures[future]] = future.result()
            done += 1
            if log_every and done % log_every == 0:
                logger.info(desc, done=done, total=len(items))
    return results  # type: ignore[return-value]
