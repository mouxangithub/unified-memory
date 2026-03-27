#!/usr/bin/env python3
"""
Knowledge Merger - 知识合并器 v7.0

功能:
- 检测相似/重复记忆
- 合并为知识块 (Knowledge Block)
- 减少记忆冗余
- 提升检索效率

Usage:
    knowledge_merger.py scan                    # 扫描相似记忆
    knowledge_merger.py merge --threshold 0.9   # 合并高相似记忆
    knowledge_merger.py stats                   # 统计合并效果
    knowledge_merger.py preview <group-id>      # 预览合并结果
"""

import argparse
import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict

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

# ============================================================
# 配置
# ============================================================
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
MERGED_DIR = MEMORY_DIR / "knowledge_blocks"

# Ollama 配置
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")

# 合并参数
SIMILARITY_THRESHOLD = 0.85    # 相似度阈值
MIN_GROUP_SIZE = 2             # 最小合并组大小
MAX_GROUP_SIZE = 10            # 最大合并组大小

# 文件路径
SIMILARITY_CACHE_FILE = MERGED_DIR / "similarity_cache.json"
MERGE_HISTORY_FILE = MERGED_DIR / "merge_history.json"
KNOWLEDGE_BLOCKS_FILE = MERGED_DIR / "knowledge_blocks.json"

# 确保目录存在
MERGED_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Embedding 服务
# ============================================================

def get_embedding(text: str) -> Optional[List[float]]:
    """获取文本向量"""
    if not HAS_REQUESTS:
        return None
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("embedding", [])
    except Exception as e:
        print(f"⚠️ Embedding 失败: {e}", file=sys.stderr)
        return None


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算余弦相似度"""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def call_llm(prompt: str, model: str = None) -> Optional[str]:
    """调用 LLM"""
    if not HAS_REQUESTS:
        return None
    
    model = model or OLLAMA_LLM_MODEL
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.3}},
            timeout=60
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"⚠️ LLM 调用失败: {e}", file=sys.stderr)
        return None


# ============================================================
# 知识合并器
# ============================================================

class KnowledgeMerger:
    """知识合并器"""
    
    def __init__(self):
        self.similarity_cache: Dict[str, Dict[str, float]] = {}
        self.merge_history: List[Dict] = []
        self.knowledge_blocks: Dict[str, Dict] = {}
        self._load()
    
    def _load(self):
        """加载缓存数据"""
        try:
            if SIMILARITY_CACHE_FILE.exists():
                self.similarity_cache = json.loads(SIMILARITY_CACHE_FILE.read_text())
            if MERGE_HISTORY_FILE.exists():
                self.merge_history = json.loads(MERGE_HISTORY_FILE.read_text())
            if KNOWLEDGE_BLOCKS_FILE.exists():
                self.knowledge_blocks = json.loads(KNOWLEDGE_BLOCKS_FILE.read_text())
        except Exception as e:
            print(f"⚠️ 加载缓存失败: {e}", file=sys.stderr)
    
    def _save(self):
        """保存缓存数据"""
        try:
            SIMILARITY_CACHE_FILE.write_text(json.dumps(self.similarity_cache, ensure_ascii=False, indent=2))
            MERGE_HISTORY_FILE.write_text(json.dumps(self.merge_history, ensure_ascii=False, indent=2))
            KNOWLEDGE_BLOCKS_FILE.write_text(json.dumps(self.knowledge_blocks, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"⚠️ 保存缓存失败: {e}", file=sys.stderr)
    
    def scan_similar(self, memories: List[Dict], threshold: float = SIMILARITY_THRESHOLD) -> Dict[str, List[str]]:
        """扫描相似记忆组"""
        groups: Dict[str, List[str]] = defaultdict(list)
        visited: Set[str] = set()
        
        print(f"🔍 扫描 {len(memories)} 条记忆...")
        
        for i, mem1 in enumerate(memories):
            id1 = mem1.get("id", f"mem_{i}")
            if id1 in visited:
                continue
            
            text1 = mem1.get("text", "")
            vec1 = mem1.get("vector") or get_embedding(text1)
            if not vec1:
                continue
            
            group = [id1]
            for j, mem2 in enumerate(memories[i+1:], i+1):
                id2 = mem2.get("id", f"mem_{j}")
                if id2 in visited:
                    continue
                
                text2 = mem2.get("text", "")
                
                # 检查缓存
                cache_key = f"{min(id1, id2)}_{max(id1, id2)}"
                if cache_key in self.similarity_cache:
                    sim = self.similarity_cache[cache_key]
                else:
                    vec2 = mem2.get("vector") or get_embedding(text2)
                    if not vec2:
                        continue
                    sim = cosine_similarity(vec1, vec2)
                    self.similarity_cache[cache_key] = sim
                
                if sim >= threshold:
                    group.append(id2)
                    visited.add(id2)
            
            if len(group) >= MIN_GROUP_SIZE:
                group_key = f"group_{len(groups)+1}"
                groups[group_key] = group
                for gid in group:
                    visited.add(gid)
        
        self._save()
        return dict(groups)
    
    def merge_group(self, memories: List[Dict], group_ids: List[str]) -> Dict:
        """合并一组相似记忆"""
        # 获取组内记忆
        group_mems = [m for m in memories if m.get("id") in group_ids]
        if not group_mems:
            return {}
        
        # 提取共同主题
        texts = [m.get("text", "") for m in group_mems]
        combined_text = "\n".join(f"- {t}" for t in texts)
        
        # 使用 LLM 生成合并摘要
        prompt = f"""请将以下 {len(texts)} 条相关记忆合并为一条精炼的知识摘要：

原始记忆:
{combined_text}

要求：
1. 提取共同主题
2. 合并重复内容
3. 保留关键细节
4. 输出格式：[主题]: [合并内容]

合并结果:"""

        merged_text = call_llm(prompt) or f"[合并] {texts[0][:100]}"
        
        # 创建知识块
        block_id = f"kb_{int(datetime.now().timestamp()*1000)}"
        knowledge_block = {
            "id": block_id,
            "text": merged_text.strip(),
            "source_memories": group_ids,
            "importance": max(m.get("importance", 0.5) for m in group_mems),
            "category": group_mems[0].get("category", "other"),
            "created_at": datetime.now().isoformat(),
            "merged_count": len(group_ids)
        }
        
        # 记录合并历史
        self.merge_history.append({
            "block_id": block_id,
            "source_ids": group_ids,
            "merged_at": datetime.now().isoformat(),
            "tokens_saved": sum(len(t) for t in texts) - len(merged_text)
        })
        
        self.knowledge_blocks[block_id] = knowledge_block
        self._save()
        
        return knowledge_block
    
    def merge_all(self, memories: List[Dict], threshold: float = SIMILARITY_THRESHOLD, dry_run: bool = False) -> List[Dict]:
        """合并所有相似记忆"""
        groups = self.scan_similar(memories, threshold)
        
        if not groups:
            print("✅ 未发现相似记忆组")
            return []
        
        print(f"📋 发现 {len(groups)} 个相似组")
        
        blocks = []
        for group_key, group_ids in groups.items():
            if len(group_ids) > MAX_GROUP_SIZE:
                print(f"⚠️ {group_key} 组过大 ({len(group_ids)} 条)，跳过")
                continue
            
            if dry_run:
                print(f"  {group_key}: {group_ids}")
            else:
                block = self.merge_group(memories, group_ids)
                if block:
                    blocks.append(block)
                    print(f"✅ 合并 {group_key}: {len(group_ids)} → 1 条")
        
        return blocks
    
    def stats(self) -> Dict:
        """统计合并效果"""
        total_merged = len(self.merge_history)
        total_blocks = len(self.knowledge_blocks)
        total_memories_merged = sum(h.get("merged_count", 0) for h in self.merge_history)
        total_tokens_saved = sum(h.get("tokens_saved", 0) for h in self.merge_history)
        
        return {
            "total_merges": total_merged,
            "total_knowledge_blocks": total_blocks,
            "total_memories_merged": total_memories_merged,
            "estimated_tokens_saved": total_tokens_saved,
            "compression_ratio": f"{(total_memories_merged - total_blocks) / total_memories_merged * 100:.1f}%" if total_memories_merged > 0 else "N/A",
            "recent_merges": self.merge_history[-5:] if self.merge_history else []
        }
    
    def preview_merge(self, memories: List[Dict], group_ids: List[str]) -> str:
        """预览合并结果（不实际合并）"""
        group_mems = [m for m in memories if m.get("id") in group_ids]
        if not group_mems:
            return "未找到记忆"
        
        lines = ["📋 合并预览", "=" * 40]
        for mem in group_mems:
            lines.append(f"- {mem.get('text', '')[:80]}...")
        
        lines.append("=" * 40)
        lines.append(f"将合并为 1 条知识块")
        
        return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Knowledge Merger v7.0")
    parser.add_argument("command", choices=["scan", "merge", "stats", "preview"])
    parser.add_argument("--threshold", type=float, default=SIMILARITY_THRESHOLD, help="相似度阈值")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际合并")
    parser.add_argument("--group-id", help="预览指定组")
    
    args = parser.parse_args()
    merger = KnowledgeMerger()
    
    # 加载记忆（从 vector 数据库或文件）
    memories = []
    if HAS_LANCEDB:
        try:
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            memories = table.to_pandas().to_dict("records")
        except Exception as e:
            print(f"⚠️ 无法加载记忆: {e}", file=sys.stderr)
    
    if args.command == "scan":
        groups = merger.scan_similar(memories, args.threshold)
        print(f"发现 {len(groups)} 个相似组:")
        for gid, ids in groups.items():
            print(f"  {gid}: {ids}")
    
    elif args.command == "merge":
        blocks = merger.merge_all(memories, args.threshold, args.dry_run)
        if args.dry_run:
            print(f"预览完成，发现 {len(blocks)} 个可合并组")
        else:
            print(f"✅ 合并完成，生成 {len(blocks)} 条知识块")
    
    elif args.command == "stats":
        stats = merger.stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    elif args.command == "preview":
        if not args.group_id:
            print("❌ 请指定 --group-id")
            sys.exit(1)
        groups = merger.scan_similar(memories, args.threshold)
        if args.group_id in groups:
            print(merger.preview_merge(memories, groups[args.group_id]))
        else:
            print(f"❌ 未找到组: {args.group_id}")
    
    else:
        print(f"未知命令: {args.command}")


if __name__ == "__main__":
    main()
