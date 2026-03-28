/**
 * Scope Isolation - AGENT/USER/TEAM/GLOBAL四级隔离
 * Filter memories by scope level + team namespace isolation
 *
 * Team isolation model:
 * - Each team has its own memory namespace prefixed with `team:{team_id}:`
 * - TEAM-scope memories belong to a specific team (stored with team_id)
 * - Cross-team (shared) memories use explicit GLOBAL scope
 * - USER and AGENT scopes are personal to a user/agent and never cross-team
 */

export const SCOPE_LEVELS = ['AGENT', 'USER', 'TEAM', 'GLOBAL'];
export const SCOPE_HIERARCHY = { AGENT: 0, USER: 1, TEAM: 2, GLOBAL: 3 };

// ============ Team Namespace Registry ============

/** @type {Map<string, { name: string, created_at: number, memoryCount: number }>} */
const teamRegistry = new Map();

/** Current active team context (thread-local via global) */
const TEAM_CONTEXT = {
  current: null, // team_id or null for no-team
};

/**
 * Normalize a scope string to SCOPE_LEVELS
 * @param {string} scope
 * @returns {string}
 */
export function normalizeScope(scope) {
  if (!scope) return 'GLOBAL';
  const upper = scope.toUpperCase();
  return SCOPE_LEVELS.includes(upper) ? upper : 'GLOBAL';
}

/**
 * Get effective scope for a scope string
 * @param {string} scope
 * @returns {string}
 */
export function getEffectiveScope(scope) {
  return normalizeScope(scope);
}

/**
 * Filter memories by scope level
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

// ============ Team Namespace Functions ============

/**
 * Create a new team namespace
 * @param {string} teamId  - Unique team identifier (e.g. 'engineering', 'product-team-a')
 * @param {string} name    - Human-readable team name
 * @returns {{ teamId: string, name: string, created_at: number }}
 */
export function createTeamNamespace(teamId, name = '') {
  const id = teamId.replace(/[^a-zA-Z0-9_-]/g, '_').toLowerCase();
  const now = Date.now();
  teamRegistry.set(id, {
    name: name || id,
    created_at: now,
    memoryCount: 0,
  });
  return { teamId: id, name: name || id, created_at: now };
}

/**
 * Delete a team namespace (archives memories)
 * @param {string} teamId
 * @returns {boolean}
 */
export function deleteTeamNamespace(teamId) {
  return teamRegistry.delete(teamId);
}

/**
 * List all registered teams
 * @returns {Array<{ teamId: string, name: string, created_at: number }>}
 */
export function listTeams() {
  return Array.from(teamRegistry.entries()).map(([id, info]) => ({
    teamId: id,
    name: info.name,
    created_at: info.created_at,
  }));
}

/**
 * Set current team context for memory operations
 * @param {string|null} teamId  - team_id or null to clear
 */
export function setCurrentTeam(teamId) {
  TEAM_CONTEXT.current = teamId || null;
}

/**
 * Get current team context
 * @returns {string|null}
 */
export function getCurrentTeam() {
  return TEAM_CONTEXT.current;
}

/**
 * Switch to a different team context (returns previous)
 * @param {string|null} teamId
 * @returns {string|null} previous team_id
 */
export function switchTeam(teamId) {
  const prev = TEAM_CONTEXT.current;
  TEAM_CONTEXT.current = teamId || null;
  return prev;
}

/**
 * Get the team prefix for memory IDs
 * @param {string|null} teamId
 * @returns {string}
 */
export function getTeamPrefix(teamId) {
  if (!teamId) return '';
  return `team:${teamId}:`;
}

/**
 * Check if a memory belongs to a specific team
 * @param {object} memory
 * @param {string} teamId
 * @returns {boolean}
 */
export function memoryBelongsToTeam(memory, teamId) {
  if (!teamId) return false;
  // TEAM-scope memories store team_id explicitly
  if (memory.team_id && memory.team_id === teamId) return true;
  // Also check id prefix for backward compat
  const prefix = getTeamPrefix(teamId);
  return memory.id && memory.id.startsWith(prefix);
}

/**
 * Filter memories for the current team context
 * TEAM-scope: only memories belonging to current team
 * USER/AGENT-scope: memories without a team_id
 * GLOBAL-scope: all memories
 * @param {Array} memories
 * @param {string} scope
 * @returns {Array}
 */
export function filterByTeamAndScope(memories, scope = 'TEAM') {
  const teamId = TEAM_CONTEXT.current;

  // GLOBAL: no team filtering needed
  if (scope === 'GLOBAL' || scope === 'GLOBAL') {
    return memories;
  }

  return memories.filter(m => {
    const mScope = normalizeScope(m.scope || 'GLOBAL');

    // For TEAM scope: only return memories that belong to current team
    if (mScope === 'TEAM') {
      if (!teamId) return false; // No team context, can't see TEAM memories
      return memoryBelongsToTeam(m, teamId);
    }

    // USER/AGENT scope: never filter by team (personal memories)
    if (mScope === 'USER' || mScope === 'AGENT') {
      return true;
    }

    // Fallback: no team filtering
    return true;
  });
}

/**
 * List memories for a specific team (ignores current context)
 * @param {Array} memories
 * @param {string} teamId
 * @returns {Array}
 */
export function listTeamMemories(memories, teamId) {
  if (!teamId) return [];
  return memories.filter(m => memoryBelongsToTeam(m, teamId));
}

/**
 * Get memory namespace key for storage
 * @param {string|null} teamId
 * @returns {string}
 */
export function getMemoryNamespace(teamId) {
  return teamId ? `team:${teamId}` : 'default';
}

/**
 * Tag a memory object with team context before storage
 * @param {object} memory
 * @param {string|null} teamId
 * @returns {object} memory with team_id set
 */
export function tagWithTeam(memory, teamId) {
  if (!teamId) return memory;
  return {
    ...memory,
    team_id: teamId,
    id: (memory.id && !memory.id.startsWith('team:'))
      ? `team:${teamId}:${memory.id}`
      : memory.id,
  };
}

/**
 * Extract team_id from a memory id prefix
 * @param {string} id
 * @returns {string|null}
 */
export function extractTeamFromId(id) {
  const match = id.match(/^team:([^:]+):/);
  return match ? match[1] : null;
}

export default {
  SCOPE_LEVELS,
  SCOPE_HIERARCHY,
  normalizeScope,
  getEffectiveScope,
  filterByScope,
  matchesScope,
  createTeamNamespace,
  deleteTeamNamespace,
  listTeams,
  setCurrentTeam,
  getCurrentTeam,
  switchTeam,
  getTeamPrefix,
  memoryBelongsToTeam,
  filterByTeamAndScope,
  listTeamMemories,
  getMemoryNamespace,
  tagWithTeam,
  extractTeamFromId,
};

// Helper: returns scope order for sorting (lower = more specific)
export function getScopeOrder(scope) {
  return SCOPE_HIERARCHY[normalizeScope(scope)] ?? 999;
}
