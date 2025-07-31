#!/usr/bin/env python3
"""
Test script for the Marketplace Matcher system
"""

import sys
import os
from marketplace_matcher import MarketplaceMatcher

def test_matcher():
    """Test the marketplace matcher with sample data"""
    print("🧪 Testing Marketplace Matcher System")
    print("=" * 50)
    
    # Initialize matcher
    matcher = MarketplaceMatcher()
    
    # Test 1: Load Excel data
    print("\n1. Testing Excel data loading...")
    success = matcher.load_excel_data('Vendors_and_Products.xlsx')
    if success:
        print("✅ Excel data loaded successfully")
        print(f"   - {len(matcher.vendors)} vendors found")
        print(f"   - {len(matcher.excel_data)} total entries")
    else:
        print("❌ Failed to load Excel data")
        return False
    
    # Test 2: Text preprocessing
    print("\n2. Testing text preprocessing...")
    test_texts = [
        "Adobe Creative Cloud",
        "Salesforce Sales Cloud",
        "ServiceNow IT Service Management"
    ]
    
    for text in test_texts:
        processed = matcher.preprocess_text(text)
        print(f"   '{text}' -> '{processed}'")
    
    # Test 3: Fuzzy matching
    print("\n3. Testing fuzzy matching...")
    test_pairs = [
        ("Adobe Creative Cloud", "Adobe Creative Cloud"),
        ("Adobe Creative Cloud", "Adobe Creative Suite"),
        ("Sales Cloud", "Salesforce Sales Cloud"),
        ("Jira Software", "Atlassian Jira")
    ]
    
    for text1, text2 in test_pairs:
        score = matcher.fuzzy_string_match(text1, text2)
        print(f"   '{text1}' vs '{text2}': {score:.1f}%")
    
    # Test 4: TF-IDF matching
    print("\n4. Testing TF-IDF matching...")
    query = "Adobe Creative Cloud"
    candidates = [
        "Adobe Creative Cloud",
        "Adobe Creative Suite",
        "Creative Cloud Platform",
        "Microsoft Office"
    ]
    
    tfidf_scores = matcher.tfidf_cosine_match(query, candidates)
    for i, score in enumerate(tfidf_scores):
        print(f"   '{query}' vs '{candidates[i]}': {score*100:.1f}%")
    
    # Test 5: Hybrid confidence calculation
    print("\n5. Testing hybrid confidence calculation...")
    test_cases = [
        ("Adobe", "Adobe Creative Cloud", "Adobe Creative Cloud"),
        ("Salesforce", "Sales Cloud", "Salesforce Sales Cloud"),
        ("ServiceNow", "IT Service Management", "ServiceNow ITSM")
    ]
    
    for vendor, solution, title in test_cases:
        confidence, breakdown = matcher.calculate_hybrid_confidence(solution, title, vendor)
        print(f"\n   Vendor: {vendor}")
        print(f"   Solution: {solution}")
        print(f"   Title: {title}")
        print(f"   Final Confidence: {confidence:.1f}%")
        print(f"   Breakdown: Fuzzy={breakdown['fuzzy']:.1f}%, TF-IDF={breakdown['tfidf']:.1f}%, "
              f"Word Overlap={breakdown['embedding']:.1f}%, Vendor={breakdown['vendor']:.1f}%")
    
    # Test 6: Vendor and solution retrieval
    print("\n6. Testing vendor and solution retrieval...")
    vendors = matcher.get_vendors()
    print(f"   Available vendors: {len(vendors)}")
    print(f"   Sample vendors: {vendors[:5]}")
    
    if vendors:
        sample_vendor = vendors[0]
        solutions = matcher.get_solutions_for_vendor(sample_vendor)
        print(f"   Solutions for '{sample_vendor}': {len(solutions)}")
        print(f"   Sample solutions: {solutions[:3]}")
    
    print("\n✅ All tests completed successfully!")
    return True

def test_sample_search():
    """Test a sample search (without actual web scraping)"""
    print("\n🔍 Testing sample search functionality...")
    
    matcher = MarketplaceMatcher()
    success = matcher.load_excel_data('Vendors_and_Products.xlsx')
    
    if not success:
        print("❌ Cannot test search without Excel data")
        return False
    
    # Test with a sample vendor and solution
    vendors = matcher.get_vendors()
    if not vendors:
        print("❌ No vendors found in Excel data")
        return False
    
    sample_vendor = vendors[0]
    solutions = matcher.get_solutions_for_vendor(sample_vendor)
    
    if not solutions:
        print(f"❌ No solutions found for vendor: {sample_vendor}")
        return False
    
    sample_solution = solutions[0]
    
    print(f"   Sample search: {sample_vendor} - {sample_solution}")
    print("   Note: Actual web scraping is disabled in test mode")
    print("   To test full functionality, run the Streamlit app")
    
    return True

if __name__ == "__main__":
    print("Starting Marketplace Matcher Tests...")
    
    # Run basic tests
    if test_matcher():
        print("\n🎉 Basic functionality tests passed!")
    else:
        print("\n❌ Basic functionality tests failed!")
        sys.exit(1)
    
    # Run sample search test
    if test_sample_search():
        print("\n🎉 Sample search test passed!")
    else:
        print("\n❌ Sample search test failed!")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎯 All tests completed! Ready to run the main application.")
    print("To start the web interface, run: streamlit run app.py")
    print("=" * 50) 