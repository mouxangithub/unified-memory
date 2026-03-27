#!/usr/bin/env python3
"""
Error Handler - 错误处理与降级机制

三层降级策略:
1. Ollama 可用 → 向量搜索
2. Ollama 不可用 → BM25 搜索
3. BM25 失败 → 缓存结果
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from functools import wraps


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self.cache_dir = Path.home() / ".openclaw" / "workspace" / "memory" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.error_log = []
    
    def log_error(self, error_type: str, error_msg: str, fallback: str):
        """记录错误"""
        self.error_log.append({
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": error_type,
            "error": error_msg,
            "fallback": fallback
        })
    
    def get_embedding_with_fallback(self, text: str) -> Optional[List[float]]:
        """获取 embedding，支持降级"""
        try:
            # 尝试 Ollama
            from unified_memory import get_ollama_embedding
            embedding = get_ollama_embedding(text)
            if embedding:
                return embedding
        except Exception as e:
            self.log_error("embedding", str(e), "skip_embedding")
        
        # 降级：不使用 embedding
        return None
    
    def search_with_fallback(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索，支持降级"""
        
        # Level 1: 尝试向量搜索
        try:
            from memory_hyde import hyde_search
            results = hyde_search(query, limit)
            if results:
                return results
        except Exception as e:
            self.log_error("vector_search", str(e), "bm25_fallback")
        
        # Level 2: 降级到 BM25
        try:
            from memory_hyde import lex_search
            results = lex_search(query, limit)
            if results:
                return results
        except Exception as e:
            self.log_error("bm25_search", str(e), "cache_fallback")
        
        # Level 3: 从缓存读取
        return self._search_cache(query, limit)
    
    def _search_cache(self, query: str, limit: int) -> List[Dict]:
        """从缓存搜索"""
        cache_files = list(self.cache_dir.glob("*.json"))
        results = []
        
        for cache_file in cache_files[:limit * 2]:
            try:
                data = json.loads(cache_file.read_text())
                if query.lower() in data.get("text", "").lower():
                    results.append(data)
                    if len(results) >= limit:
                        break
            except:
                continue
        
        self.log_error("cache_search", "using_cache", f"found_{len(results)}")
        return results
    
    def llm_generate_with_fallback(self, prompt: str, provider: str = "ollama") -> str:
        """LLM 生成，支持降级"""
        
        # Level 1: 尝试指定提供商
        try:
            from llm_provider import LLMProviderFactory
            factory = LLMProviderFactory()
            llm = factory.create(provider)
            response = llm.generate(prompt)
            if response and hasattr(response, 'content'):
                return response.content
            return str(response)
        except Exception as e:
            self.log_error("llm_generate", str(e), "template_fallback")
        
        # Level 2: 降级到模板
        return self._template_fallback(prompt)
    
    def _template_fallback(self, prompt: str) -> str:
        """模板降级"""
        # 简单的模板响应
        if "总结" in prompt:
            return "（LLM 不可用，无法生成总结）"
        elif "问题" in prompt:
            return "（LLM 不可用，无法回答问题）"
        else:
            return "（LLM 不可用，请稍后重试）"
    
    def save_to_cache(self, text: str, metadata: Dict = None):
        """保存到缓存"""
        import hashlib
        
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_file = self.cache_dir / f"{text_hash}.json"
        
        data = {
            "text": text,
            "metadata": metadata or {},
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    
    def get_error_report(self) -> List[Dict]:
        """获取错误报告"""
        return self.error_log[-100:]  # 最近 100 条


def with_retry(max_retries: int = 3, delay: float = 1.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if i < max_retries - 1:
                        time.sleep(delay * (i + 1))  # 指数退避
            raise last_error
        return wrapper
    return decorator


def with_fallback(fallback_func):
    """降级装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if result:
                    return result
                return fallback_func(*args, **kwargs)
            except Exception as e:
                print(f"⚠️ {func.__name__} 失败: {e}, 使用降级方案")
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator


# 全局错误处理器
error_handler = ErrorHandler()


# 便捷函数
def safe_embedding(text: str) -> Optional[List[float]]:
    """安全的 embedding 获取"""
    return error_handler.get_embedding_with_fallback(text)


def safe_search(query: str, limit: int = 10) -> List[Dict]:
    """安全的搜索"""
    return error_handler.search_with_fallback(query, limit)


def safe_llm(prompt: str, provider: str = "ollama") -> str:
    """安全的 LLM 调用"""
    return error_handler.llm_generate_with_fallback(prompt, provider)
