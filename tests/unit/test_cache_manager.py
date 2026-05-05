"""
Cache Manager 单元测试
"""
import pytest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cache_manager.base import CacheConfig, EvictionPolicy
from cache_manager.l1 import L1Cache


class TestCacheConfig:
    def test_default_config(self):
        config = CacheConfig()
        assert config.max_size == 1000
        assert config.ttl_seconds == 3600
        assert config.eviction_policy == EvictionPolicy.LRU


class TestL1Cache:
    def test_set_get(self):
        cache = L1Cache(max_size=100)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_cache_miss(self):
        cache = L1Cache(max_size=100)
        assert cache.get("nonexistent") is None
    
    def test_cache_expiration(self):
        cache = L1Cache(max_size=100, ttl_seconds=1)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_cache_eviction(self):
        cache = L1Cache(max_size=3)
        for i in range(5):
            cache.set(f"key{i}", f"value{i}")
        assert cache.get("key0") is None
        assert cache.get("key4") == "value4"
    
    def test_cache_delete(self):
        cache = L1Cache(max_size=100)
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_cache_clear(self):
        cache = L1Cache(max_size=100)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_stats(self):
        cache = L1Cache(max_size=100)
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("key2")
        stats = cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1
