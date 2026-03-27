#!/usr/bin/env python3
"""
Memory HTTP Server - 统一记忆 HTTP 服务
提供高性能 HTTP API，支持模型常驻内存

功能:
- FastAPI 高性能服务
- Ollama embedding 模型常驻
- LanceDB 连接池
- 完整 RESTful API
- WebSocket 支持（可选）

Usage:
    # 启动服务
    python memory_server.py --port 38080
    
    # 后台运行
    python memory_server.py --port 38080 --daemon
    
    # API 调用
    curl -X POST http://localhost:38080/search -d '{"query":"用户偏好"}'
    curl -X POST http://localhost:38080/store -d '{"content":"测试内容"}'
"""

import argparse
import json
import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加脚本目录到 path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# ============================================================
# FastAPI 应用
# ============================================================

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Unified Memory Server",
    description="统一记忆系统 HTTP API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 请求模型
# ============================================================

class SearchRequest(BaseModel):
    query: str
    mode: str = "hybrid"
    limit: int = 5
    min_score: float = 0.3

class StoreRequest(BaseModel):
    content: str
    category: str = "fact"
    context_path: Optional[str] = None
    tags: List[str] = []

class ContextRequest(BaseModel):
    action: str
    path: Optional[str] = None
    description: Optional[str] = None
    parent: Optional[str] = None

class QARequest(BaseModel):
    question: str
    context_limit: int = 5

# ============================================================
# 全局状态
# ============================================================

class MemoryServer:
    """记忆服务器状态"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.ollama_available = False
        self.lancedb_available = False
        self.embedding_model = None
        self.db = None
        self.table = None
        
        # 延迟加载
        self._initialized = False
    
    def init(self):
        """延迟初始化"""
        if self._initialized:
            return
        
        # 检查 Ollama
        try:
            import requests
            r = requests.get("http://localhost:11434/api/tags", timeout=5)
            self.ollama_available = r.ok
        except:
            self.ollama_available = False
        
        # 初始化 LanceDB
        try:
            import lancedb
            db_path = Path.home() / ".openclaw" / "workspace" / "memory" / "vector"
            self.db = lancedb.connect(str(db_path))
            self.table = self.db.open_table("memories")
            self.lancedb_available = True
        except Exception as e:
            print(f"⚠️ LanceDB 初始化失败: {e}", file=sys.stderr)
            self.lancedb_available = False
        
        self._initialized = True
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """获取 embedding（复用连接）"""
        if not self.ollama_available:
            return None
        
        try:
            import requests
            response = requests.post(
                "http://localhost:11434/api/embeddings",
                json={"model": "nomic-embed-text:latest", "prompt": text},
                timeout=30
            )
            
            if response.ok:
                return response.json().get("embedding")
        except:
            pass
        
        return None
    
    def health(self) -> Dict:
        """健康检查"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "status": "healthy",
            "uptime_seconds": uptime,
            "uptime_human": self._format_uptime(uptime),
            "ollama": "ok" if self.ollama_available else "unavailable",
            "lancedb": "ok" if self.lancedb_available else "unavailable",
            "timestamp": datetime.now().isoformat()
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"


# 全局实例
server = MemoryServer()


# ============================================================
# API 路由
# ============================================================

@app.on_event("startup")
async def startup():
    """启动时初始化"""
    server.init()
    print(f"✅ Memory Server started at {datetime.now().isoformat()}", file=sys.stderr)


@app.get("/")
async def root():
    """根路由"""
    return {
        "name": "Unified Memory Server",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return server.health()


@app.post("/search")
async def search(request: SearchRequest):
    """
    搜索记忆
    
    - mode: lex (BM25), vec (向量), hyde (假设文档), hybrid (混合)
    """
    server.init()
    
    try:
        from memory_hyde import lex_search, vec_search, hyde_search, triple_search
        
        if request.mode == "lex":
            results = lex_search(request.query, request.limit)
        elif request.mode == "vec":
            results = vec_search(request.query, request.limit)
        elif request.mode == "hyde":
            results = hyde_search(request.query, request.limit)
        else:
            results = triple_search(request.query, request.limit)
        
        # 过滤低分
        if request.min_score > 0:
            results = [r for r in results if r.get("score", r.get("rrf_score", 1)) >= request.min_score]
        
        return {
            "success": True,
            "mode": request.mode,
            "count": len(results),
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/store")
async def store(request: StoreRequest):
    """存储记忆"""
    server.init()
    
    try:
        from unified_memory import store_to_memory
        
        result = store_to_memory(request.content, request.category)
        
        return {
            "success": True,
            "message": result,
            "category": request.category
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/context")
async def context(request: ContextRequest):
    """Context Tree 操作"""
    from memory_context import ContextTree
    
    tree = ContextTree()
    
    try:
        if request.action == "add":
            tree.add_context(request.path, request.description or "", request.parent or "")
            return {"success": True, "message": f"Context added: {request.path}"}
        
        elif request.action == "get":
            ctx = tree.get_context(request.path)
            return {"success": True, "context": ctx}
        
        elif request.action == "list":
            contexts = tree.list_contexts()
            return {"success": True, "contexts": contexts}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/qa")
async def qa(request: QARequest):
    """智能问答"""
    server.init()
    
    try:
        from memory_hyde import triple_search
        
        # 搜索相关记忆
        memories = triple_search(request.question, request.context_limit)
        
        # TODO: 调用 LLM 生成答案
        answer = f"基于 {len(memories)} 条相关记忆:\n"
        answer += "\n".join([f"- {m.get('text', '')[:50]}..." for m in memories[:3]])
        
        return {
            "success": True,
            "question": request.question,
            "answer": answer,
            "sources": memories
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def status():
    """系统状态"""
    from unified_memory import get_status
    
    return {
        "success": True,
        "status": get_status(),
        "server": server.health()
    }


# ============================================================
# WebSocket 支持（可选）
# ============================================================

from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 实时搜索"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                request = json.loads(data)
                query = request.get("query", "")
                mode = request.get("mode", "hybrid")
                limit = request.get("limit", 5)
                
                # 搜索
                from memory_hyde import triple_search
                results = triple_search(query, limit)
                
                # 返回结果
                await websocket.send_json({
                    "success": True,
                    "query": query,
                    "results": results
                })
            
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
            
            except Exception as e:
                await websocket.send_json({"error": str(e)})
    
    except WebSocketDisconnect:
        pass


# ============================================================
# 主入口
# ============================================================

def run_server(port: int, host: str = "0.0.0.0"):
    """运行 HTTP 服务"""
    import uvicorn
    
    print(f"🚀 Starting Memory Server on http://{host}:{port}", file=sys.stderr)
    print(f"   API Docs: http://{host}:{port}/docs", file=sys.stderr)
    print(f"   Health: http://{host}:{port}/health", file=sys.stderr)
    
    uvicorn.run(app, host=host, port=port, log_level="info")


def run_daemon(port: int, pid_file: str = None):
    """后台运行"""
    import subprocess
    
    if pid_file is None:
        pid_file = str(Path.home() / ".cache" / "memory-server" / "server.pid")
    
    pid_path = Path(pid_file)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 检查是否已运行
    if pid_path.exists():
        try:
            with open(pid_path, "r") as f:
                old_pid = int(f.read().strip())
            
            # 检查进程是否存在
            os.kill(old_pid, 0)
            print(f"⚠️ Server already running (PID {old_pid})", file=sys.stderr)
            return
        except:
            pass  # 进程不存在，继续启动
    
    # 启动后台进程
    cmd = [sys.executable, __file__, "--port", str(port)]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    
    # 写入 PID
    with open(pid_path, "w") as f:
        f.write(str(process.pid))
    
    print(f"✅ Server started in background (PID {process.pid})", file=sys.stderr)
    print(f"   PID file: {pid_file}", file=sys.stderr)


def stop_daemon(pid_file: str = None):
    """停止后台服务"""
    if pid_file is None:
        pid_file = str(Path.home() / ".cache" / "memory-server" / "server.pid")
    
    pid_path = Path(pid_file)
    
    if not pid_path.exists():
        print("⚠️ No PID file found", file=sys.stderr)
        return
    
    try:
        with open(pid_path, "r") as f:
            pid = int(f.read().strip())
        
        os.kill(pid, signal.SIGTERM)
        pid_path.unlink()
        print(f"✅ Server stopped (PID {pid})", file=sys.stderr)
    
    except Exception as e:
        print(f"❌ Failed to stop server: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Memory HTTP Server")
    parser.add_argument("--port", type=int, default=38080, help="HTTP port")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP host")
    parser.add_argument("--daemon", action="store_true", help="Run in background")
    parser.add_argument("--stop", action="store_true", help="Stop daemon")
    args = parser.parse_args()
    
    if args.stop:
        stop_daemon()
    elif args.daemon:
        run_daemon(args.port)
    else:
        run_server(args.port, args.host)


if __name__ == "__main__":
    main()
