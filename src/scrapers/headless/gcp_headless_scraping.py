#!/usr/bin/env python3
"""
Headless browser scraping for GCP Marketplace using Selenium
"""

import asyncio
import json
import re
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Browser, Page
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GCPMarketplaceScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def start(self):
        """Start the browser and create a new page"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.page = await self.browser.new_page()
        
        # Set user agent to avoid detection
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        logger.info("Browser started successfully")
        
    async def close(self):
        """Close the browser and playwright"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        logger.info("Browser closed")
        
    async def search_products(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        Search for products on GCP Marketplace
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of product dictionaries
        """
        try:
            # Use the improved method
            results = await self.get_gcp_results(self.page, query, max_results)
            
            # Convert to our standard format
            products = []
            for title, link in results:
                products.append({
                    'title': title,
                    'link': link,
                    'marketplace': 'GCP',
                    'description': '',  # We can add description extraction later if needed
                    'vendor': '',       # We can add vendor extraction later if needed
                    'price': ''         # We can add price extraction later if needed
                })
            
            return products
            
        except Exception as e:
            logger.error(f"Error searching GCP Marketplace: {e}")
            return []

    async def get_gcp_results(self, page, query, max_results=20):
        """
        Extract product results from GCP Marketplace using h3 selector strategy
        
        Args:
            page: Playwright page object
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of tuples (title, link)
        """
        search_url = f"https://console.cloud.google.com/marketplace/browse?hl=en&q={query.replace(' ', '%20')}"
        print(f"Navigating to: {search_url}")
        
        try:
            await page.goto(search_url, timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Check if we need to login
            if "accounts.google.com" in page.url or "login" in page.url.lower():
                print("🔐 Login required. Please log in manually...")
                await page.pause()
                await page.wait_for_timeout(3000)
            
            # Use the working h3 selector strategy
            results = []
            await page.wait_for_selector("h3", timeout=15000)
            elements = await page.query_selector_all("h3")
            
            for element in elements[:max_results]:
                title = await element.inner_text()
                
                # Find the link - look for parent link
                link = None
                parent_link = await element.evaluate_handle("node => node.closest('a')")
                if parent_link:
                    link = await parent_link.get_attribute("href")
                
                if link and link.startswith("/"):
                    link = "https://console.cloud.google.com" + link
                
                if title.strip() and len(title.strip()) > 5:  # Filter out empty/short titles
                    results.append((title.strip(), link))
            
            print(f"Total results found: {len(results)}")
            return results
            
        except Exception as e:
            print(f"Error in get_gcp_results: {e}")
            return []
            
    async def _extract_products(self, max_results: int) -> List[Dict]:
        """
        Extract product information from the current page
        
        Args:
            max_results: Maximum number of results to extract
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        try:
            # Wait for product cards to load
            await self.page.wait_for_timeout(2000)
            
            # Try different selectors for product cards
            card_selectors = [
                '[data-testid="product-card"]',
                '.product-card',
                '[role="article"]',
                '.marketplace-item',
                '[class*="product"]',
                '[class*="card"]'
            ]
            
            product_cards = []
            for selector in card_selectors:
                try:
                    cards = await self.page.query_selector_all(selector)
                    if cards:
                        product_cards = cards
                        logger.info(f"Found {len(cards)} product cards using selector: {selector}")
                        break
                except:
                    continue
                    
            if not product_cards:
                # Fallback: look for any clickable elements that might be products
                logger.info("No product cards found, looking for alternative selectors")
                # Look for elements with product-like text
                all_elements = await self.page.query_selector_all('*')
                for element in all_elements:
                    try:
                        text = await element.text_content()
                        if text and len(text.strip()) > 10 and len(text.strip()) < 200:
                            # Check if it looks like a product title
                            if any(word in text.lower() for word in ['software', 'service', 'tool', 'platform', 'solution']):
                                product_cards.append(element)
                    except:
                        continue
                        
            # Extract information from each card
            for i, card in enumerate(product_cards[:max_results]):
                try:
                    product_info = await self._extract_product_info(card)
                    if product_info:
                        products.append(product_info)
                except Exception as e:
                    logger.warning(f"Error extracting product {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting products: {e}")
            
        return products
        
    async def _extract_product_info(self, card) -> Optional[Dict]:
        """
        Extract product information from a single card element
        
        Args:
            card: Playwright element representing a product card
            
        Returns:
            Product dictionary or None if extraction fails
        """
        try:
            # Get the text content
            text_content = await card.text_content()
            if not text_content:
                return None
                
            # Clean up the text
            text_content = text_content.strip()
            
            # Try to extract title (usually the first significant text)
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            title = lines[0] if lines else "Unknown Product"
            
            # Try to extract description (longer text)
            description = ""
            for line in lines[1:]:
                if len(line) > 20 and len(line) < 200:
                    description = line
                    break
                    
            # Enhanced link extraction
            link = await self._extract_product_link(card)
                
            # Try to get image
            image = ""
            try:
                img_element = await card.query_selector('img')
                if img_element:
                    image = await img_element.get_attribute('src')
            except:
                pass
                
            return {
                'title': title,
                'description': description,
                'link': link,
                'image': image,
                'source': 'GCP Marketplace'
            }
            
        except Exception as e:
            logger.warning(f"Error extracting product info: {e}")
            return None
    
    async def _extract_product_link(self, card) -> str:
        """
        Enhanced link extraction for GCP Marketplace products
        
        Args:
            card: Playwright element representing a product card
            
        Returns:
            Product URL or empty string if not found
        """
        link = ""
        
        try:
            # Method 1: Look for direct anchor tags within the card
            link_selectors = [
                'a',
                'a[href*="marketplace"]',
                'a[href*="product"]',
                '[role="link"]',
                '[data-testid*="link"]',
                '[class*="link"]'
            ]
            
            for selector in link_selectors:
                try:
                    link_element = await card.query_selector(selector)
                    if link_element:
                        href = await link_element.get_attribute('href')
                        if href:
                            link = href
                            break
                except:
                    continue
            
            # Method 2: Look for clickable elements with data attributes
            if not link:
                try:
                    # GCP often uses data attributes for navigation
                    data_attrs = ['data-product-id', 'data-product-url', 'data-href']
                    for attr in data_attrs:
                        value = await card.get_attribute(attr)
                        if value:
                            link = value
                            break
                except:
                    pass
            
            # Method 3: Look for parent clickable elements
            if not link:
                try:
                    # Check if the card itself or its parent is clickable
                    parent = card
                    for _ in range(3):  # Check up to 3 levels up
                        if parent:
                            # Check if parent has click handler or is a link
                            tag_name = await parent.evaluate('el => el.tagName.toLowerCase()')
                            if tag_name == 'a':
                                href = await parent.get_attribute('href')
                                if href:
                                    link = href
                                    break
                            parent = await parent.query_selector('..')
                except:
                    pass
            
            # Method 4: Look for onclick handlers that might contain URLs
            if not link:
                try:
                    onclick = await card.get_attribute('onclick')
                    if onclick and 'marketplace' in onclick:
                        # Extract URL from onclick handler
                        import re
                        url_match = re.search(r'["\']([^"\']*marketplace[^"\']*)["\']', onclick)
                        if url_match:
                            link = url_match.group(1)
                except:
                    pass
            
            # Normalize the link
            if link:
                # Handle relative URLs
                if link.startswith('/'):
                    link = f"https://console.cloud.google.com{link}"
                elif link.startswith('./'):
                    link = f"https://console.cloud.google.com/marketplace{link[1:]}"
                elif not link.startswith('http'):
                    # Assume it's a relative path
                    link = f"https://console.cloud.google.com/marketplace/{link}"
                
                # Clean up the URL
                link = link.split('#')[0]  # Remove fragments
                link = link.split('?')[0]  # Remove query params for now
                
                logger.info(f"Extracted link: {link}")
            
        except Exception as e:
            logger.warning(f"Error extracting link: {e}")
        
        return link
            
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        """
        Get detailed information about a specific product
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Detailed product information
        """
        try:
            await self.page.goto(product_url)
            await self.page.wait_for_load_state("networkidle")
            
            # Extract detailed information
            details = {}
            
            # Get title
            title_selectors = ['h1', '[data-testid="product-title"]', '.product-title']
            for selector in title_selectors:
                try:
                    title_element = await self.page.query_selector(selector)
                    if title_element:
                        details['title'] = await title_element.text_content()
                        break
                except:
                    continue
                    
            # Get description
            desc_selectors = ['[data-testid="product-description"]', '.product-description', 'p']
            for selector in desc_selectors:
                try:
                    desc_element = await self.page.query_selector(selector)
                    if desc_element:
                        details['description'] = await desc_element.text_content()
                        break
                except:
                    continue
                    
            # Get pricing
            pricing_selectors = ['[data-testid="pricing"]', '.pricing', '[class*="price"]']
            for selector in pricing_selectors:
                try:
                    price_element = await self.page.query_selector(selector)
                    if price_element:
                        details['pricing'] = await price_element.text_content()
                        break
                except:
                    continue
                    
            details['url'] = product_url
            details['source'] = 'GCP Marketplace'
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return None

async def main():
    """Example usage of the GCP Marketplace scraper"""
    async with GCPMarketplaceScraper(headless=False) as scraper:
        # Search for products
        query = "Jira Software"
        products = await scraper.search_products(query, max_results=10)
        
        print(f"\nFound {len(products)} products for '{query}':")
        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product.get('title', 'Unknown')}")
            print(f"   Description: {product.get('description', 'No description')}")
            print(f"   Link: {product.get('link', 'No link')}")
            
        # Get details for first product if available
        if products and products[0].get('link'):
            print(f"\nGetting details for: {products[0]['title']}")
            details = await scraper.get_product_details(products[0]['link'])
            if details:
                print(f"Detailed info: {json.dumps(details, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main()) 