#!/usr/bin/env python3
"""
MCP Server for Unified Memory
实现 Model Context Protocol，支持 Claude Desktop / Claude Code 无缝集成

暴露工具:
- memory_search: 混合搜索（BM25 + 向量 + HyDe）
- memory_store: 存储记忆
- memory_context: Context Tree 操作
- memory_health: 健康检查
- memory_qa: 智能问答

Usage:
    # stdio 模式 (默认)
    python mcp_server.py
    
    # HTTP 模式
    python mcp_server.py --http --port 8181
"""

import argparse
import asyncio
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# 添加脚本目录到 path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# 导入核心模块
from unified_memory import (
    store_to_memory, unified_query, get_status,
    ImportanceScorer, load_all_memories, OntologyGraph,
    ONTOLOGY_DIR, MEMORY_DIR
)
from memory_hyde import hyde_search, triple_search
from memory_context import ContextTree, search_with_context

# ============================================================
# MCP Protocol Implementation
# ============================================================

class MCPServer:
    """MCP Server 实现"""
    
    def __init__(self):
        self.name = "unified-memory"
        self.version = "1.0.0"
        self.tools = self._define_tools()
        self.context_tree = ContextTree()
    
    def _define_tools(self) -> List[Dict]:
        """定义 MCP 工具"""
        return [
            {
                "name": "memory_search",
                "description": "搜索记忆 - 支持三种模式: lex (关键词), vec (向量), hyde (假设文档嵌入)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询"
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["lex", "vec", "hyde", "hybrid"],
                            "default": "hybrid",
                            "description": "搜索模式: lex=BM25, vec=向量, hyde=假设文档, hybrid=混合"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 5,
                            "description": "返回结果数量"
                        },
                        "min_score": {
                            "type": "number",
                            "default": 0.3,
                            "description": "最小相关性分数"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "memory_store",
                "description": "存储记忆到长期存储，支持自动分类和重要性评分",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "记忆内容"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["preference", "fact", "decision", "entity", "reflection", "other"],
                            "default": "fact",
                            "description": "记忆分类"
                        },
                        "context_path": {
                            "type": "string",
                            "description": "Context Tree 路径，如 'user:刘总' 或 'project:官网重构'"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "标签列表"
                        }
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "memory_context",
                "description": "Context Tree 操作 - 管理记忆的层级上下文关系",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["add", "get", "list", "search"],
                            "description": "操作类型"
                        },
                        "path": {
                            "type": "string",
                            "description": "Context 路径 (如 'qmd://notes')"
                        },
                        "description": {
                            "type": "string",
                            "description": "Context 描述 (add 时使用)"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "memory_health",
                "description": "获取记忆系统健康状态和统计信息",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "memory_qa",
                "description": "基于记忆的智能问答，使用 LLM 综合检索结果生成答案",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "问题"
                        },
                        "context_limit": {
                            "type": "integer",
                            "default": 5,
                            "description": "用于回答的上下文记忆数量"
                        }
                    },
                    "required": ["question"]
                }
            },
            {
                "name": "memory_graph",
                "description": "知识图谱操作 - 查看实体关系网络",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["traverse", "list", "search"],
                            "default": "list"
                        },
                        "entity_id": {
                            "type": "string",
                            "description": "实体 ID (traverse 时使用)"
                        },
                        "depth": {
                            "type": "integer",
                            "default": 2,
                            "description": "遍历深度"
                        },
                        "entity_type": {
                            "type": "string",
                            "description": "实体类型筛选"
                        }
                    },
                    "required": ["action"]
                }
            }
        ]
    
    async def handle_request(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": self.name,
                            "version": self.version
                        }
                    }
                }
            
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": self.tools
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await self._execute_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False, indent=2)
                            }
                        ]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown method: {method}"
                    }
                }
        
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": str(e),
                    "data": traceback.format_exc()
                }
            }
    
    async def _execute_tool(self, tool_name: str, args: Dict) -> Dict:
        """执行工具调用"""
        
        if tool_name == "memory_search":
            query = args.get("query", "")
            mode = args.get("mode", "hybrid")
            limit = args.get("limit", 5)
            min_score = args.get("min_score", 0.3)
            
            if mode == "hyde":
                results = hyde_search(query, limit)
            elif mode == "hybrid":
                results = triple_search(query, limit)
            else:
                # 使用 Context Tree 增强搜索
                results = search_with_context(query, mode, limit, self.context_tree)
            
            # 过滤低分结果
            if min_score > 0:
                results = [r for r in results if r.get("score", 1) >= min_score]
            
            return {
                "success": True,
                "mode": mode,
                "count": len(results),
                "results": results
            }
        
        elif tool_name == "memory_store":
            content = args.get("content", "")
            category = args.get("category", "fact")
            context_path = args.get("context_path")
            tags = args.get("tags", [])
            
            # 存储到记忆
            result = store_to_memory(content, category)
            
            # 如果有 context_path，添加到 Context Tree
            if context_path:
                mem_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                self.context_tree.add_memory(context_path, mem_id, content, category)
            
            return {
                "success": True,
                "message": result,
                "category": category,
                "context_path": context_path
            }
        
        elif tool_name == "memory_context":
            action = args.get("action")
            path = args.get("path", "")
            description = args.get("description", "")
            
            if action == "add":
                self.context_tree.add_context(path, description)
                return {"success": True, "message": f"Context added: {path}"}
            
            elif action == "get":
                ctx = self.context_tree.get_context(path)
                return {"success": True, "context": ctx}
            
            elif action == "list":
                contexts = self.context_tree.list_contexts()
                return {"success": True, "contexts": contexts}
            
            elif action == "search":
                results = self.context_tree.search_contexts(path)
                return {"success": True, "results": results}
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        
        elif tool_name == "memory_health":
            status = get_status()
            return {
                "success": True,
                "status": status
            }
        
        elif tool_name == "memory_qa":
            question = args.get("question", "")
            context_limit = args.get("context_limit", 5)
            
            # 搜索相关记忆
            memories = triple_search(question, context_limit)
            
            # 如果有 Ollama，使用 LLM 生成答案
            answer = self._generate_answer(question, memories)
            
            return {
                "success": True,
                "question": question,
                "answer": answer,
                "sources": memories
            }
        
        elif tool_name == "memory_graph":
            action = args.get("action", "list")
            entity_id = args.get("entity_id", "")
            depth = args.get("depth", 2)
            entity_type = args.get("entity_type", "")
            
            graph = OntologyGraph(ONTOLOGY_DIR / "graph.jsonl")
            
            if action == "traverse" and entity_id:
                result = graph.traverse(entity_id, depth)
                return {"success": True, "graph": result}
            
            elif action == "list":
                entities = graph.get_entities_by_type(entity_type) if entity_type else list(graph.entities.values())
                return {
                    "success": True,
                    "count": len(entities),
                    "entities": [{"id": e.get("id"), "type": e.get("type"), "name": e.get("properties", {}).get("name")} for e in entities[:50]]
                }
            
            elif action == "search":
                results = graph.search(entity_id, 10)
                return {"success": True, "results": results}
            
            else:
                return {"success": False, "error": f"Unknown action or missing entity_id"}
        
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    
    def _generate_answer(self, question: str, memories: List[Dict]) -> str:
        """基于记忆生成答案"""
        if not memories:
            return "未找到相关记忆。"
        
        # 简单拼接相关记忆
        context = "\n".join([f"- {m.get('text', m.get('content', ''))}" for m in memories[:5]])
        
        # 如果有 Ollama，可以调用 LLM
        # 这里先用简单的模板回复
        return f"基于 {len(memories)} 条相关记忆:\n{context}"


# ============================================================
# stdio 模式
# ============================================================

async def run_stdio():
    """stdio 模式运行"""
    server = MCPServer()
    
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            request = json.loads(line.strip())
            response = await server.handle_request(request)
            
            print(json.dumps(response, ensure_ascii=False), flush=True)
        
        except json.JSONDecodeError as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"}
            }), flush=True)
        
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {e}"}
            }), flush=True)


# ============================================================
# HTTP 模式
# ============================================================

async def run_http(port: int):
    """HTTP 模式运行"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    
    server_instance = MCPServer()
    
    class MCPHTTPHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path == "/mcp":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                
                try:
                    request = json.loads(body)
                    
                    # 在事件循环中执行
                    loop = asyncio.new_event_loop()
                    response = loop.run_until_complete(server_instance.handle_request(request))
                    loop.close()
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
                
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            
            else:
                self.send_response(404)
                self.end_headers()
        
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "timestamp": datetime.now().isoformat()}).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
        
        def log_message(self, format, *args):
            print(f"[MCP HTTP] {args[0]}", file=sys.stderr)
    
    httpd = HTTPServer(("0.0.0.0", port), MCPHTTPHandler)
    print(f"✅ MCP Server running on http://0.0.0.0:{port}/mcp", file=sys.stderr)
    print(f"   Health check: http://0.0.0.0:{port}/health", file=sys.stderr)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...", file=sys.stderr)
        httpd.shutdown()


def main():
    parser = argparse.ArgumentParser(description="Unified Memory MCP Server")
    parser.add_argument("--http", action="store_true", help="Run in HTTP mode")
    parser.add_argument("--port", type=int, default=8181, help="HTTP port (default: 8181)")
    args = parser.parse_args()
    
    if args.http:
        asyncio.run(run_http(args.port))
    else:
        asyncio.run(run_stdio())


if __name__ == "__main__":
    main()
