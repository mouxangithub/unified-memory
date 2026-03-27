#!/usr/bin/env python3
"""
Conversation Deduplicator - 对话去重合并 v0.1.0

功能:
- 检测相似对话片段
- 合并重复记忆
- 智能去重策略

Usage:
    conversation_dedup.py detect --threshold 0.8
    conversation_dedup.py merge --dry-run
    conversation_dedup.py stats
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
DEDUP_FILE = MEMORY_DIR / "dedup" / "dedup_state.json"

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


class ConversationDeduplicator:
    """对话去重合并"""
    
    def __init__(self):
        self.memories = self._load_memories()
        self.dedup_state = self._load_dedup_state()
    
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
    
    def _load_dedup_state(self) -> Dict:
        """加载去重状态"""
        if DEDUP_FILE.exists():
            try:
                return json.loads(DEDUP_FILE.read_text())
            except:
                pass
        return {"duplicate_groups": [], "merged": []}
    
    def _save_dedup_state(self):
        """保存去重状态"""
        DEDUP_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEDUP_FILE.write_text(json.dumps(self.dedup_state, ensure_ascii=False, indent=2))
    
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
        if not vec1 or not vec2:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """文本相似度（Jaccard + SequenceMatcher）"""
        # Jaccard
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        jaccard = len(intersection) / len(union) if union else 0
        
        # SequenceMatcher
        seq_ratio = SequenceMatcher(None, text1, text2).ratio()
        
        # 综合
        return (jaccard + seq_ratio) / 2
    
    def detect_duplicates(self, threshold: float = 0.85) -> List[Dict]:
        """检测重复记忆
        
        Returns:
            List of duplicate groups
        """
        print(f"🔍 检测重复记忆 (阈值: {threshold})...")
        
        # 按类别分组
        by_category = defaultdict(list)
        for mem in self.memories:
            category = mem.get("category", "other")
            by_category[category].append(mem)
        
        duplicate_groups = []
        processed = set()
        
        for category, mems in by_category.items():
            print(f"  检查类别: {category} ({len(mems)} 条)")
            
            for i, mem1 in enumerate(mems):
                if mem1.get("id") in processed:
                    continue
                
                group = [mem1]
                text1 = mem1.get("text", "")
                emb1 = mem1.get("embedding")
                
                for mem2 in mems[i+1:]:
                    if mem2.get("id") in processed:
                        continue
                    
                    text2 = mem2.get("text", "")
                    emb2 = mem2.get("embedding")
                    
                    # 计算相似度
                    similarity = 0
                    
                    # 向量相似度（优先）
                    if emb1 and emb2:
                        similarity = self._cosine_similarity(emb1, emb2)
                    else:
                        # 文本相似度
                        similarity = self._text_similarity(text1, text2)
                    
                    if similarity >= threshold:
                        group.append(mem2)
                        processed.add(mem2.get("id"))
                
                if len(group) > 1:
                    duplicate_groups.append({
                        "category": category,
                        "memories": group,
                        "avg_similarity": self._avg_similarity(group)
                    })
                    processed.add(mem1.get("id"))
        
        self.dedup_state["duplicate_groups"] = duplicate_groups
        self._save_dedup_state()
        
        return duplicate_groups
    
    def _avg_similarity(self, group: List[Dict]) -> float:
        """计算组内平均相似度"""
        if len(group) < 2:
            return 1.0
        
        similarities = []
        for i, mem1 in enumerate(group):
            for mem2 in group[i+1:]:
                text1 = mem1.get("text", "")
                text2 = mem2.get("text", "")
                similarities.append(self._text_similarity(text1, text2))
        
        return sum(similarities) / len(similarities) if similarities else 1.0
    
    def merge_duplicates(self, dry_run: bool = True) -> Dict:
        """合并重复记忆"""
        if not self.dedup_state.get("duplicate_groups"):
            print("⚠️ 未检测到重复，请先运行 detect")
            return {"merged": 0}
        
        print(f"🔄 {'[DRY RUN] ' if dry_run else ''}合并重复记忆...")
        
        merged_count = 0
        merged_memories = []
        
        for group in self.dedup_state["duplicate_groups"]:
            memories = group["memories"]
            if len(memories) < 2:
                continue
            
            # 选择最优记忆（最高重要性）
            best = max(memories, key=lambda m: m.get("importance", 0))
            
            # 合并信息
            merged_text = best.get("text", "")
            merged_importance = max(m.get("importance", 0) for m in memories)
            merged_categories = list(set(m.get("category", "") for m in memories))
            merged_tags = []
            
            for mem in memories:
                tags = mem.get("tags", [])
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except:
                        tags = []
                merged_tags.extend(tags)
            
            merged_tags = list(set(merged_tags))
            
            merged_memory = {
                "id": best.get("id"),
                "text": merged_text,
                "category": best.get("category"),
                "importance": merged_importance,
                "tags": merged_tags[:5],
                "merged_from": [m.get("id") for m in memories if m.get("id") != best.get("id")],
                "merged_at": datetime.now().isoformat()
            }
            
            merged_memories.append(merged_memory)
            merged_count += len(memories) - 1
            
            print(f"  合并 {len(memories)} 条 → 保留 {best.get('id')[:8]}")
        
        if not dry_run:
            self.dedup_state["merged"] = merged_memories
            self._save_dedup_state()
            
            # TODO: 实际更新向量数据库
        
        return {
            "dry_run": dry_run,
            "merged_groups": len(merged_memories),
            "merged_count": merged_count,
            "saved_memories": merged_memories if dry_run else None
        }
    
    def stats(self) -> Dict:
        """统计信息"""
        groups = self.dedup_state.get("duplicate_groups", [])
        merged = self.dedup_state.get("merged", [])
        
        total_duplicates = sum(len(g["memories"]) for g in groups)
        
        return {
            "duplicate_groups": len(groups),
            "total_duplicates": total_duplicates,
            "potential_savings": total_duplicates - len(groups),
            "already_merged": len(merged)
        }


def main():
    parser = argparse.ArgumentParser(description="Conversation Deduplicator 0.1.0")
    parser.add_argument("command", choices=["detect", "merge", "stats"])
    parser.add_argument("--threshold", "-t", type=float, default=0.85, help="相似度阈值")
    parser.add_argument("--dry-run", action="store_true", help="预览模式")
    
    args = parser.parse_args()
    
    dedup = ConversationDeduplicator()
    
    if args.command == "detect":
        groups = dedup.detect_duplicates(args.threshold)
        
        print(f"\n📊 检测结果:")
        print(f"  发现 {len(groups)} 组重复记忆")
        
        for i, group in enumerate(groups[:5], 1):
            print(f"\n  组 {i} [{group['category']}]:")
            for mem in group["memories"]:
                text = mem.get("text", "")[:40]
                imp = mem.get("importance", 0)
                print(f"    - {text}... (重要性: {imp:.2f})")
        
        if len(groups) > 5:
            print(f"\n  ... 还有 {len(groups) - 5} 组")
    
    elif args.command == "merge":
        result = dedup.merge_duplicates(dry_run=args.dry_run)
        
        if args.dry_run:
            print(f"\n📊 预览结果:")
            print(f"  将合并 {result['merged_groups']} 组")
            print(f"  节省 {result['merged_count']} 条重复记忆")
        else:
            print(f"\n✅ 合并完成:")
            print(f"  已合并 {result['merged_groups']} 组")
            print(f"  节省 {result['merged_count']} 条重复记忆")
    
    elif args.command == "stats":
        stats = dedup.stats()
        print(f"📊 去重统计:")
        print(f"  重复组数: {stats['duplicate_groups']}")
        print(f"  总重复数: {stats['total_duplicates']}")
        print(f"  潜在节省: {stats['potential_savings']} 条")
        print(f"  已合并数: {stats['already_merged']}")


if __name__ == "__main__":
    main()
