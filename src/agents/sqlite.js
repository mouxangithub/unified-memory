/**
 * SQLite Persistence Layer
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';

const WORKSPACE = join(process.env.HOME || '/root', '.openclaw', 'workspace');
const MEMORY_DIR = join(WORKSPACE, 'memory');

function loadMemories() {
  const file = join(MEMORY_DIR, 'memories.json');
  if (!existsSync(file)) return [];
  try { return JSON.parse(readFileSync(file, 'utf-8')); }
  catch { return []; }
}

function saveMemories(memories) {
  mkdirSync(MEMORY_DIR, { recursive: true });
  writeFileSync(join(MEMORY_DIR, 'memories.json'), JSON.stringify(memories, null, 2), 'utf-8');
}

export async function store(memory) {
  const memories = loadMemories();
  const now = new Date().toISOString();
  const mem = {
    id: memory.id || `mem_${Date.now()}`,
    text: memory.text || '',
    category: memory.category || 'general',
    importance: memory.importance ?? 0.5,
    confidence: memory.confidence ?? 0.8,
    tags: memory.tags || [],
    project: memory.project || 'default',
    created_at: memory.created_at || now,
    updated_at: now,
    accessed_at: now,
    access_count: 0,
  };
  const idx = memories.findIndex(m => m.id === mem.id);
  if (idx >= 0) memories[idx] = mem;
  else memories.push(mem);
  saveMemories(memories);
  return true;
}

export async function get(id) {
  const memories = loadMemories();
  return memories.find(m => m.id === id) || null;
}

export async function remove(id) {
  const memories = loadMemories();
  const idx = memories.findIndex(m => m.id === id);
  if (idx === -1) return false;
  memories.splice(idx, 1);
  saveMemories(memories);
  return true;
}

export async function search(query, limit = 10) {
  const memories = loadMemories();
  const q = query.toLowerCase();
  return memories.filter(m => (m.text || '').toLowerCase().includes(q) || (m.tags || []).some(t => t.toLowerCase().includes(q))).slice(0, limit);
}

export async function getAll(limit = 100) {
  return loadMemories().slice(0, limit);
}

export async function count() {
  return loadMemories().length;
}

if (require.main === module) {
  console.log('\n📦 SQLite Storage Layer\n');
  console.log('  SQLite wrapper - uses JSON file storage');
  console.log('  For production, install better-sqlite3\n');
}
