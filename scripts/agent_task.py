#!/usr/bin/env python3
"""
Agent Task Collaboration - 协作任务分配系统 v1.0

功能:
- 任务创建与分配
- 任务状态追踪
- 跨Agent任务通知
- 任务完成统计

Usage:
    # 创建任务
    python3 scripts/agent_task.py create --title "整理记忆系统文档" --assignee "xiaoliu" --creator "main"
    
    # 查看任务
    python3 scripts/agent_task.py list --agent "main"
    
    # 更新任务状态
    python3 scripts/agent_task.py update --task-id "xxx" --status "completed"
    
    # 查看统计
    python3 scripts/agent_task.py stats
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
TASKS_DIR = MEMORY_DIR / "tasks"
TASKS_FILE = TASKS_DIR / "tasks.jsonl"
TASK_LOG = TASKS_DIR / "task_log.jsonl"


def ensure_dirs():
    """确保目录存在"""
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.touch()
    if not TASK_LOG.exists():
        TASK_LOG.touch()


def create_task(title: str, assignee: str, creator: str, description: str = "", priority: str = "normal") -> Dict:
    """创建任务"""
    ensure_dirs()
    
    task = {
        "id": hashlib.md5(f"{datetime.now().isoformat()}{title}".encode()).hexdigest()[:12],
        "timestamp": datetime.now().isoformat(),
        "title": title,
        "description": description,
        "creator": creator,
        "assignee": assignee,
        "status": "pending",  # pending, in_progress, completed, cancelled
        "priority": priority,  # low, normal, high, urgent
        "history": [
            {
                "action": "created",
                "timestamp": datetime.now().isoformat(),
                "agent": creator
            }
        ]
    }
    
    with open(TASKS_FILE, 'a') as f:
        f.write(json.dumps(task, ensure_ascii=False) + '\n')
    
    # 记录日志
    log_action("create", task["id"], creator, f"分配给 {assignee}")
    
    print(f"📋 创建任务: [{task['id']}] {title}")
    print(f"   创建者: {creator}")
    print(f"   执行者: {assignee}")
    print(f"   优先级: {priority}")
    
    return task


def update_task(task_id: str, status: str = None, note: str = "", agent: str = "unknown") -> Dict:
    """更新任务状态"""
    ensure_dirs()
    
    tasks = []
    updated_task = None
    
    with open(TASKS_FILE, 'r') as f:
        for line in f:
            try:
                task = json.loads(line.strip())
                if task["id"] == task_id:
                    old_status = task["status"]
                    if status:
                        task["status"] = status
                    task["history"].append({
                        "action": "status_change",
                        "from": old_status,
                        "to": status or old_status,
                        "note": note,
                        "timestamp": datetime.now().isoformat(),
                        "agent": agent
                    })
                    updated_task = task
                tasks.append(task)
            except:
                continue
    
    if updated_task:
        with open(TASKS_FILE, 'w') as f:
            for task in tasks:
                f.write(json.dumps(task, ensure_ascii=False) + '\n')
        
        log_action("update", task_id, agent, f"状态: {status}, 备注: {note}")
        print(f"✅ 更新任务: [{task_id}] 状态 → {status}")
    
    return updated_task or {}


def list_tasks(agent: str = None, status: str = None, limit: int = 20) -> List[Dict]:
    """列出任务"""
    ensure_dirs()
    
    tasks = []
    with open(TASKS_FILE, 'r') as f:
        for line in f:
            try:
                task = json.loads(line.strip())
                # 过滤
                if agent and task["assignee"] != agent and task["creator"] != agent:
                    continue
                if status and task["status"] != status:
                    continue
                tasks.append(task)
            except:
                continue
    
    # 按时间排序
    tasks.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return tasks[:limit]


def get_task(task_id: str) -> Optional[Dict]:
    """获取单个任务"""
    ensure_dirs()
    
    with open(TASKS_FILE, 'r') as f:
        for line in f:
            try:
                task = json.loads(line.strip())
                if task["id"] == task_id:
                    return task
            except:
                continue
    
    return None


def get_stats(agent: str = None) -> Dict:
    """获取任务统计"""
    ensure_dirs()
    
    stats = {
        "total": 0,
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
        "cancelled": 0,
        "by_agent": {},
        "by_priority": {"low": 0, "normal": 0, "high": 0, "urgent": 0}
    }
    
    with open(TASKS_FILE, 'r') as f:
        for line in f:
            try:
                task = json.loads(line.strip())
                
                # 过滤
                if agent and task["assignee"] != agent and task["creator"] != agent:
                    continue
                
                stats["total"] += 1
                stats[task["status"]] = stats.get(task["status"], 0) + 1
                stats["by_priority"][task["priority"]] = stats["by_priority"].get(task["priority"], 0) + 1
                
                # 按agent统计
                assignee = task["assignee"]
                if assignee not in stats["by_agent"]:
                    stats["by_agent"][assignee] = {"total": 0, "completed": 0}
                stats["by_agent"][assignee]["total"] += 1
                if task["status"] == "completed":
                    stats["by_agent"][assignee]["completed"] += 1
                    
            except:
                continue
    
    return stats


def log_action(action: str, task_id: str, agent: str, detail: str):
    """记录任务日志"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "task_id": task_id,
        "agent": agent,
        "detail": detail
    }
    
    with open(TASK_LOG, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def notify_agent(agent_id: str, message: str):
    """通知其他Agent（通过协作日志）"""
    try:
        import subprocess
        subprocess.run(
            ["python3", str(WORKSPACE / "skills/unified-memory/scripts/agent_collab.py"),
             "log", "--from", "task_system", "--to", agent_id, "--action", "task_notify", "--content", message],
            capture_output=True, timeout=10
        )
    except:
        pass


def main():
    parser = argparse.ArgumentParser(description="Agent Task Collaboration v1.0")
    parser.add_argument("command", choices=["create", "list", "get", "update", "stats", "notify"])
    parser.add_argument("--title", "-t", help="任务标题")
    parser.add_argument("--description", "-d", help="任务描述")
    parser.add_argument("--assignee", "-a", help="执行者")
    parser.add_argument("--creator", "-c", help="创建者")
    parser.add_argument("--task-id", help="任务ID")
    parser.add_argument("--status", "-s", help="状态")
    parser.add_argument("--priority", "-p", default="normal", help="优先级")
    parser.add_argument("--note", "-n", help="备注")
    parser.add_argument("--agent", help="过滤指定Agent的任务")
    parser.add_argument("--limit", "-l", type=int, default=20, help="限制数量")
    parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    
    args = parser.parse_args()
    
    if args.command == "create":
        if not all([args.title, args.assignee, args.creator]):
            print("❌ 缺少参数: --title, --assignee, --creator")
            return
        task = create_task(args.title, args.assignee, args.creator, args.description or "", args.priority)
        if args.json:
            print(json.dumps(task, ensure_ascii=False, indent=2))
    
    elif args.command == "list":
        tasks = list_tasks(args.agent, args.status, args.limit)
        if args.json:
            print(json.dumps(tasks, ensure_ascii=False, indent=2))
        else:
            print(f"📋 任务列表 (共 {len(tasks)} 条)")
            for task in tasks:
                status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "cancelled": "❌"}
                print(f"  {status_emoji.get(task['status'], '❓')} [{task['id']}] {task['title']}")
                print(f"      执行者: {task['assignee']} | 优先级: {task['priority']}")
    
    elif args.command == "get":
        if not args.task_id:
            print("❌ 缺少参数: --task-id")
            return
        task = get_task(args.task_id)
        if task:
            if args.json:
                print(json.dumps(task, ensure_ascii=False, indent=2))
            else:
                print(f"📋 任务详情: [{task['id']}]")
                print(f"   标题: {task['title']}")
                print(f"   描述: {task['description']}")
                print(f"   创建者: {task['creator']}")
                print(f"   执行者: {task['assignee']}")
                print(f"   状态: {task['status']}")
                print(f"   优先级: {task['priority']}")
        else:
            print(f"❌ 任务不存在: {args.task_id}")
    
    elif args.command == "update":
        if not args.task_id:
            print("❌ 缺少参数: --task-id")
            return
        task = update_task(args.task_id, args.status, args.note or "", args.agent or "unknown")
        if args.json:
            print(json.dumps(task, ensure_ascii=False, indent=2))
    
    elif args.command == "stats":
        stats = get_stats(args.agent)
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print("📊 任务统计")
            print(f"   总计: {stats['total']}")
            print(f"   待处理: {stats['pending']}")
            print(f"   进行中: {stats['in_progress']}")
            print(f"   已完成: {stats['completed']}")
            print(f"   已取消: {stats['cancelled']}")
            print(f"   按Agent: {stats['by_agent']}")
    
    elif args.command == "notify":
        if not all([args.assignee, args.title]):
            print("❌ 缺少参数: --assignee, --title")
            return
        notify_agent(args.assignee, args.title)
        print(f"📨 已通知 {args.assignee}: {args.title}")


if __name__ == "__main__":
    main()
