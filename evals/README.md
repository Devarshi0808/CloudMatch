# CloudMatch evaluations

`live_cases.json` is a labeled evaluation set, not a product catalog and never a runtime data source. Each case issues a fresh Tavily request and checks:

- expected grounded or abstained behavior;
- strict provider-domain provenance;
- zero canonical-title duplicates;
- bounded evidence snippets;
- top-result lexical relevance.

Run `python3 evals/run_live_evals.py`. The suite currently uses 12 Tavily basic-search credits.

The command exits successfully only when provenance/quality and negative-abstention rates are 100% and positive retrieval is at least 75%. The August 28, 2026 v4.2 run reached 88.9% positive retrieval and 91.7% overall success; the remaining miss was a JavaScript-heavy Google Cloud Marketplace listing that was visible in the provider UI but absent from Tavily's indexed product-page results. Identical live queries may vary, and that failure is intentionally visible.
