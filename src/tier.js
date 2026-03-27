/**
 * Tier Manager - HOT(7d) / WARM(7-30d) / COLD(>30d) 三层架构
 * Automatic tier assignment and redistribution
 */
export const TIER_CONFIG = {
  HOT: { maxAgeDays: 7, compress: false, priority: 3 },
  WARM: { maxAgeDays: 30, compress: false, priority: 2 },
  COLD: { maxAgeDays: Infinity, compress: true, priority: 1 },
};

const DAY_MS = 86400000;

function parseTimestamp(memory) {
  const raw = memory.timestamp || memory.created_at || memory.createdAt || Date.now();
  // Handle ISO string format from Python
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

/**
 * Assign tier to each memory
 * @param {Array} memories
 * @returns {Array} memories with .tier field added
 */
export function assignTiers(memories, now = Date.now()) {
  return memories.map(m => ({ ...m, tier: getTier(m, now) }));
}

/**
 * Partition memories by tier
 * @param {Array} memories
 * @returns {{ HOT: Array, WARM: Array, COLD: Array }}
 */
export function partitionByTier(memories) {
  const tiers = { HOT: [], WARM: [], COLD: [] };
  for (const m of assignTiers(memories)) {
    tiers[m.tier].push(m);
  }
  return tiers;
}

/**
 * Redistribute all memories across tiers (full re-tier)
 * @param {Array} memories
 * @returns {Array}
 */
export function redistributeTiers(memories) {
  return assignTiers(memories);
}

/**
 * Compress cold tier memories (summarize / drop details)
 * @param {Array} coldMemories
 * @returns {Array}
 */
export function compressColdTier(coldMemories) {
  return coldMemories.map(m => ({
    ...m,
    compressed: true,
    // Keep essential fields only
    id: m.id,
    text: m.text?.slice(0, 200) || m.text,
    category: m.category,
    timestamp: m.timestamp,
    tier: 'COLD',
  }));
}

/**
 * Get tier stats
 * @param {Array} memories
 * @returns {{ HOT: number, WARM: number, COLD: number, total: number }}
 */
export function getTierStats(memories) {
  const tiers = partitionByTier(memories);
  return {
    HOT: tiers.HOT.length,
    WARM: tiers.WARM.length,
    COLD: tiers.COLD.length,
    total: memories.length,
  };
}

export default { TIER_CONFIG, getTier, assignTiers, partitionByTier, redistributeTiers, compressColdTier, getTierStats };
