#!/usr/bin/env python3
"""
Memory Dedup - 对话去重合并 v0.1.2

功能:
- 检测相似对话
- 合并重复记忆
- 保留最新信息
- 记录合并历史

Usage:
    memory_dedup.py detect [--threshold 0.9]
    memory_dedup.py merge --dry-run
    memory_dedup.py merge --execute
    memory_dedup.py history
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import hashlib

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
DEDUP_HISTORY = MEMORY_DIR / "dedup" / "history.json"

try:
    import lancedb
    HAS_LANCEDB = True
except ImportError:
    HAS_LANCEDB = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Ollama
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")


class MemoryDedup:
    """对话去重合并"""
    
    def __init__(self):
        self.memories = self._load_memories()
        self.history = self._load_history()
    
    def _load_memories(self) -> List[Dict]:
        """加载记忆"""
        memories = []
        
        if HAS_LANCEDB:
            try:
                db = lancedb.connect(str(VECTOR_DB_DIR))
                table = db.open_table("memories")
                result = table.to_lance().to_table().to_pydict()
                
                if result:
                    count = len(result.get("id", []))
                    for i in range(count):
                        mem = {col: result[col][i] for col in result.keys() if len(result[col]) > i}
                        memories.append(mem)
            except:
                pass
        
        return memories
    
    def _load_history(self) -> Dict:
        """加载合并历史"""
        if DEDUP_HISTORY.exists():
            try:
                return json.loads(DEDUP_HISTORY.read_text())
            except:
                pass
        return {"merges": [], "stats": {"total_merged": 0}}
    
    def _save_history(self):
        """保存合并历史"""
        DEDUP_HISTORY.parent.mkdir(parents=True, exist_ok=True)
        DEDUP_HISTORY.write_text(json.dumps(self.history, ensure_ascii=False, indent=2))
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """获取向量"""
        if not HAS_REQUESTS:
            return None
        
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("embedding")
        except:
            pass
        
        return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        return dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0
    
    def _text_hash(self, text: str) -> str:
        """计算文本哈希"""
        return hashlib.md5(text.encode()).hexdigest()[:8]
    
    def _normalize_text(self, text: str) -> str:
        """标准化文本（用于比较）"""
        # 移除时间戳
        import re
        text = re.sub(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}[ T]\d{1,2}:\d{2}(:\d{2})?', '', text)
        # 移除多余空格
        text = ' '.join(text.split())
        # 转小写
        text = text.lower()
        return text
    
    def detect_duplicates(self, threshold: float = 0.9) -> List[Tuple[Dict, Dict, float]]:
        """检测重复记忆"""
        duplicates = []
        
        # 1. 完全相同文本
        text_groups = defaultdict(list)
        for mem in self.memories:
            text = self._normalize_text(mem.get("text", ""))
            text_groups[text].append(mem)
        
        for text, group in text_groups.items():
            if len(group) > 1:
                for i, mem1 in enumerate(group):
                    for mem2 in group[i+1:]:
                        duplicates.append((mem1, mem2, 1.0))
        
        # 2. 向量相似度
        seen_pairs = set()
        for i, mem1 in enumerate(self.memories):
            vec1 = mem1.get("embedding")
            if not vec1:
                vec1 = self._get_embedding(mem1.get("text", ""))
            
            if not vec1:
                continue
            
            for mem2 in self.memories[i+1:]:
                pair_key = tuple(sorted([mem1.get("id"), mem2.get("id")]))
                if pair_key in seen_pairs:
                    continue
                
                vec2 = mem2.get("embedding")
                if not vec2:
                    vec2 = self._get_embedding(mem2.get("text", ""))
                
                if not vec2:
                    continue
                
                sim = self._cosine_similarity(vec1, vec2)
                if sim >= threshold:
                    duplicates.append((mem1, mem2, sim))
                    seen_pairs.add(pair_key)
        
        return duplicates
    
    def merge_memories(self, mem1: Dict, mem2: Dict) -> Dict:
        """合并两条记忆"""
        # 保留较新的
        t1 = mem1.get("created_at") or mem1.get("timestamp") or ""
        t2 = mem2.get("created_at") or mem2.get("timestamp") or ""
        
        newer = mem1 if t1 >= t2 else mem2
        older = mem2 if t1 >= t2 else mem1
        
        # 合并内容
        merged = {
            "id": newer.get("id"),
            "text": newer.get("text"),
            "importance": max(mem1.get("importance", 0.5), mem2.get("importance", 0.5)),
            "category": newer.get("category", older.get("category")),
            "created_at": newer.get("created_at"),
            "merged_from": [older.get("id")],
            "merge_count": (older.get("merge_count", 0) + 1)
        }
        
        # 合并标签
        tags1 = set(mem1.get("tags", []))
        tags2 = set(mem2.get("tags", []))
        merged["tags"] = list(tags1 | tags2)
        
        return merged
    
    def execute_merge(self, dry_run: bool = True) -> Dict:
        """执行合并"""
        duplicates = self.detect_duplicates()
        
        if not duplicates:
            return {"found": 0, "merged": 0, "message": "No duplicates found"}
        
        merge_groups = defaultdict(list)
        
        for mem1, mem2, sim in duplicates:
            # 将相似记忆分组
            id1, id2 = mem1.get("id"), mem2.get("id")
            added = False
            
            for key, group in merge_groups.items():
                if id1 in group or id2 in group:
                    group.add(id1)
                    group.add(id2)
                    added = True
                    break
            
            if not added:
                merge_groups[id1].add(id1)
                merge_groups[id1].add(id2)
        
        merged_count = 0
        merges = []
        
        for key, group in merge_groups.items():
            if len(group) < 2:
                continue
            
            # 获取组内所有记忆
            group_mems = [m for m in self.memories if m.get("id") in group]
            if not group_mems:
                continue
            
            # 合并
            merged = group_mems[0]
            for mem in group_mems[1:]:
                merged = self.merge_memories(merged, mem)
            
            merged_count += len(group) - 1
            merges.append({
                "kept": merged.get("id"),
                "removed": [m.get("id") for m in group_mems if m.get("id") != merged.get("id")],
                "text": merged.get("text")[:50]
            })
            
            if not dry_run:
                # 记录合并历史
                self.history["merges"].append({
                    "timestamp": datetime.now().isoformat(),
                    "kept": merged.get("id"),
                    "removed": [m.get("id") for m in group_mems if m.get("id") != merged.get("id")]
                })
        
        if not dry_run:
            self.history["stats"]["total_merged"] += merged_count
            self._save_history()
        
        return {
            "found": len(duplicates),
            "merged": merged_count,
            "groups": len(merge_groups),
            "dry_run": dry_run,
            "merges": merges if len(merges) <= 10 else f"{len(merges)} merge groups (showing first 10)"
        }
    
    def get_history(self) -> Dict:
        """获取合并历史"""
        return {
            "total_merges": len(self.history.get("merges", [])),
            "total_memories_merged": self.history.get("stats", {}).get("total_merged", 0),
            "recent": self.history.get("merges", [])[-5:]
        }


def main():
    parser = argparse.ArgumentParser(description="Memory Dedup 0.1.2")
    parser.add_argument("command", choices=["detect", "merge", "history"])
    parser.add_argument("--threshold", "-t", type=float, default=0.9, help="相似度阈值")
    parser.add_argument("--dry-run", action="store_true", help="只预览不执行")
    parser.add_argument("--execute", action="store_true", help="执行合并")
    
    args = parser.parse_args()
    
    dedup = MemoryDedup()
    
    if args.command == "detect":
        print(f"🔍 检测重复记忆 (阈值: {args.threshold})...")
        duplicates = dedup.detect_duplicates(args.threshold)
        
        if not duplicates:
            print("✅ 未发现重复记忆")
        else:
            print(f"📋 发现 {len(duplicates)} 对重复记忆:")
            for i, (mem1, mem2, sim) in enumerate(duplicates[:10], 1):
                t1 = mem1.get("text", "")[:40]
                t2 = mem2.get("text", "")[:40]
                print(f"  {i}. [{sim:.2f}] '{t1}...' ≈ '{t2}...'")
    
    elif args.command == "merge":
        dry_run = not args.execute
        if dry_run:
            print("🔍 预览合并结果...")
        else:
            print("🔄 执行合并...")
        
        result = dedup.execute_merge(dry_run=dry_run)
        
        print(f"\n📊 结果:")
        print(f"  发现重复: {result['found']} 对")
        print(f"  可合并: {result['merged']} 条")
        print(f"  合并组: {result['groups']} 个")
        
        if dry_run:
            print(f"\n💡 使用 --execute 执行合并")
        else:
            print(f"✅ 合并完成")
        
        if isinstance(result.get("merges"), list):
            print(f"\n合并详情:")
            for m in result["merges"][:5]:
                print(f"  保留: {m['kept'][:8]}... | 移除: {len(m['removed'])} 条")
    
    elif args.command == "history":
        history = dedup.get_history()
        print(f"📜 合并历史:")
        print(f"  总合并次数: {history['total_merges']}")
        print(f"  总合并记忆: {history['total_memories_merged']}")
        
        if history["recent"]:
            print(f"\n最近合并:")
            for h in history["recent"]:
                print(f"  {h['timestamp'][:10]}: 保留 {h['kept'][:8]}... | 移除 {len(h['removed'])} 条")


if __name__ == "__main__":
    main()
