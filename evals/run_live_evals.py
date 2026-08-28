#!/usr/bin/env python3
"""Run a small labeled online evaluation set against current marketplace search."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.live_search import _normalized_title, _valid_url, search_live_marketplaces  # noqa: E402


def load_local_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def relevant(match, expected_terms):
    text = f"{match['title']} {match['url']}".lower()
    matched = {term.lower() for term in match.get("matched_terms", [])}
    return any(term.lower() in text or term.lower() in matched for term in expected_terms)


def evaluate_case(case):
    result = search_live_marketplaces(case["query"], case["provider"], limit=5)
    matches = result["matches"]
    titles = [_normalized_title(item["title"]) for item in matches]
    checks = {
        "expected_result_state": bool(matches) is bool(case["expect_results"]),
        "official_domain_rate": all(_valid_url(item["url"], case["provider"]) for item in matches),
        "duplicate_rate_zero": len(titles) == len(set(titles)),
        "snippets_bounded": all(len(item["description"]) <= 360 for item in matches),
        "relevant_top_result": not case["expect_results"] or (bool(matches) and relevant(matches[0], case["expected_any"])),
    }
    return {
        "id": case["id"],
        "query": case["query"],
        "provider": case["provider"],
        "passed": all(checks.values()),
        "quality_passed": checks["official_domain_rate"] and checks["duplicate_rate_zero"] and checks["snippets_bounded"],
        "checks": checks,
        "result_count": len(matches),
        "filtered_count": result.get("filtered_count", 0),
        "duplicate_count": result.get("duplicate_count", 0),
        "top_title": matches[0]["title"] if matches else None,
    }


def main():
    load_local_env()
    if not os.getenv("TAVILY_API_KEY"):
        raise SystemExit("TAVILY_API_KEY is required; no evaluation fallback is available")
    cases = json.loads((ROOT / "evals" / "live_cases.json").read_text())
    results = [evaluate_case(case) for case in cases]
    passed = sum(result["passed"] for result in results)
    positives = [result for result, case in zip(results, cases) if case["expect_results"]]
    negatives = [result for result, case in zip(results, cases) if not case["expect_results"]]
    quality_passed = sum(result["quality_passed"] for result in results)
    positive_passed = sum(result["passed"] for result in positives)
    negative_passed = sum(result["passed"] for result in negatives)
    report = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "suite": "live_official_marketplace_v1",
        "case_count": len(results),
        "passed": passed,
        "pass_rate": round(passed / len(results), 4),
        "metrics": {
            "official_quality_gate_rate": round(quality_passed / len(results), 4),
            "positive_retrieval_rate": round(positive_passed / len(positives), 4),
            "negative_abstention_rate": round(negative_passed / len(negatives), 4),
        },
        "results": results,
    }
    print(json.dumps(report, indent=2))
    targets_met = quality_passed == len(results) and negative_passed == len(negatives) and positive_passed / len(positives) >= 0.75
    return 0 if targets_met else 1


if __name__ == "__main__":
    raise SystemExit(main())
