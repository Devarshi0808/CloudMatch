"""Run the small golden-set evaluation for CloudMatch retrieval."""

import json
from pathlib import Path

from api.catalog_matcher import search_catalog


GOLDEN_SET = Path(__file__).with_name("golden_queries.json")


def evaluate():
    cases = json.loads(GOLDEN_SET.read_text())
    reciprocal_ranks = []
    hits = 0

    for case in cases:
        result = search_catalog(case["vendor"], case["solution"], limit=8)
        ranked = result["matches"]
        target = (case["expected_vendor"].lower(), case["expected_solution"].lower())
        rank = next((index + 1 for index, item in enumerate(ranked) if (item["vendor"].lower(), item["solution"].lower()) == target), None)
        if rank:
            hits += 1
            reciprocal_ranks.append(1 / rank)
        else:
            reciprocal_ranks.append(0.0)

    total = len(cases)
    precision_at_1 = hits / total if total else 0.0
    recall_at_1 = precision_at_1
    f1_at_1 = (2 * precision_at_1 * recall_at_1 / (precision_at_1 + recall_at_1)) if precision_at_1 + recall_at_1 else 0.0
    return {
        "cases": total,
        "precision_at_1": round(precision_at_1, 3),
        "recall_at_1": round(recall_at_1, 3),
        "f1": round(f1_at_1, 3),
        "mrr_at_8": round(sum(reciprocal_ranks) / total, 3) if total else 0.0,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
