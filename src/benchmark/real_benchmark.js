/**
 * Real-world Benchmark - Production usage patterns
 */

import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

const WORKSPACE = join(process.env.HOME || '/root', '.openclaw', 'workspace');
const MEMORY_DIR = join(WORKSPACE, 'memory');

/**
 * Simulate realistic memory operations
 */
export function runRealWorldBenchmark() {
  console.log('🚀 Real-World Benchmark\n');
  
  const memoriesFile = join(MEMORY_DIR, 'memories.json');
  let memories = [];
  
  if (existsSync(memoriesFile)) {
    try {
      memories = JSON.parse(readFileSync(memoriesFile, 'utf-8'));
    } catch {
      console.log('⚠️  Could not load memories, using empty dataset');
    }
  }
  
  const scenarios = [
    { name: 'Memory Load', ops: () => { if (existsSync(memoriesFile)) JSON.parse(readFileSync(memoriesFile, 'utf-8')); } },
    { name: 'Category Filter', ops: () => { memories.filter(m => m.category === 'preference'); } },
    { name: 'Importance Sort', ops: () => { [...memories].sort((a, b) => (b.importance || 0) - (a.importance || 0)); } },
    { name: 'Text Search', ops: () => { const q = 'test'; memories.filter(m => (m.text || '').toLowerCase().includes(q.toLowerCase())); } },
    { name: 'Tag Extraction', ops: () => { const allTags = []; for (const m of memories) { if (Array.isArray(m.tags)) allTags.push(...m.tags); } } },
  ];
  
  const results = [];
  
  for (const scenario of scenarios) {
    const iterations = 100;
    const start = Date.now();
    
    for (let i = 0; i < iterations; i++) {
      scenario.ops();
    }
    
    const totalMs = Date.now() - start;
    const avgMs = totalMs / iterations;
    
    results.push({
      name: scenario.name,
      ms: Math.round(avgMs * 1000) / 1000,
      opsPerSec: Math.round(1000 / avgMs * 100) / 100,
    });
    
    console.log(
      `  ${scenario.name.padEnd(20)} ${avgMs.toFixed(3).padStart(8)} ms  ${(1000 / avgMs).toFixed(2).padStart(10)} ops/sec`
    );
  }
  
  console.log('\n📊 Summary\n');
  console.log(`  Dataset size: ${memories.length} memories`);
  console.log(`  Total scenarios: ${scenarios.length}`);
  
  const fastest = results.reduce((a, b) => a.ms < b.ms ? a : b);
  const slowest = results.reduce((a, b) => a.ms > b.ms ? a : b);
  console.log(`  Fastest: ${fastest.name} (${fastest.ms} ms)`);
  console.log(`  Slowest: ${slowest.name} (${slowest.ms} ms)`);
}

// CLI
if (require.main === module) {
  runRealWorldBenchmark();
}
