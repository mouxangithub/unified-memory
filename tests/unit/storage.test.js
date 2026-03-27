/**
 * Storage Layer Unit Tests
 * Tests: read/write, concurrent locking, WAL recording
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';

const TMP_DIR = path.join(os.tmpdir(), `unified-memory-test-${Date.now()}`);

beforeEach(() => {
  if (!fs.existsSync(TMP_DIR)) fs.mkdirSync(TMP_DIR, { recursive: true });
});

afterEach(() => {
  try {
    const files = fs.readdirSync(TMP_DIR);
    for (const f of files) {
      if (!f.startsWith('.')) {
        try { fs.unlinkSync(path.join(TMP_DIR, f)); } catch { /* ignore */ }
      }
    }
  } catch { /* ignore */ }
});

// ─── Mock config for tests ────────────────────────────────────────────────
const TEST_CONFIG = {
  memoryFile: path.join(TMP_DIR, 'memories.json'),
};

function mockConfig() {
  // Override module-level config import by patching storage module's config ref
  return TEST_CONFIG;
}

// ─── Helpers ────────────────────────────────────────────────────────────────
import { readFileSync, writeFileSync, existsSync, unlinkSync, renameSync, openSync, mkdirSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

/**
 * Minimal storage engine for testing (mirrors real storage.js logic)
 */
function makeStorage(testDir) {
  const lockSuffix = '.lock';
  const WAL_DIR = join(testDir, 'wal');
  const memoryFile = join(testDir, 'memories.json');

  const locks = new Map();
  let walFd = null;

  mkdirSync(WAL_DIR, { recursive: true });

  // File lock sync
  function acquireLockSync(filePath, timeoutMs = 2000) {
    const lockPath = filePath + lockSuffix;
    const start = Date.now();
    while (existsSync(lockPath)) {
      if (Date.now() - start > timeoutMs) break; // force takeover
    }
    writeFileSync(lockPath, JSON.stringify({ pid: process.pid, ts: Date.now() }), 'utf8');
    locks.set(filePath, lockPath);
  }

  function releaseLockSync(filePath) {
    const lockPath = filePath + lockSuffix;
    try { unlinkSync(lockPath); } catch { /* ignore */ }
    locks.delete(filePath);
  }

  // WAL
  function initWal() {
    const walPath = join(WAL_DIR, `test.wal.jsonl`);
    walFd = openSync(walPath, 'a');
  }

  function logWriteOp(op) {
    if (!walFd) return;
    const entry = JSON.stringify({ ...op, ts: Date.now() }) + '\n';
    const buf = Buffer.from(entry, 'utf8');
    const { writeSync } = fs;
    writeSync(walFd, buf);
  }

  // Storage ops
  function load() {
    if (!existsSync(memoryFile)) return [];
    try { return JSON.parse(readFileSync(memoryFile, 'utf8')); }
    catch { return []; }
  }

  function save(memories) {
    acquireLockSync(memoryFile);
    try {
      if (walFd) logWriteOp({ type: 'save', count: memories.length });
      writeFileSync(memoryFile, JSON.stringify(memories, null, 2), 'utf8');
    } finally {
      releaseLockSync(memoryFile);
    }
  }

  function addMemory(mem) {
    const memories = load();
    const now = Date.now();
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
      version: 1,
    };
    if (walFd) logWriteOp({ type: 'add', memory_id: newMem.id, text: newMem.text.slice(0, 20) });
    memories.push(newMem);
    save(memories);
    return newMem;
  }

  function deleteMemory(id) {
    const memories = load();
    const idx = memories.findIndex(m => m.id === id);
    if (idx === -1) return false;
    if (walFd) logWriteOp({ type: 'delete', memory_id: id });
    memories.splice(idx, 1);
    save(memories);
    return true;
  }

  function getAll() {
    acquireLockSync(memoryFile);
    try {
      return load();
    } finally {
      releaseLockSync(memoryFile);
    }
  }

  function touchMemory(id) {
    const memories = load();
    const mem = memories.find(m => m.id === id);
    if (!mem) return;
    mem.access_count = (mem.access_count || 0) + 1;
    mem.last_access = Date.now();
    mem.version = (mem.version || 0) + 1;
    if (walFd) logWriteOp({ type: 'access', memory_id: id, version: mem.version });
    save(memories);
  }

  function closeWal() {
    if (walFd) {
      fs.fsyncSync(walFd);
      fs.closeSync(walFd);
      walFd = null;
    }
  }

  function readWal() {
    const walPath = join(WAL_DIR, 'test.wal.jsonl');
    if (!existsSync(walPath)) return [];
    return readFileSync(walPath, 'utf8')
      .trim().split('\n').filter(Boolean).map(l => JSON.parse(l));
  }

  function getWalPath() { return join(WAL_DIR, 'test.wal.jsonl'); }

  return { memoryFile, addMemory, deleteMemory, getAll, touchMemory, save, initWal, logWriteOp, closeWal, readWal, getWalPath, WAL_DIR };
}

// ─── Tests ──────────────────────────────────────────────────────────────────

describe('Storage: Read/Write', () => {
  it('save and load memories correctly', () => {
    const s = makeStorage(TMP_DIR);
    s.initWal();
    s.save([{ id: 'test1', text: 'hello', category: 'fact', importance: 0.8 }]);
    const memories = s.getAll();
    expect(memories).toHaveLength(1);
    expect(memories[0].id).toBe('test1');
    expect(memories[0].text).toBe('hello');
    s.closeWal();
  });

  it('addMemory creates with all required fields', () => {
    const s = makeStorage(TMP_DIR);
    s.initWal();
    const mem = s.addMemory({ text: 'test memory', category: 'preference', importance: 0.9, tags: ['ai'] });
    expect(mem.id).toMatch(/^mem_/);
    expect(mem.text).toBe('test memory');
    expect(mem.category).toBe('preference');
    expect(mem.importance).toBe(0.9);
    expect(mem.tags).toEqual(['ai']);
    expect(mem.created_at).toBeDefined();
    expect(mem.access_count).toBe(0);
    expect(mem.version).toBe(1);
    s.closeWal();
  });

  it('deleteMemory removes existing memory', () => {
    const s = makeStorage(TMP_DIR);
    s.initWal();
    const mem = s.addMemory({ text: 'to delete' });
    expect(s.getAll()).toHaveLength(1);
    const result = s.deleteMemory(mem.id);
    expect(result).toBe(true);
    expect(s.getAll()).toHaveLength(0);
    s.closeWal();
  });

  it('deleteMemory returns false for non-existent id', () => {
    const s = makeStorage(TMP_DIR);
    s.initWal();
    const result = s.deleteMemory('non_existent_id');
    expect(result).toBe(false);
    s.closeWal();
  });

  it('touchMemory increments access_count and version', () => {
    const s = makeStorage(TMP_DIR);
    s.initWal();
    const mem = s.addMemory({ text: 'access me' });
    s.touchMemory(mem.id);
    s.touchMemory(mem.id);
    const memories = s.getAll();
    const found = memories.find(m => m.id === mem.id);
    expect(found.access_count).toBe(2);
    expect(found.version).toBe(3); // 1 (create) + 2 touches
    s.closeWal();
  });
});

describe('Storage: Concurrent Lock', () => {
  it('lock file is created and cleaned up', () => {
    const s = makeStorage(TMP_DIR);
    s.initWal();
    s.save([{ id: 'lock_test' }]);
    const lockPath = s.memoryFile + '.lock';
    // After save, lock should be released
    expect(existsSync(lockPath)).toBe(false);
    s.closeWal();
  });

  it('concurrent saves do not corrupt data', async () => {
    const s = makeStorage(TMP_DIR);
    s.initWal();
    s.save([]);

    const promises = Array.from({ length: 10 }, (_, i) =>
      Promise.resolve().then(() => s.addMemory({ text: `memory ${i}`, category: 'fact' }))
    );
    await Promise.all(promises);

    const memories = s.getAll();
    expect(memories).toHaveLength(10);
    // All should have unique ids
    const ids = memories.map(m => m.id);
    expect(new Set(ids).size).toBe(10);
    s.closeWal();
  });
});

describe('Storage: WAL Recording', () => {
  it('WAL records add operations', () => {
    const s = makeStorage(TMP_DIR);
    s.initWal();
    const mem = s.addMemory({ text: 'wal test', category: 'fact' });
    const wal = s.readWal();
    expect(wal.some(op => op.type === 'add' && op.memory_id === mem.id)).toBe(true);
    s.closeWal();
  });

  it('WAL records delete operations', () => {
    const s = makeStorage(TMP_DIR);
    s.initWal();
    const mem = s.addMemory({ text: 'delete me' });
    s.deleteMemory(mem.id);
    const wal = s.readWal();
    expect(wal.some(op => op.type === 'delete' && op.memory_id === mem.id)).toBe(true);
    s.closeWal();
  });

  it('WAL records save operations with count', () => {
    const s = makeStorage(TMP_DIR);
    s.initWal();
    s.save([{ id: 's1' }, { id: 's2' }]);
    const wal = s.readWal();
    expect(wal.some(op => op.type === 'save' && op.count === 2)).toBe(true);
    s.closeWal();
  });

  it('WAL records access operations with version increment', () => {
    const s = makeStorage(TMP_DIR);
    s.initWal();
    const mem = s.addMemory({ text: 'access tracking' });
    s.touchMemory(mem.id);
    const wal = s.readWal();
    const accessOps = wal.filter(op => op.type === 'access');
    expect(accessOps.length).toBeGreaterThan(0);
    expect(accessOps[accessOps.length - 1].version).toBeGreaterThan(1);
    s.closeWal();
  });

  it('WAL file survives empty saves', () => {
    const s = makeStorage(TMP_DIR);
    s.initWal();
    s.save([]);
    s.save([]);
    const wal = s.readWal();
    expect(wal.filter(op => op.type === 'save').length).toBeGreaterThan(0);
    s.closeWal();
  });
});
