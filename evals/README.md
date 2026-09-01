# CloudMatch evaluations

`live_cases.json` is a labeled evaluation set, not a product catalog and never a runtime data source. Each case issues a fresh Tavily request and checks:

- expected grounded or abstained behavior;
- strict provider-domain provenance;
- zero canonical-title duplicates;
- bounded evidence snippets;
- top-result coverage of every labeled product term;
- per-provider positive retrieval, mean latency, p95 latency, and explicit failure reasons.

Run `python3 evals/run_live_evals.py`. The suite contains 24 cases—18 current products and six deliberately nonexistent queries—and uses 24 one-credit Tavily fast searches. A 0.65-second inter-case delay keeps the suite below the development-key rate limit when search responses are very fast.

The command exits successfully only when provenance/quality and negative-abstention rates are 100% and aggregate positive retrieval is at least 75%. Per-provider recall remains visible even when the aggregate gate passes. Identical live queries may vary, and failures are intentionally reported rather than replaced with local fixtures.

The September 1, 2026 v4.3 run passed 23/24 cases: 94.4% positive retrieval, 100% provider availability, 100% negative abstention, 704 ms mean latency, and 878 ms p95 latency. AWS and Azure positive retrieval were 100%; GCP was 83.3%, with Neo4j Community Edition as the sole miss.
