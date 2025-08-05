#!/usr/bin/env python3
"""
Test script for Vercel deployment
"""

import os
import sys
import json
import requests
from urllib.parse import urlencode

def test_local_api():
    """Test the API locally"""
    print("Testing local API...")
    
    # Test health endpoint
    try:
        response = requests.get('http://localhost:8000/api/health')
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Health data: {data}")
    except Exception as e:
        print(f"Health check failed: {e}")
    
    # Test search endpoint
    try:
        search_data = {
            "vendor": "Red Hat",
            "solution": "Jira"
        }
        response = requests.post('http://localhost:8000/api/search', 
                               json=search_data)
        print(f"Search test: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Search results: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Search test failed: {e}")

def test_vercel_endpoints(base_url):
    """Test Vercel deployment endpoints"""
    print(f"Testing Vercel deployment at: {base_url}")
    
    # Test health endpoint
    try:
        response = requests.get(f'{base_url}/api/health')
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Health data: {data}")
    except Exception as e:
        print(f"Health check failed: {e}")
    
    # Test search endpoint
    try:
        search_data = {
            "vendor": "Red Hat",
            "solution": "Jira"
        }
        response = requests.post(f'{base_url}/api/search', 
                               json=search_data)
        print(f"Search test: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Search results: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Search test failed: {e}")
    
    # Test GET search endpoint
    try:
        params = {
            "vendor": "Adobe",
            "solution": "Photoshop"
        }
        response = requests.get(f'{base_url}/api/search?{urlencode(params)}')
        print(f"GET Search test: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"GET Search results: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"GET Search test failed: {e}")

def check_files():
    """Check if required files exist"""
    print("Checking required files...")
    
    required_files = [
        'vercel.json',
        'requirements-vercel.txt',
        'api/index.py',
        'public/index.html',
        'data/Vendors_and_Products.xlsx'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")

def main():
    """Main test function"""
    print("=== CloudMatch Vercel Deployment Test ===\n")
    
    # Check files
    check_files()
    print()
    
    # Test local if running
    if len(sys.argv) > 1 and sys.argv[1] == '--local':
        test_local_api()
    elif len(sys.argv) > 1:
        # Test Vercel deployment
        base_url = sys.argv[1]
        test_vercel_endpoints(base_url)
    else:
        print("Usage:")
        print("  python test_vercel_deployment.py --local")
        print("  python test_vercel_deployment.py https://your-app.vercel.app")

if __name__ == "__main__":
    main() 