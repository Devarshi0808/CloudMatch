import os
from unittest.mock import MagicMock, patch
from api.provider_ingestion import ingest_aws, ingest_configured_listings, normalize_aws_listing, normalize_azure_listing

def test_normalize_aws_listing_preserves_official_provenance():
    listing = normalize_aws_listing({"listingId": "abc123", "listingName": "Ansible", "publisher": {"displayName": "Red Hat"}, "shortDescription": "Automation"})
    assert listing["verification"] == "official_api"
    assert listing["source"] == "aws_marketplace_discovery_api"
    assert listing["url"].startswith("https://aws.amazon.com/marketplace/")

def test_normalize_azure_listing_builds_product_url():
    listing = normalize_azure_listing({"displayName": "Example", "publisherDisplayName": "Vendor", "uniqueProductId": "vendor.product"})
    assert listing["verification"] == "official_api"
    assert listing["source"] == "azure_marketplace_catalog_api"
    assert listing["url"].endswith("vendor.product")

def test_unconfigured_ingestion_reports_each_provider_boundary():
    with patch.dict(os.environ, {}, clear=True): result = ingest_configured_listings("Red Hat")
    assert result["listings"] == []
    assert result["providers"]["aws"]["status"] == "not_configured"
    assert result["providers"]["azure"]["status"] == "not_configured"
    assert result["providers"]["gcp"]["status"] == "link_only"

def test_aws_adapter_uses_discovery_search():
    client = MagicMock(); client.search_listings.return_value = {"totalResults": 1, "listingSummaries": [{"listingId": "id1", "listingName": "Product"}]}
    boto3 = MagicMock(); boto3.client.return_value = client
    with patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "test", "AWS_SECRET_ACCESS_KEY": "test"}, clear=True), patch.dict("sys.modules", {"boto3": boto3}): result = ingest_aws("product", 5)
    assert result["status"] == "ok" and result["listings"][0]["title"] == "Product"
    client.search_listings.assert_called_once_with(searchText="product", maxResults=5, sortBy="RELEVANCE", sortOrder="DESCENDING")
