"""Hybrid marketplace retrieval with explicit source boundaries."""

import urllib.parse

try:
    from .catalog_matcher import search_catalog
    from .provider_ingestion import ingest_configured_listings
except ImportError:
    from catalog_matcher import search_catalog
    from provider_ingestion import ingest_configured_listings

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
    ingestion = ingest_configured_listings(query, limit)
    benchmark = search_catalog(vendor, solution, limit=limit)
    configured = sum(result["status"] == "ok" for result in ingestion["providers"].values())
    return {
        "query": query, "matches": ingestion["listings"], "catalog_matches": benchmark["matches"],
        "catalog_size": benchmark["catalog_size"], "provider_links": provider_links(query), "providers": ingestion["providers"],
        "source": "official_provider_apis" if ingestion["listings"] else "benchmark_catalog",
        "retrieval": {"official_adapters_configured": configured, "official_results": len(ingestion["listings"]), "benchmark_results": len(benchmark["matches"])},
        "disclaimer": "Official provider API results are shown first; benchmark suggestions are independently labeled." if ingestion["listings"] else "No official provider API returned results. Suggestions below come from the bundled benchmark catalog, not live marketplaces.",
    }
