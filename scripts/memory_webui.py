#!/usr/bin/env python3
"""
Memory Web UI - Web 可视化界面 v0.1.4

功能:
- 记忆浏览和搜索
- 记忆创建和编辑
- 统计仪表盘
- 响应式设计

Usage:
    python3 memory_webui.py --port 8080

或配合 memory_api.py 使用:
    uvicorn memory_api:app --port 8000
    python3 memory_webui.py --api http://localhost:8000
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import webbrowser
import threading

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

# HTML 模板
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified Memory - 记忆系统</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 12px;
            padding: 20px 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #333;
            font-size: 24px;
        }
        
        .header .subtitle {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-card .label {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }
        
        .search-box {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .search-box input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .search-box input:focus {
            border-color: #667eea;
        }
        
        .memories {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .memory-item {
            padding: 15px 20px;
            border-bottom: 1px solid #f0f0f0;
            transition: background 0.3s;
        }
        
        .memory-item:hover {
            background: #f9f9f9;
        }
        
        .memory-item:last-child {
            border-bottom: none;
        }
        
        .memory-text {
            color: #333;
            font-size: 15px;
            line-height: 1.5;
        }
        
        .memory-meta {
            display: flex;
            gap: 15px;
            margin-top: 10px;
            font-size: 13px;
            color: #888;
        }
        
        .tag {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 5px;
        }
        
        .category {
            display: inline-block;
            background: #f0f0f0;
            color: #666;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        
        .importance {
            display: inline-flex;
            gap: 2px;
        }
        
        .star { color: #ffd700; }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #888;
        }
        
        .actions {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        
        .btn {
            padding: 6px 12px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            transition: opacity 0.3s;
        }
        
        .btn:hover { opacity: 0.8; }
        .btn-primary { background: #667eea; color: white; }
        .btn-danger { background: #e74c3c; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Unified Memory</h1>
            <div class="subtitle">智能记忆系统 v0.1.4</div>
        </div>
        
        <div class="stats" id="stats">
            <!-- 统计卡片由 JS 动态填充 -->
        </div>
        
        <div class="search-box">
            <input type="text" id="search" placeholder="搜索记忆..." onkeyup="searchMemories()">
        </div>
        
        <div class="memories" id="memories">
            <!-- 记忆列表由 JS 动态填充 -->
        </div>
    </div>
    
    <script>
        // 配置
        const API_BASE = window.location.origin;
        let allMemories = [];
        
        // 加载记忆
        async function loadMemories() {
            try {
                const response = await fetch(`${API_BASE}/api/memories`);
                const data = await response.json();
                allMemories = data;
                renderMemories(data);
                updateStats(data);
            } catch (error) {
                console.error('Failed to load memories:', error);
                // 使用模拟数据
                allMemories = getMockData();
                renderMemories(allMemories);
                updateStats(allMemories);
            }
        }
        
        // 渲染记忆列表
        function renderMemories(memories) {
            const container = document.getElementById('memories');
            
            if (memories.length === 0) {
                container.innerHTML = '<div class="empty-state">暂无记忆</div>';
                return;
            }
            
            container.innerHTML = memories.map(m => `
                <div class="memory-item">
                    <div class="memory-text">${escapeHtml(m.text)}</div>
                    <div class="memory-meta">
                        <span class="category">${m.category}</span>
                        <span class="importance">${'⭐'.repeat(Math.round(m.importance * 5))}</span>
                        <span>${formatDate(m.created_at)}</span>
                    </div>
                    ${m.tags && m.tags.length > 0 ? `
                        <div style="margin-top: 8px;">
                            ${m.tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `).join('');
        }
        
        // 搜索记忆
        function searchMemories() {
            const query = document.getElementById('search').value.toLowerCase();
            
            if (!query) {
                renderMemories(allMemories);
                return;
            }
            
            const filtered = allMemories.filter(m => 
                m.text.toLowerCase().includes(query) ||
                (m.tags && m.tags.some(t => t.toLowerCase().includes(query)))
            );
            
            renderMemories(filtered);
        }
        
        // 更新统计
        function updateStats(memories) {
            const stats = {
                total: memories.length,
                categories: {},
                avgImportance: 0
            };
            
            memories.forEach(m => {
                stats.categories[m.category] = (stats.categories[m.category] || 0) + 1;
                stats.avgImportance += m.importance || 0;
            });
            
            stats.avgImportance = memories.length > 0 
                ? (stats.avgImportance / memories.length).toFixed(2) 
                : 0;
            
            document.getElementById('stats').innerHTML = `
                <div class="stat-card">
                    <div class="value">${stats.total}</div>
                    <div class="label">总记忆数</div>
                </div>
                <div class="stat-card">
                    <div class="value">${Object.keys(stats.categories).length}</div>
                    <div class="label">分类数</div>
                </div>
                <div class="stat-card">
                    <div class="value">${stats.avgImportance}</div>
                    <div class="label">平均重要性</div>
                </div>
            `;
        }
        
        // 辅助函数
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function formatDate(dateStr) {
            if (!dateStr) return '';
            return dateStr.substring(0, 10);
        }
        
        function getMockData() {
            return [
                { id: '1', text: '用户偏好使用飞书进行团队协作', category: 'preference', importance: 0.6, tags: ['协作工具'], created_at: '2026-03-18' },
                { id: '2', text: '项目官网重构正在进行中', category: 'project', importance: 0.8, tags: ['项目'], created_at: '2026-03-18' },
                { id: '3', text: '记忆系统已升级到v0.1.4版本', category: 'learning', importance: 0.5, tags: ['记忆系统'], created_at: '2026-03-18' }
            ];
        }
        
        // 初始化
        loadMemories();
    </script>
</body>
</html>
'''

# API 代理处理器
class MemoryWebHandler(SimpleHTTPRequestHandler):
    """Web UI 处理器"""
    
    def __init__(self, *args, api_base=None, **kwargs):
        self.api_base = api_base
        super().__init__(*args, directory=str(WORKSPACE), **kwargs)
    
    def do_GET(self):
        """处理 GET 请求"""
        if self.path == '/' or self.path == '/index.html':
            self.send_html(HTML_TEMPLATE)
        elif self.path == '/api/stats':
            self.handle_api_stats()
        elif self.path == '/api/memories':
            self.handle_api_memories()
        else:
            self.send_html(HTML_TEMPLATE)
    
    def do_POST(self):
        """处理 POST 请求"""
        if self.path == '/api/search':
            self.handle_api_search()
        else:
            self.send_error(404)
    
    def send_html(self, html):
        """发送 HTML 响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json(self, data):
        """发送 JSON 响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def handle_api_stats(self):
        """获取统计信息"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            
            total = len(result.get("id", []))
            categories = {}
            for cat in result.get("category", []):
                categories[cat] = categories.get(cat, 0) + 1
            
            self.send_json({
                "total_memories": total,
                "categories": categories
            })
        except Exception as e:
            self.send_json({"error": str(e)})
    
    def handle_api_memories(self):
        """获取记忆列表"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            
            memories = []
            count = len(result.get("id", []))
            for i in range(count):
                memories.append({
                    "id": result["id"][i] if i < len(result.get("id", [])) else "",
                    "text": result["text"][i] if i < len(result.get("text", [])) else "",
                    "category": result["category"][i] if i < len(result.get("category", [])) else "general",
                    "importance": float(result["importance"][i]) if i < len(result.get("importance", [])) else 0.5,
                    "tags": [],  # 数据库中没有 tags 字段
                    "created_at": str(result["timestamp"][i]) if i < len(result.get("timestamp", [])) else ""
                })
            
            self.send_json(memories)
        except Exception as e:
            print(f"Error loading memories: {e}")
            import traceback
            traceback.print_exc()
            self.send_json([])


def main():
    parser = argparse.ArgumentParser(description="Memory Web UI 0.1.4")
    parser.add_argument("--port", "-p", type=int, default=38080)
    parser.add_argument("--api", "-a", help="API 基础 URL")
    parser.add_argument("--open", "-o", action="store_true", help="自动打开浏览器")
    
    args = parser.parse_args()
    
    print(f"🌐 Memory Web UI 启动中...")
    print(f"   地址: http://localhost:{args.port}")
    print(f"   按 Ctrl+C 停止")
    
    if args.open:
        webbrowser.open(f"http://localhost:{args.port}")
    
    try:
        server = HTTPServer(('0.0.0.0', args.port), MemoryWebHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ 已停止")


if __name__ == "__main__":
    main()
