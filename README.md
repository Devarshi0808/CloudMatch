# ☁️ CloudMatch 🔍

**One search | All cloud marketplaces | Smarter vendor discovery**

CloudMatch is a modern Streamlit app that matches products and vendors from your Excel sheet with listings on AWS, Azure, and GCP marketplaces. It uses advanced fuzzy matching, confidence scoring, and LLM-powered suggestions to help you discover the best cloud solutions—fast.

---

## 🚀 Features
- **Unified Search:** Search for vendors and solutions across AWS, Azure, and GCP marketplaces in one go.
- **Fuzzy & Advanced Matching:** Finds close matches even with typos or alternate spellings.
- **LLM-Powered Suggestions:** If no match is found, get smart alternatives from an LLM (Ollama).
- **Persistent, Fuzzy Cache:** Results are cached with fuzzy matching for fast, repeatable lookups.
- **Modern UI:** Clean landing page, real marketplace logos, dynamic tips, and a sidebar for search configuration.
- **Robust & Safe:** Handles errors, database locks, and session state issues gracefully.

---

## 🛠️ Setup

1. **Clone the repo:**
   ```bash
   git clone <your-repo-url>
   cd FLYWHL
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Prepare your data:**
   - Place your Excel file (e.g., `Vendors_and_Products.xlsx`) in the `data/` directory.

4. **Run the app:**
   ```bash
   streamlit run src/app.py
   ```

---

## 💡 Usage
- Use the sidebar to search by vendor and solution.
- Click marketplace logos for direct access.
- View feature highlights and dynamic tips at the top.
- Inspect or clear the cache from the sidebar.
- If a product isn't found, CloudMatch will scrape the marketplaces and suggest alternatives using an LLM.

---

## 🧠 How Caching & LLM Suggestions Work
- **Cache:**
  - Results are stored in a persistent SQLite cache with fuzzy key matching (using rapidfuzz).
  - Cache is concurrency-safe (WAL mode, timeout) and can be cleared or inspected from the UI.
  - LLM suggestions are also cached for future use.
- **LLM:**
  - If no match is found in the Excel or cache, the app scrapes the marketplaces and queries an LLM for alternatives.
  - LLM suggestions are shown and stored in the cache for next time.

---

## 🤝 Contributing
- Fork the repo and create a feature branch.
- Make your changes with clear docstrings and comments.
- Run tests (`python -m unittest src/test_cache.py`).
- Submit a pull request!

---

## 📄 License
MIT License. See `LICENSE` for details.

## 🧪 Testing

Run the test suite to verify functionality:

```bash
# Test marketplace matching
python src/tests/test_matcher_output.py

# Test mapping functionality
python src/tests/test_mapping.py

# Test individual scrapers
python src/tests/test_aws_scraping.py
python src/tests/test_azure_scraping.py
python src/tests/test_gcp_scraping.py
```

## 📁 Project Structure

```
FLYWHL/
├── main.py                          # Main entry point
├── requirements.txt                 # Python dependencies
├── data/
│   └── Vendors_and_Products.xlsx   # Vendor and product data
├── src/
│   ├── app.py                      # Streamlit application
│   ├── marketplace_matcher.py      # Core matching logic
│   ├── scrapers/
│   │   └── headless/               # Headless browser scrapers
│   │       ├── aws_headless_scraping.py
│   │       └── gcp_headless_scraping.py
│   ├── tests/                      # Test files
│   └── utils/                      # Utility functions
└── docs/                           # Documentation
```

## 🔍 Search Examples

### Exact Matches
- **Input**: "Atlassian" + "Jira"
- **Mapping**: Atlassian (100%) → Jira Software (100%)
- **Result**: High confidence matches across all marketplaces

### Partial Matches
- **Input**: "Microsoft" + "Office"
- **Mapping**: Miro (75%) → Miro Online Whiteboard (50%)
- **Result**: Still finds relevant products with mapping information

### Unknown Products
- **Input**: "Unknown Vendor" + "Unknown Product"
- **Mapping**: Pendo (80%) → Unknown Product (0%)
- **Result**: Searches marketplaces directly for the input terms

## 🛠️ Technical Details

### Scraping Methods
- **AWS Marketplace**: Headless browser with fallback to static HTML
- **Azure Marketplace**: Direct HTML scraping with BeautifulSoup
- **GCP Marketplace**: Headless browser with Playwright

### Performance
- Parallel marketplace searching
- Rate limiting to avoid blocking
- Caching for repeated searches
- Timeout handling with fallbacks

## 🆘 Support

For issues and questions:
1. Check the documentation in `docs/`
2. Review existing issues
3. Create a new issue with detailed information

---

**Built with ❤️ for cloud marketplace discovery** 