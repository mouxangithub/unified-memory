#!/usr/bin/env python3
"""
Web UI Server - 完善 Web UI

功能:
- 用户认证 (简化版)
- 持久化状态
- RESTful API
- WebSocket 实时推送
"""

import sys
import json
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


if FASTAPI_AVAILABLE:
    app = FastAPI(title="统一记忆系统", version="1.2.0")
    security = HTTPBearer()
    
    # ============ 数据模型 ============
    
    class User(BaseModel):
        username: str
        password: str
    
    class MemoryItem(BaseModel):
        text: str
        tags: list = []
        category: str = None
    
    class SearchQuery(BaseModel):
        query: str
        limit: int = 10
        mode: str = "hybrid"
    
    # ============ 用户管理 (简化版) ============
    
    # 用户存储 (生产环境应该用数据库)
    USERS_FILE = Path.home() / ".openclaw" / "workspace" / "memory" / "users.json"
    
    def load_users() -> Dict:
        if USERS_FILE.exists():
            return json.loads(USERS_FILE.read_text())
        return {}
    
    def save_users(users: Dict):
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2))
    
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_token(username: str) -> str:
        return secrets.token_urlsafe(32)
    
    # Token 存储
    TOKENS: Dict[str, str] = {}  # token -> username
    
    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        token = credentials.credentials
        if token not in TOKENS:
            raise HTTPException(status_code=401, detail="无效的 token")
        return TOKENS[token]
    
    # ============ API 路由 ============
    
    @app.post("/api/register")
    async def register(user: User):
        """注册用户"""
        users = load_users()
        
        if user.username in users:
            raise HTTPException(status_code=400, detail="用户已存在")
        
        users[user.username] = {
            "password": hash_password(user.password),
            "created_at": datetime.now().isoformat()
        }
        
        save_users(users)
        
        return {"message": "注册成功"}
    
    @app.post("/api/login")
    async def login(user: User):
        """登录"""
        users = load_users()
        
        if user.username not in users:
            raise HTTPException(status_code=401, detail="用户不存在")
        
        if users[user.username]["password"] != hash_password(user.password):
            raise HTTPException(status_code=401, detail="密码错误")
        
        # 生成 token
        token = create_token(user.username)
        TOKENS[token] = user.username
        
        return {"token": token, "username": user.username}
    
    @app.post("/api/logout")
    async def logout(username: str = Depends(verify_token)):
        """登出"""
        # 删除 token
        for token, user in list(TOKENS.items()):
            if user == username:
                del TOKENS[token]
        
        return {"message": "已登出"}
    
    @app.get("/api/user/me")
    async def get_user_info(username: str = Depends(verify_token)):
        """获取用户信息"""
        users = load_users()
        user = users.get(username, {})
        
        return {
            "username": username,
            "created_at": user.get("created_at")
        }
    
    # ============ 记忆 API ============
    
    @app.post("/api/memory")
    async def store_memory(item: MemoryItem, username: str = Depends(verify_token)):
        """存储记忆"""
        try:
            from agent_memory import AgentMemory
            memory = AgentMemory()
            memory.store(item.text, tags=item.tags)
            
            return {"message": "存储成功", "text": item.text[:50]}
        except Exception as e:
            return {"message": f"存储失败: {e}"}
    
    @app.post("/api/memory/search")
    async def search_memory(query: SearchQuery, username: str = Depends(verify_token)):
        """搜索记忆"""
        try:
            from resilience.error_fallback import ErrorFallback
            fallback = ErrorFallback()
            result = fallback.search_with_fallback(query.query, limit=query.limit)
            
            if result.success:
                return {"results": result.data, "level": result.level}
            else:
                return {"results": [], "error": result.error}
        except Exception as e:
            return {"results": [], "error": str(e)}
    
    @app.get("/api/memory/stats")
    async def memory_stats(username: str = Depends(verify_token)):
        """记忆统计"""
        try:
            from agent_memory import AgentMemory
            memory = AgentMemory()
            status = memory.status()
            
            return status
        except Exception as e:
            return {"error": str(e)}
    
    # ============ 系统 API ============
    
    @app.get("/api/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "users": len(load_users()),
            "active_tokens": len(TOKENS)
        }
    
    # ============ WebSocket ============
    
    class ConnectionManager:
        def __init__(self):
            self.active_connections: list[WebSocket] = []
        
        async def connect(self, websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
        
        def disconnect(self, websocket: WebSocket):
            self.active_connections.remove(websocket)
        
        async def broadcast(self, message: str):
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    pass
    
    manager = ConnectionManager()
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # 广播消息
                await manager.broadcast(f"Message: {data}")
        except WebSocketDisconnect:
            manager.disconnect(websocket)
    
    # ============ Web UI ============
    
    @app.get("/", response_class=HTMLResponse)
    async def index():
        return WEB_UI_HTML
    
    @app.get("/ui", response_class=HTMLResponse)
    async def ui():
        return WEB_UI_HTML


# Web UI HTML
WEB_UI_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>统一记忆系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }
        h1 {
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2rem;
        }
        .user-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .btn {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: white;
        }
        .btn-primary:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }
        .card {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        .auth-form {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        .auth-form input {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            border: 1px solid #334155;
            background: #1e293b;
            color: #e2e8f0;
            font-size: 1rem;
        }
        .tabs {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .tab {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            background: transparent;
            border: 1px solid #334155;
            color: #94a3b8;
            cursor: pointer;
        }
        .tab.active {
            background: #3b82f6;
            color: white;
            border-color: #3b82f6;
        }
        .search-box {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .search-box input {
            flex: 1;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            border: 1px solid #334155;
            background: #1e293b;
            color: #e2e8f0;
            font-size: 1rem;
        }
        .results {
            margin-top: 1rem;
        }
        .result-item {
            background: rgba(51, 65, 85, 0.5);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
        }
        .result-item h3 {
            margin-bottom: 0.5rem;
        }
        .result-item p {
            color: #94a3b8;
            font-size: 0.9rem;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .stat-card {
            background: rgba(51, 65, 85, 0.5);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stat-label {
            color: #94a3b8;
            font-size: 0.9rem;
        }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 统一记忆系统</h1>
            <div class="user-info">
                <span id="username-display"></span>
                <button class="btn btn-primary" id="auth-btn">登录</button>
            </div>
        </div>
        
        <!-- 登录/注册表单 -->
        <div class="card" id="auth-card">
            <div class="auth-form">
                <input type="text" id="username" placeholder="用户名">
                <input type="password" id="password" placeholder="密码">
                <button class="btn btn-primary" onclick="login()">登录</button>
                <button class="btn" onclick="register()">注册</button>
            </div>
        </div>
        
        <!-- 主界面 -->
        <div id="main-ui" class="hidden">
            <!-- 统计 -->
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-value" id="stat-total">0</div>
                    <div class="stat-label">总记忆</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="stat-vectors">0</div>
                    <div class="stat-label">向量数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="stat-categories">0</div>
                    <div class="stat-label">分类数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">✅</div>
                    <div class="stat-label">系统状态</div>
                </div>
            </div>
            
            <!-- 标签页 -->
            <div class="tabs">
                <button class="tab active" onclick="showTab('search')">搜索</button>
                <button class="tab" onclick="showTab('store')">存储</button>
            </div>
            
            <!-- 搜索 -->
            <div class="card" id="search-tab">
                <div class="search-box">
                    <input type="text" id="search-query" placeholder="搜索记忆...">
                    <button class="btn btn-primary" onclick="search()">搜索</button>
                </div>
                <div class="results" id="search-results"></div>
            </div>
            
            <!-- 存储 -->
            <div class="card hidden" id="store-tab">
                <textarea id="memory-text" style="width:100%;height:150px;padding:1rem;border-radius:8px;border:1px solid #334155;background:#1e293b;color:#e2e8f0;font-size:1rem;" placeholder="输入要存储的记忆..."></textarea>
                <div style="margin-top:1rem;">
                    <input type="text" id="memory-tags" placeholder="标签 (逗号分隔)" style="width:300px;padding:0.5rem 1rem;border-radius:8px;border:1px solid #334155;background:#1e293b;color:#e2e8f0;">
                    <button class="btn btn-primary" onclick="store()" style="margin-left:1rem;">存储</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const API_BASE = window.location.origin;
        let token = localStorage.getItem('token');
        let username = localStorage.getItem('username');
        
        // 初始化
        function init() {
            if (token) {
                document.getElementById('auth-card').classList.add('hidden');
                document.getElementById('main-ui').classList.remove('hidden');
                document.getElementById('username-display').textContent = username;
                document.getElementById('auth-btn').textContent = '登出';
                loadStats();
            }
        }
        
        // 登录
        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const res = await fetch(`${API_BASE}/api/login`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            
            const data = await res.json();
            
            if (data.token) {
                localStorage.setItem('token', data.token);
                localStorage.setItem('username', data.username);
                location.reload();
            } else {
                alert(data.detail || '登录失败');
            }
        }
        
        // 注册
        async function register() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const res = await fetch(`${API_BASE}/api/register`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            
            const data = await res.json();
            alert(data.message || data.detail);
        }
        
        // 加载统计
        async function loadStats() {
            try {
                const res = await fetch(`${API_BASE}/api/memory/stats`, {
                    headers: {'Authorization': `Bearer ${token}`}
                });
                const data = await res.json();
                
                document.getElementById('stat-total').textContent = data.total_memories || 0;
                document.getElementById('stat-vectors').textContent = data.vectors || 0;
            } catch (e) {
                console.error(e);
            }
        }
        
        // 搜索
        async function search() {
            const query = document.getElementById('search-query').value;
            
            const res = await fetch(`${API_BASE}/api/memory/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({query, limit: 10})
            });
            
            const data = await res.json();
            
            const resultsEl = document.getElementById('search-results');
            resultsEl.innerHTML = '';
            
            if (data.results && data.results.length > 0) {
                data.results.forEach(item => {
                    resultsEl.innerHTML += `
                        <div class="result-item">
                            <h3>${item.text ? item.text.substring(0, 100) : 'No content'}...</h3>
                            <p>${item.tags ? item.tags.join(', ') : ''}</p>
                        </div>
                    `;
                });
            } else {
                resultsEl.innerHTML = '<p style="color:#94a3b8">无结果</p>';
            }
        }
        
        // 存储
        async function store() {
            const text = document.getElementById('memory-text').value;
            const tags = document.getElementById('memory-tags').value.split(',').map(t => t.trim()).filter(t => t);
            
            const res = await fetch(`${API_BASE}/api/memory`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({text, tags})
            });
            
            const data = await res.json();
            alert(data.message);
            
            if (data.message === '存储成功') {
                document.getElementById('memory-text').value = '';
                document.getElementById('memory-tags').value = '';
                loadStats();
            }
        }
        
        // 标签页切换
        function showTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.card').forEach(c => {
                if (c.id.includes('tab')) c.classList.add('hidden');
            });
            
            event.target.classList.add('active');
            document.getElementById(`${tab}-tab`).classList.remove('hidden');
        }
        
        // 登出
        document.getElementById('auth-btn').addEventListener('click', async () => {
            if (token) {
                await fetch(`${API_BASE}/api/logout`, {
                    headers: {'Authorization': `Bearer ${token}`}
                });
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                location.reload();
            }
        });
        
        init();
    </script>
</body>
</html>
"""


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Web UI Server")
    parser.add_argument("--port", "-p", type=int, default=38080, help="端口")
    parser.add_argument("--host", default="0.0.0.0", help="主机")
    
    args = parser.parse_args()
    
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI 未安装")
        print("请运行: pip install fastapi uvicorn python-multipart")
        return
    
    print(f"🌐 启动 Web UI: http://localhost:{args.port}")
    print(f"📚 API 文档: http://localhost:{args.port}/docs")
    print("按 Ctrl+C 停止\n")
    
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
