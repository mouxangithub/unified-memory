#!/usr/bin/env python3
"""
API Docs Generator - API 文档生成器

功能:
- 自动生成 API 文档
- 生成使用示例
- 导出为 Markdown
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class APIEndpoint:
    method: str
    path: str
    description: str
    parameters: List[Dict]
    response: Dict
    example: Optional[str] = None


class APIDocsGenerator:
    """API 文档生成器"""
    
    def __init__(self):
        self.endpoints: List[APIEndpoint] = []
    
    def add_endpoint(self, endpoint: APIEndpoint):
        """添加端点"""
        self.endpoints.append(endpoint)
    
    def generate_markdown(self, title: str = "API 文档") -> str:
        """生成 Markdown 文档"""
        md = f"# {title}\n\n"
        md += f"生成时间: {self._get_timestamp()}\n\n"
        md += "---\n\n"
        
        # 目录
        md += "## 目录\n\n"
        for i, ep in enumerate(self.endpoints, 1):
            md += f"{i}. [{ep.method}] {ep.path} - {ep.description}\n"
        md += "\n---\n\n"
        
        # 详细文档
        md += "## API 端点\n\n"
        
        for ep in self.endpoints:
            md += f"### {ep.method} {ep.path}\n\n"
            md += f"**描述**: {ep.description}\n\n"
            
            # 参数
            if ep.parameters:
                md += "**参数**:\n\n"
                md += "| 参数名 | 类型 | 必填 | 说明 |\n"
                md += "|--------|------|------|------|\n"
                for param in ep.parameters:
                    md += f"| {param.get('name')} | {param.get('type')} | {'是' if param.get('required') else '否'} | {param.get('description')} |\n"
                md += "\n"
            
            # 响应
            md += "**响应**:\n\n"
            md += "```json\n"
            md += json.dumps(ep.response, ensure_ascii=False, indent=2)
            md += "\n```\n\n"
            
            # 示例
            if ep.example:
                md += "**示例**:\n\n"
                md += "```bash\n"
                md += ep.example
                md += "\n```\n\n"
            
            md += "---\n\n"
        
        return md
    
    def generate_openapi(self, title: str = "API", version: str = "1.0.0") -> Dict:
        """生成 OpenAPI 规范"""
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "version": version
            },
            "paths": {}
        }
        
        for ep in self.endpoints:
            path = openapi["paths"].setdefault(ep.path, {})
            
            path[ep.method.lower()] = {
                "summary": ep.description,
                "parameters": [
                    {
                        "name": p["name"],
                        "in": "query" if ep.method == "GET" else "body",
                        "required": p.get("required", False),
                        "schema": {"type": p.get("type", "string")},
                        "description": p.get("description")
                    }
                    for p in ep.parameters
                ],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }
        
        return openapi
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 预定义 API 文档
def generate_unified_memory_docs() -> str:
    """生成统一记忆系统 API 文档"""
    gen = APIDocsGenerator()
    
    # 认证 API
    gen.add_endpoint(APIEndpoint(
        method="POST",
        path="/api/register",
        description="注册新用户",
        parameters=[
            {"name": "username", "type": "string", "required": True, "description": "用户名"},
            {"name": "password", "type": "string", "required": True, "description": "密码"}
        ],
        response={"message": "注册成功"},
        example='curl -X POST http://localhost:38080/api/register -H "Content-Type: application/json" -d \'{"username":"test","password":"123456"}\''
    ))
    
    gen.add_endpoint(APIEndpoint(
        method="POST",
        path="/api/login",
        description="用户登录",
        parameters=[
            {"name": "username", "type": "string", "required": True, "description": "用户名"},
            {"name": "password", "type": "string", "required": True, "description": "密码"}
        ],
        response={"token": "xxx", "username": "test"},
        example='curl -X POST http://localhost:38080/api/login -H "Content-Type: application/json" -d \'{"username":"test","password":"123456"}\''
    ))
    
    # 记忆 API
    gen.add_endpoint(APIEndpoint(
        method="POST",
        path="/api/memory",
        description="存储记忆",
        parameters=[
            {"name": "text", "type": "string", "required": True, "description": "记忆内容"},
            {"name": "tags", "type": "array", "required": False, "description": "标签列表"}
        ],
        response={"message": "存储成功"},
        example='curl -X POST http://localhost:38080/api/memory -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d \'{"text":"测试记忆","tags":["test"]}\''
    ))
    
    gen.add_endpoint(APIEndpoint(
        method="POST",
        path="/api/memory/search",
        description="搜索记忆",
        parameters=[
            {"name": "query", "type": "string", "required": True, "description": "搜索关键词"},
            {"name": "limit", "type": "integer", "required": False, "description": "结果数量"},
            {"name": "mode", "type": "string", "required": False, "description": "搜索模式 (bm25/vector/hybrid)"}
        ],
        response={"results": [], "level": "hybrid"},
        example='curl -X POST http://localhost:38080/api/memory/search -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d \'{"query":"测试","limit":10}\''
    ))
    
    gen.add_endpoint(APIEndpoint(
        method="GET",
        path="/api/memory/stats",
        description="获取记忆统计",
        parameters=[],
        response={"total_memories": 0, "vectors": 0},
        example='curl http://localhost:38080/api/memory/stats -H "Authorization: Bearer TOKEN"'
    ))
    
    # 系统 API
    gen.add_endpoint(APIEndpoint(
        method="GET",
        path="/api/health",
        description="健康检查",
        parameters=[],
        response={"status": "healthy"},
        example='curl http://localhost:38080/api/health'
    ))
    
    return gen.generate_markdown("统一记忆系统 API 文档")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="API 文档生成器")
    parser.add_argument("--output", "-o", default="API_DOCS.md", help="输出文件")
    parser.add_argument("--format", "-f", choices=["markdown", "openapi"], default="markdown", help="输出格式")
    
    args = parser.parse_args()
    
    print("📝 生成 API 文档...\n")
    
    # 生成文档
    docs = generate_unified_memory_docs()
    
    # 保存
    output_path = Path(args.output)
    output_path.write_text(docs, encoding="utf-8")
    
    print(f"✅ 文档已保存: {output_path}")
    print(f"\n预览:\n{'-'*40}")
    print(docs[:500] + "...")


if __name__ == "__main__":
    main()
