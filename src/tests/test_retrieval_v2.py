from unittest.mock import patch
from api.open_search import provider_links, search_open_marketplaces

def test_provider_links_encode_query():
    links = provider_links("Red Hat & Ansible")
    assert "Red+Hat+%26+Ansible" in links["aws"]["url"]
    assert set(links) == {"aws", "azure", "gcp"}

def test_hybrid_search_labels_benchmark_fallback():
    providers = {key: {"provider": key, "status": "not_configured", "listings": []} for key in ("aws", "azure", "gcp")}
    with patch("api.open_search.ingest_configured_listings", return_value={"listings": [], "providers": providers}): result = search_open_marketplaces("Red Hat", "Ansible")
    assert result["source"] == "benchmark_catalog" and result["matches"] == []
    assert result["catalog_matches"] and "not live marketplaces" in result["disclaimer"]
