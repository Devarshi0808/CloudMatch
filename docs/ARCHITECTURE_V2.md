# CloudMatch v2 architecture

## User story

A user submits a vendor, product, or both. CloudMatch concurrently queries every supported official provider adapter, normalizes returned listings into one schema, and renders provenance and provider health. If no official listing is available, it returns separately labeled suggestions from a local benchmark catalog plus direct provider search links.

```text
Browser
  -> POST /api/search
     -> concurrent adapter fan-out
        -> AWS Marketplace Discovery API (SigV4/IAM)
        -> Azure Marketplace Catalog API (API key)
        -> GCP capability report (link-only)
     -> normalized official listings
     -> explainable benchmark retrieval
  <- results + provenance + provider health + timing
```

## Provider contracts

| Provider | Integration | Authentication | Production state |
|---|---|---|---|
| AWS | Marketplace Discovery `SearchListings` | AWS credential chain / IAM | Implemented, credential-gated |
| Azure | Marketplace Catalog Search API `2025-05-01` | `X-API-Key` | Implemented, credential-gated |
| Google Cloud | Provider browse URL | None | Link-only; no supported public catalog search API |

All official results normalize to: `provider`, `provider_name`, `listing_id`, `title`, `vendor`, `description`, `url`, `source`, `verification`, and `retrieved_at`.

## Failure semantics

Adapters return structured health instead of raising through the request boundary:

- `ok`: official API answered, including valid zero-result searches;
- `not_configured`: required credentials are absent;
- `error`: configured provider failed or timed out;
- `link_only`: provider has no supported programmatic discovery path;
- `skipped`: query validation prevented execution.

The UI never converts a provider search URL into a listing and never labels benchmark rows as observed marketplace inventory.

## Retrieval and evaluation

The 154-row XLSX is a benchmark and fallback candidate set. Ranking combines normalized token overlap and sequence similarity across individual vendor/product fields and the combined query. Candidates below a 40-point confidence floor are rejected.

The evaluator reports top-1 precision, top-3 recall, MRR@8, abstention accuracy, overall accuracy, and per-case failures. The current 25 cases are deliberately small and transparent; metrics must not be generalized to marketplace-scale quality.

## Agent interfaces

- `mcp_server.py`: official FastMCP stdio transport, Python 3.10+.
- `/api/mcp`: lightweight JSON-RPC `tools/list` and `tools/call` interface for the deployed demo. It is not described as a full Streamable HTTP MCP transport.

Both surfaces expose the same three operations: `search_marketplaces`, `catalog_lookup`, and `ingest_listings`.

## Deployment and verification

Vercel serves `public/` statically and `api/index.py` on Python 3.12. Responses include duration, selected source, and result count. The release gate is maintained tests, evaluation, local HTTP flow, Vercel build success, live endpoint checks, and runtime-error inspection.
