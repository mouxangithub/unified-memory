/**
 * Scope Isolation - AGENT/USER/TEAM/GLOBAL四级隔离
 * Filter memories by scope level
 */
export const SCOPE_LEVELS = ['AGENT', 'USER', 'TEAM', 'GLOBAL'];
export const SCOPE_HIERARCHY = { AGENT: 0, USER: 1, TEAM: 2, GLOBAL: 3 };

/**
 * Get effective scope for a scope string
 * @param {string} scope
 * @returns {string}
 */
export function normalizeScope(scope) {
  if (!scope) return 'GLOBAL';
  const upper = scope.toUpperCase();
  return SCOPE_LEVELS.includes(upper) ? upper : 'GLOBAL';
}

/**
 * Filter memories by scope
 * @param {Array} memories
 * @param {string} scope
 * @returns {Array}
 */
export function filterByScope(memories, scope) {
  const target = normalizeScope(scope);
  const targetLevel = SCOPE_HIERARCHY[target];
  return memories.filter(m => {
    const mScope = normalizeScope(m.scope || 'GLOBAL');
    const mLevel = SCOPE_HIERARCHY[mScope];
    // Allow if memory scope >= target scope (GLOBAL >= TEAM >= USER >= AGENT)
    return mLevel >= targetLevel;
  });
}

/**
 * Check if a memory matches a scope
 * @param {object} memory
 * @param {string} scope
 * @returns {boolean}
 */
export function matchesScope(memory, scope) {
  const target = normalizeScope(scope);
  const mScope = normalizeScope(memory.scope || 'GLOBAL');
  return SCOPE_HIERARCHY[mScope] >= SCOPE_HIERARCHY[target];
}

export default { SCOPE_LEVELS, SCOPE_HIERARCHY, normalizeScope, filterByScope, matchesScope };
