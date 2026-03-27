/**
 * Performance monitoring for unified-memory-ts
 */

import { readFileSync, existsSync, writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const WORKSPACE = join(process.env.HOME || '/root', '.openclaw', 'workspace');
const MEMORY_DIR = join(WORKSPACE, 'memory');
const PERF_DIR = join(MEMORY_DIR, 'perf');

export function collectMetrics() {
  const mem = process.memoryUsage();
  const cpu = process.cpuUsage();
  
  const memoriesFile = join(MEMORY_DIR, 'memories.json');
  let memoryCount = 0;
  let fileSize = 0;
  
  if (existsSync(memoriesFile)) {
    try {
      const data = JSON.parse(readFileSync(memoriesFile, 'utf-8'));
      memoryCount = Array.isArray(data) ? data.length : 0;
      const fs = require('fs');
      fileSize = fs.statSync(memoriesFile).size;
    } catch {}
  }
  
  return {
    timestamp: new Date().toISOString(),
    memory: mem,
    cpu,
    uptime: process.uptime(),
    memoryCount,
    fileSize,
  };
}

export function snapshot() {
  const mem = process.memoryUsage();
  return {
    timestamp: new Date().toISOString(),
    heapUsed: Math.round(mem.heapUsed / 1024 / 1024 * 100) / 100,
    heapTotal: Math.round(mem.heapTotal / 1024 / 1024 * 100) / 100,
    external: Math.round(mem.external / 1024 / 1024 * 100) / 100,
    rss: Math.round(mem.rss / 1024 / 1024 * 100) / 100,
  };
}

export function saveSnapshot(name) {
  name = name || 'snapshot';
  mkdirSync(PERF_DIR, { recursive: true });
  const snap = snapshot();
  const file = join(PERF_DIR, name + '_' + Date.now() + '.json');
  writeFileSync(file, JSON.stringify(snap, null, 2), 'utf-8');
  console.log('Snapshot saved: ' + file);
}

export function printPerf() {
  const metrics = collectMetrics();
  
  console.log('\nPerformance Metrics\n');
  console.log('  Time: ' + metrics.timestamp);
  console.log('  Uptime: ' + Math.round(metrics.uptime) + 's');
  console.log('  Memories: ' + metrics.memoryCount);
  console.log('  File size: ' + (metrics.fileSize / 1024).toFixed(2) + ' KB');
  console.log('');
  console.log('  Memory:');
  console.log('    Heap Used: ' + (metrics.memory.heapUsed / 1024 / 1024).toFixed(2) + ' MB');
  console.log('    Heap Total: ' + (metrics.memory.heapTotal / 1024 / 1024).toFixed(2) + ' MB');
  console.log('    RSS: ' + (metrics.memory.rss / 1024 / 1024).toFixed(2) + ' MB');
  console.log('');
}

export function monitorLoop(intervalMs) {
  intervalMs = intervalMs || 5000;
  console.log('Starting performance monitor (every ' + intervalMs + 'ms)\n');
  
  const interval = setInterval(function() {
    const snap = snapshot();
    const time = snap.timestamp.split('T')[1].substring(0, 8);
    console.log('[' + time + '] Heap: ' + snap.heapUsed + 'MB / ' + snap.heapTotal + 'MB | RSS: ' + snap.rss + 'MB');
  }, intervalMs);
  
  return interval;
}

if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args[0] === 'snapshot') {
    saveSnapshot(args[1] || 'manual');
  } else if (args[0] === 'monitor') {
    const interval = parseInt(args[1] || '5000', 10);
    monitorLoop(interval);
  } else {
    printPerf();
  }
}
