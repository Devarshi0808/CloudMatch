from unittest.mock import patch
from api.live_search import _provider_for_url, _valid_url, detect_provider, search_live_marketplaces
from api.open_search import provider_links

def test_domain_verification_rejects_lookalikes():
    assert _valid_url("https://aws.amazon.com/marketplace/pp/prodview-1", "aws")
    assert not _valid_url("https://evil.example/aws.amazon.com/marketplace/pp/x", "aws")

def test_provider_detection_and_encoded_links():
    assert detect_provider("Find this on Microsoft Azure") == "azure"
    assert "Red+Hat+%26+Ansible" in provider_links("Red Hat & Ansible")["aws"]["url"]

def test_tavily_results_are_revalidated_by_official_domain():
    payload={"response_time":0.2,"results":[{"url":"https://aws.amazon.com/marketplace/pp/prodview-1","title":"Ansible","content":"Live","score":0.92},{"url":"https://evil.example/marketplace/pp/x","title":"Fake"}]}
    with patch.dict("os.environ", {"TAVILY_API_KEY":"test"}), patch("api.live_search._call_tavily", return_value=payload):
        result=search_live_marketplaces("Ansible", limit=5)
    assert result["source"] == "tavily_live_search" and len(result["matches"]) == 1
    assert result["matches"][0]["provider"] == "aws" and result["matches"][0]["relevance_score"] == 0.92

def test_ranking_prefers_query_terms_in_official_url():
    payload={"results":[{"url":"https://azuremarketplace.microsoft.com/en-us/marketplace/apps/other.ansible","title":"Marketplace","content":"Red Hat Ansible","score":0.95},{"url":"https://azuremarketplace.microsoft.com/en-us/marketplace/apps/redhat.rh-ansible","title":"Marketplace","content":"Red Hat Ansible","score":0.85}]}
    with patch.dict("os.environ", {"TAVILY_API_KEY":"test"}), patch("api.live_search._call_tavily", return_value=payload): result=search_live_marketplaces("Red Hat Ansible", "azure")
    assert "redhat" in result["matches"][0]["url"]

def test_missing_key_is_explicit_not_fabricated():
    with patch.dict("os.environ", {}, clear=True): result=search_live_marketplaces("OpenShift", provider="gcp")
    assert result["matches"] == [] and result["providers"]["gcp"]["status"] == "not_configured"
