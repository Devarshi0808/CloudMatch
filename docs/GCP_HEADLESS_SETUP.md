# GCP Marketplace Headless Browser Scraping Setup

This guide explains how to set up and use headless browser scraping for Google Cloud Platform (GCP) Marketplace to overcome the limitations of static HTML scraping.

## Why Headless Browser Scraping?

GCP Marketplace loads product data dynamically using JavaScript, which means:
- Static HTML scraping often returns empty or incomplete results
- Product listings are loaded after the initial page load
- Search functionality requires JavaScript execution
- Headless browsers can interact with the page like a real user

## Prerequisites

1. **Python 3.7+** installed
2. **pip** package manager
3. **Internet connection** for downloading browsers

## Installation Steps

### 1. Install Dependencies

```bash
# Install all required packages including Playwright
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
# Run the setup script
python setup_playwright.py

# Or manually install browsers
python -m playwright install chromium
```

### 3. Verify Installation

```bash
# Test the installation
python test_gcp_scraping.py
```

## Usage

### Basic Usage

```python
import asyncio
from gcp_headless_scraping import GCPMarketplaceScraper

async def search_gcp():
    async with GCPMarketplaceScraper(headless=True) as scraper:
        products = await scraper.search_products("Jira Software", max_results=10)
        for product in products:
            print(f"Title: {product['title']}")
            print(f"Description: {product['description']}")
            print(f"Link: {product['link']}")

# Run the search
asyncio.run(search_gcp())
```

### Integration with Marketplace Matcher

The headless scraper is automatically integrated into the main marketplace matcher:

```python
from marketplace_matcher import MarketplaceMatcher

matcher = MarketplaceMatcher()
matcher.load_excel_data("Vendors_and_Products.xlsx")

# This will now use headless browser for GCP
results = matcher.search_marketplaces("Atlassian", "Jira Software")
```

## Features

### 1. **Automatic Search Input Detection**
- Tries multiple selectors to find the search input
- Handles different GCP Marketplace layouts
- Fallback mechanisms for various page structures

### 2. **Dynamic Content Extraction**
- Waits for JavaScript to load product data
- Extracts titles, descriptions, and links
- Handles pagination and infinite scroll

### 3. **Robust Error Handling**
- Graceful fallback to static scraping if headless fails
- Timeout handling for slow-loading pages
- Retry mechanisms for network issues

### 4. **Configurable Options**
- `headless=True/False`: Show/hide browser window
- `max_results`: Limit number of results
- Custom user agents and headers

## Configuration Options

### Browser Settings

```python
async with GCPMarketplaceScraper(
    headless=True,  # Run in background (True) or show window (False)
) as scraper:
    # Your scraping code here
```

### Search Parameters

```python
products = await scraper.search_products(
    query="Your Search Term",
    max_results=20  # Number of results to return
)
```

## Troubleshooting

### Common Issues

1. **"Playwright not found"**
   ```bash
   pip install playwright
   python -m playwright install chromium
   ```

2. **"Browser failed to start"**
   - Check if you have sufficient system resources
   - Try running with `headless=False` to see what's happening
   - Ensure no antivirus is blocking the browser

3. **"No search results found"**
   - GCP Marketplace structure may have changed
   - Try different search terms
   - Check if the page is loading correctly

4. **"Timeout errors"**
   - Increase timeout values in the scraper
   - Check your internet connection
   - GCP may be rate-limiting requests

### Debug Mode

Run with visible browser to debug issues:

```python
async with GCPMarketplaceScraper(headless=False) as scraper:
    # This will show the browser window
    products = await scraper.search_products("test")
```

## Performance Considerations

### Rate Limiting
- GCP may rate-limit requests if too frequent
- Add delays between searches: `await asyncio.sleep(2)`
- Use reasonable `max_results` values

### Resource Usage
- Headless browsers use more memory than static scraping
- Close scrapers properly using `async with` context manager
- Consider running multiple scrapers in sequence, not parallel

### Caching
- Consider caching results to avoid repeated scraping
- Store results in a database or file for reuse

## Security and Ethics

### Best Practices
- Respect robots.txt and terms of service
- Don't overload GCP servers with requests
- Use reasonable delays between requests
- Only scrape publicly available data

### Rate Limiting
```python
# Add delays between searches
await asyncio.sleep(2)  # 2 second delay
```

## Advanced Usage

### Custom Selectors

If GCP changes their HTML structure, you can update selectors:

```python
# In gcp_headless_scraping.py, update these arrays:
search_selectors = [
    'input[placeholder*="Search"]',
    'input[aria-label*="Search"]',
    # Add new selectors here
]

card_selectors = [
    '[data-testid="product-card"]',
    '.product-card',
    # Add new selectors here
]
```

### Error Recovery

The scraper includes automatic fallback:

```python
try:
    # Try headless scraping first
    products = await scraper.search_products(query)
except Exception as e:
    # Fallback to static scraping
    products = matcher._scrape_gcp_marketplace_static(query)
```

## Testing

Run the test script to verify everything works:

```bash
python test_gcp_scraping.py
```

This will:
- Test basic search functionality
- Test product details extraction
- Show example results
- Verify the scraper is working correctly

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run with `headless=False` to see what's happening
3. Check the logs for detailed error messages
4. Verify your internet connection and GCP Marketplace access

## Updates

The scraper may need updates if GCP changes their website structure. Check for:
- New HTML selectors
- Changed page layouts
- Updated JavaScript behavior
- New authentication requirements 