"""Evaluate top-k catalog retrieval on positive and abstention cases."""
import json
from pathlib import Path
from api.catalog_matcher import search_catalog
GOLDEN_SET = Path(__file__).with_name("golden_queries.json")

def evaluate():
    cases = json.loads(GOLDEN_SET.read_text()); top1 = top3 = positives = negatives = abstentions = 0; reciprocal_ranks = []; failures = []
    for case in cases:
        ranked = search_catalog(case.get("vendor", ""), case.get("solution", ""), limit=8)["matches"]
        if case.get("expected") is None:
            negatives += 1
            if not ranked: abstentions += 1
            else: failures.append({"query": case, "reason": "expected abstention", "top": ranked[0]})
            continue
        positives += 1; target = tuple(value.lower() for value in case["expected"])
        rank = next((i + 1 for i, item in enumerate(ranked) if (item["vendor"].lower(), item["solution"].lower()) == target), None)
        top1 += rank == 1; top3 += bool(rank and rank <= 3); reciprocal_ranks.append(1 / rank if rank else 0.0)
        if rank != 1: failures.append({"query": case, "reason": f"target rank {rank}", "top": ranked[0] if ranked else None})
    total = len(cases)
    return {"cases": total, "positive_cases": positives, "negative_cases": negatives, "precision_at_1": round(top1 / positives, 3) if positives else 0.0, "recall_at_3": round(top3 / positives, 3) if positives else 0.0, "mrr_at_8": round(sum(reciprocal_ranks) / positives, 3) if positives else 0.0, "abstention_accuracy": round(abstentions / negatives, 3) if negatives else 0.0, "overall_accuracy": round((top1 + abstentions) / total, 3) if total else 0.0, "failures": failures}

if __name__ == "__main__": print(json.dumps(evaluate(), indent=2))
