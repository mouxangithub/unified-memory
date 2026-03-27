#!/usr/bin/env python3
"""
Document Generator - 文档生成器（学习 MetaGPT）

整合 MetaGPT 的文档生成能力：
- PRD（产品需求文档）
- 系统设计文档
- API 文档
- README

使用：
    from doc_generator import DocumentGenerator
    
    gen = DocumentGenerator()
    prd = gen.generate_prd(requirements)
    design_doc = gen.generate_design_doc(design)
    api_doc = gen.generate_api_doc(endpoints)
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class Document:
    """文档"""
    title: str
    doc_type: str
    content: str
    sections: Dict[str, str]
    created_at: str
    format: str = "markdown"
    
    def save(self, path: str):
        """保存到文件"""
        Path(path).write_text(self.content, encoding="utf-8")
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "doc_type": self.doc_type,
            "content": self.content,
            "sections": self.sections,
            "created_at": self.created_at,
            "format": self.format
        }


class DocumentGenerator:
    """文档生成器"""
    
    def __init__(self):
        self.templates = {
            "prd": self._prd_template,
            "design": self._design_template,
            "api": self._api_template,
            "readme": self._readme_template
        }
    
    def generate(self, 
                 doc_type: str,
                 data: Dict[str, Any],
                 title: str = None) -> Document:
        """生成文档"""
        template_func = self.templates.get(doc_type)
        if not template_func:
            raise ValueError(f"不支持的文档类型: {doc_type}")
        
        content, sections = template_func(data, title)
        
        return Document(
            title=title or f"{doc_type.upper()} Document",
            doc_type=doc_type,
            content=content,
            sections=sections,
            created_at=datetime.now().isoformat()
        )
    
    def generate_prd(self, 
                     requirements: Dict,
                     title: str = "产品需求文档") -> Document:
        """生成 PRD"""
        return self.generate("prd", requirements, title)
    
    def generate_design_doc(self,
                           design: Dict,
                           title: str = "系统设计文档") -> Document:
        """生成设计文档"""
        return self.generate("design", design, title)
    
    def generate_api_doc(self,
                        endpoints: List[Dict],
                        title: str = "API 文档") -> Document:
        """生成 API 文档"""
        return self.generate("api", {"endpoints": endpoints}, title)
    
    def generate_readme(self,
                       project: Dict,
                       title: str = "README") -> Document:
        """生成 README"""
        return self.generate("readme", project, title)
    
    # ===== 模板 =====
    
    def _prd_template(self, data: Dict, title: str) -> tuple:
        """PRD 模板"""
        features = data.get("features", [])
        constraints = data.get("constraints", [])
        
        sections = {
            "背景": "## 背景\n\n本文档描述产品需求和功能规格。",
            "目标": f"## 目标\n\n{data.get('raw_input', '构建高质量软件产品')}",
            "功能列表": self._format_features(features),
            "非功能需求": self._format_constraints(constraints),
            "验收标准": "## 验收标准\n\n- 所有功能正常工作\n- 通过测试\n- 性能达标"
        }
        
        content = f"""# {title or '产品需求文档'}

{sections['背景']}

{sections['目标']}

{sections['功能列表']}

{sections['非功能需求']}

{sections['验收标准']}

---
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
        return content, sections
    
    def _design_template(self, data: Dict, title: str) -> tuple:
        """设计文档模板"""
        architecture = data.get("architecture", "simple")
        components = data.get("components", [])
        tech_stack = data.get("tech_stack", {})
        
        sections = {
            "概述": f"## 概述\n\n系统架构: **{architecture}**",
            "架构图": "## 架构图\n\n```\n[待补充]\n```",
            "组件设计": self._format_components(components),
            "技术栈": self._format_tech_stack(tech_stack),
            "数据模型": "## 数据模型\n\n[待补充]",
            "API 设计": "## API 设计\n\n[待补充]"
        }
        
        content = f"""# {title or '系统设计文档'}

{sections['概述']}

{sections['架构图']}

{sections['组件设计']}

{sections['技术栈']}

{sections['数据模型']}

{sections['API 设计']}

---
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
        return content, sections
    
    def _api_template(self, data: Dict, title: str) -> tuple:
        """API 文档模板"""
        endpoints = data.get("endpoints", [])
        
        sections = {
            "概述": "## 概述\n\nRESTful API 文档",
            "端点列表": self._format_endpoints(endpoints)
        }
        
        content = f"""# {title or 'API 文档'}

{sections['概述']}

{sections['端点列表']}

---
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
        return content, sections
    
    def _readme_template(self, data: Dict, title: str) -> tuple:
        """README 模板"""
        name = data.get("name", "项目名称")
        description = data.get("description", "项目描述")
        features = data.get("features", [])
        
        sections = {
            "标题": f"# {name}",
            "描述": f"\n{description}\n",
            "功能": f"## 功能\n\n" + "\n".join(f"- {f}" for f in features) if features else "",
            "安装": "## 安装\n\n```bash\npip install -r requirements.txt\n```",
            "使用": "## 使用\n\n```python\npython main.py\n```",
            "许可": "## 许可证\n\nMIT"
        }
        
        content = f"""{sections['标题']}
{sections['描述']}
{sections['功能']}

{sections['安装']}

{sections['使用']}

{sections['许可']}

---
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
        return content, sections
    
    # ===== 辅助方法 =====
    
    def _format_features(self, features: List) -> str:
        """格式化功能列表"""
        if not features:
            return "## 功能列表\n\n- [待补充]"
        
        items = "\n".join(f"### {i+1}. {f}\n\n描述: [待补充]" for i, f in enumerate(features))
        return f"## 功能列表\n\n{items}"
    
    def _format_constraints(self, constraints: List) -> str:
        """格式化约束"""
        if not constraints:
            return "## 非功能需求\n\n- 性能: 响应时间 < 1s\n- 安全: HTTPS 加密\n- 可用性: 99.9%"
        
        items = "\n".join(f"- {c}" for c in constraints)
        return f"## 非功能需求\n\n{items}"
    
    def _format_components(self, components: List) -> str:
        """格式化组件"""
        if not components:
            return "## 组件设计\n\n[待补充]"
        
        items = []
        for comp in components:
            name = comp.get("name", "未知")
            comp_type = comp.get("type", "module")
            items.append(f"### {name}\n\n类型: {comp_type}")
        
        return f"## 组件设计\n\n" + "\n\n".join(items)
    
    def _format_tech_stack(self, tech_stack: Dict) -> str:
        """格式化技术栈"""
        if not tech_stack:
            return "## 技术栈\n\n[待补充]"
        
        items = []
        for key, value in tech_stack.items():
            items.append(f"- **{key}**: {value}")
        
        return f"## 技术栈\n\n" + "\n".join(items)
    
    def _format_endpoints(self, endpoints: List) -> str:
        """格式化端点"""
        if not endpoints:
            return "### 端点列表\n\n| 方法 | 路径 | 描述 |\n|------|------|------|\n| GET | /api/health | 健康检查 |"
        
        rows = []
        for ep in endpoints:
            method = ep.get("method", "GET")
            path = ep.get("path", "/")
            desc = ep.get("description", "")
            rows.append(f"| {method} | {path} | {desc} |")
        
        return f"### 端点列表\n\n| 方法 | 路径 | 描述 |\n|------|------|------|\n" + "\n".join(rows)


# ===== CLI =====

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="文档生成器")
    parser.add_argument("command", choices=["demo"])
    
    args = parser.parse_args()
    
    if args.command == "demo":
        gen = DocumentGenerator()
        
        # 生成 PRD
        prd = gen.generate_prd({
            "raw_input": "构建一个博客系统",
            "features": ["用户登录", "文章管理", "评论功能"],
            "constraints": ["性能优先", "安全优先"]
        })
        print("📄 PRD 文档:")
        print(prd.content[:500] + "...\n")
        
        # 生成设计文档
        design_doc = gen.generate_design_doc({
            "architecture": "微服务",
            "components": [
                {"name": "用户服务", "type": "service"},
                {"name": "文章服务", "type": "service"}
            ],
            "tech_stack": {
                "backend": "Python + FastAPI",
                "frontend": "React",
                "database": "PostgreSQL"
            }
        })
        print("📐 设计文档:")
        print(design_doc.content[:500] + "...\n")
