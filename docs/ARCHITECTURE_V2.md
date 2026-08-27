# CloudMatch v2 Architecture

CloudMatch v2 is an explainable retrieval prototype for cloud-product discovery.

## Request flow

1. `api/index.py` receives a search request.
2. `api/catalog_matcher.py` normalizes vendor and product text.
3. The default search sends the query to an open-web search provider with marketplace-scoped intent.
4. Only observed web pages are returned as results; no marketplace result is fabricated.
5. Provider links remain available for direct inspection. Google Cloud uses the Marketplace browse route.
6. An optional LLM web-search tool can retrieve live results when `OPENAI_API_KEY` is configured.

## Agent integration

`/api/mcp` exposes an agent tool interface with `tools/list` and `tools/call` operations:

- `search_marketplaces`
- `catalog_lookup` (explicit seed-catalog lookup only)
- `suggest_queries`

This endpoint is intentionally described as MCP-compatible tooling, not a complete MCP server
transport. A future version can add the official MCP transport and lifecycle requirements.

## Current data boundary

The repository contains a 154-row vendor/product catalog for evaluation and explicit lookup only.
It is never used as the default marketplace search source. The default path uses open-web search;
provider APIs or permitted ingestion adapters should replace it for durable listing verification.

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
