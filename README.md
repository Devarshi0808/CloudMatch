# CloudMatch

CloudMatch is an evidence-first retrieval service for cloud marketplace discovery. It searches official AWS and Azure catalog APIs when credentials are configured, reports provider health independently, and falls back to a clearly labeled 154-record benchmark catalog instead of fabricating listings.

[Live deployment](https://cloudmatch-theta.vercel.app) · [Architecture](docs/ARCHITECTURE_V2.md)

## What makes v2 different

- **Official ingestion:** AWS Marketplace Discovery `SearchListings` through Boto3/SigV4 and Azure Marketplace Catalog Search through its data-plane API.
- **Explicit capability boundaries:** Google Cloud Marketplace is link-only because no supported public catalog-search API is available.
- **Provenance on every result:** official results carry provider, source, verification method, listing ID, and retrieval timestamp.
- **Independent degradation:** one unavailable provider does not break the others; every adapter reports `ok`, `not_configured`, `error`, or `link_only`.
- **Explainable fallback:** the bundled catalog ranks vendor/product candidates with field and combined similarity evidence. It is never presented as live marketplace data.
- **Agent integration:** a native FastMCP stdio server plus an HTTP JSON-RPC tool surface.
- **Measured development baseline:** 25 transparent cases cover exact matches, aliases, typos, ambiguity, and abstention. This is a development set, not a production accuracy claim.

## Run locally

Python 3.10+ is required for native MCP; Vercel uses Python 3.12.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install pytest
.venv/bin/python dev_server.py
```

Open `http://127.0.0.1:8000`.

Provider credentials are optional. Without them, the UI remains functional using labeled benchmark results. Copy `.env.example` and configure:

- standard AWS credentials with `aws-marketplace:SearchListings` access;
- `AZURE_MARKETPLACE_CATALOG_API_KEY` from the Azure Marketplace Catalog team.

## Verify

```bash
.venv/bin/python -m pytest -q
PYTHONPATH=. .venv/bin/python evaluation/evaluate.py
```

Current maintained suite: **13 tests**. Current development set: **20 positive + 5 negative cases**. The legacy Streamlit/scraper prototype remains under `src/` and uses `requirements-legacy.txt`; it is not part of the v2 production path.

## API

```bash
curl https://cloudmatch-theta.vercel.app/api/health
curl "https://cloudmatch-theta.vercel.app/api/search?vendor=Red%20Hat&solution=Ansible"
curl -X POST https://cloudmatch-theta.vercel.app/api/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Native MCP:

```bash
python -m pip install -r requirements-mcp.txt
python mcp_server.py
```

Available tools: `search_marketplaces`, `catalog_lookup`, and `ingest_listings`.

## Honest limits

- Official AWS/Azure searches require credentials and are not enabled on the public deployment yet.
- Google Cloud offers no equivalent supported public discovery API, so CloudMatch provides a direct provider search link.
- The 25-case evaluation is small and derived from the bundled catalog. It validates behavior and metric correctness, not real-world marketplace recall.
- The static UI loads React from a CDN; a bundled frontend is a future hardening task.

## Source layout

```text
api/provider_ingestion.py   official adapters + normalization
api/open_search.py          hybrid orchestration + source boundaries
api/catalog_matcher.py      deterministic explainable fallback
api/index.py                Vercel HTTP API + JSON-RPC tools
mcp_server.py               native FastMCP stdio server
evaluation/                 labeled development set + evaluator
public/                     production UI
src/                        archived v1 Streamlit/scraper prototype
```
