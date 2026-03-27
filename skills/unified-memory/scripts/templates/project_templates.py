#!/usr/bin/env python3
"""
Project Templates - 项目模板系统

快速启动常用项目。

模板:
- software-project: 软件开发项目
- content-creation: 内容创作项目
- research: 研究项目

Usage:
    from templates import ProjectTemplate
    template = ProjectTemplate("software-project")
    template.create("/path/to/project")
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class ProjectTemplate:
    """项目模板"""
    
    TEMPLATES = {
        "software-project": {
            "name": "软件开发项目",
            "description": "适用于软件开发项目，包含完整的工作流和文档结构",
            "structure": {
                ".context": {
                    "current.md": """# 当前状态

> 最后更新: {date}

## 当前任务
项目初始化

## 进度
0%

## 备注
项目刚创建

## 最近决策
- 暂无
""",
                    "architecture.md": """# 架构设计

## 技术栈
- 前端: 待定
- 后端: 待定
- 数据库: 待定

## 目录结构
```
src/
├── frontend/
├── backend/
└── shared/
```

## 关键决策
- 待记录
"""
                },
                "memory": {},
                "docs": {
                    "README.md": """# {project_name}

## 项目简介

{description}

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发
npm run dev
```

## 项目结构

```
├── src/           # 源代码
├── docs/          # 文档
├── memory/        # 记忆系统
└── .context/      # 项目上下文
```

## 开发指南

### 工作流程
1. 查看 .context/current.md 了解当前状态
2. 查看记忆系统了解项目历史
3. 开发完成后更新状态

### 记忆系统
- 使用 `mem store` 记录重要决策
- 使用 `mem search` 搜索历史
- 使用 `ctx` 管理项目上下文
"""
                },
                "src": {
                    "frontend": {},
                    "backend": {},
                    "shared": {}
                }
            }
        },
        
        "content-creation": {
            "name": "内容创作项目",
            "description": "适用于内容创作项目，包含写作、编辑、发布流程",
            "structure": {
                ".context": {
                    "current.md": """# 当前状态

> 最后更新: {date}

## 当前任务
项目初始化

## 进度
0%

## 备注
内容创作项目

## 最近决策
- 暂无
""",
                    "content-plan.md": """# 内容计划

## 目标受众
- 待定义

## 内容主题
- 待定义

## 发布计划
- 待定义
"""
                },
                "memory": {},
                "drafts": {},
                "published": {}
            }
        },
        
        "research": {
            "name": "研究项目",
            "description": "适用于研究项目，包含文献管理、实验记录、结果分析",
            "structure": {
                ".context": {
                    "current.md": """# 当前状态

> 最后更新: {date}

## 当前任务
项目初始化

## 进度
0%

## 备注
研究项目

## 最近决策
- 暂无
""",
                    "research-plan.md": """# 研究计划

## 研究问题
- 待定义

## 文献综述
- 待完成

## 实验设计
- 待设计

## 预期结果
- 待定义
"""
                },
                "memory": {},
                "literature": {},
                "experiments": {},
                "results": {}
            }
        }
    }
    
    def __init__(self, template_name: str):
        if template_name not in self.TEMPLATES:
            raise ValueError(f"未知模板: {template_name}. 可用: {list(self.TEMPLATES.keys())}")
        
        self.template_name = template_name
        self.template = self.TEMPLATES[template_name]
    
    def create(self, project_path: Path, project_name: str, description: str = ""):
        """创建项目"""
        project_path = Path(project_path)
        project_path.mkdir(parents=True, exist_ok=True)
        
        # 创建结构
        self._create_structure(
            project_path,
            self.template["structure"],
            project_name=project_name,
            description=description or self.template["description"],
            date=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        
        # 创建项目配置
        config = {
            "name": project_name,
            "template": self.template_name,
            "created": datetime.now().isoformat(),
            "description": description
        }
        
        config_file = project_path / ".project.json"
        config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False))
        
        return project_path
    
    def _create_structure(
        self, base_path: Path, structure: Dict, **kwargs
    ):
        """递归创建目录结构"""
        for name, content in structure.items():
            path = base_path / name
            
            if isinstance(content, dict):
                # 目录
                path.mkdir(exist_ok=True)
                self._create_structure(path, content, **kwargs)
            else:
                # 文件
                path.parent.mkdir(parents=True, exist_ok=True)
                
                # 替换占位符
                content_str = content.format(**kwargs)
                path.write_text(content_str)
    
    @classmethod
    def list_templates(cls) -> Dict[str, Dict[str, str]]:
        """列出所有模板"""
        return {
            name: {
                "name": template["name"],
                "description": template["description"]
            }
            for name, template in cls.TEMPLATES.items()
        }


# CLI 入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Project Templates - 项目模板")
    subparsers = parser.add_subparsers(dest="command")
    
    # list
    subparsers.add_parser("list", help="列出所有模板")
    
    # create
    create_parser = subparsers.add_parser("create", help="创建项目")
    create_parser.add_argument("template", help="模板名称")
    create_parser.add_argument("path", help="项目路径")
    create_parser.add_argument("--name", "-n", help="项目名称")
    create_parser.add_argument("--desc", "-d", default="", help="项目描述")
    
    args = parser.parse_args()
    
    if args.command == "list":
        templates = ProjectTemplate.list_templates()
        print("📦 可用模板:\n")
        for name, info in templates.items():
            print(f"  {name}: {info['name']}")
            print(f"    {info['description']}\n")
    
    elif args.command == "create":
        template = ProjectTemplate(args.template)
        project_name = args.name or Path(args.path).name
        project_path = template.create(args.path, project_name, args.desc)
        print(f"✅ 项目创建成功: {project_path}")
    
    else:
        parser.print_help()
