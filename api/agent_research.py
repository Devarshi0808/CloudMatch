"""Grounded research briefs over live marketplace web results."""
import re
try:
    from .live_search import detect_provider, search_live_marketplaces
    from .open_search import provider_links
except ImportError:
    from live_search import detect_provider, search_live_marketplaces
    from open_search import provider_links

def parse_request(request):
    text=" ".join(str(request or "").split())[:600]; lowered=text.lower()
    compare=any(word in lowered for word in ("compare", "versus", " vs ", "alternatives"))
    provider=detect_provider(text)
    stop={"find","show","search","me","for","on","in","the","a","an","products","product","solutions","solution","marketplace","compare","alternatives","aws","amazon","azure","microsoft","gcp","google","cloud"}
    terms=[term for term in re.findall(r"[a-zA-Z0-9+#.-]+", text) if term.lower() not in stop]
    if any(term.lower() == "ansible" for term in terms) and not any(term.lower() == "automation" for term in terms): terms.extend(["Automation", "Platform"])
    search_query=" ".join(terms) or text
    return {"query":text,"search_query":search_query,"provider":provider,"intent":"compare" if compare else "discover"}

def research_products(request, limit=5):
    parsed=parse_request(request); live=search_live_marketplaces(parsed["search_query"], parsed["provider"], limit)
    if not live["matches"]:
        return {"request":parsed,"status":"abstained","confidence":0.0,"answer":"No sufficiently relevant listing could be verified from live official-domain search.","evidence":[],"providers":live["providers"],"provider_links":provider_links(parsed["search_query"]),"retrieved_at":live["retrieved_at"],"quality":{"filtered_count":live.get("filtered_count",0),"duplicate_count":live.get("duplicate_count",0),"result_count":0,"search_depth":live.get("search_depth","basic"),"estimated_credits":live.get("estimated_credits",1)},"caveats":[live["disclaimer"]]}
    evidence=[{"id":item["id"],"title":item["title"],"provider":item["provider"],"url":item["url"],"description":item["description"],"relevance_score":item["relevance_score"],"match_score":item.get("match_score",item["rank_score"]),"rank_score":item["rank_score"],"matched_terms":item.get("matched_terms",[]),"query_coverage":item.get("query_coverage",0),"verification":item["verification"],"retrieved_at":item["retrieved_at"]} for item in live["matches"]]
    top=evidence[0]
    confidence=round(max(0.0, min(0.99, top["match_score"])), 2)
    return {"request":parsed,"status":"grounded","confidence":confidence,"answer":f"Found {len(evidence)} distinct, relevant official-domain result{'s' if len(evidence)!=1 else ''}. Best match: {top['title']} on {top['provider'].upper()}.","evidence":evidence,"providers":live["providers"],"provider_links":provider_links(parsed["search_query"]),"retrieved_at":live["retrieved_at"],"quality":{"filtered_count":live.get("filtered_count",0),"duplicate_count":live.get("duplicate_count",0),"result_count":len(evidence),"search_depth":live.get("search_depth","basic"),"estimated_credits":live.get("estimated_credits",1)},"caveats":[live["disclaimer"]]}

def compare_products(request, limit=5):
    result=research_products(request, limit)
    result["comparison"]=[{"id":item["id"],"provider":item["provider"],"title":item["title"],"url":item["url"]} for item in result["evidence"]]
    if len(result["comparison"]) < 2: result["caveats"].append("Fewer than two live verified results were available, so comparison is incomplete.")
    return result
