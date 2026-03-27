#!/usr/bin/env node
/**
 * Dashboard HTTP server - serves memories.json via REST API
 * Runs independently, does NOT start the MCP server
 */
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = 3848;
const MEMORY_FILE = process.env.HOME + '/.openclaw/workspace/memory/memories.json';

function loadMemories() {
  try {
    return JSON.parse(fs.readFileSync(MEMORY_FILE, 'utf8'));
  } catch { return []; }
}

function saveMemories(data) {
  fs.writeFileSync(MEMORY_FILE, JSON.stringify(data, null, 2), 'utf8');
}

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.ico': 'image/x-icon',
};

const dashboardPath = path.join(__dirname, 'webui', 'dashboard.html');

const server = http.createServer((req, res) => {
  const url = req.url.split('?')[0];
  const ip = req.socket.remoteAddress;

  // Dashboard UI
  if (url === '/' || url === '/dashboard') {
    fs.readFile(dashboardPath, 'utf8', (err, data) => {
      if (err) { res.writeHead(404); res.end('Not found'); return; }
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(data);
    });
    return;
  }

  // REST API
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');

  try {
    if (url === '/memories' && req.method === 'GET') {
      res.end(JSON.stringify(loadMemories()));
      return;
    }
    if (url === '/stats') {
      const all = loadMemories();
      const byCategory = {}, byTier = { HOT: 0, WARM: 0, COLD: 0 }, byScope = {};
      all.forEach(m => {
        byCategory[m.category || 'unknown'] = (byCategory[m.category || 'unknown'] || 0) + 1;
        if (m.tier) byTier[m.tier]++;
        if (m.scope) byScope[m.scope] = (byScope[m.scope] || 0) + 1;
      });
      res.end(JSON.stringify({ total: all.length, byCategory, byTier, byScope, memoryCount: all.length }));
      return;
    }
    const delMatch = url.match(/^\/memories\/(.+)/);
    if (delMatch && req.method === 'DELETE') {
      const id = decodeURIComponent(delMatch[1]);
      const memories = loadMemories().filter(m => m.id !== id);
      saveMemories(memories);
      res.end(JSON.stringify({ success: true }));
      return;
    }
    if (url === '/memories' && req.method === 'POST') {
      let body = '';
      req.on('data', c => body += c);
      req.on('end', () => {
        try {
          const { text, category, importance, tags } = JSON.parse(body);
          const mem = {
            id: `mem_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
            category: category || 'general',
            content: text,
            importance: importance || 0.7,
            tags: tags || [],
            created_at: new Date().toISOString(),
            last_accessed: new Date().toISOString(),
            access_count: 0,
            scope: 'USER',
            metadata: {}
          };
          const memories = loadMemories();
          memories.push(mem);
          saveMemories(memories);
          res.end(JSON.stringify(mem));
        } catch {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'Invalid request' }));
        }
      });
      return;
    }
    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Not found' }));
  } catch (e) {
    res.writeHead(500);
    res.end(JSON.stringify({ error: e.message }));
  }
});

server.listen(PORT, () => {
  console.log(`Dashboard: http://localhost:${PORT}`);
  console.log(`Memory file: ${MEMORY_FILE}`);
});
