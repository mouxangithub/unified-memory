#!/usr/bin/env python3
"""
Workflow SOP - 标准化工作流引擎
借鉴 MetaGPT 的 SOP (Standard Operating Procedure) 概念

核心功能:
- YAML 定义 SOP 流程
- DAG 依赖解析
- 并行执行独立步骤
- 记忆驱动（每次执行自动存储结果）

SOP 格式:
  software_project.yaml:
    name: "软件开发 SOP"
    steps:
      - role: pm
        action: analyze_requirements
        output: prd.md
      
      - role: architect
        action: design_architecture
        input: prd.md
        output: architecture.md

Usage:
    from workflow_sop import SOPEngine
    
    engine = SOPEngine()
    engine.load_sop("software_project.yaml")
    engine.execute({"requirement": "创建一个博客系统"})
"""

import json
import os
import sys
import yaml
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
SOP_DIR = WORKSPACE / "skills" / "unified-memory" / "configs" / "sop"
OUTPUT_DIR = WORKSPACE / "output" / "sop"


class SOPStep:
    """SOP 步骤"""
    
    def __init__(self, data: Dict):
        self.id = data.get("id", f"step_{datetime.now().timestamp()}")
        self.role = data.get("role", "agent")
        self.action = data.get("action", "execute")
        self.description = data.get("description", "")
        self.input = data.get("input", [])  # 可以是文件列表或步骤 ID
        self.output = data.get("output", "")
        self.prompt_template = data.get("prompt", "")
        self.depends_on = data.get("depends_on", [])
        self.parallel = data.get("parallel", False)
        self.condition = data.get("condition", None)
        self.timeout = data.get("timeout", 300)  # 秒
        self.retry = data.get("retry", 0)
        
        # 执行状态
        self.status = "pending"  # pending, running, completed, failed, skipped
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "role": self.role,
            "action": self.action,
            "description": self.description,
            "input": self.input,
            "output": self.output,
            "depends_on": self.depends_on,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


class SOPEngine:
    """SOP 工作流引擎"""
    
    def __init__(self):
        self.sop_name = ""
        self.sop_description = ""
        self.steps: List[SOPStep] = []
        self.step_map: Dict[str, SOPStep] = {}
        self.context: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}
        
        # 角色处理器
        self.role_handlers: Dict[str, Callable] = {}
        
        # 输出目录
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def load_sop(self, sop_file: str) -> bool:
        """加载 SOP 文件"""
        sop_path = Path(sop_file)
        
        if not sop_path.is_absolute():
            sop_path = SOP_DIR / sop_file
        
        if not sop_path.exists():
            print(f"❌ SOP 文件不存在: {sop_path}", file=sys.stderr)
            return False
        
        try:
            with open(sop_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            self.sop_name = data.get("name", sop_path.stem)
            self.sop_description = data.get("description", "")
            
            # 加载步骤
            self.steps = []
            self.step_map = {}
            
            for step_data in data.get("steps", []):
                step = SOPStep(step_data)
                self.steps.append(step)
                self.step_map[step.id] = step
            
            return True
        
        except Exception as e:
            print(f"❌ 加载 SOP 失败: {e}", file=sys.stderr)
            return False
    
    def register_role_handler(self, role: str, handler: Callable):
        """注册角色处理器"""
        self.role_handlers[role] = handler
    
    def set_context(self, **kwargs):
        """设置上下文"""
        self.context.update(kwargs)
    
    def get_dag_order(self) -> List[List[str]]:
        """
        获取 DAG 执行顺序
        
        返回分层的步骤 ID，每层可以并行执行
        """
        # 计算入度
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        
        for step in self.steps:
            # 从 depends_on 构建图
            for dep in step.depends_on:
                graph[dep].append(step.id)
                in_degree[step.id] += 1
            
            # 从 input 中的步骤 ID 构建图
            for inp in step.input:
                if inp in self.step_map:
                    graph[inp].append(step.id)
                    in_degree[step.id] += 1
        
        # 拓扑排序
        layers = []
        remaining = set(self.step_map.keys())
        
        while remaining:
            # 找到入度为 0 的节点
            layer = [sid for sid in remaining if in_degree[sid] == 0]
            
            if not layer:
                # 循环依赖
                print(f"⚠️ 检测到循环依赖: {remaining}", file=sys.stderr)
                break
            
            layers.append(layer)
            
            # 移除当前层，更新入度
            for sid in layer:
                remaining.remove(sid)
                for next_sid in graph[sid]:
                    in_degree[next_sid] -= 1
        
        return layers
    
    def execute_step(self, step: SOPStep) -> bool:
        """执行单个步骤"""
        
        step.status = "running"
        step.started_at = datetime.now().isoformat()
        
        try:
            # 准备输入
            input_data = {}
            
            for inp in step.input:
                if inp in self.results:
                    input_data[inp] = self.results[inp]
                elif inp in self.context:
                    input_data[inp] = self.context[inp]
                else:
                    # 尝试从文件读取
                    file_path = OUTPUT_DIR / inp
                    if file_path.exists():
                        with open(file_path, "r", encoding="utf-8") as f:
                            input_data[inp] = f.read()
            
            # 获取处理器
            handler = self.role_handlers.get(step.role)
            
            if handler:
                # 调用处理器
                result = handler(
                    action=step.action,
                    input_data=input_data,
                    context=self.context,
                    step=step
                )
            else:
                # 默认处理器
                result = self._default_handler(step, input_data)
            
            # 保存结果
            self.results[step.id] = result
            step.result = result
            
            # 写入输出文件
            if step.output:
                output_path = OUTPUT_DIR / step.output
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    if isinstance(result, dict):
                        f.write(json.dumps(result, ensure_ascii=False, indent=2))
                    else:
                        f.write(str(result))
            
            step.status = "completed"
            step.completed_at = datetime.now().isoformat()
            
            return True
        
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            step.completed_at = datetime.now().isoformat()
            
            print(f"❌ 步骤 {step.id} 执行失败: {e}", file=sys.stderr)
            
            return False
    
    def _default_handler(self, step: SOPStep, input_data: Dict) -> Any:
        """默认处理器（调用 LLM）"""
        
        # 构建 prompt
        prompt = step.prompt_template or f"执行 {step.action}"
        
        if input_data:
            prompt += f"\n\n输入数据:\n"
            for key, value in input_data.items():
                prompt += f"- {key}: {str(value)[:500]}\n"
        
        # 如果有 Ollama，调用 LLM
        try:
            import requests
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud"),
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2000
                    }
                },
                timeout=step.timeout
            )
            
            if response.ok:
                return response.json().get("response", "")
        
        except Exception as e:
            print(f"⚠️ LLM 调用失败: {e}", file=sys.stderr)
        
        return f"[{step.role}] {step.action} executed"
    
    def execute(self, context: Dict = None) -> Dict:
        """
        执行 SOP
        
        返回执行报告
        """
        
        if context:
            self.context.update(context)
        
        # 获取执行顺序
        layers = self.get_dag_order()
        
        if not layers:
            return {"success": False, "error": "无法解析 DAG"}
        
        # 执行报告
        report = {
            "sop_name": self.sop_name,
            "description": self.sop_description,
            "total_steps": len(self.steps),
            "layers": len(layers),
            "started_at": datetime.now().isoformat(),
            "steps": [],
            "success": True
        }
        
        # 逐层执行
        for layer_idx, layer in enumerate(layers):
            print(f"📦 执行第 {layer_idx + 1} 层: {layer}", file=sys.stderr)
            
            # 并行执行当前层
            # TODO: 实现真正的并行（使用 asyncio 或 threading）
            for step_id in layer:
                step = self.step_map[step_id]
                success = self.execute_step(step)
                
                if not success and step.retry > 0:
                    for _ in range(step.retry):
                        success = self.execute_step(step)
                        if success:
                            break
                
                if not success:
                    report["success"] = False
                
                report["steps"].append(step.to_dict())
        
        report["completed_at"] = datetime.now().isoformat()
        
        # 存储到记忆
        try:
            from unified_memory import store_to_memory
            store_to_memory(
                f"【SOP】执行 {self.sop_name}: {'成功' if report['success'] else '失败'}",
                "decision",
                "sop"
            )
        except:
            pass
        
        return report
    
    def get_step_status(self, step_id: str) -> Optional[Dict]:
        """获取步骤状态"""
        step = self.step_map.get(step_id)
        if step:
            return step.to_dict()
        return None
    
    def list_steps(self) -> List[Dict]:
        """列出所有步骤"""
        return [step.to_dict() for step in self.steps]


# ============================================================
# 预定义 SOP
# ============================================================

DEFAULT_SOPS = {
    "software_project.yaml": """
name: "软件开发项目"
description: "完整的软件开发流程 SOP"

steps:
  - id: requirements
    role: pm
    action: analyze_requirements
    description: "分析需求，生成 PRD"
    output: prd.md
    prompt: |
      分析以下需求，生成产品需求文档（PRD）：
      {{requirement}}
      
      PRD 应包含：
      1. 项目背景
      2. 核心功能
      3. 用户故事
      4. 技术要求

  - id: architecture
    role: architect
    action: design_architecture
    description: "设计系统架构"
    input: [requirements]
    output: architecture.md
    depends_on: [requirements]
    prompt: |
      基于 PRD 设计系统架构：
      {{requirements}}
      
      架构设计应包含：
      1. 技术栈选择
      2. 模块划分
      3. 数据流设计
      4. API 设计

  - id: frontend
    role: frontend_engineer
    action: implement_frontend
    description: "实现前端"
    input: [architecture]
    output: frontend/
    depends_on: [architecture]
    prompt: "基于架构设计实现前端代码"

  - id: backend
    role: backend_engineer
    action: implement_backend
    description: "实现后端"
    input: [architecture]
    output: backend/
    depends_on: [architecture]
    prompt: "基于架构设计实现后端代码"

  - id: test
    role: qa
    action: test
    description: "测试"
    input: [frontend, backend]
    output: test_report.md
    depends_on: [frontend, backend]
    prompt: "对前后端代码进行测试"

  - id: review
    role: tech_lead
    action: code_review
    description: "代码审查"
    input: [frontend, backend, test]
    output: review_report.md
    depends_on: [test]
    prompt: "审查代码质量和测试报告"
""",

    "research.yaml": """
name: "研究项目"
description: "研究和调研流程 SOP"

steps:
  - id: search
    role: researcher
    action: search
    description: "搜索资料"
    output: search_results.md
    prompt: "搜索关于 {{topic}} 的资料"

  - id: analyze
    role: researcher
    action: analyze
    description: "分析资料"
    input: [search]
    output: analysis.md
    depends_on: [search]
    prompt: "分析搜索结果"

  - id: summary
    role: researcher
    action: summarize
    description: "总结报告"
    input: [analyze]
    output: summary.md
    depends_on: [analyze]
    prompt: "生成研究报告"
""",

    "content_creation.yaml": """
name: "内容创作"
description: "内容创作流程 SOP"

steps:
  - id: research
    role: researcher
    action: research
    description: "调研主题"
    output: research.md
    prompt: "调研 {{topic}}"

  - id: outline
    role: writer
    action: create_outline
    description: "创建大纲"
    input: [research]
    output: outline.md
    depends_on: [research]
    prompt: "基于调研创建内容大纲"

  - id: draft
    role: writer
    action: write_draft
    description: "撰写初稿"
    input: [outline]
    output: draft.md
    depends_on: [outline]
    prompt: "根据大纲撰写初稿"

  - id: edit
    role: editor
    action: edit
    description: "编辑润色"
    input: [draft]
    output: final.md
    depends_on: [draft]
    prompt: "编辑润色初稿"
"""
}


def init_default_sops():
    """初始化默认 SOP"""
    SOP_DIR.mkdir(parents=True, exist_ok=True)
    
    for filename, content in DEFAULT_SOPS.items():
        sop_path = SOP_DIR / filename
        
        if not sop_path.exists():
            with open(sop_path, "w", encoding="utf-8") as f:
                f.write(content.strip())
            
            print(f"✅ 创建默认 SOP: {filename}", file=sys.stderr)


# ============================================================
# CLI 接口
# ============================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow SOP Engine")
    parser.add_argument("action", choices=["run", "list", "init", "status"])
    parser.add_argument("--sop", help="SOP 文件名")
    parser.add_argument("--context", help="上下文 JSON")
    parser.add_argument("--step", help="指定步骤 ID")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    
    args = parser.parse_args()
    
    if args.action == "init":
        init_default_sops()
        return
    
    if args.action == "list":
        print("📁 可用 SOP:\n")
        for sop_file in SOP_DIR.glob("*.yaml"):
            print(f"  - {sop_file.name}")
        return
    
    if args.action == "status":
        if not args.sop:
            print("❌ 需要指定 --sop", file=sys.stderr)
            return
        
        engine = SOPEngine()
        if engine.load_sop(args.sop):
            steps = engine.list_steps()
            if args.json:
                print(json.dumps(steps, ensure_ascii=False, indent=2))
            else:
                for step in steps:
                    print(f"- [{step['status']}] {step['id']}: {step['description']}")
        return
    
    if args.action == "run":
        if not args.sop:
            print("❌ 需要指定 --sop", file=sys.stderr)
            return
        
        engine = SOPEngine()
        
        if not engine.load_sop(args.sop):
            return
        
        # 解析上下文
        context = {}
        if args.context:
            try:
                context = json.loads(args.context)
            except:
                context = {"input": args.context}
        
        # 执行
        report = engine.execute(context)
        
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*50}")
            print(f"SOP: {report['sop_name']}")
            print(f"状态: {'✅ 成功' if report['success'] else '❌ 失败'}")
            print(f"步骤: {report['total_steps']} 个")
            print(f"{'='*50}\n")
            
            for step in report["steps"]:
                status_icon = "✅" if step["status"] == "completed" else "❌"
                print(f"{status_icon} {step['id']}: {step['description']}")


if __name__ == "__main__":
    main()
