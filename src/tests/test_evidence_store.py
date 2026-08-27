from api.agent_research import compare_products, parse_request, research_products
from api.evidence_store import get_evidence, load_evidence, search_evidence

def test_snapshot_has_stable_provenance():
    store = load_evidence(); assert store["schema_version"] == "1.0" and len(store["listings"]) >= 10
    assert all(item["id"] and item["url"].startswith("https://") and item["verified_at"] for item in store["listings"])

def test_hybrid_retrieval_finds_capability():
    matches = search_evidence("automation orchestration")
    assert matches and "Ansible" in matches[0]["title"] and matches[0]["matched_terms"]

def test_provider_filter_is_extracted():
    assert parse_request("Find Ansible on Azure")["provider"] == "azure"
    assert all(item["provider"] == "azure" for item in search_evidence("Ansible", "azure"))

def test_agent_brief_is_grounded_and_inspectable():
    result = research_products("Find enterprise automation for Azure")
    assert result["status"] == "grounded" and result["evidence"]
    assert get_evidence(result["evidence"][0]["id"])["url"] == result["evidence"][0]["url"]

def test_agent_abstains_without_evidence():
    result = research_products("quantum banana database on mars")
    assert result["status"] == "abstained" and result["evidence"] == []

def test_comparison_has_structured_output(): assert "comparison" in compare_products("compare Datadog on Azure")
