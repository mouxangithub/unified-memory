#!/usr/bin/env python3
"""
Memory Source Tracker - 记忆来源溯源系统 v1.0

功能:
- 记录记忆来源Agent
- 追溯记忆创建者
- 冲突时确认来源
- 来源统计分析

Usage:
    # 存储带来源标记的记忆
    python3 scripts/memory_source.py store --text "刘总偏好飞书" --agent "main" --category "preference"
    
    # 查询记忆来源
    python3 scripts/memory_source.py trace --memory-id "xxx"
    
    # 查看来源统计
    python3 scripts/memory_source.py stats
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
SOURCE_DIR = MEMORY_DIR / "source"
SOURCE_FILE = SOURCE_DIR / "sources.jsonl"


def ensure_dirs():
    """确保目录存在"""
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    if not SOURCE_FILE.exists():
        SOURCE_FILE.touch()


def store_with_source(text: str, agent: str, category: str = "other", metadata: Dict = None) -> Dict:
    """存储带来源标记的记忆"""
    ensure_dirs()
    
    memory_id = hashlib.md5(f"{datetime.now().isoformat()}{text}".encode()).hexdigest()[:12]
    
    source_entry = {
        "memory_id": memory_id,
        "timestamp": datetime.now().isoformat(),
        "text": text,
        "source_agent": agent,
        "category": category,
        "metadata": metadata or {},
        "verified": False,
        "conflicts": []
    }
    
    # 存储到来源追踪文件
    with open(SOURCE_FILE, 'a') as f:
        f.write(json.dumps(source_entry, ensure_ascii=False) + '\n')
    
    # 同时存储到记忆系统
    try:
        import subprocess
        result = subprocess.run(
            ["python3", str(WORKSPACE / "skills/unified-memory/scripts/memory_agent.py"),
             "quick-store", f"[{agent}] {text}"],
            capture_output=True, timeout=30, text=True
        )
    except Exception as e:
        print(f"⚠️ 存储到记忆系统失败: {e}")
    
    print(f"📝 存储记忆: [{memory_id}] [{agent}] {text[:50]}...")
    
    return source_entry


def trace_memory(memory_id: str) -> Optional[Dict]:
    """追溯记忆来源"""
    ensure_dirs()
    
    with open(SOURCE_FILE, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry["memory_id"] == memory_id:
                    return entry
            except:
                continue
    
    return None


def find_by_agent(agent: str, limit: int = 20) -> List[Dict]:
    """查找指定Agent的记忆"""
    ensure_dirs()
    
    memories = []
    with open(SOURCE_FILE, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry["source_agent"] == agent:
                    memories.append(entry)
            except:
                continue
    
    memories.sort(key=lambda x: x["timestamp"], reverse=True)
    return memories[:limit]


def find_conflicts() -> List[Dict]:
    """查找有冲突的记忆"""
    ensure_dirs()
    
    conflicts = []
    with open(SOURCE_FILE, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("conflicts"):
                    conflicts.append(entry)
            except:
                continue
    
    return conflicts


def verify_memory(memory_id: str, verified_by: str) -> Dict:
    """验证记忆"""
    ensure_dirs()
    
    entries = []
    verified_entry = None
    
    with open(SOURCE_FILE, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry["memory_id"] == memory_id:
                    entry["verified"] = True
                    entry["verified_by"] = verified_by
                    entry["verified_at"] = datetime.now().isoformat()
                    verified_entry = entry
                entries.append(entry)
            except:
                continue
    
    if verified_entry:
        with open(SOURCE_FILE, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print(f"✅ 验证记忆: [{memory_id}] 由 {verified_by} 验证")
    
    return verified_entry or {}


def get_stats() -> Dict:
    """获取来源统计"""
    ensure_dirs()
    
    stats = {
        "total": 0,
        "by_agent": {},
        "by_category": {},
        "verified": 0,
        "unverified": 0,
        "conflicts": 0
    }
    
    with open(SOURCE_FILE, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                stats["total"] += 1
                
                # 按Agent统计
                agent = entry["source_agent"]
                if agent not in stats["by_agent"]:
                    stats["by_agent"][agent] = 0
                stats["by_agent"][agent] += 1
                
                # 按类别统计
                category = entry["category"]
                if category not in stats["by_category"]:
                    stats["by_category"][category] = 0
                stats["by_category"][category] += 1
                
                # 验证状态
                if entry.get("verified"):
                    stats["verified"] += 1
                else:
                    stats["unverified"] += 1
                
                # 冲突
                if entry.get("conflicts"):
                    stats["conflicts"] += 1
                    
            except:
                continue
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Memory Source Tracker v1.0")
    parser.add_argument("command", choices=["store", "trace", "find", "conflicts", "verify", "stats"])
    parser.add_argument("--text", "-t", help="记忆内容")
    parser.add_argument("--agent", "-a", help="来源Agent")
    parser.add_argument("--category", "-c", default="other", help="记忆类别")
    parser.add_argument("--memory-id", help="记忆ID")
    parser.add_argument("--verified-by", help="验证者")
    parser.add_argument("--limit", "-l", type=int, default=20, help="限制数量")
    parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    
    args = parser.parse_args()
    
    if args.command == "store":
        if not all([args.text, args.agent]):
            print("❌ 缺少参数: --text, --agent")
            return
        entry = store_with_source(args.text, args.agent, args.category)
        if args.json:
            print(json.dumps(entry, ensure_ascii=False, indent=2))
    
    elif args.command == "trace":
        if not args.memory_id:
            print("❌ 缺少参数: --memory-id")
            return
        entry = trace_memory(args.memory_id)
        if entry:
            if args.json:
                print(json.dumps(entry, ensure_ascii=False, indent=2))
            else:
                print(f"🔍 记忆来源: [{entry['memory_id']}]")
                print(f"   来源Agent: {entry['source_agent']}")
                print(f"   时间: {entry['timestamp']}")
                print(f"   类别: {entry['category']}")
                print(f"   内容: {entry['text'][:100]}...")
                print(f"   已验证: {'✅' if entry.get('verified') else '❌'}")
        else:
            print(f"❌ 记忆不存在: {args.memory_id}")
    
    elif args.command == "find":
        if not args.agent:
            print("❌ 缺少参数: --agent")
            return
        memories = find_by_agent(args.agent, args.limit)
        if args.json:
            print(json.dumps(memories, ensure_ascii=False, indent=2))
        else:
            print(f"📋 [{args.agent}] 的记忆 (共 {len(memories)} 条)")
            for mem in memories:
                print(f"  [{mem['memory_id']}] {mem['text'][:50]}...")
    
    elif args.command == "conflicts":
        conflicts = find_conflicts()
        if args.json:
            print(json.dumps(conflicts, ensure_ascii=False, indent=2))
        else:
            print(f"⚠️ 冲突记忆 (共 {len(conflicts)} 条)")
            for mem in conflicts:
                print(f"  [{mem['memory_id']}] {mem['text'][:50]}...")
                print(f"      冲突: {mem['conflicts']}")
    
    elif args.command == "verify":
        if not all([args.memory_id, args.verified_by]):
            print("❌ 缺少参数: --memory-id, --verified-by")
            return
        entry = verify_memory(args.memory_id, args.verified_by)
        if args.json:
            print(json.dumps(entry, ensure_ascii=False, indent=2))
    
    elif args.command == "stats":
        stats = get_stats()
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print("📊 来源统计")
            print(f"   总计: {stats['total']}")
            print(f"   按Agent: {stats['by_agent']}")
            print(f"   按类别: {stats['by_category']}")
            print(f"   已验证: {stats['verified']}")
            print(f"   未验证: {stats['unverified']}")
            print(f"   冲突数: {stats['conflicts']}")


if __name__ == "__main__":
    main()
