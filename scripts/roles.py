#!/usr/bin/env python3
"""
Roles - 角色定义系统（学习 MetaGPT）

整合 MetaGPT 的角色设计，包含：
- 角色基类
- 预定义角色（PM、Architect、Engineer、QA 等）
- 动作定义
- 技能系统

使用：
    from roles import ProductManager, Architect, Engineer
    
    pm = ProductManager()
    architect = Architect()
    engineer = Engineer()
    
    # 执行动作
    requirements = pm.analyze_requirements("做一个博客系统")
    design = architect.design_system(requirements)
    code = engineer.implement(design)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class RoleType(Enum):
    """角色类型"""
    PM = "pm"                           # 产品经理
    ARCHITECT = "architect"             # 架构师
    ENGINEER = "engineer"               # 工程师
    FRONTEND_ENGINEER = "frontend"      # 前端工程师
    BACKEND_ENGINEER = "backend"        # 后端工程师
    QA = "qa"                           # 测试工程师
    DEVOPS = "devops"                   # DevOps 工程师
    SECURITY = "security"               # 安全工程师
    DATA_ENGINEER = "data"              # 数据工程师
    DESIGNER = "designer"               # UI/UX 设计师


@dataclass
class Action:
    """动作定义"""
    name: str
    description: str
    input_keys: List[str] = field(default_factory=list)      # 输入要求
    output_key: str = ""                                       # 输出键
    required_skills: List[str] = field(default_factory=list)  # 所需技能


@dataclass
class Message:
    """Agent 间消息"""
    sender: str
    receiver: str
    content: Any
    msg_type: str = "action"  # action, request, response, notification
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class Role(ABC):
    """
    角色基类（学习 MetaGPT）
    
    每个角色有：
    - 名称、ID
    - 角色类型
    - 技能列表
    - 可执行动作
    """
    
    def __init__(self, 
                 role_id: str,
                 name: str,
                 role_type: RoleType,
                 skills: List[str] = None):
        self.role_id = role_id
        self.name = name
        self.role_type = role_type
        self.skills = skills or []
        self.actions: Dict[str, Action] = {}
        self.inbox: List[Message] = []
        self.outbox: List[Message] = []
        self.context: Dict[str, Any] = {}
        
        # 初始化动作
        self._init_actions()
    
    @abstractmethod
    def _init_actions(self):
        """初始化动作（子类实现）"""
        pass
    
    def add_action(self, action: Action):
        """添加动作"""
        self.actions[action.name] = action
    
    def can_execute(self, action_name: str) -> bool:
        """检查是否可执行某动作"""
        return action_name in self.actions
    
    def receive(self, message: Message):
        """接收消息"""
        self.inbox.append(message)
    
    def send(self, receiver: str, content: Any, msg_type: str = "action"):
        """发送消息"""
        msg = Message(
            sender=self.role_id,
            receiver=receiver,
            content=content,
            msg_type=msg_type
        )
        self.outbox.append(msg)
        return msg
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "role_id": self.role_id,
            "name": self.name,
            "role_type": self.role_type.value,
            "skills": self.skills,
            "actions": list(self.actions.keys())
        }


# ===== 预定义角色 =====

class ProductManager(Role):
    """产品经理 - 分析需求、设计产品"""
    
    def __init__(self, role_id: str = "pm"):
        super().__init__(
            role_id=role_id,
            name="产品经理",
            role_type=RoleType.PM,
            skills=["需求分析", "产品设计", "用户研究", "数据分析"]
        )
    
    def _init_actions(self):
        self.add_action(Action(
            name="analyze_requirements",
            description="分析用户需求",
            input_keys=["user_input"],
            output_key="requirements"
        ))
        self.add_action(Action(
            name="create_prd",
            description="创建产品需求文档",
            input_keys=["requirements"],
            output_key="prd"
        ))
        self.add_action(Action(
            name="prioritize_features",
            description="功能优先级排序",
            input_keys=["features"],
            output_key="priority_list"
        ))
        self.add_action(Action(
            name="write_report",
            description="撰写报告",
            input_keys=["analysis"],
            output_key="report"
        ))
    
    def analyze_requirements(self, context: Dict) -> Dict:
        """分析需求"""
        user_input = context.get("user_input", context.get("project", ""))
        
        # 简化的需求分析逻辑
        requirements = {
            "raw_input": user_input,
            "features": self._extract_features(user_input),
            "constraints": self._extract_constraints(user_input),
            "priority": "high" if "紧急" in user_input or "important" in user_input.lower() else "normal"
        }
        
        return requirements
    
    def _extract_features(self, text: str) -> List[str]:
        """提取功能（简化版，实际可用 LLM）"""
        features = []
        keywords = ["登录", "注册", "搜索", "支付", "管理", "分析", "导出", "导入"]
        for kw in keywords:
            if kw in text:
                features.append(kw)
        if not features:
            features = ["基础功能"]
        return features
    
    def _extract_constraints(self, text: str) -> List[str]:
        """提取约束"""
        constraints = []
        if "快速" in text or "fast" in text.lower():
            constraints.append("性能优先")
        if "安全" in text or "secure" in text.lower():
            constraints.append("安全优先")
        return constraints
    
    def create_prd(self, context: Dict) -> Dict:
        """创建 PRD"""
        requirements = context.get("requirements", context)
        
        prd = {
            "title": f"{requirements.get('raw_input', '项目')} 产品需求文档",
            "features": requirements.get("features", []),
            "constraints": requirements.get("constraints", []),
            "created_at": datetime.now().isoformat(),
            "sections": [
                "背景与目标",
                "用户画像",
                "功能列表",
                "非功能需求",
                "验收标准"
            ]
        }
        
        return prd


class Architect(Role):
    """架构师 - 设计系统架构"""
    
    def __init__(self, role_id: str = "architect"):
        super().__init__(
            role_id=role_id,
            name="架构师",
            role_type=RoleType.ARCHITECT,
            skills=["架构设计", "系统设计", "技术选型", "性能优化"]
        )
    
    def _init_actions(self):
        self.add_action(Action(
            name="design_system",
            description="设计系统架构",
            input_keys=["requirements"],
            output_key="design"
        ))
        self.add_action(Action(
            name="select_tech_stack",
            description="技术选型",
            input_keys=["requirements", "constraints"],
            output_key="tech_stack"
        ))
        self.add_action(Action(
            name="review_architecture",
            description="架构评审",
            input_keys=["design"],
            output_key="review_comments"
        ))
    
    def design_system(self, context: Dict) -> Dict:
        """设计系统架构"""
        requirements = context.get("requirements", context)
        features = requirements.get("features", []) if isinstance(requirements, dict) else []
        
        # 根据功能选择架构
        if len(features) > 5 or "微服务" in str(requirements):
            architecture = "microservices"
        elif len(features) > 2:
            architecture = "modular_monolith"
        else:
            architecture = "simple"
        
        design = {
            "architecture": architecture,
            "components": self._design_components(features),
            "tech_stack": self._recommend_stack(architecture),
            "diagrams": [
                "系统架构图",
                "数据流图",
                "部署图"
            ],
            "created_at": datetime.now().isoformat()
        }
        
        return design
    
    def _design_components(self, features: List[str]) -> List[Dict]:
        """设计组件"""
        components = []
        for feat in features:
            components.append({
                "name": feat,
                "type": "service" if feat in ["支付", "搜索"] else "module",
                "dependencies": []
            })
        return components
    
    def _recommend_stack(self, architecture: str) -> Dict:
        """推荐技术栈"""
        stacks = {
            "microservices": {
                "backend": "Python + FastAPI",
                "frontend": "React",
                "database": "PostgreSQL + Redis",
                "message_queue": "RabbitMQ"
            },
            "modular_monolith": {
                "backend": "Python + Django",
                "frontend": "Vue",
                "database": "PostgreSQL"
            },
            "simple": {
                "backend": "Python + Flask",
                "frontend": "简单 HTML/JS",
                "database": "SQLite"
            }
        }
        return stacks.get(architecture, stacks["simple"])


class Engineer(Role):
    """工程师 - 实现代码"""
    
    def __init__(self, role_id: str = "engineer", name: str = "工程师"):
        super().__init__(
            role_id=role_id,
            name=name,
            role_type=RoleType.ENGINEER,
            skills=["Python", "JavaScript", "代码实现", "单元测试"]
        )
    
    def _init_actions(self):
        self.add_action(Action(
            name="implement",
            description="实现功能",
            input_keys=["design"],
            output_key="code"
        ))
        self.add_action(Action(
            name="write_tests",
            description="编写测试",
            input_keys=["code"],
            output_key="tests"
        ))
        self.add_action(Action(
            name="code_review",
            description="代码审查",
            input_keys=["code"],
            output_key="review_comments"
        ))
    
    def implement(self, context: Dict) -> Dict:
        """实现代码"""
        design = context.get("design", context)
        
        code = {
            "files": [],
            "language": "python",
            "created_at": datetime.now().isoformat()
        }
        
        # 根据设计生成文件列表
        if isinstance(design, dict):
            components = design.get("components", [])
            for comp in components:
                code["files"].append({
                    "name": f"{comp['name'].replace(' ', '_')}.py",
                    "type": "module",
                    "description": f"{comp['name']} 模块"
                })
        
        return code
    
    def write_tests(self, context: Dict) -> Dict:
        """编写测试"""
        code = context.get("code", context)
        
        tests = {
            "test_files": [],
            "coverage": 0,
            "created_at": datetime.now().isoformat()
        }
        
        if isinstance(code, dict) and "files" in code:
            for f in code["files"]:
                tests["test_files"].append({
                    "name": f"test_{f['name']}",
                    "test_cases": 5
                })
            tests["coverage"] = min(len(tests["test_files"]) * 20, 100)
        
        return tests


class FrontendEngineer(Engineer):
    """前端工程师"""
    
    def __init__(self, role_id: str = "frontend"):
        super().__init__(role_id=role_id, name="前端工程师")
        self.role_type = RoleType.FRONTEND_ENGINEER
        self.skills = ["JavaScript", "React", "Vue", "CSS", "TypeScript"]
    
    def implement(self, context: Dict) -> Dict:
        design = context.get("design", context)
        
        code = {
            "files": [],
            "language": "javascript",
            "framework": "react",
            "created_at": datetime.now().isoformat()
        }
        
        if isinstance(design, dict):
            components = design.get("components", [])
            for comp in components:
                code["files"].append({
                    "name": f"{comp['name']}.jsx",
                    "type": "component",
                    "description": f"{comp['name']} 组件"
                })
        
        return code


class BackendEngineer(Engineer):
    """后端工程师"""
    
    def __init__(self, role_id: str = "backend"):
        super().__init__(role_id=role_id, name="后端工程师")
        self.role_type = RoleType.BACKEND_ENGINEER
        self.skills = ["Python", "FastAPI", "Django", "PostgreSQL", "Redis"]
    
    def implement(self, context: Dict) -> Dict:
        design = context.get("design", context)
        
        code = {
            "files": [],
            "language": "python",
            "framework": "fastapi",
            "created_at": datetime.now().isoformat()
        }
        
        if isinstance(design, dict):
            components = design.get("components", [])
            for comp in components:
                code["files"].append({
                    "name": f"{comp['name']}.py",
                    "type": "api",
                    "description": f"{comp['name']} API"
                })
        
        return code


class QA(Role):
    """测试工程师"""
    
    def __init__(self, role_id: str = "qa"):
        super().__init__(
            role_id=role_id,
            name="QA工程师",
            role_type=RoleType.QA,
            skills=["测试", "自动化测试", "性能测试", "安全测试"]
        )
    
    def _init_actions(self):
        self.add_action(Action(
            name="test",
            description="执行测试",
            input_keys=["code"],
            output_key="test_report"
        ))
        self.add_action(Action(
            name="write_test_plan",
            description="编写测试计划",
            input_keys=["requirements"],
            output_key="test_plan"
        ))
        self.add_action(Action(
            name="execute_tests",
            description="执行测试用例",
            input_keys=["test_plan", "code"],
            output_key="test_results"
        ))
    
    def test(self, context: Dict) -> Dict:
        """执行测试"""
        code = context.get("code", context)
        
        report = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "coverage": 0,
            "issues": [],
            "created_at": datetime.now().isoformat()
        }
        
        if isinstance(code, dict) and "files" in code:
            file_count = len(code["files"])
            report["total"] = file_count * 10
            report["passed"] = file_count * 9  # 90% 通过率
            report["failed"] = file_count * 1
            report["coverage"] = min(80 + file_count * 2, 95)
        
        return report


class DevOps(Role):
    """DevOps 工程师"""
    
    def __init__(self, role_id: str = "devops"):
        super().__init__(
            role_id=role_id,
            name="DevOps",
            role_type=RoleType.DEVOPS,
            skills=["CI/CD", "Docker", "Kubernetes", "AWS", "监控"]
        )
    
    def _init_actions(self):
        self.add_action(Action(
            name="deploy",
            description="部署系统",
            input_keys=["code", "test_report"],
            output_key="deployment"
        ))
        self.add_action(Action(
            name="setup_ci",
            description="配置 CI/CD",
            input_keys=["code"],
            output_key="ci_config"
        ))
        self.add_action(Action(
            name="monitor",
            description="监控设置",
            input_keys=["deployment"],
            output_key="monitoring"
        ))
    
    def deploy(self, context: Dict) -> Dict:
        """部署"""
        deployment = {
            "status": "deployed",
            "url": "https://api.example.com",
            "version": "1.0.0",
            "environment": "production",
            "created_at": datetime.now().isoformat()
        }
        
        return deployment


# ===== 角色工厂 =====

class RoleFactory:
    """角色工厂 - 创建角色实例"""
    
    @staticmethod
    def create(role_type: str, role_id: str = None) -> Role:
        """创建角色"""
        role_map = {
            "pm": ProductManager,
            "architect": Architect,
            "engineer": Engineer,
            "frontend": FrontendEngineer,
            "backend": BackendEngineer,
            "qa": QA,
            "devops": DevOps
        }
        
        role_class = role_map.get(role_type)
        if not role_class:
            raise ValueError(f"未知角色类型: {role_type}")
        
        return role_class(role_id or role_type)


# ===== CLI =====

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="角色系统")
    parser.add_argument("command", choices=["list", "demo"])
    
    args = parser.parse_args()
    
    if args.command == "list":
        print("可用角色:")
        print("  - pm: 产品经理")
        print("  - architect: 架构师")
        print("  - engineer: 工程师")
        print("  - frontend: 前端工程师")
        print("  - backend: 后端工程师")
        print("  - qa: QA工程师")
        print("  - devops: DevOps")
    
    elif args.command == "demo":
        # 创建角色
        pm = ProductManager()
        architect = Architect()
        engineer = Engineer()
        qa = QA()
        
        print("角色创建完成:")
        for role in [pm, architect, engineer, qa]:
            print(f"  - {role.name}: {len(role.actions)} 个动作")
        
        # 执行工作流
        print("\n执行工作流:")
        
        context = {"user_input": "做一个简单的博客系统"}
        
        requirements = pm.analyze_requirements(context)
        print(f"1. PM 分析需求: {requirements['features']}")
        
        context["requirements"] = requirements
        design = architect.design_system(context)
        print(f"2. 架构师设计: {design['architecture']}")
        
        context["design"] = design
        code = engineer.implement(context)
        print(f"3. 工程师实现: {len(code['files'])} 个文件")
        
        context["code"] = code
        test_report = qa.test(context)
        print(f"4. QA 测试: {test_report['passed']}/{test_report['total']} 通过")
