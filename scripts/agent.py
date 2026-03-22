#!/usr/bin/env python3
"""
Agent - 统一入口（记忆系统 + 工作流引擎）

用法:
    # 一键生成项目
    python agent.py "写一个博客系统"
    
    # 指定类型
    python agent.py "开发 API" --type fastapi
    
    # 使用特定 LLM
    python agent.py "CLI 工具" --llm claude
    
    # 多轮对话模式
    python agent.py chat
    
    # 查看历史
    python agent.py history --task <task_id>
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import argparse

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入核心模块
from workflow_engine import Workflow, WorkflowEngine, WorkflowType
from roles import RoleFactory, ProductManager, Architect, Engineer, QA, DevOps
from doc_generator import DocumentGenerator
from code_generator import CodeGenerator
from llm_provider import LLMProviderFactory, LLMResponse
from sandbox import CodeSandbox
from tool_integration import ToolRegistry

# 导入记忆系统
try:
    from unified_memory import UnifiedMemory
    from agent_knowledge_linker import KnowledgeLinker
    from feedback_loop import FeedbackLoop
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False


class Agent:
    """统一 Agent 入口"""
    
    def __init__(self,
                 llm_provider: str = "openai",
                 llm_model: str = None,
                 output_dir: str = "./output",
                 use_memory: bool = True,
                 use_sandbox: bool = True,
                 verbose: bool = False):
        """
        初始化
        
        Args:
            llm_provider: LLM 提供商
            llm_model: LLM 模型
            output_dir: 输出目录
            use_memory: 是否使用记忆系统
            use_sandbox: 是否使用沙箱
            verbose: 详细输出
        """
        # 初始化 LLM
        self.llm = LLMProviderFactory.create(
            provider=llm_provider,
            model=llm_model
        )
        
        # 初始化角色
        self.roles = {
            "pm": ProductManager(),
            "architect": Architect(),
            "engineer": Engineer(),
            "qa": QA(),
            "devops": DevOps()
        }
        
        # 初始化工具
        self.doc_gen = DocumentGenerator()
        self.code_gen = CodeGenerator()
        self.sandbox = CodeSandbox(timeout=30) if use_sandbox else None
        self.tools = ToolRegistry()
        
        # 初始化记忆系统
        self.memory = None
        self.knowledge = None
        self.feedback = None
        
        if use_memory and MEMORY_AVAILABLE:
            try:
                self.memory = UnifiedMemory()
                self.knowledge = KnowledgeLinker()
                self.feedback = FeedbackLoop()
            except Exception as e:
                print(f"⚠️ 记忆系统初始化失败: {e}")
        
        # 输出目录
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 详细模式
        self.verbose = verbose
    
    def run(self,
            description: str,
            project_type: str = "fastapi",
            project_name: str = None) -> Dict[str, Any]:
        """
        运行完整流程
        
        Args:
            description: 项目描述
            project_type: 项目类型
            project_name: 项目名称
        
        Returns:
            结果字典
        """
        # 项目名称
        if not project_name:
            project_name = self._extract_project_name(description)
        
        # 更新输出目录
        self.output_dir = self.output_dir / project_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 打印开始信息
        self._print_header(description, project_type, project_name)
        
        result = {
            "description": description,
            "project_type": project_type,
            "project_name": project_name,
            "output_dir": str(self.output_dir),
            "steps": {},
            "files": [],
            "success": True,
            "error": None,
            "timestamp": datetime.now().isoformat(),
            "memory_used": False
        }
        
        task_id = None
        decision_id = None
        
        try:
            # Step 0: 记忆检索
            if self.memory:
                similar = self._step("检索记忆",
                    lambda: self._search_similar(description))
                result["steps"]["similar"] = similar
                
                if similar:
                    print(f"   💡 发现 {len(similar)} 个相似项目")
            
            # Step 1: 需求分析
            requirements = self._step("需求分析",
                lambda: self._analyze_requirements(description))
            result["steps"]["requirements"] = requirements
            
            # 创建任务并关联
            if self.knowledge:
                task_id = self.knowledge.create_task(
                    task_type=project_type,
                    description=description,
                    created_by="agent"
                )
                result["task_id"] = task_id
            
            # Step 2: 架构设计
            design = self._step("架构设计",
                lambda: self._design_architecture(requirements, project_type))
            result["steps"]["design"] = design
            
            # 创建决策并关联
            if self.knowledge and task_id:
                decision_id = self.knowledge.create_decision(
                    decision_type="architecture",
                    context=json.dumps(design),
                    reasoning=f"基于需求选择 {project_type} 架构",
                    made_by="architect",
                    task_id=task_id
                )
                result["decision_id"] = decision_id
            
            # Step 3: 生成文档
            docs = self._step("生成文档",
                lambda: self._generate_documents(requirements, design, project_name))
            result["steps"]["docs"] = list(docs.keys())
            
            # Step 4: 生成代码
            code_files = self._step("生成代码",
                lambda: self._generate_code(requirements, design, project_type, project_name))
            result["steps"]["code"] = [f.name for f in code_files]
            
            # Step 5: 测试验证
            test_result = self._step("测试验证",
                lambda: self._test_code(code_files))
            result["steps"]["test"] = test_result
            
            # Step 6: 保存输出
            saved_files = self._step("保存输出",
                lambda: self._save_all(docs, code_files))
            result["files"] = saved_files
            
            # Step 7: 存储记忆
            if self.memory and task_id:
                self._step("存储记忆",
                    lambda: self._store_to_memory(task_id, decision_id, result))
                result["memory_used"] = True
            
            # 打印完成信息
            self._print_footer(result)
        
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            self._print_error(e)
        
        return result
    
    def chat(self):
        """多轮对话模式"""
        print("\n💬 多轮对话模式（输入 'quit' 退出）")
        print("-" * 40)
        
        context = {
            "project": None,
            "requirements": None,
            "design": None,
            "code": None
        }
        
        while True:
            try:
                user_input = input("\n你: ").strip()
                
                if user_input.lower() in ["quit", "exit", "q"]:
                    break
                
                if not user_input:
                    continue
                
                # 解析意图
                intent = self._parse_intent(user_input, context)
                
                # 执行动作
                response = self._execute_intent(intent, user_input, context)
                
                print(f"\nAI: {response}")
            
            except KeyboardInterrupt:
                break
        
        print("\n再见！")
    
    def _parse_intent(self, text: str, context: Dict) -> str:
        """解析用户意图"""
        
        # 新项目
        if any(kw in text for kw in ["写一个", "开发", "构建", "创建"]):
            return "create"
        
        # 修改
        if any(kw in text for kw in ["修改", "改成", "换成", "加个", "添加"]):
            return "modify"
        
        # 查询历史
        if any(kw in text for kw in ["上次", "历史", "以前", "之前"]):
            return "history"
        
        # 提问
        if any(kw in text for kw in ["为什么", "怎么", "如何", "什么"]):
            return "question"
        
        return "unknown"
    
    def _execute_intent(self, intent: str, text: str, context: Dict) -> str:
        """执行意图"""
        
        if intent == "create":
            result = self.run(text)
            if result["success"]:
                context["project"] = result["project_name"]
                context["requirements"] = result["steps"].get("requirements")
                context["design"] = result["steps"].get("design")
                return f"✅ 项目已生成: {result['output_dir']}"
            else:
                return f"❌ 生成失败: {result['error']}"
        
        elif intent == "modify":
            if not context["project"]:
                return "⚠️ 请先创建一个项目"
            
            # 简化：直接重新生成
            result = self.run(text, project_name=context["project"])
            return f"✅ 已更新: {text}"
        
        elif intent == "history":
            if self.memory:
                similar = self.memory.search(text, limit=3)
                if similar:
                    return f"📚 找到 {len(similar)} 个相似项目:\n" + \
                           "\n".join([f"  - {s.get('text', '')[:50]}..." for s in similar])
            return "📚 暂无历史记录"
        
        elif intent == "question":
            response = self.llm.generate(text)
            return response.content
        
        else:
            response = self.llm.generate(text)
            return response.content
    
    def history(self, task_id: str = None, limit: int = 10) -> List[Dict]:
        """查看历史"""
        
        if not self.knowledge:
            print("⚠️ 记忆系统未启用")
            return []
        
        if task_id:
            # 追溯特定任务
            return self.knowledge.trace_task(task_id)
        else:
            # 列出最近任务
            # 简化实现
            return []
    
    def _search_similar(self, description: str) -> List[Dict]:
        """检索相似项目"""
        if not self.memory:
            return []
        
        try:
            results = self.memory.search(description, limit=5)
            return results
        except:
            return []
    
    def _step(self, name: str, func) -> Any:
        """执行步骤"""
        print(f"\n📋 {name}...")
        result = func()
        print(f"   ✅ 完成")
        return result
    
    def _extract_project_name(self, description: str) -> str:
        """提取项目名称"""
        import re
        
        # 尝试提取关键词
        keywords = re.findall(r'[\u4e00-\u9fa5]+系统|[\u4e00-\u9fa5]+平台|[\u4e00-\u9fa5]+应用', description)
        if keywords:
            name_map = {
                "博客系统": "blog-system",
                "用户管理": "user-management",
                "电商系统": "e-commerce",
                "API服务": "api-service",
                "CLI工具": "cli-tool"
            }
            for key, value in name_map.items():
                if key in description:
                    return value
        
        return f"project-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _analyze_requirements(self, description: str) -> Dict:
        """分析需求"""
        
        # 使用 LLM 分析
        prompt = f"""分析以下项目需求，提取功能列表和约束条件。

项目描述：{description}

请以 JSON 格式返回：
{{
    "features": ["功能1", "功能2"],
    "constraints": ["约束1"],
    "priority": ["高优先级功能"],
    "summary": "项目概述"
}}

只返回 JSON。"""
        
        response = self.llm.generate(prompt)
        
        try:
            content = response.content
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            requirements = json.loads(content.strip())
        except:
            requirements = {
                "features": ["核心功能"],
                "constraints": ["性能优先"],
                "priority": ["核心功能"],
                "summary": description[:100]
            }
        
        requirements["raw_input"] = description
        
        return requirements
    
    def _design_architecture(self, requirements: Dict, project_type: str) -> Dict:
        """设计架构"""
        
        architectures = {
            "fastapi": {
                "architecture": "微服务",
                "tech_stack": {
                    "backend": "Python + FastAPI",
                    "database": "PostgreSQL",
                    "cache": "Redis"
                },
                "components": [
                    {"name": "API 网关", "type": "gateway"},
                    {"name": "业务服务", "type": "service"}
                ]
            },
            "flask": {
                "architecture": "单体应用",
                "tech_stack": {
                    "backend": "Python + Flask",
                    "database": "SQLite"
                }
            },
            "express": {
                "architecture": "微服务",
                "tech_stack": {
                    "backend": "Node.js + Express",
                    "database": "MongoDB"
                }
            },
            "cli": {
                "architecture": "CLI 应用",
                "tech_stack": {
                    "language": "Python",
                    "cli": "Click/Typer"
                }
            }
        }
        
        return architectures.get(project_type, architectures["fastapi"])
    
    def _generate_documents(self, requirements: Dict, design: Dict, project_name: str) -> Dict[str, str]:
        """生成文档"""
        
        docs = {}
        
        # PRD
        prd = self.doc_gen.generate_prd(requirements, title=f"{project_name} 产品需求文档")
        docs["PRD.md"] = prd.content
        
        # 设计文档
        design_doc = self.doc_gen.generate_design_doc(design, title=f"{project_name} 设计文档")
        docs["DESIGN.md"] = design_doc.content
        
        # README
        readme = self.doc_gen.generate_readme({
            "name": project_name,
            "description": requirements.get("summary", "")
        })
        docs["README.md"] = readme.content
        
        return docs
    
    def _generate_code(self, requirements: Dict, design: Dict, project_type: str, project_name: str) -> List:
        """生成代码"""
        
        return self.code_gen.generate_project({
            "name": project_name,
            "type": project_type,
            "description": requirements.get("raw_input", ""),
            "features": requirements.get("features", [])
        })
    
    def _test_code(self, code_files: List) -> Dict:
        """测试代码"""
        
        if not self.sandbox:
            return {"skipped": True, "reason": "沙箱未启用"}
        
        test_files = [f for f in code_files if "test" in f.name.lower()]
        
        if not test_files:
            return {"skipped": True, "reason": "无测试文件"}
        
        results = []
        for test_file in test_files:
            result = self.sandbox.execute(test_file.content, language="python")
            results.append({
                "file": test_file.name,
                "success": result.success
            })
        
        return {
            "total": len(results),
            "passed": sum(1 for r in results if r["success"])
        }
    
    def _save_all(self, docs: Dict[str, str], code_files: List) -> List[str]:
        """保存所有文件"""
        
        saved = []
        
        for name, content in docs.items():
            path = self.output_dir / name
            path.write_text(content, encoding="utf-8")
            saved.append(str(path))
        
        for code_file in code_files:
            code_file.save(str(self.output_dir))
            saved.append(str(self.output_dir / code_file.name))
        
        return saved
    
    def _store_to_memory(self, task_id: str, decision_id: str, result: Dict):
        """存储到记忆系统"""
        
        # 存储结果
        if self.memory:
            self.memory.store(
                text=f"项目: {result['project_name']}\n描述: {result['description']}\n类型: {result['project_type']}",
                metadata={
                    "task_id": task_id,
                    "project_name": result["project_name"],
                    "project_type": result["project_type"],
                    "timestamp": result["timestamp"]
                }
            )
        
        # 创建结果并关联
        if self.knowledge and decision_id:
            result_id = self.knowledge.create_result(
                quality=0.9 if result["success"] else 0.5,
                output=json.dumps(result["files"]),
                for_task=task_id
            )
    
    def _print_header(self, description: str, project_type: str, project_name: str):
        """打印开始信息"""
        print(f"\n{'='*60}")
        print(f"🚀 项目生成开始")
        print(f"{'='*60}")
        print(f"📝 描述: {description[:50]}...")
        print(f"📦 类型: {project_type}")
        print(f"📛 名称: {project_name}")
        if self.memory:
            print(f"🧠 记忆系统: 已启用")
        print(f"{'='*60}")
    
    def _print_footer(self, result: Dict):
        """打印完成信息"""
        print(f"\n{'='*60}")
        print(f"✅ 项目生成完成！")
        print(f"{'='*60}")
        print(f"📁 项目目录: {result['output_dir']}")
        print(f"📄 文档: {len(result['steps'].get('docs', []))} 个")
        print(f"💻 代码: {len(result['steps'].get('code', []))} 个文件")
        if result.get("memory_used"):
            print(f"🧠 已存储到记忆系统")
        print(f"{'='*60}\n")
    
    def _print_error(self, error: Exception):
        """打印错误"""
        print(f"\n❌ 错误: {error}\n")


def main():
    parser = argparse.ArgumentParser(
        description="统一 Agent 入口",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "description",
        nargs="?",
        help="项目描述"
    )
    
    parser.add_argument(
        "--type",
        choices=["fastapi", "flask", "express", "cli"],
        default="fastapi",
        help="项目类型"
    )
    
    parser.add_argument(
        "--llm",
        choices=["openai", "claude", "zhipu", "qianfan", "dashscope", "ollama"],
        default="openai",
        help="LLM 提供商"
    )
    
    parser.add_argument(
        "--output",
        default="./output",
        help="输出目录"
    )
    
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="禁用记忆系统"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    # 创建 Agent
    agent = Agent(
        llm_provider=args.llm,
        output_dir=args.output,
        use_memory=not args.no_memory,
        verbose=args.verbose
    )
    
    if args.description:
        # 一键生成
        result = agent.run(args.description, project_type=args.type)
        sys.exit(0 if result["success"] else 1)
    else:
        # 多轮对话
        agent.chat()


if __name__ == "__main__":
    main()
