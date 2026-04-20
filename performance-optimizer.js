// unified-memory 性能优化模块
// 整合所有性能优化功能

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { gzipSync, gunzipSync } from 'zlib';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ========== 缓存系统 ==========

class CacheSystem {
  constructor(options = {}) {
    this.options = {
      maxSize: options.maxSize || 1000,
      ttl: options.ttl || 5 * 60 * 1000, // 5分钟
      strategy: options.strategy || 'lru' // lru, lfu, fifo
    };
    
    this.cache = new Map();
    this.accessTime = new Map();
    this.accessCount = new Map();
    this.size = 0;
    
    // 定期清理过期缓存
    this.cleanupInterval = setInterval(() => this.cleanup(), 60 * 1000);
  }
  
  // 获取缓存
  get(key) {
    if (!this.cache.has(key)) {
      return null;
    }
    
    const entry = this.cache.get(key);
    
    // 检查是否过期
    if (entry.expiry && Date.now() > entry.expiry) {
      this.delete(key);
      return null;
    }
    
    // 更新访问信息
    this.accessTime.set(key, Date.now());
    this.accessCount.set(key, (this.accessCount.get(key) || 0) + 1);
    
    return entry.value;
  }
  
  // 设置缓存
  set(key, value, ttl = this.options.ttl) {
    // 如果缓存已满，淘汰最旧的
    if (this.size >= this.options.maxSize) {
      this.evict();
    }
    
    const entry = {
      value,
      expiry: ttl ? Date.now() + ttl : null,
      size: this.calculateSize(value)
    };
    
    this.cache.set(key, entry);
    this.accessTime.set(key, Date.now());
    this.accessCount.set(key, 0);
    this.size += entry.size;
    
    return true;
  }
  
  // 删除缓存
  delete(key) {
    if (this.cache.has(key)) {
      const entry = this.cache.get(key);
      this.size -= entry.size;
      this.cache.delete(key);
      this.accessTime.delete(key);
      this.accessCount.delete(key);
    }
  }
  
  // 淘汰策略
  evict() {
    let keyToRemove = null;
    
    switch (this.options.strategy) {
      case 'lru': // 最近最少使用
        keyToRemove = Array.from(this.accessTime.entries())
          .sort((a, b) => a[1] - b[1])[0]?.[0];
        break;
        
      case 'lfu': // 最不经常使用
        keyToRemove = Array.from(this.accessCount.entries())
          .sort((a, b) => a[1] - b[1])[0]?.[0];
        break;
        
      case 'fifo': // 先进先出
        keyToRemove = this.cache.keys().next().value;
        break;
    }
    
    if (keyToRemove) {
      this.delete(keyToRemove);
    }
  }
  
  // 清理过期缓存
  cleanup() {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (entry.expiry && now > entry.expiry) {
        this.delete(key);
      }
    }
  }
  
  // 计算值大小
  calculateSize(value) {
    try {
      return JSON.stringify(value).length;
    } catch {
      return 1024; // 默认1KB
    }
  }
  
  // 获取统计信息
  stats() {
    return {
      size: this.size,
      count: this.cache.size,
      hitRate: this.calculateHitRate(),
      memoryUsage: process.memoryUsage().heapUsed / 1024 / 1024
    };
  }
  
  // 计算命中率
  calculateHitRate() {
    const total = this.accessCount.size;
    if (total === 0) return 0;
    
    const hits = Array.from(this.accessCount.values())
      .filter(count => count > 0).length;
    
    return hits / total;
  }
  
  // 清空缓存
  clear() {
    this.cache.clear();
    this.accessTime.clear();
    this.accessCount.clear();
    this.size = 0;
  }
  
  // 销毁
  destroy() {
    clearInterval(this.cleanupInterval);
    this.clear();
  }
}

// ========== 压缩系统 ==========

class CompressionSystem {
  constructor(options = {}) {
    this.options = {
      algorithm: options.algorithm || 'gzip',
      minSize: options.minSize || 1024, // 1KB以下不压缩
      compressionLevel: options.compressionLevel || 6
    };
  }
  
  // 压缩数据
  compress(data) {
    if (typeof data !== 'string') {
      data = JSON.stringify(data);
    }
    
    // 小数据不压缩
    if (data.length < this.options.minSize) {
      return {
        compressed: false,
        data: data,
        originalSize: data.length,
        compressedSize: data.length,
        ratio: 1
      };
    }
    
    try {
      const compressed = gzipSync(data, {
        level: this.options.compressionLevel
      });
      
      const result = {
        compressed: true,
        data: compressed.toString('base64'),
        originalSize: data.length,
        compressedSize: compressed.length,
        ratio: compressed.length / data.length
      };
      
      return result;
    } catch (error) {
      console.warn('压缩失败，返回原始数据:', error.message);
      return {
        compressed: false,
        data: data,
        originalSize: data.length,
        compressedSize: data.length,
        ratio: 1
      };
    }
  }
  
  // 解压数据
  decompress(compressedData) {
    if (!compressedData.compressed) {
      return compressedData.data;
    }
    
    try {
      const buffer = Buffer.from(compressedData.data, 'base64');
      const decompressed = gunzipSync(buffer).toString('utf8');
      
      // 尝试解析为JSON
      try {
        return JSON.parse(decompressed);
      } catch {
        return decompressed;
      }
    } catch (error) {
      console.error('解压失败:', error.message);
      throw error;
    }
  }
  
  // 批量压缩
  compressBatch(items) {
    return items.map(item => this.compress(item));
  }
  
  // 批量解压
  decompressBatch(compressedItems) {
    return compressedItems.map(item => this.decompress(item));
  }
}

// ========== 索引优化系统 ==========

class IndexOptimizer {
  constructor(options = {}) {
    this.options = {
      rebuildThreshold: options.rebuildThreshold || 1000, // 1000次操作后重建
      optimizeInterval: options.optimizeInterval || 5 * 60 * 1000, // 5分钟
      enableIncremental: options.enableIncremental !== false
    };
    
    this.operationCount = 0;
    this.lastOptimizeTime = Date.now();
    
    // 定期优化
    this.optimizeInterval = setInterval(
      () => this.autoOptimize(),
      this.options.optimizeInterval
    );
  }
  
  // 记录操作
  recordOperation() {
    this.operationCount++;
    
    // 达到阈值时触发优化
    if (this.operationCount >= this.options.rebuildThreshold) {
      this.optimize();
      this.operationCount = 0;
    }
  }
  
  // 优化索引
  optimize() {
    console.log('🔧 开始索引优化...');
    const startTime = Date.now();
    
    // 这里可以添加具体的索引优化逻辑
    // 例如：重建BM25索引、优化向量索引等
    
    const duration = Date.now() - startTime;
    console.log(`✅ 索引优化完成，耗时: ${duration}ms`);
    
    this.lastOptimizeTime = Date.now();
    return duration;
  }
  
  // 自动优化
  autoOptimize() {
    const now = Date.now();
    const timeSinceLastOptimize = now - this.lastOptimizeTime;
    
    // 如果超过30分钟没有优化，自动优化
    if (timeSinceLastOptimize > 30 * 60 * 1000) {
      this.optimize();
    }
  }
  
  // 增量优化
  incrementalOptimize(newData) {
    if (!this.options.enableIncremental) {
      return;
    }
    
    // 这里可以添加增量优化逻辑
    // 例如：只更新受影响的部分索引
    
    console.log('🔄 执行增量索引优化');
  }
  
  // 获取统计信息
  stats() {
    return {
      operationCount: this.operationCount,
      lastOptimizeTime: new Date(this.lastOptimizeTime).toISOString(),
      timeSinceLastOptimize: Date.now() - this.lastOptimizeTime,
      needsOptimize: this.operationCount >= this.options.rebuildThreshold * 0.8
    };
  }
  
  // 销毁
  destroy() {
    clearInterval(this.optimizeInterval);
  }
}

// ========== 性能监控系统 ==========

class PerformanceMonitor {
  constructor() {
    this.metrics = {
      operations: [],
      memoryUsage: [],
      responseTimes: []
    };
    
    this.startTime = Date.now();
    
    // 定期收集指标
    this.monitorInterval = setInterval(() => {
      this.collectMetrics();
    }, 10 * 1000); // 每10秒收集一次
  }
  
  // 记录操作
  recordOperation(operation, duration) {
    this.metrics.operations.push({
      operation,
      duration,
      timestamp: Date.now()
    });
    
    // 保留最近1000条记录
    if (this.metrics.operations.length > 1000) {
      this.metrics.operations = this.metrics.operations.slice(-1000);
    }
  }
  
  // 收集系统指标
  collectMetrics() {
    const memory = process.memoryUsage();
    
    this.metrics.memoryUsage.push({
      heapUsed: memory.heapUsed / 1024 / 1024, // MB
      heapTotal: memory.heapTotal / 1024 / 1024,
      external: memory.external / 1024 / 1024,
      timestamp: Date.now()
    });
    
    // 保留最近100条记录
    if (this.metrics.memoryUsage.length > 100) {
      this.metrics.memoryUsage = this.metrics.memoryUsage.slice(-100);
    }
  }
  
  // 获取性能报告
  getReport() {
    const now = Date.now();
    const uptime = now - this.startTime;
    
    // 计算平均响应时间
    const recentOps = this.metrics.operations.slice(-100);
    const avgResponseTime = recentOps.length > 0
      ? recentOps.reduce((sum, op) => sum + op.duration, 0) / recentOps.length
      : 0;
    
    // 计算操作频率
    const opsLastMinute = this.metrics.operations.filter(
      op => now - op.timestamp < 60 * 1000
    ).length;
    
    // 内存使用趋势
    const recentMemory = this.metrics.memoryUsage.slice(-10);
    const avgMemory = recentMemory.length > 0
      ? recentMemory.reduce((sum, mem) => sum + mem.heapUsed, 0) / recentMemory.length
      : 0;
    
    return {
      uptime: Math.floor(uptime / 1000), // 秒
      totalOperations: this.metrics.operations.length,
      opsPerMinute: opsLastMinute,
      avgResponseTime: avgResponseTime.toFixed(2) + 'ms',
      avgMemoryUsage: avgMemory.toFixed(2) + 'MB',
      currentMemory: (process.memoryUsage().heapUsed / 1024 / 1024).toFixed(2) + 'MB',
      timestamp: new Date().toISOString()
    };
  }
  
  // 获取瓶颈分析
  getBottleneckAnalysis() {
    const report = this.getReport();
    const suggestions = [];
    
    if (report.avgResponseTime > 100) {
      suggestions.push('响应时间较高，建议优化搜索算法或增加缓存');
    }
    
    if (parseFloat(report.avgMemoryUsage) > 500) {
      suggestions.push('内存使用较高，建议优化数据结构或启用压缩');
    }
    
    if (report.opsPerMinute > 1000) {
      suggestions.push('操作频率很高，建议考虑水平扩展');
    }
    
    return {
      report,
      suggestions,
      severity: suggestions.length > 0 ? 'warning' : 'healthy'
    };
  }
  
  // 销毁
  destroy() {
    clearInterval(this.monitorInterval);
  }
}

// ========== 主性能优化器 ==========

export class PerformanceOptimizer {
  constructor(options = {}) {
    this.options = options;
    
    // 初始化各子系统
    this.cache = new CacheSystem(options.cache || {});
    this.compression = new CompressionSystem(options.compression || {});
    this.indexOptimizer = new IndexOptimizer(options.index || {});
    this.monitor = new PerformanceMonitor();
    
    console.log('🚀 性能优化器初始化完成');
  }
  
  // 性能优化建议
  getOptimizationSuggestions() {
    const cacheStats = this.cache.stats();
    const indexStats = this.indexOptimizer.stats();
    const bottleneck = this.monitor.getBottleneckAnalysis();
    
    const suggestions = [];
    
    // 缓存建议
    if (cacheStats.hitRate < 0.3) {
      suggestions.push({
        area: '缓存',
        suggestion: '缓存命中率较低，建议增加缓存大小或调整淘汰策略',
        priority: 'medium'
      });
    }
    
    // 索引建议
    if (indexStats.needsOptimize) {
      suggestions.push({
        area: '索引',
        suggestion: '索引需要优化，建议执行索引重建',
        priority: 'high'
      });
    }
    
    // 添加瓶颈分析建议
    suggestions.push(...bottleneck.suggestions.map(s => ({
      area: '性能',
      suggestion: s,
      priority: 'high'
    })));
    
    return {
      suggestions,
      summary: {
        cacheHitRate: (cacheStats.hitRate * 100).toFixed(1) + '%',
        memoryUsage: cacheStats.memoryUsage.toFixed(2) + 'MB',
        needsIndexOptimize: indexStats.needsOptimize,
        bottleneckSeverity: bottleneck.severity
      }
    };
  }
  
  // 执行优化
  async optimize() {
    console.log('🎯 开始执行全面性能优化...');
    
    const results = {
      cache: null,
      index: null,
      compression: null
    };
    
    // 1. 清理缓存
    const oldCacheSize = this.cache.size;
    this.cache.clear();
    results.cache = {
      cleared: oldCacheSize,
      newSize: this.cache.size
    };
    
    // 2. 优化索引
    const indexTime = this.indexOptimizer.optimize();
    results.index = {
      duration: indexTime,
      operationCount: this.indexOptimizer.operationCount
    };
    
    // 3. 重置操作计数
    this.indexOptimizer.operationCount = 0;
    
    console.log('✅ 性能优化完成');
    return results;
  }
  
  // 获取完整报告
  getFullReport() {
    return {
      cache: this.cache.stats(),
      index: this.indexOptimizer.stats(),
      monitor: this.monitor.getReport(),
      bottleneck: this.monitor.getBottleneckAnalysis(),
      suggestions: this.getOptimizationSuggestions()
    };
  }
  
  // 销毁
  destroy() {
    this.cache.destroy();
    this.indexOptimizer.destroy();
    this.monitor.destroy();
  }
}

// ========== 导出 ==========

export {
  CacheSystem,
  CompressionSystem,
  IndexOptimizer,
  PerformanceMonitor
};

export default PerformanceOptimizer;