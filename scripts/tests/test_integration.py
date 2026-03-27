#!/usr/bin/env python3
"""
端到端集成测试 - End-to-End Integration Test

测试完整流程：存储 → 搜索 → 读取 → 更新 → 删除
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from memory_sqlite import SQLiteMemory
from memory_pool import MemoryPool
from memory_cache import get_cache
from memory_bm25 import hybrid_search, cached_search


class IntegrationTest:
    """集成测试"""
    
    def __init__(self):
        self.results = []
        self.db = SQLiteMemory(":memory:")
        self.pool = MemoryPool()
    
    def test_store_and_retrieve(self):
        """测试存储和检索"""
        print("\n📝 测试存储和检索...")
        
        # 存储测试记忆
        test_memories = [
            {"id": "e2e_1", "text": "用户喜欢简洁界面设计", "category": "preference"},
            {"id": "e2e_2", "text": "采用微服务架构方案", "category": "decision"},
            {"id": "e2e_3", "text": "Python 是主要开发语言", "category": "fact"},
            {"id": "e2e_4", "text": "需要完成首页功能", "category": "task"},
            {"id": "e2e_5", "text": "数据库使用 PostgreSQL", "category": "fact"},
        ]
        
        for mem in test_memories:
            self.db.store(mem)
        
        count = self.db.count()
        assert count >= 5, f"存储失败: 期望 5, 实际 {count}"
        print(f"  ✅ 存储 {count} 条记忆")
        
        # 检索
        mem = self.db.get("e2e_1")
        assert mem is not None, "检索失败"
        assert "简洁界面" in mem["text"], "内容不匹配"
        print(f"  ✅ 检索成功: {mem['text'][:30]}...")
    
    def test_search(self):
        """测试搜索"""
        print("\n🔍 测试搜索...")
        
        # 获取所有文本
        memories = self.db.get_all(limit=100)
        texts = [m["text"] for m in memories]
        
        # BM25 搜索
        results = hybrid_search("界面", texts, None, top_k=3)
        assert len(results) > 0, "搜索返回空结果"
        print(f"  ✅ BM25 搜索: 找到 {len(results)} 条")
        
        # 带缓存搜索
        results = cached_search("架构", texts, top_k=3)
        assert len(results) > 0, "缓存搜索返回空结果"
        print(f"  ✅ 缓存搜索: 找到 {len(results)} 条")
    
    def test_memory_pool(self):
        """测试记忆池"""
        print("\n🏊 测试记忆池...")
        
        # 存储到不同层级
        self.pool.store({"id": "pool_e2e_1", "text": "核心记忆"}, "core")
        self.pool.store({"id": "pool_e2e_2", "text": "工作记忆"}, "working")
        self.pool.store({"id": "pool_e2e_3", "text": "上下文记忆"}, "context")
        
        stats = self.pool.get_stats()
        assert stats["core"] >= 1, "核心记忆存储失败"
        assert stats["working"] >= 1, "工作记忆存储失败"
        print(f"  ✅ 记忆池: core={stats['core']}, working={stats['working']}")
        
        # 读取
        mem = self.pool.retrieve("pool_e2e_1")
        assert mem is not None, "记忆池读取失败"
        print(f"  ✅ 记忆池读取: {mem['text']}")
    
    def test_cache(self):
        """测试缓存"""
        print("\n💾 测试缓存...")
        
        cache = get_cache()
        
        # 写入缓存
        test_data = [{"id": "cache_test", "text": "缓存测试", "score": 0.9}]
        cache.set("缓存关键词", test_data, top_k=10)
        
        # 读取缓存
        cached = cache.get("缓存关键词", top_k=10)
        assert cached is not None, "缓存读取失败"
        assert cached[0]["id"] == "cache_test", "缓存内容不匹配"
        print(f"  ✅ 缓存读写成功")
        
        # 统计
        stats = cache.stats()
        print(f"  ✅ 缓存统计: {stats}")
    
    def test_performance(self):
        """性能测试"""
        print("\n⚡ 性能测试...")
        
        # 存储性能
        start = time.time()
        for i in range(100):
            self.db.store({
                "id": f"perf_{i}",
                "text": f"性能测试记忆 {i}",
                "category": "test"
            })
        store_time = time.time() - start
        print(f"  ✅ 存储 100 条: {store_time*1000:.2f}ms ({store_time*1000/100:.2f}ms/条)")
        
        # 搜索性能
        memories = self.db.get_all(limit=1000)
        texts = [m["text"] for m in memories]
        
        start = time.time()
        for i in range(50):
            hybrid_search(f"测试 {i}", texts, None, top_k=10)
        search_time = time.time() - start
        print(f"  ✅ 搜索 50 次: {search_time*1000:.2f}ms ({search_time*1000/50:.2f}ms/次)")
    
    def run_all(self):
        """运行所有测试"""
        print("=" * 60)
        print("🧪 端到端集成测试")
        print("=" * 60)
        
        tests = [
            ("存储和检索", self.test_store_and_retrieve),
            ("搜索", self.test_search),
            ("记忆池", self.test_memory_pool),
            ("缓存", self.test_cache),
            ("性能", self.test_performance),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                test_func()
                passed += 1
            except Exception as e:
                print(f"  ❌ {name} 失败: {e}")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 测试结果: ✅ {passed} 通过, ❌ {failed} 失败")
        print("=" * 60)
        
        return failed == 0


if __name__ == "__main__":
    test = IntegrationTest()
    success = test.run_all()
    sys.exit(0 if success else 1)
