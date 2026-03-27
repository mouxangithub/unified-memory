/**
 * Proactive Memory Manager v1.0
 * Unified management of proactive recall and proactive care
 * Periodic checks, active injection
 */

import { getAllMemories } from './storage.js';
import { predictRecall } from './core/proactive_recall.js';
import { runCheck as runProactiveCare } from './core/proactive_care.js';

export class ProactiveManager {
  constructor(intervalMs = 300000) { // Default 5 minutes
    this.intervalMs = intervalMs;
    this.timer = null;
    this.lastRecallResults = [];
    this.lastCareResults = null;
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

      return {
        care: this.lastCareResults,
        recall: this.lastRecallResults.slice(0, 5),
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
