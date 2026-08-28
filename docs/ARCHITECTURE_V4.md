# CloudMatch v4 architecture

```text
UI / MCP request
      ↓
intent + provider detection
      ↓
one live Tavily domain-restricted search (over-fetch candidates)
      ↓
HTTPS hostname + marketplace-path validation
      ↓
lexical quality filter + canonical-title deduplication
      ↓
grounded result set or explicit abstention
```

## Live retrieval

`api/live_search.py` submits one Tavily basic search restricted to the selected official marketplace domains. Tavily returns titles, content snippets, URLs, and relevance scores. CloudMatch then applies its own allowlist for exact official hostnames and marketplace paths; lookalike domains and unrelated official pages are rejected.

Each accepted result includes a URL-derived stable ID, provider, concise snippet, match score, matched query terms, official-domain verification label, and UTC retrieval timestamp. Tracking parameters are removed before stable IDs are created. Exact normalized titles are collapsed per provider, with the higher-ranked listing retained. No result records are stored in the repository.

## Failure model

Each provider returns `ok` or `unavailable` independently, with a live result count and bounded diagnostic detail. A provider-constrained natural-language request searches only that provider. Zero verified results produce abstention; there is no local fallback.

## Interfaces

The Vercel handler exposes search, research, and JSON-RPC MCP endpoints. The native FastMCP stdio server exposes the same three operations. Both surfaces call the same live retrieval module, so agents and the UI share identical source boundaries. The UI uses one research request and renders its single evidence set in both the decision and result explorer; it does not issue an independent second search.

## Verification

Deterministic tests mock the Tavily network boundary and cover exact-domain rejection, provider detection, relevance filtering, canonicalization, deduplication, snippet bounds, missing configuration, API input handling, MCP discovery, grounded response contracts, and the unified UI data flow.

`evals/live_cases.json` is a labeled query set, never a runtime catalog. The live runner measures provenance quality, duplicate rate, bounded snippets, positive retrieval, and negative-query abstention against current indexing. Its pass threshold requires 100% provenance/quality compliance, 100% negative abstention, and at least 75% positive retrieval.
