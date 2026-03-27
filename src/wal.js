/**
 * Write-Ahead Log (WAL) - Ensures memory durability
 * Operations are logged before being applied, enabling crash recovery
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WAL_DIR = path.join(__dirname, '..', 'wal');

let walFd = null;       // file descriptor for fsync
let walPath = null;    // current WAL file path
let walOffset = 0;

function ensureWalDir() {
  if (!fs.existsSync(WAL_DIR)) fs.mkdirSync(WAL_DIR, { recursive: true });
}

export function initWal(runId) {
  ensureWalDir();
  walPath = path.join(WAL_DIR, `${runId || Date.now()}.wal.jsonl`);
  walFd = fs.openSync(walPath, 'a');
  walOffset = 0;
  return walPath;
}

export function logOp(op) {
  if (!walFd) return;
  const entry = JSON.stringify({ ...op, ts: Date.now() }) + '\n';
  const buf = Buffer.from(entry, 'utf8');
  fs.writeSync(walFd, buf);
  walOffset += buf.byteLength;
}

export function flushWal() {
  if (!walFd) return;
  // fsync ensures data hits physical storage (durable write)
  fs.fsyncSync(walFd);
}

export function closeWal() {
  if (!walFd) return;
  fs.fsyncSync(walFd); // ensure final flush before close
  fs.closeSync(walFd);
  walFd = null;
  walPath = null;
}

export function listWalFiles() {
  ensureWalDir();
  return fs.readdirSync(WAL_DIR).filter(f => f.endsWith('.wal.jsonl')).sort();
}

export function readWal(file) {
  const content = fs.readFileSync(path.join(WAL_DIR, file), 'utf8');
  return content.trim().split('\n').filter(Boolean).map(l => JSON.parse(l));
}
