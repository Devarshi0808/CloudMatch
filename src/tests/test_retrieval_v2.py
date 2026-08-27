from api.open_search import provider_links, search_open_marketplaces
def test_provider_links_encode_query():
    links = provider_links("Red Hat & Ansible"); assert "Red+Hat+%26+Ansible" in links["aws"]["url"] and set(links) == {"aws", "azure", "gcp"}
def test_search_returns_verified_evidence_and_labeled_benchmark():
    result = search_open_marketplaces("Red Hat", "Ansible")
    assert result["source"] == "verified_snapshot" and result["matches"] and result["matches"][0]["verification"] == "reviewed_public_listing"
    assert result["catalog_matches"] and result["snapshot_verified_at"]
def test_unknown_search_does_not_fabricate_listing():
    result = search_open_marketplaces("quantum banana", "mars database")
    assert result["matches"] == [] and result["source"] == "benchmark_catalog"
