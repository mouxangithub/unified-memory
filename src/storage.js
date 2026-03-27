import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';
import { config } from './config.js';
import { acquireLockSync, releaseLockSync, initWalStorage, logWriteOp } from './storage_lock.js';
import { logOp, readWal, closeWal } from './wal.js';

/**
 * @typedef {import('./types.js').Memory} Memory
 */

/** @type {Map<string, Memory[]>} */
const memoryCache = new Map();
let cacheDirty = false;

/**
 * @returns {Memory[]}
 */
export function loadMemories() {
  if (!existsSync(config.memoryFile)) {
    return [];
  }
  try {
    const data = JSON.parse(readFileSync(config.memoryFile, 'utf8'));
    return Array.isArray(data) ? data : (data.memories || []);
  } catch {
    return [];
  }
}

/**
 * Save memories to disk
 * @param {Memory[]} memories
 */
export function saveMemories(memories) {
  // 初始化 WAL（首次调用时）
  if (!global._walInit) {
    try {
      initWalStorage();
      global._walInit = true;
    } catch { /* WAL init failure is non-fatal */ }
  }

  // 原子写入：锁 + WAL 预写 + rename
  const lockPath = config.memoryFile;
  acquireLockSync(lockPath);
  try {
    // WAL 预写（crash recovery 用）
    if (global._walInit) {
      logWriteOp({ type: 'save', count: memories.length });
    }

    const data = JSON.stringify(memories, null, 2);
    writeFileSync(lockPath, data, 'utf8');
  } finally {
    releaseLockSync(lockPath);
  }

  memoryCache.set('all', memories);
  cacheDirty = false;
}

/**
 * Get all memories (with caching)
 * @returns {Memory[]}
 */
export function getAllMemories() {
  if (!memoryCache.has('all')) {
    memoryCache.set('all', loadMemories());
  }
  // Normalize: support both 'content' (import format) and 'text' field
  return memoryCache.get('all').map((m) => ({
    ...m,
    text: m.text || m.content || '',
    // Normalize timestamp fields (JSON import uses 'timestamp', our schema uses 'created_at')
    created_at: m.created_at || (m.timestamp ? new Date(m.timestamp).getTime() : Date.now()),
  }));
}

/**
 * Invalidate cache
 */
export function invalidateCache() {
  memoryCache.delete('all');
}

/**
 * Add a new memory
 * @param {Omit<Memory, 'id' | 'created_at' | 'updated_at' | 'access_count' | 'last_access'>} mem
 * @returns {Memory}
 */
export function addMemory(mem) {
  const memories = getAllMemories();
  const now = Date.now();
  /** @type {Memory} */
  const newMem = {
    id: `mem_${now}_${Math.random().toString(36).slice(2, 8)}`,
    text: mem.text,
    category: mem.category || 'general',
    importance: mem.importance || 0.5,
    tags: mem.tags || [],
    created_at: now,
    updated_at: now,
    access_count: 0,
    last_access: now,
  };
  memories.push(newMem);
  saveMemories(memories);
  return newMem;
}

/**
 * Delete a memory by id
 * @param {string} id
 * @returns {boolean}
 */
export function deleteMemory(id) {
  const memories = getAllMemories();
  const idx = memories.findIndex((m) => m.id === id);
  if (idx === -1) return false;
  memories.splice(idx, 1);
  saveMemories(memories);
  return true;
}

/**
 * Get a memory by id
 * @param {string} id
 * @returns {Memory|undefined}
 */
export function getMemory(id) {
  const memories = getAllMemories();
  return memories.find((m) => m.id === id);
}

/**
 * Update access stats
 * @param {string} id
 */
export function touchMemory(id) {
  const memories = getAllMemories();
  const mem = memories.find((m) => m.id === id);
  if (mem) {
    mem.access_count = (mem.access_count || 0) + 1;
    mem.last_access = Date.now();
    saveMemories(memories);
  }
}
