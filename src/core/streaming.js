/**
 * Memory Streaming - Stream memory operations with async generators
 */

import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

const WORKSPACE = join(process.env.HOME || '/root', '.openclaw', 'workspace');
const MEMORY_DIR = join(WORKSPACE, 'memory');

function loadMemories() {
  const file = join(MEMORY_DIR, 'memories.json');
  if (!existsSync(file)) return [];
  try { return JSON.parse(readFileSync(file, 'utf-8')); }
  catch { return []; }
}

export async function* streamMemories(batchSize = 10) {
  const memories = loadMemories();
  for (let i = 0; i < memories.length; i += batchSize) {
    yield memories.slice(i, i + batchSize);
    await new Promise(resolve => setTimeout(resolve, 1));
  }
}

export async function* streamByCategory(category, batchSize = 10) {
  const allMemories = loadMemories();
  const filtered = allMemories.filter(m => m.category === category);
  for (let i = 0; i < filtered.length; i += batchSize) {
    yield filtered.slice(i, i + batchSize);
    await new Promise(resolve => setTimeout(resolve, 1));
  }
}

export async function* streamSearch(query, batchSize = 10) {
  const memories = loadMemories();
  const q = query.toLowerCase();
  const filtered = memories.filter(m => (m.text || '').toLowerCase().includes(q));
  for (let i = 0; i < filtered.length; i += batchSize) {
    yield filtered.slice(i, i + batchSize);
    await new Promise(resolve => setTimeout(resolve, 1));
  }
}

export async function countMemories() {
  let count = 0;
  for await (const _batch of streamMemories(100)) { count++; }
  return count;
}

if (require.main === module) {
  const args = process.argv.slice(2);
  if (args[0] === 'count') {
    countMemories().then(count => console.log(`\n📊 Total memories: ${count}\n`));
  } else {
    console.log('\n📺 Memory Streaming Demo\n');
    let batchNum = 0;
    for await (const batch of streamMemories(5)) {
      batchNum++;
      console.log(`  Batch ${batchNum}: ${batch.length} memories`);
      if (batchNum >= 3) break;
    }
    console.log('\n✅ Streaming complete\n');
  }
}
