import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from api.catalog_matcher import load_catalog, search_catalog


def test_catalog_loads_without_pandas():
    catalog = load_catalog()
    assert len(catalog) == 154
    assert {"vendor", "solution_name"}.issubset(catalog[0])


def test_vendor_only_search_returns_ranked_evidence():
    result = search_catalog(vendor="Red Hat")
    assert result["matches"][0]["vendor"] == "Red Hat"
    assert result["matches"][0]["solution"] == "Ansible"
    assert result["matches"][0]["match_type"] == "catalog_match"
    assert result["matches"][0]["evidence"]


def test_solution_only_search_returns_provider_links():
    result = search_catalog(solution="Jira Software")
    assert result["matches"]
    assert set(result["marketplace_links"]) == {"aws", "azure", "gcp"}


def test_empty_search_is_explicitly_empty():
    result = search_catalog()
    assert result["matches"] == []
    assert result["marketplace_links"] == {}
