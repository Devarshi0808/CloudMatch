"""Open marketplace discovery with an optional live web-search provider."""

import json
import os
import urllib.parse
import urllib.request

PROVIDERS = {
    "aws": {"name": "AWS Marketplace", "url": "https://aws.amazon.com/marketplace/search?searchTerms={query}"},
    "azure": {"name": "Microsoft Azure Marketplace", "url": "https://azuremarketplace.microsoft.com/en-us/marketplace/apps?search={query}"},
    "gcp": {"name": "Google Cloud Marketplace", "url": "https://console.cloud.google.com/marketplace/browse?q={query}"},
}


def _provider_links(query):
    encoded = urllib.parse.quote_plus(query)
    return {key: {"provider": value["name"], "url": value["url"].format(query=encoded), "source": "provider_search_page"} for key, value in PROVIDERS.items()}


def _openai_web_search(query):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    payload = json.dumps({
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "tools": [{"type": "web_search_preview"}],
        "input": (
            "Search the open web for real cloud marketplace listings for this query: "
            f"{query}. Return JSON only as {{\"results\":[{{\"provider\":\"AWS|Azure|GCP\","
            "\"title\":\"...\",\"url\":\"https://...\",\"snippet\":\"...\"}}]}}. "
            "Only include pages you actually found. Do not invent listings or URLs."
        ),
    }).encode()
    request = urllib.request.Request("https://api.openai.com/v1/responses", data=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as response:
        body = json.loads(response.read().decode())
    parsed = json.loads(body.get("output_text", "{}"))
    return [{
        "provider": item.get("provider", "Unknown"), "title": item.get("title", "Untitled result"),
        "url": item.get("url", ""), "snippet": item.get("snippet", ""), "source": "open_web_llm_search"
    } for item in parsed.get("results", []) if str(item.get("url", "")).startswith("https://")]


def search_open_marketplaces(vendor="", solution=""):
    query = " ".join(part.strip() for part in (vendor, solution) if part and part.strip())
    links = _provider_links(query) if query else {}
    if not query:
        return {"query": "", "matches": [], "provider_links": {}, "source": "open_web_search"}
    try:
        matches = _openai_web_search(query)
        if matches is not None:
            return {"query": query, "matches": matches, "provider_links": links, "source": "open_web_llm_search", "disclaimer": "Results were retrieved from live web search and should be opened to verify current marketplace availability."}
    except Exception as error:
        return {"query": query, "matches": [], "provider_links": links, "source": "open_web_search_unavailable", "provider_error": str(error), "disclaimer": "Live provider search is unavailable; no catalog fallback was used."}
    return {"query": query, "matches": [], "provider_links": links, "source": "provider_search_page", "disclaimer": "No live search provider is configured; links open provider search pages and no catalog fallback is used."}
