"""Zero-cost evidence retrieval over reviewed marketplace listing snapshots."""
from functools import lru_cache
import json, math, re
from pathlib import Path

STORE = Path(__file__).parent.parent / "data" / "verified_listings.json"
PROVIDER_ALIASES = {"aws":"aws", "amazon":"aws", "azure":"azure", "microsoft":"azure", "gcp":"gcp", "google":"gcp"}
STOPWORDS = {"a", "alternatives", "an", "and", "are", "compare", "for", "find", "i", "in", "is", "me", "need", "of", "on", "or", "product", "products", "show", "solution", "the", "to", "with"}

def tokens(value): return [term for term in re.findall(r"[a-z0-9]+", str(value or "").lower()) if term not in STOPWORDS]

@lru_cache(maxsize=1)
def load_evidence(): return json.loads(STORE.read_text())

def _document(item): return " ".join([item["title"], item["vendor"], item["description"], " ".join(item["categories"]), item["delivery"], item["provider"]])

def search_evidence(query, provider="", limit=8):
    query_tokens = tokens(query); records = load_evidence()["listings"]
    provider = PROVIDER_ALIASES.get(str(provider).lower(), str(provider).lower())
    if provider: records = [item for item in records if item["provider"] == provider]
    if not query_tokens: return []
    document_tokens = [tokens(_document(item)) for item in records]; total = max(len(records), 1)
    frequencies = {term: sum(term in doc for doc in document_tokens) for term in set(query_tokens)}
    ranked = []
    for item, doc in zip(records, document_tokens):
        tfidf = sum((doc.count(term) / max(len(doc), 1)) * (math.log((total + 1) / (frequencies[term] + 1)) + 1) for term in query_tokens)
        coverage = len(set(query_tokens) & set(doc)) / len(set(query_tokens))
        phrase = 1.0 if " ".join(query_tokens) in " ".join(doc) else 0.0
        score = min(100.0, coverage * 65 + phrase * 20 + tfidf * 160)
        if score >= 18:
            matched = sorted(set(query_tokens) & set(doc))
            result = dict(item); result.update({"score": round(score, 1), "matched_terms": matched, "query_coverage": round(len(matched) / len(set(query_tokens)), 2), "source":"verified_snapshot", "verification":"reviewed_public_listing"}); ranked.append(result)
    return sorted(ranked, key=lambda item: (-item["score"], item["title"]))[:limit]

def get_evidence(evidence_id):
    return next((dict(item) for item in load_evidence()["listings"] if item["id"] == evidence_id), None)
