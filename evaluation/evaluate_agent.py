"""Evaluate grounded retrieval, provider constraints, and abstention."""
import json
from pathlib import Path
from api.agent_research import research_products

CASES = Path(__file__).with_name("agent_queries.json")

def evaluate():
    cases = json.loads(CASES.read_text()); correct_status = correct_provider = evidence_hits = grounded = 0; failures = []
    for case in cases:
        result = research_products(case["request"])
        status_ok = result["status"] == case["status"]
        correct_status += status_ok
        if case["status"] == "grounded":
            grounded += 1
            ids = [item["id"] for item in result["evidence"]]
            hit = case["expected_id"] in ids[:5]
            provider_ok = bool(result["evidence"]) and all(item["provider"] == case["provider"] for item in result["evidence"])
            evidence_hits += hit; correct_provider += provider_ok
            if not (status_ok and hit and provider_ok): failures.append({"request":case["request"],"result":result})
        elif not status_ok: failures.append({"request":case["request"],"result":result})
    abstention_cases = len(cases) - grounded
    abstentions = sum(research_products(case["request"])["status"] == "abstained" for case in cases if case["status"] == "abstained")
    return {"cases":len(cases),"grounded_cases":grounded,"abstention_cases":abstention_cases,"status_accuracy":round(correct_status/len(cases),3),"evidence_recall_at_5":round(evidence_hits/grounded,3),"provider_constraint_accuracy":round(correct_provider/grounded,3),"abstention_accuracy":round(abstentions/abstention_cases,3),"failures":failures}

if __name__ == "__main__": print(json.dumps(evaluate(), indent=2))
