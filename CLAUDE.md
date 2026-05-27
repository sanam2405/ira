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

Three independent projects, orchestrated by [`go-task`](https://taskfile.dev) at the root:

| Dir         | Stack                          | Role                                                        |
| ----------- | ------------------------------ | ----------------------------------------------------------- |
| `pipeline/` | Python 3.12, `uv`, Scrapy      | Offline ETL: scrape → translate/transliterate → embed → index |
| `api/`      | Python 3.12, `uv`, FastAPI     | Online search API over the indexed data                     |
| `web/`      | Next.js 15, React 19, `pnpm`   | Frontend (search box, song detail). UI is intentionally rough for now |
| `design/`   | —                              | Logos, mockups                                              |

`pipeline/` and `api/` are separate `uv` projects with their own `pyproject.toml`.

## Commands

Run from the repo root unless noted. Tasks are defined in `Taskfile.yaml`.

```bash
task format          # format web (prettier) + api & pipeline (ruff)
task start           # start web dev server (api start is commented out)

# per-project
cd web && pnpm dev                       # next dev --turbopack
cd api && uv run fastapi dev app.py      # FastAPI dev server
cd pipeline && uv run scrapy crawl gitabitan -O gitabitan.jsonl   # from pipeline/scrapy

# lint / format manually
uv run ruff check --fix && uv run ruff format    # in api/ or pipeline/
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
| `EmbeddingProvider`   | text/multimodal → vectors                       | **Gemini `gemini-embedding-2`** → BGE-m3, OpenAI, Cohere |
| `TranslationProvider` | Bengali → English translation + transliteration | **Gemini** → Sarvam, IndicTrans2                     |
| `DocumentStore`       | persist song docs + translations + metadata     | **local files (parquet/json)** → Postgres, object storage |
| `SearchBackend`       | index + retrieve (vector, lexical, filters)     | **local (numpy + in-mem lexical)** → Typesense, Turbopuffer |

A `SearchService` in `api/` composes `EmbeddingProvider` (query-time) + `SearchBackend` and owns
**hybrid ranking with soft filters** (see below). It depends on the ports, never the adapters.

### Key design decisions (rationale lives in `MUSE.md`)

- **Embedding model: `gemini-embedding-2` (multimodal v2).** Chosen for top multilingual MTEB and
  8,192-token input. Truncate via Matryoshka to **768 dims** (the recommended sweet spot). It is
  preview — its vector space may change at GA, which means a full re-embed. That risk is accepted
  precisely because the `EmbeddingProvider` port makes re-embedding a contained operation.
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
- **Filters are soft.** They re-rank/boost candidates, they do not hard-exclude. Concretely a
  score fusion like `final = α·semantic + β·field_matches`, computed in-process at this scale.
- **Local-first storage, adapter-gated.** Start with in-memory numpy + local files. Swapping to
  Typesense (lexical typeahead + vector + facets in one engine) or Turbopuffer is an adapter
  change, not a rewrite. Don't add Postgres/object-storage/vector-DB infra until data or traffic
  forces it.

### Pipeline stages (offline, idempotent, resumable)

`ingest` (jsonl → typed docs) → `translate` (+ transliterate) → `embed` (multi-vector) →
`index` (write to `SearchBackend`). Each stage reads/writes through `DocumentStore` and keys
everything by a stable song id (UUID).

Existing `pipeline/scripts/item_*.py` files are docstring stubs describing these stages — flesh
them out behind the ports rather than scripting vendor calls inline. `utils/tokenizer.py`
(`TokenCounter`) is a working cost/token estimator used during planning.

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
