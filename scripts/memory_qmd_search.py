#!/usr/bin/env python3
"""
Memory QMD Search - QMD-like search for unified-memory

Features:
- BM25 keyword search (local, no LLM)
- Vector semantic search (Ollama local)
- RRF hybrid fusion (no LLM needed)
- Local reranking (optional, small model)
- Snippet-level return (save tokens)

Based on QMD architecture by tobi (https://github.com/tobi/qmd)
"""

import json
import math
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
MEMORY_FILE = MEMORY_DIR / "memories.json"

# Ollama 配置
OLLAMA_URL = "http://localhost:11434"

# ============ BM25 搜索引擎 ============

class BM25Index:
    """BM25 倒排索引 - 完全本地，不调用 LLM"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0
        self.inverted_index: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.doc_count: int = 0
        self.idf_cache: Dict[str, float] = {}
        
    def tokenize(self, text: str) -> List[str]:
        """简单的分词（中英文）"""
        # 中文按字符，英文按单词
        tokens = []
        # 英文单词
        tokens.extend(re.findall(r'[a-zA-Z]+', text.lower()))
        # 中文字符
        tokens.extend(re.findall(r'[\u4e00-\u9fff]', text))
        # 数字
        tokens.extend(re.findall(r'\d+', text))
        return tokens
    
    def index(self, documents: List[Dict[str, Any]]):
        """建立索引"""
        self.doc_count = len(documents)
        total_length = 0
        
        for doc in documents:
            doc_id = doc.get("id", str(hash(doc.get("text", ""))))
            text = doc.get("text", "")
            tokens = self.tokenize(text)
            
            self.doc_lengths[doc_id] = len(tokens)
            total_length += len(tokens)
            
            # 统计词频
            term_freq = defaultdict(int)
            for token in tokens:
                term_freq[token] += 1
            
            # 更新倒排索引
            for term, freq in term_freq.items():
                self.inverted_index[term][doc_id] = freq
        
        self.avg_doc_length = total_length / self.doc_count if self.doc_count > 0 else 0
        
    def _idf(self, term: str) -> float:
        """计算 IDF"""
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        df = len(self.inverted_index.get(term, {}))
        if df == 0:
            return 0
        
        idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)
        self.idf_cache[term] = idf
        return idf
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """BM25 搜索"""
        query_tokens = self.tokenize(query)
        scores: Dict[str, float] = defaultdict(float)
        
        for term in query_tokens:
            if term not in self.inverted_index:
                continue
            
            idf = self._idf(term)
            
            for doc_id, tf in self.inverted_index[term].items():
                doc_length = self.doc_lengths.get(doc_id, 0)
                
                # BM25 公式
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
                scores[doc_id] += idf * numerator / denominator
        
        # 排序
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


# ============ 向量搜索 ============

class VectorSearch:
    """向量搜索 - 使用本地 Ollama"""
    
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self._query_cache: Dict[str, List[float]] = {}
        
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """获取向量（使用缓存）"""
        if self.use_cache and text in self._query_cache:
            return self._query_cache[text]
        
        try:
            import requests
            response = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": "nomic-embed-text:latest", "prompt": text},
                timeout=5
            )
            if response.status_code == 200:
                embedding = response.json().get("embedding")
                if self.use_cache:
                    self._query_cache[text] = embedding
                return embedding
        except Exception as e:
            print(f"[VectorSearch] Error: {e}")
        
        return None
    
    def search(self, query: str, table, top_k: int = 10) -> List[Dict]:
        """向量搜索 - 修复版 v0.3.0（兼容无向量索引的情况）"""
        embedding = self.get_embedding(query)
        if not embedding:
            return []
        
        try:
            # 尝试向量搜索（需要向量索引）
            results = table.search(embedding, vector_column_name="vector").limit(top_k).to_list()
            return results
        except Exception as e:
            # 如果向量索引不可用，回退到 BM25
            print(f"[VectorSearch] 向量索引不可用，回退到 BM25: {str(e)[:50]}...")
            return []


# ============ RRF 混合搜索 ============

class HybridSearch:
    """RRF (Reciprocal Rank Fusion) 混合搜索"""
    
    def __init__(self, k: int = 60):
        self.k = k  # RRF 常数
        
    def fuse(self, 
             bm25_results: List[Tuple[str, float]], 
             vector_results: List[Dict],
             bm25_weight: float = 1.0,
             vector_weight: float = 1.0) -> List[Tuple[str, float]]:
        """RRF 融合"""
        scores: Dict[str, float] = defaultdict(float)
        
        # BM25 分数
        for rank, (doc_id, _) in enumerate(bm25_results):
            scores[doc_id] += bm25_weight / (self.k + rank + 1)
        
        # 向量分数
        for rank, result in enumerate(vector_results):
            doc_id = result.get("id", str(hash(result.get("text", ""))))
            scores[doc_id] += vector_weight / (self.k + rank + 1)
        
        # 排序
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked


# ============ 本地重排器 ============

class LocalReranker:
    """本地重排器 - 使用小模型"""
    
    def __init__(self, model: str = "qwen2.5:0.5b"):
        self.model = model
        self.ollama_url = OLLAMA_URL
        
    def rerank(self, query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
        """重排文档"""
        if not documents:
            return []
        
        # 构建提示词
        prompt = f"""根据查询，对以下文档进行相关性打分（0-10分）。
        
查询: {query}

文档:
"""
        for i, doc in enumerate(documents[:10]):  # 最多 10 个
            prompt += f"\n[{i}] {doc.get('text', '')[:200]}...\n"
        
        prompt += "\n\n请返回最相关的文档编号列表，格式: [0, 2, 5]（按相关性降序）"
        
        try:
            import requests
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                output = response.json().get("response", "")
                # 解析结果
                import re
                matches = re.findall(r'\d+', output)
                ranked_indices = [int(m) for m in matches if int(m) < len(documents)]
                
                # 返回重排后的文档
                return [documents[i] for i in ranked_indices[:top_k]]
        except Exception as e:
            print(f"[LocalReranker] Error: {e}")
        
        # 失败时返回原顺序
        return documents[:top_k]


# ============ QMD 风格搜索 ============

class QMDSearch:
    """QMD 风格搜索 - 统一接口
    
    三层架构：
    1. BM25（默认，0 Token）- 纯关键词匹配
    2. 向量增强（可选，~100 Token）- 语义搜索
    3. LLM 重排（可选，额外 Token）- 智能重排
    
    配置方式：
    - use_vector=True: 启用向量搜索（需要 Ollama）
    - use_llm_rerank=True: 启用 LLM 重排（需要配置 llm_model）
    - llm_model: 重排用的模型，默认 qwen2.5:0.5b
    """
    
    def __init__(self, 
                 use_vector: bool = True,
                 use_llm_rerank: bool = False,
                 llm_model: str = "qwen2.5:0.5b"):
        self.bm25 = BM25Index()
        self.vector = VectorSearch() if use_vector else None
        self.hybrid = HybridSearch() if use_vector else None
        self.reranker = LocalReranker(model=llm_model) if use_llm_rerank else None
        
        self.use_vector = use_vector
        self.use_llm_rerank = use_llm_rerank
        
        self._indexed = False
        self._documents: List[Dict] = []
        self._doc_map: Dict[str, Dict] = {}
        
    def _load_documents(self) -> List[Dict]:
        """加载记忆（优先从向量库）"""
        docs = []
        
        # 优先从向量库加载（ID 一致）
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            if "memories" in db.list_tables():
                table = db.open_table("memories")
                # 用一个简单查询获取所有记录
                import requests
                response = requests.post(
                    f"{OLLAMA_URL}/api/embeddings",
                    json={"model": "nomic-embed-text:latest", "prompt": "memory"},
                    timeout=5
                )
                if response.status_code == 200:
                    vec = response.json().get("embedding")
                    # 大 limit 获取所有
                    all_docs = table.search(vec).limit(1000).to_list()
                    for d in all_docs:
                        docs.append({
                            "id": d.get("id"),
                            "text": d.get("text", ""),
                            "category": d.get("category", "unknown"),
                            "scope": d.get("scope", "agent:main"),
                            "importance": d.get("importance", 0.5),
                            "timestamp": d.get("timestamp", ""),
                        })
                    print(f"[QMDSearch] Loaded {len(docs)} docs from vector DB")
                    return docs
        except Exception as e:
            print(f"[QMDSearch] Vector DB load error: {e}")
        
        # 回退到 JSON 文件
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else data.get("memories", [])
            except Exception as e:
                print(f"[QMDSearch] JSON load error: {e}")
        
        return []
    
    def index(self):
        """建立索引"""
        self._documents = self._load_documents()
        
        # 建立 BM25 索引
        self.bm25.index(self._documents)
        
        # 建立文档映射
        self._doc_map = {}
        for doc in self._documents:
            doc_id = doc.get("id", str(hash(doc.get("text", ""))))
            self._doc_map[doc_id] = doc
        
        self._indexed = True
        print(f"[QMDSearch] Indexed {len(self._documents)} documents")
        
    def _get_vector_table(self):
        """获取向量表"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            return db.open_table("memories")
        except Exception as e:
            print(f"[QMDSearch] Vector DB error: {e}")
            return None
    
    def search(self, 
               query: str, 
               mode: str = "auto",
               top_k: int = 5,
               snippet_size: int = 200,
               min_score: float = 0.01) -> List[Dict]:
        """
        搜索记忆
        
        Args:
            query: 查询文本
            mode: 搜索模式
                - "auto": 根据配置自动选择（推荐）
                - "bm25": 纯关键词（0 Token）
                - "vector": 纯向量（需要 Ollama）
                - "hybrid": 混合搜索（需要 Ollama）
            top_k: 返回数量
            snippet_size: 片段大小（字符）
            min_score: 最小分数
        
        Returns:
            匹配的记忆列表
        """
        if not self._indexed:
            self.index()
        
        results = []
        
        # 自动模式：根据配置选择
        if mode == "auto":
            if self.use_vector:
                mode = "hybrid"
            else:
                mode = "bm25"
        
        if mode == "bm25":
            # 纯 BM25（0 Token）
            bm25_results = self.bm25.search(query, top_k * 2)
            for doc_id, score in bm25_results:
                if score >= min_score and doc_id in self._doc_map:
                    doc = self._doc_map[doc_id].copy()
                    doc["score"] = score
                    doc["snippet"] = doc.get("text", "")[:snippet_size]
                    doc["mode"] = "bm25"
                    results.append(doc)
        
        elif mode == "vector" and self.vector:
            # 纯向量
            table = self._get_vector_table()
            if table:
                vector_results = self.vector.search(query, table, top_k * 2)
                for res in vector_results:
                    if res.get("_distance", 1) < 1 - min_score:
                        doc_id = res.get("id", str(hash(res.get("text", ""))))
                        if doc_id in self._doc_map:
                            doc = self._doc_map[doc_id].copy()
                            doc["score"] = 1 - res.get("_distance", 0.5)
                            doc["snippet"] = doc.get("text", "")[:snippet_size]
                            doc["mode"] = "vector"
                            results.append(doc)
        
        elif mode == "hybrid" and self.vector and self.hybrid:
            # RRF 混合
            bm25_results = self.bm25.search(query, top_k * 2)
            
            table = self._get_vector_table()
            vector_results = []
            if table:
                vector_results = self.vector.search(query, table, top_k * 2)
            
            # RRF 融合
            fused = self.hybrid.fuse(bm25_results, vector_results)
            
            for doc_id, score in fused[:top_k * 2]:
                if score >= min_score and doc_id in self._doc_map:
                    doc = self._doc_map[doc_id].copy()
                    doc["score"] = score
                    doc["snippet"] = doc.get("text", "")[:snippet_size]
                    doc["mode"] = "hybrid"
                    results.append(doc)
        
        # LLM 重排（可选增强）
        if self.reranker and results:
            results = self.reranker.rerank(query, results, top_k)
        
        # 重排（可选）
        if self.reranker and results:
            results = self.reranker.rerank(query, results, top_k)
        
        return results[:top_k]
    
    def get_context(self, query: str, max_tokens: int = 2000) -> str:
        """
        获取上下文（Token 优化版本）
        
        只返回相关片段，不返回全文
        自动选择最佳模式
        """
        results = self.search(query, mode="auto", top_k=10)
        
        context_parts = []
        total_chars = 0
        
        for res in results:
            snippet = res.get("snippet", res.get("text", "")[:200])
            if total_chars + len(snippet) > max_tokens * 2:  # 粗略估计
                break
            
            category = res.get('category', 'unknown')
            mode_tag = res.get('mode', 'auto')
            context_parts.append(f"- [{category}|{mode_tag}] {snippet}")
            total_chars += len(snippet)
        
        return "\n".join(context_parts)


# ============ CLI 接口 ============

def load_config() -> Dict:
    """加载配置文件"""
    config_file = MEMORY_DIR / "qmd_config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    
    # 默认配置
    return {
        "use_vector": True,
        "use_llm_rerank": False,
        "llm_model": "qwen2.5:0.5b"
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="QMD-like Memory Search")
    parser.add_argument("action", choices=["search", "context", "index", "status", "config"])
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument("--mode", "-m", choices=["auto", "bm25", "vector", "hybrid"], default="auto")
    parser.add_argument("--top-k", "-k", type=int, default=5)
    parser.add_argument("--snippet-size", "-s", type=int, default=200)
    parser.add_argument("--rerank", action="store_true", help="Enable LLM reranking")
    parser.add_argument("--no-vector", action="store_true", help="Disable vector search")
    parser.add_argument("--set-config", help="Set config (JSON)")
    
    args = parser.parse_args()
    
    # 配置操作
    if args.action == "config":
        config_file = MEMORY_DIR / "qmd_config.json"
        if args.set_config:
            try:
                config = json.loads(args.set_config)
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
                print(f"✅ Config saved to {config_file}")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            config = load_config()
            print("📋 Current config:")
            print(json.dumps(config, indent=2))
        return
    
    # 加载配置
    config = load_config()
    
    # 命令行参数覆盖配置
    use_vector = config.get("use_vector", True) and not args.no_vector
    use_llm_rerank = config.get("use_llm_rerank", False) or args.rerank
    llm_model = config.get("llm_model", "qwen2.5:0.5b")
    
    searcher = QMDSearch(
        use_vector=use_vector,
        use_llm_rerank=use_llm_rerank,
        llm_model=llm_model
    )
    
    if args.action == "index":
        searcher.index()
        print("✅ Index complete")
    
    elif args.action == "status":
        searcher.index()
        print(f"📊 Documents: {len(searcher._documents)}")
        print(f"📊 Indexed terms: {len(searcher.bm25.inverted_index)}")
        print(f"📊 Vector search: {'✅' if use_vector else '❌'}")
        print(f"📊 LLM rerank: {'✅' if use_llm_rerank else '❌'} ({llm_model})")
    
    elif args.action == "search":
        if not args.query:
            print("❌ --query required")
            return
        
        results = searcher.search(
            args.query, 
            mode=args.mode, 
            top_k=args.top_k,
            snippet_size=args.snippet_size
        )
        
        for i, res in enumerate(results, 1):
            mode_tag = res.get("mode", "bm25")
            print(f"\n[{i}] Score: {res.get('score', 0):.4f} ({mode_tag})")
            print(f"    Category: {res.get('category', 'unknown')}")
            print(f"    Snippet: {res.get('snippet', '')[:100]}...")
    
    elif args.action == "context":
        if not args.query:
            print("❌ --query required")
            return
        
        context = searcher.get_context(args.query)
        print(context)


if __name__ == "__main__":
    main()
