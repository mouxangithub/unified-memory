/**
 * Memory Benchmark Suite
 * Performance testing for unified-memory-ts
 */

import { writeFileSync, readFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';

const WORKSPACE = join(process.env.HOME || '/root', '.openclaw', 'workspace');
const MEMORY_DIR = join(WORKSPACE, 'memory');
const BENCHMARK_DIR = join(MEMORY_DIR, 'benchmark');

/**
 * Simple benchmark runner
 */
export async function runBenchmark(name, fn, iterations = 100) {
  const memBefore = process.memoryUsage().heapUsed / 1024 / 1024;
  
  const start = Date.now();
  for (let i = 0; i < iterations; i++) {
    await fn();
  }
  const end = Date.now();
  
  const memAfter = process.memoryUsage().heapUsed / 1024 / 1024;
  
  const totalMs = end - start;
  const avgMs = totalMs / iterations;
  const opsPerSec = 1000 / avgMs;
  
  return {
    name,
    operations: iterations,
    totalMs,
    avgMs: Math.round(avgMs * 1000) / 1000,
    opsPerSec: Math.round(opsPerSec * 100) / 100,
    memoryMb: Math.round((memAfter - memBefore) * 100) / 100,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Generate benchmark report
 */
export function generateReport(results) {
  const summary = {
    totalBenchmarks: results.length,
    fastestOp: results.reduce((a, b) => a.opsPerSec > b.opsPerSec ? a : b).name,
    slowestOp: results.reduce((a, b) => a.opsPerSec < b.opsPerSec ? a : b).name,
    avgOpsPerSec: Math.round(
      results.reduce((sum, r) => sum + r.opsPerSec, 0) / results.length * 100
    ) / 100,
  };
  
  return {
    generatedAt: new Date().toISOString(),
    nodeVersion: process.version,
    platform: process.platform,
    results,
    summary,
  };
}

/**
 * Save benchmark result
 */
export function saveBenchmark(name, report) {
  mkdirSync(BENCHMARK_DIR, { recursive: true });
  const file = join(BENCHMARK_DIR, `${name}_${Date.now()}.json`);
  writeFileSync(file, JSON.stringify(report, null, 2), 'utf-8');
  console.log(`📊 Benchmark saved: ${file}`);
}

/**
 * Print benchmark results
 */
export function printResults(results) {
  console.log('\n📊 Benchmark Results\n');
  console.log('─'.repeat(70));
  console.log('Operation'.padEnd(20), 'Avg (ms)'.padEnd(12), 'Ops/sec'.padEnd(12), 'Memory (MB)');
  console.log('─'.repeat(70));
  
  for (const r of results) {
    console.log(
      r.name.padEnd(20),
      r.avgMs.toFixed(3).padEnd(12),
      r.opsPerSec.toFixed(2).padEnd(12),
      r.memoryMb.toFixed(3)
    );
  }
  console.log('─'.repeat(70));
}

/**
 * Run all benchmarks
 */
export async function runAllBenchmarks() {
  console.log('🚀 Running Memory Benchmark Suite...\n');
  
  const results = [];
  
  // Simple benchmark: JSON ops
  const data = {
    id: 'bench_test',
    text: 'Test memory content for benchmarking',
    category: 'test',
    importance: 0.8,
    timestamp: new Date().toISOString(),
  };
  
  const jsonResult = await runBenchmark('json_ops', async () => {
    const s = JSON.stringify(data);
    JSON.parse(s);
  }, 1000);
  results.push(jsonResult);
  
  // String search benchmark
  const texts = Array.from({ length: 100 }, (_, i) => 
    `Memory text number ${i} with some content for searching`
  );
  const searchResult = await runBenchmark('string_search', async () => {
    texts.filter(t => t.toLowerCase().includes('number'));
  }, 500);
  results.push(searchResult);
  
  printResults(results);
  
  const report = generateReport(results);
  saveBenchmark('memory', report);
  
  console.log('\n✅ Benchmark complete!\n');
}

// CLI
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args[0] === 'run') {
    runAllBenchmarks().catch(console.error);
  } else if (args[0] === 'report') {
    const reports = existsSync(BENCHMARK_DIR) 
      ? require('fs').readdirSync(BENCHMARK_DIR).filter(f => f.endsWith('.json'))
      : [];
    
    if (reports.length === 0) {
      console.log('📊 No benchmark reports found. Run `benchmark run` first.');
    } else {
      const latest = reports.sort().pop();
      const report = JSON.parse(
        readFileSync(join(BENCHMARK_DIR, latest), 'utf-8')
      );
      printResults(report.results);
    }
  } else {
    console.log('Usage:');
    console.log('  benchmark run    - Run all benchmarks');
    console.log('  benchmark report - Show latest benchmark report');
  }
}
