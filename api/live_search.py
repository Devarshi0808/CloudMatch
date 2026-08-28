"""Live Tavily retrieval with official-domain validation and quality controls."""

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
import re
import urllib.parse
import urllib.request


PROVIDERS = {
    "aws": {"name": "AWS Marketplace", "domain": "aws.amazon.com", "path": "/marketplace/pp/"},
    "azure": {"name": "Microsoft Azure Marketplace", "domain": "azuremarketplace.microsoft.com", "path": "/marketplace/apps/"},
    "gcp": {"name": "Google Cloud Marketplace", "domain": "console.cloud.google.com", "path": "/marketplace/product/"},
}
ALIASES = {"aws": "aws", "amazon": "aws", "azure": "azure", "microsoft": "azure", "gcp": "gcp", "google": "gcp"}
GENERIC_QUERY_TERMS = {
    "app", "apps", "cloud", "enterprise", "find", "marketplace", "platform",
    "product", "products", "service", "services", "solution", "solutions",
}
TRACKING_QUERY_KEYS = {"ocid", "ref", "source", "tab", "utm_campaign", "utm_content", "utm_medium", "utm_source", "utm_term"}


def _valid_url(url, provider):
    parsed = urllib.parse.urlparse(url)
    rule = PROVIDERS[provider]
    return parsed.scheme == "https" and parsed.hostname == rule["domain"] and rule["path"] in parsed.path


def _provider_for_url(url):
    return next((provider for provider in PROVIDERS if _valid_url(url, provider)), "")


def detect_provider(text):
    lowered = str(text or "").lower()
    return next((value for alias, value in ALIASES.items() if re.search(rf"\b{alias}\b", lowered)), "")


def _tokens(value):
    return re.findall(r"[a-z0-9]+", str(value or "").lower())


def _specific_terms(query):
    unique = list(dict.fromkeys(_tokens(query)))
    specific = [term for term in unique if term not in GENERIC_QUERY_TERMS and len(term) > 1]
    return specific or unique


def _canonical_url(url):
    parsed = urllib.parse.urlparse(url)
    kept_query = [
        (key, value)
        for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        if key.lower() not in TRACKING_QUERY_KEYS
    ]
    clean_path = re.sub(r"/{2,}", "/", parsed.path).rstrip("/")
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc.lower(), clean_path, "", urllib.parse.urlencode(kept_query), ""))


def _normalized_title(title):
    value = " ".join(str(title or "").split()).lower()
    value = re.sub(r"^(aws|azure|google cloud|microsoft) marketplace\s*:\s*", "", value)
    value = value.replace("®", "").replace("™", "")
    return " ".join(_tokens(value))


def _summarize_content(content, max_chars=360):
    value = str(content or "")
    value = re.sub(r"[#*_`>|]+", " ", value)
    value = re.sub(r"https?://\S+", "", value)
    value = re.sub(r"\b(?:email|phone|website)\s*:\s*\S+", "", value, flags=re.IGNORECASE)
    value = " ".join(value.split())
    if len(value) <= max_chars:
        return value
    clipped = value[: max_chars + 1]
    sentence_end = max(clipped.rfind(". "), clipped.rfind("! "), clipped.rfind("? "))
    if sentence_end >= int(max_chars * 0.55):
        return clipped[: sentence_end + 1]
    word_end = clipped.rfind(" ", 0, max_chars)
    return clipped[:word_end].rstrip(" ,;:-") + "…"


def _quality_features(raw, query):
    title = str(raw.get("title") or "")
    url_path = urllib.parse.unquote(urllib.parse.urlparse(str(raw.get("url") or "")).path)
    content = str(raw.get("content") or "")
    title_url_tokens = set(_tokens(title + " " + url_path))
    all_tokens = title_url_tokens | set(_tokens(content))
    title_url_compact = "".join(title_url_tokens)
    all_compact = "".join(all_tokens)
    terms = _specific_terms(query)
    title_matches = [term for term in terms if term in title_url_tokens or (len(term) >= 3 and term in title_url_compact)]
    all_matches = [term for term in terms if term in all_tokens or (len(term) >= 3 and term in all_compact)]
    normalized_query = " ".join(_tokens(query))
    normalized_title_url = " ".join(_tokens(title + " " + url_path))
    return {
        "specific_terms": terms,
        "matched_terms": all_matches,
        "title_url_coverage": len(title_matches) / max(len(terms), 1),
        "query_coverage": len(all_matches) / max(len(terms), 1),
        "exact_phrase": bool(normalized_query and normalized_query in normalized_title_url),
    }


def _passes_quality(raw, features):
    tavily_score = float(raw.get("score") or 0)
    term_count = len(features["specific_terms"])
    if tavily_score < 0.25 or not features["matched_terms"]:
        return False
    if term_count == 1:
        return features["title_url_coverage"] == 1
    if term_count == 2:
        return features["title_url_coverage"] >= 0.5 and features["query_coverage"] == 1
    return features["exact_phrase"] or features["title_url_coverage"] >= 0.75


def _rank_score(raw, features):
    tavily_score = max(0.0, min(1.0, float(raw.get("score") or 0)))
    score = tavily_score * 0.50 + features["title_url_coverage"] * 0.35 + features["query_coverage"] * 0.15
    if features["exact_phrase"]:
        score += 0.05
    return round(min(score, 1.0), 4)


def _display_title(raw):
    title = " ".join(str(raw.get("title") or "").split())
    generic = _normalized_title(title) in {
        "cloud solutions ai apps and agents", "google cloud console", "marketplace",
        "marketplace google cloud console", "microsoft marketplace cloud solutions ai apps and agents",
    }
    if title and not generic:
        return title
    slug = urllib.parse.unquote(urllib.parse.urlparse(str(raw.get("url") or "")).path.rstrip("/").split("/")[-1])
    if "." in slug:
        slug = slug.split(".", 1)[1]
    derived = " ".join(part.capitalize() for part in re.split(r"[-_]+", slug) if part)
    return derived or "Official marketplace listing"


def _call_tavily(query, domains, limit, api_key):
    body = json.dumps({
        "query": query,
        "search_depth": "basic",
        "max_results": min(max(limit, 1), 20),
        "include_domains": domains,
        "include_answer": False,
        "include_raw_content": False,
        "auto_parameters": False,
        "safe_search": True,
    }).encode()
    request = urllib.request.Request(
        "https://api.tavily.com/search",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "CloudMatch/4.1"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode())


def search_live_marketplaces(query, provider="", limit=5):
    query = " ".join(str(query or "").split())[:300]
    selected = [provider] if provider in PROVIDERS else list(PROVIDERS)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    statuses = {key: {"status": "pending", "result_count": 0, "detail": "Awaiting live search"} for key in selected}
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        for key in selected:
            statuses[key] = {"status": "not_configured", "result_count": 0, "detail": "TAVILY_API_KEY is required for live search"}
        return {"query": query, "matches": [], "providers": statuses, "source": "tavily_live_search", "retrieved_at": retrieved_at, "filtered_count": 0, "duplicate_count": 0, "disclaimer": "Live Tavily search is not configured; no local fallback was used."}
    try:
        requested_results = min(max(limit * 3, 10), 20)
        payload = _call_tavily(query, [PROVIDERS[key]["domain"] for key in selected], requested_results, api_key)
        candidates = []
        filtered_count = 0
        for raw in payload.get("results", []):
            url = _canonical_url(raw.get("url", ""))
            found_provider = _provider_for_url(url)
            if found_provider not in selected:
                filtered_count += 1
                continue
            normalized_raw = dict(raw, url=url)
            features = _quality_features(normalized_raw, query)
            if not _passes_quality(normalized_raw, features):
                filtered_count += 1
                continue
            title = _display_title(normalized_raw)
            score = _rank_score(normalized_raw, features)
            candidates.append({
                "id": "live-" + sha256(url.encode()).hexdigest()[:16],
                "provider": found_provider,
                "provider_name": PROVIDERS[found_provider]["name"],
                "title": title,
                "description": _summarize_content(raw.get("content") or ""),
                "relevance_score": round(float(raw.get("score") or 0), 4),
                "match_score": score,
                "rank_score": score,
                "matched_terms": features["matched_terms"],
                "query_coverage": round(features["query_coverage"], 4),
                "url": url,
                "source": "tavily_live_search",
                "verification": "official_domain",
                "retrieved_at": retrieved_at,
                "_dedupe_key": found_provider + ":" + _normalized_title(title),
            })

        candidates.sort(key=lambda item: (-item["rank_score"], -item["relevance_score"], item["title"]))
        matches = []
        seen_keys = set()
        duplicate_count = 0
        for candidate in candidates:
            if candidate["_dedupe_key"] in seen_keys:
                duplicate_count += 1
                continue
            seen_keys.add(candidate["_dedupe_key"])
            candidate.pop("_dedupe_key", None)
            matches.append(candidate)

        matches = matches[:limit]
        for key in selected:
            count = sum(item["provider"] == key for item in matches)
            statuses[key] = {"status": "ok", "result_count": count, "detail": "Tavily live search completed"}
        return {
            "query": query,
            "matches": matches,
            "providers": statuses,
            "source": "tavily_live_search",
            "retrieved_at": retrieved_at,
            "response_time": payload.get("response_time"),
            "filtered_count": filtered_count,
            "duplicate_count": duplicate_count,
            "disclaimer": "Live results are restricted to relevant official marketplace listings; low-quality and duplicate results are removed.",
        }
    except Exception as error:
        for key in selected:
            statuses[key] = {"status": "unavailable", "result_count": 0, "detail": str(error)[:140]}
        return {"query": query, "matches": [], "providers": statuses, "source": "tavily_live_search", "retrieved_at": retrieved_at, "filtered_count": 0, "duplicate_count": 0, "disclaimer": "Live search was unavailable; no local fallback was used."}
