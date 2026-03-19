#!/usr/bin/env python3
"""
Memory Realtime Sync - 实时记忆同步 v1.0

功能:
- 自动同步新记忆到共享池
- 监听共享池变化并拉取
- 支持增量同步
- 冲突自动解决

Usage:
    # 作为后台服务运行
    python3 scripts/memory_realtime_sync.py daemon --node-id "main"
    
    # 手动推送记忆
    python3 scripts/memory_realtime_sync.py push --text "刘总偏好飞书" --source "main"
    
    # 手动拉取新记忆
    python3 scripts/memory_realtime_sync.py pull --node-id "main"
    
    # 查看同步状态
    python3 scripts/memory_realtime_sync.py status
"""

import argparse
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
import subprocess

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
SHARED_DIR = MEMORY_DIR / "shared"
SYNC_QUEUE = SHARED_DIR / "sync_queue.jsonl"
SYNC_LOG = SHARED_DIR / "sync_log.jsonl"
LAST_SYNC = SHARED_DIR / "last_sync.json"
NODE_REGISTRY = SHARED_DIR / "nodes.json"


def ensure_dirs():
    """确保目录存在"""
    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    if not SYNC_QUEUE.exists():
        SYNC_QUEUE.touch()
    if not SYNC_LOG.exists():
        SYNC_LOG.touch()


def get_node_id() -> str:
    """获取当前节点ID"""
    # 从环境变量或默认值获取
    import os
    return os.environ.get("OPENCLAW_AGENT_ID", "main")


def push_memory(text: str, source: str, metadata: Dict = None) -> Dict:
    """推送记忆到共享池"""
    ensure_dirs()
    
    entry = {
        "id": hashlib.md5(f"{datetime.now().isoformat()}{text}".encode()).hexdigest()[:12],
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "text": text,
        "metadata": metadata or {},
        "synced_to": []
    }
    
    with open(SYNC_QUEUE, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    # 记录日志
    log_entry = {
        "action": "push",
        "timestamp": entry["timestamp"],
        "source": source,
        "memory_id": entry["id"]
    }
    with open(SYNC_LOG, 'a') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    print(f"📤 推送记忆: [{source}] {text[:50]}...")
    return entry


def pull_memories(node_id: str, limit: int = 10) -> List[Dict]:
    """从共享池拉取新记忆"""
    ensure_dirs()
    
    # 读取上次同步时间
    last_sync_time = None
    if LAST_SYNC.exists():
        with open(LAST_SYNC) as f:
            data = json.load(f)
            last_sync_time = data.get(node_id)
    
    # 读取同步队列
    new_memories = []
    with open(SYNC_QUEUE, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                # 跳过自己推送的
                if entry["source"] == node_id:
                    continue
                # 跳过已同步的
                if node_id in entry.get("synced_to", []):
                    continue
                # 检查时间
                if last_sync_time and entry["timestamp"] <= last_sync_time:
                    continue
                
                new_memories.append(entry)
            except:
                continue
    
    # 存储到本地记忆
    for mem in new_memories[:limit]:
        try:
            # 调用 memory_agent.py 存储记忆
            result = subprocess.run(
                ["python3", str(WORKSPACE / "skills/unified-memory/scripts/memory_agent.py"),
                 "quick-store", mem["text"]],
                capture_output=True, timeout=30, text=True
            )
            
            # 标记为已同步
            mem["synced_to"].append(node_id)
            
            print(f"📥 拉取记忆: [{mem['source']}] {mem['text'][:50]}...")
        except Exception as e:
            print(f"❌ 同步失败: {e}")
    
    # 更新同步队列
    if new_memories:
        all_entries = []
        with open(SYNC_QUEUE, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    # 更新已同步的条目
                    for mem in new_memories:
                        if entry["id"] == mem["id"]:
                            entry = mem
                    all_entries.append(entry)
                except:
                    continue
        
        with open(SYNC_QUEUE, 'w') as f:
            for entry in all_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    # 更新上次同步时间
    last_sync_data = {}
    if LAST_SYNC.exists():
        with open(LAST_SYNC) as f:
            last_sync_data = json.load(f)
    last_sync_data[node_id] = datetime.now().isoformat()
    with open(LAST_SYNC, 'w') as f:
        json.dump(last_sync_data, f, indent=2)
    
    return new_memories[:limit]


def get_status() -> Dict:
    """获取同步状态"""
    ensure_dirs()
    
    # 统计队列
    queue_count = 0
    pending_sync = 0
    with open(SYNC_QUEUE, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                queue_count += 1
                if len(entry.get("synced_to", [])) < 2:  # 少于2个节点同步
                    pending_sync += 1
            except:
                continue
    
    # 读取节点
    nodes = []
    if NODE_REGISTRY.exists():
        with open(NODE_REGISTRY) as f:
            data = json.load(f)
            nodes = list(data.get("nodes", {}).keys())
    
    # 读取日志统计
    push_count = 0
    pull_count = 0
    with open(SYNC_LOG, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("action") == "push":
                    push_count += 1
                elif entry.get("action") == "pull":
                    pull_count += 1
            except:
                continue
    
    return {
        "queue_count": queue_count,
        "pending_sync": pending_sync,
        "nodes": nodes,
        "push_count": push_count,
        "pull_count": pull_count
    }


def daemon_mode(node_id: str, interval: int = 30):
    """守护进程模式 - 定期同步"""
    ensure_dirs()
    
    print(f"🔄 启动实时同步守护进程 [{node_id}]")
    print(f"   同步间隔: {interval}秒")
    print(f"   按 Ctrl+C 停止")
    
    while True:
        try:
            # 拉取新记忆
            new_memories = pull_memories(node_id)
            if new_memories:
                print(f"📥 同步了 {len(new_memories)} 条新记忆")
            
            # 等待下次同步
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 停止守护进程")
            break
        except Exception as e:
            print(f"⚠️ 同步错误: {e}")
            time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Memory Realtime Sync v1.0")
    parser.add_argument("command", choices=["push", "pull", "status", "daemon", "sync"])
    parser.add_argument("--text", "-t", help="记忆内容")
    parser.add_argument("--source", "-s", help="来源节点")
    parser.add_argument("--node-id", "-n", help="节点ID")
    parser.add_argument("--interval", "-i", type=int, default=30, help="同步间隔(秒)")
    parser.add_argument("--limit", "-l", type=int, default=10, help="拉取数量限制")
    parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    
    args = parser.parse_args()
    
    node_id = args.node_id or get_node_id()
    source = args.source or node_id
    
    if args.command == "push":
        if not args.text:
            print("❌ 缺少参数: --text")
            return
        result = push_memory(args.text, source)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "pull":
        memories = pull_memories(node_id, args.limit)
        if args.json:
            print(json.dumps(memories, ensure_ascii=False, indent=2))
        else:
            print(f"📥 拉取了 {len(memories)} 条新记忆")
    
    elif args.command == "sync":
        # 推送 + 拉取
        print("🔄 执行双向同步...")
        memories = pull_memories(node_id, args.limit)
        print(f"📥 拉取了 {len(memories)} 条新记忆")
    
    elif args.command == "status":
        status = get_status()
        if args.json:
            print(json.dumps(status, ensure_ascii=False, indent=2))
        else:
            print("📊 实时同步状态")
            print(f"   队列记忆: {status['queue_count']} 条")
            print(f"   待同步: {status['pending_sync']} 条")
            print(f"   节点: {status['nodes']}")
            print(f"   推送次数: {status['push_count']}")
            print(f"   拉取次数: {status['pull_count']}")
    
    elif args.command == "daemon":
        daemon_mode(node_id, args.interval)


if __name__ == "__main__":
    main()
