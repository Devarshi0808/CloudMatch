# CloudMatch v3 architecture

CloudMatch separates evidence acquisition from runtime retrieval so the public product stays free, deterministic, and auditable.

```text
Optional development review (Firecrawl/browser)
                    ↓
Versioned verified_listings.json → evidence retrieval → grounded brief / abstention
                                              ↘ HTTP JSON-RPC + native MCP
Bundled benchmark catalog ───────→ labeled fallback ↗
```

## Evidence boundary

Only normalized records in `data/verified_listings.json` are treated as marketplace evidence. Each record has a stable ID, provider, vendor, title, public URL, summary, categories, delivery type, and verification date. `scripts/validate_evidence.py` rejects missing fields, duplicate IDs/URLs, unapproved source domains, and future dates. Its optional network mode checks source reachability.

Firecrawl can assist a maintainer in discovering and reading public pages, but it is not imported by the application, called by CI, or required in production. A human reviews normalized records before commit.

## Decision flow

1. Parse provider aliases and discovery/comparison intent from a natural-language request.
2. Filter by provider before scoring to enforce the requested marketplace boundary.
3. Rank records with token coverage, phrase match, and inverse document frequency.
4. Require both a score threshold and 75% meaningful-query coverage.
5. Return a grounded brief with confidence, matched terms, evidence IDs, and URLs—or an explicit abstention.

This last step prevents high scores from generic words such as “cloud” or “platform” from producing unsupported answers.

## Interfaces

- `/api/research`: natural-language grounded brief.
- `/api/search`: vendor/product evidence search plus separately labeled benchmark suggestions.
- `/api/mcp`: JSON-RPC `tools/list` and `tools/call` compatibility surface.
- `mcp_server.py`: native FastMCP stdio server with the same five tools.

## Evaluation

The legacy catalog set contains 20 positive and 5 negative cases. The agent set contains 10 grounded and 5 abstention cases and reports status accuracy, evidence recall@5, provider-constraint accuracy, and abstention accuracy. These deliberately small development sets verify contracts and regression behavior; they are not external benchmarks.
