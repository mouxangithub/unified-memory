#!/usr/bin/env python3
"""
Local GGUF Model Support - 本地模型支持
支持 GGUF 模型直接加载，无需 Ollama

优先级:
1. 本地 GGUF 模型 (llama-cpp-python)
2. Ollama API
3. 简单算法回退

Usage:
    from local_llm import get_embedder, get_reranker, get_llm
    
    embedder = get_embedder("nomic-embed-text")
    embedding = embedder.embed("文本")
    
    reranker = get_reranker()
    results = reranker.rerank("查询", ["文档1", "文档2"])
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass

# 配置
MODELS_DIR = Path.home() / ".cache" / "local-llm" / "models"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


# =============================================================================
# Embedding 接口
# =============================================================================

class Embedder:
    """Embedding 基类"""
    
    def embed(self, text: str) -> Optional[List[float]]:
        raise NotImplementedError
    
    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        return [self.embed(t) for t in texts]


class OllamaEmbedder(Embedder):
    """Ollama Embedding"""
    
    def __init__(self, model: str = "nomic-embed-text:latest"):
        self.model = model
        self.available = self._check_available()
    
    def _check_available(self) -> bool:
        try:
            import requests
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            return r.ok
        except:
            return False
    
    def embed(self, text: str) -> Optional[List[float]]:
        if not self.available:
            return None
        
        try:
            import requests
            response = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=30
            )
            
            if response.ok:
                return response.json().get("embedding")
        except Exception as e:
            print(f"⚠️ Ollama embedding 失败: {e}", file=sys.stderr)
        
        return None


class LocalGGUFEmbedder(Embedder):
    """本地 GGUF Embedding"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model = None
        self._load_model()
    
    def _load_model(self):
        try:
            from llama_cpp import Llama
            
            if not self.model_path.exists():
                raise FileNotFoundError(f"模型不存在: {self.model_path}")
            
            self.model = Llama(
                str(self.model_path),
                embedding=True,
                verbose=False
            )
            
            print(f"✅ GGUF Embedding 模型已加载: {self.model_path.name}", file=sys.stderr)
        
        except ImportError:
            print("⚠️ llama-cpp-python 未安装，请运行: pip install llama-cpp-python", file=sys.stderr)
        except Exception as e:
            print(f"⚠️ 加载 GGUF 模型失败: {e}", file=sys.stderr)
    
    def embed(self, text: str) -> Optional[List[float]]:
        if not self.model:
            return None
        
        try:
            return self.model.embed(text)
        except Exception as e:
            print(f"⚠️ GGUF embedding 失败: {e}", file=sys.stderr)
            return None


class SimpleEmbedder(Embedder):
    """简单 Embedding（TF-IDF 风格，无需模型）"""
    
    def __init__(self):
        self.vocab = {}
        self.idf = {}
    
    def embed(self, text: str) -> List[float]:
        """简单哈希 embedding（768 维）"""
        # 使用哈希生成固定维度向量
        words = text.lower().split()
        embedding = [0.0] * 768
        
        for word in words:
            # 哈希到某个维度
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % 768
            embedding[idx] += 1.0
        
        # 归一化
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding


def get_embedder(model: str = "auto") -> Embedder:
    """
    获取 Embedder
    
    Args:
        model: 模型名称或路径
            - "auto": 自动选择（GGUF > Ollama > Simple）
            - "ollama:model": 使用 Ollama
            - "/path/to/model.gguf": 使用本地 GGUF
            - "simple": 使用简单算法
    
    Returns:
        Embedder 实例
    """
    if model == "simple":
        return SimpleEmbedder()
    
    if model.startswith("ollama:"):
        model_name = model.split(":", 1)[1]
        return OllamaEmbedder(model_name)
    
    if model.endswith(".gguf") or Path(model).exists():
        return LocalGGUFEmbedder(model)
    
    # Auto: 尝试顺序
    # 1. 检查默认 GGUF 模型
    default_gguf = MODELS_DIR / "nomic-embed-text-v1.5.f16.gguf"
    if default_gguf.exists():
        try:
            return LocalGGUFEmbedder(str(default_gguf))
        except:
            pass
    
    # 2. 尝试 Ollama
    ollama = OllamaEmbedder()
    if ollama.available:
        return ollama
    
    # 3. 回退到简单算法
    print("⚠️ 无可用 embedding 模型，使用简单算法", file=sys.stderr)
    return SimpleEmbedder()


# =============================================================================
# Reranker 接口
# =============================================================================

class Reranker:
    """Reranker 基类"""
    
    def rerank(self, query: str, documents: List[str], top_k: int = 5) -> List[Dict]:
        raise NotImplementedError


class OllamaReranker(Reranker):
    """Ollama Reranker"""
    
    def __init__(self, model: str = "qwen2.5:0.5b"):
        self.model = model
        self.available = self._check_available()
    
    def _check_available(self) -> bool:
        try:
            import requests
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            return r.ok
        except:
            return False
    
    def rerank(self, query: str, documents: List[str], top_k: int = 5) -> List[Dict]:
        if not self.available or not documents:
            return [{"index": i, "document": doc, "score": 0.5} for i, doc in enumerate(documents[:top_k])]
        
        results = []
        
        try:
            import requests
            
            for i, doc in enumerate(documents):
                prompt = f"Rate the relevance of this document to the query.\nQuery: {query}\nDocument: {doc[:500]}\nRelevance score (0.0-1.0):"
                
                response = requests.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": 10, "temperature": 0.0}
                    },
                    timeout=10
                )
                
                if response.ok:
                    text = response.json().get("response", "").strip()
                    try:
                        score = float(text.split()[0])
                        score = max(0.0, min(1.0, score))
                    except:
                        score = 0.5
                else:
                    score = 0.5
                
                results.append({"index": i, "document": doc, "score": score})
        
        except Exception as e:
            print(f"⚠️ Ollama rerank 失败: {e}", file=sys.stderr)
            results = [{"index": i, "document": doc, "score": 0.5} for i, doc in enumerate(documents)]
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


class SimpleReranker(Reranker):
    """简单 Reranker（基于关键词匹配）"""
    
    def rerank(self, query: str, documents: List[str], top_k: int = 5) -> List[Dict]:
        query_words = set(query.lower().split())
        results = []
        
        for i, doc in enumerate(documents):
            doc_words = set(doc.lower().split())
            
            # Jaccard 相似度
            intersection = len(query_words & doc_words)
            union = len(query_words | doc_words)
            score = intersection / union if union > 0 else 0.0
            
            results.append({"index": i, "document": doc, "score": score})
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


def get_reranker(model: str = "auto") -> Reranker:
    """
    获取 Reranker
    
    Args:
        model: 模型名称
            - "auto": 自动选择
            - "ollama:model": 使用 Ollama
            - "simple": 使用简单算法
    
    Returns:
        Reranker 实例
    """
    if model == "simple":
        return SimpleReranker()
    
    if model.startswith("ollama:"):
        model_name = model.split(":", 1)[1]
        return OllamaReranker(model_name)
    
    # Auto
    ollama = OllamaReranker()
    if ollama.available:
        return ollama
    
    return SimpleReranker()


# =============================================================================
# LLM 接口
# =============================================================================

class LLM:
    """LLM 基类"""
    
    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError


class OllamaLLM(LLM):
    """Ollama LLM"""
    
    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = model
        self.available = self._check_available()
    
    def _check_available(self) -> bool:
        try:
            import requests
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            return r.ok
        except:
            return False
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop: List[str] = None
    ) -> str:
        if not self.available:
            return f"[LLM 不可用] {prompt[:100]}..."
        
        try:
            import requests
            
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                        "stop": stop or []
                    }
                },
                timeout=60
            )
            
            if response.ok:
                return response.json().get("response", "")
        
        except Exception as e:
            print(f"⚠️ Ollama generate 失败: {e}", file=sys.stderr)
        
        return ""


class LocalGGUFLLM(LLM):
    """本地 GGUF LLM"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model = None
        self._load_model()
    
    def _load_model(self):
        try:
            from llama_cpp import Llama
            
            if not self.model_path.exists():
                raise FileNotFoundError(f"模型不存在: {self.model_path}")
            
            self.model = Llama(
                str(self.model_path),
                n_ctx=4096,
                verbose=False
            )
            
            print(f"✅ GGUF LLM 模型已加载: {self.model_path.name}", file=sys.stderr)
        
        except ImportError:
            print("⚠️ llama-cpp-python 未安装", file=sys.stderr)
        except Exception as e:
            print(f"⚠️ 加载 GGUF 模型失败: {e}", file=sys.stderr)
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop: List[str] = None
    ) -> str:
        if not self.model:
            return ""
        
        try:
            response = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop or []
            )
            return response['choices'][0]['text']
        except:
            return ""


def get_llm(model: str = "auto") -> LLM:
    """
    获取 LLM
    
    Args:
        model: 模型名称或路径
            - "auto": 自动选择
            - "ollama:model": 使用 Ollama
            - "/path/to/model.gguf": 使用本地 GGUF
    
    Returns:
        LLM 实例
    """
    if model.startswith("ollama:"):
        model_name = model.split(":", 1)[1]
        return OllamaLLM(model_name)
    
    if model.endswith(".gguf") or Path(model).exists():
        return LocalGGUFLLM(model)
    
    # Auto
    ollama = OllamaLLM()
    if ollama.available:
        return ollama
    
    # 回退
    print("⚠️ 无可用 LLM", file=sys.stderr)
    return OllamaLLM()


# =============================================================================
# Embedding 格式化（多模型支持）
# =============================================================================

def format_for_embedding(
    text: str,
    model: str = "",
    is_query: bool = False,
    title: Optional[str] = None
) -> str:
    """
    根据模型类型格式化文本
    
    Qwen3-Embedding: 特殊格式
    Nomic: task/query 格式
    默认: 原始文本
    """
    model_lower = model.lower()
    
    # Qwen3-Embedding 格式
    if 'qwen' in model_lower and 'embed' in model_lower:
        if is_query:
            return f"Instruct: Retrieve relevant documents for the given query\nQuery: {text}"
        return f"{title}\n{text}" if title else text
    
    # Nomic 格式
    if 'nomic' in model_lower:
        if is_query:
            return f"task: search result | query: {text}"
        return f"title: {title or 'none'} | text: {text}"
    
    # 默认：原始文本
    return text


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Local LLM Support")
    parser.add_argument("action", choices=["embed", "rerank", "generate", "list"])
    parser.add_argument("--model", "-m", default="auto")
    parser.add_argument("--text", "-t")
    parser.add_argument("--query", "-q")
    parser.add_argument("--docs", "-d", nargs="+")
    
    args = parser.parse_args()
    
    if args.action == "embed":
        if not args.text:
            print("❌ 请指定 --text", file=sys.stderr)
            return
        
        embedder = get_embedder(args.model)
        embedding = embedder.embed(args.text)
        
        if embedding:
            print(f"✅ Embedding 维度: {len(embedding)}")
            print(f"   前 10 维: {embedding[:10]}")
        else:
            print("❌ Embedding 失败", file=sys.stderr)
    
    elif args.action == "rerank":
        if not args.query or not args.docs:
            print("❌ 请指定 --query 和 --docs", file=sys.stderr)
            return
        
        reranker = get_reranker(args.model)
        results = reranker.rerank(args.query, args.docs)
        
        print(f"✅ Rerank 结果:")
        for r in results:
            print(f"   [{r['score']:.3f}] {r['document'][:50]}...")
    
    elif args.action == "generate":
        if not args.text:
            print("❌ 请指定 --text", file=sys.stderr)
            return
        
        llm = get_llm(args.model)
        response = llm.generate(args.text)
        print(response)
    
    elif args.action == "list":
        print("📦 可用模型:")
        print("  Embedding:")
        print("    - nomic-embed-text:latest (Ollama)")
        print("    - *.gguf (本地 GGUF)")
        print("  LLM:")
        print("    - qwen2.5:7b (Ollama)")
        print("    - *.gguf (本地 GGUF)")


if __name__ == "__main__":
    main()
