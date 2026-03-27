#!/usr/bin/env python3
"""
Workflow Engine - SOP/DAG 混合工作流引擎

整合 MetaGPT 的工作流设计，支持：
- SOP（顺序执行）
- DAG（并行执行）
- 混合模式

使用：
    from workflow_engine import Workflow, WorkflowEngine
    
    # 创建工作流
    workflow = Workflow("software-dev", type="hybrid")
    workflow.add_step("pm", "analyze", output_key="requirements")
    workflow.add_step("architect", "design", depends_on=["pm"], output_key="design")
    workflow.add_step("frontend", "code", depends_on=["architect"])
    workflow.add_step("backend", "code", depends_on=["architect"])
    workflow.add_step("qa", "test", depends_on=["frontend", "backend"])
    
    # 执行
    engine = WorkflowEngine(agents)
    result = engine.run(workflow, initial_context)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowType(Enum):
    SOP = "sop"           # 顺序执行
    DAG = "dag"           # 并行执行
    HYBRID = "hybrid"     # 混合模式


@dataclass
class Step:
    """工作流步骤"""
    id: str
    agent_id: str
    action: str
    depends_on: List[str] = field(default_factory=list)
    output_key: Optional[str] = None
    condition: Optional[str] = None  # 条件执行
    retry: int = 0
    timeout: int = 300
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class Workflow:
    """工作流定义"""
    name: str
    type: WorkflowType = WorkflowType.HYBRID
    steps: Dict[str, Step] = field(default_factory=dict)
    step_order: List[str] = field(default_factory=list)
    
    def add_step(self, 
                 step_id: str,
                 agent_id: str,
                 action: str,
                 depends_on: List[str] = None,
                 output_key: str = None,
                 condition: str = None,
                 retry: int = 0,
                 timeout: int = 300) -> 'Workflow':
        """添加步骤"""
        step = Step(
            id=step_id,
            agent_id=agent_id,
            action=action,
            depends_on=depends_on or [],
            output_key=output_key,
            condition=condition,
            retry=retry,
            timeout=timeout
        )
        self.steps[step_id] = step
        self.step_order.append(step_id)
        return self
    
    def get_dependencies(self, step_id: str) -> List[str]:
        """获取步骤的依赖"""
        return self.steps[step_id].depends_on
    
    def get_dependents(self, step_id: str) -> List[str]:
        """获取依赖此步骤的步骤"""
        return [s.id for s in self.steps.values() if step_id in s.depends_on]
    
    def topological_sort(self) -> List[List[str]]:
        """拓扑排序，返回可并行执行的层级"""
        in_degree = {s: 0 for s in self.steps}
        
        # 计算入度
        for step in self.steps.values():
            for dep in step.depends_on:
                if dep in self.steps:
                    in_degree[step.id] += 1
        
        # 层级排序
        levels = []
        remaining = set(self.steps.keys())
        
        while remaining:
            # 找出当前可执行的步骤（入度为0）
            ready = [s for s in remaining if in_degree[s] == 0]
            
            if not ready:
                # 有环
                raise ValueError(f"工作流存在循环依赖: {remaining}")
            
            levels.append(ready)
            
            # 移除已执行的步骤，更新入度
            for step_id in ready:
                remaining.remove(step_id)
                for dependent in self.get_dependents(step_id):
                    in_degree[dependent] -= 1
        
        return levels
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type.value,
            "steps": {
                id: {
                    "agent_id": s.agent_id,
                    "action": s.action,
                    "depends_on": s.depends_on,
                    "output_key": s.output_key,
                    "condition": s.condition
                }
                for id, s in self.steps.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Workflow':
        """从字典创建"""
        workflow = cls(
            name=data["name"],
            type=WorkflowType(data.get("type", "hybrid"))
        )
        for step_id, step_data in data.get("steps", {}).items():
            workflow.add_step(
                step_id=step_id,
                agent_id=step_data["agent_id"],
                action=step_data["action"],
                depends_on=step_data.get("depends_on", []),
                output_key=step_data.get("output_key"),
                condition=step_data.get("condition")
            )
        return workflow


class Environment:
    """
    环境 - 上下文管理（学习 MetaGPT）
    
    类似 MetaGPT 的 Environment，管理：
    - 全局上下文
    - Agent 间消息传递
    - 共享资源
    """
    
    def __init__(self):
        self.context: Dict[str, Any] = {}
        self.history: List[Dict] = []
        self.artifacts: Dict[str, Any] = {}  # 产物（文档、代码等）
        self._lock = threading.Lock()
    
    def put(self, key: str, value: Any, producer: str = None):
        """存入上下文"""
        with self._lock:
            self.context[key] = value
            self.history.append({
                "action": "put",
                "key": key,
                "producer": producer,
                "timestamp": datetime.now().isoformat()
            })
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文"""
        return self.context.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有上下文"""
        return self.context.copy()
    
    def add_artifact(self, name: str, content: Any, artifact_type: str):
        """添加产物（文档、代码等）"""
        with self._lock:
            self.artifacts[name] = {
                "content": content,
                "type": artifact_type,
                "created_at": datetime.now().isoformat()
            }
    
    def get_artifact(self, name: str) -> Optional[Dict]:
        """获取产物"""
        return self.artifacts.get(name)
    
    def publish(self, topic: str, message: Dict, sender: str):
        """发布消息（Agent 间通信）"""
        with self._lock:
            self.history.append({
                "action": "publish",
                "topic": topic,
                "message": message,
                "sender": sender,
                "timestamp": datetime.now().isoformat()
            })
    
    def to_dict(self) -> dict:
        """导出为字典"""
        return {
            "context": self.context,
            "artifacts": self.artifacts,
            "history": self.history
        }


class WorkflowEngine:
    """
    工作流引擎
    
    执行 SOP/DAG/混合工作流
    """
    
    def __init__(self, agents: Dict[str, Any], max_workers: int = 4):
        """
        Args:
            agents: Agent 字典 {agent_id: agent_instance}
            max_workers: 最大并行数
        """
        self.agents = agents
        self.max_workers = max_workers
        self.env = Environment()
        self.execution_log: List[Dict] = []
    
    def run(self, 
            workflow: Workflow, 
            initial_context: Dict = None,
            on_step_complete: Callable = None) -> Dict:
        """
        执行工作流
        
        Args:
            workflow: 工作流定义
            initial_context: 初始上下文
            on_step_complete: 步骤完成回调
        
        Returns:
            执行结果
        """
        # 初始化环境
        if initial_context:
            for k, v in initial_context.items():
                self.env.put(k, v, "init")
        
        # 获取执行层级
        levels = workflow.topological_sort()
        
        total_steps = len(workflow.steps)
        completed = 0
        failed = 0
        
        print(f"\n🚀 工作流启动: {workflow.name}")
        print(f"📊 总步骤: {total_steps}, 并行层级: {len(levels)}\n")
        
        # 按层级执行
        for level_idx, level in enumerate(levels):
            print(f"📍 层级 {level_idx + 1}: {', '.join(level)}")
            
            if len(level) == 1 or workflow.type == WorkflowType.SOP:
                # 顺序执行
                for step_id in level:
                    result = self._execute_step(workflow.steps[step_id], on_step_complete)
                    if result["status"] == "completed":
                        completed += 1
                    else:
                        failed += 1
                        if workflow.type == WorkflowType.SOP:
                            # SOP 模式下出错即停止
                            break
            else:
                # 并行执行
                with ThreadPoolExecutor(max_workers=min(len(level), self.max_workers)) as executor:
                    futures = {
                        executor.submit(
                            self._execute_step, 
                            workflow.steps[step_id],
                            on_step_complete
                        ): step_id
                        for step_id in level
                    }
                    
                    for future in as_completed(futures):
                        step_id = futures[future]
                        try:
                            result = future.result()
                            if result["status"] == "completed":
                                completed += 1
                            else:
                                failed += 1
                        except Exception as e:
                            print(f"  ❌ {step_id} 执行异常: {e}")
                            failed += 1
        
        # 生成报告
        report = {
            "workflow": workflow.name,
            "status": "completed" if failed == 0 else "partial",
            "total_steps": total_steps,
            "completed": completed,
            "failed": failed,
            "environment": self.env.to_dict(),
            "execution_log": self.execution_log
        }
        
        print(f"\n✅ 工作流完成: {completed}/{total_steps} 成功")
        
        return report
    
    def _execute_step(self, step: Step, callback: Callable = None) -> Dict:
        """执行单个步骤"""
        print(f"  ▶️  {step.id} ({step.agent_id}.{step.action})")
        
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()
        
        try:
            # 获取 Agent
            agent = self.agents.get(step.agent_id)
            if not agent:
                raise ValueError(f"Agent not found: {step.agent_id}")
            
            # 构建执行上下文
            context = self.env.get_all()
            
            # 执行 Agent 动作
            if hasattr(agent, step.action):
                action_func = getattr(agent, step.action)
                result = action_func(context)
            elif callable(agent):
                result = agent(step.action, context)
            else:
                raise ValueError(f"Agent {step.agent_id} 无法执行 {step.action}")
            
            # 存储结果
            if step.output_key:
                self.env.put(step.output_key, result, step.agent_id)
            
            step.result = result
            step.status = StepStatus.COMPLETED
            step.end_time = datetime.now()
            
            # 记录日志
            log_entry = {
                "step_id": step.id,
                "agent_id": step.agent_id,
                "action": step.action,
                "status": "completed",
                "duration": (step.end_time - step.start_time).total_seconds(),
                "output_key": step.output_key
            }
            self.execution_log.append(log_entry)
            
            print(f"  ✅ {step.id} 完成 ({log_entry['duration']:.2f}s)")
            
            # 回调
            if callback:
                callback(step, result)
            
            return {"status": "completed", "result": result}
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.end_time = datetime.now()
            
            log_entry = {
                "step_id": step.id,
                "agent_id": step.agent_id,
                "action": step.action,
                "status": "failed",
                "error": str(e),
                "duration": (step.end_time - step.start_time).total_seconds()
            }
            self.execution_log.append(log_entry)
            
            print(f"  ❌ {step.id} 失败: {e}")
            
            # 重试
            if step.retry > 0:
                print(f"  🔄 重试 {step.id}...")
                step.retry -= 1
                step.status = StepStatus.PENDING
                return self._execute_step(step, callback)
            
            return {"status": "failed", "error": str(e)}


# ===== 预定义工作流模板 =====

def create_software_dev_workflow() -> Workflow:
    """创建软件开发工作流（MetaGPT 风格）"""
    workflow = Workflow("software-development", WorkflowType.HYBRID)
    
    # PM 分析需求
    workflow.add_step(
        step_id="pm_analyze",
        agent_id="pm",
        action="analyze_requirements",
        output_key="requirements"
    )
    
    # 架构师设计系统
    workflow.add_step(
        step_id="architect_design",
        agent_id="architect",
        action="design_system",
        depends_on=["pm_analyze"],
        output_key="design"
    )
    
    # 前端和后端并行开发
    workflow.add_step(
        step_id="frontend_code",
        agent_id="frontend_engineer",
        action="implement",
        depends_on=["architect_design"],
        output_key="frontend_code"
    )
    
    workflow.add_step(
        step_id="backend_code",
        agent_id="backend_engineer",
        action="implement",
        depends_on=["architect_design"],
        output_key="backend_code"
    )
    
    # QA 测试
    workflow.add_step(
        step_id="qa_test",
        agent_id="qa",
        action="test",
        depends_on=["frontend_code", "backend_code"],
        output_key="test_report"
    )
    
    # DevOps 部署
    workflow.add_step(
        step_id="deploy",
        agent_id="devops",
        action="deploy",
        depends_on=["qa_test"],
        output_key="deployment"
    )
    
    return workflow


def create_research_workflow() -> Workflow:
    """创建研究工作流"""
    workflow = Workflow("research", WorkflowType.DAG)
    
    # 数据收集（并行）
    workflow.add_step(
        step_id="collect_web",
        agent_id="researcher",
        action="collect_web_data",
        output_key="web_data"
    )
    
    workflow.add_step(
        step_id="collect_api",
        agent_id="researcher",
        action="collect_api_data",
        output_key="api_data"
    )
    
    # 数据分析（等待收集完成）
    workflow.add_step(
        step_id="analyze",
        agent_id="analyst",
        action="analyze",
        depends_on=["collect_web", "collect_api"],
        output_key="analysis"
    )
    
    # 生成报告
    workflow.add_step(
        step_id="report",
        agent_id="pm",
        action="write_report",
        depends_on=["analyze"],
        output_key="report"
    )
    
    return workflow


def create_code_review_workflow() -> Workflow:
    """创建代码审查工作流"""
    workflow = Workflow("code-review", WorkflowType.SOP)
    
    workflow.add_step(
        step_id="check_style",
        agent_id="qa",
        action="check_code_style",
        output_key="style_report"
    )
    
    workflow.add_step(
        step_id="security_scan",
        agent_id="security",
        action="scan_security",
        depends_on=["check_style"],
        output_key="security_report"
    )
    
    workflow.add_step(
        step_id="review",
        agent_id="architect",
        action="review_code",
        depends_on=["security_scan"],
        output_key="review_comments"
    )
    
    return workflow


# ===== CLI 入口 =====

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow Engine")
    parser.add_argument("command", choices=["demo", "list"])
    parser.add_argument("--type", choices=["sop", "dag", "hybrid"], default="hybrid")
    
    args = parser.parse_args()
    
    if args.command == "list":
        print("可用工作流模板:")
        print("  - software-development (软件开发)")
        print("  - research (研究分析)")
        print("  - code-review (代码审查)")
    
    elif args.command == "demo":
        # Demo: 模拟 Agent
        class MockAgent:
            def __init__(self, name):
                self.name = name
            
            def analyze_requirements(self, ctx):
                print(f"    [{self.name}] 分析需求中...")
                return {"features": ["用户登录", "数据管理"]}
            
            def design_system(self, ctx):
                print(f"    [{self.name}] 设计架构中...")
                return {"architecture": "微服务", "tech_stack": "Python + FastAPI"}
            
            def implement(self, ctx):
                print(f"    [{self.name}] 编写代码中...")
                return {"files": ["main.py", "api.py"]}
            
            def test(self, ctx):
                print(f"    [{self.name}] 测试中...")
                return {"passed": 10, "failed": 0}
            
            def deploy(self, ctx):
                print(f"    [{self.name}] 部署中...")
                return {"url": "https://api.example.com"}
        
        # 创建 Agent
        agents = {
            "pm": MockAgent("产品经理"),
            "architect": MockAgent("架构师"),
            "frontend_engineer": MockAgent("前端工程师"),
            "backend_engineer": MockAgent("后端工程师"),
            "qa": MockAgent("QA"),
            "devops": MockAgent("DevOps")
        }
        
        # 创建工作流
        workflow = create_software_dev_workflow()
        
        # 执行
        engine = WorkflowEngine(agents)
        result = engine.run(workflow, {"project": "Demo Project"})
        
        print("\n📦 最终产物:")
        for key, value in result["environment"]["context"].items():
            print(f"  - {key}: {value}")
