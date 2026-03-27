#!/usr/bin/env python3
"""
多级缓存 - Multi-Level Cache

缓存策略：
1. LRU 内存缓存（最快）
2. SQLite 持久缓存（持久化）
3. 混合模式（自动降级）
"""

import hashlib
import json
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class LRUCache:
    """
    LRU 内存缓存
    
    特点：
    - 内存级，速度极快
    - LRU 淘汰策略
    - 自动过期
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.cache = OrderedDict()  # key -> (value, timestamp)
    
    def _make_key(self, query: str, top_k: int = 10) -> str:
        """生成缓存 key"""
        raw = f"{query}:{top_k}"
        return hashlib.md5(raw.encode()).hexdigest()
    
    def get(self, query: str, top_k: int = 10) -> Optional[List[Dict]]:
        """获取缓存"""
        key = self._make_key(query, top_k)
        
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        
        # 检查过期
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None
        
        # 移到末尾（最近使用）
        self.cache.move_to_end(key)
        
        return value
    
    def set(self, query: str, results: List[Dict], top_k: int = 10):
        """设置缓存"""
        key = self._make_key(query, top_k)
        
        # 如果已存在，移除旧位置
        if key in self.cache:
            del self.cache[key]
        
        # 添加到末尾
        self.cache[key] = (results, time.time())
        
        # 检查大小，超出则淘汰最旧的
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
    
    def stats(self) -> Dict:
        """缓存统计"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl
        }


class SQLiteCache:
    """
    SQLite 持久缓存
    
    特点：
    - 持久化，重启后不丢失
    - 支持更大缓存
    - 跨进程共享
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            WORKSPACE = Path.home() / ".openclaw" / "workspace"
            db_path = str(WORKSPACE / "memory" / "cache.db")
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        import sqlite3
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_cache (
                key TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                top_k INTEGER NOT NULL,
                results TEXT NOT NULL,
                created_at TEXT NOT NULL,
                accessed_at TEXT NOT NULL,
                hit_count INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_query ON query_cache(query)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_accessed ON query_cache(accessed_at)
        """)
        
        self.conn.commit()
    
    def _make_key(self, query: str, top_k: int = 10) -> str:
        """生成缓存 key"""
        raw = f"{query}:{top_k}"
        return hashlib.md5(raw.encode()).hexdigest()
    
    def get(self, query: str, top_k: int = 10) -> Optional[List[Dict]]:
        """获取缓存"""
        key = self._make_key(query, top_k)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT results, created_at, hit_count
            FROM query_cache
            WHERE key = ?
        """, (key,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        results = json.loads(row["results"])
        hit_count = row["hit_count"] + 1
        
        # 更新访问时间
        cursor.execute("""
            UPDATE query_cache
            SET accessed_at = ?, hit_count = ?
            WHERE key = ?
        """, (datetime.now().isoformat(), hit_count, key))
        
        self.conn.commit()
        
        return results
    
    def set(self, query: str, results: List[Dict], top_k: int = 10):
        """设置缓存"""
        key = self._make_key(query, top_k)
        now = datetime.now().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO query_cache
            (key, query, top_k, results, created_at, accessed_at, hit_count)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (key, query, top_k, json.dumps(results, ensure_ascii=False), now, now))
        
        self.conn.commit()
    
    def clear(self, older_than_days: int = 7):
        """清空旧缓存"""
        cursor = self.conn.cursor()
        cutoff = (datetime.now() - timedelta(days=older_than_days)).isoformat()
        cursor.execute("DELETE FROM query_cache WHERE accessed_at < ?", (cutoff,))
        self.conn.commit()
        return cursor.rowcount
    
    def stats(self) -> Dict:
        """缓存统计"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM query_cache")
        total = cursor.fetchone()["total"]
        
        cursor.execute("SELECT SUM(hit_count) as hits FROM query_cache")
        hits = cursor.fetchone()["hits"] or 0
        
        return {
            "total_entries": total,
            "total_hits": hits,
            "hit_rate": hits / total if total > 0 else 0
        }
    
    def close(self):
        """关闭连接"""
        if hasattr(self, 'conn'):
            self.conn.close()


class HybridCache:
    """
    混合缓存（推荐）
    
    策略：
    1. 先查 LRU 内存缓存（最快）
    2. 未命中则查 SQLite 缓存
    3. 写入时同时写入两级缓存
    """
    
    def __init__(self, lru_size: int = 500, lru_ttl: int = 3600, sqlite_path: str = None):
        self.lru = LRUCache(max_size=lru_size, ttl_seconds=lru_ttl)
        self.sqlite = SQLiteCache(db_path=sqlite_path)
    
    def get(self, query: str, top_k: int = 10) -> Optional[List[Dict]]:
        """获取缓存（自动降级）"""
        # 先查 LRU
        results = self.lru.get(query, top_k)
        if results is not None:
            return results
        
        # 未命中，查 SQLite
        results = self.sqlite.get(query, top_k)
        if results is not None:
            # 回填 LRU
            self.lru.set(query, results, top_k)
            return results
        
        return None
    
    def set(self, query: str, results: List[Dict], top_k: int = 10):
        """设置缓存"""
        self.lru.set(query, results, top_k)
        self.sqlite.set(query, results, top_k)
    
    def clear(self):
        """清空所有缓存"""
        self.lru.clear()
        self.sqlite.clear()
    
    def stats(self) -> Dict:
        """统计"""
        lru_stats = self.lru.stats()
        sqlite_stats = self.sqlite.stats()
        
        return {
            "lru": lru_stats,
            "sqlite": sqlite_stats
        }


# 全局缓存实例
_cache = None

def get_cache() -> HybridCache:
    global _cache
    if _cache is None:
        _cache = HybridCache()
    return _cache


# 缓存装饰器
def cached(ttl_seconds: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 尝试从缓存获取
            cache = get_cache()
            
            # 构造查询 key
            query = str(args[0]) if args else ""
            top_k = kwargs.get('top_k', 10)
            
            results = cache.get(query, top_k)
            if results is not None:
                return results
            
            # 未命中，执行函数
            results = func(*args, **kwargs)
            
            # 写入缓存
            cache.set(query, results, top_k)
            
            return results
        return wrapper
    return decorator


if __name__ == "__main__":
    print("=" * 50)
    print("多级缓存测试")
    print("=" * 50)
    
    # 测试数据
    test_results = [
        {"id": "1", "text": "测试记忆1", "score": 0.9},
        {"id": "2", "text": "测试记忆2", "score": 0.8},
    ]
    
    # LRU 缓存测试
    print("\n📦 LRU 缓存:")
    lru = LRUCache(max_size=100, ttl_seconds=60)
    
    lru.set("测试查询", test_results)
    cached = lru.get("测试查询")
    print(f"  存储后读取: {'成功' if cached else '失败'}")
    
    cached = lru.get("不存在的查询")
    print(f"  未命中查询: {'正确' if cached is None else '错误'}")
    
    print(f"  统计: {lru.stats()}")
    
    # SQLite 缓存测试
    print("\n💾 SQLite 缓存:")
    sqlite_cache = SQLiteCache()
    
    sqlite_cache.set("SQLite测试", test_results)
    cached = sqlite_cache.get("SQLite测试")
    print(f"  存储后读取: {'成功' if cached else '失败'}")
    
    print(f"  统计: {sqlite_cache.stats()}")
    
    # 混合缓存测试
    print("\n🔄 混合缓存:")
    hybrid = HybridCache()
    
    hybrid.set("混合测试", test_results)
    cached = hybrid.get("混合测试")
    print(f"  存储后读取: {'成功' if cached else '失败'}")
    
    # 第二次读取（应该命中 LRU）
    cached = hybrid.get("混合测试")
    print(f"  第二次读取: {'成功' if cached else '失败'}")
    
    print(f"  统计: {hybrid.stats()}")
    
    print("\n✅ 多级缓存测试完成")
