#!/usr/bin/env python3
"""
Memory Association - 记忆关联推荐 v0.1.0

功能:
- 基于向量相似度推荐相关记忆
- 基于共现关系推荐关联记忆
- 基于标签关联推荐

Usage:
    memory_association.py recommend --memory-id <id> --top-k 5
    memory_association.py related --query "飞书" --top-k 5
    memory_association.py build-graph  # 构建关联图
"""

import argparse
import json
import os
import sys
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
ASSOCIATION_GRAPH = MEMORY_DIR / "associations" / "graph.json"

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


class MemoryAssociation:
    """记忆关联推荐"""
    
    def __init__(self):
        self.memories = self._load_memories()
        self.graph = self._load_graph()
        self.co_occurrence = defaultdict(Counter)
    
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
            except Exception as e:
                print(f"⚠️ 加载失败: {e}", file=sys.stderr)
        
        return memories
    
    def _load_graph(self) -> Dict:
        """加载关联图"""
        if ASSOCIATION_GRAPH.exists():
            try:
                return json.loads(ASSOCIATION_GRAPH.read_text())
            except:
                pass
        return {"nodes": {}, "edges": {}}
    
    def _save_graph(self):
        """保存关联图"""
        ASSOCIATION_GRAPH.parent.mkdir(parents=True, exist_ok=True)
        ASSOCIATION_GRAPH.write_text(json.dumps(self.graph, ensure_ascii=False, indent=2))
    
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
    
    def recommend_by_similarity(self, memory_id: str, top_k: int = 5) -> List[Dict]:
        """基于向量相似度推荐"""
        target = None
        for mem in self.memories:
            if mem.get("id") == memory_id:
                target = mem
                break
        
        if not target:
            return []
        
        target_embedding = target.get("embedding")
        if not target_embedding:
            # 尝试生成
            target_embedding = self._get_embedding(target.get("text", ""))
        
        if not target_embedding:
            return []
        
        similarities = []
        for mem in self.memories:
            if mem.get("id") == memory_id:
                continue
            
            mem_embedding = mem.get("embedding")
            if not mem_embedding:
                continue
            
            sim = self._cosine_similarity(target_embedding, mem_embedding)
            if sim > 0.5:  # 只保留高相似度
                similarities.append({
                    "memory": mem,
                    "score": sim,
                    "reason": "vector_similarity"
                })
        
        similarities.sort(key=lambda x: x["score"], reverse=True)
        return similarities[:top_k]
    
    def recommend_by_co_occurrence(self, memory_id: str, top_k: int = 5) -> List[Dict]:
        """基于共现关系推荐"""
        # 构建共现矩阵
        self._build_co_occurrence()
        
        target = None
        for mem in self.memories:
            if mem.get("id") == memory_id:
                target = mem
                break
        
        if not target:
            return []
        
        # 获取共现记忆
        co_occur = self.co_occurrence.get(memory_id, {})
        
        results = []
        for related_id, count in co_occur.most_common(top_k):
            for mem in self.memories:
                if mem.get("id") == related_id:
                    results.append({
                        "memory": mem,
                        "score": count,
                        "reason": "co_occurrence"
                    })
                    break
        
        return results
    
    def recommend_by_tags(self, memory_id: str, top_k: int = 5) -> List[Dict]:
        """基于标签关联推荐"""
        target = None
        for mem in self.memories:
            if mem.get("id") == memory_id:
                target = mem
                break
        
        if not target:
            return []
        
        target_tags = set()
        target_text = target.get("text", "").lower()
        
        # 提取标签（关键词）
        keywords = ["飞书", "微信", "项目", "协作", "任务", "记忆", "系统", "偏好", "决策"]
        for kw in keywords:
            if kw in target_text:
                target_tags.add(kw)
        
        # 按类别关联
        target_category = target.get("category", "")
        
        results = []
        for mem in self.memories:
            if mem.get("id") == memory_id:
                continue
            
            score = 0
            
            # 同类别加分
            if mem.get("category") == target_category:
                score += 0.5
            
            # 标签重叠加分
            mem_text = mem.get("text", "").lower()
            overlap = sum(1 for tag in target_tags if tag in mem_text)
            score += overlap * 0.3
            
            if score > 0:
                results.append({
                    "memory": mem,
                    "score": score,
                    "reason": "tag_similarity"
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def recommend(self, memory_id: str, top_k: int = 5) -> List[Dict]:
        """综合推荐（融合多种策略）"""
        # 获取各策略结果
        by_sim = self.recommend_by_similarity(memory_id, top_k * 2)
        by_co = self.recommend_by_co_occurrence(memory_id, top_k)
        by_tag = self.recommend_by_tags(memory_id, top_k * 2)
        
        # 合并打分
        scores = defaultdict(lambda: {"score": 0, "reasons": [], "memory": None})
        
        for item in by_sim:
            mem_id = item["memory"].get("id")
            scores[mem_id]["score"] += item["score"] * 0.5  # 向量相似度权重
            scores[mem_id]["reasons"].append("相似度")
            scores[mem_id]["memory"] = item["memory"]
        
        for item in by_co:
            mem_id = item["memory"].get("id")
            scores[mem_id]["score"] += item["score"] * 0.3  # 共现权重
            scores[mem_id]["reasons"].append("共现")
            scores[mem_id]["memory"] = item["memory"]
        
        for item in by_tag:
            mem_id = item["memory"].get("id")
            scores[mem_id]["score"] += item["score"] * 0.2  # 标签权重
            scores[mem_id]["reasons"].append("标签")
            scores[mem_id]["memory"] = item["memory"]
        
        # 排序
        results = [
            {
                "memory": v["memory"],
                "score": v["score"],
                "reasons": list(set(v["reasons"]))
            }
            for v in scores.values()
            if v["memory"] and v["memory"].get("id") != memory_id
        ]
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def _build_co_occurrence(self):
        """构建共现矩阵"""
        if self.co_occurrence:
            return  # 已构建
        
        # 按时间窗口分组（同一天的记忆视为共现）
        by_date = defaultdict(list)
        for mem in self.memories:
            created_at = mem.get("created_at") or mem.get("timestamp")
            if created_at:
                try:
                    date_key = created_at[:10]  # YYYY-MM-DD
                    by_date[date_key].append(mem.get("id"))
                except:
                    pass
        
        # 构建共现
        for date, mem_ids in by_date.items():
            for i, id1 in enumerate(mem_ids):
                for id2 in mem_ids[i+1:]:
                    self.co_occurrence[id1][id2] += 1
                    self.co_occurrence[id2][id1] += 1
    
    def build_graph(self) -> Dict:
        """构建关联图"""
        self._build_co_occurrence()
        
        nodes = {}
        edges = {}
        
        for mem in self.memories:
            mem_id = mem.get("id")
            nodes[mem_id] = {
                "text": mem.get("text", "")[:50],
                "category": mem.get("category"),
                "importance": mem.get("importance", 0.5)
            }
        
        for mem_id, co_occur in self.co_occurrence.items():
            for related_id, count in co_occur.items():
                edge_key = f"{mem_id}_{related_id}"
                if edge_key not in edges:
                    edges[edge_key] = {
                        "source": mem_id,
                        "target": related_id,
                        "weight": count,
                        "type": "co_occurrence"
                    }
        
        self.graph = {"nodes": nodes, "edges": edges}
        self._save_graph()
        
        return {
            "nodes": len(nodes),
            "edges": len(edges),
            "saved": str(ASSOCIATION_GRAPH)
        }
    
    def related_to_query(self, query: str, top_k: int = 5) -> List[Dict]:
        """查询相关记忆（带关联推荐）"""
        # 首先直接搜索
        results = []
        query_lower = query.lower()
        
        for mem in self.memories:
            text = mem.get("text", "").lower()
            if query_lower in text:
                results.append({
                    "memory": mem,
                    "score": 1.0,
                    "reasons": ["直接匹配"]
                })
        
        # 如果有结果，推荐关联记忆
        if results:
            top_result = results[0]
            mem_id = top_result["memory"].get("id")
            related = self.recommend(mem_id, top_k)
            
            # 合并去重
            seen_ids = {r["memory"].get("id") for r in results}
            for rel in related:
                rel_id = rel["memory"].get("id")
                if rel_id not in seen_ids:
                    rel["reasons"].append("关联推荐")
                    results.append(rel)
                    seen_ids.add(rel_id)
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


def main():
    parser = argparse.ArgumentParser(description="Memory Association 0.1.0")
    parser.add_argument("command", choices=["recommend", "related", "build-graph"])
    parser.add_argument("--memory-id", "-m", help="记忆 ID")
    parser.add_argument("--query", "-q", help="查询文本")
    parser.add_argument("--top-k", "-k", type=int, default=5, help="返回数量")
    
    args = parser.parse_args()
    
    association = MemoryAssociation()
    
    if args.command == "recommend":
        if not args.memory_id:
            print("❌ 请指定 --memory-id")
            sys.exit(1)
        
        results = association.recommend(args.memory_id, args.top_k)
        
        print(f"📋 推荐关联记忆 (top {len(results)}):")
        for i, item in enumerate(results, 1):
            text = item["memory"].get("text", "")[:60]
            score = item["score"]
            reasons = "+".join(item["reasons"])
            print(f"  {i}. [{reasons}] {text}... (score: {score:.2f})")
    
    elif args.command == "related":
        if not args.query:
            print("❌ 请指定 --query")
            sys.exit(1)
        
        results = association.related_to_query(args.query, args.top_k)
        
        print(f"📋 相关记忆 (top {len(results)}):")
        for i, item in enumerate(results, 1):
            text = item["memory"].get("text", "")[:60]
            reasons = "+".join(item["reasons"])
            print(f"  {i}. [{reasons}] {text}...")
    
    elif args.command == "build-graph":
        result = association.build_graph()
        print(f"✅ 关联图已构建:")
        print(f"  节点: {result['nodes']}")
        print(f"  边: {result['edges']}")
        print(f"  保存到: {result['saved']}")


if __name__ == "__main__":
    main()
