"""Vercel HTTP handler for CloudMatch."""

from http.server import BaseHTTPRequestHandler
import json
import time
from urllib.parse import parse_qs, urlparse

try:
    from .catalog_matcher import search_catalog
    from .open_search import search_open_marketplaces
    from .provider_ingestion import ingest_configured_listings
except ImportError:
    from catalog_matcher import search_catalog
    from open_search import search_open_marketplaces
    from provider_ingestion import ingest_configured_listings

MAX_BODY_BYTES = 16_384


class handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json({"status": "healthy", "service": "CloudMatch API", "version": "2.0.0"})
        elif parsed.path == "/api/search":
            params = parse_qs(parsed.query)
            self.handle_search(params.get("vendor", [""])[0], params.get("solution", [""])[0])
        elif parsed.path == "/api/mcp":
            self.send_json({"jsonrpc": "2.0", "id": None, "result": {"tools": self.mcp_tools()}})
        else:
            self.send_json({"status": "ok", "service": "CloudMatch API", "endpoints": ["/api/health", "/api/search", "/api/mcp"]})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > MAX_BODY_BYTES:
                return self.send_json({"status": "error", "message": "Request body is too large"}, 413)
            request = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return self.send_json({"status": "error", "message": "Request body must be valid JSON"}, 400)
        if path == "/api/search":
            self.handle_search(request.get("vendor", ""), request.get("solution", ""))
        elif path == "/api/mcp":
            self.handle_mcp(request)
        else:
            self.send_json({"status": "error", "message": "Not found"}, 404)

    def handle_search(self, vendor, solution):
        if not isinstance(vendor, str) or not isinstance(solution, str):
            return self.send_json({"status": "error", "message": "vendor and solution must be strings"}, 400)
        if not vendor.strip() and not solution.strip():
            return self.send_json({"status": "error", "message": "Enter a vendor, product, or both"}, 400)
        started = time.perf_counter()
        try:
            result = search_open_marketplaces(vendor, solution)
            result["observability"] = {"duration_ms": round((time.perf_counter() - started) * 1000, 2), "source": result["source"], "result_count": len(result["matches"])}
            self.send_json({"status": "success", "results": result})
        except Exception as error:
            self.send_json({"status": "error", "message": "Search failed", "detail": str(error)[:200]}, 500)

    @staticmethod
    def mcp_tools():
        search_schema = {"type": "object", "properties": {"vendor": {"type": "string"}, "solution": {"type": "string"}}}
        return [
            {"name": "search_marketplaces", "description": "Search official provider APIs and return labeled benchmark fallbacks.", "inputSchema": search_schema},
            {"name": "catalog_lookup", "description": "Rank the bundled benchmark catalog; this is not live marketplace data.", "inputSchema": search_schema},
            {"name": "ingest_listings", "description": "Run official marketplace adapters and return health metadata.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
        ]

    def handle_mcp(self, request):
        request_id = request.get("id")
        try:
            method = request.get("method")
            if method == "tools/list":
                result = {"tools": self.mcp_tools()}
            elif method == "tools/call":
                params = request.get("params") or {}
                arguments = params.get("arguments") or {}
                tools = {
                    "search_marketplaces": lambda: search_open_marketplaces(arguments.get("vendor", ""), arguments.get("solution", "")),
                    "catalog_lookup": lambda: search_catalog(arguments.get("vendor", ""), arguments.get("solution", "")),
                    "ingest_listings": lambda: ingest_configured_listings(arguments.get("query", "")),
                }
                if params.get("name") not in tools:
                    raise ValueError(f"Unknown tool: {params.get('name')}")
                result = {"content": [{"type": "text", "text": json.dumps(tools[params["name"]](), ensure_ascii=False)}]}
            else:
                raise ValueError(f"Unsupported method: {method}")
            self.send_json({"jsonrpc": "2.0", "id": request_id, "result": result})
        except (TypeError, ValueError) as error:
            self.send_json({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": str(error)}}, 400)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
