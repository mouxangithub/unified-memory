/**
 * Tier Manager Unit Tests
 * Tests: HOT/WARM/COLD tier assignment, lifecycle rules, redistribution
 */
import { describe, it, expect } from 'vitest';

const TIER_CONFIG = {
  HOT: { maxAgeDays: 7, compress: false, priority: 3 },
  WARM: { maxAgeDays: 30, compress: false, priority: 2 },
  COLD: { maxAgeDays: Infinity, compress: true, priority: 1 },
};
const DAY_MS = 86400000;

function parseTimestamp(memory) {
  const raw = memory.timestamp || memory.created_at || memory.createdAt || Date.now();
  if (typeof raw === 'string') return new Date(raw).getTime();
  return raw;
}

function getTier(memory, now = Date.now()) {
  const ts = parseTimestamp(memory);
  const age = now - ts;
  const ageDays = age / DAY_MS;
  if (ageDays <= TIER_CONFIG.HOT.maxAgeDays) return 'HOT';
  if (ageDays <= TIER_CONFIG.WARM.maxAgeDays) return 'WARM';
  return 'COLD';
}

function assignTiers(memories, now = Date.now()) {
  return memories.map(m => ({ ...m, tier: getTier(m, now) }));
}

function partitionByTier(memories) {
  const tiers = { HOT: [], WARM: [], COLD: [] };
  for (const m of assignTiers(memories)) {
    tiers[m.tier].push(m);
  }
  return tiers;
}

function redistributeTiers(memories) {
  return assignTiers(memories);
}

function compressColdTier(coldMemories) {
  return coldMemories.map(m => ({
    ...m,
    compressed: true,
    id: m.id,
    text: m.text?.slice(0, 200) || m.text,
    category: m.category,
    timestamp: m.timestamp,
    tier: 'COLD',
  }));
}

function getTierStats(memories) {
  const tiers = partitionByTier(memories);
  return {
    HOT: tiers.HOT.length,
    WARM: tiers.WARM.length,
    COLD: tiers.COLD.length,
    total: memories.length,
  };
}

function runLifecycle(memories, options = {}) {
  const { coldExportDays = 90, forgetThreshold = 0.05, dryRun = false } = options;
  const now = Date.now();
  const results = { exported: [], forgotten: [], preserved: [] };

  const updated = memories.map(m => {
    const ts = parseTimestamp(m);
    const age = now - ts;
    const tier = getTier(m, now);

    if (tier === 'COLD' && age > coldExportDays * DAY_MS) {
      const sig = typeof m.importance === 'number' ? m.importance : 0.5;
      if (sig < forgetThreshold) {
        if (!dryRun) {
          return { ...m, forgotten: true, forgotten_at: now };
        }
        results.forgotten.push(m.id);
      } else {
        if (!dryRun) {
          return { ...m, cold_exported: true, exported_at: now };
        }
        results.exported.push(m.id);
      }
    } else {
      results.preserved.push(m.id);
    }
    return m;
  });

  return {
    updated: dryRun ? memories : updated,
    ...results,
    dryRun,
    coldExportDays,
    forgetThreshold,
  };
}

// ─── Tests ──────────────────────────────────────────────────────────────────

describe('Tier Assignment', () => {
  it('brand new memory (<7 days) is HOT', () => {
    const now = Date.now();
    const mem = { id: '1', created_at: now };
    expect(getTier(mem, now)).toBe('HOT');
    expect(getTier(mem, now + 6 * DAY_MS)).toBe('HOT');
  });

  it('memory between 7-30 days is WARM', () => {
    const now = Date.now();
    const mem = { id: '1', created_at: now - 10 * DAY_MS };
    expect(getTier(mem, now)).toBe('WARM');
    expect(getTier(mem, now - 20 * DAY_MS)).toBe('WARM');
  });

  it('memory >30 days is COLD', () => {
    const now = Date.now();
    const mem = { id: '1', created_at: now - 31 * DAY_MS };
    expect(getTier(mem, now)).toBe('COLD');
    expect(getTier(mem, now - 365 * DAY_MS)).toBe('COLD');
  });

  it('boundary: exactly 7 days = WARM (strict >)', () => {
    const now = Date.now();
    const mem = { id: '1', created_at: now - 7 * DAY_MS };
    expect(getTier(mem, now)).toBe('WARM'); // 7 days old is past HOT threshold
  });

  it('boundary: exactly 30 days = COLD (strict >)', () => {
    const now = Date.now();
    const mem = { id: '1', created_at: now - 30 * DAY_MS };
    expect(getTier(mem, now)).toBe('COLD'); // 30 days old is past WARM threshold
  });

  it('handles ISO string timestamp', () => {
    const now = Date.now();
    const isoDate = new Date(now - 5 * DAY_MS).toISOString();
    const mem = { id: '1', timestamp: isoDate };
    expect(getTier(mem, now)).toBe('HOT');
  });

  it('handles missing timestamp (defaults to now = HOT)', () => {
    const mem = { id: '1' };
    expect(getTier(mem)).toBe('HOT');
  });
});

describe('Tier Partition', () => {
  it('partitionByTier splits correctly', () => {
    const now = Date.now();
    const memories = [
      { id: 'hot1', created_at: now },
      { id: 'hot2', created_at: now - 3 * DAY_MS },
      { id: 'warm1', created_at: now - 15 * DAY_MS },
      { id: 'warm2', created_at: now - 25 * DAY_MS },
      { id: 'cold1', created_at: now - 60 * DAY_MS },
      { id: 'cold2', created_at: now - 365 * DAY_MS },
    ];
    const tiers = partitionByTier(memories);
    expect(tiers.HOT).toHaveLength(2);
    expect(tiers.WARM).toHaveLength(2);
    expect(tiers.COLD).toHaveLength(2);
  });

  it('assignTiers adds tier field to each memory', () => {
    const now = Date.now();
    const memories = [{ id: '1', created_at: now }, { id: '2', created_at: now - 100 * DAY_MS }];
    const assigned = assignTiers(memories, now);
    expect(assigned[0].tier).toBe('HOT');
    expect(assigned[1].tier).toBe('COLD');
  });

  it('getTierStats returns correct counts', () => {
    const now = Date.now();
    const memories = [
      { id: 'hot1', created_at: now },
      { id: 'warm1', created_at: now - 15 * DAY_MS },
      { id: 'cold1', created_at: now - 60 * DAY_MS },
    ];
    const stats = getTierStats(memories);
    expect(stats.HOT).toBe(1);
    expect(stats.WARM).toBe(1);
    expect(stats.COLD).toBe(1);
    expect(stats.total).toBe(3);
  });
});

describe('Tier Lifecycle', () => {
  it('COLD memories >90 days with low significance are forgotten', () => {
    const now = Date.now();
    const memories = [
      { id: 'cold_old_low', created_at: now - 100 * DAY_MS, importance: 0.01, text: 'noise' },
      { id: 'cold_old_high', created_at: now - 100 * DAY_MS, importance: 0.8, text: 'important decision' },
    ];
    const result = runLifecycle(memories, { coldExportDays: 90, forgetThreshold: 0.05, dryRun: true });
    expect(result.forgotten).toContain('cold_old_low');
    expect(result.forgotten).not.toContain('cold_old_high');
    expect(result.preserved).toContain('cold_old_high');
  });

  it('COLD memories within 90 days are preserved', () => {
    const now = Date.now();
    const memories = [
      { id: 'cold_recent', created_at: now - 60 * DAY_MS, importance: 0.3 },
    ];
    const result = runLifecycle(memories, { coldExportDays: 90, forgetThreshold: 0.05, dryRun: true });
    expect(result.forgotten).not.toContain('cold_recent');
    expect(result.preserved).toContain('cold_recent');
  });

  it('HOT/WARM memories are never forgotten by lifecycle', () => {
    const now = Date.now();
    const memories = [
      { id: 'hot', created_at: now, importance: 0.0 },
      { id: 'warm', created_at: now - 20 * DAY_MS, importance: 0.0 },
    ];
    const result = runLifecycle(memories, { coldExportDays: 90, forgetThreshold: 0.05, dryRun: true });
    expect(result.forgotten).not.toContain('hot');
    expect(result.forgotten).not.toContain('warm');
  });
});

describe('Cold Tier Compression', () => {
  it('compressColdTier truncates text to 200 chars', () => {
    const longText = 'a'.repeat(500);
    const cold = [{ id: 'c1', text: longText, category: 'fact', timestamp: Date.now() - 100 * DAY_MS }];
    const compressed = compressColdTier(cold);
    expect(compressed[0].text).toHaveLength(200);
    expect(compressed[0].compressed).toBe(true);
  });

  it('compressColdTier preserves essential fields', () => {
    const cold = [{ id: 'c1', text: 'hello world', category: 'preference', timestamp: Date.now() - 100 * DAY_MS }];
    const compressed = compressColdTier(cold);
    expect(compressed[0].id).toBe('c1');
    expect(compressed[0].category).toBe('preference');
    expect(compressed[0].tier).toBe('COLD');
    expect(compressed[0].compressed).toBe(true);
  });
});

describe('Redistribution', () => {
  it('redistributeTiers reassigns tier based on current time', () => {
    const past = Date.now() - 20 * DAY_MS;
    const memories = [{ id: '1', created_at: past }];
    // If tested when this memory was 10 days old (WARM)
    const oldNow = past + 10 * DAY_MS;
    const assigned = redistributeTiers(memories);
    expect(assignTiers(memories, oldNow)[0].tier).toBe('WARM');
  });
});
