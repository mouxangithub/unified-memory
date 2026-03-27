#!/usr/bin/env python3
"""
Agent Collaboration Log - 多Agent协作日志 v1.0

功能:
- 记录Agent之间的协作历史
- 追踪任务分配和完成
- 支持协作统计分析

Usage:
    python3 scripts/agent_collab.py log --from "main" --to "xiaoliu" --action "share_memory" --content "刘总偏好飞书"
    python3 scripts/agent_collab.py history --agent "main"
    python3 scripts/agent_collab.py stats
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
COLLAB_DIR = MEMORY_DIR / "collaboration"
COLLAB_LOG = COLLAB_DIR / "collab_log.jsonl"
AGENTS_FILE = COLLAB_DIR / "agents.json"


def ensure_dirs():
    """确保目录存在"""
    COLLAB_DIR.mkdir(parents=True, exist_ok=True)
    if not AGENTS_FILE.exists():
        with open(AGENTS_FILE, 'w') as f:
            json.dump({"agents": ["main", "xiaoliu"]}, f, indent=2)


def log_collab(from_agent: str, to_agent: str, action: str, content: str, metadata: Dict = None):
    """记录协作日志"""
    ensure_dirs()
    
    entry = {
        "id": hashlib.md5(f"{datetime.now().isoformat()}{from_agent}{to_agent}{action}".encode()).hexdigest()[:12],
        "timestamp": datetime.now().isoformat(),
        "from_agent": from_agent,
        "to_agent": to_agent,
        "action": action,
        "content": content,
        "metadata": metadata or {}
    }
    
    with open(COLLAB_LOG, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"📝 协作日志已记录: {from_agent} → {to_agent} [{action}]")
    return entry["id"]


def get_history(agent: str = None, limit: int = 20):
    """获取协作历史"""
    if not COLLAB_LOG.exists():
        return []
    
    entries = []
    with open(COLLAB_LOG, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if agent is None or entry["from_agent"] == agent or entry["to_agent"] == agent:
                    entries.append(entry)
            except:
                continue
    
    return entries[-limit:]


def get_stats():
    """获取协作统计"""
    if not COLLAB_LOG.exists():
        return {"total": 0, "by_agent": {}, "by_action": {}}
    
    stats = {
        "total": 0,
        "by_agent": {},
        "by_action": {},
        "recent": []
    }
    
    with open(COLLAB_LOG, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                stats["total"] += 1
                
                # 按agent统计
                for agent in [entry["from_agent"], entry["to_agent"]]:
                    if agent not in stats["by_agent"]:
                        stats["by_agent"][agent] = 0
                    stats["by_agent"][agent] += 1
                
                # 按action统计
                action = entry["action"]
                if action not in stats["by_action"]:
                    stats["by_action"][action] = 0
                stats["by_action"][action] += 1
                
            except:
                continue
    
    stats["recent"] = get_history(limit=5)
    return stats


def main():
    parser = argparse.ArgumentParser(description="Agent Collaboration Log v1.0")
    parser.add_argument("command", choices=["log", "history", "stats", "clear"])
    parser.add_argument("--from", dest="from_agent", help="来源Agent")
    parser.add_argument("--to", dest="to_agent", help="目标Agent")
    parser.add_argument("--action", "-a", help="协作动作")
    parser.add_argument("--content", "-c", help="内容")
    parser.add_argument("--agent", help="查询指定Agent的历史")
    parser.add_argument("--limit", "-l", type=int, default=20, help="限制数量")
    parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    
    args = parser.parse_args()
    
    if args.command == "log":
        if not all([args.from_agent, args.to_agent, args.action]):
            print("❌ 缺少参数: --from, --to, --action")
            return
        log_collab(args.from_agent, args.to_agent, args.action, args.content or "")
    
    elif args.command == "history":
        history = get_history(args.agent, args.limit)
        if args.json:
            print(json.dumps(history, ensure_ascii=False, indent=2))
        else:
            print(f"📜 协作历史 (共 {len(history)} 条)")
            for entry in history:
                ts = entry["timestamp"][:16]
                print(f"  [{ts}] {entry['from_agent']} → {entry['to_agent']}: {entry['action']}")
    
    elif args.command == "stats":
        stats = get_stats()
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print("📊 协作统计")
            print(f"   总计: {stats['total']} 次协作")
            print(f"   按Agent: {stats['by_agent']}")
            print(f"   按动作: {stats['by_action']}")
    
    elif args.command == "clear":
        if COLLAB_LOG.exists():
            COLLAB_LOG.unlink()
            print("🗑️ 协作日志已清空")


if __name__ == "__main__":
    main()
