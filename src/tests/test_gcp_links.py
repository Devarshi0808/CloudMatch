#!/usr/bin/env python3
"""
Test script specifically for GCP Marketplace product link extraction
"""

import asyncio
import json
from gcp_headless_scraping import GCPMarketplaceScraper

async def test_link_extraction():
    """Test link extraction from GCP Marketplace"""
    
    print("🔗 Testing GCP Marketplace Product Link Extraction")
    print("=" * 60)
    
    # Test queries that should have clear product links
    test_queries = [
        "GitLab",
        "Jira",
        "Confluence"
    ]
    
    async with GCPMarketplaceScraper(headless=True) as scraper:
        for query in test_queries:
            print(f"\n🔍 Searching for: {query}")
            print("-" * 40)
            
            try:
                products = await scraper.search_products(query, max_results=5)
                if not products:
                    print("No products found.")
                    continue
                for i, product in enumerate(products):
                    print(f"{i+1}. {product['title']}")
                    print(f"   Link: {product['link']}")
                    print(f"   Description: {product['description']}")
            except Exception as e:
                print(f"Error: {e}")

async def test_specific_product_links():
    """Test getting detailed information for products with links"""
    
    print("\n🔗 Testing Product Details with Links")
    print("=" * 60)
    
    async with GCPMarketplaceScraper(headless=False) as scraper:
        # Search for a specific product
        query = "Jira Software"
        products = await scraper.search_products(query, max_results=3)
        
        for i, product in enumerate(products, 1):
            title = product.get('title', 'Unknown')
            link = product.get('link', '')
            
            print(f"\n{i}. {title}")
            print(f"   Link: {link}")
            
            if link:
                try:
                    print(f"   🔍 Getting detailed information...")
                    details = await scraper.get_product_details(link)
                    
                    if details:
                        print(f"   ✅ Successfully extracted details:")
                        print(f"      Title: {details.get('title', 'N/A')}")
                        print(f"      Description: {details.get('description', 'N/A')[:100]}...")
                        print(f"      Pricing: {details.get('pricing', 'N/A')}")
                    else:
                        print(f"   ❌ Could not extract details")
                        
                except Exception as e:
                    print(f"   ❌ Error getting details: {str(e)[:50]}...")
            else:
                print(f"   ❌ No link available for detailed extraction")

async def analyze_link_patterns():
    """Analyze the patterns of links found in GCP Marketplace"""
    
    print("\n🔍 Analyzing GCP Marketplace Link Patterns")
    print("=" * 60)
    
    async with GCPMarketplaceScraper(headless=False) as scraper:
        query = "Jira Software"
        products = await scraper.search_products(query, max_results=10)
        
        link_patterns = {}
        
        for product in products:
            link = product.get('link', '')
            if link:
                # Analyze link structure
                if 'marketplace' in link:
                    if 'product' in link:
                        pattern = 'marketplace/product'
                    elif 'search' in link:
                        pattern = 'marketplace/search'
                    else:
                        pattern = 'marketplace/other'
                elif 'console.cloud.google.com' in link:
                    pattern = 'console.cloud.google.com'
                else:
                    pattern = 'other'
                
                link_patterns[pattern] = link_patterns.get(pattern, 0) + 1
                
                print(f"Title: {product.get('title', 'Unknown')}")
                print(f"Link: {link}")
                print(f"Pattern: {pattern}")
                print("-" * 30)
        
        print(f"\n📊 Link Pattern Analysis:")
        for pattern, count in link_patterns.items():
            print(f"   {pattern}: {count} links")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_link_extraction())
    asyncio.run(test_specific_product_links())
    asyncio.run(analyze_link_patterns()) 