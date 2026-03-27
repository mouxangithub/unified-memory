#!/usr/bin/env python3
"""
FAISS 向量索引 - 高性能近似最近邻搜索

核心：毫秒级搜索，支持百万级向量
"""

import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
INDEX_FILE = MEMORY_DIR / "faiss_index.bin"
META_FILE = MEMORY_DIR / "faiss_meta.json"


class FAISSIndex:
    """FAISS 向量索引"""
    
    def __init__(self, dim: int = 768):
        self.dim = dim
        self.index = None
        self.use_numpy = True
        self.vectors = None
        self.meta = {"ids": [], "texts": []}
        self._load()
    
    def _load(self):
        """加载索引"""
        try:
            import faiss
            self.use_numpy = False
        except ImportError:
            self.use_numpy = True
        
        if INDEX_FILE.exists() and not self.use_numpy:
            try:
                import faiss
                self.index = faiss.read_index(str(INDEX_FILE))
                with open(META_FILE, "r") as f:
                    self.meta = json.load(f)
            except:
                self.index = None
    
    def _save(self):
        """保存索引"""
        if self.index is None and self.vectors is None:
            return
        
        try:
            if not self.use_numpy:
                import faiss
                faiss.write_index(self.index, str(INDEX_FILE))
            with open(META_FILE, "w") as f:
                json.dump(self.meta, f)
        except:
            pass
    
    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        """L2 归一化"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / (norms + 1e-8)
    
    def build(self, memories: List[Dict]):
        """构建索引"""
        if not memories:
            return
        
        vectors = []
        ids = []
        texts = []
        
        for mem in memories:
            vec = mem.get("vector", [])
            if vec and len(vec) == self.dim:
                vectors.append(vec)
                ids.append(mem.get("id", ""))
                texts.append(mem.get("text", "")[:100])
        
        if not vectors:
            print("⚠️ 没有有效向量")
            return
        
        vectors_np = np.array(vectors).astype('float32')
        vectors_np = self._normalize(vectors_np)
        
        if not self.use_numpy:
            try:
                import faiss
                self.index = faiss.IndexHNSWFlat(self.dim, 32)
                self.index.add(vectors_np)
                self.meta = {"ids": ids, "texts": texts}
                self._save()
                print(f"✅ 构建 HNSW 索引: {len(ids)} 条")
                return
            except:
                self.use_numpy = True
        
        # numpy 降级
        self.use_numpy = True
        self.vectors = vectors_np
        self.meta = {"ids": ids, "texts": texts}
        self._save()
        print(f"✅ 构建 numpy 索引: {len(ids)} 条")
    
    def search(self, query_vec: List[float], k: int = 10) -> List[Tuple[str, float]]:
        """搜索 Top-K"""
        if self.index is None and self.vectors is None:
            return []
        
        query_np = np.array([query_vec]).astype('float32')
        query_np = self._normalize(query_np)
        
        if not self.use_numpy and self.index is not None:
            try:
                import faiss
                D, I = self.index.search(query_np, k)
                results = []
                for i, idx in enumerate(I[0]):
                    if idx >= 0 and idx < len(self.meta["ids"]):
                        results.append((self.meta["ids"][idx], float(D[0][i])))
                return results
            except:
                pass
        
        # numpy 降级
        if self.vectors is not None:
            similarities = np.dot(self.vectors, query_np.T).flatten()
            top_k_idx = np.argsort(similarities)[-k:][::-1]
            return [(self.meta["ids"][i], float(similarities[i])) 
                    for i in top_k_idx if i < len(self.meta["ids"])]
        
        return []
    
    def get_stats(self) -> Dict:
        return {
            "total": len(self.meta["ids"]),
            "dim": self.dim,
            "backend": "numpy" if self.use_numpy else "faiss"
        }


def build_faiss_index(memories: List[Dict]) -> FAISSIndex:
    idx = FAISSIndex()
    idx.build(memories)
    return idx


if __name__ == "__main__":
    print("=" * 50)
    print("FAISS 索引测试")
    print("=" * 50)
    
    idx = FAISSIndex()
    memories = [
        {"id": "mem_1", "text": "用户喜欢简洁界面", "vector": [0.1] * 768},
        {"id": "mem_2", "text": "微服务架构", "vector": [0.2] * 768},
        {"id": "mem_3", "text": "Python 开发", "vector": [0.3] * 768},
    ]
    idx.build(memories)
    print(f"📊 统计: {idx.get_stats()}")
    results = idx.search([0.15] * 768, k=2)
    print(f"🔍 搜索结果: {results}")
    print("✅ FAISS 索引测试完成")
