# ☁️ Cloud Marketplace Matcher

An intelligent system that matches vendor products from an Excel file with listings across AWS, Azure, and GCP marketplaces using advanced text matching algorithms.

## 🚀 Features

- **Interactive Web Interface**: User-friendly Streamlit app for vendor and solution selection
- **Multi-Algorithm Matching**: Combines fuzzy matching, TF-IDF cosine similarity, and word embeddings
- **Three Cloud Marketplaces**: Searches AWS, Azure, and GCP marketplaces simultaneously
- **Confidence Scoring**: Detailed confidence scores with algorithm breakdown
- **Direct Product Links**: Extracts actual marketplace product URLs
- **Alternative Suggestions**: Suggests alternatives when exact matches aren't found

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or download the project files**
   ```bash
   # Make sure you have these files in your directory:
   # - Vendors_and_Products.xlsx
   # - marketplace_matcher.py
   # - app.py
   # - requirements.txt
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download NLTK data** (if not already downloaded)
   ```python
   import nltk
   nltk.download('stopwords')
   nltk.download('wordnet')
   ```

## 📊 Data Format

The system expects an Excel file (`Vendors_and_Products.xlsx`) with the following structure:

| vendor | solution_name |
|--------|---------------|
| Adobe | Adobe Creative Cloud |
| Salesforce | Sales Cloud |
| ServiceNow | IT Service Management |
| ... | ... |

## 🎯 Usage

### Web Interface (Recommended)

1. **Start the Streamlit app**
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** and navigate to the provided URL (usually `http://localhost:8501`)

3. **Select vendor and solution** from the dropdown menus in the sidebar

4. **Click "Search Marketplaces"** to find matches

5. **View results** with confidence scores and direct links

### Command Line Testing

1. **Run the test script** to verify functionality
   ```bash
   python test_matcher.py
   ```

2. **Test individual components**
   ```python
   from marketplace_matcher import MarketplaceMatcher
   
   matcher = MarketplaceMatcher()
   matcher.load_excel_data('Vendors_and_Products.xlsx')
   
   # Get available vendors
   vendors = matcher.get_vendors()
   print(f"Available vendors: {vendors}")
   
   # Get solutions for a vendor
   solutions = matcher.get_solutions_for_vendor('Adobe')
   print(f"Adobe solutions: {solutions}")
   ```

## 🔍 Matching Algorithm

The system uses a hybrid approach combining multiple algorithms:

### 1. Fuzzy String Matching (30% weight)
- Levenshtein distance
- Jaro-Winkler similarity
- Token-based matching

### 2. TF-IDF Cosine Similarity (40% weight)
- Term frequency-inverse document frequency
- Cosine similarity between text vectors
- Handles word importance and order

### 3. Word Embedding Similarity (20% weight)
- Word overlap analysis
- Semantic similarity understanding
- Handles synonyms and related terms

### 4. Vendor Name Matching (10% weight)
- Direct vendor name presence
- Brand recognition

### Confidence Levels
- **95-100%**: Exact/Perfect match
- **85-94%**: Very high confidence
- **70-84%**: High confidence
- **50-69%**: Medium confidence
- **30-49%**: Low confidence
- **<30%**: No match (suggests alternatives)

## 📈 Results Display

The system provides:

1. **Summary Metrics**: Total matches, confidence distribution
2. **Best Matches**: Top results with confidence scores
3. **Detailed Breakdown**: Algorithm-specific scores
4. **Direct Links**: Actual marketplace product URLs
5. **Alternative Suggestions**: When no good matches found

## 🔧 Configuration

### Rate Limiting
The system includes built-in rate limiting to respect marketplace websites:
```python
time.sleep(1)  # 1 second delay between requests
```

### Search Queries
Multiple search strategies are used:
- `{vendor} {solution}` - Full vendor and solution name
- `{solution}` - Solution name only
- `{vendor} {first_word_of_solution}` - Vendor with first word

### Result Limits
- Maximum 10 results per marketplace per query
- Top 5 results displayed in detailed view
- All results included in summary statistics

## 🚨 Important Notes

### Web Scraping
- The system respects website terms and includes rate limiting
- Some marketplaces may block automated requests
- Results depend on current marketplace content

### Data Accuracy
- Confidence scores are algorithmic estimates
- Manual verification of important matches is recommended
- Marketplace content changes over time

### Alternative Suggestions
When no good matches are found, the system suggests:
- Category-based alternatives
- Different search strategies
- Related product categories

## 🐛 Troubleshooting

### Common Issues

1. **Excel file not found**
   - Ensure `Vendors_and_Products.xlsx` is in the same directory
   - Check file permissions

2. **Import errors**
   - Install all dependencies: `pip install -r requirements.txt`
   - Check Python version (3.8+ required)

3. **No search results**
   - Check internet connection
   - Verify marketplace URLs are accessible
   - Try different vendor/solution combinations

4. **Low confidence scores**
   - Try searching with just the vendor name
   - Check for alternative product names
   - Verify spelling and formatting

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Example Output

```
Search Results for: Adobe - Adobe Creative Cloud

Summary:
- Total Matches: 12
- High Confidence: 3
- Medium Confidence: 5
- Low Confidence: 4

Best Matches:
1. Adobe Creative Cloud (AWS Marketplace) - 95.2% confidence
2. Adobe Creative Cloud Platform (Azure Marketplace) - 87.1% confidence
3. Adobe Creative Suite (GCP Marketplace) - 82.3% confidence

Score Breakdown for #1:
- Fuzzy Match: 100.0%
- TF-IDF: 92.5%
- Word Overlap: 100.0%
- Vendor Match: 100.0%
```

## 🤝 Contributing

To improve the system:

1. **Enhance matching algorithms**
2. **Add more marketplace support**
3. **Improve web scraping robustness**
4. **Add more alternative suggestion logic**
5. **Enhance the user interface**

## 📄 License

This project is for educational and research purposes. Please respect the terms of service of the marketplace websites being accessed.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Run the test script to verify functionality
3. Review the error logs for specific issues
4. Ensure all dependencies are properly installed 