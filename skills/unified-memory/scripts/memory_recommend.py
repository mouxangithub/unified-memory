#!/usr/bin/env python3
"""
Memory Recommend - 智能关联推荐 v1.0

功能:
- 向量相似度推荐
- 共现关系推荐
- 标签关联推荐
- 综合推荐（融合多种策略）
- 主动推送相关记忆

Usage:
    python3 scripts/memory_recommend.py recommend --query "飞书"
    python3 scripts/memory_recommend.py hot --k 5
    python3 scripts/memory_recommend.py related --id MEM_ID
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple
import os

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
HISTORY_FILE = MEMORY_DIR / "access_history.json"
RECOMMEND_CACHE = MEMORY_DIR / "recommend_cache.json"

# Ollama 配置
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")


class AccessHistory:
    """访问历史记录"""
    
    def __init__(self):
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE) as f:
                return json.load(f)
        return {"accesses": [], "co_occurrences": {}}
    
    def save(self):
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def record_access(self, mem_id: str, context: str = ""):
        """记录访问"""
        self.history["accesses"].append({
            "id": mem_id,
            "timestamp": datetime.now().isoformat(),
            "context": context
        })
        
        # 保留最近 1000 条
        if len(self.history["accesses"]) > 1000:
            self.history["accesses"] = self.history["accesses"][-1000:]
        
        self.save()
    
    def record_co_occurrence(self, mem_ids: List[str]):
        """记录共现关系"""
        for i, id1 in enumerate(mem_ids):
            for id2 in mem_ids[i+1:]:
                key = f"{id1}|{id2}" if id1 < id2 else f"{id2}|{id1}"
                self.history["co_occurrences"][key] = self.history["co_occurrences"].get(key, 0) + 1
        self.save()
    
    def get_co_occurrences(self, mem_id: str) -> Dict[str, int]:
        """获取与指定记忆共现的其他记忆"""
        result = {}
        for key, count in self.history["co_occurrences"].items():
            ids = key.split("|")
            if mem_id in ids:
                other_id = ids[1] if ids[0] == mem_id else ids[0]
                result[other_id] = count
        return result


class MemoryRecommender:
    """记忆推荐引擎"""
    
    def __init__(self):
        self.memories = self._load_memories()
        self.history = AccessHistory()
        self.embeddings = {}
    
    def _load_memories(self) -> List[Dict]:
        """加载记忆"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            df = table.to_lance().to_table().to_pydict()
            
            memories = []
            for i in range(len(df.get("id", []))):
                memories.append({
                    "id": df["id"][i],
                    "text": df["text"][i],
                    "category": df.get("category", [""])[i] if i < len(df.get("category", [])) else "",
                    "importance": df.get("importance", [0.5])[i] if i < len(df.get("importance", [])) else 0.5,
                    "tags": df.get("tags", [[]])[i] if i < len(df.get("tags", [])) else [],
                    "timestamp": df.get("timestamp", [""])[i] if i < len(df.get("timestamp", [])) else "",
                    "vector": df.get("vector", [None])[i] if i < len(df.get("vector", [])) else None
                })
            return memories
        except Exception as e:
            print(f"⚠️ 加载记忆失败: {e}")
            return []
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本嵌入向量"""
        cache_key = text[:50]  # 简单缓存
        if cache_key in self.embeddings:
            return self.embeddings[cache_key]
        
        try:
            import requests
            response = requests.post(
                f"{OLLAMA_HOST}/api/embeddings",
                json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
                timeout=10
            )
            if response.ok:
                embedding = response.json().get("embedding", [])
                self.embeddings[cache_key] = embedding
                return embedding
        except Exception as e:
            print(f"⚠️ 获取嵌入失败: {e}")
        return None
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """计算余弦相似度"""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def recommend_by_vector(self, query: str, k: int = 5) -> List[Dict]:
        """基于向量相似度推荐"""
        query_vec = self._get_embedding(query)
        if not query_vec:
            return []
        
        scores = []
        for mem in self.memories:
            if mem.get("vector"):
                sim = self._cosine_similarity(query_vec, mem["vector"])
                scores.append((mem, sim))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [{"memory": m, "score": s, "type": "vector"} for m, s in scores[:k]]
    
    def recommend_by_co_occurrence(self, mem_id: str, k: int = 5) -> List[Dict]:
        """基于共现关系推荐"""
        co_occur = self.history.get_co_occurrences(mem_id)
        if not co_occur:
            return []
        
        # 排序并取 top-k
        sorted_co = sorted(co_occur.items(), key=lambda x: x[1], reverse=True)[:k]
        
        results = []
        for other_id, count in sorted_co:
            mem = next((m for m in self.memories if m["id"] == other_id), None)
            if mem:
                results.append({
                    "memory": mem,
                    "score": count / 10,  # 归一化
                    "type": "co_occurrence",
                    "co_count": count
                })
        
        return results
    
    def recommend_by_tags(self, tags: List[str], k: int = 5) -> List[Dict]:
        """基于标签关联推荐"""
        if not tags:
            return []
        
        scores = []
        for mem in self.memories:
            mem_tags = set(mem.get("tags", []))
            query_tags = set(tags)
            
            # Jaccard 相似度
            intersection = len(mem_tags & query_tags)
            union = len(mem_tags | query_tags)
            
            if union > 0 and intersection > 0:
                jaccard = intersection / union
                scores.append((mem, jaccard))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [{"memory": m, "score": s, "type": "tag"} for m, s in scores[:k]]
    
    def recommend_combined(self, query: str, context_ids: List[str] = None, k: int = 5) -> List[Dict]:
        """综合推荐（融合多种策略）"""
        results = {}
        
        # 1. 向量相似度
        vector_results = self.recommend_by_vector(query, k * 2)
        for r in vector_results:
            mem_id = r["memory"]["id"]
            if mem_id not in results:
                results[mem_id] = {"memory": r["memory"], "scores": {}}
            results[mem_id]["scores"]["vector"] = r["score"]
        
        # 2. 标签关联
        query_tags = self._extract_tags(query)
        tag_results = self.recommend_by_tags(query_tags, k * 2)
        for r in tag_results:
            mem_id = r["memory"]["id"]
            if mem_id not in results:
                results[mem_id] = {"memory": r["memory"], "scores": {}}
            results[mem_id]["scores"]["tag"] = r["score"]
        
        # 3. 共现关系（如果有上下文记忆）
        if context_ids:
            for ctx_id in context_ids[:3]:
                co_results = self.recommend_by_co_occurrence(ctx_id, k)
                for r in co_results:
                    mem_id = r["memory"]["id"]
                    if mem_id not in results:
                        results[mem_id] = {"memory": r["memory"], "scores": {}}
                    results[mem_id]["scores"]["co_occurrence"] = r["score"]
        
        # 4. 融合计算
        final_results = []
        for mem_id, data in results.items():
            # 加权融合
            scores = data["scores"]
            combined = (
                scores.get("vector", 0) * 0.5 +
                scores.get("tag", 0) * 0.3 +
                scores.get("co_occurrence", 0) * 0.2
            )
            
            # 加入重要性因子
            importance = data["memory"].get("importance", 0.5)
            combined = combined * 0.7 + importance * 0.3
            
            final_results.append({
                "memory": data["memory"],
                "score": combined,
                "type": "combined",
                "breakdown": scores
            })
        
        # 排序
        final_results.sort(key=lambda x: x["score"], reverse=True)
        
        # 记录共现
        if len(final_results) > 1:
            ids = [r["memory"]["id"] for r in final_results[:5]]
            self.history.record_co_occurrence(ids)
        
        return final_results[:k]
    
    def _extract_tags(self, text: str) -> List[str]:
        """提取标签"""
        # 预定义关键词
        keywords = {
            "飞书", "微信", "QQ", "龙宫", "项目", "电商",
            "偏好", "协作", "管理", "记忆系统", "EvoMap",
            "刘总", "会议", "任务", "决策"
        }
        
        found = []
        for kw in keywords:
            if kw in text:
                found.append(kw)
        
        return found
    
    def get_hot_memories(self, days: int = 7, k: int = 5) -> List[Dict]:
        """获取热点记忆"""
        cutoff = datetime.now() - timedelta(days=days)
        
        # 统计访问频率
        access_count = Counter()
        for acc in self.history.history.get("accesses", []):
            try:
                ts = datetime.fromisoformat(acc["timestamp"])
                if ts > cutoff:
                    access_count[acc["id"]] += 1
            except:
                pass
        
        # 获取 top-k
        hot_ids = [id for id, _ in access_count.most_common(k)]
        
        results = []
        for mem_id in hot_ids:
            mem = next((m for m in self.memories if m["id"] == mem_id), None)
            if mem:
                results.append({
                    "memory": mem,
                    "access_count": access_count[mem_id],
                    "type": "hot"
                })
        
        return results
    
    def get_recommendations_for_context(self, context: str, current_memories: List[str] = None, k: int = 3) -> Dict:
        """为上下文获取推荐（供 Agent 集成使用）"""
        recommendations = self.recommend_combined(context, current_memories, k)
        
        return {
            "query": context,
            "recommendations": [
                {
                    "id": r["memory"]["id"],
                    "text": r["memory"]["text"][:100] + "...",
                    "score": round(r["score"], 3),
                    "type": r["type"],
                    "reason": self._explain_recommendation(r)
                }
                for r in recommendations
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    def _explain_recommendation(self, result: Dict) -> str:
        """解释推荐原因"""
        scores = result.get("breakdown", {})
        reasons = []
        
        if scores.get("vector", 0) > 0.5:
            reasons.append("语义相似")
        if scores.get("tag", 0) > 0.3:
            reasons.append("标签关联")
        if scores.get("co_occurrence", 0) > 0.1:
            reasons.append("经常一起出现")
        
        if result["memory"].get("importance", 0) > 0.7:
            reasons.append("重要性高")
        
        return "、".join(reasons) if reasons else "综合推荐"


def main():
    parser = argparse.ArgumentParser(description="Memory Recommend v1.0")
    parser.add_argument("command", choices=["recommend", "hot", "related", "context"])
    parser.add_argument("--query", "-q", help="查询文本")
    parser.add_argument("--id", "-i", help="记忆 ID")
    parser.add_argument("--k", "-k", type=int, default=5, help="返回数量")
    parser.add_argument("--tags", "-t", nargs="+", help="标签列表")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    recommender = MemoryRecommender()
    
    if args.command == "recommend":
        if not args.query:
            print("❌ 请提供 --query")
            return
        
        print(f"🔍 智能推荐: {args.query}")
        results = recommender.recommend_combined(args.query, k=args.k)
        
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"\n找到 {len(results)} 条推荐:")
            for i, r in enumerate(results, 1):
                mem = r["memory"]
                print(f"\n{i}. [{r['type']}] {mem['text'][:80]}...")
                print(f"   评分: {r['score']:.3f}")
                if "breakdown" in r:
                    print(f"   分解: {r['breakdown']}")
    
    elif args.command == "hot":
        print(f"🔥 热点记忆 (最近 7 天)")
        results = recommender.get_hot_memories(k=args.k)
        
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for i, r in enumerate(results, 1):
                mem = r["memory"]
                print(f"{i}. [访问 {r['access_count']} 次] {mem['text'][:60]}...")
    
    elif args.command == "related":
        if not args.id:
            print("❌ 请提供 --id")
            return
        
        print(f"🔗 相关记忆: {args.id[:8]}...")
        results = recommender.recommend_by_co_occurrence(args.id, k=args.k)
        
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for i, r in enumerate(results, 1):
                mem = r["memory"]
                print(f"{i}. [共现 {r.get('co_count', 0)} 次] {mem['text'][:60]}...")
    
    elif args.command == "context":
        if not args.query:
            print("❌ 请提供 --query")
            return
        
        result = recommender.get_recommendations_for_context(args.query, k=args.k)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
