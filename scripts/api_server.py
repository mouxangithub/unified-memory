#!/usr/bin/env python3
"""
API Server - Agent Collaboration System RESTful API

提供完整的 HTTP API，支持远程调用和 Web UI

启动:
    python3 scripts/api_server.py --port 8080

API 文档:
    http://localhost:8080/docs
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, FileResponse
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("⚠️  FastAPI 未安装，请运行: pip install fastapi uvicorn")


# ===== 导入核心系统 =====

from agent_collab_system import AgentCollaborationSystem, Agent, Task, Conflict


# ===== API 数据模型 =====

if FASTAPI_AVAILABLE:
    class AgentRegister(BaseModel):
        agent_id: str
        name: str
        role: str
        skills: List[str] = []
    
    class TaskCreate(BaseModel):
        task_id: str
        task_type: str
        description: str
        required_skills: List[str] = []
        priority: str = "normal"
    
    class TaskAssign(BaseModel):
        task_id: str
        agent_id: str
    
    class DecisionRequest(BaseModel):
        context: str
        options: List[str]
        criteria: List[str]
        weights: Optional[Dict[str, float]] = None
    
    class BroadcastRequest(BaseModel):
        from_agent: str
        event_type: str
        data: Dict = {}


# ===== 创建应用 =====

if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Agent Collaboration System API",
        description="多 Agent 协作系统 RESTful API",
        version="3.1.0"
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 初始化系统
    system = AgentCollaborationSystem()
    
    # ===== 首页 =====
    
    @app.get("/", response_class=HTMLResponse)
    async def root():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Agent Collaboration System</title>
            <meta http-equiv="refresh" content="0;url=/ui">
        </head>
        <body>
            <h1>Agent Collaboration System API</h1>
            <p>Redirecting to <a href="/ui">Web UI</a>...</p>
            <p>API Docs: <a href="/docs">/docs</a></p>
        </body>
        </html>
        """
    
    # ===== Web UI =====
    
    @app.get("/ui", response_class=HTMLResponse)
    async def web_ui():
        return get_dashboard_html()
    
    # ===== Agent API =====
    
    @app.get("/api/agents")
    async def list_agents():
        """列出所有 Agent"""
        agents = system.list_agents()
        return {
            "count": len(agents),
            "agents": [a.__dict__ for a in agents]
        }
    
    @app.get("/api/agents/{agent_id}")
    async def get_agent(agent_id: str):
        """获取 Agent 详情"""
        agent = system.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent.__dict__
    
    @app.post("/api/agents/register")
    async def register_agent(req: AgentRegister):
        """注册 Agent"""
        agent = system.register_agent(req.agent_id, req.name, req.role, req.skills)
        return {"status": "success", "agent": agent.__dict__}
    
    # ===== Task API =====
    
    @app.get("/api/tasks")
    async def list_tasks(status: str = None):
        """列出任务"""
        tasks = system.list_tasks(status)
        return {
            "count": len(tasks),
            "tasks": [t.__dict__ for t in tasks]
        }
    
    @app.post("/api/tasks")
    async def create_task(req: TaskCreate):
        """创建任务"""
        task = system.add_task(req.task_id, req.task_type, req.description,
                              req.required_skills, req.priority)
        return {"status": "success", "task": task.__dict__}
    
    @app.post("/api/tasks/assign")
    async def assign_task(req: TaskAssign):
        """分配任务"""
        success = system.assign_task(req.task_id, req.agent_id)
        if not success:
            raise HTTPException(status_code=400, detail="Assignment failed")
        return {"status": "success", "task_id": req.task_id, "agent_id": req.agent_id}
    
    @app.post("/api/tasks/{task_id}/complete")
    async def complete_task(task_id: str, result: Dict = None):
        """完成任务"""
        system.complete_task(task_id, result)
        return {"status": "success", "task_id": task_id}
    
    # ===== Recommendation API =====
    
    @app.get("/api/recommend")
    async def recommend_agent(task_type: str, skills: str, strategy: str = "hybrid"):
        """推荐 Agent"""
        skills_list = skills.split(",") if skills else []
        recommendations = system.recommend_agent(task_type, skills_list, strategy)
        return {
            "recommendations": [
                {"agent": r[0].__dict__, "score": r[1]}
                for r in recommendations[:5]
            ]
        }
    
    # ===== Conflict API =====
    
    @app.get("/api/conflicts")
    async def list_conflicts(resolved: bool = None):
        """列出冲突"""
        conflicts = system.list_conflicts(resolved)
        return {
            "count": len(conflicts),
            "conflicts": [c.__dict__ for c in conflicts]
        }
    
    @app.post("/api/conflicts/check")
    async def check_conflicts():
        """检测冲突"""
        conflicts = system.detect_conflicts()
        return {
            "detected": len(conflicts),
            "conflicts": [c.__dict__ for c in conflicts]
        }
    
    # ===== Decision API =====
    
    @app.post("/api/decisions")
    async def make_decision(req: DecisionRequest):
        """智能决策"""
        decision = system.make_decision(req.context, req.options,
                                       req.criteria, req.weights)
        return decision
    
    # ===== Broadcast API =====
    
    @app.post("/api/broadcast")
    async def broadcast(req: BroadcastRequest):
        """广播事件"""
        system.broadcast(req.from_agent, req.event_type, req.data)
        return {"status": "success"}
    
    # ===== Stats API =====
    
    @app.get("/api/stats")
    async def get_stats():
        """获取统计"""
        return system.get_stats()
    
    @app.get("/api/health")
    async def health():
        """健康检查"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "agents": len(system.agents),
            "tasks": len(system.tasks)
        }


# ===== Dashboard HTML =====

def get_dashboard_html() -> str:
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Collaboration Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header {
            background: rgba(255,255,255,0.95);
            padding: 20px 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 {
            font-size: 24px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status { padding: 8px 20px; border-radius: 20px; font-weight: 600; }
        .status.online { background: #10b981; color: white; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }
        .card {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .card h2 {
            font-size: 18px;
            margin-bottom: 20px;
            color: #667eea;
        }
        .stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .stat-item {
            background: #f8fafc;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: #667eea;
        }
        .stat-label { font-size: 12px; color: #64748b; margin-top: 5px; }
        .agent-list { list-style: none; }
        .agent-item {
            display: flex;
            justify-content: space-between;
            padding: 15px;
            background: #f8fafc;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        .agent-name { font-weight: 600; }
        .agent-role { font-size: 12px; color: #64748b; }
        .workload-bar {
            width: 100px;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
        }
        .workload-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea, #764ba2);
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            cursor: pointer;
            font-weight: 600;
        }
        .btn:hover { transform: translateY(-2px); }
        input, select {
            padding: 10px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            width: 100%;
            margin-bottom: 10px;
        }
        .log {
            background: #1e293b;
            border-radius: 10px;
            padding: 15px;
            color: #e2e8f0;
            font-family: monospace;
            font-size: 12px;
            max-height: 200px;
            overflow-y: auto;
        }
        .log-entry { margin-bottom: 5px; }
        .log-time { color: #64748b; }
        .log-success { color: #34d399; }
        .log-info { color: #60a5fa; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Agent Collaboration System</h1>
            <span class="status online">● v3.1</span>
        </header>
        
        <div class="grid">
            <div class="card">
                <h2>📊 系统状态</h2>
                <div class="stat-grid" id="stats">
                    <div class="stat-item">
                        <div class="stat-value" id="agentCount">-</div>
                        <div class="stat-label">Agent 数量</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="taskCount">-</div>
                        <div class="stat-label">任务数量</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="completionRate">-</div>
                        <div class="stat-label">完成率</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="conflictCount">-</div>
                        <div class="stat-label">冲突数量</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>👥 Agent 团队</h2>
                <ul class="agent-list" id="agentList"></ul>
            </div>
            
            <div class="card">
                <h2>📋 创建任务</h2>
                <input type="text" id="taskId" placeholder="任务 ID">
                <input type="text" id="taskType" placeholder="任务类型">
                <input type="text" id="taskDesc" placeholder="任务描述">
                <select id="taskPriority">
                    <option value="low">低</option>
                    <option value="normal" selected>中</option>
                    <option value="high">高</option>
                    <option value="critical">紧急</option>
                </select>
                <button class="btn" onclick="createTask()">创建任务</button>
            </div>
            
            <div class="card">
                <h2>🎯 智能决策</h2>
                <input type="text" id="decisionContext" placeholder="决策上下文">
                <input type="text" id="decisionOptions" placeholder="选项（逗号分隔）">
                <input type="text" id="decisionCriteria" placeholder="标准（逗号分隔）">
                <button class="btn" onclick="makeDecision()">做出决策</button>
            </div>
        </div>
        
        <div class="grid">
            <div class="card" style="grid-column: 1/-1">
                <h2>📜 操作日志</h2>
                <div class="log" id="log"></div>
            </div>
        </div>
    </div>
    
    <script>
        const API = '/api';
        
        function log(msg, type='info') {
            const logEl = document.getElementById('log');
            const time = new Date().toLocaleTimeString();
            logEl.innerHTML += `<div class="log-entry"><span class="log-time">[${time}]</span> <span class="log-${type}">${msg}</span></div>`;
            logEl.scrollTop = logEl.scrollHeight;
        }
        
        async function loadStats() {
            try {
                const res = await fetch(`${API}/stats`);
                const data = await res.json();
                document.getElementById('agentCount').textContent = data.agents.total;
                document.getElementById('taskCount').textContent = data.tasks.total;
                document.getElementById('completionRate').textContent = (data.tasks.completion_rate * 100).toFixed(0) + '%';
                document.getElementById('conflictCount').textContent = data.conflicts.total;
            } catch(e) { log('加载统计失败', 'error'); }
        }
        
        async function loadAgents() {
            try {
                const res = await fetch(`${API}/agents`);
                const data = await res.json();
                const list = document.getElementById('agentList');
                list.innerHTML = data.agents.map(a => `
                    <li class="agent-item">
                        <div>
                            <div class="agent-name">${a.name}</div>
                            <div class="agent-role">${a.role} | 负载: ${(a.workload * 100).toFixed(0)}%</div>
                        </div>
                        <div class="workload-bar">
                            <div class="workload-fill" style="width: ${a.workload * 100}%"></div>
                        </div>
                    </li>
                `).join('');
                log('加载 Agent 列表成功', 'success');
            } catch(e) { log('加载 Agent 失败', 'error'); }
        }
        
        async function createTask() {
            const taskId = document.getElementById('taskId').value;
            const taskType = document.getElementById('taskType').value;
            const taskDesc = document.getElementById('taskDesc').value;
            const priority = document.getElementById('taskPriority').value;
            
            if (!taskId || !taskType || !taskDesc) {
                log('请填写完整信息', 'error');
                return;
            }
            
            try {
                const res = await fetch(`${API}/tasks`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        task_id: taskId,
                        task_type: taskType,
                        description: taskDesc,
                        priority: priority
                    })
                });
                const data = await res.json();
                log(`任务创建成功: ${taskId}`, 'success');
                loadStats();
            } catch(e) { log('创建任务失败', 'error'); }
        }
        
        async function makeDecision() {
            const context = document.getElementById('decisionContext').value;
            const options = document.getElementById('decisionOptions').value.split(',');
            const criteria = document.getElementById('decisionCriteria').value.split(',');
            
            if (!context || options.length < 2 || criteria.length < 1) {
                log('请填写完整决策信息', 'error');
                return;
            }
            
            try {
                const res = await fetch(`${API}/decisions`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({context, options, criteria})
                });
                const data = await res.json();
                log(`决策: ${data.chosen_option} (${(data.confidence * 100).toFixed(0)}%)`, 'success');
            } catch(e) { log('决策失败', 'error'); }
        }
        
        // 初始化
        loadStats();
        loadAgents();
        setInterval(loadStats, 10000);
    </script>
</body>
</html>
"""


# ===== CLI =====

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Agent Collaboration API Server")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--reload", action="store_true")
    
    args = parser.parse_args()
    
    if not FASTAPI_AVAILABLE:
        print("❌ 请先安装 FastAPI: pip install fastapi uvicorn")
        return
    
    print(f"\n🚀 启动 API 服务器: http://{args.host}:{args.port}")
    print(f"📖 API 文档: http://{args.host}:{args.port}/docs")
    print(f"🖥️  Web UI: http://{args.host}:{args.port}/ui\n")
    
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
