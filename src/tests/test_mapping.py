#!/usr/bin/env python3
"""
Test vendor and solution mapping functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from marketplace_matcher import MarketplaceMatcher

def test_mapping():
    """Test vendor and solution mapping"""
    print("🧪 Testing Vendor and Solution Mapping")
    print("=" * 50)
    
    # Initialize matcher
    matcher = MarketplaceMatcher()
    if not matcher.load_excel_data("data/Vendors_and_Products.xlsx"):
        print("❌ Failed to load Excel data")
        return
    
    print("✅ Excel data loaded successfully")
    
    # Test cases
    test_cases = [
        # (input_vendor, input_solution, expected_vendor, expected_solution)
        ("Atlassian", "Jira", "Atlassian", "Jira Software"),  # Exact vendor, partial solution
        ("Microsoft", "Office", "Miro", "Office 365"),        # Partial vendor, partial solution
        ("GitLab", "GitLab", "GitLab", "GitLab Ultimate"),    # Exact vendor, partial solution
        ("Adobe", "Photoshop", "Adobe", "Adobe Photoshop"),   # Exact vendor, exact solution
        ("Unknown Vendor", "Unknown Product", "Unknown Vendor", "Unknown Product"),  # No matches
        ("Slack", "Slack", "Slack Technologies", "Slack"),    # Partial vendor, exact solution
    ]
    
    for i, (input_vendor, input_solution, expected_vendor, expected_solution) in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {input_vendor} - {input_solution}")
        print("-" * 40)
        
        # Test vendor mapping
        mapped_vendor, vendor_score = matcher.map_vendor_to_closest(input_vendor)
        print(f"Vendor mapping: {input_vendor} → {mapped_vendor} ({vendor_score:.1f}%)")
        
        # Test solution mapping
        mapped_solution, solution_score = matcher.map_solution_to_closest(mapped_vendor, input_solution)
        print(f"Solution mapping: {input_solution} → {mapped_solution} ({solution_score:.1f}%)")
        
        # Test full search
        print("Searching marketplaces...")
        results = matcher.search_marketplaces(input_vendor, input_solution)
        
        print(f"Results: AWS={len(results['aws_results'])}, Azure={len(results['azure_results'])}, GCP={len(results['gcp_results'])}")
        
        if results['summary']['best_matches']:
            top_match = results['summary']['best_matches'][0]
            print(f"Top match: {top_match['title']} ({top_match['confidence']:.1f}%)")
        else:
            print("No matches found")
    
    print("\n✅ Mapping tests completed!")

if __name__ == "__main__":
    test_mapping() 