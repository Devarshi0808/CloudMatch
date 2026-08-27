"""Grounded research briefs designed for AI agents and human inspection."""
import re
try:
    from .evidence_store import PROVIDER_ALIASES, load_evidence, search_evidence
except ImportError:
    from evidence_store import PROVIDER_ALIASES, load_evidence, search_evidence

def parse_request(request):
    text = " ".join(str(request or "").split())[:600]; lowered = text.lower()
    provider = next((value for alias, value in PROVIDER_ALIASES.items() if re.search(rf"\b{alias}\b", lowered)), "")
    compare = any(word in lowered for word in ("compare", "versus", " vs ", "alternatives"))
    return {"query": text, "provider": provider, "intent": "compare" if compare else "discover"}

def research_products(request, limit=5):
    parsed = parse_request(request); matches = search_evidence(parsed["query"], parsed["provider"], limit)
    confident = [item for item in matches if item["score"] >= 35 and item["query_coverage"] >= 0.75]
    if not confident:
        return {"request": parsed, "status":"abstained", "confidence":0.0, "answer":"I could not ground this request in the reviewed listing snapshot.", "evidence":[], "caveats":["Try a vendor, product, capability, or provider present in the evidence set."], "snapshot_verified_at":load_evidence()["verified_at"]}
    top = confident[0]; confidence = min(0.99, top["score"] / 100)
    answer = f"Found {len(confident)} grounded candidate{'s' if len(confident) != 1 else ''}. Best match: {top['title']} by {top['vendor']} on {top['provider'].upper()}."
    return {"request":parsed, "status":"grounded", "confidence":round(confidence, 2), "answer":answer, "evidence":[{"id":item["id"],"title":item["title"],"provider":item["provider"],"vendor":item["vendor"],"url":item["url"],"score":item["score"],"matched_terms":item["matched_terms"],"why":item["description"]} for item in confident], "caveats":["Evidence is a reviewed snapshot, not a complete or real-time marketplace inventory."], "snapshot_verified_at":load_evidence()["verified_at"]}

def compare_products(request, limit=5):
    result = research_products(request, limit)
    if result["status"] == "grounded" and len(result["evidence"]) < 2:
        result["caveats"].append("Only one sufficiently grounded candidate was found; comparison is incomplete.")
    result["comparison"] = [{"id":item["id"], "provider":item["provider"], "vendor":item["vendor"], "fit_score":item["score"]} for item in result["evidence"]]
    return result
