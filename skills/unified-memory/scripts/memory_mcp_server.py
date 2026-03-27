#!/usr/bin/env python3
"""
Unified Memory MCP Server - Model Context Protocol server for unified-memory

Exposes unified-memory search and management as MCP tools and resources.
Memories are accessible via memory:// URIs.

Based on QMD's MCP implementation by tobi (https://github.com/tobi/qmd)
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

# MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        Resource,
        ResourceTemplate,
        ImageContent,
        EmbeddedResource,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("❌ MCP SDK not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Import unified-memory
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from memory_qmd_search import QMDSearch, load_config

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

# 创建 MCP Server
app = Server("unified-memory")

# 全局搜索器
searcher: Optional[QMDSearch] = None


def get_searcher() -> QMDSearch:
    """获取搜索器实例"""
    global searcher
    if searcher is None:
        config = load_config()
        searcher = QMDSearch(
            use_vector=config.get("use_vector", True),
            use_llm_rerank=config.get("use_llm_rerank", False),
            llm_model=config.get("llm_model", "qwen2.5:0.5b")
        )
    return searcher


def format_search_results(results: list, query: str) -> str:
    """格式化搜索结果"""
    if not results:
        return f'No results found for "{query}"'
    
    lines = [f"Found {len(results)} result(s) for \"{query}\":\n"]
    
    for i, r in enumerate(results, 1):
        score = r.get("score", 0)
        category = r.get("category", "unknown")
        mode = r.get("mode", "auto")
        text = r.get("text", "")[:200]
        
        lines.append(f"[{i}] Score: {score:.4f} | Category: {category} | Mode: {mode}")
        lines.append(f"    {text}...")
        lines.append("")
    
    return "\n".join(lines)


# ============ MCP Tools ============

@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="memory_search",
            description="""Search memories using QMD-style layered search.

Three modes available:
- BM25 (0 Token): Fast keyword search
- Vector + RRF (~100 Token): Semantic search  
- + LLM Rerank (~400 Token): Best quality

Returns matching memories with scores and snippets.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["auto", "bm25", "vector", "hybrid"],
                        "default": "auto",
                        "description": "Search mode (auto=hybrid if vector enabled)"
                    },
                    "top_k": {
                        "type": "number",
                        "default": 5,
                        "description": "Number of results"
                    },
                    "use_rerank": {
                        "type": "boolean",
                        "default": False,
                        "description": "Enable LLM reranking for better quality"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="memory_store",
            description="""Store a new memory with category and importance.

Categories:
- preference: User preferences
- fact: Important facts
- decision: Decisions made
- entity: People, projects, things
- learning: Lessons learned
- other: General memories""",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Memory content"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["preference", "fact", "decision", "entity", "learning", "other"],
                        "default": "other",
                        "description": "Memory category"
                    },
                    "importance": {
                        "type": "number",
                        "default": 0.5,
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Importance score (0-1)"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="memory_status",
            description="""Get unified-memory system status.

Returns:
- Total memories count
- Index status (BM25 terms, vector status)
- Configuration (vector enabled, LLM rerank)""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="memory_config",
            description="""View or update QMD search configuration.

Config options:
- use_vector: Enable vector search
- use_llm_rerank: Enable LLM reranking
- llm_model: Model for reranking""",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["get", "set"],
                        "default": "get",
                        "description": "Get current config or set new values"
                    },
                    "config": {
                        "type": "object",
                        "description": "Config to set (only for action=set)"
                    }
                }
            }
        ),
        Tool(
            name="memory_health",
            description="""Check memory system health.

Analyzes:
- Orphaned memories (no relations)
- Contradictions
- Redundancy
- Outdated memories

Returns health score and recommendations.""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """执行工具调用"""
    try:
        if name == "memory_search":
            query = arguments.get("query", "")
            mode = arguments.get("mode", "auto")
            top_k = arguments.get("top_k", 5)
            use_rerank = arguments.get("use_rerank", False)
            
            # 如果启用重排，临时创建新搜索器
            if use_rerank:
                config = load_config()
                s = QMDSearch(
                    use_vector=config.get("use_vector", True),
                    use_llm_rerank=True,
                    llm_model=config.get("llm_model", "qwen2.5:0.5b")
                )
            else:
                s = get_searcher()
            
            results = s.search(query, mode=mode, top_k=top_k)
            output = format_search_results(results, query)
            
            return [TextContent(type="text", text=output)]
        
        elif name == "memory_store":
            text = arguments.get("text", "")
            category = arguments.get("category", "other")
            importance = arguments.get("importance", 0.5)
            
            # 存储到向量库
            from memory import store_memory
            memory_id = store_memory(text, category=category, importance=importance)
            
            output = f"✅ Memory stored successfully\nID: {memory_id}\nCategory: {category}\nImportance: {importance}"
            
            # 重置搜索器以重新索引
            global searcher
            searcher = None
            
            return [TextContent(type="text", text=output)]
        
        elif name == "memory_status":
            s = get_searcher()
            s.index()
            
            config = load_config()
            
            output = f"""📊 Unified Memory Status

Total Memories: {len(s._documents)}
BM25 Terms: {len(s.bm25.inverted_index)}

Configuration:
- Vector Search: {'✅' if config.get('use_vector', True) else '❌'}
- LLM Rerank: {'✅' if config.get('use_llm_rerank', False) else '❌'}
- Rerank Model: {config.get('llm_model', 'qwen2.5:0.5b')}

Vector DB: {VECTOR_DB_DIR}
"""
            return [TextContent(type="text", text=output)]
        
        elif name == "memory_config":
            action = arguments.get("action", "get")
            
            if action == "get":
                config = load_config()
                output = f"📋 Current Config:\n{json.dumps(config, indent=2)}"
            else:
                new_config = arguments.get("config", {})
                config_file = MEMORY_DIR / "qmd_config.json"
                
                # 合并配置
                current = load_config()
                current.update(new_config)
                
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(current, f, indent=2)
                
                # 重置搜索器
                global searcher
                searcher = None
                
                output = f"✅ Config updated:\n{json.dumps(current, indent=2)}"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "memory_health":
            from memory_health import health_check
            report = health_check()
            
            output = f"""🏥 Memory Health Report

Health Score: {report.get('score', 0)}/100

Issues:
- Orphaned: {report.get('orphaned', 0)}
- Contradictions: {report.get('contradictions', 0)}
- Redundant: {report.get('redundant', 0)}
- Outdated: {report.get('outdated', 0)}

Recommendations:
{chr(10).join('- ' + r for r in report.get('recommendations', []))}
"""
            return [TextContent(type="text", text=output)]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ============ MCP Resources ============

@app.list_resources()
async def list_resources() -> list[Resource]:
    """列出可用资源"""
    s = get_searcher()
    s.index()
    
    resources = []
    
    # 每个记忆作为一个资源
    for doc in s._documents[:20]:  # 限制前20个
        doc_id = doc.get("id", "")
        text = doc.get("text", "")[:50]
        category = doc.get("category", "unknown")
        
        resources.append(Resource(
            uri=f"memory://{doc_id}",
            name=f"[{category}] {text}...",
            mimeType="text/plain",
            description=doc.get("text", "")[:200]
        ))
    
    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    """读取资源内容"""
    if not uri.startswith("memory://"):
        raise ValueError(f"Invalid URI scheme: {uri}")
    
    doc_id = uri[9:]  # 去掉 "memory://"
    
    s = get_searcher()
    s.index()
    
    if doc_id in s._doc_map:
        doc = s._doc_map[doc_id]
        return json.dumps(doc, indent=2, ensure_ascii=False)
    else:
        raise ValueError(f"Memory not found: {doc_id}")


# ============ 启动服务器 ============

async def run():
    """运行 MCP 服务器"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """入口"""
    if not MCP_AVAILABLE:
        sys.exit(1)
    
    asyncio.run(run())


if __name__ == "__main__":
    main()
