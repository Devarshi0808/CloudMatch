"""Live marketplace retrieval with explicit provider status."""
import urllib.parse
try:
    from .live_search import search_live_marketplaces
except ImportError:
    from live_search import search_live_marketplaces

PROVIDER_LINKS={
    "aws":"https://aws.amazon.com/marketplace/search?searchTerms={query}",
    "azure":"https://azuremarketplace.microsoft.com/en-us/marketplace/apps?search={query}",
    "gcp":"https://console.cloud.google.com/marketplace/browse?q={query}",
}

def provider_links(query):
    encoded=urllib.parse.quote_plus(query)
    return {key:{"url":template.format(query=encoded),"source":"provider_search_page"} for key,template in PROVIDER_LINKS.items()}

def search_open_marketplaces(vendor="", solution="", limit=10):
    vendor=" ".join(str(vendor or "").split())[:160]; solution=" ".join(str(solution or "").split())[:160]
    query=" ".join(part for part in (vendor,solution) if part)
    if not query: return {"query":"","matches":[],"providers":{},"provider_links":{},"source":"empty_query","disclaimer":"Enter a vendor, product, or both."}
    result=search_live_marketplaces(query, limit=limit)
    result["provider_links"]=provider_links(query)
    return result
