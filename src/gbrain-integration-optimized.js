/**
 * GBrain Integration with Performance Optimization - GBrain 性能优化集成
 * 
 * 在原有 GBrain 集成基础上添加性能优化功能
 * 
 * 优化功能：
 * - 查询缓存
 * - 关系图缓存
 * - 实体索引
 * - 关系索引
 * - 批量操作
 * - 异步处理
 * 
 * @module gbrain-integration-optimized
 */

import { GBrainIntegration } from './gbrain-integration.js';
import { createPerformanceOptimizer, PerformanceOptimizer } from './performance_optimizer.js';

/**
 * 性能优化的 GBrain 集成
 */
export class GBrainIntegrationOptimized extends GBrainIntegration {
  constructor(options = {}) {
    super(options);
    
    // 初始化性能优化器
    this.optimizer = createPerformanceOptimizer(options.optimizer);
    
    // 启用性能优化
    this.enableOptimization = options.enableOptimization !== false;
  }

  /**
   * 保存记忆（带性能优化）
   */
  async saveMemory(memory, context = {}) {
    // 如果启用优化，使用异步处理
    if (this.enableOptimization) {
      return await this.optimizer.asyncProcessor.execute(() => 
        super.saveMemory(memory, context)
      );
    }
    
    return super.saveMemory(memory, context);
  }

  /**
   * 搜索记忆（带缓存）
   */
  async search(query, options = {}) {
    if (!this.enableOptimization) {
      return super.search(query, options);
    }
    
    const cacheKey = this.optimizer.queryCache.getCacheKey(query, options);
    const cached = this.optimizer.queryCache.get(cacheKey);
    
    if (cached) {
      return cached;
    }
    
    const results = await super.search(query, options);
    
    // 缓存结果
    this.optimizer.queryCache.set(cacheKey, results);
    
    return results;
  }

  /**
   * 获取实体（带索引）
   */
  getEntity(entityId) {
    if (!this.enableOptimization) {
      return null;
    }
    
    // 先从索引查找
    const indexed = this.optimizer.entityIndex.getById(entityId);
    if (indexed) {
      return indexed;
    }
    
    // 否则从主系统查找
    return null; // 这里需要集成到实际的记忆系统
  }

  /**
   * 添加实体到索引
   */
  indexEntity(entity) {
    if (!this.enableOptimization) return;
    
    this.optimizer.entityIndex.add(entity);
  }

  /**
   * 添加关系到索引
   */
  indexRelationship(relationship) {
    if (!this.enableOptimization) return;
    
    this.optimizer.relationshipIndex.add(relationship);
  }

  /**
   * 获取关系统计（带缓存）
   */
  getRelationshipStats(entityId) {
    if (!this.enableOptimization) {
      return null;
    }
    
    const cached = this.optimizer.relationshipCache.getStats(entityId);
    if (cached) {
      return cached;
    }
    
    // 这里需要计算实际的关系统计
    const stats = {
      total: 0,
      byType: {},
    };
    
    // 缓存统计
    this.optimizer.relationshipCache.setStats(entityId, stats);
    
    return stats;
  }

  /**
   * 批量保存记忆
   */
  async batchSaveMemories(memories, context = {}) {
    if (!this.enableOptimization) {
      // 非优化模式，逐个保存
      const results = [];
      for (const memory of memories) {
        results.push(await this.saveMemory(memory, context));
      }
      return results;
    }
    
    // 优化模式，批量处理
    const tasks = memories.map(memory => () => 
      this.saveMemory(memory, context)
    );
    
    return await this.optimizer.asyncProcessor.executeBatch(tasks);
  }

  /**
   * 批量添加关系
   */
  async batchAddTypedLinks(relations) {
    if (!this.enableOptimization) {
      // 非优化模式，逐个添加
      const results = [];
      for (const relation of relations) {
        this.typedLinks.add(relation.sourceId, relation.targetId, relation.type, relation.metadata);
        results.push(relation);
      }
      return results;
    }
    
    // 优化模式，批量处理
    const tasks = relations.map(relation => () => {
      this.typedLinks.add(relation.sourceId, relation.targetId, relation.type, relation.metadata);
      return relation;
    });
    
    return await this.optimizer.asyncProcessor.executeBatch(tasks);
  }

  /**
   * 获取性能统计
   */
  getPerformanceStats() {
    return this.optimizer.getStats();
  }

  /**
   * 清除缓存和索引
   */
  clearCache() {
    this.optimizer.clear();
  }
}

/**
 * 创建性能优化的 GBrain 集成
 */
export function createGBrainIntegrationOptimized(options = {}) {
  return new GBrainIntegrationOptimized(options);
}
