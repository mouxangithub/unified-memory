#!/usr/bin/env python3
"""
Smart Search - 智能检索模块 v1.0

功能:
- 上下文感知检索
- 关联推荐
- 智能排序
- 实时提示

排序算法:
综合评分 = 相关性 × 0.4 + 重要性 × 0.3 + 新鲜度 × 0.2 + 使用频率 × 0.1
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter

# 添加脚本目录
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from memory import MemorySystemV7
    HAS_MEMORY = True
except ImportError:
    HAS_MEMORY = False

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
CACHE_DIR = MEMORY_DIR / "cache"

# 缓存文件
CONTEXT_CACHE = CACHE_DIR / "search_context.json"
RECOMMENDATIONS_CACHE = CACHE_DIR / "recommendations.json"

# 权重
WEIGHT_RELEVANCE = 0.4
WEIGHT_IMPORTANCE = 0.3
WEIGHT_FRESHNESS = 0.2
WEIGHT_FREQUENCY = 0.1

# 确保目录存在
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class SmartSearch:
    """智能检索模块"""
    
    def __init__(self):
        self.memory = MemorySystemV7() if HAS_MEMORY else None
        self.context: Dict[str, Any] = {}
        self.recommendations: List[Dict] = []
        self.search_history: List[str] = []
        self._load()
    
    def _load(self):
        """加载缓存"""
        try:
            if CONTEXT_CACHE.exists():
                self.context = json.loads(CONTEXT_CACHE.read_text())
            if RECOMMENDATIONS_CACHE.exists():
                self.recommendations = json.loads(RECOMMENDATIONS_CACHE.read_text())
        except Exception as e:
            print(f"⚠️ 加载搜索缓存失败: {e}", file=sys.stderr)
    
    def _save(self):
        """保存缓存"""
        try:
            CONTEXT_CACHE.write_text(json.dumps(self.context, ensure_ascii=False, indent=2))
            RECOMMENDATIONS_CACHE.write_text(json.dumps(self.recommendations, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"⚠️ 保存搜索缓存失败: {e}", file=sys.stderr)
    
    def search(self, query: str, top_k: int = 10, context: str = None) -> List[Dict]:
        """智能搜索"""
        if not self.memory:
            return []
        
        # 获取所有记忆
        all_memories = self.memory.memories if self.memory else []
        
        # 计算综合评分
        scored_memories = []
        for mem in all_memories:
            score = self._calculate_score(mem, query, context)
            if score > 0:
                scored_memories.append({
                    "memory": mem,
                    "score": score,
                    "components": {
                        "relevance": self._relevance_score(mem, query),
                        "importance": self._importance_score(mem),
                        "freshness": self._freshness_score(mem),
                        "frequency": self._frequency_score(mem)
                    }
                })
        
        # 排序
        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        
        # 记录搜索历史
        self.search_history.append(query)
        self._save()
        
        return scored_memories[:top_k]
    
    def _calculate_score(self, memory: Dict, query: str, context: str = None) -> float:
        """计算综合评分"""
        relevance = self._relevance_score(memory, query)
        importance = self._importance_score(memory)
        freshness = self._freshness_score(memory)
        frequency = self._frequency_score(memory)
        
        # 基础评分
        score = (
            relevance * WEIGHT_RELEVANCE +
            importance * WEIGHT_IMPORTANCE +
            freshness * WEIGHT_FRESHNESS +
            frequency * WEIGHT_FREQUENCY
        )
        
        # 上下文加成
        if context:
            context_bonus = self._context_bonus(memory, context)
            score += context_bonus * 0.2
        
        return score
    
    def _relevance_score(self, memory: Dict, query: str) -> float:
        """相关性评分"""
        text = memory.get("text", "").lower()
        query_lower = query.lower()
        
        # 完全匹配
        if query_lower in text:
            return 1.0
        
        # 部分匹配
        query_words = set(query_lower.split())
        text_words = set(text.split())
        
        if not query_words:
            return 0.0
        
        matches = query_words & text_words
        return len(matches) / len(query_words)
    
    def _importance_score(self, memory: Dict) -> float:
        """重要性评分"""
        importance = memory.get("importance", 0.5)
        return min(max(importance, 0), 1)
    
    def _freshness_score(self, memory: Dict) -> float:
        """新鲜度评分"""
        timestamp = memory.get("timestamp") or memory.get("created_at")
        if not timestamp:
            return 0.5
        
        try:
            if "T" in timestamp:
                mem_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
            else:
                mem_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            
            age_days = (datetime.now() - mem_time).days
            
            # 新鲜度衰减：30天内为高分，超过90天为低分
            if age_days < 7:
                return 1.0
            elif age_days < 30:
                return 0.8
            elif age_days < 90:
                return 0.5
            else:
                return 0.2
        except:
            return 0.5
    
    def _frequency_score(self, memory: Dict) -> float:
        """使用频率评分"""
        # 基于访问次数
        access_count = memory.get("access_count", 0)
        
        if access_count == 0:
            return 0.3
        elif access_count < 5:
            return 0.5
        elif access_count < 10:
            return 0.7
        else:
            return 1.0
    
    def _context_bonus(self, memory: Dict, context: str) -> float:
        """上下文加成"""
        if not context:
            return 0.0
        
        memory_text = memory.get("text", "").lower()
        context_lower = context.lower()
        
        # 检查上下文中的关键词是否出现在记忆中
        context_words = set(context_lower.split())
        memory_words = set(memory_text.split())
        
        if not context_words:
            return 0.0
        
        overlap = context_words & memory_words
        return len(overlap) / len(context_words) * 0.5
    
    def recommend(self, current_context: str = None, top_k: int = 5) -> List[Dict]:
        """推荐相关记忆"""
        if not self.memory:
            return []
        
        # 获取所有记忆
        all_memories = self.memory.memories if self.memory else []
        
        # 基于上下文推荐
        recommendations = []
        for mem in all_memories:
            relevance = self._relevance_score(mem, current_context or "")
            importance = self._importance_score(mem)
            
            # 推荐评分 = 相关性 × 0.6 + 重要性 × 0.4
            score = relevance * 0.6 + importance * 0.4
            
            if score > 0.3:  # 只推荐评分 > 0.3 的记忆
                recommendations.append({
                    "memory": mem,
                    "score": score,
                    "reason": "与当前上下文相关" if relevance > 0.5 else "重要性较高"
                })
        
        # 排序
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        # 更新缓存
        self.recommendations = recommendations[:top_k]
        self._save()
        
        return self.recommendations
    
    def get_trending_keywords(self, top_k: int = 10) -> List[Dict]:
        """获取热门关键词"""
        if not self.search_history:
            return []
        
        # 统计关键词频率
        all_words = []
        for query in self.search_history:
            all_words.extend(query.lower().split())
        
        word_counts = Counter(all_words)
        trending = word_counts.most_common(top_k)
        
        return [{"keyword": word, "count": count} for word, count in trending]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_searches": len(self.search_history),
            "total_recommendations": len(self.recommendations),
            "recent_searches": self.search_history[-10:],
            "trending_keywords": self.get_trending_keywords(5)
        }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="智能检索模块")
    parser.add_argument("command", choices=["search", "recommend", "trending", "stats"])
    parser.add_argument("--query", "-q", help="搜索查询")
    parser.add_argument("--context", "-c", help="上下文")
    parser.add_argument("--top-k", "-k", type=int, default=5, help="返回结果数量")
    
    args = parser.parse_args()
    
    searcher = SmartSearch()
    
    if args.command == "search":
        if not args.query:
            print("❌ 请提供搜索查询 --query")
            return
        
        results = searcher.search(args.query, args.top_k, args.context)
        
        print(f"\n🔍 搜索结果 (查询: {args.query}):")
        for i, result in enumerate(results, 1):
            mem = result["memory"]
            print(f"\n#{i} [{result['score']:.2f}]")
            print(f"  文本: {mem.get('text', '')[:80]}...")
            print(f"  评分详情: {result['components']}")
    
    elif args.command == "recommend":
        results = searcher.recommend(args.context, args.top_k)
        
        print(f"\n💡 推荐记忆:")
        for i, rec in enumerate(results, 1):
            mem = rec["memory"]
            print(f"\n#{i} [{rec['score']:.2f}] {rec['reason']}")
            print(f"  文本: {mem.get('text', '')[:80]}...")
    
    elif args.command == "trending":
        trending = searcher.get_trending_keywords(args.top_k)
        
        print(f"\n🔥 热门关键词:")
        for i, kw in enumerate(trending, 1):
            print(f"  #{i} {kw['keyword']} ({kw['count']} 次)")
    
    elif args.command == "stats":
        stats = searcher.get_stats()
        print(f"\n📊 检索统计:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
