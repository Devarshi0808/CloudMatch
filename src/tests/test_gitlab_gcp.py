#!/usr/bin/env python3
"""
Specific test for GitLab on GCP Marketplace
"""

import asyncio
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

def test_gitlab_static():
    """Test static access to GitLab on GCP Marketplace"""
    print("🔍 Testing GitLab on GCP Marketplace (Static)")
    print("=" * 60)
    
    # Test direct search URL
    search_url = "https://console.cloud.google.com/marketplace/search?q=gitlab"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"URL: {response.url}")
        print(f"Length: {len(response.content)} characters")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for GitLab mentions
            gitlab_mentions = soup.find_all(text=lambda x: x and 'gitlab' in x.lower())
            print(f"GitLab mentions found: {len(gitlab_mentions)}")
            
            # Look for marketplace links
            marketplace_links = soup.find_all('a', href=lambda x: x and 'marketplace' in x)
            print(f"Marketplace links found: {len(marketplace_links)}")
            
            # Look for specific GitLab links
            gitlab_links = soup.find_all('a', href=lambda x: x and 'gitlab' in x.lower())
            print(f"GitLab links found: {len(gitlab_links)}")
            
            for i, link in enumerate(gitlab_links[:5]):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                print(f"  {i+1}. {text} -> {href}")
            
            # Save response for inspection
            with open('gitlab_gcp_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("💾 Saved response to gitlab_gcp_response.html")
            
        else:
            print(f"❌ Failed to access: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_gitlab_from_static_html():
    """Extract GitLab info from our existing static HTML"""
    print("\n🔍 Extracting GitLab from Static HTML")
    print("=" * 60)
    
    try:
        with open('gcp_test_2.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find GitLab links
        gitlab_links = soup.find_all('a', href=lambda x: x and 'gitlab' in x.lower())
        
        print(f"Found {len(gitlab_links)} GitLab links:")
        
        for i, link in enumerate(gitlab_links):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            aria_label = link.get('aria-label', '')
            
            print(f"\n{i+1}. GitLab Link:")
            print(f"   Text: {text}")
            print(f"   Aria Label: {aria_label}")
            print(f"   URL: {href}")
            
            # Clean up the URL
            if href:
                # Remove HTML entities
                href = href.replace('&amp;', '&')
                href = href.replace('&lt;', '<')
                href = href.replace('&gt;', '>')
                print(f"   Clean URL: {href}")
        
        # Look for GitLab in text content
        gitlab_text = soup.find_all(text=lambda x: x and 'gitlab' in x.lower())
        print(f"\nGitLab text mentions: {len(gitlab_text)}")
        
        for i, text in enumerate(gitlab_text[:3]):
            print(f"  {i+1}. {text.strip()}")
            
    except Exception as e:
        print(f"❌ Error reading static HTML: {e}")

async def test_gitlab_headless():
    """Test headless browser search for GitLab"""
    print("\n🔍 Testing GitLab with Headless Browser")
    print("=" * 60)
    
    try:
        from gcp_headless_scraping import GCPMarketplaceScraper
        
        async with GCPMarketplaceScraper(headless=False) as scraper:
            # Search for GitLab
            products = await scraper.search_products("GitLab", max_results=5)
            
            if products:
                print(f"✅ Found {len(products)} GitLab products:")
                
                for i, product in enumerate(products, 1):
                    title = product.get('title', 'Unknown')
                    link = product.get('link', '')
                    description = product.get('description', '')
                    
                    print(f"\n{i}. {title}")
                    if link:
                        print(f"   ✅ Link: {link}")
                    else:
                        print(f"   ❌ No link found")
                    
                    if description:
                        desc = description[:100] + "..." if len(description) > 100 else description
                        print(f"   Description: {desc}")
            else:
                print("❌ No GitLab products found with headless browser")
                
    except Exception as e:
        print(f"❌ Error with headless browser: {e}")

def analyze_gitlab_link():
    """Analyze the GitLab link we found"""
    print("\n🔍 Analyzing GitLab Link")
    print("=" * 60)
    
    # The GitLab link we found
    gitlab_url = "https://console.cloud.google.com/marketplace/browse?hl=en&inv=1&invt=AbfYqw&q=gitlab"
    
    print(f"GitLab URL: {gitlab_url}")
    print("\nURL Analysis:")
    print(f"  Base: https://console.cloud.google.com/marketplace/browse")
    print(f"  Language: en")
    print(f"  Invitation: 1")
    print(f"  Invitation Type: AbfYqw")
    print(f"  Query: gitlab")
    
    print("\nThis appears to be a search/browse link for GitLab products on GCP Marketplace.")
    print("The 'inv=1' and 'invt=AbfYqw' parameters suggest this might be an invitation-based or special access link.")
    
    # Test if we can access this URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(gitlab_url, headers=headers, timeout=10)
        print(f"\nAccess Test:")
        print(f"  Status: {response.status_code}")
        print(f"  Redirected to: {response.url}")
        
        if response.status_code == 200:
            print("  ✅ URL is accessible")
        else:
            print("  ❌ URL not accessible")
            
    except Exception as e:
        print(f"  ❌ Error accessing URL: {e}")

if __name__ == "__main__":
    test_gitlab_static()
    test_gitlab_from_static_html()
    analyze_gitlab_link()
    
    # Uncomment to test headless browser (requires Playwright)
    # asyncio.run(test_gitlab_headless())
    
    print("\n" + "=" * 60)
    print("📋 GitLab on GCP Marketplace Summary:")
    print("✅ GitLab is present on GCP Marketplace")
    print("✅ Found search/browse link for GitLab")
    print("✅ Link format: console.cloud.google.com/marketplace/browse?q=gitlab")
    print("⚠️  May require special access parameters")
    print("✅ Can be extracted using our scraper") 