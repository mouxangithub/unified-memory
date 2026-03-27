#!/usr/bin/env python3
"""
Agent Scheduler - Agent 调度器

功能:
- 任务分配 (根据能力匹配)
- 负载均衡 (避免某个 Agent 过载)
- 优先级调度 (紧急任务优先)
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random

sys.path.insert(0, str(Path(__file__).parent.parent))


class TaskPriority(str, Enum):
    CRITICAL = "critical"  # 紧急
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskType(str, Enum):
    CODE = "code"
    DESIGN = "design"
    DOCUMENT = "document"
    TEST = "test"
    RESEARCH = "research"
    DEPLOY = "deploy"
    REVIEW = "review"
    COMMUNICATE = "communicate"


@dataclass
class Agent:
    id: str
    name: str
    role: str
    capabilities: List[str]
    current_load: int = 0  # 当前任务数
    max_load: int = 3  # 最大并行任务
    performance_score: float = 0.8  # 历史表现分数


@dataclass
class Task:
    id: str
    type: TaskType
    priority: TaskPriority
    required_capabilities: List[str]
    estimated_time: int  # 分钟
    description: str
    assigned_to: Optional[str] = None
    status: str = "pending"


class AgentScheduler:
    """Agent 调度器"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.assignment_history: List[Dict] = []
        
        # 能力到任务类型映射
        self.capability_mapping = {
            "python": ["code", "test"],
            "javascript": ["code", "test"],
            "architecture": ["design", "code"],
            "documentation": ["document"],
            "testing": ["test", "review"],
            "deployment": ["deploy"],
            "research": ["research"],
            "communication": ["communicate", "document"],
            "review": ["review"]
        }
    
    def register_agent(self, agent: Agent):
        """注册 Agent"""
        self.agents[agent.id] = agent
    
    def submit_task(self, task: Task):
        """提交任务"""
        self.tasks[task.id] = task
    
    def schedule(self) -> Dict[str, str]:
        """智能调度"""
        assignments = {}
        
        # 按优先级排序任务
        pending_tasks = [t for t in self.tasks.values() if t.status == "pending"]
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        pending_tasks.sort(key=lambda t: priority_order[t.priority])
        
        for task in pending_tasks:
            # 找最佳 Agent
            best_agent = self._find_best_agent(task)
            
            if best_agent:
                # 分配任务
                task.assigned_to = best_agent.id
                task.status = "assigned"
                best_agent.current_load += 1
                
                assignments[task.id] = best_agent.id
                
                # 记录历史
                self.assignment_history.append({
                    "task_id": task.id,
                    "agent_id": best_agent.id,
                    "timestamp": datetime.now().isoformat()
                })
        
        return assignments
    
    def _find_best_agent(self, task: Task) -> Optional[Agent]:
        """找最佳 Agent"""
        candidates = []
        
        for agent in self.agents.values():
            # 检查能力匹配
            capability_match = self._check_capability_match(
                agent.capabilities,
                task.required_capabilities
            )
            
            if capability_match > 0:
                # 检查负载
                if agent.current_load >= agent.max_load:
                    continue
                
                # 计算分数
                score = self._calculate_score(agent, task, capability_match)
                candidates.append((agent, score))
        
        if not candidates:
            return None
        
        # 返回最高分
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def _check_capability_match(self, agent_caps: List[str], required: List[str]) -> float:
        """检查能力匹配度"""
        if not required:
            return 0.5  # 没有要求，默认中等匹配
        
        # 将 Agent 能力转换为任务类型
        agent_task_types = set()
        for cap in agent_caps:
            types = self.capability_mapping.get(cap.lower(), [])
            agent_task_types.update(types)
        
        # 计算匹配度
        required_set = set(required)
        matched = required_set & agent_task_types
        
        return len(matched) / len(required_set) if required_set else 0
    
    def _calculate_score(self, agent: Agent, task: Task, capability_match: float) -> float:
        """计算 Agent 适合度分数"""
        # 负载因子 (负载越低越好)
        load_factor = 1 - (agent.current_load / agent.max_load)
        
        # 表现因子
        performance_factor = agent.performance_score
        
        # 能力匹配因子
        capability_factor = capability_match
        
        # 综合分数 (加权)
        score = (
            load_factor * 0.3 +
            performance_factor * 0.3 +
            capability_factor * 0.4
        )
        
        return score
    
    def get_agent_workload(self) -> Dict[str, Dict]:
        """获取各 Agent 负载"""
        return {
            agent.id: {
                "name": agent.name,
                "current_load": agent.current_load,
                "max_load": agent.max_load,
                "utilization": agent.current_load / agent.max_load
            }
            for agent in self.agents.values()
        }
    
    def complete_task(self, task_id: str, agent_id: str, success: bool = True):
        """完成任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = "completed" if success else "failed"
            
            # 减少 Agent 负载
            if agent_id in self.agents:
                self.agents[agent_id].current_load = max(
                    0,
                    self.agents[agent_id].current_load - 1
                )
                
                # 更新表现分数
                if success:
                    self.agents[agent_id].performance_score = min(
                        1.0,
                        self.agents[agent_id].performance_score + 0.05
                    )
                else:
                    self.agents[agent_id].performance_score = max(
                        0.1,
                        self.agents[agent_id].performance_score - 0.1
                    )


# CLI 入口
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 调度器")
    parser.add_argument("--demo", action="store_true", help="演示调度")
    
    args = parser.parse_args()
    
    scheduler = AgentScheduler()
    
    # 注册 Agent
    scheduler.register_agent(Agent(
        id="pm",
        name="产品经理",
        role="pm",
        capabilities=["communication", "documentation", "research"]
    ))
    
    scheduler.register_agent(Agent(
        id="architect",
        name="架构师",
        role="architect",
        capabilities=["architecture", "python", "javascript"]
    ))
    
    scheduler.register_agent(Agent(
        id="engineer",
        name="工程师",
        role="engineer",
        capabilities=["python", "javascript", "testing"]
    ))
    
    scheduler.register_agent(Agent(
        id="qa",
        name="测试工程师",
        role="qa",
        capabilities=["testing", "review"]
    ))
    
    if args.demo:
        # 提交任务
        scheduler.submit_task(Task(
            id="t1",
            type=TaskType.CODE,
            priority=TaskPriority.HIGH,
            required_capabilities=["python"],
            estimated_time=60,
            description="开发用户登录功能"
        ))
        
        scheduler.submit_task(Task(
            id="t2",
            type=TaskType.TEST,
            priority=TaskPriority.MEDIUM,
            required_capabilities=["testing"],
            estimated_time=30,
            description="编写登录功能测试用例"
        ))
        
        scheduler.submit_task(Task(
            id="t3",
            type=TaskType.DOCUMENT,
            priority=TaskPriority.LOW,
            required_capabilities=["documentation"],
            estimated_time=20,
            description="编写 API 文档"
        ))
        
        # 调度
        print("🤖 Agent 调度演示\n")
        print("已注册 Agent:")
        for agent in scheduler.agents.values():
            print(f"  - {agent.name}: {agent.capabilities}")
        
        print("\n提交任务:")
        for task in scheduler.tasks.values():
            print(f"  - {task.description} ({task.priority})")
        
        print("\n调度结果:")
        assignments = scheduler.schedule()
        for task_id, agent_id in assignments.items():
            task = scheduler.tasks[task_id]
            agent = scheduler.agents[agent_id]
            print(f"  ✅ {task.description} → {agent.name}")
        
        print("\n负载情况:")
        for agent_id, info in scheduler.get_agent_workload().items():
            print(f"  {info['name']}: {info['current_load']}/{info['max_load']} ({info['utilization']:.0%})")
    
    else:
        print("使用 --demo 查看调度演示")


if __name__ == "__main__":
    main()
