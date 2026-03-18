#!/usr/bin/env python3
"""
Memory Search - 高级搜索 v0.0.7

功能:
- 分类搜索
- 时间范围搜索
- 模糊搜索
- 组合条件搜索

Usage:
    memory_search.py search --query "飞书" --category preference
    memory_search.py search --query "项目" --from 2026-03-01 --to 2026-03-18
    memory_search.py search --query "用户" --fuzzy --threshold 0.7
    memory_search.py search --query "重要" --min-importance 0.7
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher

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


class MemorySearch:
    """高级记忆搜索"""
    
    def __init__(self):
        self.memories = self._load_memories()
    
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
            except Exception as e:
                print(f"⚠️ 加载失败: {e}")
        
        return memories
    
    def search(
        self,
        query: str,
        category: Optional[str] = None,
        min_importance: Optional[float] = None,
        max_importance: Optional[float] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        fuzzy: bool = False,
        threshold: float = 0.7,
        use_vector: bool = True,
        limit: int = 10
    ) -> List[Dict]:
        """高级搜索"""
        results = []
        
        for mem in self.memories:
            # 基础文本匹配
            text = mem.get("text", "")
            query_lower = query.lower()
            text_lower = text.lower()
            
            if fuzzy:
                # 模糊匹配
                similarity = SequenceMatcher(None, query_lower, text_lower).ratio()
                if similarity < threshold:
                    continue
                mem["_similarity"] = similarity
            else:
                # 精确匹配
                if query_lower not in text_lower:
                    continue
            
            # 分类过滤
            if category and mem.get("category") != category:
                continue
            
            # 重要性过滤
            importance = mem.get("importance", 0.5)
            if min_importance is not None and importance < min_importance:
                continue
            if max_importance is not None and importance > max_importance:
                continue
            
            # 时间范围过滤
            created_at = mem.get("created_at") or mem.get("timestamp")
            if created_at:
                try:
                    if "T" in created_at:
                        mem_time = datetime.fromisoformat(created_at.replace("Z", "+00:00")).replace(tzinfo=None)
                    else:
                        mem_time = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                    
                    if from_date:
                        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
                        if mem_time < from_dt:
                            continue
                    
                    if to_date:
                        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
                        if mem_time > to_dt:
                            continue
                except:
                    pass
            
            results.append(mem)
        
        # 排序
        if fuzzy:
            results.sort(key=lambda x: x.get("_similarity", 0), reverse=True)
        else:
            results.sort(key=lambda x: x.get("importance", 0), reverse=True)
        
        return results[:limit]
    
    def vector_search(self, query: str, limit: int = 10) -> List[Dict]:
        """向量搜索"""
        if not HAS_LANCEDB or not HAS_REQUESTS:
            return []
        
        try:
            # 生成查询向量
            response = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={
                    "model": OLLAMA_EMBED_MODEL,
                    "prompt": query
                },
                timeout=10
            )
            
            if response.status_code != 200:
                return []
            
            query_embedding = response.json().get("embedding")
            
            # 向量搜索
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            
            results = table.search(query_embedding).limit(limit).to_list()
            return results
        
        except Exception as e:
            print(f"⚠️ 向量搜索失败: {e}", file=sys.stderr)
            return []
    
    def hybrid_search(self, query: str, limit: int = 10) -> List[Dict]:
        """混合搜索（关键词 + 向量）"""
        # 关键词搜索
        keyword_results = self.search(query, limit=limit)
        
        # 向量搜索
        vector_results = self.vector_search(query, limit=limit)
        
        # 合并去重
        seen_ids = set()
        combined = []
        
        for mem in keyword_results + vector_results:
            mem_id = mem.get("id")
            if mem_id not in seen_ids:
                seen_ids.add(mem_id)
                combined.append(mem)
        
        return combined[:limit]
    
    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[Dict]:
        """标签搜索"""
        results = []
        
        for mem in self.memories:
            mem_tags = mem.get("tags", [])
            if isinstance(mem_tags, str):
                mem_tags = json.loads(mem_tags)
            
            # 计算标签重叠
            overlap = len(set(tags) & set(mem_tags))
            if overlap > 0:
                mem["_tag_overlap"] = overlap
                results.append(mem)
        
        results.sort(key=lambda x: x.get("_tag_overlap", 0), reverse=True)
        return results[:limit]
    
    def search_by_entity(self, entity: str, limit: int = 10) -> List[Dict]:
        """实体搜索"""
        results = []
        
        for mem in self.memories:
            entities = mem.get("entities", [])
            if isinstance(entities, str):
                try:
                    entities = json.loads(entities)
                except:
                    entities = []
            
            if entity in entities:
                results.append(mem)
        
        return results[:limit]


def main():
    parser = argparse.ArgumentParser(description="Memory Search 0.0.7")
    parser.add_argument("command", choices=["search", "vector", "hybrid", "tags", "entity"])
    parser.add_argument("--query", "-q", required=True, help="搜索查询")
    parser.add_argument("--category", "-c", help="分类过滤")
    parser.add_argument("--min-importance", type=float, help="最小重要性")
    parser.add_argument("--max-importance", type=float, help="最大重要性")
    parser.add_argument("--from", dest="from_date", help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--fuzzy", action="store_true", help="模糊搜索")
    parser.add_argument("--threshold", type=float, default=0.7, help="模糊匹配阈值")
    parser.add_argument("--limit", "-l", type=int, default=10, help="结果数量限制")
    parser.add_argument("--tags", nargs="+", help="标签搜索")
    parser.add_argument("--entity", "-e", help="实体搜索")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="输出格式")
    
    args = parser.parse_args()
    
    search = MemorySearch()
    
    if args.command == "search":
        results = search.search(
            query=args.query,
            category=args.category,
            min_importance=args.min_importance,
            max_importance=args.max_importance,
            from_date=args.from_date,
            to_date=args.to_date,
            fuzzy=args.fuzzy,
            threshold=args.threshold,
            limit=args.limit
        )
    
    elif args.command == "vector":
        results = search.vector_search(args.query, args.limit)
    
    elif args.command == "hybrid":
        results = search.hybrid_search(args.query, args.limit)
    
    elif args.command == "tags":
        if not args.tags:
            print("❌ 请指定 --tags")
            sys.exit(1)
        results = search.search_by_tags(args.tags, args.limit)
    
    elif args.command == "entity":
        entity = args.entity or args.query
        results = search.search_by_entity(entity, args.limit)
    
    # 输出结果
    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"📋 找到 {len(results)} 条记忆:")
        for i, mem in enumerate(results, 1):
            importance = mem.get("importance", 0)
            category = mem.get("category", "other")
            text = mem.get("text", "")[:80]
            similarity = mem.get("_similarity", None)
            
            sim_str = f" (相似度: {similarity:.2f})" if similarity else ""
            print(f"{i}. [{category}] {text}... (重要性: {importance:.2f}){sim_str}")


if __name__ == "__main__":
    main()
