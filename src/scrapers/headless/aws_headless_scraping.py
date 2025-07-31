#!/usr/bin/env python3
"""
Headless browser scraping for AWS Marketplace using Selenium
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
from urllib.parse import quote_plus
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_aws_marketplace_first_page(query):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    url = f"https://aws.amazon.com/marketplace/search/results?searchTerms={query.replace(' ', '+')}"
    driver.get(url)
    try:
        # Wait for product cards to appear (10s max)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-selection-item='item']"))
        )
        cards = driver.find_elements(By.CSS_SELECTOR, "[data-selection-item='item']")
        for i, card in enumerate(cards[:20], 1):
            try:
                # Try to get the title from h2, h3, or a
                title_elem = None
                for selector in ["h2", "h3", "a"]:
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, selector)
                        if title_elem and title_elem.text.strip():
                            break
                    except Exception:
                        continue
                if not title_elem:
                    continue
                title = title_elem.text.strip()
                # Get the first link in the card
                link_elem = card.find_element(By.CSS_SELECTOR, "a")
                link = link_elem.get_attribute("href")
                print(f"{i}. {title}")
                print(f"   Link: {link}")
            except Exception:
                continue
    finally:
        driver.quit()

def test_aws_headless_scraping():
    """
    Test the headless scraping with GitLab
    """
    search_query = "GitLab"
    print(f"Testing AWS Marketplace headless scraping for: {search_query}")
    print("=" * 60)
    
    scrape_aws_marketplace_first_page(search_query)
    
    print("-" * 40)

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Red Hat Enterprise Linux"
    scrape_aws_marketplace_first_page(query) 