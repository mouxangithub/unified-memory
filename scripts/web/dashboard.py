#!/usr/bin/env python3
"""
Web Dashboard - 可视化界面

启动:
    python dashboard.py --port 38080

访问:
    http://localhost:38080/
    http://localhost:38080/graph
    http://localhost:38080/workflow
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("⚠️  FastAPI 未安装，请运行: pip install fastapi uvicorn")


# 创建应用
app = FastAPI(
    title="统一记忆系统",
    description="AI Agent 记忆管理系统",
    version="1.1.0"
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
# API 端点
# ============================================================

@app.get("/")
async def index():
    """主页"""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/graph")
async def graph_page():
    """知识图谱页面"""
    return HTMLResponse(content=GRAPH_HTML)


@app.get("/workflow")
async def workflow_page():
    """工作流页面"""
    return HTMLResponse(content=WORKFLOW_HTML)


@app.get("/api/status")
async def get_status():
    """系统状态"""
    try:
        from unified_interface import AgentCollab, SOPWorkflow
        
        ac = AgentCollab()
        stats = ac.get_stats()
        
        wf = SOPWorkflow()
        sops = wf.list_sops()
        
        return {
            "status": "ok",
            "agent_count": stats.get("agent_count", 0),
            "task_count": stats.get("task_count", 0),
            "sop_count": len(sops),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/memories")
async def list_memories(limit: int = 20):
    """列出记忆"""
    try:
        from unified_interface import HybridSearch
        
        search = HybridSearch()
        # 使用空查询获取所有
        results = search.search("", mode="lex", limit=limit)
        
        return {
            "memories": results,
            "count": len(results)
        }
    except Exception as e:
        return {
            "memories": [],
            "error": str(e)
        }


@app.post("/api/memories")
async def store_memory(request: Request):
    """存储记忆"""
    try:
        data = await request.json()
        text = data.get("text", "")
        category = data.get("category", "fact")
        
        from unified_interface import UnifiedMemory
        um = UnifiedMemory()
        
        memory_id = um.quick_store(text, category=category)
        
        return {
            "status": "ok",
            "memory_id": memory_id
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/search")
async def search_memories(q: str, mode: str = "hybrid", limit: int = 10):
    """搜索记忆"""
    try:
        from unified_interface import HybridSearch
        
        search = HybridSearch()
        results = search.search(q, mode=mode, limit=limit)
        
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        return {
            "query": q,
            "results": [],
            "error": str(e)
        }


@app.get("/api/graph")
async def get_graph():
    """获取知识图谱"""
    try:
        from unified_interface import MemoryManager
        
        mm = MemoryManager()
        graph = mm.get_graph()
        
        return graph
    except Exception as e:
        return {
            "entities": [],
            "relations": [],
            "error": str(e)
        }


@app.get("/api/agents")
async def list_agents():
    """列出 Agent"""
    try:
        from unified_interface import AgentCollab
        
        ac = AgentCollab()
        agents = ac.list_agents()
        
        return {
            "agents": agents,
            "count": len(agents)
        }
    except Exception as e:
        return {
            "agents": [],
            "error": str(e)
        }


@app.get("/api/sops")
async def list_sops():
    """列出 SOP"""
    try:
        from unified_interface import SOPWorkflow
        
        wf = SOPWorkflow()
        sops = wf.list_sops()
        
        return {
            "sops": sops,
            "count": len(sops)
        }
    except Exception as e:
        return {
            "sops": [],
            "error": str(e)
        }


# ============================================================
# HTML 页面
# ============================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>统一记忆系统 - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }
        h1 {
            font-size: 2rem;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        nav a {
            color: #94a3b8;
            text-decoration: none;
            margin-left: 1.5rem;
            transition: color 0.3s;
        }
        nav a:hover { color: #3b82f6; }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #334155;
        }
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #3b82f6;
        }
        .stat-label {
            color: #94a3b8;
            margin-top: 0.5rem;
        }
        
        .search-box {
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }
        .search-input {
            width: 100%;
            padding: 1rem;
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            color: #e2e8f0;
            font-size: 1rem;
        }
        .search-input:focus {
            outline: none;
            border-color: #3b82f6;
        }
        
        .memories-list {
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
        }
        .memory-item {
            padding: 1rem;
            border-bottom: 1px solid #334155;
        }
        .memory-item:last-child { border-bottom: none; }
        .memory-text {
            color: #e2e8f0;
            margin-bottom: 0.5rem;
        }
        .memory-meta {
            font-size: 0.875rem;
            color: #64748b;
        }
        
        .btn {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: background 0.3s;
        }
        .btn:hover { background: #2563eb; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧠 统一记忆系统</h1>
            <nav>
                <a href="/">Dashboard</a>
                <a href="/graph">知识图谱</a>
                <a href="/workflow">工作流</a>
            </nav>
        </header>
        
        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-value" id="agent-count">-</div>
                <div class="stat-label">Agent 数量</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="task-count">-</div>
                <div class="stat-label">任务数量</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="sop-count">-</div>
                <div class="stat-label">SOP 工作流</div>
            </div>
        </div>
        
        <div class="search-box">
            <input type="text" class="search-input" id="search-input" 
                   placeholder="搜索记忆..." onkeypress="handleSearch(event)">
        </div>
        
        <div class="memories-list">
            <h2 style="margin-bottom: 1rem;">最近记忆</h2>
            <div id="memories">
                <p style="color: #64748b;">加载中...</p>
            </div>
        </div>
    </div>
    
    <script>
        // 加载状态
        async function loadStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('agent-count').textContent = data.agent_count || 0;
                document.getElementById('task-count').textContent = data.task_count || 0;
                document.getElementById('sop-count').textContent = data.sop_count || 0;
            } catch (e) {
                console.error(e);
            }
        }
        
        // 加载记忆
        async function loadMemories() {
            try {
                const res = await fetch('/api/memories?limit=10');
                const data = await res.json();
                
                const container = document.getElementById('memories');
                if (data.memories && data.memories.length > 0) {
                    container.innerHTML = data.memories.map(m => `
                        <div class="memory-item">
                            <div class="memory-text">${m.text || JSON.stringify(m)}</div>
                            <div class="memory-meta">${m.category || ''}</div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<p style="color: #64748b;">暂无记忆</p>';
                }
            } catch (e) {
                console.error(e);
            }
        }
        
        // 搜索
        async function handleSearch(e) {
            if (e.key === 'Enter') {
                const query = e.target.value;
                const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                
                const container = document.getElementById('memories');
                if (data.results && data.results.length > 0) {
                    container.innerHTML = data.results.map(m => `
                        <div class="memory-item">
                            <div class="memory-text">${m.text || JSON.stringify(m)}</div>
                            <div class="memory-meta">分数: ${m.score || 0}</div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<p style="color: #64748b;">未找到结果</p>';
                }
            }
        }
        
        // 初始化
        loadStatus();
        loadMemories();
    </script>
</body>
</html>
"""

GRAPH_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>知识图谱 - 统一记忆系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }
        h1 {
            font-size: 2rem;
            background: linear-gradient(135deg, #10b981, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        nav a {
            color: #94a3b8;
            text-decoration: none;
            margin-left: 1.5rem;
        }
        nav a:hover { color: #3b82f6; }
        
        .graph-container {
            background: #1e293b;
            border-radius: 12px;
            padding: 2rem;
            min-height: 600px;
        }
        .node {
            display: inline-block;
            background: #3b82f6;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            margin: 0.5rem;
        }
        .relation {
            padding: 0.5rem;
            margin: 0.5rem;
            background: #334155;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 知识图谱</h1>
            <nav>
                <a href="/">Dashboard</a>
                <a href="/graph">知识图谱</a>
                <a href="/workflow">工作流</a>
            </nav>
        </header>
        
        <div class="graph-container" id="graph">
            <p style="color: #64748b;">加载中...</p>
        </div>
    </div>
    
    <script>
        async function loadGraph() {
            try {
                const res = await fetch('/api/graph');
                const data = await res.json();
                
                const container = document.getElementById('graph');
                let html = '';
                
                if (data.entities && data.entities.length > 0) {
                    html += '<h2>实体</h2>';
                    html += '<div>' + data.entities.map(e => 
                        `<span class="node">${e}</span>`
                    ).join('') + '</div>';
                }
                
                if (data.relations && data.relations.length > 0) {
                    html += '<h2 style="margin-top: 2rem;">关系</h2>';
                    html += data.relations.map(r => 
                        `<div class="relation">${r}</div>`
                    ).join('');
                }
                
                if (!html) {
                    html = '<p style="color: #64748b;">知识图谱为空</p>';
                }
                
                container.innerHTML = html;
            } catch (e) {
                console.error(e);
            }
        }
        
        loadGraph();
    </script>
</body>
</html>
"""

WORKFLOW_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>工作流 - 统一记忆系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }
        h1 {
            font-size: 2rem;
            background: linear-gradient(135deg, #f59e0b, #ef4444);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        nav a {
            color: #94a3b8;
            text-decoration: none;
            margin-left: 1.5rem;
        }
        nav a:hover { color: #3b82f6; }
        
        .sop-card {
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border: 1px solid #334155;
        }
        .sop-name {
            font-size: 1.25rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .sop-desc {
            color: #94a3b8;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚙️ SOP 工作流</h1>
            <nav>
                <a href="/">Dashboard</a>
                <a href="/graph">知识图谱</a>
                <a href="/workflow">工作流</a>
            </nav>
        </header>
        
        <div id="sops">
            <p style="color: #64748b;">加载中...</p>
        </div>
    </div>
    
    <script>
        async function loadSOPs() {
            try {
                const res = await fetch('/api/sops');
                const data = await res.json();
                
                const container = document.getElementById('sops');
                if (data.sops && data.sops.length > 0) {
                    container.innerHTML = data.sops.map(sop => `
                        <div class="sop-card">
                            <div class="sop-name">${sop}</div>
                            <div class="sop-desc">标准操作流程</div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<p style="color: #64748b;">暂无 SOP</p>';
                }
            } catch (e) {
                console.error(e);
            }
        }
        
        loadSOPs();
    </script>
</body>
</html>
"""


def main():
    """启动服务"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Web Dashboard")
    parser.add_argument("--port", type=int, default=38080, help="端口")
    parser.add_argument("--host", default="0.0.0.0", help="主机")
    
    args = parser.parse_args()
    
    print(f"🌐 启动 Web 服务: http://localhost:{args.port}")
    print()
    print("页面:")
    print(f"  Dashboard: http://localhost:{args.port}/")
    print(f"  知识图谱: http://localhost:{args.port}/graph")
    print(f"  工作流:   http://localhost:{args.port}/workflow")
    print(f"  API 文档: http://localhost:{args.port}/docs")
    print()
    print("按 Ctrl+C 停止")
    
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
