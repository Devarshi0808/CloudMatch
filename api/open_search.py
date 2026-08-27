"""Hybrid marketplace retrieval with explicit source boundaries."""

import urllib.parse

try:
    from .catalog_matcher import search_catalog
    from .evidence_store import load_evidence, search_evidence
except ImportError:
    from catalog_matcher import search_catalog
    from evidence_store import load_evidence, search_evidence

PROVIDERS = {
    "aws": {"name": "AWS Marketplace", "url": "https://aws.amazon.com/marketplace/search?searchTerms={query}"},
    "azure": {"name": "Microsoft Azure Marketplace", "url": "https://azuremarketplace.microsoft.com/en-us/marketplace/apps?search={query}"},
    "gcp": {"name": "Google Cloud Marketplace", "url": "https://console.cloud.google.com/marketplace/browse?q={query}"},
}


def provider_links(query):
    encoded = urllib.parse.quote_plus(query)
    return {key: {"provider": value["name"], "url": value["url"].format(query=encoded), "source": "provider_search_page"} for key, value in PROVIDERS.items()}


def search_open_marketplaces(vendor="", solution="", limit=10):
    vendor = " ".join(str(vendor or "").split())[:160]
    solution = " ".join(str(solution or "").split())[:160]
    query = " ".join(part for part in (vendor, solution) if part)
    if not query:
        return {"query": "", "matches": [], "catalog_matches": [], "provider_links": {}, "providers": {}, "source": "empty_query", "disclaimer": "Enter a vendor, product, or both."}
    verified = search_evidence(query, limit=limit)
    benchmark = search_catalog(vendor, solution, limit=limit)
    snapshot = load_evidence()
    counts = {provider: sum(item["provider"] == provider for item in snapshot["listings"]) for provider in PROVIDERS}
    providers = {provider: {"provider": provider, "provider_name": config["name"], "status": "snapshot", "listings": [], "detail": f"{counts[provider]} reviewed listings in snapshot"} for provider, config in PROVIDERS.items()}
    return {
        "query": query, "matches": verified, "catalog_matches": benchmark["matches"],
        "catalog_size": benchmark["catalog_size"], "provider_links": provider_links(query), "providers": providers,
        "source": "verified_snapshot" if verified else "benchmark_catalog",
        "retrieval": {"snapshot_results": len(verified), "snapshot_size": len(snapshot["listings"]), "benchmark_results": len(benchmark["matches"])},
        "snapshot_verified_at": snapshot["verified_at"],
        "disclaimer": "Results come from reviewed public marketplace pages; benchmark suggestions are independently labeled." if verified else "No reviewed listing matched. Suggestions below come from the bundled benchmark catalog, not live marketplaces.",
    }
