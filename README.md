# CloudMatch

CloudMatch is a zero-cost, agent-native research service for cloud marketplace discovery. It turns natural-language product requests into grounded briefs backed by reviewed public listings, exposes stable evidence IDs and source URLs, and abstains when its evidence cannot support an answer.

[Live deployment](https://cloudmatch-theta.vercel.app) · [Architecture](docs/ARCHITECTURE_V3.md)

## Why it is different

- **Grounded agent workflow:** interpret provider and intent, retrieve candidates, calculate confidence, return evidence, or abstain.
- **Inspectable provenance:** every marketplace result carries a stable ID, provider, public source URL, verification label, and date.
- **No paid runtime dependency:** no AWS account, Azure subscription, API key, hosted model, vector database, or Firecrawl account is required to run the product.
- **Hybrid retrieval with strict labels:** the reviewed evidence snapshot and 154-record benchmark catalog never masquerade as live inventory.
- **Agent integration:** five tools are available through native FastMCP and an HTTP JSON-RPC surface.
- **Measured behavior:** separate labeled sets test catalog ranking and the grounded agent's retrieval, provider constraints, and abstention.
- **Evidence operations:** schema/domain validation and a scheduled CI workflow make snapshot maintenance reproducible.

Firecrawl is used only as an optional development tool to discover and review public listing pages before they enter the versioned snapshot. Production reads the committed evidence file and continues to work with no Firecrawl key or quota.

## Run and verify

Python 3.10+ is sufficient; the production path uses the standard library.

```bash
python3 -m venv .venv
.venv/bin/pip install pytest
.venv/bin/python dev_server.py
```

Open `http://127.0.0.1:8000`, then run:

```bash
.venv/bin/python -m pytest -q
PYTHONPATH=. .venv/bin/python evaluation/evaluate.py
PYTHONPATH=. .venv/bin/python evaluation/evaluate_agent.py
.venv/bin/python scripts/validate_evidence.py
```

Use `scripts/validate_evidence.py --check-urls` for a live network check. CI intentionally performs deterministic schema/provenance validation without depending on third-party uptime.

## API and MCP

```bash
curl https://cloudmatch-theta.vercel.app/api/health
curl -X POST https://cloudmatch-theta.vercel.app/api/research \
  -H 'Content-Type: application/json' \
  -d '{"request":"Find enterprise automation products on Azure"}'
curl -X POST https://cloudmatch-theta.vercel.app/api/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

For a native stdio MCP server, install `requirements-mcp.txt` and run `python mcp_server.py`. Tools: `research_products`, `compare_products`, `search_marketplaces`, `get_evidence`, and `catalog_lookup`.

## Honest limits

- The reviewed snapshot currently contains 11 AWS and Azure listings and is not a complete or real-time marketplace inventory.
- Google Cloud remains link-only until reviewed records are added; provider-constrained requests correctly abstain when coverage is absent.
- The 25-case catalog and 15-case agent sets are development evaluations, not claims about production-scale recall.
- Retrieval is deterministic and explainable; “AI-native” refers to the agent contract and grounded decision workflow, not an unnecessary paid LLM call.
- The static UI loads React from a CDN, so local/offline frontend bundling remains future hardening work.

## Source layout

```text
api/agent_research.py       intent parsing, grounded briefs, abstention
api/evidence_store.py       reviewed-evidence retrieval and provenance
api/open_search.py          hybrid evidence/benchmark orchestration
api/index.py                Vercel HTTP API and JSON-RPC tool surface
data/verified_listings.json versioned public-listing evidence
mcp_server.py               native FastMCP stdio server
evaluation/                 labeled catalog and agent evaluations
scripts/validate_evidence.py snapshot integrity and optional URL checks
public/                     production research UI
```
