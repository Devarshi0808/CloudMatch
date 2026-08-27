import io
import json
from unittest.mock import patch
from api.index import handler

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
    result = {"query": "Red Hat", "matches": [], "source": "benchmark_catalog"}
    with patch("api.index.search_open_marketplaces", return_value=result): instance.handle_search("Red Hat", "")
    payload = json.loads(instance.wfile.getvalue())
    assert captured["status"] == 200
    assert payload["results"]["observability"]["result_count"] == 0

def test_mcp_unknown_tool_preserves_request_id():
    instance, captured = make_handler()
    instance.handle_mcp({"jsonrpc": "2.0", "id": 42, "method": "tools/call", "params": {"name": "missing"}})
    payload = json.loads(instance.wfile.getvalue())
    assert captured["status"] == 400 and payload["id"] == 42
