# CloudMatch v2 Architecture

CloudMatch v2 is an explainable retrieval prototype for cloud-product discovery.

## Request flow

1. `api/index.py` receives a search request.
2. `api/catalog_matcher.py` normalizes vendor and product text.
3. The matcher ranks the local XLSX catalog using token overlap and sequence similarity.
4. Each candidate returns a score and the evidence used to rank it.
5. Provider links are generated as external discovery links and are not presented as verified listings.
	Google Cloud uses the Marketplace browse route because its search route requires sign-in.
6. An optional LLM can suggest query variants when `OPENAI_API_KEY` is configured.

## Agent integration

`/api/mcp` exposes an agent tool interface with `tools/list` and `tools/call` operations:

- `search_catalog`
- `suggest_queries`

This endpoint is intentionally described as MCP-compatible tooling, not a complete MCP server
transport. A future version can add the official MCP transport and lifecycle requirements.

## Current data boundary

The repository contains a 154-row vendor/product catalog. It does not yet contain a verified,
continuously refreshed inventory of AWS, Azure, or Google Cloud listings. Provider adapters should
be added only through official APIs or permitted ingestion methods. Until then, provider URLs are
external search fallbacks.

## Evaluation

`evaluation/golden_queries.json` contains a small, transparent development set. Run:

```bash
PYTHONPATH=. python3 evaluation/evaluate.py
```

The result is a retrieval baseline, not a production quality claim. The set should grow with
reviewed positive and negative pairs before reporting metrics publicly.

## Observability

Search responses include:

- `duration_ms`
- `cache_hit`
- `cache_size`

The cache is bounded per warm serverless process and is not a shared persistence layer.
