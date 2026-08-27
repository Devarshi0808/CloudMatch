"""Official cloud marketplace adapters with normalized provenance metadata."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
import time
import urllib.parse
import urllib.request

PROVIDER_NAMES = {"aws": "AWS Marketplace", "azure": "Microsoft Azure Marketplace", "gcp": "Google Cloud Marketplace"}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _result(provider, status, listings=None, started=None, error=None, detail=None):
    response = {"provider": provider, "provider_name": PROVIDER_NAMES[provider], "status": status, "listings": listings or [], "duration_ms": round((time.perf_counter() - started) * 1000, 2) if started else 0}
    if error:
        response["error"] = str(error)[:240]
    if detail:
        response["detail"] = detail
    return response


def normalize_aws_listing(item):
    """Normalize one SearchListings summary from AWS Marketplace Discovery."""
    associated = item.get("associatedEntities") or []
    product = next((entry.get("product", {}) for entry in associated if entry.get("product")), {})
    publisher = item.get("publisher") or product.get("manufacturer") or {}
    listing_id = str(item.get("listingId") or item.get("id") or "").strip()
    return {
        "provider": "aws", "provider_name": PROVIDER_NAMES["aws"], "listing_id": listing_id,
        "title": str(item.get("listingName") or product.get("productName") or "").strip(),
        "vendor": str(publisher.get("displayName") or "").strip(),
        "description": str(item.get("shortDescription") or "").strip(),
        "url": f"https://aws.amazon.com/marketplace/pp/prodview-{listing_id}" if listing_id else "https://aws.amazon.com/marketplace",
        "source": "aws_marketplace_discovery_api", "verification": "official_api", "retrieved_at": _now(),
    }


def ingest_aws(query, limit=10):
    """Search AWS Marketplace through the official, IAM-authenticated Discovery API."""
    started = time.perf_counter()
    if not os.getenv("AWS_ACCESS_KEY_ID") and not os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE"):
        return _result("aws", "not_configured", started=started, detail="AWS IAM credentials are required")
    try:
        import boto3
        client = boto3.client("marketplace-discovery", region_name=os.getenv("AWS_REGION", "us-east-1"))
        payload = client.search_listings(searchText=query, maxResults=min(max(limit, 1), 100), sortBy="RELEVANCE", sortOrder="DESCENDING")
        listings = [normalize_aws_listing(item) for item in payload.get("listingSummaries", [])]
        listings = [item for item in listings if item["title"]]
        return _result("aws", "ok", listings, started, detail=f"{payload.get('totalResults', len(listings))} total matches")
    except Exception as error:
        return _result("aws", "error", started=started, error=error)


def normalize_azure_listing(item):
    """Normalize one Azure Marketplace Catalog search result."""
    product_id = str(item.get("uniqueProductId") or item.get("productId") or "").strip()
    return {
        "provider": "azure", "provider_name": PROVIDER_NAMES["azure"], "listing_id": product_id,
        "title": str(item.get("displayName") or item.get("title") or "").strip(),
        "vendor": str(item.get("publisherDisplayName") or item.get("publisherId") or "").strip(),
        "description": str(item.get("summary") or item.get("description") or "").strip(),
        "url": f"https://azuremarketplace.microsoft.com/en-us/marketplace/apps/{urllib.parse.quote(product_id, safe='.-_')}" if product_id else "https://azuremarketplace.microsoft.com/",
        "source": "azure_marketplace_catalog_api", "verification": "official_api", "retrieved_at": _now(),
    }


def ingest_azure(query, limit=10):
    """Search the official Azure Marketplace Catalog data-plane API."""
    started = time.perf_counter()
    api_key = os.getenv("AZURE_MARKETPLACE_CATALOG_API_KEY")
    if not api_key:
        return _result("azure", "not_configured", started=started, detail="Azure Marketplace Catalog API key is required")
    params = urllib.parse.urlencode({
        "api-version": "2025-05-01", "language": "en", "market": os.getenv("AZURE_MARKETPLACE_MARKET", "US"),
        "publishingStage": "Public", "publisherTypes": "Microsoft,ThirdParty", "searchQuery": query,
        "top": min(max(limit, 1), 100),
        "select": "DisplayName,PublisherId,PublisherDisplayName,UniqueProductId,ProductType,Summary,Description,RatingAverage,RatingCount",
    })
    request = urllib.request.Request(f"https://catalogapi.azure.com/search?{params}", headers={"X-API-Key": api_key, "Accept": "application/json", "User-Agent": "CloudMatch/2.0"})
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
        raw = payload.get("results") or payload.get("value") or []
        listings = [normalize_azure_listing(item) for item in raw]
        listings = [item for item in listings if item["title"]]
        return _result("azure", "ok", listings, started, detail=f"{payload.get('totalCount', len(listings))} total matches")
    except Exception as error:
        return _result("azure", "error", started=started, error=error)


def ingest_gcp(_query, _limit=10):
    return _result("gcp", "link_only", detail="No supported public Google Cloud Marketplace catalog-search API; use the provider search page")


def ingest_configured_listings(query="", limit=10):
    query = " ".join(str(query or "").split())[:512]
    if not query:
        providers = {name: _result(name, "skipped", detail="A non-empty query is required") for name in PROVIDER_NAMES}
        return {"query": "", "listings": [], "providers": providers, "source": "official_provider_apis"}
    adapters = {"aws": ingest_aws, "azure": ingest_azure, "gcp": ingest_gcp}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {name: executor.submit(adapter, query, limit) for name, adapter in adapters.items()}
        providers = {name: future.result() for name, future in futures.items()}
    listings = [listing for provider in providers.values() for listing in provider["listings"]]
    return {"query": query, "listings": listings, "providers": providers, "source": "official_provider_apis"}
