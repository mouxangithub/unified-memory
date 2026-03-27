#!/usr/bin/env python3
"""
Task Queue - 智能任务分配系统 v1.0

功能:
- 智能任务分配 (技能匹配/负载均衡/轮询/主动认领/专家优先)
- 任务状态追踪与移交
- 与 Agent Profile 和 Collab Bus 集成
- 任务优先级管理

Usage:
    # 添加任务
    python3 scripts/task_queue.py add "标题" --desc "描述" --skills "python,coding" --priority 7

    # 分配任务
    python3 scripts/task_queue.py assign <id> --strategy skill_match

    # 开始任务
    python3 scripts/task_queue.py start <id> --agent xiao-zhi

    # 完成任务
    python3 scripts/task_queue.py complete <id> --result '{"status":"success"}'

    # 任务移交
    python3 scripts/task_queue.py handoff <id> --from xiao-zhi --to xiao-liu --reason "需要飞书操作"

    # 查看任务
    python3 scripts/task_queue.py list --agent xiao-zhi

    # 统计
    python3 scripts/task_queue.py stats
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import uuid


# ============================================================================
# 枚举和数据类
# ============================================================================

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AssignmentStrategy(Enum):
    SKILL_MATCH = "skill_match"      # 技能匹配
    LOAD_BALANCE = "load_balance"    # 负载均衡
    ROUND_ROBIN = "round_robin"      # 轮询
    VOLUNTEER = "volunteer"          # 主动认领
    EXPERT_FIRST = "expert_first"    # 专家优先


@dataclass
class Task:
    task_id: str
    title: str
    description: str
    required_skills: List[str]
    priority: int = 5  # 1-10
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None  # agent_id
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    handoff_history: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['status'] = self.status.value
        d['created_at'] = self.created_at.isoformat() if self.created_at else None
        d['started_at'] = self.started_at.isoformat() if self.started_at else None
        d['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return d
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'Task':
        d['status'] = TaskStatus(d['status'])
        d['created_at'] = datetime.fromisoformat(d['created_at']) if d.get('created_at') else datetime.now()
        d['started_at'] = datetime.fromisoformat(d['started_at']) if d.get('started_at') else None
        d['completed_at'] = datetime.fromisoformat(d['completed_at']) if d.get('completed_at') else None
        return cls(**d)


# ============================================================================
# Agent Profile (简化版，用于独立运行)
# ============================================================================

class AgentProfile:
    """Agent 能力画像"""
    
    def __init__(self, agent_id: str, name: str = None):
        self.agent_id = agent_id
        self.name = name or agent_id
        self.skills: Dict[str, float] = {}  # skill -> score (0-1)
        self.workload: float = 0.0  # 当前任务数
        self.expertise: List[str] = []  # 专家领域
        self.preferences: Dict = {}
        self.trust_scores: Dict[str, float] = {}
        self.task_history: List[str] = []  # 完成的任务ID
        self.success_rate: float = 1.0
    
    def add_skill(self, skill: str, score: float):
        self.skills[skill.lower()] = min(1.0, max(0.0, score))
    
    def has_skill(self, skill: str) -> bool:
        return skill.lower() in self.skills
    
    def get_skill_score(self, skill: str) -> float:
        return self.skills.get(skill.lower(), 0.0)
    
    def to_dict(self) -> Dict:
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'skills': self.skills,
            'workload': self.workload,
            'expertise': self.expertise,
            'preferences': self.preferences,
            'trust_scores': self.trust_scores,
            'task_history': self.task_history[-20:],  # 最近20个
            'success_rate': self.success_rate
        }
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'AgentProfile':
        profile = cls(d['agent_id'], d.get('name'))
        profile.skills = d.get('skills', {})
        profile.workload = d.get('workload', 0.0)
        profile.expertise = d.get('expertise', [])
        profile.preferences = d.get('preferences', {})
        profile.trust_scores = d.get('trust_scores', {})
        profile.task_history = d.get('task_history', [])
        profile.success_rate = d.get('success_rate', 1.0)
        return profile


class AgentProfileManager:
    """Agent 画像管理器"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.profiles: Dict[str, AgentProfile] = {}
        self._load()
    
    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for agent_id, profile_data in data.get('profiles', {}).items():
                        self.profiles[agent_id] = AgentProfile.from_dict(profile_data)
            except:
                pass
        
        # 默认 Agents
        if 'xiao-zhi' not in self.profiles:
            self.profiles['xiao-zhi'] = AgentProfile('xiao-zhi', '小智')
            self.profiles['xiao-zhi'].add_skill('coding', 0.9)
            self.profiles['xiao-zhi'].add_skill('python', 0.9)
            self.profiles['xiao-zhi'].add_skill('planning', 0.85)
            self.profiles['xiao-zhi'].add_skill('documentation', 0.8)
        
        if 'xiao-liu' not in self.profiles:
            self.profiles['xiao-liu'] = AgentProfile('xiao-liu', '小六')
            self.profiles['xiao-liu'].add_skill('feishu', 0.95)
            self.profiles['xiao-liu'].add_skill('communication', 0.9)
            self.profiles['xiao-liu'].add_skill('coordination', 0.85)
    
    def _save(self):
        data = {
            'profiles': {aid: p.to_dict() for aid, p in self.profiles.items()}
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_profile(self, agent_id: str) -> Optional[AgentProfile]:
        return self.profiles.get(agent_id)
    
    def get_all_agents(self) -> List[AgentProfile]:
        return list(self.profiles.values())
    
    def update_workload(self, agent_id: str, delta: int):
        if agent_id in self.profiles:
            self.profiles[agent_id].workload = max(0, self.profiles[agent_id].workload + delta)
            self._save()
    
    def record_task_completion(self, agent_id: str, task_id: str, success: bool):
        if agent_id in self.profiles:
            profile = self.profiles[agent_id]
            profile.task_history.append(task_id)
            # 更新成功率
            total = len(profile.task_history)
            successful = sum(1 for t in profile.task_history if t.endswith('_success'))
            profile.success_rate = successful / total if total > 0 else 1.0
            self._save()


# ============================================================================
# Collaboration Bus (简化版，用于独立运行)
# ============================================================================

class CollabBus:
    """协作总线 - 用于Agent间通信"""
    
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.subscribers: Dict[str, Set[str]] = {}  # topic -> agent_ids
        self._ensure_log()
    
    def _ensure_log(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.touch()
    
    def publish(self, event_type: str, data: Dict, from_agent: str = "system"):
        """发布事件"""
        event = {
            'id': hashlib.md5(f"{datetime.now().isoformat()}{event_type}".encode()).hexdigest()[:12],
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'from': from_agent,
            'data': data
        }
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        return event['id']
    
    def notify_task_assigned(self, task_id: str, agent_id: str, assigned_by: str = "system"):
        """通知任务分配"""
        return self.publish('task_assigned', {
            'task_id': task_id,
            'agent_id': agent_id,
            'assigned_by': assigned_by
        }, from_agent=assigned_by)
    
    def notify_task_handoff(self, task_id: str, from_agent: str, to_agent: str, reason: str):
        """通知任务移交"""
        return self.publish('task_handoff', {
            'task_id': task_id,
            'from_agent': from_agent,
            'to_agent': to_agent,
            'reason': reason
        }, from_agent=from_agent)
    
    def notify_task_completed(self, task_id: str, agent_id: str, result: Dict):
        """通知任务完成"""
        return self.publish('task_completed', {
            'task_id': task_id,
            'agent_id': agent_id,
            'result': result
        }, from_agent=agent_id)
    
    def get_recent_events(self, limit: int = 20) -> List[Dict]:
        """获取最近事件"""
        events = []
        with open(self.log_path, 'r') as f:
            for line in f:
                try:
                    events.append(json.loads(line.strip()))
                except:
                    continue
        return events[-limit:]


# ============================================================================
# 分配引擎
# ============================================================================

class AssignmentEngine:
    """智能任务分配引擎"""
    
    def __init__(self, agent_profiles: AgentProfileManager):
        self.agent_profiles = agent_profiles
        self.round_robin_index = 0
    
    def find_best_agent(self, task: Task, strategy: AssignmentStrategy) -> Optional[str]:
        """找最佳 Agent"""
        agents = self.agent_profiles.get_all_agents()
        if not agents:
            return None
        
        if strategy == AssignmentStrategy.SKILL_MATCH:
            return self._skill_match(task, agents)
        elif strategy == AssignmentStrategy.LOAD_BALANCE:
            return self._load_balance(task, agents)
        elif strategy == AssignmentStrategy.ROUND_ROBIN:
            return self._round_robin(task, agents)
        elif strategy == AssignmentStrategy.EXPERT_FIRST:
            return self._expert_first(task, agents)
        else:
            return agents[0].agent_id
    
    def _skill_match(self, task: Task, agents: List[AgentProfile]) -> Optional[str]:
        """技能匹配 - 选择技能最匹配的 Agent"""
        best_agent = None
        best_score = -1
        
        for agent in agents:
            score = self.calculate_skill_match_score(task, agent.agent_id)
            # 考虑负载
            score -= agent.workload * 0.1
            if score > best_score:
                best_score = score
                best_agent = agent.agent_id
        
        return best_agent
    
    def _load_balance(self, task: Task, agents: List[AgentProfile]) -> Optional[str]:
        """负载均衡 - 选择最空闲的 Agent"""
        best_agent = None
        min_workload = float('inf')
        
        for agent in agents:
            # 至少要有一些技能匹配
            if task.required_skills:
                skill_score = self.calculate_skill_match_score(task, agent.agent_id)
                if skill_score < 0.3:
                    continue
            
            score = self.get_load_balance_score(agent.agent_id)
            if score < min_workload:
                min_workload = score
                best_agent = agent.agent_id
        
        return best_agent
    
    def _round_robin(self, task: Task, agents: List[AgentProfile]) -> Optional[str]:
        """轮询分配"""
        if not agents:
            return None
        
        # 跳过没有相关技能的 Agent
        attempts = 0
        while attempts < len(agents):
            agent = agents[self.round_robin_index % len(agents)]
            self.round_robin_index += 1
            
            if task.required_skills:
                skill_score = self.calculate_skill_match_score(task, agent.agent_id)
                if skill_score >= 0.3:
                    return agent.agent_id
            else:
                return agent.agent_id
            
            attempts += 1
        
        return agents[0].agent_id
    
    def _expert_first(self, task: Task, agents: List[AgentProfile]) -> Optional[str]:
        """专家优先 - 选择专家领域匹配且成功率最高的 Agent"""
        best_agent = None
        best_score = -1
        
        for agent in agents:
            # 检查专家领域
            expertise_match = any(
                skill.lower() in [e.lower() for e in agent.expertise]
                for skill in task.required_skills
            )
            
            # 计算综合分数
            skill_score = self.calculate_skill_match_score(task, agent.agent_id)
            success_score = agent.success_rate
            
            # 专家加成
            if expertise_match:
                skill_score *= 1.5
            
            score = skill_score * 0.6 + success_score * 0.4 - agent.workload * 0.1
            
            if score > best_score:
                best_score = score
                best_agent = agent.agent_id
        
        return best_agent
    
    def calculate_skill_match_score(self, task: Task, agent_id: str) -> float:
        """计算技能匹配分数"""
        profile = self.agent_profiles.get_profile(agent_id)
        if not profile:
            return 0.0
        
        if not task.required_skills:
            return 1.0
        
        scores = []
        for skill in task.required_skills:
            score = profile.get_skill_score(skill)
            scores.append(score)
        
        # 返回平均分数
        return sum(scores) / len(scores) if scores else 0.0
    
    def get_load_balance_score(self, agent_id: str) -> float:
        """获取负载均衡分数 (越低越空闲)"""
        profile = self.agent_profiles.get_profile(agent_id)
        if not profile:
            return float('inf')
        return profile.workload


# ============================================================================
# 任务队列
# ============================================================================

class TaskQueue:
    """智能任务队列"""
    
    def __init__(self, storage_path: Path, agent_profiles: AgentProfileManager, collab_bus: CollabBus):
        self.storage_path = storage_path
        self.history_path = storage_path.parent / "history.jsonl"
        self.agent_profiles = agent_profiles
        self.collab_bus = collab_bus
        self.assignment_engine = AssignmentEngine(agent_profiles)
        
        self.tasks: Dict[str, Task] = {}
        self._load()
    
    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for task_id, task_data in data.get('tasks', {}).items():
                        self.tasks[task_id] = Task.from_dict(task_data)
            except:
                pass
    
    def _save(self):
        data = {
            'tasks': {tid: task.to_dict() for tid, task in self.tasks.items()}
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _append_history(self, task: Task):
        """添加到历史记录"""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, 'a') as f:
            f.write(json.dumps(task.to_dict(), ensure_ascii=False) + '\n')
    
    def add_task(self, task: Task) -> str:
        """添加任务"""
        if not task.task_id:
            task.task_id = hashlib.md5(
                f"{datetime.now().isoformat()}{task.title}".encode()
            ).hexdigest()[:12]
        
        self.tasks[task.task_id] = task
        self._save()
        
        print(f"✅ 创建任务: [{task.task_id}] {task.title}")
        print(f"   技能要求: {', '.join(task.required_skills) or '无'}")
        print(f"   优先级: {task.priority}/10")
        
        return task.task_id
    
    def assign(self, task_id: str, strategy: AssignmentStrategy = AssignmentStrategy.SKILL_MATCH) -> Optional[str]:
        """智能分配任务，返回分配的 agent_id"""
        task = self.tasks.get(task_id)
        if not task:
            print(f"❌ 任务不存在: {task_id}")
            return None
        
        if task.status != TaskStatus.PENDING:
            print(f"❌ 任务状态不允许分配: {task.status.value}")
            return None
        
        agent_id = self.assignment_engine.find_best_agent(task, strategy)
        if not agent_id:
            print(f"❌ 没有可用的 Agent")
            return None
        
        task.assigned_to = agent_id
        task.status = TaskStatus.ASSIGNED
        
        # 更新 Agent 负载
        self.agent_profiles.update_workload(agent_id, 1)
        
        self._save()
        
        # 发送通知
        self.collab_bus.notify_task_assigned(task_id, agent_id)
        
        print(f"✅ 任务已分配: [{task_id}] → {agent_id}")
        print(f"   分配策略: {strategy.value}")
        
        return agent_id
    
    def get_agent_tasks(self, agent_id: str, status: Optional[TaskStatus] = None) -> List[Task]:
        """获取 Agent 的任务"""
        result = []
        for task in self.tasks.values():
            if task.assigned_to == agent_id:
                if status is None or task.status == status:
                    result.append(task)
        
        # 按优先级排序
        result.sort(key=lambda t: -t.priority)
        return result
    
    def start_task(self, task_id: str, agent_id: str):
        """开始任务"""
        task = self.tasks.get(task_id)
        if not task:
            print(f"❌ 任务不存在: {task_id}")
            return False
        
        if task.assigned_to != agent_id:
            print(f"❌ 任务未分配给 {agent_id}")
            return False
        
        if task.status != TaskStatus.ASSIGNED:
            print(f"❌ 任务状态不允许开始: {task.status.value}")
            return False
        
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        
        self._save()
        
        print(f"🚀 任务开始: [{task_id}] by {agent_id}")
        return True
    
    def complete_task(self, task_id: str, agent_id: str, result: Dict):
        """完成任务"""
        task = self.tasks.get(task_id)
        if not task:
            print(f"❌ 任务不存在: {task_id}")
            return False
        
        if task.assigned_to != agent_id:
            print(f"❌ 任务未分配给 {agent_id}")
            return False
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.result = result
        
        # 更新 Agent 负载
        self.agent_profiles.update_workload(agent_id, -1)
        self.agent_profiles.record_task_completion(agent_id, task_id + "_success", True)
        
        # 移动到历史
        self._append_history(task)
        del self.tasks[task_id]
        
        self._save()
        
        # 发送通知
        self.collab_bus.notify_task_completed(task_id, agent_id, result)
        
        print(f"✅ 任务完成: [{task_id}] by {agent_id}")
        return True
    
    def fail_task(self, task_id: str, agent_id: str, error: str):
        """任务失败"""
        task = self.tasks.get(task_id)
        if not task:
            print(f"❌ 任务不存在: {task_id}")
            return False
        
        if task.assigned_to != agent_id:
            print(f"❌ 任务未分配给 {agent_id}")
            return False
        
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now()
        task.result = {"error": error}
        
        # 更新 Agent 负载
        self.agent_profiles.update_workload(agent_id, -1)
        self.agent_profiles.record_task_completion(agent_id, task_id + "_failed", False)
        
        # 移动到历史
        self._append_history(task)
        del self.tasks[task_id]
        
        self._save()
        
        print(f"❌ 任务失败: [{task_id}] by {agent_id}")
        print(f"   错误: {error}")
        return True
    
    def handoff(self, task_id: str, from_agent: str, to_agent: str, reason: str):
        """任务移交"""
        task = self.tasks.get(task_id)
        if not task:
            print(f"❌ 任务不存在: {task_id}")
            return False
        
        if task.assigned_to != from_agent:
            print(f"❌ 任务未分配给 {from_agent}")
            return False
        
        # 记录移交历史
        task.handoff_history.append({
            'from': from_agent,
            'to': to_agent,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        
        # 更新分配
        task.assigned_to = to_agent
        
        # 更新负载
        self.agent_profiles.update_workload(from_agent, -1)
        self.agent_profiles.update_workload(to_agent, 1)
        
        self._save()
        
        # 发送通知
        self.collab_bus.notify_task_handoff(task_id, from_agent, to_agent, reason)
        
        print(f"🔄 任务移交: [{task_id}] {from_agent} → {to_agent}")
        print(f"   原因: {reason}")
        return True
    
    def get_pending_tasks(self) -> List[Task]:
        """获取待分配任务"""
        result = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING
        ]
        # 按优先级排序
        result.sort(key=lambda t: -t.priority)
        return result
    
    def get_task_stats(self) -> Dict:
        """获取任务统计"""
        stats = {
            'total': len(self.tasks),
            'by_status': {},
            'by_agent': {},
            'by_priority': {},
            'pending_count': 0,
            'in_progress_count': 0
        }
        
        for status in TaskStatus:
            stats['by_status'][status.value] = 0
        
        for task in self.tasks.values():
            stats['by_status'][task.status.value] += 1
            
            # 按优先级
            p = task.priority
            stats['by_priority'][p] = stats['by_priority'].get(p, 0) + 1
            
            # 按 Agent
            if task.assigned_to:
                agent = task.assigned_to
                if agent not in stats['by_agent']:
                    stats['by_agent'][agent] = 0
                stats['by_agent'][agent] += 1
        
        stats['pending_count'] = stats['by_status']['pending']
        stats['in_progress_count'] = stats['by_status']['in_progress'] + stats['by_status']['assigned']
        
        return stats
    
    def volunteer(self, task_id: str, agent_id: str) -> bool:
        """主动认领任务"""
        task = self.tasks.get(task_id)
        if not task:
            print(f"❌ 任务不存在: {task_id}")
            return False
        
        if task.status != TaskStatus.PENDING:
            print(f"❌ 任务已被分配或处理")
            return False
        
        # 检查技能是否匹配
        if task.required_skills:
            profile = self.agent_profiles.get_profile(agent_id)
            if profile:
                skill_score = self.assignment_engine.calculate_skill_match_score(task, agent_id)
                if skill_score < 0.3:
                    print(f"⚠️ 技能匹配度较低: {skill_score:.2f}")
        
        task.assigned_to = agent_id
        task.status = TaskStatus.ASSIGNED
        
        # 更新负载
        self.agent_profiles.update_workload(agent_id, 1)
        
        self._save()
        
        # 发送通知
        self.collab_bus.notify_task_assigned(task_id, agent_id, assigned_by=agent_id)
        
        print(f"🙋 任务已认领: [{task_id}] by {agent_id}")
        return True


# ============================================================================
# CLI 接口
# ============================================================================

def main():
    # 配置路径
    workspace = Path.home() / ".openclaw" / "workspace"
    memory_dir = workspace / "memory"
    tasks_dir = memory_dir / "tasks"
    
    queue_path = tasks_dir / "queue.json"
    profiles_path = tasks_dir / "agent_profiles.json"
    bus_log = tasks_dir / "collab_bus.jsonl"
    
    # 初始化组件
    tasks_dir.mkdir(parents=True, exist_ok=True)
    agent_profiles = AgentProfileManager(profiles_path)
    collab_bus = CollabBus(bus_log)
    task_queue = TaskQueue(queue_path, agent_profiles, collab_bus)
    
    parser = argparse.ArgumentParser(description="Task Queue - 智能任务分配系统 v1.0")
    parser.add_argument("command", choices=[
        "add", "assign", "start", "complete", "fail", "handoff",
        "volunteer", "list", "get", "stats", "agents"
    ])
    
    # 通用参数
    parser.add_argument("--id", "-i", help="任务ID")
    parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    
    # add 参数
    parser.add_argument("--title", "-t", help="任务标题")
    parser.add_argument("--desc", "-d", help="任务描述")
    parser.add_argument("--skills", "-s", help="所需技能 (逗号分隔)")
    parser.add_argument("--priority", "-p", type=int, default=5, help="优先级 1-10")
    parser.add_argument("--creator", "-c", help="创建者")
    
    # assign 参数
    parser.add_argument("--strategy", choices=[s.value for s in AssignmentStrategy],
                        default="skill_match", help="分配策略")
    
    # start/complete/fail 参数
    parser.add_argument("--agent", "-a", help="Agent ID")
    parser.add_argument("--result", "-r", help="结果 (JSON)")
    
    # handoff 参数
    parser.add_argument("--from", dest="from_agent", help="来源 Agent")
    parser.add_argument("--to", dest="to_agent", help="目标 Agent")
    parser.add_argument("--reason", help="移交原因")
    
    # list 参数
    parser.add_argument("--status", help="过滤状态")
    parser.add_argument("--limit", "-l", type=int, default=20, help="限制数量")
    
    args = parser.parse_args()
    
    if args.command == "add":
        if not args.title:
            print("❌ 缺少参数: --title")
            return
        
        skills = [s.strip() for s in (args.skills or "").split(",") if s.strip()]
        
        task = Task(
            task_id="",
            title=args.title,
            description=args.desc or "",
            required_skills=skills,
            priority=args.priority,
            created_by=args.creator or "cli"
        )
        
        task_id = task_queue.add_task(task)
        
        if args.json:
            print(json.dumps({"task_id": task_id, "task": task.to_dict()}, ensure_ascii=False, indent=2))
    
    elif args.command == "assign":
        task_id = args.id
        
        # 如果没有指定任务ID，自动分配优先级最高的待分配任务
        if not task_id:
            pending = task_queue.get_pending_tasks()
            if pending:
                task_id = pending[0].task_id
                print(f"📋 自动选择最高优先级任务: {task_id}")
            else:
                print("❌ 没有待分配的任务")
                return
        
        strategy = AssignmentStrategy(args.strategy)
        agent_id = task_queue.assign(task_id, strategy)
        
        if args.json:
            print(json.dumps({"task_id": task_id, "assigned_to": agent_id, "strategy": args.strategy}, ensure_ascii=False))
    
    elif args.command == "start":
        if not all([args.id, args.agent]):
            print("❌ 缺少参数: --id, --agent")
            return
        task_queue.start_task(args.id, args.agent)
    
    elif args.command == "complete":
        if not all([args.id, args.agent]):
            print("❌ 缺少参数: --id, --agent")
            return
        result = json.loads(args.result) if args.result else {}
        task_queue.complete_task(args.id, args.agent, result)
    
    elif args.command == "fail":
        if not all([args.id, args.agent]):
            print("❌ 缺少参数: --id, --agent")
            return
        task_queue.fail_task(args.id, args.agent, args.reason or "Unknown error")
    
    elif args.command == "handoff":
        if not all([args.id, args.from_agent, args.to_agent]):
            print("❌ 缺少参数: --id, --from, --to")
            return
        task_queue.handoff(args.id, args.from_agent, args.to_agent, args.reason or "")
    
    elif args.command == "volunteer":
        if not all([args.id, args.agent]):
            print("❌ 缺少参数: --id, --agent")
            return
        task_queue.volunteer(args.id, args.agent)
    
    elif args.command == "list":
        if args.agent:
            status = TaskStatus(args.status) if args.status else None
            tasks = task_queue.get_agent_tasks(args.agent, status)
        elif args.status:
            status = TaskStatus(args.status)
            tasks = [t for t in task_queue.tasks.values() if t.status == status]
        else:
            tasks = list(task_queue.tasks.values())
        
        # 按优先级排序
        tasks.sort(key=lambda t: -t.priority)
        tasks = tasks[:args.limit]
        
        if args.json:
            print(json.dumps([t.to_dict() for t in tasks], ensure_ascii=False, indent=2))
        else:
            status_emoji = {
                "pending": "⏳", "assigned": "📋", "in_progress": "🔄",
                "completed": "✅", "failed": "❌", "cancelled": "🚫"
            }
            print(f"📋 任务列表 (共 {len(tasks)} 条)")
            for task in tasks:
                emoji = status_emoji.get(task.status.value, "❓")
                print(f"  {emoji} [{task.task_id}] {task.title}")
                print(f"      状态: {task.status.value} | 优先级: {task.priority} | 分配给: {task.assigned_to or '未分配'}")
    
    elif args.command == "get":
        if not args.id:
            print("❌ 缺少参数: --id")
            return
        task = task_queue.tasks.get(args.id)
        if task:
            if args.json:
                print(json.dumps(task.to_dict(), ensure_ascii=False, indent=2))
            else:
                print(f"📋 任务详情: [{task.task_id}]")
                print(f"   标题: {task.title}")
                print(f"   描述: {task.description}")
                print(f"   状态: {task.status.value}")
                print(f"   优先级: {task.priority}/10")
                print(f"   技能要求: {', '.join(task.required_skills) or '无'}")
                print(f"   分配给: {task.assigned_to or '未分配'}")
                print(f"   创建者: {task.created_by}")
                print(f"   创建时间: {task.created_at}")
                if task.handoff_history:
                    print(f"   移交历史: {len(task.handoff_history)} 次")
        else:
            print(f"❌ 任务不存在: {args.id}")
    
    elif args.command == "stats":
        stats = task_queue.get_task_stats()
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print("📊 任务统计")
            print(f"   总计: {stats['total']}")
            print(f"   待分配: {stats['pending_count']}")
            print(f"   进行中: {stats['in_progress_count']}")
            print(f"   按状态: {stats['by_status']}")
            print(f"   按Agent: {stats['by_agent']}")
    
    elif args.command == "agents":
        agents = agent_profiles.get_all_agents()
        if args.json:
            print(json.dumps([a.to_dict() for a in agents], ensure_ascii=False, indent=2))
        else:
            print("👥 Agent 列表")
            for agent in agents:
                skills = ", ".join([f"{k}:{v:.1f}" for k, v in list(agent.skills.items())[:5]])
                print(f"  • {agent.agent_id} ({agent.name})")
                print(f"    技能: {skills}")
                print(f"    负载: {agent.workload} | 成功率: {agent.success_rate:.0%}")


if __name__ == "__main__":
    main()
