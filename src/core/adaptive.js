/**
 * Adaptive Memory System
 */

import { readFileSync, existsSync, writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const WORKSPACE = join(process.env.HOME || '/root', '.openclaw', 'workspace');
const MEMORY_DIR = join(WORKSPACE, 'memory');

const DEFAULT_CONFIG = { learningRate: 0.1, decayThreshold: 0.05, boostThreshold: 0.2, minImportance: 0.1, maxImportance: 0.95 };

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

export function adaptMemory(memory, recentAccesses) {
  const oldImportance = memory.importance ?? 0.5;
  let newImportance = oldImportance;
  let action = 'keep';
  let reason = '';
  
  if (recentAccesses >= 5) {
    newImportance = Math.min(DEFAULT_CONFIG.maxImportance, oldImportance + DEFAULT_CONFIG.learningRate * recentAccesses);
    action = 'boost';
    reason = `Frequent access (${recentAccesses} times)`;
  } else if (recentAccesses === 0) {
    newImportance = Math.max(DEFAULT_CONFIG.minImportance, oldImportance - DEFAULT_CONFIG.decayThreshold);
    action = 'decay';
    reason = 'No recent access';
  }
  
  newImportance = Math.round(newImportance * 100) / 100;
  return { memoryId: memory.id || 'unknown', action, oldImportance, newImportance, reason };
}

export function autoTune() {
  const memories = loadMemories();
  let adapted = 0;
  
  for (const mem of memories) {
    const accesses = mem.access_count ?? 0;
    const result = adaptMemory(mem, accesses);
    if (result.action !== 'keep') {
      mem.importance = result.newImportance;
      adapted++;
    }
  }
  
  if (adapted > 0) saveMemories(memories);
  console.log(`✅ Adapted ${adapted}/${memories.length} memories`);
  return adapted;
}

export function printAdaptationReport() {
  const memories = loadMemories();
  let boosted = 0, decayed = 0, stable = 0;
  let totalImportance = 0;
  
  for (const mem of memories) {
    const accesses = mem.access_count ?? 0;
    if (accesses >= 5) boosted++;
    else if (accesses === 0) decayed++;
    else stable++;
    totalImportance += mem.importance ?? 0.5;
  }
  
  console.log('\n🔄 Memory Adaptation Report\n');
  console.log(`  Total Memories: ${memories.length}`);
  console.log(`  Average Importance: ${memories.length > 0 ? (totalImportance / memories.length).toFixed(2) : 0}`);
  console.log(`  📈 Boosted: ${boosted}`);
  console.log(`  📉 Decayed: ${decayed}`);
  console.log(`  ➡️  Stable: ${stable}`);
  console.log('');
}

if (require.main === module) {
  const args = process.argv.slice(2);
  if (args[0] === 'tune') autoTune();
  else printAdaptationReport();
}
