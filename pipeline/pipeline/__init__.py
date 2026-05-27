"""ira pipeline — offline ETL: ingest → translate → embed → index.

Everything external (embedding model, translation provider, document store, search
backend) sits behind a port in `core.ports`. Core/stage logic depends only on
those ports, never on a vendor SDK. See CLAUDE.md.
"""
