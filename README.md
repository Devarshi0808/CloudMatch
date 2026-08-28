# CloudMatch

CloudMatch is an agent-native cloud marketplace research service. Every request performs a current Tavily search restricted to official AWS Marketplace, Microsoft Azure Marketplace, and Google Cloud Marketplace domains. It returns source URLs and retrieval timestamps or explicitly abstains when no live listing can be verified.

[Live deployment](https://cloudmatch-theta.vercel.app) · [Architecture](docs/ARCHITECTURE_V4.md)

## Runtime guarantees

- No bundled product catalog, synthetic listing data, or precomputed result snapshot.
- No AWS account, Azure subscription, marketplace credentials, or paid plan; Tavily's free API key is required.
- Results must use HTTPS, match an allowlisted official hostname, and match that provider's marketplace path.
- Results must also pass query-term coverage thresholds and canonical-title deduplication.
- Evidence snippets are cleaned and bounded; the UI shows at most five ranked results from one shared request.
- Provider failures are reported independently; unavailable retrieval never creates a fallback listing.
- Natural-language research and comparison are available through HTTP and native MCP tools.

The production API makes one Tavily basic search with `include_domains` restricted to the three official hosts, over-fetches up to 15 candidates, then validates, filters, ranks, and deduplicates locally. Automatic parameters and generated answers are disabled to keep each request at one free-plan credit and preserve CloudMatch's own grounding boundary.

## Run and verify

```bash
cp .env.example .env  # add the free TAVILY_API_KEY
python3 -m venv .venv
.venv/bin/pip install pytest
.venv/bin/python dev_server.py
.venv/bin/python -m pytest -q
.venv/bin/python evals/run_live_evals.py
```

The deterministic suite covers parser, allowlist, relevance, deduplication, snippet bounds, abstention, API, MCP, and unified-UI contracts. The labeled live suite uses 12 current marketplace queries and 12 Tavily credits. Consecutive runs on August 27, 2026 measured 100% provenance/quality-gate compliance, 66.7–77.8% positive retrieval, 100% negative-query abstention, and 75–83.3% overall case success. The range is reported because public search coverage fluctuates between identical runs.

For a focused integration check:

```bash
curl -X POST http://127.0.0.1:8000/api/research \
  -H 'Content-Type: application/json' \
  -d '{"request":"Find Red Hat Ansible on AWS"}'
```

## Interfaces

- `POST /api/research` — live natural-language research brief or abstention.
- `GET|POST /api/search` — live vendor/product search.
- `POST /api/mcp` — JSON-RPC `tools/list` and `tools/call`.
- `python mcp_server.py` — native FastMCP stdio server.

MCP tools: `search_marketplaces`, `research_products`, and `compare_products`.

## Honest limitations

- Results depend on public web indexing and provider page discoverability; this is not an exhaustive inventory API.
- The labeled evaluation currently exposes weaker recall for some GCP and Azure listings; CloudMatch abstains rather than relaxing provenance or relevance checks.
- Azure may challenge direct automated requests and Google pages are JavaScript-heavy, which is why discovery uses official-domain web indexing.
- Tavily's free tier currently provides 1,000 basic searches per month. CloudMatch reports quota or retrieval failures instead of hiding them.
- Result snippets come from current search-index content; users can inspect every official source URL directly.
