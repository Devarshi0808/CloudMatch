# Requires: rapidfuzz (pip install rapidfuzz)
import sqlite3
import json
import time
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from rapidfuzz import fuzz

class SearchCache:
    """
    SQLite-based cache for search results with frequency and recency tracking.
    
    Features:
    - Persistent storage with SQLite database
    - Fuzzy matching for cache keys
    - Automatic eviction of old entries
    - Access count tracking
    - Result type categorization
    - Concurrency-safe operations with WAL mode
    """
    
    def __init__(self, db_path: str = "../data/search_cache.db", max_size: int = 1000, expiry_days: int = 30):
        self.db_path = db_path
        self.max_size = max_size
        self.expiry_days = expiry_days
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the cache database with proper schema"""
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    cache_key TEXT PRIMARY KEY,
                    vendor TEXT NOT NULL,
                    solution TEXT NOT NULL,
                    result_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1,
                    result_type TEXT DEFAULT 'excel_match'
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_last_accessed ON search_cache(last_accessed)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_access_count ON search_cache(access_count)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON search_cache(created_at)")
            
            conn.commit()
    
    def _make_key(self, vendor: str, solution: str) -> str:
        """Create a cache key from vendor and solution"""
        return f"{vendor.lower().strip()}|{solution.lower().strip()}"
    
    def get(self, vendor: str, solution: str) -> Optional[Dict[str, Any]]:
        """Get cached result for vendor/solution pair"""
        cache_key = self._make_key(vendor, solution)
        
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            # Check if entry exists and is not expired
            cursor = conn.execute("""
                SELECT result_data, access_count, result_type 
                FROM search_cache 
                WHERE cache_key = ? AND created_at > ?
            """, (cache_key, datetime.now() - timedelta(days=self.expiry_days)))
            
            row = cursor.fetchone()
            if row:
                result_data, access_count, result_type = row
                
                # Update access count and last accessed time
                conn.execute("""
                    UPDATE search_cache 
                    SET access_count = ?, last_accessed = CURRENT_TIMESTAMP 
                    WHERE cache_key = ?
                """, (access_count + 1, cache_key))
                conn.commit()
                
                return {
                    'result': json.loads(result_data),
                    'access_count': access_count + 1,
                    'result_type': result_type
                }
        
        return None
    
    def set(self, vendor: str, solution: str, result: Dict[str, Any], result_type: str = 'excel_match'):
        """Cache a search result"""
        cache_key = self._make_key(vendor, solution)
        result_json = json.dumps(result)
        
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            # Check if entry already exists
            cursor = conn.execute("SELECT cache_key FROM search_cache WHERE cache_key = ?", (cache_key,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing entry
                conn.execute("""
                    UPDATE search_cache 
                    SET result_data = ?, last_accessed = CURRENT_TIMESTAMP, 
                        access_count = access_count + 1, result_type = ?
                    WHERE cache_key = ?
                """, (result_json, result_type, cache_key))
            else:
                # Insert new entry
                conn.execute("""
                    INSERT INTO search_cache (cache_key, vendor, solution, result_data, result_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (cache_key, vendor, solution, result_json, result_type))
            
            conn.commit()
            
            # Check if we need to evict old entries
            self._evict_if_needed()
    
    def _evict_if_needed(self):
        """Evict least recently/frequently used entries if cache is too large"""
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            # Count total entries
            cursor = conn.execute("SELECT COUNT(*) FROM search_cache")
            count = cursor.fetchone()[0]
            
            if count > self.max_size:
                # Calculate eviction score (lower is better for eviction)
                # Formula: (days_since_last_access * 2) + (1 / access_count)
                conn.execute("""
                    DELETE FROM search_cache 
                    WHERE cache_key IN (
                        SELECT cache_key FROM search_cache 
                        ORDER BY (
                            (julianday('now') - julianday(last_accessed)) * 2 + 
                            (1.0 / access_count)
                        ) DESC 
                        LIMIT ?
                    )
                """, (count - self.max_size + 100,))  # Evict extra to make room
                conn.commit()
    
    def cleanup_expired(self):
        """Remove expired entries from cache"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM search_cache 
                WHERE created_at < ?
            """, (datetime.now() - timedelta(days=self.expiry_days),))
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM search_cache")
            total_entries = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT AVG(access_count) FROM search_cache")
            avg_access = cursor.fetchone()[0] or 0
            
            cursor = conn.execute("""
                SELECT result_type, COUNT(*) 
                FROM search_cache 
                GROUP BY result_type
            """)
            type_counts = dict(cursor.fetchall())
            
            cursor = conn.execute("""
                SELECT vendor, COUNT(*) 
                FROM search_cache 
                GROUP BY vendor 
                ORDER BY COUNT(*) DESC 
                LIMIT 5
            """)
            top_vendors = dict(cursor.fetchall())
            
            return {
                'total_entries': total_entries,
                'avg_access_count': round(avg_access, 2),
                'type_distribution': type_counts,
                'top_vendors': top_vendors
            }
    
    def pre_cache_popular(self, matcher, top_n: int = 20):
        """Pre-cache popular vendor/solution combinations"""
        if matcher.excel_data is None or matcher.excel_data.empty:
            return
        
        # Get vendors with most products (fix column names)
        vendor_counts = matcher.excel_data.groupby('vendor')['solution_name'].count().sort_values(ascending=False)
        
        cached_count = 0
        for vendor in vendor_counts.head(top_n).index:
            solutions = matcher.get_solutions_for_vendor(vendor)
            for solution in solutions[:3]:  # Cache top 3 solutions per vendor
                if not self.get(vendor, solution):
                    try:
                        results = matcher.search_marketplaces(vendor, solution)
                        self.set(vendor, solution, results, 'excel_match')
                        cached_count += 1
                    except Exception as e:
                        print(f"Failed to pre-cache {vendor} - {solution}: {e}")
        
        print(f"Pre-cached {cached_count} popular vendor/solution combinations")

# Global cache instance
_cache_instance = None

def get_cache() -> SearchCache:
    """Get the global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SearchCache()
    return _cache_instance

def get_from_cache(vendor: str, solution: str) -> Optional[Dict[str, Any]]:
    """Get cached result for vendor/solution pair"""
    key = f"{vendor.lower().strip()}|{solution.lower().strip()}"
    print(f"[CACHE] Checking for key: '{key}'")
    result = get_cache().get(vendor, solution)
    if result:
        print(f"[CACHE] HIT for key: '{key}'")
    else:
        print(f"[CACHE] MISS for key: '{key}'")
    return result

def set_in_cache(vendor: str, solution: str, result: Dict[str, Any], result_type: str = 'excel_match'):
    """Cache a search result"""
    key = f"{vendor.lower().strip()}|{solution.lower().strip()}"
    print(f"[CACHE] Writing to cache: '{key}' (type: {result_type})")
    get_cache().set(vendor, solution, result, result_type)

def cleanup_cache():
    """Clean up expired cache entries"""
    get_cache().cleanup_expired()

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return get_cache().get_stats()

def get_from_cache_fuzzy(vendor: str, solution: str, threshold: int = 90) -> Optional[Dict[str, Any]]:
    """
    Get cached result for vendor/solution pair using fuzzy matching on the cache key.
    
    Args:
        vendor: Vendor name to search for
        solution: Solution/product name to search for
        threshold: Minimum similarity score (0-100) for fuzzy matching
        
    Returns:
        Cached result dictionary with 'result', 'access_count', and 'result_type' keys,
        or None if no match found
    """
    norm_vendor = vendor.replace(' ', '').lower().strip()
    norm_solution = solution.replace(' ', '').lower().strip()
    search_key = f"{norm_vendor}|{norm_solution}"
    cache = get_cache()
    # Try exact match first
    result = cache.get(vendor, solution)
    if result:
        print(f"[CACHE] Exact HIT for key: '{search_key}'")
        return result
    # Fuzzy match if exact miss
    with sqlite3.connect(cache.db_path, timeout=10) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.execute("SELECT cache_key FROM search_cache")
        best_score = 0
        best_key = None
        for (key,) in cursor.fetchall():
            score = fuzz.ratio(search_key, key)
            if score > best_score:
                best_score = score
                best_key = key
        if best_score >= threshold:
            print(f"[CACHE] Fuzzy HIT for key: '{search_key}' matched '{best_key}' ({best_score}%)")
            cursor = conn.execute("SELECT result_data, access_count, result_type FROM search_cache WHERE cache_key = ?", (best_key,))
            row = cursor.fetchone()
            if row:
                result_data, access_count, result_type = row
                return {
                    'result': json.loads(result_data),
                    'access_count': access_count,
                    'result_type': result_type
                }
    print(f"[CACHE] MISS for key: '{search_key}'")
    return None 