#!/usr/bin/env python3
"""
OpenClaw 原生集成 - OpenClaw Native Integration

集成到 OpenClaw 插件系统
提供标准的 memory tools
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# OpenClaw 配置路径
OPENCLAW_CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"


class OpenClawIntegration:
    """
    OpenClaw 原生集成
    
    提供：
    1. memory_recall - 记忆召回
    2. memory_store - 记忆存储
    3. memory_forget - 记忆删除
    4. memory_update - 记忆更新
    5. memory_stats - 统计信息
    6. memory_list - 记忆列表
    """
    
    def __init__(self):
        self.db_path = str(MEMORY_DIR / "vector")
        self.scope = "agent:main"  # 默认作用域
        self._sqlite = None
        self._pool = None
    
    def _get_sqlite(self):
        """获取 SQLite 连接"""
        if self._sqlite is None:
            from memory_sqlite import SQLiteMemory
            self._sqlite = SQLiteMemory()
        return self._sqlite
    
    def _get_pool(self):
        """获取记忆池"""
        if self._pool is None:
            from memory_pool import MemoryPool
            self._pool = MemoryPool()
        return self._pool
    
    def recall(self, query: str, limit: int = 5, scope: str = None) -> List[Dict]:
        """
        记忆召回
        
        对应 memory_recall tool
        """
        from memory_bm25 import hybrid_search
        from memory_cache import get_cache
        
        scope = scope or self.scope
        
        # 尝试从缓存获取
        cache = get_cache()
        cached = cache.get(query, limit)
        if cached:
            return cached
        
        # 获取所有记忆进行搜索
        db = self._get_sqlite()
        memories = db.get_all(limit=100)
        
        if not memories:
            return []
        
        texts = [m.get("text", "") for m in memories]
        
        # 混合搜索
        results = hybrid_search(query, texts, None, top_k=limit)
        
        # 合并元数据
        id_to_mem = {m["id"]: m for m in memories}
        for r in results:
            if r["index"] < len(memories):
                r.update(id_to_mem.get(memories[r["index"]]["id"], {}))
        
        return results
    
    def store(self, 
               text: str, 
               category: str = "general",
               importance: float = 0.5,
               scope: str = None) -> bool:
        """
        记忆存储
        
        对应 memory_store tool
        """
        from memory_sqlite import SQLiteMemory
        from memory_pool import MemoryPool
        from datetime import datetime
        
        scope = scope or self.scope
        
        memory = {
            "id": f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "text": text,
            "category": category,
            "importance": importance,
            "confidence": 0.8,
            "tags": [],
            "project": scope,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "accessed_at": datetime.now().isoformat(),
        }
        
        # 存储到 SQLite
        db = SQLiteMemory()
        success = db.store(memory)
        
        # 也存储到记忆池
        pool = MemoryPool()
        pool.store(memory, "context")
        
        return success
    
    def forget(self, memory_id: str) -> bool:
        """
        记忆删除
        
        对应 memory_forget tool
        """
        from memory_sqlite import SQLiteMemory
        
        db = SQLiteMemory()
        return db.delete(memory_id)
    
    def update(self, 
                memory_id: str,
                text: str = None,
                category: str = None,
                importance: float = None) -> bool:
        """
        记忆更新
        
        对应 memory_update tool
        """
        from memory_sqlite import SQLiteMemory
        from datetime import datetime
        
        db = SQLiteMemory()
        memory = db.get(memory_id)
        
        if not memory:
            return False
        
        # 更新字段
        if text is not None:
            memory["text"] = text
        if category is not None:
            memory["category"] = category
        if importance is not None:
            memory["importance"] = importance
        
        memory["updated_at"] = datetime.now().isoformat()
        
        return db.store(memory)
    
    def stats(self, scope: str = None) -> Dict:
        """
        统计信息
        
        对应 memory_stats tool
        """
        from memory_sqlite import SQLiteMemory
        
        scope = scope or self.scope
        
        db = SQLiteMemory()
        basic_stats = db.get_stats()
        
        return {
            "total": basic_stats.get("total", 0),
            "scope": scope,
            "db_path": self.db_path,
            "by_category": basic_stats.get("by_category", {}),
        }
    
    def list_memories(self, 
                      limit: int = 20,
                      category: str = None,
                      scope: str = None) -> List[Dict]:
        """
        记忆列表
        
        对应 memory_list tool
        """
        from memory_sqlite import SQLiteMemory
        
        scope = scope or self.scope
        
        db = SQLiteMemory()
        memories = db.get_all(limit=limit)
        
        # 过滤
        if category:
            memories = [m for m in memories if m.get("category") == category]
        if scope:
            memories = [m for m in memories if m.get("project") == scope]
        
        return memories


# 全局实例
_integration = None

def get_openclaw_integration() -> OpenClawIntegration:
    """获取集成实例"""
    global _integration
    if _integration is None:
        _integration = OpenClawIntegration()
    return _integration


# CLI 入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw Memory Integration")
    subparsers = parser.add_subparsers(dest="command")
    
    # recall
    recall_parser = subparsers.add_parser("recall", help="召回记忆")
    recall_parser.add_argument("query", help="查询")
    recall_parser.add_argument("--limit", "-n", type=int, default=5)
    
    # store
    store_parser = subparsers.add_parser("store", help="存储记忆")
    store_parser.add_argument("text", help="记忆内容")
    store_parser.add_argument("--category", "-c", default="general")
    store_parser.add_argument("--importance", "-i", type=float, default=0.5)
    
    # stats
    subparsers.add_parser("stats", help="统计")
    
    # list
    list_parser = subparsers.add_parser("list", help="列表")
    list_parser.add_argument("--limit", "-n", type=int, default=20)
    
    args = parser.parse_args()
    
    integration = get_openclaw_integration()
    
    if args.command == "recall":
        results = integration.recall(args.query, args.limit)
        print(f"\n🔍 召回 '{args.query}' ({len(results)} 条)\n")
        for r in results:
            print(f"  - [{r.get('category')}] {r.get('text', '')[:60]}...")
    
    elif args.command == "store":
        success = integration.store(args.text, args.category, args.importance)
        print(f"{'✅' if success else '❌'} 已存储: {args.text[:50]}...")
    
    elif args.command == "stats":
        stats = integration.stats()
        print(f"\n📊 统计\n")
        print(f"  总记忆: {stats.get('total', 0)}")
        print(f"  作用域: {stats.get('scope')}")
        print(f"  路径: {stats.get('db_path')}")
    
    elif args.command == "list":
        memories = integration.list_memories(args.limit)
        print(f"\n📝 记忆列表 ({len(memories)} 条)\n")
        for m in memories:
            print(f"  - [{m.get('category')}] {m.get('text', '')[:60]}...")
    
    else:
        parser.print_help()
