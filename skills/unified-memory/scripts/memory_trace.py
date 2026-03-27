#!/usr/bin/env python3
"""
Memory Trace - 决策追溯链 v1.0

功能:
- 追溯记忆的来源和决策背景
- 显示决策链条（A → B → C）
- 支持时间线视图

Usage:
    mem trace <记忆ID>
    mem trace --timeline  # 显示决策时间线
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

MEMORY_DIR = Path.home() / ".openclaw/workspace/memory"
MEMORIES_FILE = MEMORY_DIR / "memories.json"
DECISIONS_DIR = MEMORY_DIR / "decisions"
TRACE_FILE = MEMORY_DIR / "decision_traces.json"


def load_memories() -> List[Dict]:
    """加载所有记忆"""
    if MEMORIES_FILE.exists():
        return json.loads(MEMORIES_FILE.read_text())
    return []


def load_traces() -> Dict:
    """加载追溯链"""
    if TRACE_FILE.exists():
        return json.loads(TRACE_FILE.read_text())
    return {"traces": {}, "chains": []}


def save_traces(traces: Dict):
    """保存追溯链"""
    TRACE_FILE.write_text(json.dumps(traces, indent=2, ensure_ascii=False))


def find_memory_by_id(memories: List[Dict], mem_id: str) -> Optional[Dict]:
    """通过ID查找记忆"""
    for m in memories:
        if m.get("id", "").startswith(mem_id) or mem_id in m.get("id", ""):
            return m
    return None


def find_related_memories(memories: List[Dict], mem: Dict) -> List[Dict]:
    """查找相关记忆（基于关键词和时间）"""
    related = []
    text = mem.get("text", "")
    timestamp = mem.get("timestamp", "")
    
    # 提取关键词
    import re
    keywords = set(re.findall(r'[\u4e00-\u9fff]+', text))
    
    for m in memories:
        if m.get("id") == mem.get("id"):
            continue
        
        m_text = m.get("text", "")
        m_keywords = set(re.findall(r'[\u4e00-\u9fff]+', m_text))
        
        # 关键词重叠度
        overlap = len(keywords & m_keywords)
        if overlap >= 2:  # 至少2个关键词重叠
            m["relevance"] = overlap
            related.append(m)
    
    # 按相关性排序
    related.sort(key=lambda x: x.get("relevance", 0), reverse=True)
    return related[:5]


def trace_memory(mem_id: str) -> Dict:
    """追溯记忆来源"""
    memories = load_memories()
    traces = load_traces()
    
    mem = find_memory_by_id(memories, mem_id)
    if not mem:
        return {"error": f"未找到记忆: {mem_id}"}
    
    # 查找相关记忆
    related = find_related_memories(memories, mem)
    
    # 构建追溯链
    chain = {
        "target": {
            "id": mem.get("id"),
            "text": mem.get("text", "")[:100],
            "timestamp": mem.get("timestamp"),
            "category": mem.get("category")
        },
        "related": [
            {
                "id": m.get("id"),
                "text": m.get("text", "")[:60],
                "relevance": m.get("relevance")
            }
            for m in related
        ],
        "timeline": []
    }
    
    # 时间线（按时间排序）
    timeline_memories = [mem] + related
    timeline_memories.sort(key=lambda x: x.get("timestamp", ""))
    
    for m in timeline_memories:
        chain["timeline"].append({
            "timestamp": m.get("timestamp"),
            "text": m.get("text", "")[:50],
            "id": m.get("id")
        })
    
    return chain


def show_timeline(limit: int = 10) -> List[Dict]:
    """显示决策时间线"""
    memories = load_memories()
    
    # 过滤决策类记忆
    decisions = [m for m in memories if m.get("category") == "decision"]
    decisions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    timeline = []
    for i, d in enumerate(decisions[:limit]):
        timeline.append({
            "order": i + 1,
            "timestamp": d.get("timestamp"),
            "text": d.get("text", "")[:80],
            "id": d.get("id")
        })
    
    return timeline


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Trace - 决策追溯链")
    parser.add_argument("mem_id", nargs="?", help="记忆ID")
    parser.add_argument("--timeline", "-t", action="store_true", help="显示决策时间线")
    parser.add_argument("--limit", "-l", type=int, default=10, help="显示数量")
    
    args = parser.parse_args()
    
    if args.timeline:
        print("📅 决策时间线\n")
        timeline = show_timeline(args.limit)
        for t in timeline:
            print(f"  [{t['order']}] {t['timestamp'][:10]}")
            print(f"      {t['text']}...")
            print()
        if not timeline:
            print("  暂无决策记录")
    
    elif args.mem_id:
        print(f"🔍 追溯记忆: {args.mem_id}\n")
        chain = trace_memory(args.mem_id)
        
        if "error" in chain:
            print(f"❌ {chain['error']}")
            return
        
        print("📍 目标记忆:")
        print(f"   {chain['target']['text']}...")
        print(f"   ID: {chain['target']['id']}")
        print(f"   时间: {chain['target']['timestamp']}")
        
        if chain['related']:
            print("\n🔗 相关记忆:")
            for r in chain['related']:
                print(f"   [{r['relevance']} 关键词] {r['text']}...")
        
        if len(chain['timeline']) > 1:
            print("\n📅 时间线:")
            for t in chain['timeline']:
                print(f"   {t['timestamp'][:10]} | {t['text']}...")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
