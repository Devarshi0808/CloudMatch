from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from marketplace_matcher import MarketplaceMatcher

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = {
            "message": "CloudMatch API is running!",
            "endpoints": {
                "search": "/api/search?vendor=<vendor>&solution=<solution>",
                "health": "/api/health"
            }
        }
        
        self.wfile.write(json.dumps(response).encode())
        return

    def do_POST(self):
        if self.path == '/api/search':
            self.handle_search()
        else:
            self.send_response(404)
            self.end_headers()
            return

    def handle_search(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            vendor = data.get('vendor', '')
            solution = data.get('solution', '')
            
            # Initialize matcher
            matcher = MarketplaceMatcher()
            
            # Perform search
            results = matcher.search_marketplaces(vendor, solution)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "vendor": vendor,
                "solution": solution,
                "results": results
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "error": str(e),
                "message": "An error occurred during search"
            }
            
            self.wfile.write(json.dumps(error_response).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return 