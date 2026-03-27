#!/usr/bin/env python3
"""
Collaboration Analytics - 协作效率分析系统 v1.0

功能:
- 统计协作效率指标
- 分析任务完成率
- 识别协作瓶颈
- 生成优化建议

Usage:
    # 生成报告
    python3 scripts/collab_analytics.py report
    
    # 查看指标
    python3 scripts/collab_analytics.py metrics
    
    # 分析瓶颈
    python3 scripts/collab_analytics.py bottlenecks
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
TASKS_DIR = MEMORY_DIR / "tasks"
TASKS_FILE = TASKS_DIR / "tasks.jsonl"
COLLAB_DIR = MEMORY_DIR / "collaboration"
COLLAB_LOG = COLLAB_DIR / "collab_log.jsonl"
SYNC_DIR = MEMORY_DIR / "shared"
SYNC_QUEUE = SYNC_DIR / "sync_queue.jsonl"
ANALYTICS_DIR = MEMORY_DIR / "analytics"
REPORTS_FILE = ANALYTICS_DIR / "reports.jsonl"


def ensure_dirs():
    """确保目录存在"""
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    if not REPORTS_FILE.exists():
        REPORTS_FILE.touch()


def load_tasks() -> List[Dict]:
    """加载任务数据"""
    if not TASKS_FILE.exists():
        return []
    
    tasks = []
    with open(TASKS_FILE, 'r') as f:
        for line in f:
            try:
                tasks.append(json.loads(line.strip()))
            except:
                continue
    return tasks


def load_collab_logs() -> List[Dict]:
    """加载协作日志"""
    if not COLLAB_LOG.exists():
        return []
    
    logs = []
    with open(COLLAB_LOG, 'r') as f:
        for line in f:
            try:
                logs.append(json.loads(line.strip()))
            except:
                continue
    return logs


def load_sync_queue() -> List[Dict]:
    """加载同步队列"""
    if not SYNC_QUEUE.exists():
        return []
    
    items = []
    with open(SYNC_QUEUE, 'r') as f:
        for line in f:
            try:
                items.append(json.loads(line.strip()))
            except:
                continue
    return items


def calculate_metrics() -> Dict:
    """计算协作效率指标"""
    tasks = load_tasks()
    logs = load_collab_logs()
    sync_items = load_sync_queue()
    
    # 任务指标
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.get("status") == "completed")
    pending_tasks = sum(1 for t in tasks if t.get("status") == "pending")
    in_progress_tasks = sum(1 for t in tasks if t.get("status") == "in_progress")
    
    # 任务完成率
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # 平均任务时长（秒）
    task_durations = []
    for task in tasks:
        if task.get("status") == "completed" and task.get("history"):
            created = None
            completed = None
            for h in task["history"]:
                if h.get("action") == "created":
                    created = datetime.fromisoformat(h["timestamp"])
                elif h.get("action") == "status_change" and h.get("to") == "completed":
                    completed = datetime.fromisoformat(h["timestamp"])
            if created and completed:
                task_durations.append((completed - created).total_seconds())
    
    avg_task_duration = sum(task_durations) / len(task_durations) if task_durations else 0
    
    # 协作日志指标
    total_collabs = len(logs)
    collab_by_action = defaultdict(int)
    collab_by_agent = defaultdict(int)
    
    for log in logs:
        action = log.get("action", "unknown")
        collab_by_action[action] += 1
        
        from_agent = log.get("from_agent", "unknown")
        to_agent = log.get("to_agent", "unknown")
        collab_by_agent[from_agent] += 1
        collab_by_agent[to_agent] += 1
    
    # 同步指标
    total_syncs = len(sync_items)
    synced_items = sum(1 for s in sync_items if len(s.get("synced_to", [])) >= 2)
    pending_syncs = total_syncs - synced_items
    
    sync_rate = (synced_items / total_syncs * 100) if total_syncs > 0 else 0
    
    return {
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
            "pending": pending_tasks,
            "in_progress": in_progress_tasks,
            "completion_rate": round(completion_rate, 1),
            "avg_duration_seconds": round(avg_task_duration, 1)
        },
        "collaboration": {
            "total_actions": total_collabs,
            "by_action": dict(collab_by_action),
            "by_agent": dict(collab_by_agent)
        },
        "sync": {
            "total": total_syncs,
            "synced": synced_items,
            "pending": pending_syncs,
            "sync_rate": round(sync_rate, 1)
        },
        "timestamp": datetime.now().isoformat()
    }


def identify_bottlenecks() -> List[Dict]:
    """识别协作瓶颈"""
    metrics = calculate_metrics()
    bottlenecks = []
    
    # 任务积压
    if metrics["tasks"]["pending"] > 5:
        bottlenecks.append({
            "type": "task_backlog",
            "severity": "high" if metrics["tasks"]["pending"] > 10 else "medium",
            "description": f"待处理任务积压: {metrics['tasks']['pending']} 个",
            "suggestion": "考虑分配更多资源或调整优先级"
        })
    
    # 同步延迟
    if metrics["sync"]["pending"] > 3:
        bottlenecks.append({
            "type": "sync_delay",
            "severity": "medium",
            "description": f"待同步记忆: {metrics['sync']['pending']} 条",
            "suggestion": "检查同步服务是否正常运行"
        })
    
    # 任务完成率低
    if metrics["tasks"]["completion_rate"] < 50 and metrics["tasks"]["total"] > 0:
        bottlenecks.append({
            "type": "low_completion",
            "severity": "high",
            "description": f"任务完成率低: {metrics['tasks']['completion_rate']}%",
            "suggestion": "分析未完成任务原因，优化任务分配"
        })
    
    # Agent 活跃度不均
    agent_activity = metrics["collaboration"]["by_agent"]
    if agent_activity:
        max_activity = max(agent_activity.values())
        min_activity = min(agent_activity.values())
        if max_activity > 0 and max_activity / max(min_activity, 1) > 3:
            bottlenecks.append({
                "type": "agent_imbalance",
                "severity": "low",
                "description": "Agent 活跃度不均衡",
                "suggestion": "重新分配任务负载"
            })
    
    return bottlenecks


def generate_report() -> Dict:
    """生成完整报告"""
    ensure_dirs()
    
    metrics = calculate_metrics()
    bottlenecks = identify_bottlenecks()
    
    # 计算整体效率分数
    efficiency_score = 100
    
    # 任务完成率影响
    efficiency_score -= (100 - metrics["tasks"]["completion_rate"]) * 0.3
    
    # 同步率影响
    efficiency_score -= (100 - metrics["sync"]["sync_rate"]) * 0.2
    
    # 瓶颈影响
    for b in bottlenecks:
        if b["severity"] == "high":
            efficiency_score -= 10
        elif b["severity"] == "medium":
            efficiency_score -= 5
    
    efficiency_score = max(0, min(100, efficiency_score))
    
    report = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "timestamp": datetime.now().isoformat(),
        "efficiency_score": round(efficiency_score, 1),
        "metrics": metrics,
        "bottlenecks": bottlenecks,
        "recommendations": generate_recommendations(metrics, bottlenecks)
    }
    
    # 存储报告
    with open(REPORTS_FILE, 'a') as f:
        f.write(json.dumps(report, ensure_ascii=False) + '\n')
    
    return report


def generate_recommendations(metrics: Dict, bottlenecks: List[Dict]) -> List[str]:
    """生成优化建议"""
    recommendations = []
    
    if metrics["tasks"]["pending"] > 0:
        recommendations.append(f"有 {metrics['tasks']['pending']} 个待处理任务，建议优先处理")
    
    if metrics["sync"]["pending"] > 0:
        recommendations.append(f"有 {metrics['sync']['pending']} 条记忆待同步，建议执行同步")
    
    for b in bottlenecks:
        recommendations.append(f"[{b['type']}] {b['suggestion']}")
    
    return recommendations


def main():
    parser = argparse.ArgumentParser(description="Collaboration Analytics v1.0")
    parser.add_argument("command", choices=["report", "metrics", "bottlenecks", "history"])
    parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    parser.add_argument("--limit", "-l", type=int, default=10, help="限制数量")
    
    args = parser.parse_args()
    
    if args.command == "report":
        report = generate_report()
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"📊 协作效率报告 [{report['id']}]")
            print(f"   效率分数: {report['efficiency_score']}/100")
            print(f"\n   任务指标:")
            print(f"     总计: {report['metrics']['tasks']['total']}")
            print(f"     已完成: {report['metrics']['tasks']['completed']}")
            print(f"     完成率: {report['metrics']['tasks']['completion_rate']}%")
            print(f"\n   同步指标:")
            print(f"     总计: {report['metrics']['sync']['total']}")
            print(f"     同步率: {report['metrics']['sync']['sync_rate']}%")
            
            if report["bottlenecks"]:
                print(f"\n   ⚠️ 瓶颈 ({len(report['bottlenecks'])} 个):")
                for b in report["bottlenecks"]:
                    print(f"     - [{b['severity']}] {b['description']}")
            
            if report["recommendations"]:
                print(f"\n   💡 建议:")
                for r in report["recommendations"]:
                    print(f"     - {r}")
    
    elif args.command == "metrics":
        metrics = calculate_metrics()
        if args.json:
            print(json.dumps(metrics, ensure_ascii=False, indent=2))
        else:
            print("📊 协作指标")
            print(f"   任务: {metrics['tasks']}")
            print(f"   协作: {metrics['collaboration']}")
            print(f"   同步: {metrics['sync']}")
    
    elif args.command == "bottlenecks":
        bottlenecks = identify_bottlenecks()
        if args.json:
            print(json.dumps(bottlenecks, ensure_ascii=False, indent=2))
        else:
            if bottlenecks:
                print(f"⚠️ 协作瓶颈 ({len(bottlenecks)} 个)")
                for b in bottlenecks:
                    print(f"   [{b['severity']}] {b['type']}: {b['description']}")
                    print(f"      建议: {b['suggestion']}")
            else:
                print("✅ 未发现明显瓶颈")
    
    elif args.command == "history":
        if not REPORTS_FILE.exists():
            print("暂无历史报告")
            return
        
        reports = []
        with open(REPORTS_FILE, 'r') as f:
            for line in f:
                try:
                    reports.append(json.loads(line.strip()))
                except:
                    continue
        
        reports = reports[-args.limit:]
        
        if args.json:
            print(json.dumps(reports, ensure_ascii=False, indent=2))
        else:
            print(f"📈 历史报告 (最近 {len(reports)} 条)")
            for r in reports:
                print(f"   [{r['id']}] 效率分数: {r['efficiency_score']}/100")


if __name__ == "__main__":
    main()
