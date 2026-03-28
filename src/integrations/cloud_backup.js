/**
 * src/integrations/cloud_backup.js
 * 云备份 - SuperMemory API + 通用 REST 两种模式
 */

import { config } from '../config.js';
import { getAllMemories } from '../storage.js';
import { log as logger } from '../logger.js';

export class CloudBackupManager {
  constructor(cfg = {}) {
    this.enabled = cfg.enabled ?? config.cloud?.enabled ?? false;
    this.provider = cfg.provider ?? config.cloud?.provider ?? 'supermemory';
    
    if (this.provider === 'supermemory') {
      this.endpoint = cfg.endpoint ?? config.cloud?.supermemory_endpoint ?? 'https://api.supermemory.ai';
      this.apiKey = cfg.apiKey ?? config.cloud?.supermemory_api_key ?? process.env.SUPERMEMORY_API_KEY;
    } else {
      // Custom REST
      this.endpoint = cfg.endpoint ?? config.cloud?.rest_endpoint ?? 'https://api.example.com';
      this.apiKey = cfg.apiKey ?? config.cloud?.rest_api_key ?? process.env.CLOUD_REST_API_KEY;
    }

    this.scope = cfg.scope ?? 'agent';
  }

  /**
   * 获取 HTTP headers
   */
  _headers() {
    return {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json',
    };
  }

  /**
   * Push 本地记忆到云端
   * @param {Object} opts
   * @param {Array} [opts.memories] - 要推送的记忆，默认全部
   * @param {string} [opts.scope] - 作用域
   */
  async push({ memories, scope } = {}) {
    if (!this.enabled) {
      return { pushed: false, reason: 'cloud backup disabled' };
    }

    const mems = memories || (await getAllMemories({ scope: scope || this.scope }));
    const body = {
      memories: mems,
      scope: scope || this.scope,
      timestamp: Date.now(),
    };

    try {
      if (this.provider === 'supermemory') {
        const res = await fetch(`${this.endpoint}/memories`, {
          method: 'POST',
          headers: this._headers(),
          body: JSON.stringify(body),
        });
        const data = await res.json();
        return { pushed: true, count: mems.length, response: data };
      } else {
        // Generic REST
        const res = await fetch(`${this.endpoint}/sync`, {
          method: 'POST',
          headers: this._headers(),
          body: JSON.stringify({ ...body, direction: 'push' }),
        });
        const data = await res.json();
        return { pushed: true, count: mems.length, response: data };
      }
    } catch (e) {
      logger.error(`Cloud push failed: ${e.message}`);
      return { pushed: false, error: e.message };
    }
  }

  /**
   * Pull 从云端拉取记忆
   * @param {Object} opts
   * @param {string} [opts.scope] - 作用域
   * @param {number} [opts.since] - 拉取此时间之后的记忆
   */
  async pull({ scope, since } = {}) {
    if (!this.enabled) {
      return { pulled: false, reason: 'cloud backup disabled' };
    }

    const url = new URL(`${this.endpoint}/memories`);
    url.searchParams.set('scope', scope || this.scope);
    if (since) url.searchParams.set('since', since);

    try {
      const res = await fetch(url.toString(), { headers: this._headers() });
      const data = await res.json();
      const memories = data.memories || data.results || data || [];
      return { pulled: true, memories, count: memories.length };
    } catch (e) {
      logger.error(`Cloud pull failed: ${e.message}`);
      return { pulled: false, error: e.message };
    }
  }

  /**
   * 双向同步：以时间戳为准，较新者获胜
   */
  async sync({ scope } = {}) {
    if (!this.enabled) {
      return { synced: false, reason: 'cloud backup disabled' };
    }

    // 1. push local
    const pushResult = await this.push({ scope });
    if (!pushResult.pushed) {
      return { synced: false, pushFailed: true, error: pushResult.error };
    }

    // 2. pull remote
    const pullResult = await this.pull({ scope });
    if (!pullResult.pulled) {
      return { synced: false, pullFailed: true, error: pullResult.error };
    }

    // 3. merge: newer wins (simplified - full impl would do proper conflict resolution)
    const local = await getAllMemories({ scope: scope || this.scope });
    const remote = pullResult.memories;

    const merged = this._merge(local, remote);
    
    return {
      synced: true,
      pushCount: pushResult.count,
      pullCount: pullResult.count,
      mergedCount: merged.length,
      conflicts: merged.filter(m => m._conflict).length,
    };
  }

  /**
   * 简单合并策略：按 memory_id 去重，较新者保留
   */
  _merge(local, remote) {
    const map = new Map();

    for (const m of local) {
      map.set(m.id, { ...m, _source: 'local' });
    }
    for (const m of remote) {
      const existing = map.get(m.id);
      if (!existing) {
        map.set(m.id, { ...m, _source: 'remote' });
      } else if (m.updated_at > existing.updated_at) {
        map.set(m.id, { ...m, _source: 'remote', _updated: true });
      }
    }

    return Array.from(map.values());
  }
}

// 导出单例
let _instance = null;
export function getCloudBackupManager(opts = {}) {
  if (!_instance) {
    _instance = new CloudBackupManager(opts);
  }
  return _instance;
}
