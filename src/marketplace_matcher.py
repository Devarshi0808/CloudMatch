import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import quote_plus, urljoin
import json
from typing import List, Dict, Tuple, Optional
import logging
import subprocess
import sys
import os

# Text processing and matching libraries
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download required NLTK data
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketplaceMatcher:
    def __init__(self):
        self.excel_data = None
        self.vendors = []
        self.solutions_by_vendor = {}
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Headers for web scraping
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def load_excel_data(self, file_path: str) -> bool:
        """Load and process Excel data"""
        try:
            self.excel_data = pd.read_excel(file_path)
            self.vendors = sorted(self.excel_data['vendor'].unique().tolist())
            
            # Group solutions by vendor
            for vendor in self.vendors:
                vendor_solutions = self.excel_data[self.excel_data['vendor'] == vendor]['solution_name'].tolist()
                self.solutions_by_vendor[vendor] = sorted(vendor_solutions)
            
            logger.info(f"Loaded {len(self.excel_data)} entries with {len(self.vendors)} vendors")
            return True
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            return False
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for better matching"""
        if not isinstance(text, str):
            return ""
        
        # Remove special characters, keep alphanumeric and spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove stopwords
        words = text.split()
        words = [word for word in words if word not in self.stop_words]
        
        # Lemmatization
        words = [self.lemmatizer.lemmatize(word) for word in words]
        
        return ' '.join(words)
    
    def fuzzy_string_match(self, text1: str, text2: str) -> float:
        """Calculate fuzzy string similarity"""
        if not text1 or not text2:
            return 0.0
        
        # Use multiple fuzzy matching algorithms
        ratio = fuzz.ratio(text1.lower(), text2.lower())
        partial_ratio = fuzz.partial_ratio(text1.lower(), text2.lower())
        token_sort_ratio = fuzz.token_sort_ratio(text1.lower(), text2.lower())
        token_set_ratio = fuzz.token_set_ratio(text1.lower(), text2.lower())
        
        # Return the highest score
        return max(ratio, partial_ratio, token_sort_ratio, token_set_ratio)
    
    def tfidf_cosine_match(self, query_text: str, candidate_texts: List[str]) -> List[float]:
        """Calculate TF-IDF cosine similarity"""
        if not query_text or not candidate_texts:
            return [0.0] * len(candidate_texts)
        
        try:
            # Preprocess all texts
            processed_query = self.preprocess_text(query_text)
            processed_candidates = [self.preprocess_text(text) for text in candidate_texts]
            
            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words='english',
                ngram_range=(1, 2),  # Unigrams and bigrams
                max_features=1000,
                min_df=1
            )
            
            # Combine all texts for vectorization
            all_texts = [processed_query] + processed_candidates
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Calculate cosine similarity
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
            
            return similarities[0].tolist()
        except Exception as e:
            logger.error(f"Error in TF-IDF calculation: {e}")
            return [0.0] * len(candidate_texts)
    
    def calculate_hybrid_confidence(self, excel_solution: str, marketplace_title: str, vendor_name: str) -> Tuple[float, Dict]:
        """Calculate hybrid confidence score using fuzzy matching and TF-IDF
        If solution is blank, match using vendor name only."""
        scores = {}
        # Vendor-only matching if solution is blank
        if not excel_solution.strip():
            # Fuzzy and TF-IDF between vendor_name and marketplace_title
            fuzzy_score = self.fuzzy_string_match(vendor_name, marketplace_title)
            scores['fuzzy'] = fuzzy_score
            tfidf_scores = self.tfidf_cosine_match(vendor_name, [marketplace_title])
            tfidf_score = tfidf_scores[0] * 100 if tfidf_scores else 0
            scores['tfidf'] = tfidf_score
            final_score = (
                scores['fuzzy'] * 0.60 +
                scores['tfidf'] * 0.40
            )
            return final_score, scores
        # ... existing code ...
        fuzzy_score = self.fuzzy_string_match(excel_solution, marketplace_title)
        scores['fuzzy'] = fuzzy_score
        tfidf_scores = self.tfidf_cosine_match(excel_solution, [marketplace_title])
        tfidf_score = tfidf_scores[0] * 100 if tfidf_scores else 0
        scores['tfidf'] = tfidf_score
        final_score = (
            scores['fuzzy'] * 0.60 +
            scores['tfidf'] * 0.40
        )
        return final_score, scores
    
    def scrape_aws_marketplace(self, search_query: str) -> List[Dict]:
        """Scrape AWS Marketplace for products using headless browser script"""
        results = []
        try:
            # Get the path to the AWS headless scraper
            current_dir = os.path.dirname(os.path.abspath(__file__))
            aws_scraper_path = os.path.join(current_dir, 'scrapers', 'headless', 'aws_headless_scraping.py')
            
            # Call the headless browser script as a subprocess using sys.executable
            process = subprocess.run([
                sys.executable, aws_scraper_path, search_query
            ], capture_output=True, text=True, timeout=30)
            
            if process.returncode != 0:
                logger.error(f"Headless script failed with return code {process.returncode}")
                logger.error(f"Error output: {process.stderr}")
                # Fallback to static scraping
                return self._scrape_aws_marketplace_static(search_query)
            
            output = process.stdout
            logger.info(f"AWS headless script output length: {len(output)}")
            
            # Parse the output for product results
            # The script outputs results in this format:
            # 1. Product Title
            #    Vendor: ...
            #    Link: ...
            #    Description: ...
            current = {}
            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Check if this is a numbered result line (e.g., "1. Product Title")
                if line[0].isdigit() and '. ' in line:
                    if current:
                        if 'link' not in current:
                            current['link'] = ''
                        results.append(current)
                        current = {}
                    current = {
                        'title': line.split('. ', 1)[1] if '. ' in line else line,
                        'marketplace': 'AWS'
                    }
                elif line.lower().startswith("link:") or line.lower().startswith("   link:"):
                    # Robustly extract the link value
                    link_value = line.split(':', 1)[1].strip()
                    if link_value:
                        current['link'] = link_value
                elif line.startswith("   Vendor:"):
                    current['vendor'] = line.split(':', 1)[1].strip()
                elif line.startswith("   Description:"):
                    current['description'] = line.split(':', 1)[1].strip()
            # Add the last result if exists
            if current:
                if 'link' not in current:
                    current['link'] = ''
                results.append(current)
            
            logger.info(f"Parsed {len(results)} AWS products from headless script")
            
        except subprocess.TimeoutExpired:
            logger.warning(f"AWS headless scraping timed out after 30 seconds for '{search_query}', falling back to static scraping")
            # Fallback to static scraping
            return self._scrape_aws_marketplace_static(search_query)
        except Exception as e:
            logger.error(f"Error running headless AWS scraper: {e}")
            logger.error(f"Full error: {str(e)}")
            # Fallback to static scraping
            return self._scrape_aws_marketplace_static(search_query)
        
        return results
    
    def _scrape_aws_marketplace_static(self, search_query: str) -> List[Dict]:
        """Fallback static scraping for AWS Marketplace"""
        results = []
        try:
            # AWS Marketplace search URL
            search_url = f"https://aws.amazon.com/marketplace/search/results?searchTerms={quote_plus(search_query)}"
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for product cards or listings
                product_elements = []
                # Try different selectors for product elements
                selectors = [
                    'div[class*="product"]',
                    'div[class*="card"]', 
                    'div[class*="listing"]',
                    'div[class*="item"]',
                    'article[class*="product"]',
                    'article[class*="card"]'
                ]
                
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        product_elements.extend(elements)
                        break
                
                # If no specific product elements found, try general approach
                if not product_elements:
                    product_elements = soup.find_all(['div', 'article'], limit=20)
                
                for element in product_elements[:10]:  # Limit to first 10 results
                    # Try to extract title
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        
                        # Extract link
                        link = ""
                        if title_elem.name == 'a':
                            link = title_elem.get('href', '')
                        else:
                            link_elem = element.find('a')
                            if link_elem:
                                link = link_elem.get('href', '')
                        
                        # Make sure link is absolute
                        if link and link.startswith('/'):
                            link = urljoin('https://aws.amazon.com', link)
                        
                        # Check if this product matches our search query
                        search_words = search_query.lower().split()
                        title_lower = title.lower()
                        
                        if any(word.lower() in title_lower for word in search_words):
                            results.append({
                                'title': title,
                                'link': link,
                                'marketplace': 'AWS'
                            })
                            logger.info(f"Found AWS product (static): {title}")
            
            logger.info(f"AWS Marketplace (static): Found {len(results)} results for '{search_query}'")
            
        except Exception as e:
            logger.error(f"Error in static AWS scraping: {e}")
        
        return results
    
    def scrape_azure_marketplace(self, search_query: str) -> List[Dict]:
        """Scrape Azure Marketplace for products"""
        results = []
        try:
            # Azure Marketplace search URL - using the correct format
            search_url = f"https://azuremarketplace.microsoft.com/en-us/marketplace/apps?search={quote_plus(search_query)}&page=1"
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                logger.info(f"Azure Marketplace response length: {len(response.content)}")
                
                # Based on the actual HTML structure provided, look for tileContent divs
                tile_contents = soup.find_all('div', class_='tileContent')
                logger.info(f"Found {len(tile_contents)} tileContent elements")
                
                for tile in tile_contents:
                    # Extract title from h3 element with title class
                    title_elem = tile.find('h3', class_='title')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        title_attr = title_elem.get('title', '')
                        
                        # Use title attribute if available, otherwise use text content
                        product_title = title_attr if title_attr else title
                        
                        # Extract provider information - try different selectors
                        provider = ""
                        provider_selectors = [
                            'div[class*="provider"]',
                            'div[id*="labelBy"]',
                            'div[class*="by"]'
                        ]
                        
                        for selector in provider_selectors:
                            provider_elem = tile.select_one(selector)
                            if provider_elem:
                                provider = provider_elem.get_text(strip=True)
                                break
                        
                        # If no provider found, try looking for text that starts with "By "
                        if not provider:
                            all_text = tile.get_text()
                            by_match = re.search(r'By\s+([^\n\r]+)', all_text)
                            if by_match:
                                provider = by_match.group(1).strip()
                        
                        # Extract description
                        desc_elem = tile.find('div', class_='description')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        # Extract the actual product link - look for anchor tags within the tile
                        product_link = ""
                        link_elem = tile.find('a')
                        if link_elem:
                            href = link_elem.get('href', '')
                            if href:
                                # Make sure it's a full URL
                                if href.startswith('/'):
                                    product_link = urljoin('https://azuremarketplace.microsoft.com', href)
                                elif href.startswith('http'):
                                    product_link = href
                                else:
                                    product_link = f"https://azuremarketplace.microsoft.com{href}"
                        
                        # If no direct link found, try to find it in the title element's parent
                        if not product_link and title_elem:
                            parent_link = title_elem.find_parent('a')
                            if parent_link:
                                href = parent_link.get('href', '')
                                if href:
                                    if href.startswith('/'):
                                        product_link = urljoin('https://azuremarketplace.microsoft.com', href)
                                    elif href.startswith('http'):
                                        product_link = href
                                    else:
                                        product_link = f"https://azuremarketplace.microsoft.com{href}"
                        
                        # Check if this product matches our search query
                        search_words = search_query.lower().split()
                        title_lower = product_title.lower()
                        
                        # Check if any search word is in the title
                        if any(word.lower() in title_lower for word in search_words):
                            # If no specific product link found, fall back to search link
                            if not product_link:
                                product_link = f"https://azuremarketplace.microsoft.com/en-us/marketplace/apps?search={quote_plus(product_title)}"
                            
                            results.append({
                                'title': product_title,
                                'link': product_link,
                                'marketplace': 'Azure',
                                'provider': provider,
                                'description': description
                            })
                            logger.info(f"Found Azure product: {product_title} by {provider} - Link: {product_link}")
                
                # If no results found with tileContent, try alternative approach
                if not results:
                    logger.info("No results found with tileContent, trying alternative approach")
                    
                    # Look for any h3 elements with title class
                    title_elements = soup.find_all('h3', class_='title')
                    for title_elem in title_elements:
                        title = title_elem.get_text(strip=True)
                        title_attr = title_elem.get('title', '')
                        product_title = title_attr if title_attr else title
                        
                        # Try to find the product link
                        product_link = ""
                        parent_link = title_elem.find_parent('a')
                        if parent_link:
                            href = parent_link.get('href', '')
                            if href:
                                if href.startswith('/'):
                                    product_link = urljoin('https://azuremarketplace.microsoft.com', href)
                                elif href.startswith('http'):
                                    product_link = href
                                else:
                                    product_link = f"https://azuremarketplace.microsoft.com{href}"
                        
                        # Check if this product matches our search query
                        search_words = search_query.lower().split()
                        title_lower = product_title.lower()
                        
                        if any(word.lower() in title_lower for word in search_words):
                            # If no specific product link found, fall back to search link
                            if not product_link:
                                product_link = f"https://azuremarketplace.microsoft.com/en-us/marketplace/apps?search={quote_plus(product_title)}"
                            
                            results.append({
                                'title': product_title,
                                'link': product_link,
                                'marketplace': 'Azure'
                            })
                            logger.info(f"Found Azure product (alternative): {product_title} - Link: {product_link}")
            
            logger.info(f"Azure Marketplace: Found {len(results)} results for '{search_query}'")
            
        except Exception as e:
            logger.error(f"Error scraping Azure Marketplace: {e}")
            logger.error(f"Full error: {str(e)}")
        
        return results
    
    def scrape_gcp_marketplace(self, search_query: str) -> List[Dict]:
        """Scrape GCP Marketplace for products using headless browser"""
        results = []
        try:
            # Import the headless scraper
            import asyncio
            from scrapers.headless.gcp_headless_scraping import GCPMarketplaceScraper
            
            # Run the headless scraper in a new event loop
            async def run_scraper():
                async with GCPMarketplaceScraper(headless=True) as scraper:
                    return await scraper.search_products(search_query, max_results=10)
            
            # Run the async function
            products = asyncio.run(run_scraper())
            
            # Convert the results to our format
            for product in products:
                results.append({
                    'title': product.get('title', ''),
                    'link': product.get('link', ''),
                    'marketplace': 'GCP',
                    'vendor': '',  # GCP scraper doesn't extract vendor separately
                    'description': product.get('description', '')
                })
            
            logger.info(f"GCP Marketplace (headless): Found {len(results)} results for '{search_query}'")
            
        except Exception as e:
            logger.error(f"Error scraping GCP Marketplace with headless browser: {e}")
            # Fallback to static scraping if headless fails
            logger.info("Falling back to static GCP scraping")
            results = self._scrape_gcp_marketplace_static(search_query)
        
        return results
    
    def _scrape_gcp_marketplace_static(self, search_query: str) -> List[Dict]:
        """Fallback static scraping for GCP Marketplace"""
        results = []
        try:
            # GCP Marketplace search URL
            search_url = f"https://console.cloud.google.com/marketplace/search?q={quote_plus(search_query)}"
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                logger.info(f"GCP Marketplace static response length: {len(response.content)}")
                
                # Based on the actual HTML structure, look for mp-search-results-list-item elements
                product_items = soup.find_all('mp-search-results-list-item')
                logger.info(f"Found {len(product_items)} GCP product items")
                
                for item in product_items[:10]:  # Limit to first 10 results
                    # Extract title from h3 element with cfc-truncated-text class
                    title_elem = item.find('h3', class_='cfc-truncated-text')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        
                        # Extract vendor/provider from h4 element
                        vendor_elem = item.find('h4', class_='cfc-truncated-text')
                        vendor = vendor_elem.get_text(strip=True) if vendor_elem else ""
                        
                        # Extract description from p element
                        desc_elem = item.find('p', class_='cfc-truncated-text-multi-line-3')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        # Extract link from the anchor tag
                        link_elem = item.find('a', class_='mp-search-results-list-item-link')
                        link = ""
                        if link_elem:
                            link = link_elem.get('href', '')
                            # Make sure it's a full URL
                            if link.startswith('/'):
                                link = urljoin('https://console.cloud.google.com', link)
                        
                        # Check if this product matches our search query
                        search_words = search_query.lower().split()
                        title_lower = title.lower()
                        
                        # Check if any search word is in the title
                        if any(word.lower() in title_lower for word in search_words):
                            results.append({
                                'title': title,
                                'link': link,
                                'marketplace': 'GCP',
                                'vendor': vendor,
                                'description': description
                            })
                            logger.info(f"Found GCP product: {title} by {vendor}")
                
                # If no results found with the specific structure, try alternative approach
                if not results:
                    logger.info("No results found with GCP Angular structure, trying alternative approach")
                    
                    # Look for any h3 elements that might be product titles
                    title_elements = soup.find_all('h3')
                    for title_elem in title_elements:
                        title = title_elem.get_text(strip=True)
                        
                        # Check if this product matches our search query
                        search_words = search_query.lower().split()
                        title_lower = title.lower()
                        
                        if any(word.lower() in title_lower for word in search_words):
                            # Try to find a parent link
                            parent_link = title_elem.find_parent('a')
                            link = ""
                            if parent_link:
                                link = parent_link.get('href', '')
                                if link.startswith('/'):
                                    link = urljoin('https://console.cloud.google.com', link)
                            
                            results.append({
                                'title': title,
                                'link': link,
                                'marketplace': 'GCP'
                            })
                            logger.info(f"Found GCP product (alternative): {title}")
            
            logger.info(f"GCP Marketplace (static): Found {len(results)} results for '{search_query}'")
            
        except Exception as e:
            logger.error(f"Error in static GCP Marketplace scraping: {e}")
            logger.error(f"Full error: {str(e)}")
        
        return results
    
    def map_vendor_to_closest(self, input_vendor: str) -> Tuple[str, float]:
        """Map input vendor to closest vendor in our Excel data"""
        if not input_vendor or not self.vendors:
            return input_vendor, 0.0
        
        # Try exact match first
        if input_vendor in self.vendors:
            return input_vendor, 100.0
        
        # Use fuzzy matching to find closest vendor
        best_match = input_vendor  # Default to input
        best_score = 0.0
        
        for vendor in self.vendors:
            score = self.fuzzy_string_match(input_vendor.lower(), vendor.lower())
            if score > best_score:
                best_score = score
                best_match = vendor
        
        # Return best match if score is above threshold
        if best_score >= 50:  # 50% similarity threshold
            return best_match, best_score
        
        return input_vendor, 0.0
    
    def map_solution_to_closest(self, vendor: str, input_solution: str) -> Tuple[str, float]:
        """Map input solution to closest solution for the given vendor"""
        if not input_solution or not vendor:
            return input_solution, 0.0
        
        # Get solutions for this vendor
        vendor_solutions = self.get_solutions_for_vendor(vendor)
        if not vendor_solutions:
            return input_solution, 0.0
        
        # Try exact match first
        if input_solution in vendor_solutions:
            return input_solution, 100.0
        
        # Use fuzzy matching to find closest solution
        best_match = input_solution  # Default to input
        best_score = 0.0
        
        for solution in vendor_solutions:
            score = self.fuzzy_string_match(input_solution.lower(), solution.lower())
            if score > best_score:
                best_score = score
                best_match = solution
        
        # Return best match if score is above threshold
        if best_score >= 50:  # 50% similarity threshold
            return best_match, best_score
        
        return input_solution, 0.0
    
    def search_marketplaces(self, vendor: str, solution: str) -> Dict:
        """Search all marketplaces for a vendor-solution combination"""
        # Map vendor to closest match in our data
        mapped_vendor, vendor_match_score = self.map_vendor_to_closest(vendor)
        
        # Map solution to closest match for the mapped vendor
        mapped_solution, solution_match_score = self.map_solution_to_closest(mapped_vendor, solution)
        
        results = {
            'original_vendor': vendor,
            'original_solution': solution,
            'mapped_vendor': mapped_vendor,
            'mapped_solution': mapped_solution,
            'vendor_match_score': vendor_match_score,
            'solution_match_score': solution_match_score,
            'aws_results': [],
            'azure_results': [],
            'gcp_results': [],
            'summary': {}
        }
        
        # Create search queries - use mapped values if available, otherwise use originals
        search_vendor = mapped_vendor if vendor_match_score > 0 else vendor
        search_solution = mapped_solution if solution_match_score > 0 else solution
        
        search_queries = [
            f"{search_vendor} {search_solution}",
            search_solution,
            f"{search_vendor} {search_solution.split()[0]}" if search_solution else search_vendor
        ]
        
        logger.info(f"Searching marketplaces for: {vendor} - {solution}")
        logger.info(f"Mapped to: {mapped_vendor} - {mapped_solution} (vendor: {vendor_match_score:.1f}%, solution: {solution_match_score:.1f}%)")
        
        # Search AWS Marketplace
        for query in search_queries:
            aws_results = self.scrape_aws_marketplace(query)
            results['aws_results'].extend(aws_results)
            time.sleep(1)  # Rate limiting
        
        # Search Azure Marketplace
        for query in search_queries:
            azure_results = self.scrape_azure_marketplace(query)
            results['azure_results'].extend(azure_results)
            time.sleep(1)  # Rate limiting
        
        # Search GCP Marketplace
        for query in search_queries:
            gcp_results = self.scrape_gcp_marketplace(query)
            results['gcp_results'].extend(gcp_results)
            time.sleep(1)  # Rate limiting
        
        # Remove duplicates and calculate confidence scores
        # Use mapped solution for confidence calculation if available
        confidence_solution = mapped_solution if solution_match_score > 0 else solution
        results['aws_results'] = self.remove_duplicates_and_score(results['aws_results'], search_vendor, confidence_solution)
        results['azure_results'] = self.remove_duplicates_and_score(results['azure_results'], search_vendor, confidence_solution)
        results['gcp_results'] = self.remove_duplicates_and_score(results['gcp_results'], search_vendor, confidence_solution)
        
        # Create summary
        results['summary'] = self.create_summary(results)
        
        return results
    
    def remove_duplicates_and_score(self, results: List[Dict], vendor: str, solution: str) -> List[Dict]:
        """Remove duplicates and add confidence scores. If solution is blank, match using vendor only."""
        seen_titles = set()
        unique_results = []
        for result in results:
            title = result['title']
            if title not in seen_titles:
                seen_titles.add(title)
                # If solution is blank, pass empty string for solution and use vendor for matching
                confidence, score_breakdown = self.calculate_hybrid_confidence(solution, title, vendor)
                result['confidence'] = confidence
                result['score_breakdown'] = score_breakdown
                unique_results.append(result)
        unique_results.sort(key=lambda x: x['confidence'], reverse=True)
        return unique_results
    
    def create_summary(self, results: Dict) -> Dict:
        """Create a summary of the search results"""
        summary = {
            'best_matches': []
        }
        
        all_results = results['aws_results'] + results['azure_results'] + results['gcp_results']
        
        for result in all_results:
            confidence = result['confidence']
            
            # Add to best matches if confidence > 30
            if confidence > 30:
                summary['best_matches'].append({
                    'marketplace': result['marketplace'],
                    'title': result['title'],
                    'confidence': confidence,
                    'link': result.get('link', ''),
                    'score_breakdown': result.get('score_breakdown', {})
                })
        
        # Sort best matches by confidence
        summary['best_matches'].sort(key=lambda x: x['confidence'], reverse=True)
        
        return summary
    
    def get_vendors(self) -> List[str]:
        """Get list of available vendors"""
        return self.vendors
    
    def get_solutions_for_vendor(self, vendor: str) -> List[str]:
        """Get solutions for a specific vendor"""
        return self.solutions_by_vendor.get(vendor, []) 
    
    def is_in_excel(self, vendor: str, solution: str) -> bool:
        """Check if the given vendor and/or solution is present in the Excel data"""
        if self.excel_data is None:
            return False
        vendor = vendor.strip().lower() if vendor else ""
        solution = solution.strip().lower() if solution else ""
        if vendor and solution:
            return not self.excel_data[
                (self.excel_data['vendor'].str.lower() == vendor) &
                (self.excel_data['solution_name'].str.lower() == solution)
            ].empty
        elif vendor:
            return not self.excel_data[
                (self.excel_data['vendor'].str.lower() == vendor)
            ].empty
        elif solution:
            return not self.excel_data[
                (self.excel_data['solution_name'].str.lower() == solution)
            ].empty
        return False 