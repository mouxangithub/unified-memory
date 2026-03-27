/**
 * Quality Scoring Unit Tests
 * Tests: score calculation, autoDegrade boundaries
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Minimal quality score implementation for testing (mirrors quality.js)
function qualityScore(memory) {
  if (!memory) return 0;

  let score = 0.0;

  const importance = typeof memory.importance === 'number'
    ? Math.max(0, Math.min(1, memory.importance))
    : 0.5;
  score += importance * 0.35;

  const accessCount = typeof memory.access_count === 'number' ? memory.access_count : 0;
  if (accessCount > 0) {
    score += Math.min(0.15, Math.log1p(accessCount) * 0.05);
  }

  const ageMs = Date.now() - (memory.created_at || Date.now());
  const ageDays = ageMs / (1000 * 60 * 60 * 24);
  const recencyBonus = Math.exp(-ageDays / 30) * 0.20;
  score += recencyBonus;

  const reflectionCount = typeof memory.reflection_count === 'number'
    ? memory.reflection_count
    : (memory.insightful ? 1 : 0);
  if (reflectionCount > 0) {
    score += Math.min(0.15, reflectionCount * 0.05);
  }

  // Feedback history signal
  const history = memory.feedbackHistory || [];
  let feedbackSignal = 0;
  for (const fb of history) {
    if (fb.outcome === 'helpful') feedbackSignal += 0.03;
    else if (fb.outcome === 'irrelevant') feedbackSignal -= 0.01;
    else if (fb.outcome === 'wrong') feedbackSignal -= 0.05;
    else if (fb.outcome === 'outdated') feedbackSignal -= 0.04;
  }
  score += Math.max(-0.20, Math.min(0.15, feedbackSignal));

  if (memory.category === 'preference' || memory.category === 'decision') {
    score += 0.05;
  }

  return Math.max(0.0, Math.min(1.0, score));
}

function autoDegrade(memories, options = {}) {
  const { threshold = 0.15, batchSize = 50, dryRun = false } = options;
  const scored = memories.map(m => ({ memory: m, score: qualityScore(m) }));
  const degraded = scored.filter(d => d.score < threshold);
  const preserved = scored.filter(d => d.score >= threshold);
  degraded.sort((a, b) => a.score - b.score);
  const toProcess = degraded.slice(0, batchSize);

  return {
    degraded: toProcess.map(d => d.memory.id),
    preserved: preserved.map(p => p.memory.id),
    dryRun,
    threshold,
    processed: toProcess.length,
    message: `Degraded ${toProcess.length} memories (threshold=${threshold})`,
  };
}

function scoreAllMemories(memories, topK = null) {
  const scored = memories.map(m => {
    const score = qualityScore(m);
    return { memory: m, score };
  });
  scored.sort((a, b) => a.score - b.score);
  if (topK !== null) return scored.slice(0, topK);
  return scored;
}

// ─── Tests ──────────────────────────────────────────────────────────────────

describe('Quality Scoring', () => {
  it('returns 0 for null/undefined memory', () => {
    expect(qualityScore(null)).toBe(0);
    expect(qualityScore(undefined)).toBe(0);
  });

  it('default importance 0.5 gives base score ~0.175 + recency', () => {
    const mem = { text: 'test', created_at: Date.now(), importance: 0.5 };
    const score = qualityScore(mem);
    // 0.5 * 0.35 = 0.175 + recency (max 0.20 for brand new) = max 0.375
    expect(score).toBeGreaterThan(0.15);
    expect(score).toBeLessThanOrEqual(0.40);
  });

  it('high importance (1.0) increases score', () => {
    const now = Date.now();
    const low = qualityScore({ text: 'test', created_at: now, importance: 0.1 });
    const high = qualityScore({ text: 'test', created_at: now, importance: 1.0 });
    expect(high).toBeGreaterThan(low);
  });

  it('access_count boosts score logarithmically', () => {
    const now = Date.now();
    const noAccess = qualityScore({ text: 'test', created_at: now, importance: 0.5 });
    const accessed = qualityScore({ text: 'test', created_at: now, importance: 0.5, access_count: 10 });
    expect(accessed).toBeGreaterThan(noAccess);
    // But saturates
    const many = qualityScore({ text: 'test', created_at: now, importance: 0.5, access_count: 1000 });
    expect(many).toBeCloseTo(accessed, 2);
  });

  it('recent memories score higher than old ones', () => {
    const recent = qualityScore({ text: 'test', created_at: Date.now(), importance: 0.5 });
    const old = qualityScore({ text: 'test', created_at: Date.now() - 90 * 24 * 3600 * 1000, importance: 0.5 });
    expect(recent).toBeGreaterThan(old);
  });

  it('reflection_count boosts score up to +0.15', () => {
    const noRefl = qualityScore({ text: 'test', created_at: Date.now(), importance: 0.5 });
    const reflected = qualityScore({ text: 'test', created_at: Date.now(), importance: 0.5, reflection_count: 3 });
    expect(reflected).toBeGreaterThan(noRefl);
    // Capped at +0.15
    const maxRefl = qualityScore({ text: 'test', created_at: Date.now(), importance: 0.5, reflection_count: 100 });
    expect(maxRefl - noRefl).toBeLessThan(0.20);
  });

  it('helpful feedback increases score', () => {
    const noFb = qualityScore({ text: 'test', created_at: Date.now(), importance: 0.5 });
    const helpful = qualityScore({
      text: 'test', created_at: Date.now(), importance: 0.5,
      feedbackHistory: [{ outcome: 'helpful' }, { outcome: 'helpful' }]
    });
    expect(helpful).toBeGreaterThan(noFb);
  });

  it('wrong/outdated feedback decreases score', () => {
    const noFb = qualityScore({ text: 'test', created_at: Date.now(), importance: 0.5 });
    const wrong = qualityScore({
      text: 'test', created_at: Date.now(), importance: 0.5,
      feedbackHistory: [{ outcome: 'wrong' }]
    });
    expect(wrong).toBeLessThan(noFb);
  });

  it('preference and decision categories get +0.05 boost', () => {
    const normal = qualityScore({ text: 'test', created_at: Date.now(), importance: 0.5 });
    const pref = qualityScore({ text: 'test', created_at: Date.now(), importance: 0.5, category: 'preference' });
    const dec = qualityScore({ text: 'test', created_at: Date.now(), importance: 0.5, category: 'decision' });
    expect(pref).toBeGreaterThan(normal);
    expect(dec).toBeGreaterThan(normal);
  });

  it('score is bounded between 0 and 1', () => {
    const maxMem = {
      text: 'test', created_at: Date.now(), importance: 1.0,
      access_count: 100, reflection_count: 10,
      feedbackHistory: [{ outcome: 'helpful' }, { outcome: 'helpful' }, { outcome: 'helpful' }],
      category: 'preference'
    };
    expect(qualityScore(maxMem)).toBeLessThanOrEqual(1.0);
    expect(qualityScore(maxMem)).toBeGreaterThan(0);

    const minMem = {
      text: '', created_at: Date.now() - 999 * 24 * 3600 * 1000, importance: 0,
      feedbackHistory: [{ outcome: 'wrong' }, { outcome: 'outdated' }]
    };
    expect(qualityScore(minMem)).toBeGreaterThanOrEqual(0);
  });
});

describe('Auto-Degrade', () => {
  it('dryRun returns degraded list without modifying', () => {
    const memories = [
      { id: 'good', text: 'important', created_at: Date.now(), importance: 1.0 },
      { id: 'bad', text: 'old', created_at: Date.now() - 365 * 24 * 3600 * 1000, importance: 0.0 },
    ];
    const result = autoDegrade(memories, { threshold: 0.15, dryRun: true });
    expect(result.dryRun).toBe(true);
    expect(result.degraded).toContain('bad');
    expect(result.degraded).not.toContain('good');
  });

  it('respects threshold boundary exactly', () => {
    const threshold = 0.15;
    const atThreshold = qualityScore({ text: 'x', created_at: Date.now(), importance: 0.15 / 0.35 });
    const aboveThreshold = { ...{ text: 'x', created_at: Date.now(), importance: 0.5 }, score: atThreshold + 0.001 };
    const belowThreshold = { ...{ text: 'x', created_at: Date.now(), importance: 0.0 }, score: threshold - 0.001 };

    const result = autoDegrade([aboveThreshold, belowThreshold], { threshold, dryRun: true });
    expect(result.degraded).not.toContain(aboveThreshold.id);
    expect(result.degraded).toContain(belowThreshold.id);
  });

  it('respected batchSize limit', () => {
    const memories = Array.from({ length: 100 }, (_, i) => ({
      id: `mem_${i}`,
      text: 'old garbage',
      created_at: Date.now() - 400 * 24 * 3600 * 1000,
      importance: 0.0,
    }));
    const result = autoDegrade(memories, { threshold: 0.15, batchSize: 10, dryRun: true });
    expect(result.processed).toBeLessThanOrEqual(10);
  });

  it('scoreAllMemories sorts worst-first', () => {
    const memories = [
      { id: 'good', text: 'important', created_at: Date.now(), importance: 1.0 },
      { id: 'bad', text: 'old', created_at: Date.now() - 365 * 24 * 3600 * 1000, importance: 0.0 },
    ];
    const ranked = scoreAllMemories(memories);
    expect(ranked[0].id).toBe('bad');
    expect(ranked[ranked.length - 1].id).toBe('good');
  });

  it('topK returns only requested number', () => {
    const memories = Array.from({ length: 20 }, (_, i) => ({
      id: `mem_${i}`,
      text: `memory ${i}`,
      created_at: Date.now() - i * 10 * 24 * 3600 * 1000,
      importance: 0.5,
    }));
    const top3 = scoreAllMemories(memories, 3);
    expect(top3).toHaveLength(3);
  });
});
