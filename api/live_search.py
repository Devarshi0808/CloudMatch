"""Live Tavily search restricted to official marketplace domains."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
import re
import urllib.parse
import urllib.request

PROVIDERS = {
    "aws": {"name":"AWS Marketplace", "domain":"aws.amazon.com", "path":"/marketplace/pp/"},
    "azure": {"name":"Microsoft Azure Marketplace", "domain":"azuremarketplace.microsoft.com", "path":"/marketplace/apps/"},
    "gcp": {"name":"Google Cloud Marketplace", "domain":"console.cloud.google.com", "path":"/marketplace/product/"},
}
ALIASES = {"aws":"aws", "amazon":"aws", "azure":"azure", "microsoft":"azure", "gcp":"gcp", "google":"gcp"}

def _valid_url(url, provider):
    parsed=urllib.parse.urlparse(url); rule=PROVIDERS[provider]
    return parsed.scheme == "https" and parsed.hostname == rule["domain"] and rule["path"] in parsed.path

def _provider_for_url(url):
    return next((provider for provider in PROVIDERS if _valid_url(url, provider)), "")

def detect_provider(text):
    lowered=str(text or "").lower()
    return next((value for alias,value in ALIASES.items() if re.search(rf"\b{alias}\b", lowered)), "")

def _rank_score(raw, query):
    tavily=float(raw.get("score") or 0); title=str(raw.get("title") or "").lower(); url=str(raw.get("url") or "").lower()
    terms=set(re.findall(r"[a-z0-9]+", query.lower())); compact=(title+" "+url).replace("-", "").replace("_", "")
    coverage=sum(term in compact for term in terms) / max(len(terms), 1)
    phrase_bonus=0.12 if query.lower() in title else 0
    product_bonus=0.08 if any(marker in url for marker in ("/prodview-", "/marketplace/apps/", "/marketplace/product/")) else 0
    return round(tavily + coverage * 0.45 + phrase_bonus + product_bonus, 4)

def _call_tavily(query, domains, limit, api_key):
    body=json.dumps({"query":query,"search_depth":"basic","max_results":min(max(limit,1),20),"include_domains":domains,"include_answer":False,"include_raw_content":False,"auto_parameters":False,"safe_search":True}).encode()
    request=urllib.request.Request("https://api.tavily.com/search", data=body, headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json","User-Agent":"CloudMatch/4.0"})
    with urllib.request.urlopen(request, timeout=20) as response: return json.loads(response.read().decode())

def search_live_marketplaces(query, provider="", limit=5):
    query=" ".join(str(query or "").split())[:300]; selected=[provider] if provider in PROVIDERS else list(PROVIDERS)
    retrieved_at=datetime.now(timezone.utc).isoformat(); statuses={key:{"status":"pending","result_count":0,"detail":"Awaiting live search"} for key in selected}
    api_key=os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        for key in selected: statuses[key]={"status":"not_configured","result_count":0,"detail":"TAVILY_API_KEY is required for live search"}
        return {"query":query,"matches":[],"providers":statuses,"source":"tavily_live_search","retrieved_at":retrieved_at,"disclaimer":"Live Tavily search is not configured; no local fallback was used."}
    try:
        payload=_call_tavily(query, [PROVIDERS[key]["domain"] for key in selected], limit, api_key)
        raw_results=payload.get("results", [])
        matches=[]; seen=set()
        for raw in raw_results:
            url=raw.get("url", ""); found_provider=_provider_for_url(url)
            if found_provider not in selected or url in seen: continue
            seen.add(url); matches.append({"id":"live-"+sha256(url.encode()).hexdigest()[:16],"provider":found_provider,"provider_name":PROVIDERS[found_provider]["name"],"title":" ".join(str(raw.get("title") or "Untitled listing").split()),"description":" ".join(str(raw.get("content") or "").split()),"relevance_score":round(float(raw.get("score") or 0),4),"rank_score":_rank_score(raw, query),"url":url,"source":"tavily_live_search","verification":"official_domain","retrieved_at":retrieved_at})
        matches.sort(key=lambda item:(-item["rank_score"], -item["relevance_score"], item["title"]))
        for key in selected:
            count=sum(item["provider"] == key for item in matches)
            statuses[key]={"status":"ok","result_count":count,"detail":"Tavily live search completed"}
        return {"query":query,"matches":matches[:limit],"providers":statuses,"source":"tavily_live_search","retrieved_at":retrieved_at,"response_time":payload.get("response_time"),"disclaimer":"Live results are restricted to official marketplace domains; coverage depends on current public web indexing."}
    except Exception as error:
        for key in selected: statuses[key]={"status":"unavailable","result_count":0,"detail":str(error)[:140]}
        return {"query":query,"matches":[],"providers":statuses,"source":"tavily_live_search","retrieved_at":retrieved_at,"disclaimer":"Live search was unavailable; no local fallback was used."}
