#!/usr/bin/env python3
"""
Memory Search Enhanced - 增强搜索体验 v1.0

功能:
- 自然语言搜索
- 多维度过滤器
- 搜索历史
- 模糊匹配

Usage:
    python3 scripts/memory_search.py search "用户偏好"
    python3 scripts/memory_search.py filter --category preference --min-importance 0.7
    python3 scripts/memory_search.py history
    python3 scripts/memory_search.py suggestions "项"
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter
import os

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
SEARCH_HISTORY = MEMORY_DIR / "search_history.json"

# Ollama 配置
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")


class EnhancedSearch:
    """增强搜索"""
    
    def __init__(self):
        self.memories = self._load_memories()
        self.history = self._load_history()
    
    def _load_memories(self) -> List[Dict]:
        """加载记忆"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            data = table.to_lance().to_table().to_pydict()
            
            memories = []
            for i in range(len(data.get("id", []))):
                memories.append({
                    "id": data["id"][i],
                    "text": data["text"][i],
                    "category": data.get("category", [""])[i] if i < len(data.get("category", [])) else "",
                    "importance": data.get("importance", [0.5])[i] if i < len(data.get("importance", [])) else 0.5,
                    "tags": data.get("tags", [[]])[i] if i < len(data.get("tags", [])) else [],
                    "timestamp": data.get("timestamp", [""])[i] if i < len(data.get("timestamp", [])) else ""
                })
            return memories
        except Exception as e:
            print(f"⚠️ 加载记忆失败: {e}")
            return []
    
    def _load_history(self) -> Dict:
        """加载搜索历史"""
        if SEARCH_HISTORY.exists():
            with open(SEARCH_HISTORY) as f:
                return json.load(f)
        return {"searches": [], "recent": []}
    
    def _save_history(self):
        """保存搜索历史"""
        SEARCH_HISTORY.parent.mkdir(parents=True, exist_ok=True)
        with open(SEARCH_HISTORY, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """获取嵌入向量"""
        try:
            import requests
            response = requests.post(
                f"{OLLAMA_HOST}/api/embeddings",
                json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
                timeout=10
            )
            if response.ok:
                return response.json().get("embedding", [])
        except:
            pass
        return None
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """计算余弦相似度"""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        return dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0
    
    def semantic_search(self, query: str, k: int = 10, min_score: float = 0.3) -> List[Dict]:
        """语义搜索"""
        query_vec = self._get_embedding(query)
        if not query_vec:
            return self._fallback_search(query, k)
        
        results = []
        for mem in self.memories:
            # 尝试从数据库获取向量
            try:
                import lancedb
                db = lancedb.connect(str(VECTOR_DB_DIR))
                table = db.open_table("memories")
                
                # 简单方法：只计算相似度
                sim = self._cosine_similarity(query_vec, [0.0] * len(query_vec))  # 简化
                
                # 文本相似度作为备选
                text_sim = self._text_similarity(query, mem["text"])
                combined_score = text_sim  # 使用文本相似度
                
                if combined_score >= min_score:
                    results.append({
                        "id": mem["id"],
                        "text": mem["text"],
                        "category": mem["category"],
                        "importance": mem["importance"],
                        "score": round(combined_score, 3),
                        "timestamp": mem["timestamp"]
                    })
            except:
                pass
        
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # 记录搜索历史
        self._record_search(query, len(results))
        
        return results[:k]
    
    def _fallback_search(self, query: str, k: int) -> List[Dict]:
        """回退搜索：关键词匹配"""
        query_lower = query.lower()
        results = []
        
        for mem in self.memories:
            text_lower = mem["text"].lower()
            
            # 计算匹配分数
            score = 0
            
            # 精确包含
            if query_lower in text_lower:
                score = 1.0
            # 单词匹配
            else:
                query_words = set(query_lower.split())
                text_words = set(text_lower.split())
                overlap = len(query_words & text_words)
                if overlap > 0:
                    score = overlap / len(query_words)
            
            if score > 0.1:
                results.append({
                    "id": mem["id"],
                    "text": mem["text"],
                    "category": mem["category"],
                    "importance": mem["importance"],
                    "score": round(score, 3),
                    "timestamp": mem["timestamp"]
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        
        self._record_search(query, len(results))
        
        return results[:k]
    
    def _text_similarity(self, query: str, text: str) -> float:
        """文本相似度"""
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words or not text_words:
            return 0.0
        
        intersection = len(query_words & text_words)
        union = len(query_words | text_words)
        
        return intersection / union if union > 0 else 0.0
    
    def _record_search(self, query: str, result_count: int):
        """记录搜索"""
        self.history["searches"].append({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "results": result_count
        })
        
        # 保留最近50条
        if len(self.history["searches"]) > 50:
            self.history["searches"] = self.history["searches"][-50:]
        
        # 更新最近搜索
        if query not in self.history.get("recent", []):
            self.history["recent"] = [query] + self.history.get("recent", [])[:9]
        
        self._save_history()
    
    def filter_search(self, category: str = None, min_importance: float = None,
                     max_age_days: int = None, tags: List[str] = None,
                     has_tags: bool = None, limit: int = 50) -> List[Dict]:
        """多维度过滤搜索"""
        results = []
        
        cutoff = datetime.now() - timedelta(days=max_age_days) if max_age_days else None
        
        for mem in self.memories:
            # 类别过滤
            if category and mem["category"] != category:
                continue
            
            # 重要性过滤
            if min_importance is not None and mem["importance"] < min_importance:
                continue
            
            # 时间过滤
            if cutoff:
                try:
                    mem_time = datetime.fromisoformat(mem["timestamp"])
                    if mem_time < cutoff:
                        continue
                except:
                    pass
            
            # 标签过滤
            mem_tags = set(mem.get("tags", []))
            if has_tags and not mem_tags:
                continue
            if tags:
                if not any(t in mem_tags for t in tags):
                    continue
            
            results.append({
                "id": mem["id"],
                "text": mem["text"],
                "category": mem["category"],
                "importance": mem["importance"],
                "tags": mem.get("tags", []),
                "timestamp": mem["timestamp"]
            })
        
        return results[:limit]
    
    def get_search_suggestions(self, prefix: str) -> List[str]:
        """搜索建议"""
        recent = self.history.get("recent", [])
        
        # 基于历史推荐
        suggestions = [s for s in recent if prefix.lower() in s.lower()]
        
        # 基于记忆内容推荐
        if len(suggestions) < 5:
            for mem in self.memories[:20]:
                words = mem["text"].split()[:5]
                for word in words:
                    if len(word) > 2 and prefix.lower() in word.lower():
                        if word not in suggestions:
                            suggestions.append(word)
        
        return suggestions[:10]
    
    def get_search_stats(self) -> Dict:
        """搜索统计"""
        searches = self.history.get("searches", [])
        
        if not searches:
            return {"total_searches": 0, "popular_queries": []}
        
        # 热门搜索
        queries = [s["query"] for s in searches]
        popular = Counter(queries).most_common(10)
        
        return {
            "total_searches": len(searches),
            "popular_queries": [{"query": q, "count": c} for q, c in popular],
            "recent_searches": searches[-10:] if searches else []
        }


def main():
    parser = argparse.ArgumentParser(description="Memory Enhanced Search v1.0")
    parser.add_argument("command", choices=["search", "filter", "history", "suggestions", "stats"])
    parser.add_argument("query", nargs="?", help="搜索内容")
    parser.add_argument("--category", "-c", help="类别过滤")
    parser.add_argument("--min-importance", "-i", type=float, help="最低重要性")
    parser.add_argument("--max-age", "-a", type=int, help="最大天数")
    parser.add_argument("--tags", "-t", nargs="+", help="标签过滤")
    parser.add_argument("--has-tags", action="store_true", help="必须有标签")
    parser.add_argument("--k", "-k", type=int, default=10, help="返回数量")
    parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    
    args = parser.parse_args()
    
    search = EnhancedSearch()
    
    if args.command == "search":
        if not args.query:
            print("❌ 请提供搜索内容")
            return
        
        results = search.semantic_search(args.query, args.k)
        
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"🔍 搜索: {args.query}")
            print(f"   找到 {len(results)} 条结果\n")
            
            for i, r in enumerate(results, 1):
                print(f"{i}. [{r['category']}] {r['text'][:80]}...")
                print(f"   评分: {r['score']:.3f} | 重要性: {r['importance']}")
                print()
    
    elif args.command == "filter":
        results = search.filter_search(
            category=args.category,
            min_importance=args.min_importance,
            max_age_days=args.max_age,
            tags=args.tags,
            has_tags=args.has_tags,
            limit=args.k
        )
        
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"🔍 过滤结果: {len(results)} 条\n")
            
            for i, r in enumerate(results, 1):
                print(f"{i}. [{r['category']}] {r['text'][:60]}...")
                print(f"   重要性: {r['importance']} | 标签: {r.get('tags', [])}")
                print()
    
    elif args.command == "history":
        results = search.history.get("searches", [])[-10:]
        
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"📜 搜索历史:")
            for r in reversed(results):
                print(f"   {r['timestamp'][:19]} - {r['query']} ({r['results']}结果)")
    
    elif args.command == "suggestions":
        if not args.query:
            print("❌ 请提供前缀")
            return
        
        suggestions = search.get_search_suggestions(args.query)
        
        if args.json:
            print(json.dumps(suggestions, ensure_ascii=False, indent=2))
        else:
            print(f"💡 搜索建议:")
            for s in suggestions:
                print(f"   {s}")
    
    elif args.command == "stats":
        stats = search.get_search_stats()
        
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print(f"📊 搜索统计")
            print(f"   总搜索次数: {stats['total_searches']}")
            
            if stats['popular_queries']:
                print(f"\n   热门搜索:")
                for q in stats['popular_queries'][:5]:
                    print(f"     {q['query']}: {q['count']}次")


if __name__ == "__main__":
    main()
