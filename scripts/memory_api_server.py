#!/usr/bin/env python3
"""
RESTful API 服务 - Memory API Server

提供 HTTP API 接口
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading


WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"


class MemoryAPI:
    """记忆 API"""
    
    def __init__(self):
        self.port = 38421
        self.server = None
        self.server_thread = None
        
        # 延迟导入，避免启动慢
        self._memory = None
    
    def _get_memory(self):
        """懒加载记忆模块"""
        if self._memory is None:
            try:
                from memory_sqlite import get_sqlite_memory
                self._memory = get_sqlite_memory()
            except:
                self._memory = None
        return self._memory
    
    def handle_request(self, method: str, path: str, data: Dict = None) -> Dict:
        """
        处理请求
        """
        parsed = urlparse(path)
        path_parts = parsed.path.strip("/").split("/")
        
        # 路由
        if path_parts[0] == "memory":
            return self._handle_memory(method, path_parts[1:], data, parse_qs(parsed.query))
        
        elif path_parts[0] == "search":
            return self._handle_search(method, path_parts[1:], data, parse_qs(parsed.query))
        
        elif path_parts[0] == "stats":
            return self._handle_stats(method)
        
        elif path_parts[0] == "health":
            return {"status": "ok", "timestamp": datetime.now().isoformat()}
        
        return {"error": "Not found", "path": path}
    
    def _handle_memory(self, method: str, parts: List, data: Dict, query: Dict) -> Dict:
        """记忆 CRUD"""
        memory = self._get_memory()
        if not memory:
            return {"error": "Memory not available"}
        
        if method == "GET" and not parts:
            # 列表
            limit = int(query.get("limit", [10])[0])
            offset = int(query.get("offset", [0])[0])
            memories = memory.get_all(limit, offset)
            return {"memories": memories, "total": memory.count()}
        
        elif method == "GET" and parts:
            # 获取单个
            mem_id = parts[0]
            result = memory.get(mem_id)
            if result:
                return {"memory": result}
            return {"error": "Not found"}, 404
        
        elif method == "POST":
            # 创建
            if data:
                memory.store(data)
                return {"success": True, "memory": data}
            return {"error": "No data"}, 400
        
        elif method == "DELETE" and parts:
            # 删除
            mem_id = parts[0]
            success = memory.delete(mem_id)
            return {"success": success}
        
        return {"error": "Method not allowed"}
    
    def _handle_search(self, method: str, parts: List, data: Dict, query: Dict) -> Dict:
        """搜索"""
        memory = self._get_memory()
        if not memory:
            return {"error": "Memory not available"}
        
        q = query.get("q", [""])[0]
        if not q:
            return {"error": "No query"}, 400
        
        limit = int(query.get("limit", [10])[0])
        
        results = memory.search(q, limit)
        return {"results": results, "query": q, "count": len(results)}
    
    def _handle_stats(self, method: str) -> Dict:
        """统计"""
        memory = self._get_memory()
        if not memory:
            return {"error": "Memory not available"}
        
        return memory.get_stats()
    
    def start(self, port: int = None):
        """启动服务"""
        if port:
            self.port = port
        
        self.server = HTTPServer(("0.0.0.0", self.port), self._create_handler())
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        return self.port
    
    def stop(self):
        """停止服务"""
        if self.server:
            self.server.shutdown()
    
    def _create_handler(self):
        """创建请求处理器"""
        api = self
        
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                try:
                    result = api.handle_request("GET", self.path)
                    self._send_json(result)
                except Exception as e:
                    self._send_json({"error": str(e)}, 500)
            
            def do_POST(self):
                try:
                    content_length = int(self.headers.get("Content-Length", 0))
                    data = json.loads(self.rfile.read(content_length)) if content_length > 0 else None
                    result = api.handle_request("POST", self.path, data)
                    self._send_json(result)
                except Exception as e:
                    self._send_json({"error": str(e)}, 500)
            
            def do_DELETE(self):
                try:
                    result = api.handle_request("DELETE", self.path)
                    self._send_json(result)
                except Exception as e:
                    self._send_json({"error": str(e)}, 500)
            
            def _send_json(self, data, status=200):
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
            
            def log_message(self, format, *args):
                pass  # 静默日志
        
        return Handler


# 全局实例
_api = None

def get_memory_api() -> MemoryAPI:
    global _api
    if _api is None:
        _api = MemoryAPI()
    return _api


def start_api_server(port: int = 38421) -> int:
    """启动 API 服务"""
    api = get_memory_api()
    return api.start(port)


if __name__ == "__main__":
    print("=" * 50)
    print("RESTful API 服务测试")
    print("=" * 50)
    
    api = MemoryAPI()
    
    # 测试请求处理
    print("\n📡 测试请求:")
    
    # 健康检查
    result = api.handle_request("GET", "/health")
    print(f"  GET /health: {result}")
    
    # 统计
    result = api.handle_request("GET", "/stats")
    print(f"  GET /stats: {result}")
    
    # 创建记忆
    result = api.handle_request("POST", "/memory", {
        "id": "test_api",
        "text": "API 测试记忆",
        "category": "test"
    })
    print(f"  POST /memory: {result.get('success')}")
    
    # 搜索
    result = api.handle_request("GET", "/search?q=测试")
    print(f"  GET /search?q=测试: 找到 {result.get('count')} 条")
    
    # 列表
    result = api.handle_request("GET", "/memory?limit=5")
    print(f"  GET /memory?limit=5: {result.get('total')} 条")
    
    print("\n✅ API 服务测试完成")
