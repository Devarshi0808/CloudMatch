#!/usr/bin/env python3
"""
Test script for Azure Marketplace scraping with correct HTML structure
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import re

def test_azure_scraping():
    """Test Azure Marketplace scraping with Jira Software"""
    search_query = "Jira Software"
    
    # Azure Marketplace search URL
    search_url = f"https://azuremarketplace.microsoft.com/en-us/marketplace/apps?search={quote_plus(search_query)}&page=1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Testing Azure Marketplace scraping for: {search_query}")
    print(f"URL: {search_url}")
    print("=" * 60)
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"Response status: {response.status_code}")
        print(f"Response length: {len(response.content)} characters")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Test the correct selectors based on actual HTML structure
            print("\n1. Testing tileContent selector:")
            tile_contents = soup.find_all('div', class_='tileContent')
            print(f"Found {len(tile_contents)} tileContent elements")
            
            print("\n2. Testing h3.title selector:")
            title_elements = soup.find_all('h3', class_='title')
            print(f"Found {len(title_elements)} h3.title elements")
            
            for i, title_elem in enumerate(title_elements[:5]):
                title = title_elem.get_text(strip=True)
                title_attr = title_elem.get('title', '')
                print(f"  {i+1}. Text: '{title}' | Title attr: '{title_attr}'")
            
            print("\n3. Testing provider selector:")
            provider_elements = soup.find_all('div', class_='provider')
            print(f"Found {len(provider_elements)} provider elements")
            
            for i, provider_elem in enumerate(provider_elements[:3]):
                provider = provider_elem.get_text(strip=True)
                print(f"  {i+1}. Provider: '{provider}'")
            
            print("\n4. Looking for Jira-related content:")
            jira_products = []
            
            # Check tileContent elements
            for tile in tile_contents:
                title_elem = tile.find('h3', class_='title')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    title_attr = title_elem.get('title', '')
                    product_title = title_attr if title_attr else title
                    
                    if 'jira' in product_title.lower():
                        provider_elem = tile.find('div', class_='provider')
                        provider = provider_elem.get_text(strip=True) if provider_elem else ""
                        jira_products.append((product_title, provider))
            
            print(f"Found {len(jira_products)} Jira products in tileContent:")
            for title, provider in jira_products:
                print(f"  - {title} by {provider}")
                
        else:
            print(f"Failed to get response: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_azure_scraping() 