#!/usr/bin/env python3
"""
Agent 记忆池 - Memory Pool

MemGPT 创新：多层记忆池
├── 核心记忆（永远保留）
├── 工作记忆（当前任务）
├── 上下文记忆（最近对话）
└── 档案记忆（归档）
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class MemoryPool:
    """
    Agent 记忆池
    
    核心思想：记忆分级，不同级别不同策略
    """
    
    def __init__(self):
        WORKSPACE = Path.home() / ".openclaw" / "workspace"
        MEMORY_DIR = WORKSPACE / "memory"
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        
        self.pool_file = MEMORY_DIR / "memory_pool.json"
        self.pool = self._load_pool()
    
    def _load_pool(self) -> Dict:
        if self.pool_file.exists():
            with open(self.pool_file, "r") as f:
                return json.load(f)
        return {
            "core": [],      # 核心记忆（永远保留）
            "working": [],   # 工作记忆（当前任务）
            "context": [],    # 上下文记忆（最近对话）
            "archive": []    # 档案记忆（归档）
        }
    
    def _save_pool(self):
        with open(self.pool_file, "w") as f:
            json.dump(self.pool, f, indent=2, ensure_ascii=False)
    
    # ===== 存储 =====
    
    def store(self, memory: Dict, tier: str = "context"):
        """
        存储记忆到指定层级
        
        Args:
            memory: 记忆数据
            tier: core/working/context/archive
        """
        memory["tier"] = tier
        memory["stored_at"] = datetime.now().isoformat()
        
        if tier not in self.pool:
            self.pool[tier] = []
        
        self.pool[tier].append(memory)
        self._save_pool()
    
    def promote(self, memory_id: str, from_tier: str, to_tier: str):
        """提升记忆层级"""
        if from_tier not in self.pool:
            return False
        
        memory = None
        for i, m in enumerate(self.pool[from_tier]):
            if m.get("id") == memory_id:
                memory = self.pool[from_tier].pop(i)
                break
        
        if memory:
            memory["tier"] = to_tier
            memory["promoted_at"] = datetime.now().isoformat()
            
            if to_tier not in self.pool:
                self.pool[to_tier] = []
            self.pool[to_tier].append(memory)
            self._save_pool()
            return True
        return False
    
    def demote(self, memory_id: str, from_tier: str, to_tier: str = "archive"):
        """降级记忆"""
        return self.promote(memory_id, from_tier, to_tier)
    
    # ===== 检索 =====
    
    def search_all(self, query: str) -> List[Dict]:
        """搜索所有层级"""
        results = []
        
        for tier, memories in self.pool.items():
            for mem in memories:
                if query.lower() in mem.get("text", "").lower():
                    results.append({**mem, "tier": tier})
        
        # 按层级优先级排序
        tier_priority = {"core": 4, "working": 3, "context": 2, "archive": 1}
        results.sort(key=lambda x: tier_priority.get(x.get("tier", ""), 0), reverse=True)
        return results
    
    def search_tier(self, tier: str, query: str = None) -> List[Dict]:
        """搜索指定层级"""
        memories = self.pool.get(tier, [])
        
        if query is None:
            return memories
        
        return [m for m in memories if query.lower() in m.get("text", "").lower()]
    
    # ===== 自动管理 =====
    
    def auto_tier(self, memory: Dict) -> str:
        """
        根据记忆内容自动判断层级
        
        Returns:
            tier: core/working/context/archive
        """
        text = memory.get("text", "")
        category = memory.get("category", "")
        
        # 核心记忆：偏好、重要决策、长期信息
        core_keywords = ["永远", "必须", "绝对", "始终", "偏好", "喜欢", "不喜欢"]
        if any(kw in text for kw in core_keywords):
            return "core"
        
        # 工作记忆：当前任务、进行中项目
        if category == "task" or "进行" in text or "当前" in text:
            return "working"
        
        # 上下文记忆：最近的对话
        return "context"
    
    def archive_old_context(self, days: int = 7):
        """归档旧的上下文记忆"""
        cutoff = datetime.now() - timedelta(days=days)
        
        context = self.pool.get("context", [])
        to_archive = []
        remaining = []
        
        for mem in context:
            stored_at = datetime.fromisoformat(mem.get("stored_at", "2000-01-01"))
            if stored_at < cutoff:
                to_archive.append(mem)
            else:
                remaining.append(mem)
        
        self.pool["context"] = remaining
        self.pool["archive"].extend(to_archive)
        self._save_pool()
        
        return len(to_archive)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            tier: len(memories) 
            for tier, memories in self.pool.items()
        }
    
    def get_full_context(self) -> str:
        """构建完整上下文"""
        parts = []
        
        # 核心记忆优先
        for mem in self.pool.get("core", [])[-5:]:
            parts.append(f"【核心】{mem.get('text', '')}")
        
        # 工作记忆
        for mem in self.pool.get("working", [])[-3:]:
            parts.append(f"【工作】{mem.get('text', '')}")
        
        # 上下文记忆
        for mem in self.pool.get("context", [])[-5:]:
            parts.append(f"【上下文】{mem.get('text', '')}")
        
        return "\n".join(parts)


# 全局实例
_pool = None

def get_memory_pool() -> MemoryPool:
    global _pool
    if _pool is None:
        _pool = MemoryPool()
    return _pool


if __name__ == "__main__":
    print("=" * 50)
    print("记忆池测试")
    print("=" * 50)
    
    pool = MemoryPool()
    
    # 存储测试
    print("\n📝 存储记忆:")
    pool.store({"id": "mem_1", "text": "用户永远喜欢简洁界面", "category": "preference"}, "core")
    pool.store({"id": "mem_2", "text": "当前任务：完成首页设计", "category": "task"}, "working")
    pool.store({"id": "mem_3", "text": "讨论了微服务架构", "category": "conversation"}, "context")
    
    print(f"  core: 1, working: 1, context: 1")
    
    # 统计
    print(f"\n📊 统计: {pool.get_stats()}")
    
    # 搜索
    print(f"\n🔍 搜索'界面':")
    results = pool.search_all("界面")
    for r in results:
        print(f"  [{r['tier']}] {r['text']}")
    
    # 自动分层
    print(f"\n🎯 自动分层:")
    test_memories = [
        {"text": "用户永远喜欢蓝色", "category": "preference"},
        {"text": "当前正在开发电商功能", "category": "task"},
        {"text": "刚才讨论了数据库设计", "category": "conversation"},
    ]
    for mem in test_memories:
        tier = pool.auto_tier(mem)
        print(f"  '{mem['text'][:20]}...' -> {tier}")
    
    print("\n✅ 记忆池测试完成")
