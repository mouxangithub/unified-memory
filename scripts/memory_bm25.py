#!/usr/bin/env python3
"""
BM25 + 混合搜索

BM25 (Best Matching 25) 是信息检索经典算法
配合向量实现混合搜索
"""

import math
import numpy as np
from typing import List, Dict, Tuple


class BM25Index:
    """BM25 索引"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = []
        self.avgdl = 0
        self.doc_freqs = {}  # 词 -> 文档频率
        self.doc_len = []      # 每篇文档长度
    
    def build(self, texts: List[str]):
        """构建索引"""
        self.documents = texts
        self.doc_len = []
        self.doc_freqs = {}
        
        for doc in texts:
            # 分词 (简单 2-gram)
            words = self._tokenize(doc)
            self.doc_len.append(len(words))
            
            # 统计词频
            for word in set(words):
                self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1
        
        # 平均文档长度
        self.avgdl = sum(self.doc_len) / len(self.doc_len) if self.doc_len else 0
    
    def _tokenize(self, text: str) -> List[str]:
        """简单中文分词 (2-gram)"""
        text = text.lower().replace("，", "").replace("。", "").replace("！", "").replace("？", "")
        return [text[i:i+2] for i in range(len(text)-1)]
    
    def _score(self, doc: str, query: str) -> float:
        """计算 BM25 分数"""
        words = self._tokenize(doc)
        query_words = self._tokenize(query)
        
        score = 0.0
        N = len(self.documents)
        
        for qw in query_words:
            if qw not in self.doc_freqs:
                continue
            
            df = self.doc_freqs[qw]
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
            
            # 词在文档中的频率
            tf = words.count(qw)
            
            # BM25 公式
            score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * len(words) / self.avgdl))
        
        return score
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """搜索"""
        scores = []
        for i, doc in enumerate(self.documents):
            score = self._score(doc, query)
            if score > 0:
                scores.append({
                    "index": i,
                    "text": doc,
                    "score": score
                })
        
        # 排序
        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:top_k]


def bm25_search(query: str, texts: List[str], top_k: int = 10) -> List[Dict]:
    """BM25 搜索便捷函数"""
    if not query or not texts:
        return []
    
    index = BM25Index()
    index.build(texts)
    return index.search(query, top_k)


def hybrid_search(query: str, texts: List[str], vectors: List[List[float]], 
                 top_k: int = 10, alpha: float = 0.5) -> List[Dict]:
    """
    混合搜索：BM25 + 向量
    
    Args:
        query: 查询
        texts: 文档列表
        vectors: 向量列表
        top_k: 返回数量
        alpha: BM25 权重 (1-alpha 是向量权重)
    
    Returns:
        混合排序结果
    """
    if not query or not texts:
        return []
    
    # BM25 搜索
    bm25_index = BM25Index()
    bm25_index.build(texts)
    bm25_results = bm25_index.search(query, top_k * 2)
    
    # 向量相似度
    query_vec = _get_query_vector(query)
    if query_vec and vectors and len(vectors[0]) == len(query_vec):
        vector_scores = _cosine_similarity(query_vec, vectors)
    else:
        vector_scores = [0.0] * len(texts)
    
    # 归一化 BM25 分数
    max_bm25 = max(r["score"] for r in bm25_results) if bm25_results else 1.0
    max_vec = max(vector_scores) if vector_scores else 1.0
    
    # 融合分数
    results = []
    seen = set()
    
    for r in bm25_results:
        idx = r["index"]
        if idx in seen:
            continue
        seen.add(idx)
        
        bm25_score = r["score"] / max_bm25 if max_bm25 > 0 else 0
        vec_score = vector_scores[idx] / max_vec if max_vec > 0 else 0
        
        hybrid_score = alpha * bm25_score + (1 - alpha) * vec_score
        
        results.append({
            "index": idx,
            "text": texts[idx],
            "bm25_score": r["score"],
            "vector_score": vector_scores[idx],
            "hybrid_score": hybrid_score,
            "score": hybrid_score
        })
    
    # 按混合分数排序
    results.sort(key=lambda x: x["hybrid_score"], reverse=True)
    
    return results[:top_k]


def _get_query_vector(query: str) -> List[float]:
    """获取查询向量（简化版，实际应该调用 Ollama）"""
    # 简单 hash 作为伪向量
    import hashlib
    h = hashlib.md5(query.encode()).digest()
    return [float(b) / 255.0 * 2 - 1 for b in h[:128]] + [0.0] * 640


def _cosine_similarity(a: List[float], b: List[List[float]]) -> List[float]:
    """计算余弦相似度"""
    a = np.array(a)
    scores = []
    for vec in b:
        vec = np.array(vec)
        dot = np.dot(a, vec)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(vec)
        if norm_a * norm_b == 0:
            scores.append(0.0)
        else:
            scores.append(float(dot / (norm_a * norm_b)))
    return scores


if __name__ == "__main__":
    print("=" * 50)
    print("BM25 + 混合搜索测试")
    print("=" * 50)
    
    texts = [
        "用户喜欢简洁的界面设计",
        "采用微服务架构提升性能",
        "Python 是一种广泛使用的编程语言",
        "数据库设计需要遵循三范式",
        "微服务之间通过 API 进行通信"
    ]
    
    # BM25 测试
    print("\n📝 BM25 搜索 '界面':")
    results = bm25_search("界面", texts, top_k=3)
    for r in results:
        print(f"  [{r['score']:.3f}] {r['text']}")
    
    # 混合搜索测试
    print("\n🔍 混合搜索 '微服务':")
    vectors = [[0.1] * 768, [0.2] * 768, [0.3] * 768, [0.4] * 768, [0.5] * 768]
    results = hybrid_search("微服务", texts, vectors, alpha=0.5)
    for r in results[:3]:
        print(f"  [{r['hybrid_score']:.3f}] {r['text']}")
        print(f"       BM25={r['bm25_score']:.3f}, Vec={r['vector_score']:.3f}")
    
    print("\n✅ BM25 + 混合搜索测试完成")

# ===== 缓存增强 =====
from memory_cache import get_cache


def cached_search(query: str, texts: List[str], top_k: int = 10) -> List[Dict]:
    """
    带缓存的搜索
    
    缓存策略：
    1. 先查缓存（< 1ms）
    2. 未命中则搜索并写入缓存
    """
    cache = get_cache()
    
    # 尝试从缓存获取
    results = cache.get(query, top_k)
    if results is not None:
        return [{"source": "cache", **r} for r in results[:top_k]]
    
    # 未命中，执行搜索
    results = hybrid_search(query, texts, None, top_k)
    
    # 写入缓存
    cache.set(query, results, top_k)
    
    return results


def benchmark_cacheImprovement(texts_count: int = 1000, queries: int = 100):
    """Benchmark 缓存效果"""
    import time
    
    print(f"\n📊 缓存效果 Benchmark ({texts_count} 条文本, {queries} 次查询)")
    print("-" * 50)
    
    # 生成测试数据
    texts = [f"测试文本 {i} 关于某个主题 {i % 100}" for i in range(texts_count)]
    
    # 第一次：冷启动（无缓存）
    print("\n🔥 冷启动（无缓存）...")
    start = time.time()
    for i in range(queries):
        hybrid_search(f"主题 {i % 10}", texts, None, top_k=10)
    cold_time = time.time() - start
    print(f"  耗时: {cold_time:.3f}s ({cold_time/queries*1000:.2f}ms/查询)")
    
    # 第二次：热启动（有缓存）
    print("\n🚀 热启动（有缓存）...")
    start = time.time()
    for i in range(queries):
        cached_search(f"主题 {i % 10}", texts, top_k=10)
    hot_time = time.time() - start
    print(f"  耗时: {hot_time:.3f}s ({hot_time/queries*1000:.2f}ms/查询)")
    
    # 统计
    speedup = cold_time / hot_time if hot_time > 0 else 1
    cache_stats = get_cache().stats()
    
    print(f"\n📈 加速比: {speedup:.1f}x")
    print(f"💾 缓存统计: {cache_stats}")
