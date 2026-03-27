#!/usr/bin/env python3
"""
Simple HTTP Server - Agent Collaboration System Web UI

无需 FastAPI，使用 Python 内置 http.server

启动:
    python3 scripts/simple_server.py --port 8080

访问:
    http://localhost:8080
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import argparse

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from agent_collab_system import AgentCollaborationSystem


# ===== 初始化系统 =====

system = AgentCollaborationSystem()


# ===== HTTP 处理器 =====

class APIHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        if path == "/" or path == "/ui":
            self.send_html(get_dashboard_html())
        
        elif path == "/api/agents":
            agents = system.list_agents()
            self.send_json({
                "count": len(agents),
                "agents": [a.__dict__ for a in agents]
            })
        
        elif path.startswith("/api/agents/"):
            agent_id = path.split("/")[-1]
            agent = system.get_agent(agent_id)
            if agent:
                self.send_json(agent.__dict__)
            else:
                self.send_error(404, "Agent not found")
        
        elif path == "/api/tasks":
            status = query.get("status", [None])[0]
            tasks = system.list_tasks(status)
            self.send_json({
                "count": len(tasks),
                "tasks": [t.__dict__ for t in tasks]
            })
        
        elif path == "/api/stats":
            self.send_json(system.get_stats())
        
        elif path == "/api/health":
            self.send_json({
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            })
        
        else:
            self.send_error(404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        # 读取 body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"
        
        try:
            data = json.loads(body)
        except:
            data = {}
        
        if path == "/api/agents/register":
            agent = system.register_agent(
                data.get("agent_id"),
                data.get("name"),
                data.get("role"),
                data.get("skills", [])
            )
            self.send_json({"status": "success", "agent": agent.__dict__})
        
        elif path == "/api/tasks":
            task = system.add_task(
                data.get("task_id"),
                data.get("task_type"),
                data.get("description"),
                data.get("required_skills", []),
                data.get("priority", "normal")
            )
            self.send_json({"status": "success", "task": task.__dict__})
        
        elif path == "/api/tasks/assign":
            success = system.assign_task(
                data.get("task_id"),
                data.get("agent_id")
            )
            if success:
                self.send_json({"status": "success"})
            else:
                self.send_error(400, "Assignment failed")
        
        elif path == "/api/tasks/complete":
            system.complete_task(data.get("task_id"), data.get("result"))
            self.send_json({"status": "success"})
        
        elif path == "/api/conflicts/check":
            conflicts = system.detect_conflicts()
            self.send_json({
                "detected": len(conflicts),
                "conflicts": [c.__dict__ for c in conflicts]
            })
        
        elif path == "/api/decisions":
            decision = system.make_decision(
                data.get("context"),
                data.get("options", []),
                data.get("criteria", []),
                data.get("weights")
            )
            self.send_json(decision)
        
        elif path == "/api/broadcast":
            system.broadcast(
                data.get("from_agent"),
                data.get("event_type"),
                data.get("data", {})
            )
            self.send_json({"status": "success"})
        
        else:
            self.send_error(404)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        # 自定义日志格式
        print(f"📡 {self.address_string()} - {format % args}")


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
        .status { padding: 8px 20px; border-radius: 20px; font-weight: 600; background: #10b981; color: white; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }
        .card {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .card h2 { font-size: 18px; margin-bottom: 20px; color: #667eea; }
        .stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .stat-item {
            background: #f8fafc;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value { font-size: 28px; font-weight: 700; color: #667eea; }
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
        .workload-bar { width: 100px; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }
        .workload-fill { height: 100%; background: linear-gradient(135deg, #667eea, #764ba2); }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            cursor: pointer;
            font-weight: 600;
            width: 100%;
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
        .log-error { color: #f87171; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Agent Collaboration System</h1>
            <span class="status">● v3.1</span>
        </header>
        
        <div class="grid">
            <div class="card">
                <h2>📊 系统状态</h2>
                <div class="stat-grid">
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
                <input type="text" id="taskId" placeholder="任务 ID (如: task_002)">
                <input type="text" id="taskType" placeholder="任务类型 (如: development)">
                <input type="text" id="taskDesc" placeholder="任务描述">
                <select id="taskPriority">
                    <option value="low">低优先级</option>
                    <option value="normal" selected>中优先级</option>
                    <option value="high">高优先级</option>
                    <option value="critical">紧急</option>
                </select>
                <button class="btn" onclick="createTask()">创建任务</button>
            </div>
            
            <div class="card">
                <h2>🎯 智能决策</h2>
                <input type="text" id="decisionContext" placeholder="决策上下文 (如: 选择技术栈)">
                <input type="text" id="decisionOptions" placeholder="选项 (如: Python,Go,Node.js)">
                <input type="text" id="decisionCriteria" placeholder="标准 (如: 性能,效率,生态)">
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
                log('Agent 列表已加载', 'success');
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
            const options = document.getElementById('decisionOptions').value.split(',').map(s=>s.trim());
            const criteria = document.getElementById('decisionCriteria').value.split(',').map(s=>s.trim());
            
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
                log(`决策结果: ${data.chosen_option} (置信度: ${(data.confidence * 100).toFixed(0)}%)`, 'success');
            } catch(e) { log('决策失败', 'error'); }
        }
        
        // 初始化
        loadStats();
        loadAgents();
        setInterval(loadStats, 10000);
        log('Dashboard 初始化完成', 'success');
    </script>
</body>
</html>
"""


# ===== Main =====

def main():
    parser = argparse.ArgumentParser(description="Agent Collaboration Simple Server")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    args = parser.parse_args()
    
    print(f"\n🚀 启动服务器: http://{args.host}:{args.port}")
    print(f"🖥️  Web UI: http://{args.host}:{args.port}/ui")
    print(f"📡 API: http://{args.host}:{args.port}/api/...\n")
    
    server = HTTPServer((args.host, args.port), APIHandler)
    print("✅ 服务器运行中...\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")


if __name__ == "__main__":
    main()
