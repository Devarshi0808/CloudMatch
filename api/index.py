from http.server import BaseHTTPRequestHandler
import json
import sys
import os

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
            "status": "success",
            "version": "1.0.0",
            "endpoints": {
                "search": "/api/search?vendor=<vendor>&solution=<solution>",
                "health": "/api/health"
            },
            "usage": {
                "method": "POST",
                "body": {
                    "vendor": "vendor_name",
                    "solution": "solution_name"
                }
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
            
            # Simple mock response for now
            # In production, this would integrate with the full marketplace_matcher
            mock_results = {
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
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "vendor": vendor,
                "solution": solution,
                "results": mock_results,
                "status": "success",
                "message": "Search completed successfully"
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "error": str(e),
                "message": "An error occurred during search",
                "status": "error"
            }
            
            self.wfile.write(json.dumps(error_response).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return 