# CLAUDE.md

Guidance for working in the **ira** monorepo. Read this before making changes.

## What ira is

A semantic + lexical search engine for **Rabindra Sangeet** (Tagore's songs from
[gitabitan.net](http://gitabitan.net)). The audience is **non-native users who cannot read
or write Bengali** but want to find songs and understand their meaning. Every result must be
surfaceable in three forms: **original Bengali**, **transliteration** (Latin script, for
singing/recognition), and **English translation** (for comprehension). Search spans not just
lyrics but mood, context, references, raag, taal, and time of composition.

`ira` is a personal project (built by Manas, alias _sanam_). Optimize for **learning and clean,
swappable design** over shipping speed — over-engineering toward modularity is acceptable here.

## Monorepo layout

A **`uv` workspace** (one shared `.venv` + one root `uv.lock`) of three Python members plus the
web app, orchestrated by [`go-task`](https://taskfile.dev) at the root:

| Dir         | Package    | Stack                        | Role                                                        |
| ----------- | ---------- | ---------------------------- | ----------------------------------------------------------- |
| `core/`     | `core`     | Python 3.12, `uv`            | Shared search brain: domain, ports, adapters, chunking, config. No Scrapy/FastAPI. |
| `pipeline/` | `pipeline` | Python 3.12, `uv`, Scrapy    | Offline ETL: scrape → translate/transliterate → embed → index. Depends on `core`. |
| `api/`      | `api`      | Python 3.12, `uv`, FastAPI   | Online search API (`/search`, `/songs/{id}`, `/health`) — thin shell over `core`'s SearchService. |
| `web/`      | —          | Next.js 15, React 19, `pnpm` | Frontend (search box, song detail). UI is intentionally rough for now |
| `design/`   | —          | —                            | Logos, mockups                                              |

`pipeline` and `api` both depend on `core` as a workspace source (local path, editable) — edit
`core` and both see it instantly. The package dir is nested inside the project dir (e.g.
`core/core/`, `pipeline/pipeline/`); the outer dir holds `pyproject.toml`, the inner is what you
`import`. `api` is a virtual project (run by path, not installed).

## Commands

The root is a virtual workspace, so `uv` commands work from the root or any member dir.

```bash
task format          # format web (prettier) + core/api/pipeline (ruff)
task start           # start web + api dev servers

uv sync                                      # set up the shared venv (run once / after dep changes)
uv run python -m pipeline.cli all            # ingest → translate → embed → index
uv run python -m pipeline.cli all --fake     # offline, no key (plumbing/smoke test)
uv run python -m pipeline.cli search "monsoon longing"

cd web && pnpm dev                           # next dev --turbopack
cd api && uv run fastapi dev app.py          # FastAPI dev server
cd pipeline/scrapy && uv run scrapy crawl gitabitan -O gitabitan.jsonl

uv run ruff check --fix && uv run ruff format # lint/format (from root or a member dir)
```

## Data

Scraping is **done**. The canonical dataset lives in `pipeline/scrapy/`:

- `metacite.jsonl` — **canonical**, 2,276 songs with `title`, `lyrics`, `metadata`, `citations`
- `metadata.jsonl`, `gitabitan.jsonl` — earlier crawl stages (subsets of the above)

`*.jsonl`/`*.json` are **gitignored** (local-only, regenerable via the Scrapy spider). `MUSE.md`
is also gitignored — it's the private scratchpad / decision log, not committed.

Per-song shape (see `pipeline/scrapy/schema.json` for a full example):

```jsonc
{
  "domain": "gitabitan",
  "title": "...",            // Bengali
  "url": "http://gitabitan.net/top.asp?songid=...",
  "lyrics": "...",           // Bengali, newline-separated lines
  "metadata": {              // raag, taal, raag_taal, composition_date, poet_age,
    "raag": "...",           // composition_location, publication_date,
    "taal": "...",           // gitabitan_index, notation, notator, context (আলোচনা)
    "composition_date": "...",
    "context": "..."         // long-form scholarly context, can be large
  },
  "citations": ["...", "..."] // scholarly commentary, often large (~3.7k tokens/song avg)
}
```

**Scale is small: 2,276 songs.** All vectors fit in RAM. This is why the default search backend
can be plain in-memory numpy — see the architecture notes below before reaching for infra.

## Architecture — modular, swappable by design

The single most important constraint: **every external dependency sits behind an adapter (port)
so models, providers, and stores can be swapped without touching core logic.** When adding a
capability, define/extend the port first, then write the adapter. Never call a vendor SDK
directly from core search/pipeline logic.

### Ports (interfaces) and their adapters

| Port                  | Responsibility                                  | Adapters (current → future)                          |
| --------------------- | ----------------------------------------------- | ---------------------------------------------------- |
| `EmbeddingProvider`   | `embed(texts)` → vectors                        | **Gemini `gemini-embedding-001`** (concurrent) + batch-API variant → `gemini-embedding-2` (at GA), BGE-m3 |
| `TranslationProvider` | `render(texts)` → {translation, transliteration}| **Gemini** (one structured call per text, concurrent) → Sarvam, IndicTrans2 |
| `DocumentStore`       | persist song docs + translations + metadata     | **local files (per-song json)** → Postgres, object storage |
| `SearchBackend`       | index + retrieve (vector, lexical, filters)     | **local (numpy + in-mem lexical)** → Typesense, Turbopuffer |
| `FusionStrategy`      | combine ranked lists into a final order         | **`RRFFusion`** (default, rank-based) ↔ `WeightedSumFusion` (legacy α/β); future cross-encoder / Cohere rerank |

Ports and adapters all live in **`core`**. `core.search.SearchService` composes `DocumentStore`
+ `EmbeddingProvider` (query-time) + `SearchBackend` and owns **hybrid ranking with soft filters**
(see below); `api` is just an HTTP shell over it. It depends on the ports, never the adapters.

**Throughput.** Gemini calls are blocking HTTP, so adapters parallelize via the shared
`core.concurrency.parallel_map` (a thread pool). `TranslationProvider.render` also returns both
English forms in *one* structured call (halving translation calls). For the one-time full-corpus
run, set `USE_BATCH_API=true` to route embeddings through the **Gemini Batch API** (50% cheaper,
async job + polling) via `GeminiBatchEmbeddingProvider`. Concurrency is the low-latency default;
batch is the cheap bulk path — both behind the same port. `core.factory` picks the implementation.

### Key design decisions (rationale lives in `MUSE.md`)

- **Embedding model: `gemini-embedding-001` (GA, stable) for v1.** Chosen over the preview v2 to
  sit on a stable vector space (no forced re-embed from preview→GA churn). Truncate via Matryoshka
  to **768 dims** (recommended sweet spot). Its **2,048-token input cap** makes multi-vector +
  citation chunking *mandatory* — per-song `citations` average ~3.7k tokens. **Planned upgrade:**
  re-embed the whole corpus with `gemini-embedding-2` (multimodal, 8,192-token, top MTEB) once *it*
  reaches GA. The `EmbeddingProvider` port makes that a deliberate, contained operation — not a
  forced migration.
- **Multi-vector per song.** Do **not** embed a whole song as one vector — `context` + `citations`
  alone routinely exceed even large input limits, and field-level hits carry different intent.
  Embed `title`, `lyrics`, `context`, and chunked `citations` as separate vectors that link back
  to the song id.
- **Embed both languages.** Embed original **Bengali** (authoritative, cross-lingual) **and** the
  **English translation** (sharper for English queries), then fuse. Cheap at this scale.
- **Translation/transliteration is v1, not "enrichment."** For a non-Bengali reader the English
  text *is* the product, so it's on the critical path. A single Gemini batch pass yields both.
- **Deferred enrichment.** *Derived* facets (mood, season, theme) are explicitly out of scope for
  now; soft filters use the structured fields already scraped (`raag`, `taal`, `composition_date`,
  `gitabitan_index`, …).
- **Filters are soft, fusion is pluggable.** Hybrid ranking happens via the `FusionStrategy`
  port. Default is **Reciprocal Rank Fusion** (rank-based, scale-agnostic — robust when
  cosine scores cluster tightly); `WeightedSumFusion` keeps the legacy `α·semantic +
  β·field_matches` formula as an explicit fallback. Per-call override via `--fusion` on the
  CLI and `?fusion=` on the API for A/B during tuning. Filters re-rank/boost candidates and
  never hard-exclude — non-matching songs are absent from the filter ranked list and so
  contribute 0 via RRF.
- **Local-first storage, adapter-gated.** Start with in-memory numpy + local files. Swapping to
  Typesense (lexical typeahead + vector + facets in one engine) or Turbopuffer is an adapter
  change, not a rewrite. Don't add Postgres/object-storage/vector-DB infra until data or traffic
  forces it.

### Package layout

```
core/core/
  config.py        typed settings (env vars like GEMINI_API_KEY, reads workspace-root .env)
  domain/          vendor-neutral models + enums (Song, SongTranslation, Embedding, ...)
  ports/           the four ABCs (DocumentStore, EmbeddingProvider, TranslationProvider, SearchBackend)
  adapters/        concrete impls: document_store/, embedding/, translation/, search_backend/
                   each has a real adapter (gemini/local) AND a fake for offline runs
  search/          SearchService + view models (SearchResult, SongView) — hybrid ranking
  chunking.py      token-aware splitter + `truncate_to_tokens` defensive guard
  concurrency.py   parallel_map — shared thread-pool helper used by adapters/stages
  templates.py     get_jinja_template — load Jinja2 prompts from a `templates/` dir next to the caller
  factory.py       build_embedding_provider / build_translation_provider (Gemini vs fake; concurrent vs batch)

pipeline/pipeline/
  stages/          ingest → translate → embed → index (depend only on core's ports)
  cli.py           composition root — the ONLY place concrete adapters are chosen
  tokenizer.py     TokenCounter cost/token estimator (planning tool)

api/
  app.py           FastAPI: /search, /songs/{id}, /health (composition root for the read side)
```

Stages are idempotent/resumable: each keys by stable song UUID and skips work already done
(`DocumentStore.exists`). Artifacts land in **`data/` at the workspace root** (gitignored, shared
between pipeline writer and api reader): `songs/`, `translations/`, `embeddings/` collections + an
index snapshot under `index/`.

```bash
# uses Gemini when GEMINI_API_KEY is set (in workspace-root .env), else fake providers
uv run python -m pipeline.cli all              # ingest → translate → embed → index
uv run python -m pipeline.cli all --fake       # offline, no key (plumbing/smoke test)
uv run python -m pipeline.cli search "monsoon longing"
```

When adding a provider/store: implement the port (in `core/core/ports`), add the adapter under
`core/core/adapters/`, wire it in `pipeline/pipeline/cli.py`. Never call a vendor SDK from
`stages/` or `domain/`.

## Conventions

- **Python:** `ruff` for lint + format (line via `ruff format`). `structlog` for logging
  (bind a `class_name`/`context`). `pydantic` models for all data contracts. Type hints required.
- **Web:** `prettier` (+ organize-imports), ESLint via `next lint`. React Query for data fetching.
  `@/` path alias → `src/`. The web client's API contract types live in `web/src/utils/index.ts`
  (`ISong`, `ISearchResult`); `getSearchResults`/`getSongDetails` are currently mocked and marked
  to be replaced by real API calls.
- **Commits:** `[type]: short summary` where type ∈ `feat|fix|chore|refactor`, with a
  `Signed-off-by:` trailer (DCO). Keep the existing style.

## Guardrails

- Preserve the personal/poetic tone of `README.md` — it's public-facing.
- Keep core logic vendor-agnostic; new providers/stores must implement an existing port.
- Don't introduce hosted infra "because the design doc mentions it" — the 2.3k-song scale doesn't
  justify it yet. Justify any infra addition by data/traffic, behind an adapter.
