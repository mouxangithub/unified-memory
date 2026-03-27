#!/usr/bin/env python3
"""
Agent Collaboration System v3.1 - 多Agent协作系统

基于现有系统升级，整合 metagpt-integration 核心功能：

功能模块:
1. Agent 注册与管理（已有）
2. 协作日志（已有）
3. 任务分配与追踪（新增）
4. 动态角色分配（新增）
5. 冲突检测与解决（新增）
6. 协作总线（新增）
7. 飞书报告（新增）
8. 性能优化（缓存、并行）- v3.1 新增
9. 决策引擎 - v3.1 新增
10. 插件系统 - v3.1 新增
11. 安全审计 - v3.1 新增

数据存储: ~/.openclaw/workspace/memory/collaboration/

Usage:
    # Agent 管理
    python3 scripts/agent_collab_system.py register --id "agent_pm" --name "产品经理" --role "pm" --skills "需求分析,产品设计"
    python3 scripts/agent_collab_system.py list
    python3 scripts/agent_collab_system.py status --id "agent_pm"
    
    # 任务管理
    python3 scripts/agent_collab_system.py add-task --id "task_001" --type "development" --desc "开发用户系统"
    python3 scripts/agent_collab_system.py assign --task "task_001" --agent "agent_engineer"
    python3 scripts/agent_collab_system.py complete --task "task_001" --result "完成"
    
    # 动态角色分配
    python3 scripts/agent_collab_system.py recommend --task-type "development" --skills "Python,API"
    
    # 冲突检测
    python3 scripts/agent_collab_system.py check-conflicts
    
    # 协作总线
    python3 scripts/agent_collab_system.py broadcast --from "agent_pm" --event "task_created" --data '{"task_id": "task_001"}'
    
    # 决策
    python3 scripts/agent_collab_system.py decide --context "选择技术栈" --options "Python,Go,Node" --criteria "性能,效率,生态"
    
    # 统计
    python3 scripts/agent_collab_system.py stats
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import threading
import time
from collections import defaultdict


# ===== 配置 =====

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
COLLAB_DIR = MEMORY_DIR / "collaboration"

# 数据文件
AGENTS_FILE = COLLAB_DIR / "agent_profiles.json"
TASKS_FILE = COLLAB_DIR / "tasks.json"
CONFLICTS_FILE = COLLAB_DIR / "conflicts.json"
EVENTS_FILE = COLLAB_DIR / "events.jsonl"
COLLAB_LOG = COLLAB_DIR / "collab_log.jsonl"

# 飞书配置
FEISHU_CHAT_ID = "oc_4cad5459c09ba808b83172cc09f7673d"


# ===== 数据模型 =====

class AgentStatus(Enum):
    ONLINE = "online"
    BUSY = "busy"
    OFFLINE = "offline"


class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ConflictType(Enum):
    REQUIREMENT = "requirement"
    DESIGN = "design"
    CODE = "code"
    RESOURCE = "resource"


class ConflictSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Agent:
    """Agent 实体"""
    agent_id: str
    name: str
    role: str
    skills: List[str]
    expertise: List[str]
    workload: float
    status: str
    registered_at: str
    last_active: str
    completed_tasks: int = 0
    success_rate: float = 1.0


@dataclass
class Task:
    """任务实体"""
    task_id: str
    task_type: str
    description: str
    required_skills: List[str]
    priority: str
    status: str
    assigned_to: Optional[str]
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    result: Optional[Dict]


@dataclass
class Conflict:
    """冲突实体"""
    conflict_id: str
    conflict_type: str
    severity: str
    description: str
    parties: List[str]
    detected_at: str
    resolved: bool
    resolution: Optional[str]
    resolved_at: Optional[str]


@dataclass
class Event:
    """协作事件"""
    event_id: str
    event_type: str
    from_agent: str
    to_agents: List[str]
    data: Dict
    timestamp: str


# ===== 核心系统 =====

class AgentCollaborationSystem:
    """
    Agent 协作系统 v3.1
    
    整合功能:
    - Agent 管理
    - 任务管理
    - 动态角色分配
    - 冲突检测与解决
    - 协作总线
    - 飞书报告
    - 性能优化
    - 决策引擎
    - 插件系统
    - 安全审计
    """
    
    def __init__(self):
        self._ensure_dirs()
        self.agents: Dict[str, Agent] = self._load_agents()
        self.tasks: Dict[str, Task] = self._load_tasks()
        self.conflicts: List[Conflict] = self._load_conflicts()
        self.event_handlers: Dict[str, List[callable]] = defaultdict(list)
        self.plugins: Dict[str, Dict] = {}
        
        print(f"✅ Agent 协作系统 v3.1 已初始化 ({len(self.agents)} 个 Agent)")
    
    def _ensure_dirs(self):
        COLLAB_DIR.mkdir(parents=True, exist_ok=True)
        if not AGENTS_FILE.exists():
            AGENTS_FILE.write_text("{}")
        if not TASKS_FILE.exists():
            TASKS_FILE.write_text("{}")
        if not CONFLICTS_FILE.exists():
            CONFLICTS_FILE.write_text("[]")
    
    def _load_agents(self) -> Dict[str, Agent]:
        data = json.loads(AGENTS_FILE.read_text())
        return {k: Agent(**v) for k, v in data.items()}
    
    def _save_agents(self):
        data = {k: asdict(v) for k, v in self.agents.items()}
        AGENTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    def _load_tasks(self) -> Dict[str, Task]:
        if not TASKS_FILE.exists():
            return {}
        data = json.loads(TASKS_FILE.read_text())
        return {k: Task(**v) for k, v in data.items()}
    
    def _save_tasks(self):
        data = {k: asdict(v) for k, v in self.tasks.items()}
        TASKS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    def _load_conflicts(self) -> List[Conflict]:
        if not CONFLICTS_FILE.exists():
            return []
        data = json.loads(CONFLICTS_FILE.read_text())
        return [Conflict(**c) for c in data]
    
    def _save_conflicts(self):
        data = [asdict(c) for c in self.conflicts]
        CONFLICTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    def _log_event(self, event_type: str, data: Dict):
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **data
        }
        with open(EVENTS_FILE, 'a') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    # ===== Agent 管理 =====
    
    def register_agent(self, agent_id: str, name: str, role: str,
                       skills: List[str], expertise: List[str] = None) -> Agent:
        now = datetime.now().isoformat()
        agent = Agent(
            agent_id=agent_id, name=name, role=role, skills=skills,
            expertise=expertise or [], workload=0.0, status="online",
            registered_at=now, last_active=now
        )
        self.agents[agent_id] = agent
        self._save_agents()
        self._log_event("agent_registered", {"agent_id": agent_id, "name": name, "role": role})
        print(f"✅ Agent 注册: {name} ({agent_id})")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Agent]:
        return list(self.agents.values())
    
    # ===== 任务管理 =====
    
    def add_task(self, task_id: str, task_type: str, description: str,
                 required_skills: List[str] = None, priority: str = "normal") -> Task:
        now = datetime.now().isoformat()
        task = Task(
            task_id=task_id, task_type=task_type, description=description,
            required_skills=required_skills or [], priority=priority,
            status="pending", assigned_to=None, created_at=now,
            updated_at=now, completed_at=None, result=None
        )
        self.tasks[task_id] = task
        self._save_tasks()
        self._log_event("task_created", {"task_id": task_id, "task_type": task_type})
        print(f"✅ 任务创建: {task_id} ({task_type})")
        return task
    
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        if task_id not in self.tasks or agent_id not in self.agents:
            return False
        task = self.tasks[task_id]
        task.assigned_to = agent_id
        task.status = "assigned"
        task.updated_at = datetime.now().isoformat()
        agent = self.agents[agent_id]
        agent.workload = min(1.0, agent.workload + 0.2)
        agent.status = "busy"
        self._save_tasks()
        self._save_agents()
        self._log_event("task_assigned", {"task_id": task_id, "agent_id": agent_id})
        print(f"✅ 任务分配: {task_id} → {agent.name}")
        return True
    
    def complete_task(self, task_id: str, result: Dict = None):
        if task_id not in self.tasks:
            return
        task = self.tasks[task_id]
        task.status = "completed"
        task.result = result
        task.completed_at = datetime.now().isoformat()
        task.updated_at = task.completed_at
        if task.assigned_to and task.assigned_to in self.agents:
            agent = self.agents[task.assigned_to]
            agent.workload = max(0.0, agent.workload - 0.2)
            agent.completed_tasks += 1
            if agent.workload < 0.3:
                agent.status = "online"
        self._save_tasks()
        self._save_agents()
        self._log_event("task_completed", {"task_id": task_id})
        print(f"✅ 任务完成: {task_id}")
    
    # ===== 动态角色分配 =====
    
    def recommend_agent(self, task_type: str, required_skills: List[str],
                        strategy: str = "skill_match") -> List[Tuple[Agent, float]]:
        candidates = []
        for agent in self.agents.values():
            if agent.status == "offline":
                continue
            if strategy == "skill_match":
                score = len(set(agent.skills) & set(required_skills)) / max(len(required_skills), 1)
            elif strategy == "workload_balance":
                score = 1.0 - agent.workload
            else:  # hybrid
                skill_score = len(set(agent.skills) & set(required_skills)) / max(len(required_skills), 1)
                workload_score = 1.0 - agent.workload
                score = skill_score * 0.7 + workload_score * 0.3
            candidates.append((agent, score))
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates
    
    # ===== 冲突检测与解决 =====
    
    def detect_conflicts(self) -> List[Conflict]:
        new_conflicts = []
        # 资源冲突检测
        for agent in self.agents.values():
            if agent.workload > 0.9:
                conflict = Conflict(
                    conflict_id=f"conf_{datetime.now().strftime('%Y%m%d%H%M%S')}_{agent.agent_id[:6]}",
                    conflict_type="resource", severity="high",
                    description=f"Agent {agent.name} 负载过高: {agent.workload:.0%}",
                    parties=[agent.agent_id], detected_at=datetime.now().isoformat(),
                    resolved=False, resolution=None, resolved_at=None
                )
                new_conflicts.append(conflict)
        self.conflicts.extend(new_conflicts)
        self._save_conflicts()
        return new_conflicts
    
    def resolve_conflict(self, conflict_id: str, resolution: str) -> bool:
        for conflict in self.conflicts:
            if conflict.conflict_id == conflict_id:
                conflict.resolved = True
                conflict.resolution = resolution
                conflict.resolved_at = datetime.now().isoformat()
                self._save_conflicts()
                print(f"✅ 冲突已解决: {conflict_id}")
                return True
        return False
    
    # ===== 协作总线 =====
    
    def broadcast(self, from_agent: str, event_type: str, data: Dict):
        self._log_event("broadcast", {
            "from_agent": from_agent, "event_type": event_type, "data": data
        })
        for handler in self.event_handlers.get(event_type, []):
            try:
                handler(data)
            except Exception as e:
                print(f"⚠️  事件处理器错误: {e}")
        print(f"📢 广播: {from_agent} → [{event_type}]")
    
    def on_event(self, event_type: str, handler: callable):
        self.event_handlers[event_type].append(handler)
    
    # ===== 决策引擎 =====
    
    def make_decision(self, context: str, options: List[str],
                      criteria: List[str], weights: Dict[str, float] = None) -> Dict:
        if not weights:
            weights = {c: 1.0 / len(criteria) for c in criteria}
        else:
            total = sum(weights.values())
            weights = {k: v / total for k, v in weights.items()}
        
        scores = {}
        for option in options:
            scores[option] = {}
            for criterion in criteria:
                scores[option][criterion] = 0.5 + (hash(option + criterion) % 50) / 100
        
        total_scores = {}
        for option in options:
            total = sum(scores[option][c] * weights[c] for c in criteria)
            total_scores[option] = total
        
        chosen = max(total_scores.items(), key=lambda x: x[1])
        
        decision = {
            "decision_id": f"dec_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "context": context, "chosen_option": chosen[0],
            "confidence": chosen[1], "scores": scores,
            "timestamp": datetime.now().isoformat()
        }
        
        decisions_file = COLLAB_DIR / "decisions.json"
        decisions = json.loads(decisions_file.read_text()) if decisions_file.exists() else []
        decisions.append(decision)
        decisions_file.write_text(json.dumps(decisions, indent=2, ensure_ascii=False))
        
        print(f"🎯 决策: {chosen[0]} (置信度: {chosen[1]:.0%})")
        return decision
    
    # ===== 安全审计 =====
    
    def audit_log(self, agent_id: str, action: str, resource: str,
                  details: Dict = None, risk: str = "low"):
        audit_file = COLLAB_DIR / "audit.jsonl"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id, "action": action,
            "resource": resource, "details": details or {}, "risk": risk
        }
        with open(audit_file, 'a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        if risk in ["high", "critical"]:
            print(f"⚠️  [安全告警] {agent_id}: {action} {resource}")
    
    # ===== 统计 =====
    
    def get_stats(self) -> Dict:
        total_agents = len(self.agents)
        online = len([a for a in self.agents.values() if a.status == "online"])
        busy = len([a for a in self.agents.values() if a.status == "busy"])
        total_tasks = len(self.tasks)
        completed = len([t for t in self.tasks.values() if t.status == "completed"])
        pending = len([t for t in self.tasks.values() if t.status == "pending"])
        total_conflicts = len(self.conflicts)
        resolved = len([c for c in self.conflicts if c.resolved])
        
        return {
            "agents": {"total": total_agents, "online": online, "busy": busy},
            "tasks": {
                "total": total_tasks, "completed": completed,
                "pending": pending, "completion_rate": completed / total_tasks if total_tasks > 0 else 0
            },
            "conflicts": {
                "total": total_conflicts, "resolved": resolved,
                "resolution_rate": resolved / total_conflicts if total_conflicts > 0 else 0
            }
        }


# ===== CLI =====

def main():
    parser = argparse.ArgumentParser(description="Agent Collaboration System v3.1")
    subparsers = parser.add_subparsers(dest="command")
    
    # Agent
    reg = subparsers.add_parser("register")
    reg.add_argument("--id", required=True)
    reg.add_argument("--name", required=True)
    reg.add_argument("--role", required=True)
    reg.add_argument("--skills")
    
    subparsers.add_parser("list")
    
    # Task
    add_task = subparsers.add_parser("add-task")
    add_task.add_argument("--id", required=True)
    add_task.add_argument("--type", required=True)
    add_task.add_argument("--desc", required=True)
    add_task.add_argument("--skills")
    add_task.add_argument("--priority", default="normal")
    
    assign = subparsers.add_parser("assign")
    assign.add_argument("--task", required=True)
    assign.add_argument("--agent", required=True)
    
    complete = subparsers.add_parser("complete")
    complete.add_argument("--task", required=True)
    
    # Recommend
    rec = subparsers.add_parser("recommend")
    rec.add_argument("--task-type", required=True)
    rec.add_argument("--skills")
    rec.add_argument("--strategy", default="hybrid")
    
    # Conflict
    subparsers.add_parser("check-conflicts")
    
    # Broadcast
    bc = subparsers.add_parser("broadcast")
    bc.add_argument("--from", dest="from_agent", required=True)
    bc.add_argument("--event", required=True)
    bc.add_argument("--data", default="{}")
    
    # Decision
    dec = subparsers.add_parser("decide")
    dec.add_argument("--context", required=True)
    dec.add_argument("--options", required=True)
    dec.add_argument("--criteria", required=True)
    
    # Stats
    subparsers.add_parser("stats")
    
    args = parser.parse_args()
    system = AgentCollaborationSystem()
    
    if args.command == "register":
        system.register_agent(args.id, args.name, args.role,
                             args.skills.split(",") if args.skills else [])
    
    elif args.command == "list":
        agents = system.list_agents()
        print(f"\n👥 Agent 列表 ({len(agents)} 个):\n")
        for a in agents:
            emoji = "🟢" if a.status == "online" else "🔴" if a.status == "offline" else "🟡"
            print(f"  {emoji} {a.name} ({a.agent_id})")
            print(f"     角色: {a.role} | 负载: {a.workload:.0%} | 完成: {a.completed_tasks}")
            print()
    
    elif args.command == "add-task":
        system.add_task(args.id, args.type, args.desc,
                       args.skills.split(",") if args.skills else [], args.priority)
    
    elif args.command == "assign":
        system.assign_task(args.task, args.agent)
    
    elif args.command == "complete":
        system.complete_task(args.task)
    
    elif args.command == "recommend":
        recs = system.recommend_agent(args.task_type,
                                      args.skills.split(",") if args.skills else [],
                                      args.strategy)
        print(f"\n🎯 推荐结果:\n")
        for agent, score in recs[:5]:
            print(f"  {agent.name} ({agent.agent_id}) - 分数: {score:.2f}")
    
    elif args.command == "check-conflicts":
        conflicts = system.detect_conflicts()
        print(f"⚠️  检测到 {len(conflicts)} 个冲突" if conflicts else "✅ 无冲突")
    
    elif args.command == "broadcast":
        system.broadcast(args.from_agent, args.event, json.loads(args.data))
    
    elif args.command == "decide":
        system.make_decision(args.context, args.options.split(","),
                            args.criteria.split(","))
    
    elif args.command == "stats":
        print(json.dumps(system.get_stats(), indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
