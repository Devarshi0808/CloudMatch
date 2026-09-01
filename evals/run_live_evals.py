#!/usr/bin/env python3
"""Run a small labeled online evaluation set against current marketplace search."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from time import perf_counter, sleep

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
    return all(term.lower() in text or term.lower() in matched for term in expected_terms)


def evaluate_case(case):
    started = perf_counter()
    result = search_live_marketplaces(case["query"], case["provider"], limit=5)
    latency_ms = round((perf_counter() - started) * 1000)
    matches = result["matches"]
    provider_status = result["providers"][case["provider"]]["status"]
    provider_available = provider_status == "ok"
    titles = [_normalized_title(item["title"]) for item in matches]
    checks = {
        "provider_available": provider_available,
        "expected_result_state": bool(matches) is bool(case["expect_results"]),
        "official_domain_rate": all(_valid_url(item["url"], case["provider"]) for item in matches),
        "duplicate_rate_zero": len(titles) == len(set(titles)),
        "snippets_bounded": all(len(item["description"]) <= 360 for item in matches),
        "relevant_top_result": not case["expect_results"] or (bool(matches) and relevant(matches[0], case["expected_all"])),
    }
    return {
        "id": case["id"],
        "query": case["query"],
        "provider": case["provider"],
        "passed": all(checks.values()),
        "provider_available": provider_available,
        "provider_status": provider_status,
        "provider_detail": result["providers"][case["provider"]].get("detail"),
        "quality_passed": checks["official_domain_rate"] and checks["duplicate_rate_zero"] and checks["snippets_bounded"],
        "checks": checks,
        "result_count": len(matches),
        "filtered_count": result.get("filtered_count", 0),
        "duplicate_count": result.get("duplicate_count", 0),
        "latency_ms": latency_ms,
        "provider_response_time": result.get("response_time"),
        "search_depth": result.get("search_depth"),
        "estimated_credits": result.get("estimated_credits"),
        "top_title": matches[0]["title"] if matches else None,
    }


def main():
    load_local_env()
    if not os.getenv("TAVILY_API_KEY"):
        raise SystemExit("TAVILY_API_KEY is required; no evaluation fallback is available")
    cases = json.loads((ROOT / "evals" / "live_cases.json").read_text())
    delay_seconds = max(0.0, float(os.getenv("CLOUDMATCH_EVAL_DELAY_SECONDS", "0.65")))
    results = []
    for index, case in enumerate(cases):
        if index:
            sleep(delay_seconds)
        results.append(evaluate_case(case))
    passed = sum(result["passed"] for result in results)
    positives = [result for result, case in zip(results, cases) if case["expect_results"]]
    negatives = [result for result, case in zip(results, cases) if not case["expect_results"]]
    quality_passed = sum(result["quality_passed"] for result in results)
    positive_passed = sum(result["passed"] for result in positives)
    negative_passed = sum(result["passed"] for result in negatives)
    available_positives = [result for result in positives if result["provider_available"]]
    provider_metrics = {}
    for provider in sorted({case["provider"] for case in cases}):
        provider_positives = [
            result for result, case in zip(results, cases)
            if case["provider"] == provider and case["expect_results"]
        ]
        provider_metrics[provider] = {
            "positive_cases": len(provider_positives),
            "available_cases": sum(result["provider_available"] for result in provider_positives),
            "positive_passed": sum(result["passed"] for result in provider_positives),
            "positive_retrieval_rate": round(
                sum(result["passed"] for result in provider_positives) / len(provider_positives), 4
            ),
            "conditional_recall_rate": round(
                sum(result["passed"] for result in provider_positives if result["provider_available"])
                / max(sum(result["provider_available"] for result in provider_positives), 1), 4
            ),
        }
    failed_cases = [
        {"id": result["id"], "provider_status": result["provider_status"], "failed_checks": [key for key, passed in result["checks"].items() if not passed]}
        for result in results if not result["passed"]
    ]
    report = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "suite": "live_official_marketplace_v2",
        "case_count": len(results),
        "inter_case_delay_seconds": delay_seconds,
        "passed": passed,
        "pass_rate": round(passed / len(results), 4),
        "metrics": {
            "official_quality_gate_rate": round(quality_passed / len(results), 4),
            "positive_retrieval_rate": round(positive_passed / len(positives), 4),
            "conditional_recall_rate": round(
                sum(result["passed"] for result in available_positives) / max(len(available_positives), 1), 4
            ),
            "provider_availability_rate": round(sum(result["provider_available"] for result in results) / len(results), 4),
            "negative_abstention_rate": round(negative_passed / len(negatives), 4),
            "estimated_credits": sum(result["estimated_credits"] or 0 for result in results),
            "mean_latency_ms": round(sum(result["latency_ms"] for result in results) / len(results)),
            "p95_latency_ms": sorted(result["latency_ms"] for result in results)[max(0, round(len(results) * 0.95) - 1)],
            "provider_positive_retrieval": provider_metrics,
        },
        "failed_cases": failed_cases,
        "results": results,
    }
    print(json.dumps(report, indent=2))
    targets_met = quality_passed == len(results) and negative_passed == len(negatives) and positive_passed / len(positives) >= 0.75
    return 0 if targets_met else 1


if __name__ == "__main__":
    raise SystemExit(main())
