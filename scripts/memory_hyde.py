#!/usr/bin/env python3
"""
Memory HyDe - 三重搜索模式实现
Hypothetical Document Embedding 搜索

核心功能:
- lex: BM25 关键词搜索 (0 Token)
- vec: 向量语义搜索
- hyde: 假设文档嵌入搜索
- hybrid: 三重混合 + RRF 融合

Usage:
    from memory_hyde import hyde_search, triple_search
    
    # HyDe 搜索
    results = hyde_search("用户偏好", limit=5)
    
    # 三重混合搜索
    results = triple_search("项目进度", limit=10)
"""

import json
import os
import sys
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# 添加脚本目录到 path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from unified_memory import (
    load_all_memories, get_ollama_embedding, search_vector,
    BM25, ImportanceScorer, OLLAMA_URL
)

import requests

# ============================================================
# HyDe - 假设文档嵌入
# ============================================================

def generate_hypothetical_document(query: str) -> str:
    """
    使用 LLM 生成假设文档
    基于查询生成一个"理想答案"，然后对其做 embedding
    """
    
    # 检查 Ollama 是否可用
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if not r.ok:
            return query  # Ollama 不可用，退回原始查询
    except:
        return query
    
    # HyDe Prompt
    prompt = f"""请根据以下问题，生成一段可能包含答案的文档片段（50-100字）。
问题：{query}

文档片段："""
    
    try:
        # 调用 Ollama 生成
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud"),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150
                }
            },
            timeout=30
        )
        
        if response.ok:
            data = response.json()
            hypothetical = data.get("response", "").strip()
            
            # 如果生成的文档太短，退回原始查询
            if len(hypothetical) < 20:
                return query
            
            return hypothetical
        
    except Exception as e:
        print(f"⚠️ HyDe 生成失败: {e}", file=sys.stderr)
    
    return query


def hyde_search(query: str, limit: int = 5) -> List[Dict]:
    """
    HyDe 搜索
    
    1. 生成假设文档
    2. 对假设文档做 embedding
    3. 用假设 embedding 搜索真实记忆
    """
    
    # 生成假设文档
    hypothetical = generate_hypothetical_document(query)
    
    # 对假设文档做 embedding
    embedding = get_ollama_embedding(hypothetical)
    
    if embedding is None:
        # Ollama 不可用，退回普通向量搜索
        return vector_search_fallback(query, limit)
    
    # 用假设 embedding 搜索
    results = search_vector_by_embedding(embedding, limit)
    
    # 添加元数据
    for r in results:
        r["mode"] = "hyde"
        r["hypothetical"] = hypothetical[:100] + "..." if len(hypothetical) > 100 else hypothetical
    
    return results


def vector_search_fallback(query: str, limit: int) -> List[Dict]:
    """向量搜索回退"""
    return search_vector(query, limit)


def search_vector_by_embedding(embedding: List[float], limit: int = 5) -> List[Dict]:
    """用 embedding 搜索向量数据库"""
    try:
        import lancedb
        db = lancedb.connect(str(Path.home() / ".openclaw" / "workspace" / "memory" / "vector"))
        table = db.open_table("memories")
        
        results = table.search(embedding).limit(limit).to_list()
        
        # 格式化结果
        formatted = []
        for r in results:
            formatted.append({
                "id": r.get("id"),
                "text": r.get("text"),
                "category": r.get("category"),
                "importance": r.get("importance"),
                "timestamp": r.get("timestamp"),
                "score": 1 - r.get("_distance", 0),  # 转换为相似度
                "mode": "vec"
            })
        
        return formatted
    
    except Exception as e:
        print(f"⚠️ 向量搜索失败: {e}", file=sys.stderr)
        return []


# ============================================================
# BM25 关键词搜索
# ============================================================

def lex_search(query: str, limit: int = 5) -> List[Dict]:
    """
    BM25 关键词搜索
    0 Token 消耗，快速精确匹配
    """
    
    memories = load_all_memories()
    
    if not memories:
        return []
    
    # 构建 BM25 索引
    bm25 = BM25()
    bm25.fit(memories)
    
    # 搜索
    results = bm25.search(query, limit)
    
    # 格式化结果
    formatted = []
    for idx, score, doc in results:
        formatted.append({
            "id": f"mem_{idx}",
            "text": doc.get("text"),
            "category": doc.get("category"),
            "importance": doc.get("importance"),
            "timestamp": doc.get("timestamp", "").isoformat() if isinstance(doc.get("timestamp"), datetime) else str(doc.get("timestamp", "")),
            "score": float(score),
            "mode": "lex"
        })
    
    return formatted


# ============================================================
# 向量语义搜索
# ============================================================

def vec_search(query: str, limit: int = 5) -> List[Dict]:
    """
    向量语义搜索
    需要 Ollama embedding
    """
    
    embedding = get_ollama_embedding(query)
    
    if embedding is None:
        return []
    
    return search_vector_by_embedding(embedding, limit)


# ============================================================
# RRF 融合 (Reciprocal Rank Fusion)
# ============================================================

def rrf_fusion(results_list: List[List[Dict]], k: int = 60) -> List[Dict]:
    """
    RRF 融合多个搜索结果
    
    RRF(d) = Σ 1/(k + rank(d))
    
    k: 平滑参数，通常 60
    """
    
    # 收集所有文档
    doc_scores = defaultdict(float)
    doc_data = {}
    
    for results in results_list:
        for rank, doc in enumerate(results, 1):
            doc_id = doc.get("id") or doc.get("text", "")[:50]
            
            # RRF 分数
            doc_scores[doc_id] += 1.0 / (k + rank)
            
            # 保存文档数据（保留最高分的版本）
            if doc_id not in doc_data:
                doc_data[doc_id] = doc
    
    # 排序
    sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
    
    # 返回结果
    fused = []
    for doc_id, score in sorted_docs:
        doc = doc_data[doc_id].copy()
        doc["rrf_score"] = score
        doc["mode"] = "hybrid"
        fused.append(doc)
    
    return fused


# ============================================================
# 三重混合搜索
# ============================================================

def triple_search(query: str, limit: int = 5) -> List[Dict]:
    """
    三重混合搜索
    
    1. BM25 关键词搜索 (lex)
    2. 向量语义搜索 (vec)
    3. HyDe 假设文档搜索 (hyde)
    
    使用 RRF 融合结果
    """
    
    # 并行执行三种搜索
    lex_results = lex_search(query, limit * 2)
    vec_results = vec_search(query, limit * 2)
    hyde_results = hyde_search(query, limit * 2)
    
    # RRF 融合
    fused = rrf_fusion([lex_results, vec_results, hyde_results])
    
    # 返回 top N
    return fused[:limit]


# ============================================================
# CLI 接口
# ============================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory HyDe Search")
    parser.add_argument("query", help="搜索查询")
    parser.add_argument("--mode", choices=["lex", "vec", "hyde", "hybrid"], default="hybrid")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    
    args = parser.parse_args()
    
    # 执行搜索
    if args.mode == "lex":
        results = lex_search(args.query, args.limit)
    elif args.mode == "vec":
        results = vec_search(args.query, args.limit)
    elif args.mode == "hyde":
        results = hyde_search(args.query, args.limit)
    else:
        results = triple_search(args.query, args.limit)
    
    # 输出
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"🔍 搜索结果 ({args.mode} 模式, {len(results)} 条):\n")
        for i, r in enumerate(results, 1):
            score = r.get("score", r.get("rrf_score", 0))
            print(f"  {i}. [{r.get('mode', 'unknown')}] [score={score:.3f}]")
            print(f"     {r.get('text', '')[:80]}...")
            print()


if __name__ == "__main__":
    main()
