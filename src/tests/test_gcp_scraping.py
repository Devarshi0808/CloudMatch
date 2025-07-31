#!/usr/bin/env python3
"""
Test script for GCP Marketplace headless browser scraping
"""

import asyncio
import json
from gcp_headless_scraping import GCPMarketplaceScraper

async def test_gcp_scraping():
    """Test the GCP Marketplace scraper"""
    
    print("🚀 Testing GCP Marketplace Headless Browser Scraping")
    print("=" * 60)
    
    # Test queries from your Excel file
    test_queries = [
        "Jira Software",
        "Confluence",
        "Bitbucket",
        "Atlassian",
        "Microsoft Office",
        "Slack"
    ]
    
    async with GCPMarketplaceScraper(headless=False) as scraper:
        for query in test_queries:
            print(f"\n🔍 Searching for: {query}")
            print("-" * 40)
            
            try:
                # Search for products
                products = await scraper.search_products(query, max_results=5)
                
                if products:
                    print(f"✅ Found {len(products)} products:")
                    for i, product in enumerate(products, 1):
                        print(f"\n  {i}. {product.get('title', 'Unknown Title')}")
                        if product.get('description'):
                            desc = product['description'][:100] + "..." if len(product['description']) > 100 else product['description']
                            print(f"     Description: {desc}")
                        if product.get('link'):
                            print(f"     Link: {product['link']}")
                else:
                    print("❌ No products found")
                    
            except Exception as e:
                print(f"❌ Error searching for '{query}': {e}")
                
            # Add delay between searches to be respectful
            await asyncio.sleep(2)
    
    print("\n" + "=" * 60)
    print("✅ GCP Marketplace scraping test completed!")

async def test_single_product_details():
    """Test getting detailed information for a specific product"""
    
    print("\n🔍 Testing Product Details Extraction")
    print("=" * 60)
    
    async with GCPMarketplaceScraper(headless=False) as scraper:
        # First search for a product
        query = "Jira Software"
        products = await scraper.search_products(query, max_results=1)
        
        if products and products[0].get('link'):
            product_url = products[0]['link']
            print(f"Getting details for: {products[0]['title']}")
            print(f"URL: {product_url}")
            
            try:
                details = await scraper.get_product_details(product_url)
                if details:
                    print("\n📋 Product Details:")
                    print(json.dumps(details, indent=2))
                else:
                    print("❌ Could not extract product details")
            except Exception as e:
                print(f"❌ Error getting product details: {e}")
        else:
            print("❌ No product found to get details for")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_gcp_scraping())
    asyncio.run(test_single_product_details()) 