/**
 * Proactive Memory Manager v1.0
 * Unified management of proactive recall and proactive care
 * Periodic checks, active injection
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';
import { getAllMemories } from './storage.js';
import { predictRecall } from './core/proactive_recall.js';
import { runCheck as runProactiveCare } from './core/proactive_care.js';
import { autoDegrade } from './quality.js';
import { runLifecycle } from './tier.js';

const LIFECYCLE_STATE_FILE = join(process.env.HOME || '/root', '.unified-memory', 'lifecycle_state.json');

function loadOperationCount() {
  try {
    if (existsSync(LIFECYCLE_STATE_FILE)) {
      const data = JSON.parse(readFileSync(LIFECYCLE_STATE_FILE, 'utf8'));
      return typeof data.operationCount === 'number' ? data.operationCount : 0;
    }
  } catch { /* ignore */ }
  return 0;
}

function saveOperationCount(count) {
  try {
    const dir = join(process.env.HOME || '/root', '.unified-memory');
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
    writeFileSync(LIFECYCLE_STATE_FILE, JSON.stringify({ operationCount: count }, null, 2), 'utf8');
  } catch (e) {
    console.error('[ProactiveManager] failed to persist operationCount:', e.message);
  }
}

export class ProactiveManager {
  constructor(intervalMs = 300000) { // Default 5 minutes
    this.intervalMs = intervalMs;
    this.timer = null;
    this.lastRecallResults = [];
    this.lastCareResults = null;
    this.operationCount = loadOperationCount();
  }

  start() {
    if (this.timer) return;
    this.timer = setInterval(() => this.tick(), this.intervalMs);
    console.log(`[ProactiveManager] started, interval=${this.intervalMs}ms`);
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  async tick() {
    try {
      // 1. Run proactive care (status detection)
      this.lastCareResults = await runProactiveCare();

      // 2. Predict memories that need recall
      const recent = this._getRecentContext();
      this.lastRecallResults = predictRecall(recent);

      // 3. Auto-degrade low-quality memories to COLD tier
      this.lastDegradeResult = autoDegrade({ threshold: 0.15, batchSize: 50 });

      // 4. Lifecycle: every 100 operations, run lifecycle management
      this.operationCount++;
      if (this.operationCount % 100 === 0) {
        console.log(`[ProactiveManager] operationCount=${this.operationCount}, triggering lifecycle...`);
        this.lastLifecycleResult = runLifecycle();
        saveOperationCount(this.operationCount);
      }

      return {
        care: this.lastCareResults,
        recall: this.lastRecallResults.slice(0, 5),
        degrade: this.lastDegradeResult,
        lifecycle: this.lastLifecycleResult || null,
        ts: Date.now(),
      };
    } catch (e) {
      console.error('[ProactiveManager] tick error:', e.message);
    }
  }

  _getRecentContext() {
    // Extract context from recent memories
    const memories = getAllMemories();
    const recent = memories
      .sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0))
      .slice(0, 10)
      .map(m => m.text)
      .join(' ');
    return recent;
  }

  getStatus() {
    return {
      running: !!this.timer,
      intervalMs: this.intervalMs,
      lastCare: this.lastCareResults,
      lastRecallCount: this.lastRecallResults.length,
      recallPredictions: this.lastRecallResults.slice(0, 3),
      lastDegrade: this.lastDegradeResult || null,
    };
  }

  // Manual trigger once
  async trigger() {
    return this.tick();
  }
}

// Global instance
let globalManager = null;

export function getProactiveManager() {
  if (!globalManager) {
    globalManager = new ProactiveManager();
  }
  return globalManager;
}
