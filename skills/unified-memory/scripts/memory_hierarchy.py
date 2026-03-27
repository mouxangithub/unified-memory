#!/usr/bin/env python3
"""
Memory Hierarchy - 记忆分层缓存 v7.0

三层记忆架构:
- L1 Hot: 最近 24h，高重要性，常驻内存
- L2 Warm: 最近 7 天，中重要性，按需加载
- L3 Cold: 长期记忆，压缩摘要，解压加载

Usage:
    memory_hierarchy.py init                    # 初始化分层
    memory_hierarchy.py promote                # 晋升记忆到更热层
    memory_hierarchy.py demote                 # 降级记忆到更冷层
    memory_hierarchy.py get-context <query>    # 获取上下文（分层加载）
    memory_hierarchy.py stats                  # 分层统计
    memory_hierarchy.py compress               # 压缩 L3 记忆
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from collections import defaultdict

# ============================================================
# 配置
# ============================================================
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
HIERARCHY_DIR = MEMORY_DIR / "hierarchy"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

# 分层参数
L1_HOT_HOURS = 24        # L1: 最近 24 小时
L2_WARM_DAYS = 7         # L2: 最近 7 天
L1_MIN_IMPORTANCE = 0.6  # L1 最低重要性
L2_MIN_IMPORTANCE = 0.3  # L2 最低重要性
L1_MAX_SIZE = 20         # L1 最大记忆数
L2_MAX_SIZE = 100        # L2 最大记忆数

# 文件路径
L1_CACHE_FILE = HIERARCHY_DIR / "l1_hot.json"
L2_CACHE_FILE = HIERARCHY_DIR / "l2_warm.json"
L3_INDEX_FILE = HIERARCHY_DIR / "l3_index.json"
METADATA_FILE = HIERARCHY_DIR / "hierarchy_meta.json"

# 确保目录存在
HIERARCHY_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 记忆分层管理
# ============================================================

class MemoryHierarchy:
    """三层记忆分层管理器"""
    
    def __init__(self):
        self.l1_hot: List[Dict] = []      # 热记忆
        self.l2_warm: List[Dict] = []     # 温记忆
        self.l3_index: Dict = {}          # 冷记忆索引
        self.meta: Dict = {
            "last_promotion": None,
            "last_demotion": None,
            "last_compress": None,
            "total_promotions": 0,
            "total_demotions": 0
        }
        self._load()
    
    def _load(self):
        """加载分层缓存"""
        try:
            if L1_CACHE_FILE.exists():
                self.l1_hot = json.loads(L1_CACHE_FILE.read_text())
            if L2_CACHE_FILE.exists():
                self.l2_warm = json.loads(L2_CACHE_FILE.read_text())
            if L3_INDEX_FILE.exists():
                self.l3_index = json.loads(L3_INDEX_FILE.read_text())
            if METADATA_FILE.exists():
                self.meta = json.loads(METADATA_FILE.read_text())
        except Exception as e:
            print(f"⚠️ 加载分层缓存失败: {e}", file=sys.stderr)
    
    def _save(self):
        """保存分层缓存"""
        try:
            L1_CACHE_FILE.write_text(json.dumps(self.l1_hot, ensure_ascii=False, indent=2))
            L2_CACHE_FILE.write_text(json.dumps(self.l2_warm, ensure_ascii=False, indent=2))
            L3_INDEX_FILE.write_text(json.dumps(self.l3_index, ensure_ascii=False, indent=2))
            METADATA_FILE.write_text(json.dumps(self.meta, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"⚠️ 保存分层缓存失败: {e}", file=sys.stderr)
    
    def classify(self, memory: Dict) -> str:
        """判断记忆应该属于哪一层"""
        now = datetime.now()
        created_at = memory.get("created_at") or memory.get("timestamp")
        
        if created_at:
            try:
                if "T" in created_at:
                    mem_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                else:
                    mem_time = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                age_hours = (now - mem_time.replace(tzinfo=None)).total_seconds() / 3600
            except:
                age_hours = 999
        else:
            age_hours = 999
        
        importance = float(memory.get("importance", 0.5))
        
        # L1: 最近 24h 且重要性 > 0.6
        if age_hours <= L1_HOT_HOURS and importance >= L1_MIN_IMPORTANCE:
            return "L1"
        # L2: 最近 7 天 且重要性 > 0.3
        elif age_hours <= L2_WARM_DAYS * 24 and importance >= L2_MIN_IMPORTANCE:
            return "L2"
        # L3: 其他
        else:
            return "L3"
    
    def add_memory(self, memory: Dict) -> str:
        """添加新记忆到合适的层级"""
        layer = self.classify(memory)
        memory_id = memory.get("id") or f"mem_{int(time.time()*1000)}"
        memory["id"] = memory_id
        memory["layer"] = layer
        memory["layer_added_at"] = datetime.now().isoformat()
        
        if layer == "L1":
            self.l1_hot.insert(0, memory)
            # L1 容量限制
            if len(self.l1_hot) > L1_MAX_SIZE:
                demoted = self.l1_hot.pop()
                self._demote_to_l2(demoted)
        elif layer == "L2":
            self.l2_warm.insert(0, memory)
            # L2 容量限制
            if len(self.l2_warm) > L2_MAX_SIZE:
                demoted = self.l2_warm.pop()
                self._demote_to_l3(demoted)
        else:
            self._add_to_l3(memory)
        
        self._save()
        return layer
    
    def _demote_to_l2(self, memory: Dict):
        """从 L1 降级到 L2"""
        memory["layer"] = "L2"
        memory["demoted_at"] = datetime.now().isoformat()
        self.l2_warm.insert(0, memory)
        self.meta["total_demotions"] += 1
    
    def _demote_to_l3(self, memory: Dict):
        """从 L2 降级到 L3"""
        memory_id = memory.get("id")
        memory["layer"] = "L3"
        memory["demoted_at"] = datetime.now().isoformat()
        
        # L3 只存索引和摘要
        self.l3_index[memory_id] = {
            "id": memory_id,
            "summary": memory.get("text", "")[:100],
            "keywords": memory.get("tags", []),
            "importance": memory.get("importance", 0.5),
            "created_at": memory.get("created_at"),
            "demoted_at": memory["demoted_at"]
        }
        self.meta["total_demotions"] += 1
    
    def _add_to_l3(self, memory: Dict):
        """直接添加到 L3"""
        memory_id = memory.get("id")
        self.l3_index[memory_id] = {
            "id": memory_id,
            "summary": memory.get("text", "")[:100],
            "keywords": memory.get("tags", []),
            "importance": memory.get("importance", 0.5),
            "created_at": memory.get("created_at"),
            "layer_added_at": datetime.now().isoformat()
        }
    
    def promote(self, memory_id: str) -> Optional[str]:
        """晋升记忆到更热的层级"""
        # 检查 L2
        for i, mem in enumerate(self.l2_warm):
            if mem.get("id") == memory_id:
                promoted = self.l2_warm.pop(i)
                promoted["layer"] = "L1"
                promoted["promoted_at"] = datetime.now().isoformat()
                self.l1_hot.insert(0, promoted)
                self.meta["total_promotions"] += 1
                self._save()
                return "L2->L1"
        
        # 检查 L3 索引
        if memory_id in self.l3_index:
            # 从 L3 提升需要重新加载完整记忆
            # 这里简化处理，标记为需要加载
            self.l3_index[memory_id]["needs_reload"] = True
            self._save()
            return "L3->needs_reload"
        
        return None
    
    def get_context(self, query: str = None, max_memories: int = 10) -> List[Dict]:
        """获取上下文记忆（分层加载）"""
        context = []
        
        # 1. L1 热记忆直接返回（最多 5 条）
        context.extend(self.l1_hot[:5])
        
        # 2. 如果需要更多，从 L2 加载
        if len(context) < max_memories and query:
            # 简单关键词匹配
            query_lower = query.lower()
            relevant = [
                mem for mem in self.l2_warm
                if any(kw in query_lower for kw in self._extract_keywords(mem))
            ][:max_memories - len(context)]
            context.extend(relevant)
        
        return context
    
    def _extract_keywords(self, memory: Dict) -> List[str]:
        """从记忆提取关键词"""
        text = memory.get("text", "")
        tags = memory.get("tags", [])
        # 简单提取：标签 + 文本中的中文词
        keywords = tags.copy()
        # 提取 2-4 字的中文词
        import re
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
        keywords.extend(chinese_words[:5])
        return keywords
    
    def rebuild_from_memories(self, memories: List[Dict]):
        """从记忆列表重建分层"""
        self.l1_hot = []
        self.l2_warm = []
        self.l3_index = {}
        
        for mem in memories:
            self.add_memory(mem)
        
        self.meta["last_rebuild"] = datetime.now().isoformat()
        self._save()
        print(f"✅ 分层重建完成: L1={len(self.l1_hot)}, L2={len(self.l2_warm)}, L3={len(self.l3_index)}")
    
    def stats(self) -> Dict:
        """统计分层状态"""
        l1_importance_avg = sum(m.get("importance", 0) for m in self.l1_hot) / len(self.l1_hot) if self.l1_hot else 0
        l2_importance_avg = sum(m.get("importance", 0) for m in self.l2_warm) / len(self.l2_warm) if self.l2_warm else 0
        l3_importance_avg = sum(v.get("importance", 0) for v in self.l3_index.values()) / len(self.l3_index) if self.l3_index else 0
        
        return {
            "L1_hot": {
                "count": len(self.l1_hot),
                "max_size": L1_MAX_SIZE,
                "avg_importance": round(l1_importance_avg, 3),
                "age_limit": f"{L1_HOT_HOURS}h"
            },
            "L2_warm": {
                "count": len(self.l2_warm),
                "max_size": L2_MAX_SIZE,
                "avg_importance": round(l2_importance_avg, 3),
                "age_limit": f"{L2_WARM_DAYS}d"
            },
            "L3_cold": {
                "count": len(self.l3_index),
                "avg_importance": round(l3_importance_avg, 3)
            },
            "meta": self.meta
        }
    
    def compress_l3(self):
        """压缩 L3 记忆（合并相似记忆）"""
        if len(self.l3_index) < 10:
            print("L3 记忆数量不足，无需压缩")
            return
        
        # 简单合并：按关键词分组
        groups = defaultdict(list)
        for mem_id, mem_data in self.l3_index.items():
            key = tuple(sorted(mem_data.get("keywords", []))[:2])
            groups[key].append(mem_id)
        
        # 合并同组记忆
        merged_count = 0
        for key, ids in groups.items():
            if len(ids) > 1:
                # 保留最重要的，删除其他
                sorted_ids = sorted(ids, key=lambda x: self.l3_index[x].get("importance", 0), reverse=True)
                for mem_id in sorted_ids[1:]:
                    del self.l3_index[mem_id]
                    merged_count += 1
        
        self.meta["last_compress"] = datetime.now().isoformat()
        self._save()
        print(f"✅ L3 压缩完成: 合并 {merged_count} 条记忆")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Memory Hierarchy v7.0")
    parser.add_argument("command", choices=["init", "stats", "promote", "demote", "get-context", "compress"])
    parser.add_argument("--memory-id", help="记忆 ID")
    parser.add_argument("--query", help="查询内容")
    parser.add_argument("--max", type=int, default=10, help="最大返回数")
    
    args = parser.parse_args()
    hierarchy = MemoryHierarchy()
    
    if args.command == "init":
        print("🔄 初始化记忆分层...")
        hierarchy._save()
        print("✅ 初始化完成")
    
    elif args.command == "stats":
        stats = hierarchy.stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    elif args.command == "promote":
        if not args.memory_id:
            print("❌ 请指定 --memory-id")
            sys.exit(1)
        result = hierarchy.promote(args.memory_id)
        if result:
            print(f"✅ 晋升成功: {result}")
        else:
            print("❌ 晋升失败：未找到记忆")
    
    elif args.command == "get-context":
        context = hierarchy.get_context(args.query, args.max)
        print(json.dumps(context, ensure_ascii=False, indent=2))
    
    elif args.command == "compress":
        hierarchy.compress_l3()
    
    else:
        print(f"未知命令: {args.command}")


if __name__ == "__main__":
    main()
