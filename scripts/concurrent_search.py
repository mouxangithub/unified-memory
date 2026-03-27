#!/usr/bin/env python3
"""
Concurrent Search - 并发查询 v0.1.2

功能:
- 并行多条件搜索
- 结果合并排序
- 超时控制
- 性能追踪

Usage:
    concurrent_search.py search --queries "飞书,微信,协作" --top-k 5
    concurrent_search.py multi --tags "项目,任务" --text "进度"
    concurrent_search.py benchmark
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import threading

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

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

# 并发配置
MAX_WORKERS = 4
DEFAULT_TIMEOUT = 30.0


class ConcurrentSearch:
    """并发查询"""
    
    def __init__(self):
        self.memories = self._load_memories()
        self.stats = {"searches": 0, "total_time_ms": 0, "concurrent_searches": 0}
        self._lock = threading.Lock()
    
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
    
    def _search_single(self, query: str, top_k: int = 5) -> List[Dict]:
        """单次搜索"""
        query_lower = query.lower()
        results = []
        
        # 文本匹配
        for mem in self.memories:
            text = mem.get("text", "").lower()
            if query_lower in text:
                score = text.count(query_lower) / len(text) if text else 0
                results.append({
                    "memory": mem,
                    "score": score + 0.5,  # 基础匹配分
                    "match_type": "text"
                })
        
        # 向量搜索（可选）
        query_vec = self._get_embedding(query)
        if query_vec:
            for mem in self.memories:
                mem_vec = mem.get("embedding")
                if mem_vec:
                    sim = self._cosine_similarity(query_vec, mem_vec)
                    if sim > 0.7:
                        results.append({
                            "memory": mem,
                            "score": sim,
                            "match_type": "vector"
                        })
        
        # 去重排序
        seen = set()
        unique = []
        for r in sorted(results, key=lambda x: x["score"], reverse=True):
            mem_id = r["memory"].get("id")
            if mem_id not in seen:
                seen.add(mem_id)
                unique.append(r)
        
        return unique[:top_k]
    
    def search_concurrent(self, queries: List[str], top_k: int = 5, timeout: float = DEFAULT_TIMEOUT) -> Dict:
        """并发搜索多个查询"""
        start_time = time.time()
        all_results = {}
        errors = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 提交所有搜索任务
            futures = {
                executor.submit(self._search_single, q, top_k): q
                for q in queries
            }
            
            # 收集结果
            for future in as_completed(futures, timeout=timeout):
                query = futures[future]
                try:
                    results = future.result(timeout=timeout)
                    all_results[query] = results
                except Exception as e:
                    errors.append({"query": query, "error": str(e)})
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # 更新统计
        with self._lock:
            self.stats["searches"] += len(queries)
            self.stats["total_time_ms"] += elapsed_ms
            self.stats["concurrent_searches"] += 1
        
        # 合并结果
        merged = self._merge_results(all_results, top_k)
        
        return {
            "queries": len(queries),
            "results": merged,
            "per_query": {q: len(r) for q, r in all_results.items()},
            "elapsed_ms": round(elapsed_ms, 2),
            "errors": errors if errors else None
        }
    
    def _merge_results(self, all_results: Dict[str, List[Dict]], top_k: int) -> List[Dict]:
        """合并多个查询结果"""
        # 按记忆聚合分数
        mem_scores = {}
        
        for query, results in all_results.items():
            for r in results:
                mem_id = r["memory"].get("id")
                if mem_id not in mem_scores:
                    mem_scores[mem_id] = {
                        "memory": r["memory"],
                        "total_score": 0,
                        "match_count": 0,
                        "queries": []
                    }
                
                mem_scores[mem_id]["total_score"] += r["score"]
                mem_scores[mem_id]["match_count"] += 1
                mem_scores[mem_id]["queries"].append(query)
        
        # 排序
        sorted_results = sorted(
            mem_scores.values(),
            key=lambda x: x["total_score"],
            reverse=True
        )
        
        return [
            {
                "memory": r["memory"],
                "score": round(r["total_score"], 3),
                "matched_queries": r["queries"],
                "match_count": r["match_count"]
            }
            for r in sorted_results[:top_k]
        ]
    
    def multi_filter(self, tags: List[str], text: str, top_k: int = 10) -> Dict:
        """多条件过滤"""
        start_time = time.time()
        results = []
        
        for mem in self.memories:
            score = 0
            match_reasons = []
            
            # 标签匹配
            mem_tags = set(mem.get("tags", []))
            tag_overlap = set(tags) & mem_tags if tags else set()
            if tag_overlap:
                score += len(tag_overlap) * 0.3
                match_reasons.append(f"tags: {list(tag_overlap)}")
            
            # 文本匹配
            mem_text = mem.get("text", "").lower()
            if text.lower() in mem_text:
                score += 0.5
                match_reasons.append("text match")
            
            # 类别匹配
            category = mem.get("category", "")
            if category in tags:
                score += 0.2
                match_reasons.append(f"category: {category}")
            
            if score > 0:
                results.append({
                    "memory": mem,
                    "score": score,
                    "reasons": match_reasons
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            "filters": {"tags": tags, "text": text},
            "results": results[:top_k],
            "total_matched": len(results),
            "elapsed_ms": round(elapsed_ms, 2)
        }
    
    def benchmark(self) -> Dict:
        """性能基准测试"""
        test_queries = ["飞书", "项目", "协作", "记忆", "系统"]
        
        # 串行测试
        start = time.time()
        for q in test_queries:
            self._search_single(q, top_k=5)
        serial_ms = (time.time() - start) * 1000
        
        # 并发测试
        start = time.time()
        self.search_concurrent(test_queries, top_k=5)
        concurrent_ms = (time.time() - start) * 1000
        
        return {
            "queries": len(test_queries),
            "serial_ms": round(serial_ms, 2),
            "concurrent_ms": round(concurrent_ms, 2),
            "speedup": round(serial_ms / concurrent_ms, 2) if concurrent_ms > 0 else 0,
            "avg_per_query_serial": round(serial_ms / len(test_queries), 2),
            "avg_per_query_concurrent": round(concurrent_ms / len(test_queries), 2)
        }


def main():
    parser = argparse.ArgumentParser(description="Concurrent Search 0.1.2")
    parser.add_argument("command", choices=["search", "multi", "benchmark"])
    parser.add_argument("--queries", "-q", help="逗号分隔的查询列表")
    parser.add_argument("--tags", "-t", help="逗号分隔的标签列表")
    parser.add_argument("--text", "-x", help="文本查询")
    parser.add_argument("--top-k", "-k", type=int, default=5, help="返回数量")
    parser.add_argument("--timeout", type=float, default=30.0, help="超时秒数")
    
    args = parser.parse_args()
    
    search = ConcurrentSearch()
    
    if args.command == "search":
        if not args.queries:
            print("❌ 请指定 --queries")
            sys.exit(1)
        
        queries = [q.strip() for q in args.queries.split(",")]
        print(f"🔍 并发搜索 {len(queries)} 个查询...")
        
        result = search.search_concurrent(queries, args.top_k, args.timeout)
        
        print(f"\n✅ 完成 ({result['elapsed_ms']} ms):")
        for q, count in result["per_query"].items():
            print(f"  '{q}': {count} 条结果")
        
        print(f"\n📋 合并结果 (top {len(result['results'])}):")
        for i, r in enumerate(result["results"], 1):
            text = r["memory"].get("text", "")[:40]
            print(f"  {i}. [{r['score']:.2f}] {text}... (匹配 {r['match_count']} 个查询)")
    
    elif args.command == "multi":
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
        text = args.text or ""
        
        print(f"🔍 多条件过滤: tags={tags}, text='{text}'...")
        
        result = search.multi_filter(tags, text, args.top_k)
        
        print(f"\n✅ 找到 {result['total_matched']} 条 ({result['elapsed_ms']} ms):")
        for i, r in enumerate(result["results"], 1):
            mem_text = r["memory"].get("text", "")[:40]
            reasons = ", ".join(r["reasons"])
            print(f"  {i}. [{r['score']:.2f}] {mem_text}... ({reasons})")
    
    elif args.command == "benchmark":
        print("📊 运行性能基准测试...")
        result = search.benchmark()
        
        print(f"\n📊 基准测试结果:")
        print(f"  查询数量: {result['queries']}")
        print(f"  串行耗时: {result['serial_ms']} ms")
        print(f"  并发耗时: {result['concurrent_ms']} ms")
        print(f"  加速比: {result['speedup']}x")
        print(f"  平均/查询 (串行): {result['avg_per_query_serial']} ms")
        print(f"  平均/查询 (并发): {result['avg_per_query_concurrent']} ms")


if __name__ == "__main__":
    main()
