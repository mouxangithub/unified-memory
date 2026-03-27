#!/usr/bin/env python3
"""
Workflow Visualizer - 工作流可视化

功能:
- 实时进度显示（HTML）
- 记忆图谱可视化
- Context Tree 可视化
- 记忆统计面板

Usage:
    viz = WorkflowVisualizer()
    viz.add_task("t1", "设计架构", "PM")
    viz.update_progress("t1", 50)
    status = viz.get_status()
    
    # 生成 HTML 报告
    html = generate_dashboard(status)
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskProgress:
    task_id: str
    name: str
    status: TaskStatus
    progress: float
    agent: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


class WorkflowVisualizer:
    """工作流可视化"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskProgress] = {}
        self.history: List[Dict] = []
    
    def add_task(self, task_id: str, name: str, agent: str = None):
        self.tasks[task_id] = TaskProgress(
            task_id=task_id, name=name, status=TaskStatus.PENDING,
            progress=0, agent=agent, started_at=datetime.now().isoformat()
        )
    
    def update_progress(self, task_id: str, progress: float):
        if task_id in self.tasks:
            self.tasks[task_id].progress = min(100, max(0, progress))
            if progress > 0 and self.tasks[task_id].status == TaskStatus.PENDING:
                self.tasks[task_id].status = TaskStatus.RUNNING
    
    def complete_task(self, task_id: str):
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
            self.tasks[task_id].progress = 100
            self.tasks[task_id].completed_at = datetime.now().isoformat()
    
    def fail_task(self, task_id: str):
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.FAILED
    
    def get_status(self) -> Dict:
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        
        return {
            "total": total,
            "completed": completed,
            "running": running,
            "failed": failed,
            "pending": pending,
            "progress": (completed / total * 100) if total > 0 else 0,
            "tasks": [t.to_dict() for t in self.tasks.values()]
        }


def generate_dashboard(status: Dict, title: str = "记忆系统状态") -> str:
    """生成 HTML 仪表盘"""
    
    status_color = {
        "completed": "#22c55e",
        "running": "#3b82f6", 
        "failed": "#ef4444",
        "pending": "#94a3b8"
    }
    
    tasks_html = ""
    for task in status.get("tasks", []):
        s = task["status"]
        color = status_color.get(s, "#94a3b8")
        pct = task["progress"]
        
        tasks_html += f"""
        <div class="task">
          <div class="task-header">
            <span class="task-name">{task['name']}</span>
            <span class="task-agent">{task.get('agent', '')}</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {pct}%; background: {color}"></div>
          </div>
          <div class="task-meta">
            <span class="status {s}">{s.upper()}</span>
            <span class="progress-text">{pct:.0f}%</span>
          </div>
        </div>"""
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 24px; }}
.header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }}
h1 {{ font-size: 24px; font-weight: 600; }}
.timestamp {{ color: #64748b; font-size: 14px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px; }}
.stat {{ background: #1e293b; border-radius: 12px; padding: 20px; }}
.stat-value {{ font-size: 36px; font-weight: 700; }}
.stat-label {{ color: #94a3b8; font-size: 14px; margin-top: 4px; }}
.stat.completed .stat-value {{ color: #22c55e; }}
.stat.running .stat-value {{ color: #3b82f6; }}
.stat.failed .stat-value {{ color: #ef4444; }}
.overall-progress {{ background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 32px; }}
.progress-header {{ display: flex; justify-content: space-between; margin-bottom: 12px; }}
.progress-track {{ background: #334155; border-radius: 8px; height: 16px; overflow: hidden; }}
.progress-fill {{ height: 100%; background: linear-gradient(90deg, #3b82f6, #22c55e); border-radius: 8px; transition: width 0.3s; }}
.tasks {{ background: #1e293b; border-radius: 12px; padding: 20px; }}
.tasks h2 {{ font-size: 18px; margin-bottom: 16px; }}
.task {{ margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #334155; }}
.task:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
.task-header {{ display: flex; justify-content: space-between; margin-bottom: 8px; }}
.task-name {{ font-weight: 500; }}
.task-agent {{ color: #94a3b8; font-size: 14px; }}
.progress-bar {{ background: #334155; border-radius: 6px; height: 8px; overflow: hidden; margin-bottom: 8px; }}
.task-meta {{ display: flex; justify-content: space-between; font-size: 13px; }}
.status {{ padding: 2px 8px; border-radius: 4px; font-weight: 500; }}
.status.completed {{ background: #22c55e20; color: #22c55e; }}
.status.running {{ background: #3b82f620; color: #3b82f6; }}
.status.failed {{ background: #ef444420; color: #ef4444; }}
.status.pending {{ background: #94a3b820; color: #94a3b8; }}
</style>
</head>
<body>
<div class="header">
  <h1>{title}</h1>
  <span class="timestamp">更新于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
</div>

<div class="grid">
  <div class="stat completed">
    <div class="stat-value">{status.get('completed', 0)}</div>
    <div class="stat-label">已完成</div>
  </div>
  <div class="stat running">
    <div class="stat-value">{status.get('running', 0)}</div>
    <div class="stat-label">进行中</div>
  </div>
  <div class="stat failed">
    <div class="stat-value">{status.get('failed', 0)}</div>
    <div class="stat-label">失败</div>
  </div>
  <div class="stat">
    <div class="stat-value">{status.get('total', 0)}</div>
    <div class="stat-label">总任务</div>
  </div>
</div>

<div class="overall-progress">
  <div class="progress-header">
    <span>总体进度</span>
    <span>{status.get('progress', 0):.1f}%</span>
  </div>
  <div class="progress-track">
    <div class="progress-fill" style="width: {status.get('progress', 0)}%"></div>
  </div>
</div>

<div class="tasks">
  <h2>任务详情</h2>
  {tasks_html or '<p style="color:#64748b">暂无任务</p>'}
</div>
</body>
</html>"""
    
    return html


def generate_memory_dashboard(memory_stats: Dict) -> str:
    """生成记忆系统仪表盘"""
    
    stats = memory_stats.get("stats", {})
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>记忆系统仪表盘</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 24px; }}
h1 {{ font-size: 24px; margin-bottom: 24px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 32px; }}
.card {{ background: #1e293b; border-radius: 12px; padding: 24px; }}
.value {{ font-size: 42px; font-weight: 700; color: #3b82f6; }}
.label {{ color: #94a3b8; font-size: 14px; margin-top: 8px; }}
.section {{ background: #1e293b; border-radius: 12px; padding: 24px; margin-bottom: 16px; }}
.section h2 {{ font-size: 16px; color: #94a3b8; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 1px; }}
.bar {{ background: #334155; border-radius: 6px; height: 12px; margin-bottom: 8px; overflow: hidden; }}
.bar-fill {{ height: 100%; background: linear-gradient(90deg, #3b82f6, #8b5cf6); border-radius: 6px; }}
.tag {{ display: inline-block; background: #334155; padding: 4px 12px; border-radius: 16px; font-size: 13px; margin: 4px; }}
.timestamp {{ color: #64748b; font-size: 12px; position: fixed; bottom: 16px; right: 24px; }}
</style>
</head>
<body>
<h1>🧠 记忆系统仪表盘</h1>

<div class="grid">
  <div class="card">
    <div class="value">{stats.get('total_memories', 0)}</div>
    <div class="label">总记忆数</div>
  </div>
  <div class="card">
    <div class="value">{stats.get('vector_memories', 0)}</div>
    <div class="label">向量记忆</div>
  </div>
  <div class="card">
    <div class="value">{stats.get('access_count', 0)}</div>
    <div class="label">访问次数</div>
  </div>
  <div class="card">
    <div class="value">{stats.get('health_score', 0)}</div>
    <div class="label">健康分数</div>
  </div>
</div>

<div class="section">
  <h2>📊 系统状态</h2>
  <div class="bar"><div class="bar-fill" style="width: {stats.get('health_score', 0)}%"></div></div>
</div>

<div class="section">
  <h2>🏷️ 分类分布</h2>
  {''.join(f'<span class="tag">{k}: {v}</span>' for k, v in stats.get('category_dist', {}).items()) or '<span class="tag">暂无数据</span>'}
</div>

<div class="timestamp">更新于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
</body>
</html>"""
    
    return html


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow Visualizer")
    sub = parser.add_subparsers(dest="cmd")
    
    demo = sub.add_parser("demo", help="演示仪表盘")
    demo.add_argument("--output", "-o", default="/tmp/workflow_viz.html")
    
    args = parser.parse_args()
    
    viz = WorkflowVisualizer()
    viz.add_task("analyze", "需求分析", "PM")
    viz.add_task("design", "架构设计", "Architect")
    viz.add_task("frontend", "前端开发", "Frontend")
    viz.add_task("backend", "后端开发", "Backend")
    viz.add_task("test", "测试", "QA")
    
    viz.update_progress("analyze", 100)
    viz.update_progress("design", 100)
    viz.update_progress("frontend", 65)
    viz.update_progress("backend", 50)
    viz.update_progress("test", 0)
    
    status = viz.get_status()
    
    if args.cmd == "demo":
        html = generate_dashboard(status, "Workflow Demo")
        Path(args.output).write_text(html)
        print(f"✅ 仪表盘已生成: {args.output}")
