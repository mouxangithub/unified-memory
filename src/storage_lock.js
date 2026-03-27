/**
 * Storage Concurrency Lock + WAL Integration v1.0
 * 文件锁机制：flock-style write lock，防止并发写冲突
 * WAL机制：每次写操作先记日志再应用，支持crash恢复
 */

import * as fs from 'fs';
import { writeFileSync, readFileSync, existsSync, unlinkSync, renameSync, mkdirSync, openSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const LOCK_FILE_SUFFIX = '.lock';
const WAL_DIR = join(__dirname, '..', 'wal');

// ─── 文件锁实现（进程级） ───────────────────────────────────────────────────

const locks = new Map();

/**
 * 异步获取文件锁
 * @param {string} filePath
 * @param {number} timeoutMs
 */
export async function acquireLock(filePath, timeoutMs = 5000) {
  const lockPath = filePath + LOCK_FILE_SUFFIX;
  const start = Date.now();

  while (existsSync(lockPath)) {
    if (Date.now() - start > timeoutMs) {
      throw new Error(`Lock timeout for ${filePath} after ${timeoutMs}ms`);
    }
    await sleep(50);
  }

  writeFileSync(lockPath, JSON.stringify({ pid: process.pid, ts: Date.now() }), 'utf8');
  locks.set(filePath, lockPath);
}

/**
 * 释放文件锁
 * @param {string} filePath
 */
export function releaseLock(filePath) {
  const lockPath = filePath + LOCK_FILE_SUFFIX;
  try {
    if (existsSync(lockPath)) unlinkSync(lockPath);
  } catch { /* ignore */ }
  locks.delete(filePath);
}

/**
 * 同步获取文件锁（适配 Node.js fs 同步 API）
 * @param {string} filePath
 * @param {number} timeoutMs
 */
export function acquireLockSync(filePath, timeoutMs = 5000) {
  const lockPath = filePath + LOCK_FILE_SUFFIX;
  const start = Date.now();

  while (existsSync(lockPath)) {
    if (Date.now() - start > timeoutMs) {
      // 超时强制抢锁（防止死锁）
      break;
    }
  }

  writeFileSync(lockPath, JSON.stringify({ pid: process.pid, ts: Date.now() }), 'utf8');
  locks.set(filePath, lockPath);
}

/**
 * 同步释放文件锁
 * @param {string} filePath
 */
export function releaseLockSync(filePath) {
  const lockPath = filePath + LOCK_FILE_SUFFIX;
  try {
    unlinkSync(lockPath);
  } catch { /* ignore */ }
  locks.delete(filePath);
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// ─── WAL 集成 ──────────────────────────────────────────────────────────────

let walFd = null;
let walRunId = null;
let walPath = null;

function ensureWalDir() {
  if (!existsSync(WAL_DIR)) mkdirSync(WAL_DIR, { recursive: true });
}

/**
 * 初始化 WAL 存储
 * @param {string} [runId]
 */
export function initWalStorage(runId) {
  ensureWalDir();
  walRunId = runId || `store-${Date.now()}`;
  walPath = join(WAL_DIR, `${walRunId}.wal.jsonl`);
  walFd = openSync(walPath, 'a');
}

/**
 * 记录写操作到 WAL
 * @param {object} op
 */
export function logWriteOp(op) {
  if (!walFd) return;
  const entry = JSON.stringify({ ...op, ts: Date.now() }) + '\n';
  const buf = Buffer.from(entry, 'utf8');
  // Use fs.writeSync for numeric file descriptor
  fs.writeSync(walFd, buf);
}

/**
 * 获取当前 WAL 文件描述符
 */
export function getWalFd() {
  return walFd;
}

/**
 * 获取 WAL 目录
 */
export function getWalDir() {
  return WAL_DIR;
}

// ─── 原子写入 ──────────────────────────────────────────────────────────────

/**
 * 原子保存（锁 + WAL + rename）
 * @param {string} filePath
 * @param {string} data
 * @param {object|null} walOp
 */
export async function atomicSave(filePath, data, walOp = null) {
  await acquireLock(filePath);
  try {
    if (walOp) logWriteOp(walOp);
    const tmpPath = `${filePath}.tmp.${process.pid}`;
    writeFileSync(tmpPath, data, 'utf8');
    renameSync(tmpPath, filePath);
  } finally {
    releaseLock(filePath);
  }
}

// ─── WAL Recovery ──────────────────────────────────────────────────────────

/**
 * 从 WAL 文件恢复数据
 * 读取 wal/*.wal.jsonl，按时间顺序重放 add/delete 操作
 * @param {string[]} walFiles - WAL 文件列表
 * @param {string} targetFile - 目标数据文件路径
 * @param {object[]} memories - 当前内存中的数据
 * @returns {object[]} 恢复后的 memories
 */
export function recoverFromWAL(walFiles, targetFile, memories) {
  const memMap = new Map(memories.map(m => [m.id, m]));

  for (const walFile of walFiles) {
    try {
      const lines = readFileSync(join(WAL_DIR, walFile), 'utf8')
        .trim().split('\n').filter(Boolean);

      for (const line of lines) {
        const op = JSON.parse(line);
        const { type, memory, memory_id: delId } = op;

        if (type === 'add' && memory) {
          memMap.set(memory.id, memory);
        } else if (type === 'delete' && delId) {
          memMap.delete(delId);
        }
      }
    } catch { /* skip corrupted WAL files */ }
  }

  return Array.from(memMap.values());
}
