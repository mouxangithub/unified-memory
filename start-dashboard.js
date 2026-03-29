#!/usr/bin/env node
/**
 * Unified Memory v3.0 — All-in-One Dashboard Server
 * Serves the v3.0 HTML UI + full REST API on port 3848
 */
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { homedir } from 'os';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = 3848;
const HOME = homedir();
const WORKSPACE = path.join(HOME, '.openclaw', 'workspace');
const MEMORY_FILE = path.join(WORKSPACE, 'memory', 'memories.json');
const VECTOR_DB_DIR = path.join(HOME, '.unified-memory', 'vector.lance');

const dashboardPath = path.join(__dirname, 'webui', 'dashboard.html');

// ── Data Loading ──────────────────────────────────────
function loadMemories() {
  try {
    if (!existsSync(MEMORY_FILE)) return [];
    const data = JSON.parse(readFileSync(MEMORY_FILE, 'utf-8'));
    return Array.isArray(data) ? data : (data.memories || []);
  } catch { return []; }
}

function saveMemories(data) {
  try {
    mkdirSync(path.dirname(MEMORY_FILE), { recursive: true });
    writeFileSync(MEMORY_FILE, JSON.stringify(data, null, 2), 'utf-8');
  } catch (e) { /* ignore */ }
}

// ── Stats Computation ──────────────────────────────────
let _statsCache = null;
let _statsCacheTime = 0;
const STATS_CACHE_TTL = 2000;

function computeStats() {
  const now = Date.now();
  if (_statsCache && (now - _statsCacheTime) < STATS_CACHE_TTL) {
    return _statsCache;
  }

  const memories = loadMemories();
  const byCategory = {}, byScope = { AGENT: 0, USER: 0, TEAM: 0, GLOBAL: 0, unknown: 0 };
  const byTier = { HOT: 0, WARM: 0, COLD: 0 };
  const byImportance = { high: 0, medium: 0, low: 0 };
  const tagCount = {};

  for (const m of memories) {
    const cat = m.category || 'unknown';
    byCategory[cat] = (byCategory[cat] || 0) + 1;

    const scope = m.scope || 'unknown';
    if (scope in byScope) byScope[scope]++;
    else byScope.unknown++;

    if (m.tier) byTier[m.tier] = (byTier[m.tier] || 0) + 1;

    const imp = m.importance ?? 0.5;
    if (imp >= 0.7) byImportance.high++;
    else if (imp >= 0.4) byImportance.medium++;
    else byImportance.low++;

    if (Array.isArray(m.tags)) {
      for (const t of m.tags) tagCount[t] = (tagCount[t] || 0) + 1;
    }
  }

  const topTags = Object.entries(tagCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([tag, count]) => ({ tag, count }));

  // 7-day growth
  const sevenDaysAgo = new Date(now - 7 * 24 * 60 * 60 * 1000);
  const growth7d = memories.filter(m => new Date(m.created_at) >= sevenDaysAgo).length;

  // 14-day growth trend
  const growthTrend = [];
  for (let i = 13; i >= 0; i--) {
    const dayStart = new Date(now - i * 24 * 60 * 60 * 1000);
    dayStart.setHours(0, 0, 0, 0);
    const dayEnd = new Date(dayStart);
    dayEnd.setDate(dayEnd.getDate() + 1);
    const count = memories.filter(m => {
      const d = new Date(m.created_at);
      return d >= dayStart && d < dayEnd;
    }).length;
    growthTrend.push({ label: `${dayStart.getMonth() + 1}/${dayStart.getDate()}`, count });
  }

  // Total accesses
  const totalAccessCount = memories.reduce((s, m) => s + (m.access_count || 0), 0);
  const accessCounts = memories.map(m => m.access_count || 0).filter(x => x > 0);

  _statsCache = {
    total: memories.length,
    byCategory,
    byScope,
    byTier,
    byImportance,
    totalAccessCount,
    avgAccessCount: accessCounts.length ? (totalAccessCount / accessCounts.length).toFixed(2) : '0',
    growth7d,
    growthTrend,
    topTags,
  };
  _statsCacheTime = now;
  return _statsCache;
}

// ── Health Check ──────────────────────────────────────
async function getHealth() {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    memoryFile: { status: 'unknown' },
    storage: { status: 'unknown', used: 0, total: 0, percent: 0 },
  };

  try {
    if (existsSync(MEMORY_FILE)) {
      const stat = fs.statSync(MEMORY_FILE);
      health.memoryFile = { status: 'ok', size: stat.size, sizeMB: (stat.size / 1024 / 1024).toFixed(2), path: MEMORY_FILE };
    } else {
      health.memoryFile = { status: 'not_found', path: MEMORY_FILE };
    }
  } catch (e) {
    health.memoryFile = { status: 'error', error: e.message };
  }

  try {
    health.storage.path = WORKSPACE;
    const { execSync } = await import('child_process');
    const df = execSync('df -B1 ' + WORKSPACE + ' 2>/dev/null').toString().split('\n')[1];
    if (df) {
      const parts = df.split(/\s+/);
      const total = parseInt(parts[1]) || 0;
      const used = parseInt(parts[2]) || 0;
      health.storage.total = total;
      health.storage.used = used;
      health.storage.percent = total > 0 ? Math.round((used / total) * 100) : 0;
      health.storage.status = health.storage.percent > 90 ? 'critical' : health.storage.percent > 75 ? 'warning' : 'ok';
    }
  } catch { /* ignore */ }

  return health;
}

// ── Request Handler ────────────────────────────────────
async function handleRequest(req, res) {
  const url = req.url.split('?')[0];
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  // ── HTML Dashboard (v3.0) ─────────────────────────
  if ((url === '/' || url === '/dashboard') && req.method === 'GET') {
    fs.readFile(dashboardPath, 'utf8', (err, data) => {
      if (err) { res.writeHead(404); res.end('Not found'); return; }
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(data);
    });
    return;
  }

  // ── REST API ─────────────────────────────────────
  res.setHeader('Content-Type', 'application/json');

  try {
    // GET /memories — list all
    if (url === '/memories' && req.method === 'GET') {
      res.end(JSON.stringify(loadMemories()));
      return;
    }

    // GET /stats — computed stats
    if (url === '/stats' && req.method === 'GET') {
      res.end(JSON.stringify(computeStats()));
      return;
    }

    // GET /health — health check
    if (url === '/health' && req.method === 'GET') {
      const h = await getHealth();
      res.end(JSON.stringify(h));
      return;
    }

    // GET /api/stats — alias for stats (v2.7 compatibility)
    if (url === '/api/stats' && req.method === 'GET') {
      res.end(JSON.stringify(computeStats()));
      return;
    }

    // GET /api/memories — alias (v2.7 compatibility)
    if (url === '/api/memories' && req.method === 'GET') {
      res.end(JSON.stringify(loadMemories()));
      return;
    }

    // GET /api/health — alias (v2.7 compatibility)
    if (url === '/api/health' && req.method === 'GET') {
      res.end(JSON.stringify(await getHealth()));
      return;
    }

    // DELETE /memories/:id
    const delMatch = url.match(/^\/memories\/(.+)/);
    if (delMatch && req.method === 'DELETE') {
      const id = decodeURIComponent(delMatch[1]);
      const memories = loadMemories().filter(m => m.id !== id);
      saveMemories(memories);
      _statsCache = null;
      res.end(JSON.stringify({ success: true }));
      return;
    }

    // POST /memories — create
    if (url === '/memories' && req.method === 'POST') {
      let body = '';
      req.on('data', c => body += c);
      req.on('end', () => {
        try {
          const { text, category, importance, scope, tags } = JSON.parse(body);
          if (!text || !text.trim()) {
            res.writeHead(400); res.end(JSON.stringify({ error: 'text is required' })); return;
          }
          const mem = {
            id: `mem_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
            category: category || 'general',
            content: text.trim(),
            importance: Math.max(0, Math.min(1, importance ?? 0.7)),
            tags: Array.isArray(tags) ? tags : [],
            created_at: new Date().toISOString(),
            last_accessed: new Date().toISOString(),
            access_count: 1,
            scope: scope || 'USER',
          };
          const memories = loadMemories();
          memories.unshift(mem);
          saveMemories(memories);
          _statsCache = null;
          res.end(JSON.stringify(mem));
        } catch (e) {
          res.writeHead(400); res.end(JSON.stringify({ error: e.message }));
        }
      });
      return;
    }

    // 404
    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Not found: ' + url }));
  } catch (e) {
    res.writeHead(500);
    res.end(JSON.stringify({ error: e.message }));
  }
}

// ── Start Server ──────────────────────────────────────
http.createServer((req, res) => handleRequest(req, res)).listen(PORT, () => {
  console.log(`\n✅ Unified Memory v3.0 — Dashboard`);
  console.log(`   URL:      http://localhost:${PORT}`);
  console.log(`   API:      http://localhost:${PORT}/memories`);
  console.log(`   Stats:    http://localhost:${PORT}/stats`);
  console.log(`   Health:   http://localhost:${PORT}/health`);
  console.log(`   Memory:   ${MEMORY_FILE}\n`);
});
