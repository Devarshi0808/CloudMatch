from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import time
from urllib.parse import parse_qs, urlparse
try:
    from .catalog_matcher import cache_info, llm_suggestions, search_catalog
    from .open_search import search_open_marketplaces
except ImportError:
    from catalog_matcher import cache_info, llm_suggestions, search_catalog
    from open_search import search_open_marketplaces

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/api/health':
            self.handle_health()
        elif path == '/api/search':
            self.handle_search_get(parsed_url.query)
        elif path == '/api/mcp':
            self.send_json({
                "jsonrpc": "2.0",
                "id": None,
                "result": {"tools": self.mcp_tools()},
            })
        else:
            self.handle_root()
    
    def do_POST(self):
        """Handle POST requests"""
        path = urlparse(self.path).path
        if path == '/api/search':
            self.handle_search_post()
        elif path == '/api/mcp':
            self.handle_mcp()
        else:
            self.send_response(404)
            self.end_headers()
            return
    
    def handle_root(self):
        """Handle root endpoint"""
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'public', 'index.html')
        try:
            with open(frontend_path, 'rb') as frontend:
                content = frontend.read()

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
            return
        except OSError:
            pass

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "message": "CloudMatch API is running!",
            "status": "success",
            "version": "1.0.0",
            "endpoints": {
                "health": "/api/health",
                "search": "/api/search?vendor=<vendor>&solution=<solution>",
                "search_post": "/api/search (POST with JSON body)"
            }
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def handle_health(self):
        """Handle health check endpoint"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "healthy",
            "service": "CloudMatch API",
            "version": "1.0.0",
            "message": "API is ready for searches"
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def handle_search_get(self, query_string):
        """Handle GET search requests"""
        try:
            # Parse query parameters
            params = parse_qs(query_string)
            vendor = params.get('vendor', [''])[0]
            solution = params.get('solution', [''])[0]
            
            results = self.perform_search(vendor, solution)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "vendor": vendor,
                "solution": solution,
                "results": results,
                "status": "success",
                "message": "Search completed successfully"
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error_response(str(e))
    
    def handle_search_post(self):
        """Handle POST search requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                vendor = data.get('vendor', '')
                solution = data.get('solution', '')
            else:
                vendor = ''
                solution = ''
            
            results = self.perform_search(vendor, solution)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "vendor": vendor,
                "solution": solution,
                "results": results,
                "status": "success",
                "message": "Search completed successfully"
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error_response(str(e))
    
    def perform_search(self, vendor, solution):
        """Perform the search and return results"""
        started = time.perf_counter()
        result = search_open_marketplaces(vendor, solution)
        result["llm"] = {"enabled": result["source"] == "open_web_llm_search"}
        result["observability"] = {
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            "cache_hit": False,
            "cache_size": 0,
            "source": result["source"],
        }
        return result

    def send_json(self, response, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def mcp_tools(self):
        return [
            {
                "name": "search_marketplaces",
                "description": "Search open web results for cloud marketplace listings.",
                "inputSchema": {"type": "object", "properties": {"vendor": {"type": "string"}, "solution": {"type": "string"}}},
            },
            {
                "name": "catalog_lookup",
                "description": "Look up the local seed catalog explicitly; not a live marketplace search.",
                "inputSchema": {"type": "object", "properties": {"vendor": {"type": "string"}, "solution": {"type": "string"}}},
            },
            {
                "name": "suggest_queries",
                "description": "Suggest marketplace query variants using an optional LLM.",
                "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            },
        ]

    def handle_mcp(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            request = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
            method = request.get('method')
            if method == 'tools/list':
                result = {"tools": self.mcp_tools()}
            elif method == 'tools/call':
                name = request.get('params', {}).get('name')
                arguments = request.get('params', {}).get('arguments', {})
                if name == 'search_marketplaces':
                    result = {"content": [{"type": "json", "json": search_open_marketplaces(arguments.get('vendor', ''), arguments.get('solution', ''))}]}
                elif name == 'catalog_lookup':
                    result = {"content": [{"type": "json", "json": search_catalog(arguments.get('vendor', ''), arguments.get('solution', ''))}]}
                elif name == 'suggest_queries':
                    result = {"content": [{"type": "json", "json": llm_suggestions(arguments.get('query', ''))}]}
                else:
                    raise ValueError(f'Unknown tool: {name}')
            else:
                raise ValueError(f'Unsupported MCP method: {method}')
            self.send_json({"jsonrpc": "2.0", "id": request.get('id'), "result": result})
        except Exception as error:
            self.send_json({"jsonrpc": "2.0", "id": None, "error": {"code": -32602, "message": str(error)}}, 400)
    
    def get_marketplace_results(self, vendor, solution):
        """Get marketplace results with intelligent matching"""
        results = {
            "aws": [],
            "azure": [],
            "gcp": []
        }
        
        # Simple fuzzy matching logic
        vendor_lower = vendor.lower()
        solution_lower = solution.lower()
        
        query = ' '.join(part for part in (vendor, solution) if part).strip()

        # AWS Marketplace
        if query:
            aws_confidence = self.calculate_confidence(vendor_lower, solution_lower)
            if aws_confidence > 50:
                results["aws"].append({
                    "title": f"{query} on AWS Marketplace",
                    "url": f"https://aws.amazon.com/marketplace/search?searchTerms={query.replace(' ', '+')}",
                    "confidence": aws_confidence
                })
        
        # Azure Marketplace
        if query:
            azure_confidence = self.calculate_confidence(vendor_lower, solution_lower)
            if azure_confidence > 50:
                results["azure"].append({
                    "title": f"{query} on Azure Marketplace",
                    "url": f"https://azuremarketplace.microsoft.com/en-us/marketplace/apps?search={query.replace(' ', '+')}",
                    "confidence": azure_confidence
                })
        
        # GCP Marketplace
        if query:
            gcp_confidence = self.calculate_confidence(vendor_lower, solution_lower)
            if gcp_confidence > 50:
                results["gcp"].append({
                    "title": f"{query} on Google Cloud Marketplace",
                    "url": f"https://console.cloud.google.com/marketplace/search?q={query.replace(' ', '+')}",
                    "confidence": gcp_confidence
                })
        
        return results
    
    def calculate_confidence(self, vendor, solution):
        """Calculate confidence score based on input quality"""
        confidence = 70  # Base confidence
        
        # Increase confidence for longer, more specific inputs
        if len(vendor) > 3:
            confidence += 10
        if len(solution) > 3:
            confidence += 10
        
        # Common vendor names get higher confidence
        common_vendors = ['microsoft', 'adobe', 'red hat', 'atlassian', 'oracle', 'sap']
        if any(cv in vendor for cv in common_vendors):
            confidence += 15
        
        # Common solution names get higher confidence
        common_solutions = ['office', 'photoshop', 'jira', 'wordpress', 'mysql', 'postgresql']
        if any(cs in solution for cs in common_solutions):
            confidence += 15
        
        return min(confidence, 95)  # Cap at 95%
    
    def get_mock_results(self, vendor, solution):
        """Return mock results when actual search fails"""
        return {
            "aws": [
                {
                    "title": f"{vendor} {solution} on AWS",
                    "url": f"https://aws.amazon.com/marketplace/search?searchTerms={vendor}+{solution}",
                    "confidence": 85
                }
            ],
            "azure": [
                {
                    "title": f"{vendor} {solution} on Azure",
                    "url": f"https://azuremarketplace.microsoft.com/en-us/marketplace/apps?search={vendor}+{solution}",
                    "confidence": 80
                }
            ],
            "gcp": [
                {
                    "title": f"{vendor} {solution} on GCP",
                    "url": f"https://console.cloud.google.com/marketplace/search?q={vendor}+{solution}",
                    "confidence": 75
                }
            ]
        }
    
    def send_error_response(self, error_message):
        """Send error response"""
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        error_response = {
            "error": error_message,
            "message": "An error occurred during search",
            "status": "error"
        }
        
        self.wfile.write(json.dumps(error_response).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return 