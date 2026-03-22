#!/usr/bin/env python3
"""
Workflow Visualizer - 工作流可视化

功能:
- 实时进度显示
- Agent 状态监控
- 任务依赖图
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
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
    
    def complete_task(self, task_id: str):
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
            self.tasks[task_id].progress = 100
    
    def fail_task(self, task_id: str):
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.FAILED
    
    def get_status(self) -> Dict:
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        return {
            "total": total,
            "completed": completed,
            "progress": (completed / total * 100) if total > 0 else 0,
            "tasks": [t.to_dict() for t in self.tasks.values()]
        }


if __name__ == "__main__":
    viz = WorkflowVisualizer()
    viz.add_task("t1", "设计架构", "PM")
    viz.update_progress("t1", 50)
    print(viz.get_status())
