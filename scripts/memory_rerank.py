#!/usr/bin/env python3
"""
RAG Rerank - Cross-Encoder 重排序

QMD 的核心优势：对 BM25+Vector 结果进行 Rerank
"""

import numpy as np
from typing import List, Dict, Tuple


class CrossEncoderRerank:
    """Cross-Encoder 重排序"""
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载 Cross-Encoder 模型"""
        try:
            from sentence_transformers import CrossEncoder
            # 使用小型 Cross-Encoder
            self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            print("✅ Cross-Encoder 模型加载成功")
        except ImportError:
            print("⚠️ sentence-transformers 未安装，使用简单重排")
            self.model = None
    
    def rerank(self, query: str, results: List[Dict], top_k: int = 10) -> List[Dict]:
        """
        对搜索结果进行 Rerank
        
        Args:
            query: 查询
            results: BM25+Vector 混合搜索结果
            top_k: 返回前 K 个
        
        Returns:
            重排后的结果
        """
        if not results:
            return []
        
        if self.model is None:
            # 降级：使用简单评分
            return self._simple_rerank(query, results, top_k)
        
        try:
            # Cross-Encoder 评分
            pairs = [(query, r.get("text", "")) for r in results]
            scores = self.model.predict(pairs)
            
            # 合并原始分数和 Cross-Encoder 分数
            reranked = []
            for i, r in enumerate(results):
                # 混合评分：原始分 * 0.3 + rerank分 * 0.7
                original_score = r.get("score", r.get("hybrid_score", 0))
                cross_score = float(scores[i])
                final_score = original_score * 0.3 + cross_score * 0.7
                
                reranked.append({
                    **r,
                    "cross_score": cross_score,
                    "final_score": final_score
                })
            
            # 按 final_score 排序
            reranked.sort(key=lambda x: x["final_score"], reverse=True)
            return reranked[:top_k]
            
        except Exception as e:
            print(f"Rerank 失败: {e}")
            return results[:top_k]
    
    def _simple_rerank(self, query: str, results: List[Dict], top_k: int) -> List[Dict]:
        """简单的重排序（无模型）"""
        query_words = set(query.lower().split())
        
        for r in results:
            text = r.get("text", "").lower()
            text_words = set(text.split())
            
            # 计算关键词重叠
            overlap = len(query_words & text_words)
            
            # 综合评分
            original = r.get("score", r.get("hybrid_score", 0))
            r["cross_score"] = overlap / max(len(query_words), 1)
            r["final_score"] = original * 0.5 + r["cross_score"] * 0.5
        
        results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        return results[:top_k]


def rerank_results(query: str, results: List[Dict], top_k: int = 10) -> List[Dict]:
    """便捷函数"""
    reranker = CrossEncoderRerank()
    return reranker.rerank(query, results, top_k)


if __name__ == "__main__":
    print("=" * 50)
    print("Rerank 测试")
    print("=" * 50)
    
    reranker = CrossEncoderRerank()
    
    # 测试数据
    results = [
        {"text": "用户喜欢简洁的界面设计", "score": 0.8},
        {"text": "微服务架构性能很好", "score": 0.7},
        {"text": "Python 是编程语言", "score": 0.6},
        {"text": "界面设计需要简洁", "score": 0.5},
    ]
    
    query = "用户界面设计"
    
    print(f"\n🔍 查询: {query}")
    print("\n原始结果:")
    for r in results:
        print(f"  [{r['score']:.2f}] {r['text']}")
    
    reranked = reranker.rerank(query, results)
    
    print("\n重排后:")
    for r in reranked:
        print(f"  [{r.get('final_score', 0):.2f}] {r['text']}")
    
    print("\n✅ Rerank 测试完成")
