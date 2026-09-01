import json
from unittest.mock import MagicMock, patch
from api.live_search import _call_tavily, _canonical_url, _display_title, _retrieval_query, _search_depth, _summarize_content, _valid_url, detect_provider, search_live_marketplaces
from api.open_search import provider_links

def test_domain_verification_rejects_lookalikes():
    assert _valid_url("https://aws.amazon.com/marketplace/pp/prodview-1", "aws")
    assert _valid_url("https://marketplace.microsoft.com/en-us/product/redhat.rhaapomsa", "azure")
    assert _valid_url("https://marketplace.microsoft.com/es-es/product/saas/redhat.ansible", "azure")
    assert _valid_url("https://azuremarketplace.microsoft.com/en-us/marketplace/apps/redhat.ansible", "azure")
    assert not _valid_url("https://evil.example/aws.amazon.com/marketplace/pp/x", "aws")
    assert not _valid_url("https://marketplace.microsoft.com/en-us/marketplace/apps", "azure")

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
    payload={"results":[{"url":"https://marketplace.microsoft.com/en-us/product/other.ansible","title":"Marketplace","content":"Red Hat Ansible","score":0.95},{"url":"https://marketplace.microsoft.com/en-us/product/redhat.rh-ansible","title":"Marketplace","content":"Red Hat Ansible","score":0.85}]}
    with patch.dict("os.environ", {"TAVILY_API_KEY":"test"}), patch("api.live_search._call_tavily", return_value=payload): result=search_live_marketplaces("Red Hat Ansible", "azure")
    assert "redhat" in result["matches"][0]["url"]

def test_tracking_parameters_are_removed_from_canonical_url():
    url = "https://azuremarketplace.microsoft.com/marketplace/apps/redhat.ansible?tab=Overview&utm_source=test&plan=pro"
    assert _canonical_url(url).endswith("redhat.ansible?plan=pro")

def test_duplicate_titles_are_collapsed_across_distinct_offer_urls():
    payload={"results":[
        {"url":"https://aws.amazon.com/marketplace/pp/prodview-one","title":"Red Hat Ansible Automation Platform Service on AWS","content":"Red Hat Ansible Automation Platform managed service.","score":0.96},
        {"url":"https://aws.amazon.com/marketplace/pp/prodview-two","title":"Red Hat® Ansible Automation Platform Service on AWS","content":"Red Hat Ansible Automation Platform managed service.","score":0.92},
        {"url":"https://aws.amazon.com/marketplace/pp/prodview-three","title":"Red Hat Ansible Automation Platform Quickstart","content":"Red Hat Ansible Automation Platform quickstart.","score":0.85},
    ]}
    with patch.dict("os.environ", {"TAVILY_API_KEY":"test"}), patch("api.live_search._call_tavily", return_value=payload):
        result=search_live_marketplaces("Red Hat Ansible Automation Platform", "aws")
    assert len(result["matches"]) == 2
    assert result["duplicate_count"] == 1
    assert result["matches"][0]["url"].endswith("prodview-one")

def test_irrelevant_high_semantic_score_is_filtered():
    payload={"results":[
        {"url":"https://azuremarketplace.microsoft.com/marketplace/apps/redhat.rhel-ha","title":"Red Hat Enterprise Linux with High Availability","content":"A Red Hat Linux platform.","score":0.98},
        {"url":"https://azuremarketplace.microsoft.com/marketplace/apps/redhat.ansible","title":"Red Hat Ansible Automation Platform","content":"Enterprise automation from Red Hat.","score":0.80},
    ]}
    with patch.dict("os.environ", {"TAVILY_API_KEY":"test"}), patch("api.live_search._call_tavily", return_value=payload):
        result=search_live_marketplaces("Red Hat Ansible Automation Platform", "azure")
    assert [item["title"] for item in result["matches"]] == ["Red Hat Ansible Automation Platform"]
    assert result["filtered_count"] == 1

def test_exact_query_in_body_does_not_override_wrong_product_title():
    payload={"results":[{"url":"https://azuremarketplace.microsoft.com/marketplace/apps/redhat.rhel-ha","title":"Red Hat Enterprise Linux with High Availability","content":"Integrates with Red Hat Ansible Automation Platform.","score":0.99}]}
    with patch.dict("os.environ", {"TAVILY_API_KEY":"test"}), patch("api.live_search._call_tavily", return_value=payload):
        result=search_live_marketplaces("Red Hat Ansible Automation Platform", "azure")
    assert result["matches"] == []

def test_content_is_cleaned_and_bounded_for_ui():
    content = "## Overview **Useful product.** " + "Long marketplace boilerplate " * 40
    summary = _summarize_content(content)
    assert len(summary) <= 360
    assert "#" not in summary and "*" not in summary
    assert summary.endswith((".", "…"))

def test_generic_marketplace_title_is_derived_from_offer_slug():
    raw={"title":"Microsoft Marketplace | cloud solutions, AI apps, and agents","url":"https://azuremarketplace.microsoft.com/marketplace/apps/snowflake.snowflake_contact_me"}
    assert _display_title(raw) == "Snowflake Contact Me"

def test_single_term_must_appear_in_title_or_product_url():
    payload={"results":[{"url":"https://console.cloud.google.com/marketplace/product/google/patents","title":"Google Cloud console","content":"Runs on Kubernetes","score":0.99}]}
    with patch.dict("os.environ", {"TAVILY_API_KEY":"test"}), patch("api.live_search._call_tavily", return_value=payload):
        result=search_live_marketplaces("Kubernetes", "gcp")
    assert result["matches"] == []

def test_live_search_overfetches_before_quality_filtering():
    with patch.dict("os.environ", {"TAVILY_API_KEY":"test"}), patch("api.live_search._call_tavily", return_value={"results":[]}) as call:
        search_live_marketplaces("Kubernetes", "gcp", limit=5)
    assert call.call_args.args[2] == 15
    assert call.call_args.args[4] == "fast"

def test_azure_search_uses_current_and_legacy_official_domains():
    with patch.dict("os.environ", {"TAVILY_API_KEY":"test"}), patch("api.live_search._call_tavily", return_value={"results":[]}) as call:
        search_live_marketplaces("Ansible", "azure", limit=5)
    assert call.call_args.args[1] == ["marketplace.microsoft.com", "azuremarketplace.microsoft.com"]
    assert call.call_args.args[4] == "fast"

def test_azure_retrieval_query_adds_provider_context_only_for_discovery():
    assert _retrieval_query("MongoDB Atlas", ["aws"]) == "MongoDB Atlas AWS Marketplace"
    assert _retrieval_query("Red Hat OpenShift", ["azure"]) == "Red Hat OpenShift Microsoft Marketplace Azure"
    assert _retrieval_query("Neo4j", ["gcp"]) == "Neo4j"

def test_search_depth_defaults_to_one_credit_fast_mode_and_allows_override():
    with patch.dict("os.environ", {}, clear=True):
        assert _search_depth(["aws"]) == "fast"
        assert _search_depth(["azure"]) == "fast"
        assert _search_depth(["gcp"]) == "fast"
    with patch.dict("os.environ", {"TAVILY_SEARCH_DEPTH":"basic"}):
        assert _search_depth(["aws"]) == "basic"

def test_fast_request_omits_unsupported_safe_search_parameter():
    response = MagicMock()
    response.__enter__.return_value.read.return_value = b'{"results":[]}'
    with patch("api.live_search.urllib.request.urlopen", return_value=response) as urlopen:
        _call_tavily("Datadog", ["aws.amazon.com"], 5, "test", "fast")
    request_body = json.loads(urlopen.call_args.args[0].data)
    assert request_body["search_depth"] == "fast"
    assert "safe_search" not in request_body

def test_missing_key_is_explicit_not_fabricated():
    with patch.dict("os.environ", {}, clear=True): result=search_live_marketplaces("OpenShift", provider="gcp")
    assert result["matches"] == [] and result["providers"]["gcp"]["status"] == "not_configured"
