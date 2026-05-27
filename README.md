# _ira_

## _with_ ♥️ _for love by sanam_

> _ira, one lyric at a time_ — a search engine for Tagore's songs, so they can be found and
> understood by anyone, in any tongue.

- [Manas Pratim Biswas](https://www.linkedin.com/in/manas-pratim-biswas)

---

### What's inside

A `uv` workspace + a web app, orchestrated with [`go-task`](https://taskfile.dev):

- **`core/`** — shared search brain: domain, ports, adapters, embeddings
- **`pipeline/`** — Python/Scrapy ETL: scrape → translate & transliterate → embed → index
- **`api/`** — FastAPI search service
- **`web/`** — Next.js frontend

See [`CLAUDE.md`](./CLAUDE.md) for architecture and development notes.
