# CloudMatch evaluations

`live_cases.json` is a labeled evaluation set, not a product catalog and never a runtime data source. Each case issues a fresh Tavily request and checks:

- expected grounded or abstained behavior;
- strict provider-domain provenance;
- zero canonical-title duplicates;
- bounded evidence snippets;
- top-result lexical relevance.

Run `python3 evals/run_live_evals.py`. The suite currently uses 12 Tavily basic-search credits.

The command exits successfully only when provenance/quality and negative-abstention rates are 100% and positive retrieval is at least 75%. Identical live queries can cross that threshold between runs because Tavily sometimes returns no candidates for otherwise discoverable Azure or Google Cloud listings; the failure is intentionally visible.
