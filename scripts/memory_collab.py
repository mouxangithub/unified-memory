#!/usr/bin/env python3
"""
协作效率可视化 v1.0

功能:
- 统计小智和小刘的任务完成情况
- 分析协作流转效率
- 生成可视化报告

Usage:
    mem collab                    # 显示协作统计
    mem collab --html             # 生成HTML报告
    mem collab --period 7         # 最近7天统计
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List

MEMORY_DIR = Path.home() / ".openclaw/workspace/memory"
COLLAB_DIR = Path.home() / ".openclaw/workspace/collab"
TASKS_DIR = Path.home() / ".openclaw/workspace/tasks"
HANDOVER_DIR = Path.home() / ".openclaw/workspace/handover"
STATS_FILE = MEMORY_DIR / "collab_stats.json"


def load_json_files(directory: Path, days: int = 7) -> List[Dict]:
    """加载目录下的JSON文件"""
    if not directory.exists():
        return []
    
    files = []
    cutoff = datetime.now() - timedelta(days=days)
    
    for f in directory.glob("*.json"):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime > cutoff:
                data = json.loads(f.read_text())
                data["_file"] = str(f)
                data["_mtime"] = mtime.isoformat()
                files.append(data)
        except:
            continue
    
    return files


def collect_stats(days: int = 7) -> Dict:
    """收集协作统计数据"""
    stats = {
        "period": f"最近{days}天",
        "generated_at": datetime.now().isoformat(),
        "agents": {
            "xiaozhi": {"tasks_completed": 0, "tasks_created": 0, "handovers_sent": 0},
            "xiaoliu": {"tasks_completed": 0, "tasks_created": 0, "handovers_sent": 0}
        },
        "collaboration": {
            "total_handovers": 0,
            "avg_response_time_hours": 0,
            "success_rate": 0
        },
        "tasks": {
            "total": 0,
            "completed": 0,
            "in_progress": 0
        },
        "timeline": []
    }
    
    # 统计任务
    task_files = load_json_files(TASKS_DIR, days)
    for task in task_files:
        stats["tasks"]["total"] += 1
        
        assignee = task.get("assignee", "unknown")
        status = task.get("status", "unknown")
        
        if status == "completed":
            stats["tasks"]["completed"] += 1
            if assignee in stats["agents"]:
                stats["agents"][assignee]["tasks_completed"] += 1
        elif status == "in_progress":
            stats["tasks"]["in_progress"] += 1
        
        creator = task.get("created_by", "unknown")
        if creator in stats["agents"]:
            stats["agents"][creator]["tasks_created"] += 1
    
    # 统计交接
    handover_files = load_json_files(HANDOVER_DIR, days)
    response_times = []
    
    for handover in handover_files:
        stats["collaboration"]["total_handovers"] += 1
        
        sender = handover.get("from", "unknown")
        if sender in stats["agents"]:
            stats["agents"][sender]["handovers_sent"] += 1
        
        # 计算响应时间
        if handover.get("responded_at") and handover.get("sent_at"):
            try:
                sent = datetime.fromisoformat(handover["sent_at"])
                responded = datetime.fromisoformat(handover["responded_at"])
                hours = (responded - sent).total_seconds() / 3600
                response_times.append(hours)
            except:
                pass
    
    # 平均响应时间
    if response_times:
        stats["collaboration"]["avg_response_time_hours"] = round(
            sum(response_times) / len(response_times), 1
        )
    
    # 成功率
    if stats["tasks"]["total"] > 0:
        stats["collaboration"]["success_rate"] = round(
            stats["tasks"]["completed"] / stats["tasks"]["total"] * 100, 1
        )
    
    # 时间线
    all_files = task_files + handover_files
    all_files.sort(key=lambda x: x.get("_mtime", ""), reverse=True)
    
    for f in all_files[:10]:
        stats["timeline"].append({
            "time": f.get("_mtime", "")[:10],
            "type": "task" if "task" in f.get("_file", "") else "handover",
            "summary": str(f)[:50]
        })
    
    return stats


def generate_html_report(stats: Dict) -> str:
    """生成HTML可视化报告"""
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>协作效率报告</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f5f5f5; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #4CAF50; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
        .agent-section {{ margin: 20px 0; padding: 15px; background: #fafafa; border-radius: 8px; }}
        .progress-bar {{ background: #e0e0e0; height: 20px; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ background: #4CAF50; height: 100%; transition: width 0.3s; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <h1>🤝 协作效率报告</h1>
    <p>统计周期: {stats["period"]} | 生成时间: {stats["generated_at"][:10]}</p>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{stats["tasks"]["total"]}</div>
            <div class="stat-label">总任务数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats["tasks"]["completed"]}</div>
            <div class="stat-label">已完成</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats["collaboration"]["success_rate"]}%</div>
            <div class="stat-label">完成率</div>
        </div>
    </div>
    
    <div class="agent-section">
        <h2>📊 Agent 统计</h2>
        <table>
            <tr>
                <th>Agent</th>
                <th>完成任务</th>
                <th>创建任务</th>
                <th>发起交接</th>
            </tr>
            <tr>
                <td>🤖 小智</td>
                <td>{stats["agents"]["xiaozhi"]["tasks_completed"]}</td>
                <td>{stats["agents"]["xiaozhi"]["tasks_created"]}</td>
                <td>{stats["agents"]["xiaozhi"]["handovers_sent"]}</td>
            </tr>
            <tr>
                <td>🤖 小刘</td>
                <td>{stats["agents"]["xiaoliu"]["tasks_completed"]}</td>
                <td>{stats["agents"]["xiaoliu"]["tasks_created"]}</td>
                <td>{stats["agents"]["xiaoliu"]["handovers_sent"]}</td>
            </tr>
        </table>
    </div>
    
    <div class="agent-section">
        <h2>🔄 协作效率</h2>
        <p><strong>总交接次数:</strong> {stats["collaboration"]["total_handovers"]}</p>
        <p><strong>平均响应时间:</strong> {stats["collaboration"]["avg_response_time_hours"]} 小时</p>
        
        <p><strong>任务完成进度:</strong></p>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {stats["collaboration"]["success_rate"]}%"></div>
        </div>
    </div>
    
    <div class="agent-section">
        <h2>📅 最近活动</h2>
        <table>
            <tr><th>时间</th><th>类型</th><th>摘要</th></tr>
'''
    
    for event in stats["timeline"]:
        html += f'<tr><td>{event["time"]}</td><td>{event["type"]}</td><td>{event["summary"]}</td></tr>\n'
    
    html += '''        </table>
    </div>
</body>
</html>'''
    
    return html


def print_text_report(stats: Dict):
    """打印文本报告"""
    print(f"🤝 协作效率报告 - {stats['period']}\n")
    print("=" * 50)
    
    print("\n📊 总体统计")
    print(f"   总任务: {stats['tasks']['total']}")
    print(f"   已完成: {stats['tasks']['completed']}")
    print(f"   进行中: {stats['tasks']['in_progress']}")
    print(f"   完成率: {stats['collaboration']['success_rate']}%")
    
    print("\n🤖 Agent 统计")
    print("   小智:")
    print(f"      完成任务: {stats['agents']['xiaozhi']['tasks_completed']}")
    print(f"      创建任务: {stats['agents']['xiaozhi']['tasks_created']}")
    print(f"      发起交接: {stats['agents']['xiaozhi']['handovers_sent']}")
    
    print("   小刘:")
    print(f"      完成任务: {stats['agents']['xiaoliu']['tasks_completed']}")
    print(f"      创建任务: {stats['agents']['xiaoliu']['tasks_created']}")
    print(f"      发起交接: {stats['agents']['xiaoliu']['handovers_sent']}")
    
    print("\n🔄 协作效率")
    print(f"   总交接次数: {stats['collaboration']['total_handovers']}")
    print(f"   平均响应时间: {stats['collaboration']['avg_response_time_hours']} 小时")
    
    # 进度条
    progress = int(stats['collaboration']['success_rate'] / 5)
    bar = "█" * progress + "░" * (20 - progress)
    print(f"\n   任务完成进度: |{bar}| {stats['collaboration']['success_rate']}%")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="协作效率可视化")
    parser.add_argument("--html", "-H", action="store_true", help="生成HTML报告")
    parser.add_argument("--period", "-p", type=int, default=7, help="统计周期（天）")
    parser.add_argument("--save", "-s", action="store_true", help="保存统计")
    
    args = parser.parse_args()
    
    # 收集统计
    stats = collect_stats(args.period)
    
    if args.html:
        html = generate_html_report(stats)
        output = MEMORY_DIR / "collab_report.html"
        output.write_text(html)
        print(f"✅ HTML报告已生成: {output}")
    else:
        print_text_report(stats)
    
    if args.save:
        STATS_FILE.write_text(json.dumps(stats, indent=2, ensure_ascii=False))
        print(f"\n💾 统计已保存: {STATS_FILE}")


if __name__ == "__main__":
    main()
