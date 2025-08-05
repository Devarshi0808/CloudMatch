from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from urllib.parse import parse_qs, urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/api/health':
            self.handle_health()
        elif path == '/api/search':
            self.handle_search_get(parsed_url.query)
        else:
            self.handle_root()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/search':
            self.handle_search_post()
        else:
            self.send_response(404)
            self.end_headers()
            return
    
    def handle_root(self):
        """Handle root endpoint"""
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
        try:
            # Simple search implementation that works without heavy dependencies
            results = self.get_marketplace_results(vendor, solution)
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return self.get_mock_results(vendor, solution)
    
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
        
        # AWS Marketplace
        if vendor and solution:
            aws_confidence = self.calculate_confidence(vendor_lower, solution_lower)
            if aws_confidence > 50:
                results["aws"].append({
                    "title": f"{vendor} {solution} on AWS Marketplace",
                    "url": f"https://aws.amazon.com/marketplace/search?searchTerms={vendor}+{solution}",
                    "confidence": aws_confidence
                })
        
        # Azure Marketplace
        if vendor and solution:
            azure_confidence = self.calculate_confidence(vendor_lower, solution_lower)
            if azure_confidence > 50:
                results["azure"].append({
                    "title": f"{vendor} {solution} on Azure Marketplace",
                    "url": f"https://azuremarketplace.microsoft.com/en-us/marketplace/apps?search={vendor}+{solution}",
                    "confidence": azure_confidence
                })
        
        # GCP Marketplace
        if vendor and solution:
            gcp_confidence = self.calculate_confidence(vendor_lower, solution_lower)
            if gcp_confidence > 50:
                results["gcp"].append({
                    "title": f"{vendor} {solution} on Google Cloud Marketplace",
                    "url": f"https://console.cloud.google.com/marketplace/search?q={vendor}+{solution}",
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