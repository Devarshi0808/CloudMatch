import io
import json
from unittest.mock import patch
from api.index import handler
from api.agent_research import parse_request

def make_handler(body=b"{}"):
    instance = object.__new__(handler)
    instance.rfile = io.BytesIO(body)
    instance.wfile = io.BytesIO()
    instance.headers = {"Content-Length": str(len(body))}
    instance.request_version = "HTTP/1.1"
    instance.command = "POST"
    instance.requestline = "POST /api/search HTTP/1.1"
    instance.client_address = ("127.0.0.1", 1)
    instance.server = None
    captured = {}
    instance.send_response = lambda status: captured.update(status=status)
    instance.send_header = lambda key, value: None
    instance.end_headers = lambda: None
    return instance, captured

def test_search_rejects_empty_query():
    instance, captured = make_handler()
    instance.handle_search("", "")
    assert captured["status"] == 400
    assert json.loads(instance.wfile.getvalue())["status"] == "error"

def test_search_returns_observability():
    instance, captured = make_handler()
    result = {"query": "Red Hat", "matches": [], "source": "live_web_search"}
    with patch("api.index.search_open_marketplaces", return_value=result): instance.handle_search("Red Hat", "")
    payload = json.loads(instance.wfile.getvalue())
    assert captured["status"] == 200
    assert payload["results"]["observability"]["result_count"] == 0

def test_mcp_unknown_tool_preserves_request_id():
    instance, captured = make_handler()
    instance.handle_mcp({"jsonrpc": "2.0", "id": 42, "method": "tools/call", "params": {"name": "missing"}})
    payload = json.loads(instance.wfile.getvalue())
    assert captured["status"] == 400 and payload["id"] == 42

def test_research_tool_is_exposed():
    names = {tool["name"] for tool in handler.mcp_tools()}
    assert names == {"search_marketplaces", "research_products", "compare_products"}

def test_research_returns_grounded_evidence():
    live={"query":"Ansible","matches":[{"id":"live-1","provider":"azure","title":"Ansible","url":"https://marketplace.microsoft.com/en-us/product/x","description":"Live","relevance_score":0.9,"match_score":0.95,"rank_score":0.95,"matched_terms":["ansible"],"query_coverage":1.0,"verification":"official_domain","retrieved_at":"now"}],"providers":{"azure":{"status":"ok"}},"retrieved_at":"now","filtered_count":2,"duplicate_count":1,"disclaimer":"live"}
    with patch("api.agent_research.search_live_marketplaces", return_value=live):
        result = __import__("api.agent_research", fromlist=["research_products"]).research_products("Find Ansible on Azure")
    assert result["status"] == "grounded"
    assert result["evidence"][0]["provider"] == "azure"
    assert result["confidence"] == 0.95
    assert result["quality"] == {"filtered_count": 2, "duplicate_count": 1, "result_count": 1}
    assert "azure" in result["provider_links"]

def test_agent_expands_known_product_family_without_changing_user_request():
    parsed=parse_request("Find Red Hat Ansible on Azure")
    assert parsed["query"] == "Find Red Hat Ansible on Azure"
    assert parsed["search_query"] == "Red Hat Ansible Automation Platform"

def test_abstention_exposes_quality_controls_without_fallback_data():
    live={"query":"impossible","matches":[],"providers":{"gcp":{"status":"ok","result_count":0}},"retrieved_at":"now","filtered_count":4,"duplicate_count":0,"disclaimer":"live only"}
    with patch("api.agent_research.search_live_marketplaces", return_value=live):
        result = __import__("api.agent_research", fromlist=["research_products"]).research_products("Find impossible on GCP")
    assert result["status"] == "abstained"
    assert result["quality"]["filtered_count"] == 4
    assert result["evidence"] == []
