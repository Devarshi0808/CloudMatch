#!/usr/bin/env python3
"""
Test script for the cache functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.cache import get_cache, get_cache_stats, cleanup_cache
from marketplace_matcher import MarketplaceMatcher
import unittest
from src.utils.cache import get_from_cache_fuzzy, set_in_cache

def test_cache():
    """Test the cache functionality"""
    print("🧪 Testing Cache Functionality...")
    
    # Initialize cache
    cache = get_cache()
    print("✅ Cache initialized")
    
    # Test basic operations
    test_vendor = "Microsoft"
    test_solution = "Office 365"
    test_result = {
        "vendor": test_vendor,
        "solution": test_solution,
        "results": ["test1", "test2"]
    }
    
    # Set cache
    cache.set(test_vendor, test_solution, test_result, 'test')
    print("✅ Set cache entry")
    
    # Get cache
    result = cache.get(test_vendor, test_solution)
    if result:
        print("✅ Retrieved cache entry")
        print(f"   Access count: {result['access_count']}")
        print(f"   Result type: {result['result_type']}")
    else:
        print("❌ Failed to retrieve cache entry")
    
    # Test with different case
    result2 = cache.get("microsoft", "office 365")
    if result2:
        print("✅ Case-insensitive cache retrieval works")
    else:
        print("❌ Case-insensitive cache retrieval failed")
    
    # Get stats
    stats = get_cache_stats()
    print("📊 Cache Stats:")
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Avg access count: {stats['avg_access_count']}")
    print(f"   Type distribution: {stats['type_distribution']}")
    
    # Test matcher integration
    print("\n🔍 Testing with MarketplaceMatcher...")
    matcher = MarketplaceMatcher()
    success = matcher.load_excel_data('../data/Vendors_and_Products.xlsx')
    
    if success:
        print("✅ Matcher loaded successfully")
        
        # Test pre-caching
        print("📦 Testing pre-caching...")
        cache.pre_cache_popular(matcher, top_n=3)
        
        # Get updated stats
        stats_after = get_cache_stats()
        print(f"   Entries after pre-caching: {stats_after['total_entries']}")
        
        # Test a real search
        print("🔍 Testing real search...")
        if matcher.is_in_excel("Microsoft", "Office 365"):
            results = matcher.search_marketplaces("Microsoft", "Office 365")
            cache.set("Microsoft", "Office 365", results, 'excel_match')
            print("✅ Real search cached")
        else:
            print("⚠️ Microsoft Office 365 not found in Excel data")
    else:
        print("❌ Failed to load matcher")
    
    print("\n✅ Cache test completed!")

class TestCache(unittest.TestCase):
    """Unit tests for the cache utility functions."""

    def setUp(self):
        cleanup_cache()

    def test_set_and_get_exact(self):
        """Test setting and getting a cache entry with exact match."""
        set_in_cache('TestVendor', 'TestSolution', {'foo': 'bar'}, 'test')
        result = get_from_cache_fuzzy('TestVendor', 'TestSolution')
        self.assertIsNotNone(result)
        if result is not None:
            self.assertEqual(result['result']['foo'], 'bar')

    def test_fuzzy_match(self):
        """Test fuzzy matching for similar vendor/solution keys."""
        set_in_cache('FuzzyVendor', 'FuzzySolution', {'baz': 'qux'}, 'test')
        result = get_from_cache_fuzzy('fuzzy vendor', 'fuzzy solution')
        self.assertIsNotNone(result)
        if result is not None:
            self.assertEqual(result['result']['baz'], 'qux')

    def tearDown(self):
        cleanup_cache()

if __name__ == "__main__":
    test_cache()
    unittest.main() 