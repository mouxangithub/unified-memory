#!/usr/bin/env python3
"""
Memory Agent Interface - Agent 专用接口 v0.1.6

功能:
- 快速上下文加载
- 预测性加载
- 增量更新
- 批量操作

Usage:
    python3 scripts/memory_agent.py load "当前任务"
    python3 scripts/memory_agent.py context
    python3 scripts/memory_agent.py update
    python3 scripts/memory_agent.py quick-store "记住这个"
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
CACHE_FILE = MEMORY_DIR / "cache" / "agent_context.json"

try:
    import lancedb
    import requests
    HAS_LANCEDB = True
except ImportError:
    HAS_LANCEDB = False

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")


def get_embedding(text: str) -> Optional[List[float]]:
    """获取向量"""
    if not HAS_LANCEDB:
        return None
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("embedding")
    except:
        pass
    return None


def load_context(query: str = "", top_k: int = 10) -> Dict:
    """快速加载上下文"""
    result = {
        "memories": [],
        "stats": {},
        "suggestions": [],
        "load_time_ms": 0
    }
    
    start = datetime.now()
    
    if not HAS_LANCEDB:
        return result
    
    try:
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        data = table.to_lance().to_table().to_pydict()
        
        total = len(data.get("id", []))
        memories = []
        
        for i in range(total):
            memories.append({
                "id": data["id"][i] if i < len(data.get("id", [])) else "",
                "text": data["text"][i] if i < len(data.get("text", [])) else "",
                "category": data["category"][i] if i < len(data.get("category", [])) else "",
                "importance": float(data["importance"][i]) if i < len(data.get("importance", [])) else 0.5
            })
        
        # 如果有查询，进行相关性排序
        if query:
            query_lower = query.lower()
            # 简单文本匹配
            scored = []
            for m in memories:
                score = 0
                text_lower = m["text"].lower()
                if query_lower in text_lower:
                    score = text_lower.count(query_lower) * 10 + m["importance"] * 5
                else:
                    # 词级别匹配
                    for word in query_lower.split():
                        if word in text_lower:
                            score += 2
                if score > 0:
                    m["_score"] = score
                    scored.append(m)
            
            scored.sort(key=lambda x: x.get("_score", 0), reverse=True)
            memories = scored[:top_k]
        else:
            # 按 importance 排序
            memories.sort(key=lambda x: x.get("importance", 0), reverse=True)
            memories = memories[:top_k]
        
        result["memories"] = memories
        result["stats"] = {
            "total": total,
            "loaded": len(memories)
        }
        
        # 生成建议
        categories = {}
        for m in memories:
            cat = m.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        if categories:
            top_cat = max(categories, key=categories.get)
            result["suggestions"].append(f"主要关注: {top_cat} ({categories[top_cat]}条)")
        
    except Exception as e:
        result["error"] = str(e)
    
    result["load_time_ms"] = (datetime.now() - start).total_seconds() * 1000
    
    return result


def predict_load(current_context: str = "") -> List[str]:
    """预测性加载 - 预测下一步可能需要的记忆"""
    predictions = []
    
    # 基于当前上下文预测
    keywords = {
        "项目": ["进度", "状态", "负责人", "时间"],
        "会议": ["时间", "地点", "参与者", "议题"],
        "任务": ["截止", "优先级", "状态", "负责人"],
        "用户": ["偏好", "习惯", "联系方式", "历史"],
    }
    
    if current_context:
        for key, related in keywords.items():
            if key in current_context:
                predictions.extend(related)
    
    return list(set(predictions))


def quick_store(text: str, category: str = "general") -> bool:
    """快速存储"""
    if not HAS_LANCEDB:
        print("❌ LanceDB 未安装")
        return False
    
    try:
        import uuid
        
        # 获取向量
        embedding = get_embedding(text)
        
        # 连接数据库
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        
        # 存储
        table.add([{
            "id": str(uuid.uuid4()),
            "text": text,
            "category": category,
            "importance": 0.6,
            "timestamp": datetime.now().isoformat(),
            "vector": embedding or []
        }])
        
        return True
    except Exception as e:
        print(f"❌ 存储失败: {e}")
        return False


def batch_update(updates: List[Dict]) -> Dict:
    """批量更新"""
    results = {"success": 0, "failed": 0}
    
    for update in updates:
        text = update.get("text", "")
        category = update.get("category", "general")
        
        if quick_store(text, category):
            results["success"] += 1
        else:
            results["failed"] += 1
    
    return results


def get_memory_by_id(memory_id: str) -> Optional[Dict]:
    """获取单条记忆"""
    if not HAS_LANCEDB:
        return None
    
    try:
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        data = table.to_lance().to_table().to_pydict()
        
        total = len(data.get("id", []))
        for i in range(total):
            if data["id"][i] == memory_id:
                return {
                    "id": data["id"][i],
                    "text": data["text"][i],
                    "category": data["category"][i],
                    "importance": float(data["importance"][i]) if i < len(data.get("importance", [])) else 0.5,
                    "timestamp": data["timestamp"][i] if i < len(data.get("timestamp", [])) else ""
                }
    except:
        pass
    
    return None


def main():
    parser = argparse.ArgumentParser(description="Memory Agent Interface 0.1.6")
    parser.add_argument("command", choices=["load", "context", "update", "quick-store", "get", "predict"])
    parser.add_argument("query", nargs="?", help="查询或内容")
    parser.add_argument("--top-k", "-k", type=int, default=10)
    parser.add_argument("--category", "-c", default="general")
    parser.add_argument("--id", help="记忆 ID")
    
    args = parser.parse_args()
    
    if args.command == "load":
        result = load_context(args.query or "", args.top_k)
        print(f"⚡ 加载完成 ({result['load_time_ms']:.1f}ms)")
        print(f"   记忆: {result['stats'].get('loaded', 0)}/{result['stats'].get('total', 0)}")
        
        if result['suggestions']:
            print(f"\n💡 建议:")
            for s in result['suggestions']:
                print(f"   {s}")
        
        if result['memories']:
            print(f"\n📚 记忆:")
            for m in result['memories'][:5]:
                print(f"   [{m['category']}] {m['text'][:40]}...")
    
    elif args.command == "context":
        # 加载缓存上下文
        if CACHE_FILE.exists():
            with open(CACHE_FILE) as f:
                cached = json.load(f)
            print(f"📦 缓存上下文 ({len(cached)} 条)")
        else:
            print("📦 无缓存上下文，使用 load 命令加载")
    
    elif args.command == "quick-store":
        if not args.query:
            print("请提供内容")
            return
        if quick_store(args.query, args.category):
            print(f"✅ 已存储: {args.query[:40]}...")
        else:
            print("❌ 存储失败")
    
    elif args.command == "get":
        memory_id = args.id or args.query
        if not memory_id:
            print("请提供记忆 ID")
            return
        m = get_memory_by_id(memory_id)
        if m:
            print(json.dumps(m, ensure_ascii=False, indent=2))
        else:
            print("❌ 未找到")
    
    elif args.command == "predict":
        predictions = predict_load(args.query or "")
        if predictions:
            print("🔮 预测相关:")
            for p in predictions:
                print(f"   - {p}")
        else:
            print("暂无预测")


if __name__ == "__main__":
    main()
