/**
 * Typed Links - 类型化链接
 * 
 * 扩展记忆关联网络，支持类型化关系
 * 
 * 功能：
 * - 定义关系类型
 * - 创建/查询关系
 * - 关系图遍历
 * 
 * @module typed_links
 */

import { MemoryGraph, RelationType, NodeType } from './memory_graph.js';

/**
 * 类型化关系类型
 */
export const TypedLinkType = {
  // 人物相关
  WORKS_AT: 'works_at',           // 张三 works_at 公司 A
  MANAGES: 'manages',             // 张三 manages 李四
  COLLEAGUE_OF: 'colleague_of',   // 张三 colleague_of 李四
  REPORTS_TO: 'reports_to',       // 张三 reports_to 王五
  COFOUNDED: 'cofounded',         // 张三 cofounded 公司 A
  INVESTED_IN: 'invested_in',     // 张三 invested_in 公司 A
  KNOWS: 'knows',                 // 张三 knows 李四
  
  // 公司相关
  HAS_PROJECT: 'has_project',     // 公司 A has_project 项目 X
  PARTNER_OF: 'partner_of',       // 公司 A partner_of 公司 B
  COMPETITOR_OF: 'competitor_of', // 公司 A competitor_of 公司 B
  SPONSORED_BY: 'sponsored_by',   // 公司 A sponsored_by 公司 B
  
  // 项目相关
  USES_TECH: 'uses_tech',         // 项目 X uses_tech React
  BLOCKED_BY: 'blocked_by',       // 项目 X blocked_by 依赖 Y
  DEPENDS_ON: 'depends_on',       // 项目 X depends_on 项目 Y
};

/**
 * 关系类型描述
 */
export const RelationDescription = {
  [TypedLinkType.WORKS_AT]: '工作于',
  [TypedLinkType.MANAGES]: '管理',
  [TypedLinkType.COLLEAGUE_OF]: '同事关系',
  [TypedLinkType.REPORTS_TO]: '汇报给',
  [TypedLinkType.COFOUNDED]: '共同创立',
  [TypedLinkType.INVESTED_IN]: '投资',
  [TypedLinkType.KNOWS]: '认识',
  
  [TypedLinkType.HAS_PROJECT]: '有项目',
  [TypedLinkType.PARTNER_OF]: '合作伙伴',
  [TypedLinkType.COMPETITOR_OF]: '竞争对手',
  [TypedLinkType.SPONSORED_BY]: '赞助方',
  
  [TypedLinkType.USES_TECH]: '使用技术',
  [TypedLinkType.BLOCKED_BY]: '被阻塞',
  [TypedLinkType.DEPENDS_ON]: '依赖',
};

/**
 * 类型化链接管理器
 */
export class TypedLinks {
  constructor(options = {}) {
    this.config = {
      maxRelationsPerNode: options.maxRelationsPerNode || 50,
      autoLink: options.autoLink !== false,
    };
    
    // 存储：sourceId -> [{ targetId, type, metadata }]
    this.relations = new Map();
    
    // 索引：targetId -> [{ sourceId, type }]
    this.inboundIndex = new Map();
    
    // 索引：type -> [{ sourceId, targetId }]
    this.typeIndex = new Map();
  }

  /**
   * 添加关系
   */
  add(sourceId, targetId, type, metadata = {}) {
    // 检查是否已存在
    if (this.has(sourceId, targetId, type)) {
      return false;
    }
    
    // 添加关系
    if (!this.relations.has(sourceId)) {
      this.relations.set(sourceId, []);
    }
    
    this.relations.get(sourceId).push({
      targetId,
      type,
      metadata,
      createdAt: Date.now(),
    });
    
    // 更新索引
    if (!this.inboundIndex.has(targetId)) {
      this.inboundIndex.set(targetId, []);
    }
    this.inboundIndex.get(targetId).push({
      sourceId,
      type,
    });
    
    // 更新类型索引
    if (!this.typeIndex.has(type)) {
      this.typeIndex.set(type, []);
    }
    this.typeIndex.get(type).push({
      sourceId,
      targetId,
    });
    
    return true;
  }

  /**
   * 检查关系是否存在
   */
  has(sourceId, targetId, type) {
    const relations = this.relations.get(sourceId) || [];
    return relations.some(r => r.targetId === targetId && r.type === type);
  }

  /**
   * 获取源节点的所有关系
   */
  getOutgoing(sourceId) {
    return this.relations.get(sourceId) || [];
  }

  /**
   * 获取目标节点的所有入站关系
   */
  getInbound(targetId) {
    return this.inboundIndex.get(targetId) || [];
  }

  /**
   * 获取特定类型的关系
   */
  getByType(type) {
    return this.typeIndex.get(type) || [];
  }

  /**
   * 获取特定类型的入站关系
   */
  getInboundByType(targetId, type) {
    const inbound = this.getInbound(targetId);
    return inbound.filter(r => r.type === type);
  }

  /**
   * 获取特定类型的出站关系
   */
  getOutgoingByType(sourceId, type) {
    const outgoing = this.getOutgoing(sourceId);
    return outgoing.filter(r => r.type === type);
  }

  /**
   * 删除关系
   */
  remove(sourceId, targetId, type) {
    const relations = this.relations.get(sourceId) || [];
    const filtered = relations.filter(r => !(r.targetId === targetId && r.type === type));
    
    if (filtered.length === relations.length) {
      return false; // 未找到
    }
    
    this.relations.set(sourceId, filtered);
    
    // 更新索引
    if (this.inboundIndex.has(targetId)) {
      const inbound = this.inboundIndex.get(targetId);
      this.inboundIndex.set(targetId, inbound.filter(r => !(r.sourceId === sourceId && r.type === type)));
    }
    
    if (this.typeIndex.has(type)) {
      const typeRelations = this.typeIndex.get(type);
      this.typeIndex.set(type, typeRelations.filter(r => !(r.sourceId === sourceId && r.targetId === targetId)));
    }
    
    return true;
  }

  /**
   * 遍历关系图
   */
  traverse(startId, maxDepth = 3, visited = new Set()) {
    if (visited.has(startId) || maxDepth <= 0) {
      return [];
    }
    
    visited.add(startId);
    const result = [];
    
    const outgoing = this.getOutgoing(startId);
    for (const relation of outgoing) {
      result.push({
        type: 'direct',
        targetId: relation.targetId,
        relation: relation,
      });
      
      // 递归遍历
      if (maxDepth > 1) {
        const subRelations = this.traverse(relation.targetId, maxDepth - 1, new Set(visited));
        for (const sub of subRelations) {
          sub.type = 'indirect';
          result.push(sub);
        }
      }
    }
    
    return result;
  }

  /**
   * 查询特定类型的关系
   */
  query(query) {
    const { type, sourceId, targetId } = query;
    
    if (type && sourceId && targetId) {
      // 查询特定类型、特定源和目标的关系
      return this.has(sourceId, targetId, type);
    }
    
    if (type && sourceId) {
      // 查询特定类型、特定源的所有关系
      return this.getOutgoingByType(sourceId, type);
    }
    
    if (type && targetId) {
      // 查询特定类型、特定目标的所有入站关系
      return this.getInboundByType(targetId, type);
    }
    
    if (type) {
      // 查询特定类型的所有关系
      return this.getByType(type);
    }
    
    return [];
  }

  /**
   * 获取关系统计
   */
  getStats() {
    const stats = {
      totalRelations: 0,
      byType: {},
      byNode: {},
    };
    
    for (const [sourceId, relations] of this.relations.entries()) {
      stats.totalRelations += relations.length;
      stats.byNode[sourceId] = relations.length;
      
      for (const relation of relations) {
        if (!stats.byType[relation.type]) {
          stats.byType[relation.type] = 0;
        }
        stats.byType[relation.type]++;
      }
    }
    
    return stats;
  }
}

/**
 * 工具函数：创建 Typed Links 实例
 */
export function createTypedLinks(options = {}) {
  return new TypedLinks(options);
}

/**
 * 工具函数：格式化关系
 */
export function formatRelation(relation) {
  const description = RelationDescription[relation.type] || relation.type;
  return `${description}: ${relation.sourceId} → ${relation.targetId}`;
}
