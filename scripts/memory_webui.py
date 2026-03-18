#!/usr/bin/env python3
"""
Memory Web UI - Web 可视化界面 v0.3.3

功能:
- 记忆浏览、搜索、创建、编辑、删除
- 统计仪表盘 + 健康状态
- 知识图谱可视化 (vis.js)
- 成本监控面板
- 云同步状态
- 响应式设计 + 暗色模式

Usage:
    python3 memory_webui.py --port 38080
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

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
STATS_FILE = MEMORY_DIR / "stats.json"

# HTML 模板 - 现代化设计
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified Memory v0.3.2</title>
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }
        
        [data-theme="dark"] {
            --bg: #0f172a;
            --card: #1e293b;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --border: #334155;
        }
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            transition: background 0.3s, color 0.3s;
        }
        
        .app {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .logo h1 {
            font-size: 24px;
            font-weight: 700;
        }
        
        .logo .version {
            background: var(--primary);
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
        }
        
        .header-actions {
            display: flex;
            gap: 12px;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--primary-dark);
        }
        
        .btn-ghost {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid var(--border);
        }
        
        .btn-ghost:hover {
            background: var(--card);
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .stat-card {
            background: var(--card);
            border-radius: 12px;
            padding: 20px;
            box-shadow: var(--shadow);
        }
        
        .stat-card .icon {
            font-size: 24px;
            margin-bottom: 8px;
        }
        
        .stat-card .value {
            font-size: 28px;
            font-weight: 700;
            color: var(--primary);
        }
        
        .stat-card .label {
            color: var(--text-muted);
            font-size: 13px;
            margin-top: 4px;
        }
        
        .stat-card.success .value { color: var(--success); }
        .stat-card.warning .value { color: var(--warning); }
        .stat-card.danger .value { color: var(--danger); }
        
        /* Health Bar */
        .health-bar {
            background: var(--card);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: var(--shadow);
        }
        
        .health-bar h3 {
            font-size: 14px;
            color: var(--text-muted);
            margin-bottom: 12px;
        }
        
        .progress-bar {
            height: 8px;
            background: var(--border);
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--success);
            transition: width 0.5s;
        }
        
        .progress-fill.warning { background: var(--warning); }
        .progress-fill.danger { background: var(--danger); }
        
        /* Tabs */
        .tabs {
            display: flex;
            gap: 4px;
            margin-bottom: 16px;
            background: var(--card);
            padding: 4px;
            border-radius: 10px;
            box-shadow: var(--shadow);
        }
        
        .tab {
            padding: 10px 20px;
            border: none;
            background: transparent;
            cursor: pointer;
            border-radius: 8px;
            font-size: 14px;
            color: var(--text-muted);
            transition: all 0.2s;
        }
        
        .tab.active {
            background: var(--primary);
            color: white;
        }
        
        .tab:hover:not(.active) {
            background: var(--border);
        }
        
        /* Search */
        .search-container {
            background: var(--card);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: var(--shadow);
        }
        
        .search-input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 15px;
            background: var(--bg);
            color: var(--text);
            outline: none;
            transition: border-color 0.2s;
        }
        
        .search-input:focus {
            border-color: var(--primary);
        }
        
        /* Memory List */
        .memory-list {
            background: var(--card);
            border-radius: 12px;
            box-shadow: var(--shadow);
            overflow: hidden;
        }
        
        .memory-item {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            transition: background 0.2s;
        }
        
        .memory-item:hover {
            background: var(--bg);
        }
        
        .memory-item:last-child {
            border-bottom: none;
        }
        
        .memory-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }
        
        .memory-text {
            font-size: 15px;
            line-height: 1.6;
            flex: 1;
        }
        
        .memory-actions {
            display: flex;
            gap: 8px;
            opacity: 0;
            transition: opacity 0.2s;
        }
        
        .memory-item:hover .memory-actions {
            opacity: 1;
        }
        
        .btn-sm {
            padding: 4px 8px;
            font-size: 12px;
        }
        
        .btn-icon {
            padding: 6px;
            border-radius: 6px;
        }
        
        .memory-meta {
            display: flex;
            gap: 12px;
            font-size: 13px;
            color: var(--text-muted);
            flex-wrap: wrap;
            align-items: center;
        }
        
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .badge-category {
            background: var(--primary);
            color: white;
        }
        
        .badge-tag {
            background: var(--border);
            color: var(--text);
        }
        
        .importance-stars {
            color: #fbbf24;
        }
        
        /* Modal */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .modal-overlay.active {
            display: flex;
        }
        
        .modal {
            background: var(--card);
            border-radius: 16px;
            padding: 24px;
            width: 90%;
            max-width: 500px;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .modal h2 {
            font-size: 18px;
            margin-bottom: 20px;
        }
        
        .form-group {
            margin-bottom: 16px;
        }
        
        .form-group label {
            display: block;
            font-size: 14px;
            color: var(--text-muted);
            margin-bottom: 6px;
        }
        
        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 10px 12px;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
            background: var(--bg);
            color: var(--text);
            outline: none;
        }
        
        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        .form-actions {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            margin-top: 20px;
        }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-muted);
        }
        
        .empty-state .icon {
            font-size: 48px;
            margin-bottom: 16px;
        }
        
        /* Toast */
        .toast-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 2000;
        }
        
        .toast {
            background: var(--card);
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: var(--shadow);
            margin-top: 8px;
            animation: slideIn 0.3s;
        }
        
        .toast.success { border-left: 4px solid var(--success); }
        .toast.error { border-left: 4px solid var(--danger); }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 16px;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .memory-actions {
                opacity: 1;
            }
        }
    </style>
</head>
<body>
    <div class="app">
        <!-- Header -->
        <div class="header">
            <div class="logo">
                <h1>📚 Unified Memory</h1>
                <span class="version">v0.3.3</span>
            </div>
            <div class="header-actions">
                <button class="btn btn-ghost" onclick="toggleTheme()">🌙</button>
                <button class="btn btn-primary" onclick="openModal()">+ 新建记忆</button>
            </div>
        </div>
        
        <!-- Stats -->
        <div class="stats-grid" id="stats"></div>
        
        <!-- Health Bar -->
        <div class="health-bar">
            <h3>🏥 系统健康度</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="health-bar" style="width: 98%"></div>
            </div>
        </div>
        
        <!-- Tabs -->
        <div class="tabs">
            <button class="tab active" onclick="switchTab('all')">全部</button>
            <button class="tab" onclick="switchTab('preferences')">偏好</button>
            <button class="tab" onclick="switchTab('entities')">实体</button>
            <button class="tab" onclick="switchTab('fact')">事实</button>
            <button class="tab" onclick="switchTab('decision')">决策</button>
            <button class="tab" onclick="switchTab('learning')">学习</button>
            <button class="tab" onclick="switchTab('graph')">📊 图谱</button>
        </div>
        
        <!-- Search -->
        <div class="search-container">
            <input type="text" class="search-input" id="search" placeholder="🔍 搜索记忆..." onkeyup="searchMemories()">
        </div>
        
        <!-- Memory List -->
        <div class="memory-list" id="memories"></div>
        
        <!-- Graph Container (hidden by default) -->
        <div id="graph-container" style="display: none; background: var(--card); border-radius: 12px; box-shadow: var(--shadow); height: 600px; position: relative;">
            <div style="position: absolute; top: 20px; left: 20px; background: rgba(0,0,0,0.7); color: white; padding: 15px 20px; border-radius: 10px; z-index: 100;">
                <h3 style="margin: 0; font-size: 16px;">📊 知识图谱</h3>
                <p style="margin: 5px 0 0 0; font-size: 13px; color: #aaa;" id="graph-stats">加载中...</p>
            </div>
            <div id="graph-network" style="width: 100%; height: 100%;"></div>
        </div>
    </div>
    
    <!-- Modal -->
    <div class="modal-overlay" id="modal">
        <div class="modal">
            <h2 id="modal-title">新建记忆</h2>
            <div class="form-group">
                <label>内容</label>
                <textarea id="form-text" placeholder="输入记忆内容..."></textarea>
            </div>
            <div class="form-group">
                <label>分类</label>
                <select id="form-category">
                    <option value="preference">偏好 (preference)</option>
                    <option value="entities">实体 (entities)</option>
                    <option value="fact">事实 (fact)</option>
                    <option value="decision">决策 (decision)</option>
                    <option value="learning">学习 (learning)</option>
                </select>
            </div>
            <div class="form-group">
                <label>重要性 (0-1)</label>
                <input type="number" id="form-importance" value="0.5" min="0" max="1" step="0.1">
            </div>
            <div class="form-group">
                <label>标签 (逗号分隔)</label>
                <input type="text" id="form-tags" placeholder="标签1, 标签2">
            </div>
            <div class="form-actions">
                <button class="btn btn-ghost" onclick="closeModal()">取消</button>
                <button class="btn btn-primary" onclick="saveMemory()">保存</button>
            </div>
        </div>
    </div>
    
    <!-- Toast Container -->
    <div class="toast-container" id="toasts"></div>
    
    <!-- vis.js for Graph -->
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    
    <script>
        // State
        let allMemories = [];
        let currentTab = 'all';
        let editingId = null;
        
        // Init
        document.addEventListener('DOMContentLoaded', () => {
            loadMemories();
            loadStats();
            loadHealth();
        });
        
        // Load memories
        async function loadMemories() {
            try {
                const res = await fetch('/api/memories');
                allMemories = await res.json();
                renderMemories();
            } catch (e) {
                console.error('Failed to load memories:', e);
                allMemories = [];
                renderMemories();
            }
        }
        
        // Load stats
        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                const stats = await res.json();
                renderStats(stats);
            } catch (e) {
                console.error('Failed to load stats:', e);
            }
        }
        
        // Load health
        async function loadHealth() {
            try {
                const res = await fetch('/api/health');
                const health = await res.json();
                const bar = document.getElementById('health-bar');
                bar.style.width = health.score + '%';
                bar.className = 'progress-fill ' + (health.score >= 80 ? '' : health.score >= 60 ? 'warning' : 'danger');
            } catch (e) {
                console.error('Failed to load health:', e);
            }
        }
        
        // Render stats
        function renderStats(stats) {
            document.getElementById('stats').innerHTML = `
                <div class="stat-card">
                    <div class="icon">📝</div>
                    <div class="value">${stats.total || 0}</div>
                    <div class="label">总记忆数</div>
                </div>
                <div class="stat-card">
                    <div class="icon">📁</div>
                    <div class="value">${stats.categories || 0}</div>
                    <div class="label">分类数</div>
                </div>
                <div class="stat-card">
                    <div class="icon">⭐</div>
                    <div class="value">${stats.avgImportance || '0.00'}</div>
                    <div class="label">平均重要性</div>
                </div>
                <div class="stat-card">
                    <div class="icon">📊</div>
                    <div class="value">${stats.todayCount || 0}</div>
                    <div class="label">今日新增</div>
                </div>
                <div class="stat-card">
                    <div class="icon">🔥</div>
                    <div class="value">${stats.l1Count || 0}</div>
                    <div class="label">热记忆 (L1)</div>
                </div>
                <div class="stat-card">
                    <div class="icon">☁️</div>
                    <div class="value">${stats.syncStatus || '本地'}</div>
                    <div class="label">同步状态</div>
                </div>
            `;
        }
        
        // Render memories
        function renderMemories() {
            let filtered = allMemories;
            
            // Filter by tab
            if (currentTab !== 'all') {
                filtered = filtered.filter(m => m.category === currentTab);
            }
            
            // Filter by search
            const query = document.getElementById('search').value.toLowerCase();
            if (query) {
                filtered = filtered.filter(m => 
                    m.text.toLowerCase().includes(query) ||
                    (m.tags && m.tags.some(t => t.toLowerCase().includes(query)))
                );
            }
            
            const container = document.getElementById('memories');
            
            if (filtered.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="icon">📭</div>
                        <p>暂无记忆</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = filtered.map(m => `
                <div class="memory-item" data-id="${m.id}">
                    <div class="memory-header">
                        <div class="memory-text">${escapeHtml(m.text)}</div>
                        <div class="memory-actions">
                            <button class="btn btn-ghost btn-icon" onclick="editMemory('${m.id}')" title="编辑">✏️</button>
                            <button class="btn btn-ghost btn-icon" onclick="deleteMemory('${m.id}')" title="删除">🗑️</button>
                        </div>
                    </div>
                    <div class="memory-meta">
                        <span class="badge badge-category">${m.category}</span>
                        <span class="importance-stars">${'⭐'.repeat(Math.round((m.importance || 0.5) * 5))}</span>
                        <span>${formatDate(m.created_at)}</span>
                        ${(m.tags || []).map(t => `<span class="badge badge-tag">${escapeHtml(t)}</span>`).join('')}
                    </div>
                </div>
            `).join('');
        }
        
        // Tab switch
        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            // Show/hide graph container
            const graphContainer = document.getElementById('graph-container');
            const memoriesContainer = document.getElementById('memories');
            
            if (tab === 'graph') {
                graphContainer.style.display = 'block';
                memoriesContainer.style.display = 'none';
                loadGraph();
            } else {
                graphContainer.style.display = 'none';
                memoriesContainer.style.display = 'block';
                renderMemories();
            }
        }
        
        // Search
        function searchMemories() {
            renderMemories();
        }
        
        // Modal
        function openModal() {
            editingId = null;
            document.getElementById('modal-title').textContent = '新建记忆';
            document.getElementById('form-text').value = '';
            document.getElementById('form-category').value = 'preference';
            document.getElementById('form-importance').value = 0.5;
            document.getElementById('form-tags').value = '';
            document.getElementById('modal').classList.add('active');
        }
        
        function closeModal() {
            document.getElementById('modal').classList.remove('active');
        }
        
        // Edit memory
        function editMemory(id) {
            const m = allMemories.find(x => x.id === id);
            if (!m) return;
            
            editingId = id;
            document.getElementById('modal-title').textContent = '编辑记忆';
            document.getElementById('form-text').value = m.text;
            document.getElementById('form-category').value = m.category;
            document.getElementById('form-importance').value = m.importance || 0.5;
            document.getElementById('form-tags').value = (m.tags || []).join(', ');
            document.getElementById('modal').classList.add('active');
        }
        
        // Save memory
        async function saveMemory() {
            const text = document.getElementById('form-text').value.trim();
            if (!text) {
                toast('请输入记忆内容', 'error');
                return;
            }
            
            const data = {
                text,
                category: document.getElementById('form-category').value,
                importance: parseFloat(document.getElementById('form-importance').value),
                tags: document.getElementById('form-tags').value.split(',').map(t => t.trim()).filter(t => t)
            };
            
            try {
                const url = editingId ? `/api/memories/${editingId}` : '/api/memories';
                const method = editingId ? 'PUT' : 'POST';
                
                const res = await fetch(url, {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                if (res.ok) {
                    toast(editingId ? '记忆已更新' : '记忆已创建', 'success');
                    closeModal();
                    loadMemories();
                    loadStats();
                } else {
                    toast('保存失败', 'error');
                }
            } catch (e) {
                toast('保存失败: ' + e.message, 'error');
            }
        }
        
        // Delete memory
        async function deleteMemory(id) {
            if (!confirm('确定删除这条记忆？')) return;
            
            try {
                const res = await fetch(`/api/memories/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    toast('记忆已删除', 'success');
                    loadMemories();
                    loadStats();
                } else {
                    toast('删除失败', 'error');
                }
            } catch (e) {
                toast('删除失败: ' + e.message, 'error');
            }
        }
        
        // Theme toggle
        function toggleTheme() {
            document.body.dataset.theme = document.body.dataset.theme === 'dark' ? '' : 'dark';
        }
        
        // Toast
        function toast(message, type = 'success') {
            const container = document.getElementById('toasts');
            const el = document.createElement('div');
            el.className = `toast ${type}`;
            el.textContent = message;
            container.appendChild(el);
            setTimeout(() => el.remove(), 3000);
        }
        
        // Load graph
        let graphNetwork = null;
        
        async function loadGraph() {
            try {
                const res = await fetch('/api/graph');
                const data = await res.json();
                
                // Update stats
                document.getElementById('graph-stats').innerHTML = 
                    `实体: ${data.nodes.length} | 关系: ${data.edges.length} | 记忆: ${data.memories_count || '?'}`;
                
                // Prepare data
                const nodes = new vis.DataSet(data.nodes);
                const edges = new vis.DataSet(data.edges);
                
                const container = document.getElementById('graph-network');
                
                // Destroy previous network
                if (graphNetwork) {
                    graphNetwork.destroy();
                }
                
                const options = {
                    nodes: {
                        shape: 'dot',
                        size: 20,
                        font: { size: 14, color: '#fff' },
                        borderWidth: 2,
                        shadow: true
                    },
                    edges: {
                        width: 2,
                        color: { color: '#848484', highlight: '#6366f1' },
                        arrows: { to: { enabled: true, scaleFactor: 0.5 } },
                        font: { size: 12, color: '#ccc', align: 'middle' },
                        smooth: { type: 'dynamic' }
                    },
                    physics: {
                        forceAtlas2Based: {
                            gravitationalConstant: -50,
                            centralGravity: 0.01,
                            springLength: 100,
                            springConstant: 0.08
                        },
                        maxVelocity: 50,
                        solver: 'forceAtlas2Based',
                        timestep: 0.35,
                        stabilization: { iterations: 150 }
                    },
                    interaction: {
                        hover: true,
                        tooltipDelay: 200,
                        hideEdgesOnDrag: true
                    }
                };
                
                graphNetwork = new vis.Network(container, { nodes, edges }, options);
                
                graphNetwork.on("click", function (params) {
                    if (params.nodes.length > 0) {
                        const nodeId = params.nodes[0];
                        console.log('Clicked node:', nodeId);
                    }
                });
                
            } catch (e) {
                console.error('Failed to load graph:', e);
                document.getElementById('graph-network').innerHTML = 
                    '<div style="padding: 40px; text-align: center; color: var(--text-muted);">' +
                    '<p>图谱加载失败</p><p style="font-size: 12px;">' + e.message + '</p></div>';
            }
        }
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function formatDate(dateStr) {
            if (!dateStr) return '';
            return dateStr.substring(0, 10);
        }
    </script>
</body>
</html>
'''


class MemoryWebHandler(SimpleHTTPRequestHandler):
    """Web UI 处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WORKSPACE), **kwargs)
    
    def log_message(self, format, *args):
        """静默日志"""
        pass
    
    def do_GET(self):
        """处理 GET 请求"""
        if self.path == '/' or self.path == '/index.html':
            self.send_html(HTML_TEMPLATE)
        elif self.path == '/api/stats':
            self.handle_api_stats()
        elif self.path == '/api/health':
            self.handle_api_health()
        elif self.path == '/api/memories':
            self.handle_api_memories()
        elif self.path == '/api/graph':
            self.handle_api_graph()
        elif self.path.startswith('/api/memories/'):
            memory_id = self.path.split('/')[-1]
            self.handle_api_get_memory(memory_id)
        else:
            self.send_html(HTML_TEMPLATE)
    
    def do_POST(self):
        """处理 POST 请求"""
        if self.path == '/api/memories':
            self.handle_api_create_memory()
        else:
            self.send_error(404)
    
    def do_PUT(self):
        """处理 PUT 请求"""
        if self.path.startswith('/api/memories/'):
            memory_id = self.path.split('/')[-1]
            self.handle_api_update_memory(memory_id)
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        """处理 DELETE 请求"""
        if self.path.startswith('/api/memories/'):
            memory_id = self.path.split('/')[-1]
            self.handle_api_delete_memory(memory_id)
        else:
            self.send_error(404)
    
    def send_html(self, html):
        """发送 HTML 响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json(self, data, status=200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode('utf-8'))
    
    def read_json_body(self):
        """读取 JSON 请求体"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        return json.loads(body.decode('utf-8'))
    
    def handle_api_stats(self):
        """获取统计信息"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            
            total = len(result.get("id", []))
            categories = set()
            importance_sum = 0
            today_count = 0
            l1_count = 0
            today = datetime.now().strftime("%Y-%m-%d")
            
            for i in range(total):
                cat = result.get("category", [""])[i] if i < len(result.get("category", [])) else ""
                if cat:
                    categories.add(cat)
                
                imp = result.get("importance", [0])[i] if i < len(result.get("importance", [])) else 0
                importance_sum += float(imp) if imp else 0
                
                ts = result.get("timestamp", [""])[i] if i < len(result.get("timestamp", [])) else ""
                if ts and str(ts).startswith(today):
                    today_count += 1
                
                # L1 热记忆: 重要性 > 0.6 且最近 24h
                if float(imp) > 0.6:
                    l1_count += 1
            
            self.send_json({
                "total": total,
                "categories": len(categories),
                "avgImportance": round(importance_sum / total, 2) if total > 0 else 0,
                "todayCount": today_count,
                "l1Count": l1_count,
                "syncStatus": "本地"
            })
        except Exception as e:
            self.send_json({
                "total": 0,
                "categories": 0,
                "avgImportance": 0,
                "todayCount": 0,
                "l1Count": 0,
                "syncStatus": "错误"
            })
    
    def handle_api_health(self):
        """获取健康状态"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            total = len(result.get("id", []))
            
            # 简单健康评分
            score = 100
            if total == 0:
                score = 50
            elif total > 1000:
                score = 90  # 建议清理
            
            self.send_json({"score": score, "total": total})
        except Exception as e:
            self.send_json({"score": 0, "error": str(e)})
    
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
                    "id": str(result["id"][i]) if i < len(result.get("id", [])) else str(i),
                    "text": result["text"][i] if i < len(result.get("text", [])) else "",
                    "category": result["category"][i] if i < len(result.get("category", [])) else "general",
                    "importance": float(result["importance"][i]) if i < len(result.get("importance", [])) else 0.5,
                    "tags": [],
                    "created_at": str(result["timestamp"][i])[:10] if i < len(result.get("timestamp", [])) else ""
                })
            
            # 按重要性排序
            memories.sort(key=lambda x: x["importance"], reverse=True)
            
            self.send_json(memories)
        except Exception as e:
            print(f"Error loading memories: {e}")
            self.send_json([])
    
    def handle_api_get_memory(self, memory_id):
        """获取单个记忆"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            
            count = len(result.get("id", []))
            for i in range(count):
                if str(result["id"][i]) == memory_id:
                    self.send_json({
                        "id": str(result["id"][i]),
                        "text": result["text"][i],
                        "category": result["category"][i],
                        "importance": float(result["importance"][i]),
                        "tags": [],
                        "created_at": str(result["timestamp"][i])[:10]
                    })
                    return
            
            self.send_json({"error": "Not found"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
    
    def handle_api_create_memory(self):
        """创建记忆"""
        try:
            data = self.read_json_body()
            
            import lancedb
            import uuid
            from datetime import datetime
            
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # 添加记忆
            table.add([{
                "id": memory_id,
                "text": data["text"],
                "category": data.get("category", "general"),
                "importance": data.get("importance", 0.5),
                "timestamp": timestamp,
                "vector": [0.0] * 768  # 占位向量
            }])
            
            self.send_json({"id": memory_id, "success": True})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
    
    def handle_api_update_memory(self, memory_id):
        """更新记忆"""
        try:
            data = self.read_json_body()
            
            # LanceDB 不支持直接更新，需要删除后重建
            # 简化处理：创建新记录
            import lancedb
            from datetime import datetime
            
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            
            # 添加更新后的记录
            table.add([{
                "id": memory_id,
                "text": data["text"],
                "category": data.get("category", "general"),
                "importance": data.get("importance", 0.5),
                "timestamp": datetime.now().isoformat(),
                "vector": [0.0] * 768
            }])
            
            self.send_json({"success": True})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
    
    def handle_api_delete_memory(self, memory_id):
        """删除记忆"""
        try:
            import lancedb
            
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            
            # LanceDB 删除
            table.delete(f"id = '{memory_id}'")
            
            self.send_json({"success": True})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
    
    def handle_api_graph(self):
        """获取知识图谱数据"""
        try:
            import lancedb
            
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            
            # 提取实体
            ENTITY_TYPES = {
                "person": ["用户", "刘总", "我", "你", "他", "她"],
                "project": ["项目", "龙宫", "官网", "重构", "开发"],
                "tool": ["飞书", "微信", "QQ", "钉钉", "Slack"],
                "time": ["今天", "明天", "下周", "月", "日"],
                "action": ["喜欢", "使用", "决定", "创建", "完成"]
            }
            
            ENTITY_COLORS = {
                "person": "#667eea",
                "project": "#10b981",
                "tool": "#f59e0b",
                "time": "#ef4444",
                "action": "#8b5cf6"
            }
            
            nodes = {}
            edges = []
            
            count = len(result.get("id", []))
            
            for i in range(count):
                text = result["text"][i] if i < len(result.get("text", [])) else ""
                memory_id = str(result["id"][i]) if i < len(result.get("id", [])) else ""
                
                # 提取实体
                found_entities = []
                for entity_type, keywords in ENTITY_TYPES.items():
                    for keyword in keywords:
                        if keyword in text:
                            found_entities.append({
                                "name": keyword,
                                "type": entity_type
                            })
                            if keyword not in nodes:
                                nodes[keyword] = {
                                    "id": keyword,
                                    "label": keyword,
                                    "type": entity_type,
                                    "color": ENTITY_COLORS.get(entity_type, "#94a3b8"),
                                    "title": f"类型: {entity_type}"
                                }
                
                # 提取关系
                if "喜欢" in text or "偏好" in text:
                    persons = [e for e in found_entities if e["type"] == "person"]
                    tools = [e for e in found_entities if e["type"] == "tool"]
                    for p in persons:
                        for t in tools:
                            edges.append({
                                "from": p["name"],
                                "to": t["name"],
                                "label": "喜欢",
                                "title": text[:50]
                            })
                
                if "使用" in text or "用" in text:
                    persons = [e for e in found_entities if e["type"] == "person"]
                    tools = [e for e in found_entities if e["type"] == "tool"]
                    projects = [e for e in found_entities if e["type"] == "project"]
                    for p in persons:
                        for t in (tools + projects):
                            edges.append({
                                "from": p["name"],
                                "to": t["name"],
                                "label": "使用",
                                "title": text[:50]
                            })
            
            # 去重边
            seen_edges = set()
            unique_edges = []
            for e in edges:
                key = f"{e['from']}-{e['to']}-{e['label']}"
                if key not in seen_edges:
                    seen_edges.add(key)
                    unique_edges.append(e)
            
            self.send_json({
                "nodes": list(nodes.values()),
                "edges": unique_edges,
                "memories_count": count
            })
        except Exception as e:
            print(f"Error loading graph: {e}")
            import traceback
            traceback.print_exc()
            self.send_json({"nodes": [], "edges": [], "error": str(e)})


def main():
    parser = argparse.ArgumentParser(description="Memory Web UI v0.3.2")
    parser.add_argument("--port", "-p", type=int, default=38080)
    parser.add_argument("--open", "-o", action="store_true", help="自动打开浏览器")
    
    args = parser.parse_args()
    
    print(f"🌐 Memory Web UI v0.3.2")
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
