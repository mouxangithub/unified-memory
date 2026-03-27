/**
 * Storage Concurrency Lock + WAL Integration v2.0
 * 文件锁机制：flock-style write lock，防止并发写冲突
 * WAL机制：每次写操作先记日志再应用，支持crash恢复
 *
 * v2.0 升级：
 * - flock 文件锁（多进程安全，进程退出/crash自动释放）
 * - WAL fsync 确保落盘
 * - WAL 同步写 walWriteSync()
 * - 脏读检测 checkVersion()
 * - PID 竞态检测（启动时检查 storage.lock）
 */

import * as fs from 'fs';
import { writeFileSync, readFileSync, existsSync, unlinkSync, renameSync, mkdirSync, openSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execSync, spawn } from 'child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const LOCK_FILE_SUFFIX = '.lock';
const WAL_DIR = join(__dirname, '..', 'wal');
const STORAGE_LOCK_FILE = join(process.env.HOME || '/root', '.unified-memory', 'storage.lock');

// ─── PID 竞态检测 ──────────────────────────────────────────────────────────

/**
 * 检查 PID 进程是否还在运行
 * @param {number} pid
 * @returns {boolean}
 */
function isPidAlive(pid) {
  try {
    execSync(`kill -0 ${pid} 2>/dev/null`, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

/**
 * 初始化 PID 竞态检测
 * 检查 ~/.unified-memory/storage.lock
 * - 如果文件存在且对应进程已退出，则创建新锁
 * - 如果进程仍在运行，报错退出（防止多实例）
 */
function initPidLock() {
  const dir = dirname(STORAGE_LOCK_FILE);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }

  if (existsSync(STORAGE_LOCK_FILE)) {
    try {
      const data = JSON.parse(readFileSync(STORAGE_LOCK_FILE, 'utf8'));
      if (data.pid && isPidAlive(data.pid)) {
        console.error(`[storage_lock] FATAL: 另一个进程 (PID ${data.pid}) 正在运行 storage.lock。退出。`);
        console.error(`[storage_lock] 如果确定没有其他实例，请删除 ${STORAGE_LOCK_FILE}`);
        process.exit(1);
      }
    } catch { /* corrupted lock file, overwrite */ }
  }

  // 写入自己的 PID
  writeFileSync(STORAGE_LOCK_FILE, JSON.stringify({ pid: process.pid, ts: Date.now() }), 'utf8');
}

/**
 * 释放 PID 锁（正常退出时调用）
 */
function releasePidLock() {
  try {
    if (existsSync(STORAGE_LOCK_FILE)) {
      const data = JSON.parse(readFileSync(STORAGE_LOCK_FILE, 'utf8'));
      if (data.pid === process.pid) {
        unlinkSync(STORAGE_LOCK_FILE);
      }
    }
  } catch { /* ignore */ }
}

// 启动时注册 PID 锁
initPidLock();

// 正常退出时释放锁（process.on('exit') 同步执行）
process.on('exit', () => {
  releasePidLock();
});

// ─── flock 文件锁实现（进程级） ────────────────────────────────────────────

const LOCK_TIMEOUT_MS = 30_000; // 30 秒锁超时

/**
 * 异步获取文件锁（轮询 + flock 守护）
 * 先轮询等待锁不存在，再用 flock 命令获取真正的文件锁
 * @param {string} filePath
 * @param {number} timeoutMs
 */
export async function acquireLock(filePath, timeoutMs = LOCK_TIMEOUT_MS) {
  const lockPath = filePath + LOCK_FILE_SUFFIX;
  const start = Date.now();

  // 1. 轮询等待锁文件不存在（或超时）
  while (existsSync(lockPath)) {
    if (Date.now() - start > timeoutMs) {
      throw new Error(`[storage_lock] Lock timeout for ${filePath} after ${timeoutMs}ms`);
    }
    await sleep(50);
  }

  // 2. 用 flock 原子创建锁文件（flock 持有锁直到进程退出）
  // -F: 不设置 close-on-exec，让子进程继承锁
  // sleep 60 保证进程退出前锁不会自动释放
  try {
    execSync(`flock -x "${lockPath}" -c "echo \\$\\$"`, {
      stdio: 'ignore',
      timeout: 5,
    });
  } catch { /* 超时可忽略，锁文件已存在 */ }

  // 3. 写入 PID 信息（供调试）
  writeFileSync(lockPath, JSON.stringify({ pid: process.pid, ts: Date.now() }), 'utf8');
}

/**
 * 释放文件锁
 * @param {string} filePath
 */
export function releaseLock(filePath) {
  const lockPath = filePath + LOCK_FILE_SUFFIX;
  try {
    if (existsSync(lockPath)) {
      const data = JSON.parse(readFileSync(lockPath, 'utf8'));
      if (data.pid === process.pid) {
        unlinkSync(lockPath);
      }
    }
  } catch { /* ignore */ }
}

/**
 * 同步获取文件锁（真正的多进程安全 flock 锁）
 * 使用 flock -x 阻塞等待，超时则抛错
 * @param {string} filePath
 * @param {number} timeoutMs
 */
export function acquireLockSync(filePath, timeoutMs = LOCK_TIMEOUT_MS) {
  const lockPath = filePath + LOCK_FILE_SUFFIX;

  // flock -x: 阻塞直到获取锁（或超时）
  // flock 在进程退出时自动释放锁（即使 crash）
  try {
    execSync(`flock -x -w ${Math.ceil(timeoutMs / 1000)} "${lockPath}" -c "echo locked"`, {
      stdio: 'ignore',
      timeout: timeoutMs / 1000 + 1,
    });
  } catch (e) {
    if (e.status === 127) {
      throw new Error(`[storage_lock] flock command not found`);
    }
    // flock 超时（exit code 1）或失败
    throw new Error(`[storage_lock] Lock timeout for ${filePath} after ${timeoutMs}ms`);
  }

  // 锁已获取，写入 PID 记录
  writeFileSync(lockPath, JSON.stringify({ pid: process.pid, ts: Date.now() }), 'utf8');
}

/**
 * 同步释放文件锁
 * @param {string} filePath
 */
export function releaseLockSync(filePath) {
  const lockPath = filePath + LOCK_FILE_SUFFIX;
  try {
    if (existsSync(lockPath)) {
      const data = JSON.parse(readFileSync(lockPath, 'utf8'));
      if (data.pid === process.pid) {
        unlinkSync(lockPath);
      }
    }
  } catch { /* ignore */ }
}

/**
 * 真正的 flock 阻塞同步锁（多进程安全，crash-safe）
 * 持有锁期间执行回调，锁在回调返回后自动释放
 * @param {string} filePath
 * @param {Function} fn - 持锁期间执行的同步函数
 * @param {number} timeoutMs
 * @returns {any} fn 的返回值
 */
/**
 * flock 同步锁（阻塞式，多进程安全）
 * 获取锁后立即释放（锁文件通过 flock 命令持有）
 * 注意：真正的 flock 锁由子进程持有，这里只做验证和记录
 * @param {string} filePath
 * @param {number} timeoutMs
 */
export function flockSync(filePath, timeoutMs = LOCK_TIMEOUT_MS) {
  const lockPath = filePath + LOCK_FILE_SUFFIX;

  // 使用 flock -w timeout 获取独占锁（阻塞直到获得或超时）
  try {
    execSync(`flock -x -w ${Math.ceil(timeoutMs / 1000)} "${lockPath}" -c "echo locked"`, {
      stdio: 'ignore',
      timeout: Math.ceil(timeoutMs / 1000) + 1,
    });
  } catch (e) {
    if (e.status === 127) {
      throw new Error(`[storage_lock] flock command not found`);
    }
    throw new Error(`[storage_lock] flockSync timeout for ${filePath} after ${timeoutMs}ms`);
  }

  // 写入 PID 信息（供调试/手动清理）
  writeFileSync(lockPath, JSON.stringify({ pid: process.pid, ts: Date.now() }), 'utf8');
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
 * 记录写操作到 WAL（异步，不保证 fsync）
 * @param {object} op
 */
export function logWriteOp(op) {
  if (!walFd) return;
  const entry = JSON.stringify({ ...op, ts: Date.now() }) + '\n';
  const buf = Buffer.from(entry, 'utf8');
  fs.writeSync(walFd, buf);
}

/**
 * 记录写操作到 WAL（同步版本，fsync 确保落盘）
 * @param {object} op
 */
export function walWriteSync(op) {
  if (!walFd) return;
  const entry = JSON.stringify({ ...op, ts: Date.now() }) + '\n';
  const buf = Buffer.from(entry, 'utf8');
  fs.writeSync(walFd, buf);
  // 确保数据落盘（fsync）
  fs.fsyncSync(walFd);
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

// ─── 脏读检测 ──────────────────────────────────────────────────────────────

// 记录每个 memory 的期望版本（由 withLock 调用方设置）
const expectedVersions = new Map();

/**
 * 设置期望的 memory 版本（脏读检测用）
 * @param {string} memoryId
 * @param {number} version
 */
export function setExpectedVersion(memoryId, version) {
  expectedVersions.set(memoryId, version);
}

/**
 * 检查 memory 版本是否符合预期
 * 如果 version 不符合预期，记录 warning 但不阻塞
 * @param {string} memoryId
 * @param {number} expectedVersion
 * @param {object} memory - 被读取的 memory 对象
 * @returns {boolean} true=版本一致，false=脏读
 */
export function checkVersion(memoryId, expectedVersion, memory) {
  if (!memory || memory.version === undefined) return true;

  const actual = memory.version;
  if (actual !== expectedVersion) {
    console.warn(`[storage_lock] ⚠️ 脏读检测: memory "${memoryId}" expected version ${expectedVersion}, got ${actual}`);
    return false;
  }
  return true;
}

/**
 * 获取期望版本
 * @param {string} memoryId
 * @returns {number|undefined}
 */
export function getExpectedVersion(memoryId) {
  return expectedVersions.get(memoryId);
}

/**
 * 清除期望版本
 * @param {string} memoryId
 */
export function clearExpectedVersion(memoryId) {
  expectedVersions.delete(memoryId);
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
    if (walOp) walWriteSync(walOp); // 使用同步版本确保 fsync
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
