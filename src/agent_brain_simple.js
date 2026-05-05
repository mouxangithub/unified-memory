/**
 * AgentBrain 简化版 - 直接文件存储
 * 用于快速集成到 OpenClaw
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class SimpleAgentBrain {
  constructor(options = {}) {
    this.storageDir = options.storageDir || '/root/.openclaw/workspace/agentbrain_storage';
    this.memoriesFile = path.join(this.storageDir, 'memories.json');
    this.statsFile = path.join(this.storageDir, 'stats.json');
    this._ensureStorageDir();
    this._stats = {
      rememberCount: 0,
      searchCount: 0,
      startTime: Date.now()
    };
  }
  
  async _ensureStorageDir() {
    try {
      await fs.mkdir(this.storageDir, { recursive: true });
    } catch (error) {
      // 目录已存在
    }
  }
  
  async _loadMemories() {
    try {
      const data = await fs.readFile(this.memoriesFile, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      return [];
    }
  }
  
  async _saveMemories(memories) {
    await fs.writeFile(this.memoriesFile, JSON.stringify(memories, null, 2), 'utf-8');
  }
  
  async _saveStats() {
    await fs.writeFile(this.statsFile, JSON.stringify(this._stats, null, 2), 'utf-8');
  }
  
  /**
   * 记住信息
   */
  async remember(text, options = {}) {
    const memories = await this._loadMemories();
    
    const memory = {
      id: `mem_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      text,
      category: options.category || 'general',
      importance: options.importance || 0.5,
      tags: options.tags || [],
      created_at: Date.now(),
      updated_at: Date.now(),
      metadata: options.metadata || {}
    };
    
    memories.push(memory);
    await this._saveMemories(memories);
    
    this._stats.rememberCount++;
    await this._saveStats();
    
    return { success: true, id: memory.id, memory };
  }
  
  /**
   * 搜索记忆
   */
  async search(query, options = {}) {
    const memories = await this._loadMemories();
    
    // 简单文本搜索
    const results = memories.filter(memory => {
      if (!memory.text) return false;
      return memory.text.toLowerCase().includes(query.toLowerCase());
    });
    
    // 按重要性排序
    results.sort((a, b) => (b.importance || 0) - (a.importance || 0));
    
    // 限制结果数量
    const limit = options.limit || 10;
    const limitedResults = results.slice(0, limit);
    
    this._stats.searchCount++;
    await this._saveStats();
    
    return limitedResults;
  }
  
  /**
   * 获取统计信息
   */
  getStats() {
    return {
      ...this._stats,
      uptime: Date.now() - this._stats.startTime,
      storageDir: this.storageDir
    };
  }
  
  /**
   * 获取上下文
   */
  async getContext(options = {}) {
    const memories = await this._loadMemories();
    
    // 获取最近记忆
    const recentMemories = [...memories]
      .sort((a, b) => b.created_at - a.created_at)
      .slice(0, options.limit || 5);
    
    return {
      sessionId: options.sessionId || 'default',
      recentMemories,
      totalMemories: memories.length,
      stats: this.getStats()
    };
  }
  
  /**
   * 清理记忆
   */
  async cleanup(options = {}) {
    const memories = await this._loadMemories();
    const threshold = options.threshold || 0.1;
    const maxAgeDays = options.maxAgeDays || 30;
    const maxAgeMs = maxAgeDays * 24 * 60 * 60 * 1000;
    const cutoffTime = Date.now() - maxAgeMs;
    
    const kept = memories.filter(memory => {
      // 检查重要性
      if ((memory.importance || 0) < threshold) {
        return false;
      }
      // 检查年龄
      if (memory.created_at < cutoffTime) {
        return false;
      }
      return true;
    });
    
    const cleanedCount = memories.length - kept.length;
    
    if (cleanedCount > 0) {
      await this._saveMemories(kept);
    }
    
    return {
      cleanedCount,
      keptCount: kept.length,
      totalBefore: memories.length,
      totalAfter: kept.length
    };
  }
}

// 创建单例
let instance = null;

export function getSimpleAgentBrain(options = {}) {
  if (!instance) {
    instance = new SimpleAgentBrain(options);
  }
  return instance;
}

export { SimpleAgentBrain };