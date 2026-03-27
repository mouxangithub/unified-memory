/**
 * Memory Optimizer - Optimize memory storage
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

export function deduplicate() {
  const memories = loadMemories();
  const seen = new Set();
  const before = memories.length;
  const unique = memories.filter(mem => {
    const key = (mem.text || '').toLowerCase().trim();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  saveMemories(unique);
  return { affected: before - unique.length, before, after: unique.length };
}

export function removeEmpty() {
  const memories = loadMemories();
  const before = memories.length;
  const valid = memories.filter(mem => (mem.text || '').trim().length > 0);
  saveMemories(valid);
  return { affected: before - valid.length, before, after: valid.length };
}

export function optimizeAll() {
  console.log('🚀 Running memory optimizations...\n');
  const dedup = deduplicate();
  if (dedup.affected > 0) console.log(`  ✅ Dedup: removed ${dedup.affected}`);
  const empty = removeEmpty();
  if (empty.affected > 0) console.log(`  ✅ Removed ${empty.affected} empty`);
  console.log(`\n📊 Remaining: ${empty.after} memories\n`);
}

if (require.main === module) {
  optimizeAll();
}
