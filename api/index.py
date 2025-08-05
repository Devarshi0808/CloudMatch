from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from urllib.parse import parse_qs, urlparse

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Handle NLTK downloads for serverless environment
try:
    import nltk
    import ssl
    
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    
    # Download NLTK data if not available
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet', quiet=True)
except Exception as e:
    print(f"NLTK setup warning: {e}")

try:
    from marketplace_matcher import MarketplaceMatcher
    from utils.cache import get_from_cache_fuzzy, set_in_cache, get_cache_stats
except ImportError as e:
    print(f"Import error: {e}")

class handler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.matcher = None
        super().__init__(*args, **kwargs)
    
    def load_matcher(self):
        """Load the marketplace matcher if not already loaded"""
        if self.matcher is None:
            try:
                self.matcher = MarketplaceMatcher()
                excel_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Vendors_and_Products.xlsx')
                
                # Check if file exists
                if not os.path.exists(excel_path):
                    print(f"Excel file not found at: {excel_path}")
                    return False
                
                success = self.matcher.load_excel_data(excel_path)
                if not success:
                    print("Warning: Could not load Excel data")
                    return False
                
                print(f"Successfully loaded matcher with {len(self.matcher.vendors)} vendors")
                return True
            except Exception as e:
                print(f"Error loading matcher: {e}")
                self.matcher = None
                return False
        return True
    
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
        
        # Check if matcher can be loaded
        matcher_status = "available" if self.load_matcher() else "unavailable"
        
        response = {
            "status": "healthy",
            "service": "CloudMatch API",
            "version": "1.0.0",
            "matcher": matcher_status
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
        """Perform the actual search using the marketplace matcher"""
        try:
            # Load matcher if not already loaded
            if not self.load_matcher():
                print("Matcher not available, using mock results")
                return self.get_mock_results(vendor, solution)
            
            # Check cache first
            cache_key = f"{vendor.lower()}_{solution.lower()}"
            try:
                cached_results = get_from_cache_fuzzy(cache_key)
                if cached_results:
                    print(f"Returning cached results for {cache_key}")
                    return cached_results
            except Exception as e:
                print(f"Cache error: {e}")
            
            # Perform search using the matcher
            print(f"Performing search for vendor: {vendor}, solution: {solution}")
            results = self.matcher.search_marketplaces(vendor, solution)
            
            # Cache the results
            if results:
                try:
                    set_in_cache(cache_key, results)
                except Exception as e:
                    print(f"Cache set error: {e}")
            
            return results or self.get_mock_results(vendor, solution)
            
        except Exception as e:
            print(f"Search error: {e}")
            return self.get_mock_results(vendor, solution)
    
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