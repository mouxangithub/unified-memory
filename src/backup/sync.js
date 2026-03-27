/**
 * sync.js - 多Agent记忆同步
 * Ported from Python memory_sync.py
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { join } from 'path';
import { getAllMemories } from '../storage.js';
import { log } from '../utils/logger.js';

const HOME = process.env.HOME || '/root';
const MEMORY_DIR = join(HOME, '.openclaw/workspace/memory');
const SHARED_DIR = join(MEMORY_DIR, 'shared');
const SYNC_STATE_FILE = join(SHARED_DIR, 'sync_state.json');
const NODE_REGISTRY_FILE = join(SHARED_DIR, 'nodes.json');

function ensureSharedDir() {
  if (!existsSync(SHARED_DIR)) {
    mkdirSync(SHARED_DIR, { recursive: true });
  }
}

function loadRegistry() {
  ensureSharedDir();
  try {
    if (existsSync(NODE_REGISTRY_FILE)) {
      return JSON.parse(readFileSync(NODE_REGISTRY_FILE, 'utf-8'));
    }
  } catch { }
  return { nodes: {}, last_updated: new Date().toISOString() };
}

function saveRegistry(registry) {
  registry.last_updated = new Date().toISOString();
  writeFileSync(NODE_REGISTRY_FILE, JSON.stringify(registry, null, 2), 'utf-8');
}

function loadState() {
  ensureSharedDir();
  try {
    if (existsSync(SYNC_STATE_FILE)) {
      return JSON.parse(readFileSync(SYNC_STATE_FILE, 'utf-8'));
    }
  } catch { }
  return {
    schema: 'memory-sync-v1',
    last_sync: null,
    active_nodes: [],
    conflicts: {},
    sync_count: 0
  };
}

function saveState(state) {
  writeFileSync(SYNC_STATE_FILE, JSON.stringify(state, null, 2), 'utf-8');
}

/**
 * 检测冲突
 */
function detectConflicts(existingData, newData) {
  const conflicts = [];
  
  for (const [key, newVal] of Object.entries(newData)) {
    if (!(key in existingData)) continue;
    
    const existingVal = existingData[key];
    if (typeof existingVal === 'string' && typeof newVal === 'string') {
      if (existingVal.trim() !== newVal.trim()) {
        conflicts.push({
          key,
          existing: existingVal.slice(0, 50) + (existingVal.length > 50 ? '...' : ''),
          proposed: newVal.slice(0, 50) + (newVal.length > 50 ? '...' : ''),
          type: 'text_conflict'
        });
      }
    }
  }
  
  return conflicts;
}

/**
 * 获取当前记忆作为字典
 */
function getCurrentMemories() {
  const memories = getAllMemories();
  const result = {};
  for (const m of memories) {
    result[m.id] = m.text || '';
  }
  return result;
}

/**
 * 注册节点
 */
export function registerNode(nodeId) {
  const registry = loadRegistry();
  
  if (!registry.nodes[nodeId]) {
    registry.nodes[nodeId] = {
      registered_at: new Date().toISOString(),
      version: 0,
      status: 'active'
    };
    saveRegistry(registry);
    return { registered: true, node_id: nodeId };
  }
  
  return { registered: false, node_id: nodeId, reason: 'already exists' };
}

/**
 * 注销节点
 */
export function unregisterNode(nodeId) {
  const registry = loadRegistry();
  
  if (registry.nodes[nodeId]) {
    delete registry.nodes[nodeId];
    saveRegistry(registry);
    return { unregistered: true };
  }
  
  return { unregistered: false, reason: 'not found' };
}

/**
 * 获取所有节点
 */
export function getNodes() {
  const registry = loadRegistry();
  return Object.entries(registry.nodes).map(([nodeId, info]) => ({
    node_id: nodeId,
    ...info
  }));
}

/**
 * 记录数据
 */
export function recordData(nodeId, data) {
  const registry = loadRegistry();
  const state = loadState();
  const currentMemories = getCurrentMemories();
  
  const conflicts = detectConflicts(currentMemories, data);
  
  const result = {
    recorded: false,
    conflicts,
    node_id: nodeId
  };
  
  if (conflicts.length > 0) {
    state.conflicts[new Date().toISOString()] = { node_id: nodeId, conflicts };
    result.needs_resolution = true;
  }
  
  // 更新节点版本
  if (registry.nodes[nodeId]) {
    registry.nodes[nodeId].version++;
    registry.nodes[nodeId].last_update = new Date().toISOString();
  }
  
  saveState(state);
  saveRegistry(registry);
  
  result.recorded = true;
  return result;
}

/**
 * 同步
 */
export function sync(sourceNode = null) {
  const registry = loadRegistry();
  const state = loadState();
  
  state.last_sync = new Date().toISOString();
  state.sync_count++;
  state.active_nodes = Object.keys(registry.nodes);
  
  saveState(state);
  
  return {
    synced: true,
    timestamp: state.last_sync,
    nodes: state.active_nodes.length,
    conflicts_pending: Object.keys(state.conflicts).length
  };
}

/**
 * 解决冲突
 */
export function resolveConflicts(strategy = 'last_write_wins') {
  const state = loadState();
  const resolved = [];
  
  for (const [timestamp, conflictData] of Object.entries(state.conflicts)) {
    for (const conflict of conflictData.conflicts || []) {
      resolved.push({
        key: conflict.key,
        strategy,
        result: 'accepted_proposed'
      });
    }
  }
  
  state.conflicts = {};
  saveState(state);
  
  return {
    resolved: resolved.length,
    strategy,
    details: resolved
  };
}

/**
 * 获取状态
 */
export function getSyncStatus() {
  const registry = loadRegistry();
  const state = loadState();
  
  return {
    nodes: Object.keys(registry.nodes).length,
    active_nodes: state.active_nodes,
    last_sync: state.last_sync,
    sync_count: state.sync_count,
    pending_conflicts: Object.keys(state.conflicts).length
  };
}
