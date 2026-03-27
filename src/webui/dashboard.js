/**
 * dashboard.js - Web UI Dashboard
 * Provides HTTP server with HTML dashboard for memory management
 * 
 * Usage:
 *   node src/webui/dashboard.js [--port 38080]
 */

import { createServer } from 'http';
import { readFileSync } from 'fs';
import { join, extname } from 'path';
import { getAllMemories, addMemory, deleteMemory } from '../storage.js';
import { hybridSearch } from '../fusion.js';
import { getSyncStatus } from '../backup/sync.js';
import { getBackupStats, listBackups } from '../backup/backup.js';
import { log } from '../utils/logger.js';

const PORT = parseInt(process.argv.find(a => a.startsWith('--port='))?.split('=')[1]) || 38080;

/**
 * Send JSON response
 */
function sendJSON(res, status, data) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(data));
}

/**
 * Send HTML response
 */
function sendHTML(res, status, html) {
  res.writeHead(status, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(html);
}

/**
 * Send static file
 */
function sendFile(res, path, mimeType) {
  try {
    const content = readFileSync(path);
    res.writeHead(200, { 'Content-Type': mimeType });
    res.end(content);
  } catch {
    res.writeHead(404);
    res.end('Not found');
  }
}

/**
 * Parse JSON body from request
 */
function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch {
        reject(new Error('Invalid JSON'));
      }
    });
    req.on('error', reject);
  });
}

/**
 * API handler
 */
async function handleAPI(req, res, path, query) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const parts = path.split('/').filter(Boolean);

  try {
    // /api/status
    if (parts[0] === 'api' && parts[1] === 'status') {
      const memories = getAllMemories();
      const syncStatus = getSyncStatus();
      const backupStats = getBackupStats();
      let ollamaOk = false;
      try {
        const r = await fetch('http://localhost:11434/api/tags');
        ollamaOk = r.ok;
      } catch { }
      return sendJSON(res, 200, {
        status: 'ok',
        timestamp: new Date().toISOString(),
        memories: memories.length,
        ollama: ollamaOk ? 'connected' : 'disconnected',
        sync: syncStatus,
        backup: backupStats
      });
    }

    // /api/memories
    if (parts[0] === 'api' && parts[1] === 'memories') {
      if (req.method === 'GET') {
        const limit = parseInt(query.get('limit') || 50);
        const offset = parseInt(query.get('offset') || 0);
        const memories = getAllMemories();
        return sendJSON(res, 200, {
          memories: memories.slice(offset, offset + limit),
          total: memories.length
        });
      }
      if (req.method === 'POST') {
        const body = await parseBody(req);
        const mem = addMemory({
          text: body.text || '',
          category: body.category || 'general',
          importance: body.importance || 0.5,
          tags: body.tags || []
        });
        return sendJSON(res, 201, { success: true, id: mem.id });
      }
    }

    // /api/memories/:id
    if (parts[0] === 'api' && parts[1] === 'memories' && parts[2]) {
      const id = parts[2];
      if (req.method === 'DELETE') {
        const ok = deleteMemory(id);
        return sendJSON(res, ok ? 200 : 404, { success: ok });
      }
      const memories = getAllMemories();
      const mem = memories.find(m => m.id === id);
      if (mem) {
        return sendJSON(res, 200, { memory: mem });
      }
      return sendJSON(res, 404, { error: 'Not found' });
    }

    // /api/search
    if (parts[0] === 'api' && parts[1] === 'search') {
      const q = query.get('q') || query.get('query') || '';
      const topK = parseInt(query.get('topK') || query.get('k') || 10);
      if (!q) return sendJSON(res, 400, { error: 'q is required' });
      const results = await hybridSearch(q, topK, 'hybrid');
      return sendJSON(res, 200, {
        query: q,
        count: results.length,
        results: results.map(r => ({
          id: r.memory.id,
          text: r.memory.text,
          category: r.memory.category,
          score: Math.round(r.fusionScore * 1000) / 1000
        }))
      });
    }

    // /api/backups
    if (parts[0] === 'api' && parts[1] === 'backups') {
      const backups = listBackups();
      return sendJSON(res, 200, { backups });
    }

    // /api/graph
    if (parts[0] === 'api' && parts[1] === 'graph') {
      return sendJSON(res, 200, { entities: [], relations: [] });
    }

    // /api/health
    if (parts[0] === 'api' && parts[1] === 'health') {
      return sendJSON(res, 200, { status: 'ok', timestamp: new Date().toISOString() });
    }

    sendJSON(res, 404, { error: 'API endpoint not found' });
  } catch (err) {
    log('ERROR', `Dashboard API error: ${err.message}`);
    sendJSON(res, 500, { error: err.message });
  }
}

/**
 * Main HTML page
 */
const DASHBOARD_HTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🧠 统一记忆系统</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0f172a;
  color: #e2e8f0;
  min-height: 100vh;
}
.container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
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
  font-size: 0.95rem;
}
nav a:hover { color: #3b82f6; }
nav a.active { color: #3b82f6; border-bottom: 2px solid #3b82f6; }

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}
.stat-card {
  background: #1e293b;
  border-radius: 12px;
  padding: 1.25rem;
  border: 1px solid #334155;
}
.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #3b82f6;
}
.stat-label { color: #94a3b8; font-size: 0.875rem; margin-top: 0.25rem; }

.search-box {
  background: #1e293b;
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}
.search-row { display: flex; gap: 0.75rem; }
.search-input {
  flex: 1;
  padding: 0.875rem 1rem;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 1rem;
}
.search-input:focus { outline: none; border-color: #3b82f6; }
.btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.875rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
  transition: background 0.2s;
}
.btn:hover { background: #2563eb; }
.btn-ghost {
  background: transparent;
  border: 1px solid #334155;
  color: #94a3b8;
}
.btn-ghost:hover { border-color: #3b82f6; color: #3b82f6; }

.section {
  background: #1e293b;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
h2 { font-size: 1.1rem; color: #e2e8f0; }

.memory-item {
  padding: 1rem;
  border-bottom: 1px solid #334155;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  background: #0f172a;
}
.memory-item:hover { background: #1a2744; }
.memory-text { color: #e2e8f0; line-height: 1.5; word-break: break-all; }
.memory-meta {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: #64748b;
}
.memory-meta span { display: flex; align-items: center; gap: 0.25rem; }
.badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  background: #334155;
  color: #94a3b8;
}
.score { color: #3b82f6; font-weight: bold; }
.empty { color: #64748b; text-align: center; padding: 2rem; }

.add-form {
  background: #0f172a;
  border-radius: 8px;
  padding: 1.25rem;
  margin-top: 1rem;
}
.add-form textarea {
  width: 100%;
  padding: 0.75rem;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 6px;
  color: #e2e8f0;
  font-size: 0.95rem;
  resize: vertical;
  min-height: 80px;
  margin-bottom: 0.75rem;
}
.add-form textarea:focus { outline: none; border-color: #3b82f6; }
.form-row { display: flex; gap: 0.75rem; margin-bottom: 0.75rem; }
.form-row input {
  padding: 0.5rem 0.75rem;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 6px;
  color: #e2e8f0;
  font-size: 0.875rem;
}
.form-row input:focus { outline: none; border-color: #3b82f6; }
.form-row input[type="number"] { width: 100px; }

.alert {
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}
.alert-success { background: #052e16; border: 1px solid #166534; color: #86efac; }
.alert-error { background: #2c1515; border: 1px solid #991b1b; color: #fca5a5; }

.footer {
  text-align: center;
  color: #475569;
  font-size: 0.8rem;
  padding: 2rem 0;
}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>🧠 统一记忆系统</h1>
    <nav>
      <a href="/" class="active">Dashboard</a>
      <a href="/graph">知识图谱</a>
      <a href="/backups">备份</a>
    </nav>
  </header>

  <div class="stats" id="stats">
    <div class="stat-card"><div class="stat-value" id="mem-count">-</div><div class="stat-label">记忆总数</div></div>
    <div class="stat-card"><div class="stat-value" id="sync-nodes">-</div><div class="stat-label">同步节点</div></div>
    <div class="stat-card"><div class="stat-value" id="backups">-</div><div class="stat-label">备份数</div></div>
    <div class="stat-card"><div class="stat-value" id="ollama-status">-</div><div class="stat-label">Ollama</div></div>
  </div>

  <div class="search-box">
    <div class="search-row">
      <input type="text" class="search-input" id="search-input" placeholder="🔍 搜索记忆... (按 Enter 搜索)">
    </div>
  </div>

  <div class="section">
    <div class="section-header">
      <h2>📋 最近记忆</h2>
      <button class="btn btn-ghost" onclick="showAddForm()">+ 添加记忆</button>
    </div>
    <div id="add-form" class="add-form" style="display:none">
      <textarea id="new-text" placeholder="记忆内容..."></textarea>
      <div class="form-row">
        <input type="text" id="new-category" placeholder="分类" value="general">
        <input type="number" id="new-importance" placeholder="重要性" value="0.5" min="0" max="1" step="0.1">
        <button class="btn" onclick="addMemory()">保存</button>
        <button class="btn btn-ghost" onclick="hideAddForm()">取消</button>
      </div>
    </div>
    <div id="alert-box"></div>
    <div id="memories-list"><p class="empty">加载中...</p></div>
  </div>

  <div class="footer">
    Unified Memory System v1.0 | Memory API on port 38421
  </div>
</div>

<script>
let alertTimeout;
function showAlert(msg, type) {
  clearTimeout(alertTimeout);
  const box = document.getElementById('alert-box');
  box.className = 'alert alert-' + type;
  box.textContent = msg;
  alertTimeout = setTimeout(() => { box.textContent = ''; box.className = ''; }, 4000);
}

async function loadStatus() {
  try {
    const r = await fetch('/api/status');
    const d = await r.json();
    document.getElementById('mem-count').textContent = d.memories || 0;
    document.getElementById('sync-nodes').textContent = d.sync?.nodes || 0;
    document.getElementById('backups').textContent = d.backup?.backup_count || 0;
    document.getElementById('ollama-status').textContent = d.ollama === 'connected' ? '✅' : '⚠️';
  } catch(e) { console.error(e); }
}

async function loadMemories(limit=20) {
  try {
    const r = await fetch('/api/memories?limit=' + limit);
    const d = await r.json();
    const list = document.getElementById('memories-list');
    if (!d.memories || d.memories.length === 0) {
      list.innerHTML = '<p class="empty">暂无记忆，添加第一条吧！</p>';
      return;
    }
    list.innerHTML = d.memories.map(m => {
      const text = (m.text || '').replace(/</g, '&lt;').replace(/>/g, '&gt;').slice(0, 300);
      const cat = m.category || 'general';
      const imp = m.importance != null ? m.importance.toFixed(1) : '0.5';
      const score = m.fusionScore != null ? Math.round(m.fusionScore * 100) + '%' : '';
      return \`<div class="memory-item">
        <div class="memory-text">\${text}\${text.length >= 300 ? '...' : ''}</div>
        <div class="memory-meta">
          <span class="badge">\${cat}</span>
          <span>重要性: \${imp}</span>
          \${score ? '<span class="score">匹配 ' + score + '</span>' : ''}
        </div>
      </div>\`;
    }).join('');
  } catch(e) { console.error(e); }
}

function showAddForm() { document.getElementById('add-form').style.display = 'block'; }
function hideAddForm() { document.getElementById('add-form').style.display = 'none'; }

async function addMemory() {
  const text = document.getElementById('new-text').value.trim();
  const category = document.getElementById('new-category').value.trim() || 'general';
  const importance = parseFloat(document.getElementById('new-importance').value) || 0.5;
  if (!text) { showAlert('请输入记忆内容', 'error'); return; }
  try {
    const r = await fetch('/api/memories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, category, importance })
    });
    const d = await r.json();
    if (d.success) {
      showAlert('✅ 记忆已添加', 'success');
      hideAddForm();
      document.getElementById('new-text').value = '';
      loadMemories();
      loadStatus();
    } else {
      showAlert('❌ 添加失败', 'error');
    }
  } catch(e) { showAlert('❌ ' + e.message, 'error'); }
}

document.getElementById('search-input').addEventListener('keypress', async (e) => {
  if (e.key !== 'Enter') return;
  const q = e.target.value.trim();
  if (!q) return;
  const r = await fetch('/api/search?q=' + encodeURIComponent(q));
  const d = await r.json();
  const list = document.getElementById('memories-list');
  if (!d.results || d.results.length === 0) {
    list.innerHTML = '<p class="empty">未找到相关记忆</p>';
    return;
  }
  list.innerHTML = d.results.map(m => {
    const text = (m.text || '').replace(/</g, '&lt;').replace(/>/g, '&gt;').slice(0, 300);
    return \`<div class="memory-item">
      <div class="memory-text">\${text}\${text.length >= 300 ? '...' : ''}</div>
      <div class="memory-meta">
        <span class="badge">\${m.category || 'general'}</span>
        <span class="score">匹配 \${Math.round(m.score * 100)}%</span>
      </div>
    </div>\`;
  }).join('');
});

loadStatus();
loadMemories();
</script>
</body>
</html>`;

/**
 * Graph page HTML
 */
const GRAPH_HTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>📊 知识图谱 - 统一记忆系统</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
h1 { font-size: 2rem; background: linear-gradient(135deg, #10b981, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
nav a { color: #94a3b8; text-decoration: none; margin-left: 1.5rem; font-size: 0.95rem; }
nav a:hover { color: #3b82f6; }
nav a.active { color: #3b82f6; border-bottom: 2px solid #3b82f6; }
.graph-container { background: #1e293b; border-radius: 12px; padding: 2rem; min-height: 500px; }
.info-card { background: #0f172a; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; }
.info-card h3 { color: #3b82f6; margin-bottom: 0.75rem; font-size: 1rem; }
.info-row { display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #334155; color: #94a3b8; font-size: 0.9rem; }
.info-row:last-child { border-bottom: none; }
.empty { color: #64748b; text-align: center; padding: 3rem; }
.footer { text-align: center; color: #475569; font-size: 0.8rem; padding: 2rem 0; }
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>📊 知识图谱</h1>
    <nav>
      <a href="/">Dashboard</a>
      <a href="/graph" class="active">知识图谱</a>
      <a href="/backups">备份</a>
    </nav>
  </header>

  <div class="graph-container">
    <div class="info-card">
      <h3>图谱统计</h3>
      <div id="graph-info">
        <div class="info-row"><span>实体数量</span><span id="entity-count">-</span></div>
        <div class="info-row"><span>关系数量</span><span id="relation-count">-</span></div>
        <div class="info-row"><span>节点总数</span><span id="node-count">-</span></div>
        <div class="info-row"><span>边总数</span><span id="edge-count">-</span></div>
      </div>
    </div>

    <div class="info-card">
      <h3>最近实体</h3>
      <div id="entities" class="empty">加载中...</div>
    </div>
  </div>

  <div class="footer">Unified Memory System v1.0</div>
</div>
<script>
async function loadGraph() {
  try {
    const r = await fetch('/api/graph');
    const d = await r.json();
    document.getElementById('entity-count').textContent = (d.entities || []).length;
    document.getElementById('relation-count').textContent = (d.relations || []).length;
    document.getElementById('node-count').textContent = d.node_count || 0;
    document.getElementById('edge-count').textContent = d.edge_count || 0;
    
    const entities = d.entities || [];
    const el = document.getElementById('entities');
    if (entities.length === 0) {
      el.innerHTML = '<p class="empty">暂无实体数据，运行 "memory graph build" 构建图谱</p>';
    } else {
      el.innerHTML = entities.slice(0, 20).map(e => 
        '<div class="info-row"><span>' + e + '</span></div>'
      ).join('');
    }
  } catch(e) { console.error(e); }
}
loadGraph();
</script>
</body>
</html>`;

/**
 * Backups page HTML
 */
const BACKUPS_HTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🗂️ 备份管理 - 统一记忆系统</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
h1 { font-size: 2rem; background: linear-gradient(135deg, #f59e0b, #ef4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
nav a { color: #94a3b8; text-decoration: none; margin-left: 1.5rem; font-size: 0.95rem; }
nav a:hover { color: #3b82f6; }
nav a.active { color: #3b82f6; border-bottom: 2px solid #3b82f6; }
.section { background: #1e293b; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
.info-row { display: flex; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid #334155; color: #94a3b8; }
.info-row:last-child { border-bottom: none; }
.info-row span:first-child { color: #e2e8f0; }
.empty { color: #64748b; text-align: center; padding: 2rem; }
.btn { background: #3b82f6; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer; font-size: 0.95rem; }
.btn:hover { background: #2563eb; }
.btn-danger { background: #dc2626; }
.btn-danger:hover { background: #b91c1c; }
.footer { text-align: center; color: #475569; font-size: 0.8rem; padding: 2rem 0; }
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>🗂️ 备份管理</h1>
    <nav>
      <a href="/">Dashboard</a>
      <a href="/graph">知识图谱</a>
      <a href="/backups" class="active">备份</a>
    </nav>
  </header>

  <div class="section">
    <h2 style="margin-bottom:1rem;">备份统计</h2>
    <div id="backup-stats">
      <div class="info-row"><span>备份数量</span><span id="backup-count">-</span></div>
      <div class="info-row"><span>总大小</span><span id="backup-size">-</span></div>
      <div class="info-row"><span>最新备份</span><span id="newest-backup">-</span></div>
      <div class="info-row"><span>最旧备份</span><span id="oldest-backup">-</span></div>
    </div>
  </div>

  <div class="section">
    <h2 style="margin-bottom:1rem;">可用备份</h2>
    <div id="backup-list"><p class="empty">加载中...</p></div>
  </div>

  <div class="footer">Unified Memory System v1.0</div>
</div>
<script>
async function loadBackups() {
  try {
    const r = await fetch('/api/status');
    const d = await r.json();
    const bs = d.backup || {};
    document.getElementById('backup-count').textContent = bs.backup_count || 0;
    document.getElementById('backup-size').textContent = (bs.total_size_mb || 0) + ' MB';
    document.getElementById('newest-backup').textContent = bs.newest_backup || '无';
    document.getElementById('oldest-backup').textContent = bs.oldest_backup || '无';
    
    const rb = await fetch('/api/backups');
    const bd = await rb.json();
    const bl = document.getElementById('backup-list');
    if (!bd.backups || bd.backups.length === 0) {
      bl.innerHTML = '<p class="empty">暂无备份</p>';
    } else {
      bl.innerHTML = bd.backups.map(b => 
        '<div class="info-row"><span>' + b.filename + '</span><span>' + b.memory_count + ' 条 | ' + b.created + '</span></div>'
      ).join('');
    }
  } catch(e) { console.error(e); }
}
loadBackups();
</script>
</body>
</html>`;

/**
 * Request handler
 */
async function handleRequest(req, res) {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const path = url.pathname;
  const query = url.searchParams;

  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  try {
    // Serve HTML pages
    if (path === '/' || path === '/index.html') {
      return sendHTML(res, 200, DASHBOARD_HTML);
    }
    if (path === '/graph') {
      return sendHTML(res, 200, GRAPH_HTML);
    }
    if (path === '/backups') {
      return sendHTML(res, 200, BACKUPS_HTML);
    }

    // API routes
    if (path.startsWith('/api/')) {
      return handleAPI(req, res, path, query);
    }

    sendHTML(res, 200, DASHBOARD_HTML);
  } catch (err) {
    log('ERROR', `Dashboard error: ${err.message}`);
    sendJSON(res, 500, { error: err.message });
  }
}

/**
 * Start the dashboard server
 */
export function startDashboard(port = PORT) {
  const server = createServer(handleRequest);
  server.listen(port, () => {
    log('INFO', `🌐 Dashboard running at http://localhost:${port}/`);
    log('INFO', `   Graph: http://localhost:${port}/graph`);
    log('INFO', `   Backups: http://localhost:${port}/backups`);
    log('INFO', `   API: http://localhost:${port}/api/status`);
  });
  return server;
}

// CLI
if (process.argv[1] && process.argv[1].endsWith('dashboard.js')) {
  startDashboard();
}
