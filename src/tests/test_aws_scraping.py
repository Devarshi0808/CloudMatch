#!/usr/bin/env python3
"""
Test script for AWS Marketplace scraping
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import re

def test_aws_scraping():
    """Test AWS Marketplace scraping with Red Hat Enterprise Linux"""
    search_query = "Red Hat Enterprise Linux"
    
    # AWS Marketplace search URL
    search_url = f"https://aws.amazon.com/marketplace/search/results?searchTerms={quote_plus(search_query)}"
    
    print(f"Testing AWS Marketplace scraping for: {search_query}")
    print(f"URL: {search_url}")
    print("=" * 60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"Response status: {response.status_code}")
        print(f"Response length: {len(response.content)} characters")
        print()
        
        # Save the HTML to a file for inspection
        with open('aws_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("Saved HTML response to aws_response.html")
        print()
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Test 1: Look for table rows with data-selection-item="item"
            product_rows = soup.find_all('tr', attrs={'data-selection-item': 'item'})
            print(f"1. Testing data-selection-item='item' selector:")
            print(f"Found {len(product_rows)} product rows")
            print()
            
            # Test 2: Look for search result divs
            search_results = soup.find_all('div', attrs={'data-test-selector': 'searchResult'})
            print(f"2. Testing data-test-selector='searchResult' selector:")
            print(f"Found {len(search_results)} search result divs")
            print()
            
            # Test 3: Look for title elements
            title_elements = soup.find_all('h2', attrs={'data-semantic': 'title'})
            print(f"3. Testing h2[data-semantic='title'] selector:")
            print(f"Found {len(title_elements)} title elements")
            print()
            
            # Test 4: Look for any table rows
            all_rows = soup.find_all('tr')
            print(f"4. Testing all tr elements:")
            print(f"Found {len(all_rows)} total table rows")
            
            # Look for rows that might contain product data
            for i, row in enumerate(all_rows[:10]):
                row_text = row.get_text(strip=True)
                if 'red hat' in row_text.lower() or 'rhel' in row_text.lower():
                    print(f"  Row {i+1}: {row_text[:200]}...")
            print()
            
            # Test 5: Look for any divs with class containing 'product' or 'item'
            product_divs = soup.find_all('div', class_=re.compile(r'product|item|card'))
            print(f"5. Testing divs with product/item/card classes:")
            print(f"Found {len(product_divs)} product divs")
            
            for i, div in enumerate(product_divs[:5]):
                div_text = div.get_text(strip=True)
                if 'red hat' in div_text.lower() or 'rhel' in div_text.lower():
                    print(f"  Div {i+1}: {div_text[:200]}...")
            print()
            
            # Test 6: Look for any links containing 'marketplace'
            marketplace_links = soup.find_all('a', href=re.compile(r'marketplace'))
            print(f"6. Testing marketplace links:")
            print(f"Found {len(marketplace_links)} marketplace links")
            
            for i, link in enumerate(marketplace_links[:5]):
                title = link.get_text(strip=True)
                href = link.get('href', '')
                if title and 'red hat' in title.lower():
                    print(f"  Link {i+1}: '{title}' -> {href[:100]}...")
            print()
            
            # Test 7: Look for any text containing "Red Hat"
            all_text = soup.get_text()
            red_hat_mentions = re.findall(r'Red Hat[^.]*', all_text, re.IGNORECASE)
            print(f"7. Testing text search for 'Red Hat':")
            print(f"Found {len(red_hat_mentions)} mentions of Red Hat")
            
            for i, mention in enumerate(red_hat_mentions[:5]):
                print(f"  Mention {i+1}: {mention.strip()}")
            
        else:
            print(f"Failed to get response: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_aws_scraping() 