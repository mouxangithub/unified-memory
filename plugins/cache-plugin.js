/**
 * Cache Plugin - 缓存增强插件
 * 提供 LRU 缓存和查询结果缓存
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';
import crypto from 'crypto';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const require = createRequire(import.meta.url);

// 简单 LRU 缓存实现
class LRUCache {
  constructor(maxSize = 1000, ttl = 3600000) {
    this.maxSize = maxSize;
    this.ttl = ttl; // 毫秒
    this.cache = new Map();
    this.accessOrder = [];
  }
  
  get(key) {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    // 检查过期
    if (Date.now() - entry.timestamp > this.ttl) {
      this.cache.delete(key);
      this.removeFromAccessOrder(key);
      return null;
    }
    
    // 更新访问顺序
    this.removeFromAccessOrder(key);
    this.accessOrder.push(key);
    
    return entry.value;
  }
  
  set(key, value) {
    // 如果已存在，先删除
    if (this.cache.has(key)) {
      this.cache.delete(key);
      this.removeFromAccessOrder(key);
    }
    
    // 检查容量
    while (this.cache.size >= this.maxSize) {
      const oldest = this.accessOrder.shift();
      if (oldest) {
        this.cache.delete(oldest);
      }
    }
    
    this.cache.set(key, {
      value,
      timestamp: Date.now()
    });
    this.accessOrder.push(key);
  }
  
  has(key) {
    return this.get(key) !== null;
  }
  
  remove(key) {
    this.cache.delete(key);
    this.removeFromAccessOrder(key);
  }
  
  clear() {
    this.cache.clear();
    this.accessOrder = [];
  }
  
  removeFromAccessOrder(key) {
    const index = this.accessOrder.indexOf(key);
    if (index > -1) {
      this.accessOrder.splice(index, 1);
    }
  }
  
  getStats() {
    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      ttl: this.ttl
    };
  }
}

// 生成缓存键
function generateCacheKey(type, ...args) {
  const data = JSON.stringify({ type, args });
  return crypto.createHash('md5').update(data).digest('hex');
}

// 插件配置
let pluginConfig = {
  maxSize: 500,
  ttl: 300000, // 5分钟
  persistCache: true,
  cacheFile: path.join(__dirname, '..', 'cache', 'query-cache.json')
};

// 缓存实例
let memoryCache;
let searchCache;

export default {
  name: 'cache',
  version: '1.0.0',
  description: '增强缓存功能，提供 LRU 缓存和查询结果缓存',
  author: 'unified-memory',
  dependencies: [],
  
  defaultConfig: {
    maxSize: 500,
    ttl: 300000,
    persistCache: true,
    cacheFile: path.join(__dirname, '..', 'cache', 'query-cache.json')
  },
  
  async initialize(context) {
    pluginConfig = { ...pluginConfig, ...context.config };
    
    memoryCache = new LRUCache(pluginConfig.maxSize, pluginConfig.ttl);
    searchCache = new LRUCache(pluginConfig.maxSize * 2, pluginConfig.ttl);
    
    // 加载持久化缓存
    if (pluginConfig.persistCache) {
      loadPersistedCache();
    }
    
    console.log(`💾 Cache plugin initialized: maxSize=${pluginConfig.maxSize}, ttl=${pluginConfig.ttl}ms`);
  },
  
  async destroy(context) {
    if (pluginConfig.persistCache) {
      persistCache();
    }
    console.log(`💾 Cache plugin shutting down`);
  },
  
  hooks: {
    // 记忆加载前检查缓存
    beforeLoad: async (context) => {
      const cacheKey = 'all_memories';
      const cached = memoryCache.get(cacheKey);
      if (cached) {
        context.setState('cacheHit', true);
        context.setState('cachedMemories', cached);
      }
      return true;
    },
    
    // 记忆加载后缓存结果
    afterLoad: async (memories, context) => {
      const cacheKey = 'all_memories';
      if (!context.getState('cacheHit')) {
        memoryCache.set(cacheKey, memories);
      }
      return context.getState('cacheHit') ? context.getState('cachedMemories') : memories;
    },
    
    // 搜索前检查缓存
    beforeSearch: async (query, context) => {
      const cacheKey = generateCacheKey('search', query);
      const cached = searchCache.get(cacheKey);
      if (cached) {
        context.setState('searchCacheHit', true);
        context.setState('cachedResults', cached);
      }
      return query;
    },
    
    // 搜索后缓存结果
    afterSearch: async (results, context) => {
      const cacheKey = generateCacheKey('search', context.getState('lastQuery') || '');
      if (!context.getState('searchCacheHit') && results) {
        searchCache.set(cacheKey, results);
      }
      return context.getState('searchCacheHit') ? context.getState('cachedResults') : results;
    },
    
    // 保存后清除相关缓存
    afterSave: async (memory, context) => {
      // 清除记忆缓存
      memoryCache.remove('all_memories');
      // 清除所有搜索缓存（保守策略）
      searchCache.clear();
      return memory;
    },
    
    // 删除后清除缓存
    afterDelete: async (memoryId, context) => {
      memoryCache.remove('all_memories');
      searchCache.clear();
      return memoryId;
    }
  }
};

// 持久化缓存
function persistCache() {
  const cacheDir = path.dirname(pluginConfig.cacheFile);
  if (!fs.existsSync(cacheDir)) {
    fs.mkdirSync(cacheDir, { recursive: true });
  }
  
  const data = {
    memory: Array.from(memoryCache.cache.entries()),
    search: Array.from(searchCache.cache.entries()),
    persistedAt: new Date().toISOString()
  };
  
  try {
    fs.writeFileSync(pluginConfig.cacheFile, JSON.stringify(data), 'utf8');
    console.log(`💾 Cache persisted to: ${pluginConfig.cacheFile}`);
  } catch (error) {
    console.error(`💾 Failed to persist cache:`, error.message);
  }
}

function loadPersistedCache() {
  if (!fs.existsSync(pluginConfig.cacheFile)) return;
  
  try {
    const data = JSON.parse(fs.readFileSync(pluginConfig.cacheFile, 'utf8'));
    
    if (data.memory) {
      data.memory.forEach(([key, entry]) => {
        // 只加载未过期的
        if (Date.now() - entry.timestamp < pluginConfig.ttl) {
          memoryCache.cache.set(key, entry);
        }
      });
    }
    
    if (data.search) {
      data.search.forEach(([key, entry]) => {
        if (Date.now() - entry.timestamp < pluginConfig.ttl) {
          searchCache.cache.set(key, entry);
        }
      });
    }
    
    console.log(`💾 Loaded persisted cache`);
  } catch (error) {
    console.error(`💾 Failed to load persisted cache:`, error.message);
  }
}

// 导出缓存统计
export function getCacheStats() {
  return {
    memory: memoryCache?.getStats() || { size: 0 },
    search: searchCache?.getStats() || { size: 0 }
  };
}

export function clearAllCache() {
  memoryCache?.clear();
  searchCache?.clear();
  console.log('💾 All caches cleared');
}
