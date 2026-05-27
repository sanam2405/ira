"""ira core — the shared search brain.

Vendor-neutral domain models, the four ports, their adapters, chunking, and config.
Both `pipeline` (writes the index) and `ira_api` (reads/searches it) depend on this
package; nothing here depends on Scrapy or FastAPI. See CLAUDE.md.
"""
