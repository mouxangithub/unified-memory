#!/usr/bin/env python3
"""
完整 Rerank 实现 - 支持真实 Cross-Encoder 模型

如果 sentence-transformers 未安装，使用降级方案
"""

import numpy as np
from typing import List, Dict, Tuple


class Reranker:
    """
    重排序器
    
    支持：
    1. Cross-Encoder (真实模型)
    2. 轻量级重排 (无模型)
    3. BM25 分数融合
    """
    
    def __init__(self):
        self.model = None
        self.model_name = None
        self._load_model()
    
    def _load_model(self):
        """加载模型"""
        try:
            from sentence_transformers import CrossEncoder
            
            # 尝试加载小型模型
            model_names = [
                'cross-encoder/ms-marco-MiniLM-L-6-v2',
                'cross-encoder/ms-marco-TinyBERT-L-2-v2',
                'cross-encoder/quora-roberta-base',
            ]
            
            for name in model_names:
                try:
                    self.model = CrossEncoder(name)
                    self.model_name = name
                    print(f"✅ Cross-Encoder 模型加载: {name}")
                    return
                except:
                    continue
            
            print("⚠️ 所有 Cross-Encoder 模型加载失败，使用降级")
            self.model = None
            
        except ImportError:
            print("⚠️ sentence-transformers 未安装，使用降级方案")
            self.model = None
    
    def rerank(self, query: str, results: List[Dict], top_k: int = 10) -> List[Dict]:
        """
        重排序
        
        Args:
            query: 查询
            results: 初始搜索结果 [{"text": ..., "score": ...}, ...]
            top_k: 返回前 k 个
        
        Returns:
            重排后的结果
        """
        if not results:
            return []
        
        if self.model is not None:
            return self._rerank_with_model(query, results, top_k)
        else:
            return self._rerank_fallback(query, results, top_k)
    
    def _rerank_with_model(self, query: str, results: List[Dict], top_k: int) -> List[Dict]:
        """使用真实模型重排"""
        try:
            # 构造 pairs
            pairs = [(query, r.get("text", "")) for r in results]
            
            # 模型预测
            scores = self.model.predict(pairs)
            
            # 融合分数
            reranked = []
            for i, r in enumerate(results):
                original_score = r.get("score", r.get("hybrid_score", 0))
                cross_score = float(scores[i])
                
                # 加权融合
                # 原始分 * 0.3 + cross-encoder 分 * 0.7
                final_score = original_score * 0.3 + cross_score * 0.7
                
                reranked.append({
                    **r,
                    "cross_score": cross_score,
                    "original_score": original_score,
                    "final_score": final_score
                })
            
            # 按 final_score 排序
            reranked.sort(key=lambda x: x["final_score"], reverse=True)
            
            return reranked[:top_k]
            
        except Exception as e:
            print(f"⚠️ 模型预测失败: {e}")
            return self._rerank_fallback(query, results, top_k)
    
    def _rerank_fallback(self, query: str, results: List[Dict], top_k: int) -> List[Dict]:
        """降级重排（无模型）"""
        # 关键词重叠评分
        query_words = set(query.lower().split())
        
        reranked = []
        for r in results:
            text = r.get("text", "").lower()
            text_words = set(text.split())
            
            # 计算重叠
            overlap = len(query_words & text_words)
            union = len(query_words | text_words)
            jaccard = overlap / union if union > 0 else 0
            
            # 关键词位置
            positions = []
            for i, word in enumerate(query_words):
                if word in text_words:
                    positions.append(i)
            position_score = 1.0 / (min(positions) + 1) if positions else 0
            
            # 综合评分
            original = r.get("score", r.get("hybrid_score", 0))
            final = original * 0.4 + jaccard * 0.3 + position_score * 0.3
            
            reranked.append({
                **r,
                "cross_score": jaccard,
                "original_score": original,
                "final_score": final
            })
        
        reranked.sort(key=lambda x: x["final_score"], reverse=True)
        return reranked[:top_k]
    
    def cross_encode(self, pairs: List[Tuple[str, str]]) -> List[float]:
        """直接使用 Cross-Encoder 计算相关性"""
        if self.model is None:
            return [0.0] * len(pairs)
        
        try:
            return self.model.predict(pairs).tolist()
        except:
            return [0.0] * len(pairs)


def rerank(query: str, results: List[Dict], top_k: int = 10) -> List[Dict]:
    """便捷函数"""
    reranker = Reranker()
    return reranker.rerank(query, results, top_k)


if __name__ == "__main__":
    print("=" * 50)
    print("完整 Rerank 测试")
    print("=" * 50)
    
    reranker = Reranker()
    
    # 测试数据
    results = [
        {"text": "用户喜欢简洁的界面设计", "score": 0.8},
        {"text": "微服务架构性能很好", "score": 0.7},
        {"text": "Python 是编程语言", "score": 0.6},
        {"text": "界面设计需要简洁", "score": 0.5},
        {"text": "数据库使用 PostgreSQL", "score": 0.4},
    ]
    
    query = "用户界面设计"
    
    print(f"\n🔍 查询: {query}")
    print("\n原始结果:")
    for r in results:
        print(f"  [{r['score']:.2f}] {r['text']}")
    
    reranked = reranker.rerank(query, results, top_k=5)
    
    print("\n重排后:")
    for r in reranked:
        print(f"  [{r.get('final_score', 0):.2f}] {r['text']}")
        print(f"       (原始: {r.get('original_score', 0):.2f}, 交叉: {r.get('cross_score', 0):.2f})")
    
    print("\n✅ Rerank 测试完成")
