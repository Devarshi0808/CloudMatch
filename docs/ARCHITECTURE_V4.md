# CloudMatch v4 architecture

```text
UI / MCP request
      ↓
intent + provider detection
      ↓
one live Tavily domain-restricted search
      ↓
HTTPS hostname + marketplace-path validation
      ↓
grounded result set or explicit abstention
```

## Live retrieval

`api/live_search.py` submits one Tavily basic search restricted to the selected official marketplace domains. Tavily returns titles, content snippets, URLs, and relevance scores. CloudMatch then applies its own allowlist for exact official hostnames and marketplace paths; lookalike domains and unrelated official pages are rejected.

Each accepted result includes a URL-derived stable ID, provider, title, snippet, official-domain verification label, and UTC retrieval timestamp. No result records are stored in the repository.

## Failure model

Each provider returns `ok` or `unavailable` independently, with a live result count and bounded diagnostic detail. A provider-constrained natural-language request searches only that provider. Zero verified results produce abstention; there is no local fallback.

## Interfaces

The Vercel handler exposes search, research, and JSON-RPC MCP endpoints. The native FastMCP stdio server exposes the same three operations. Both surfaces call the same live retrieval module, so agents and the UI share identical source boundaries.

## Verification

Deterministic tests mock the Tavily network boundary and cover exact-domain rejection, provider detection, missing configuration, API input handling, MCP discovery, and grounded response contracts. Live production checks separately verify real network behavior because external search results cannot be made deterministic.
