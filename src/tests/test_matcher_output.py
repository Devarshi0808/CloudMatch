#!/usr/bin/env python3
"""
Test script to verify the marketplace matcher with improved GCP headless scraping
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from marketplace_matcher import MarketplaceMatcher
import json

def test_matcher_with_gcp():
    """Test the marketplace matcher with GCP headless scraping"""
    
    print("🧪 Testing Marketplace Matcher with GCP Headless Scraping")
    print("=" * 60)
    
    # Initialize the matcher
    matcher = MarketplaceMatcher()
    
    # Load the Excel data
    excel_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'Vendors_and_Products.xlsx')
    if not matcher.load_excel_data(excel_path):
        print("❌ Failed to load Excel data")
        return
    
    print("✅ Excel data loaded successfully")
    print(f"📊 Total vendors: {len(matcher.get_vendors())}")
    
    # Test with some specific vendor-solution combinations
    test_cases = [
        ("Atlassian", "Jira Software"),
        ("Atlassian", "Confluence"),
        ("GitLab", "GitLab"),
        ("Microsoft", "Office 365"),
        ("Slack", "Slack")
    ]
    
    for vendor, solution in test_cases:
        print(f"\n🔍 Testing: {vendor} - {solution}")
        print("-" * 40)
        
        try:
            # Search all marketplaces
            results = matcher.search_marketplaces(vendor, solution)
            
            # Display results
            print(f"📈 AWS Results: {len(results['aws_results'])}")
            print(f"📈 Azure Results: {len(results['azure_results'])}")
            print(f"📈 GCP Results: {len(results['gcp_results'])}")
            
            # Show top GCP results
            if results['gcp_results']:
                print("\n🏆 Top GCP Matches:")
                for i, result in enumerate(results['gcp_results'][:3], 1):
                    confidence = result.get('confidence', 0)
                    title = result.get('title', 'Unknown')
                    link = result.get('link', 'No link')
                    print(f"  {i}. {title}")
                    print(f"     Confidence: {confidence:.2f}")
                    print(f"     Link: {link}")
                    print()
            else:
                print("❌ No GCP results found")
                
        except Exception as e:
            print(f"❌ Error testing {vendor} - {solution}: {e}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_matcher_with_gcp() 