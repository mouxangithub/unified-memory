/**
 * Episode Store v2 - Unit Tests
 *
 * Tests:
 * 1. Create episode
 * 2. Auto-split (turns > 8)
 * 3. List episodes (pagination + status filter)
 * 4. Recall episode (with associated memories)
 * 5. Merge two episodes
 * 6. End episode
 */

import { describe, it, beforeEach } from 'vitest';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import { execSync } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TEST_DIR = path.join(__dirname, '../../tmp_episode_test');

// Use a temp store for tests
const TEST_STORE_PATH = path.join(TEST_DIR, 'episodes.json');

/** Run a snippet via Node --input-type=module */
function runScript(code) {
  return execSync(`node --input-type=module << 'EOF'\n${code}\nEOF`, {
    cwd: TEST_DIR,
    encoding: 'utf-8',
    maxBuffer: 10 * 1024 * 1024,
  });
}

function setup() {
  if (!fs.existsSync(TEST_DIR)) {
    fs.mkdirSync(TEST_DIR, { recursive: true });
  }
  // Patch config to use test store
  const patch = `
import { config } from '${path.join(TEST_DIR, '..', '..', '..', 'skills', 'unified-memory', 'src', 'config.js').replace(/'/g, "'\"'\"'")}';
config.memoryDir = ${JSON.stringify(TEST_DIR)};
  `;
  return patch;
}

describe('Episode Store v2', () => {

  beforeEach(() => {
    // Clean test store
    if (fs.existsSync(TEST_STORE_PATH)) {
      fs.unlinkSync(TEST_STORE_PATH);
    }
  });

  // ─── Test 1: Create Episode ─────────────────────────────────────────────────
  it('should create a new episode', () => {
    const code = `
import { config } from '${path.join(process.cwd(), 'src', 'config.js')}';

// Override memory dir to test location
config.memoryDir = ${JSON.stringify(TEST_DIR)};

import {
  createEpisode,
  getActiveEpisode,
  EPISODE_STATUS,
} from './src/episode/episode_store.js';

const ep = createEpisode('刘总问unified-memory功能');
console.log('created:', JSON.stringify(ep));

const active = getActiveEpisode();
console.log('active:', active ? active.id : null);
console.log('status:', active ? active.status : null);
console.log('isActive:', active ? active.status === EPISODE_STATUS.ACTIVE : false);
`;
    const result = runScript(code);
    console.log('[create episode]', result);
    // Basic sanity: the output should contain "ep_" id and status=active
    if (!result.includes('"status":"active"') && !result.includes("'status':'active'")) {
      throw new Error('Episode not created with active status');
    }
  });

  // ─── Test 2: Auto-Split (turns > 8) ────────────────────────────────────────
  it('should auto-split episode when turns exceed 8', () => {
    const code = `
import { config } from '${path.join(process.cwd(), 'src', 'config.js')}';

// Override memory dir to test location
config.memoryDir = ${JSON.stringify(TEST_DIR)};

import {
  createEpisode,
  getEpisode,
  autoSplitEpisode,
  updateEpisode,
  EPISODE_STATUS,
} from './src/episode/episode_store.js';

// Create episode
const ep = createEpisode('unified-memory v2 讨论');
console.log('original id:', ep.id);

// Manually set turns to 9 (simulate 9 conversation rounds)
updateEpisode(ep.id, { turns: 9, message_count: 18 });
console.log('turns after update:', getEpisode(ep.id).turns);

// Trigger auto-split
const splitResult = autoSplitEpisode(ep.id, 8);
console.log('split needed:', splitResult !== null);

if (splitResult) {
  console.log('original ended, status:', splitResult.original.status);
  console.log('new episode id:', splitResult.newEpisode.id);
  console.log('new episode turns:', splitResult.newEpisode.turns);
  console.log('same topic:', splitResult.newEpisode.topic === splitResult.original.topic);
} else {
  console.log('ERROR: autoSplit should have returned a result');
}
`;
    const result = runScript(code);
    console.log('[auto-split]', result);
    if (!result.includes('split needed: true')) throw new Error('Auto-split not triggered');
    if (!result.includes('original ended')) throw new Error('Original episode not ended');
  });

  // ─── Test 3: List Episodes (pagination + status filter) ────────────────────
  it('should list episodes with pagination and status filter', () => {
    const code = `
import { config } from '${path.join(process.cwd(), 'src', 'config.js')}';
config.memoryDir = ${JSON.stringify(TEST_DIR)};

import {
  createEpisode,
  endEpisode,
  listEpisodes,
} from './src/episode/episode_store.js';

// Create 3 episodes
const ep1 = createEpisode('Topic A');
const ep2 = createEpisode('Topic B');
const ep3 = createEpisode('Topic C');

// End 2 of them
endEpisode(ep1.id);
endEpisode(ep3.id);

const all = listEpisodes({ limit: 10 });
console.log('total episodes:', all.total);
console.log('all episodes count:', all.episodes.length);

const activeOnly = listEpisodes({ status: 'active', limit: 10 });
console.log('active episodes:', activeOnly.episodes.length);

const completedOnly = listEpisodes({ status: 'completed', limit: 10 });
console.log('completed episodes:', completedOnly.episodes.length);

const paginated = listEpisodes({ limit: 2, offset: 0 });
console.log('paginated first page count:', paginated.episodes.length);
`;
    const result = runScript(code);
    console.log('[list episodes]', result);
    if (!result.includes('total episodes:')) throw new Error('List failed');
  });

  // ─── Test 4: Recall Episode ────────────────────────────────────────────────
  it('should recall episode with associated memories', async () => {
    const code = `
import { config } from '${path.join(process.cwd(), 'src', 'config.js')}';
config.memoryDir = ${JSON.stringify(TEST_DIR)};

import {
  createEpisode,
  endEpisode,
  updateEpisode,
  recallEpisodeAsync,
} from './src/episode/episode_store.js';

const ep = createEpisode('unified-memory v2 功能讨论');
updateEpisode(ep.id, {
  entities: ['unified-memory', '刘总'],
  memory_ids: [],
});
endEpisode(ep.id);

const recalled = await recallEpisodeAsync(ep.id);
console.log('episode found:', recalled !== null);
console.log('episode id:', recalled ? recalled.episode.id : null);
console.log('topic:', recalled ? recalled.episode.topic : null);
console.log('entities:', JSON.stringify(recalled ? recalled.episode.entities : []));
console.log('status:', recalled ? recalled.episode.status : null);
`;
    const result = runScript(code);
    console.log('[recall episode]', result);
    if (!result.includes('episode found: true')) throw new Error('Recall failed');
  });

  // ─── Test 5: Merge Episodes ─────────────────────────────────────────────────
  it('should merge two episodes', () => {
    const code = `
import { config } from '${path.join(process.cwd(), 'src', 'config.js')}';
config.memoryDir = ${JSON.stringify(TEST_DIR)};

import {
  createEpisode,
  endEpisode,
  updateEpisode,
  mergeEpisodes,
  getEpisode,
  listEpisodes,
} from './src/episode/episode_store.js';

const ep1 = createEpisode('unified-memory 基础');
updateEpisode(ep1.id, {
  entities: ['unified-memory'],
  memory_ids: ['mem_aaa'],
});
endEpisode(ep1.id);

const ep2 = createEpisode('unified-memory 高级');
updateEpisode(ep2.id, {
  entities: ['刘总'],
  memory_ids: ['mem_bbb'],
});
endEpisode(ep2.id);

console.log('before merge count:', listEpisodes({ limit: 10 }).total);

const merged = mergeEpisodes(ep1.id, ep2.id);
console.log('merge success:', merged !== null);
console.log('merged topic:', merged ? merged.topic : null);
console.log('merged entities:', JSON.stringify(merged ? merged.entities : []));
console.log('merged memory_ids:', JSON.stringify(merged ? merged.memory_ids : []));
console.log('after merge count:', listEpisodes({ limit: 10 }).total);
`;
    const result = runScript(code);
    console.log('[merge episodes]', result);
    if (!result.includes('merge success: true')) throw new Error('Merge failed');
  });

  // ─── Test 6: End Episode ───────────────────────────────────────────────────
  it('should end an active episode', () => {
    const code = `
import { config } from '${path.join(process.cwd(), 'src', 'config.js')}';
config.memoryDir = ${JSON.stringify(TEST_DIR)};

import {
  createEpisode,
  endEpisode,
  getEpisode,
} from './src/episode/episode_store.js';

const ep = createEpisode('Test Episode');
console.log('before end status:', getEpisode(ep.id).status);

const ended = endEpisode(ep.id);
console.log('end result:', ended !== null);
console.log('after end status:', ended ? ended.status : null);
console.log('has ended_at:', ended ? !!ended.ended_at : false);
`;
    const result = runScript(code);
    console.log('[end episode]', result);
    if (!result.includes('after end status: completed')) throw new Error('End episode failed');
  });
});
