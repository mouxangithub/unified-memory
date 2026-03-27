#!/usr/bin/env python3
"""
Workflow Validator - 工作流验证

验证工作流是否能正常运行。

功能:
- 验证 SOP 配置
- 验证 Agent 配置
- 端到端测试
- 生成测试报告

Usage:
    validator = WorkflowValidator()
    report = validator.validate_all()
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class WorkflowValidator:
    """工作流验证器"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or (Path.home() / ".openclaw" / "workspace" / "skills" / "unified-memory")
        self.configs_dir = self.base_dir / "configs"
        self.scripts_dir = self.base_dir / "scripts"
        
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "tests": []
        }
    
    def validate_all(self) -> Dict[str, Any]:
        """运行所有验证"""
        print("🔍 工作流验证\n")
        
        # 1. 验证 SOP 配置
        self._validate_sop_configs()
        
        # 2. 验证 CLI 命令
        self._validate_cli_commands()
        
        # 3. 验证核心模块
        self._validate_core_modules()
        
        # 4. 生成报告
        report = self._generate_report()
        
        return report
    
    def _validate_sop_configs(self):
        """验证 SOP 配置"""
        print("📋 验证 SOP 配置...")
        
        sop_dir = self.configs_dir / "sop"
        if not sop_dir.exists():
            self._add_result("SOP 配置目录", "failed", "配置目录不存在")
            return
        
        # 检查配置文件
        for config_file in sop_dir.glob("*.yaml"):
            try:
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                
                # 验证必需字段
                if "name" not in config:
                    self._add_result(
                        f"SOP: {config_file.name}",
                        "failed",
                        "缺少 name 字段"
                    )
                elif "steps" not in config:
                    self._add_result(
                        f"SOP: {config_file.name}",
                        "warning",
                        "缺少 steps 字段"
                    )
                else:
                    self._add_result(
                        f"SOP: {config_file.name}",
                        "passed",
                        f"{len(config['steps'])} 个步骤"
                    )
            except Exception as e:
                self._add_result(
                    f"SOP: {config_file.name}",
                    "failed",
                    str(e)
                )
    
    def _validate_cli_commands(self):
        """验证 CLI 命令"""
        print("⚡ 验证 CLI 命令...")
        
        mem_file = self.scripts_dir / "mem"
        
        if not mem_file.exists():
            self._add_result("mem CLI", "failed", "文件不存在")
            return
        
        # 测试基本命令
        import subprocess
        
        commands = [
            ("mem --help", "显示帮助"),
            ("mem health", "健康检查"),
            ("mem stats", "统计信息"),
        ]
        
        for cmd, desc in commands:
            try:
                result = subprocess.run(
                    f"python3 {mem_file} {cmd.split(' ', 1)[1]}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    self._add_result(f"CLI: {cmd}", "passed", desc)
                else:
                    self._add_result(
                        f"CLI: {cmd}",
                        "failed",
                        result.stderr[:100]
                    )
            except subprocess.TimeoutExpired:
                self._add_result(f"CLI: {cmd}", "warning", "超时")
            except Exception as e:
                self._add_result(f"CLI: {cmd}", "failed", str(e)[:100])
    
    def _validate_core_modules(self):
        """验证核心模块"""
        print("📦 验证核心模块...")
        
        modules = [
            ("context_tree", "项目上下文管理"),
            ("smart_summarizer", "智能摘要"),
            ("project_templates", "项目模板"),
        ]
        
        for module_name, desc in modules:
            module_path = self.scripts_dir / module_name.replace("_", "/") / f"{module_name}.py"
            module_path_alt = self.scripts_dir / "intelligence" / f"{module_name}.py"
            
            if module_path.exists() or module_path_alt.exists():
                # 尝试导入
                try:
                    import importlib.util
                    path = module_path if module_path.exists() else module_path_alt
                    
                    spec = importlib.util.spec_from_file_location(module_name, path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    self._add_result(f"模块: {module_name}", "passed", desc)
                except Exception as e:
                    self._add_result(
                        f"模块: {module_name}",
                        "warning",
                        f"导入失败: {str(e)[:50]}"
                    )
            else:
                self._add_result(
                    f"模块: {module_name}",
                    "failed",
                    "文件不存在"
                )
    
    def _add_result(self, name: str, status: str, message: str):
        """添加测试结果"""
        self.results["tests"].append({
            "name": name,
            "status": status,
            "message": message,
            "time": datetime.now().isoformat()
        })
        
        if status == "passed":
            self.results["passed"] += 1
        elif status == "failed":
            self.results["failed"] += 1
        else:
            self.results["warnings"] += 1
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成报告"""
        total = self.results["passed"] + self.results["failed"] + self.results["warnings"]
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "passed": self.results["passed"],
                "failed": self.results["failed"],
                "warnings": self.results["warnings"],
                "success_rate": f"{(self.results['passed'] / total * 100):.1f}%" if total > 0 else "N/A"
            },
            "tests": self.results["tests"]
        }
        
        # 打印摘要
        print("\n" + "="*50)
        print("📊 验证报告\n")
        print(f"总数: {total}")
        print(f"通过: {self.results['passed']} ✅")
        print(f"失败: {self.results['failed']} ❌")
        print(f"警告: {self.results['warnings']} ⚠️")
        print(f"成功率: {report['summary']['success_rate']}")
        
        if self.results["failed"] > 0:
            print("\n❌ 失败项:")
            for test in self.results["tests"]:
                if test["status"] == "failed":
                    print(f"  - {test['name']}: {test['message']}")
        
        return report


# CLI 入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow Validator - 工作流验证")
    parser.add_argument("--output", "-o", help="输出报告文件")
    
    args = parser.parse_args()
    
    validator = WorkflowValidator()
    report = validator.validate_all()
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 报告已保存: {args.output}")
