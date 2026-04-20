/**
 * Monitor Plugin - 性能监控插件
 * 监控 memory 操作性能和系统资源使用
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const require = createRequire(import.meta.url);

// 性能指标收集器
class MetricsCollector {
  constructor() {
    this.metrics = {
      operations: {
        save: { count: 0, totalTime: 0, min: Infinity, max: 0 },
        search: { count: 0, totalTime: 0, min: Infinity, max: 0 },
        load: { count: 0, totalTime: 0, min: Infinity, max: 0 },
        delete: { count: 0, totalTime: 0, min: Infinity, max: 0 }
      },
      cache: {
        hits: 0,
        misses: 0
      },
      memory: {
        heapUsed: [],
        heapTotal: [],
        rss: [],
        timestamps: []
      },
      errors: []
    };
    
    this.operationTimers = new Map();
    this.maxHistoryLength = 100;
  }
  
  startOperation(operation) {
    this.operationTimers.set(operation, Date.now());
  }
  
  endOperation(operation) {
    const startTime = this.operationTimers.get(operation);
    if (!startTime) return;
    
    const duration = Date.now() - startTime;
    this.operationTimers.delete(operation);
    
    const metrics = this.metrics.operations[operation];
    if (metrics) {
      metrics.count++;
      metrics.totalTime += duration;
      metrics.min = Math.min(metrics.min, duration);
      metrics.max = Math.max(metrics.max, duration);
    }
    
    return duration;
  }
  
  recordCacheHit() {
    this.metrics.cache.hits++;
  }
  
  recordCacheMiss() {
    this.metrics.cache.misses++;
  }
  
  recordMemoryUsage() {
    const mem = process.memoryUsage();
    const entry = {
      heapUsed: mem.heapUsed,
      heapTotal: mem.heapTotal,
      rss: mem.rss,
      external: mem.external,
      timestamp: Date.now()
    };
    
    this.metrics.memory.heapUsed.push(mem.heapUsed);
    this.metrics.memory.heapTotal.push(mem.heapTotal);
    this.metrics.memory.rss.push(mem.rss);
    this.metrics.memory.timestamps.push(entry.timestamp);
    
    // 限制历史长度
    if (this.metrics.memory.timestamps.length > this.maxHistoryLength) {
      this.metrics.memory.heapUsed.shift();
      this.metrics.memory.heapTotal.shift();
      this.metrics.memory.rss.shift();
      this.metrics.memory.timestamps.shift();
    }
  }
  
  recordError(operation, error) {
    this.metrics.errors.push({
      operation,
      error: error.message,
      timestamp: Date.now()
    });
    
    // 只保留最近 50 个错误
    if (this.metrics.errors.length > 50) {
      this.metrics.errors.shift();
    }
  }
  
  getReport() {
    const report = {
      operations: {},
      cache: this.getCacheReport(),
      memory: this.getMemoryReport(),
      errors: this.metrics.errors.slice(-10)
    };
    
    // 计算操作统计
    Object.entries(this.metrics.operations).forEach(([op, metrics]) => {
      if (metrics.count > 0) {
        report.operations[op] = {
          count: metrics.count,
          avgTime: (metrics.totalTime / metrics.count).toFixed(2) + 'ms',
          min: metrics.min === Infinity ? 'N/A' : metrics.min + 'ms',
          max: metrics.max + 'ms',
          totalTime: metrics.totalTime + 'ms'
        };
      } else {
        report.operations[op] = { count: 0 };
      }
    });
    
    return report;
  }
  
  getCacheReport() {
    const total = this.metrics.cache.hits + this.metrics.cache.misses;
    const hitRate = total > 0 ? (this.metrics.cache.hits / total * 100).toFixed(2) + '%' : 'N/A';
    
    return {
      hits: this.metrics.cache.hits,
      misses: this.metrics.cache.misses,
      hitRate,
      total
    };
  }
  
  getMemoryReport() {
    if (this.metrics.memory.timestamps.length === 0) {
      return { current: null, history: 0 };
    }
    
    const latest = this.metrics.memory.timestamps.length - 1;
    return {
      current: {
        heapUsed: this.formatBytes(this.metrics.memory.heapUsed[latest]),
        heapTotal: this.formatBytes(this.metrics.memory.heapTotal[latest]),
        rss: this.formatBytes(this.metrics.memory.rss[latest])
      },
      history: this.metrics.memory.timestamps.length
    };
  }
  
  formatBytes(bytes) {
    if (bytes < 1024) return bytes + 'B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + 'KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + 'MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + 'GB';
  }
  
  reset() {
    this.metrics = {
      operations: {
        save: { count: 0, totalTime: 0, min: Infinity, max: 0 },
        search: { count: 0, totalTime: 0, min: Infinity, max: 0 },
        load: { count: 0, totalTime: 0, min: Infinity, max: 0 },
        delete: { count: 0, totalTime: 0, min: Infinity, max: 0 }
      },
      cache: { hits: 0, misses: 0 },
      memory: { heapUsed: [], heapTotal: [], rss: [], timestamps: [] },
      errors: []
    };
  }
}

// 插件配置
let pluginConfig = {
  reportInterval: 60000, // 1分钟
  collectMemoryInterval: 5000, // 5秒
  enableProfiling: false
};

// 指标收集器实例
let metricsCollector;
let memoryIntervalId;
let reportIntervalId;

export default {
  name: 'monitor',
  version: '1.0.0',
  description: '监控 memory 操作性能和系统资源使用',
  author: 'unified-memory',
  dependencies: [],
  
  defaultConfig: {
    reportInterval: 60000,
    collectMemoryInterval: 5000,
    enableProfiling: false
  },
  
  async initialize(context) {
    pluginConfig = { ...pluginConfig, ...context.config };
    
    metricsCollector = new MetricsCollector();
    
    // 开始定期收集内存使用
    memoryIntervalId = setInterval(() => {
      metricsCollector.recordMemoryUsage();
    }, pluginConfig.collectMemoryInterval);
    
    // 定期输出报告
    reportIntervalId = setInterval(() => {
      const report = metricsCollector.getReport();
      console.log('\n📊 Performance Report:');
      console.log(`   Operations:`, JSON.stringify(report.operations));
      console.log(`   Cache: ${report.cache.hits} hits, ${report.cache.misses} misses (${report.cache.hitRate})`);
      if (report.memory.current) {
        console.log(`   Memory: ${report.memory.current.heapUsed} / ${report.memory.current.heapTotal}`);
      }
    }, pluginConfig.reportInterval);
    
    // 立即收集一次
    metricsCollector.recordMemoryUsage();
    
    console.log(`📊 Monitor plugin initialized`);
  },
  
  async destroy(context) {
    if (memoryIntervalId) clearInterval(memoryIntervalId);
    if (reportIntervalId) clearInterval(reportIntervalId);
    console.log(`📊 Monitor plugin shutting down`);
  },
  
  hooks: {
    beforeSave: async (memory, context) => {
      metricsCollector.startOperation('save');
      return memory;
    },
    
    afterSave: async (result, context) => {
      const duration = metricsCollector.endOperation('save');
      if (duration > 1000) {
        console.warn(`⚠️  Slow save operation: ${duration}ms`);
      }
      return result;
    },
    
    beforeSearch: async (query, context) => {
      metricsCollector.startOperation('search');
      return query;
    },
    
    afterSearch: async (results, context) => {
      const duration = metricsCollector.endOperation('search');
      if (duration > 1000) {
        console.warn(`⚠️  Slow search operation: ${duration}ms`);
      }
      return results;
    },
    
    beforeLoad: async (context) => {
      metricsCollector.startOperation('load');
      return true;
    },
    
    afterLoad: async (memories, context) => {
      metricsCollector.endOperation('load');
      return memories;
    },
    
    beforeDelete: async (memoryId, context) => {
      metricsCollector.startOperation('delete');
      return memoryId;
    },
    
    afterDelete: async (memoryId, context) => {
      metricsCollector.endOperation('delete');
      return memoryId;
    }
  }
};

// 导出获取指标的函数
export function getMetrics() {
  return metricsCollector?.getReport() || null;
}

export function resetMetrics() {
  metricsCollector?.reset();
  console.log('📊 Metrics reset');
}
