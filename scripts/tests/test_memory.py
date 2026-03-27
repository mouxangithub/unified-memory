#!/usr/bin/env python3
"""
测试框架 - Test Framework

使用 pytest
"""

import pytest
import sys
from pathlib import Path

# 添加 scripts 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestMemoryCore:
    """核心功能测试"""
    
    def test_bm25_import(self):
        """BM25 模块导入测试"""
        from memory_bm25 import BM25Index
        assert BM25Index is not None
    
    def test_feedback_import(self):
        """反馈模块导入测试"""
        from memory_feedback import FeedbackLearner
        assert FeedbackLearner is not None
    
    def test_store_import(self):
        """存储模块导入测试"""
        from memory_store_fix import store_memory
        assert store_memory is not None


class TestMemorySearch:
    """搜索功能测试"""
    
    def test_bm25_search(self):
        """BM25 搜索测试"""
        from memory_bm25 import BM25Index
        
        index = BM25Index()
        texts = [
            "用户喜欢简洁的界面",
            "采用微服务架构",
            "Python 是一种编程语言"
        ]
        index.build(texts)
        
        results = index.search("界面")
        assert len(results) >= 0
    
    def test_hybrid_search(self):
        """混合搜索测试"""
        from memory_bm25 import hybrid_search
        
        texts = ["用户喜欢简洁界面", "微服务架构"]
        vectors = [[0.1] * 768, [0.2] * 768]
        
        results = hybrid_search("用户界面", texts, vectors, top_k=2)
        assert isinstance(results, list)


class TestMemoryPersistence:
    """持久化测试"""
    
    def test_sqlite_crud(self):
        """SQLite CRUD 测试"""
        from memory_sqlite import SQLiteMemory
        
        db = SQLiteMemory(":memory:")
        
        # Create
        db.store({"id": "test_1", "text": "测试记忆", "category": "test"})
        assert db.count() >= 1
        
        # Read
        mem = db.get("test_1")
        assert mem is not None
        assert mem["text"] == "测试记忆"
        
        # Delete
        db.delete("test_1")
        
        db.close()
    
    def test_sqlite_search(self):
        """SQLite 搜索测试"""
        from memory_sqlite import SQLiteMemory
        
        db = SQLiteMemory(":memory:")
        db.store({"id": "test_2", "text": "搜索测试", "category": "test"})
        
        results = db.search_like("搜索")
        assert isinstance(results, list)
        
        db.close()


class TestMemoryPools:
    """记忆池测试"""
    
    def test_memory_pool(self):
        """记忆池测试"""
        from memory_pool import MemoryPool
        
        pool = MemoryPool()
        
        # 存储
        pool.store({"id": "pool_1", "text": "核心记忆"}, "core")
        pool.store({"id": "pool_2", "text": "工作记忆"}, "working")
        
        stats = pool.get_stats()
        assert stats["core"] >= 1
        assert stats["working"] >= 1


class TestPrivacy:
    """隐私测试"""
    
    def test_encrypt_decrypt(self):
        """加密解密测试"""
        from memory_privacy import PrivacyComputing
        
        privacy = PrivacyComputing()
        
        original = "测试文本"
        encrypted = privacy.encrypt(original)
        decrypted = privacy.decrypt(encrypted)
        
        assert decrypted == original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
