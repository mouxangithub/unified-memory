/**
 * 记忆关联网络 - MemoryGraph
 * 
 * 记忆不是孤立的，通过关联构建知识网络
 * 
 * 功能：
 * - 关联相似记忆
 * - 构建记忆网络
 * - 支持"相关记忆"查询
 * 
 * @module memory_graph
 */

/**
 * 关联类型
 */
export const RelationType = {
  SIMILAR: 'similar',         // 相似
  TEMPORAL: 'temporal',       // 时间相近
  CAUSAL: 'causal',           // 因果关系
  PART_OF: 'part_of',        // 属于（项目的一部分等）
  REFERENCE: 'reference',     // 引用
  TOPIC: 'topic',             // 同一话题
};

/**
 * 节点类型
 */
export const NodeType = {
  MEMORY: 'memory',
  ENTITY: 'entity',
  TOPIC: 'topic',
  PROJECT: 'project',
};

/**
 * 记忆关联网络
 */
export class MemoryGraph {
  constructor(options = {}) {
    // 节点存储：memoryId -> node
    this.nodes = new Map();
    
    // 边存储：sourceId -> [{ targetId, relation, weight }]
    this.edges = new Map();
    
    // 实体索引：entityName -> [memoryId]
    this.entityIndex = new Map();
    
    // 话题索引：topic -> [memoryId]
    this.topicIndex = new Map();
    
    // 项目索引：projectName -> [memoryId]
    this.projectIndex = new Map();
    
    // 相似性缓存
    this.similarityCache = new Map();
    this.maxCacheSize = options.maxCacheSize || 5000;
    
    // 配置
    this.config = {
      similarityThreshold: options.similarityThreshold || 0.6,
      maxRelationsPerNode: options.maxRelationsPerNode || 20,
      autoLink: options.autoLink !== false, // 默认自动关联
    };
  }

  // ─────────────────────────────────────────────────────────────
  // 节点管理
  // ─────────────────────────────────────────────────────────────

  /**
   * 添加记忆节点
   * 
   * @param {Object} memory - 记忆对象（需包含 id, text, category）
   * @returns {Object} 添加的节点
   * 
   * @example
   * graph.addNode({
   *   id: 'mem_123',
   *   text: '用户喜欢单引号',
   *   category: 'preference',
   *   entities: ['单引号'],
   *   project: '后端项目',
   * });
   */
  addNode(memory) {
    const node = {
      id: memory.id,
      text: memory.text || '',
      category: memory.category || 'other',
      importance: memory.importance || 0.5,
      createdAt: memory.createdAt || memory.timestamp || Date.now(),
      metadata: memory.metadata || {},
      entities: memory.entities || [],
      project: memory.project || null,
      topics: memory.topics || [],
    };
    
    this.nodes.set(memory.id, node);
    
    // 更新索引
    this._indexEntity(node);
    this._indexProject(node);
    this._indexTopics(node);
    
    // 自动关联
    if (this.config.autoLink) {
      this._autoLink(node);
    }
    
    return node;
  }

  /**
   * 批量添加节点
   * 
   * @param {Array} memories - 记忆数组
   */
  addNodes(memories) {
    for (const memory of memories) {
      this.addNode(memory);
    }
  }

  /**
   * 获取节点
   * 
   * @param {string} memoryId - 记忆 ID
   * @returns {Object|null} 节点
   */
  getNode(memoryId) {
    return this.nodes.get(memoryId) || null;
  }

  /**
   * 删除节点
   * 
   * @param {string} memoryId - 记忆 ID
   */
  removeNode(memoryId) {
    const node = this.nodes.get(memoryId);
    if (!node) return;
    
    // 删除节点
    this.nodes.delete(memoryId);
    
    // 删除相关边
    this.edges.delete(memoryId);
    for (const [sourceId, edges] of this.edges) {
      const filtered = edges.filter(e => e.targetId !== memoryId);
      if (filtered.length === 0) {
        this.edges.delete(sourceId);
      } else {
        this.edges.set(sourceId, filtered);
      }
    }
    
    // 清理索引
    this._removeFromIndex(memoryId, node);
    
    // 清理缓存
    this.similarityCache.delete(memoryId);
  }

  /**
   * 更新节点
   * 
   * @param {string} memoryId - 记忆 ID
   * @param {Object} updates - 更新内容
   */
  updateNode(memoryId, updates) {
    const node = this.nodes.get(memoryId);
    if (!node) return null;
    
    // 更新字段
    Object.assign(node, updates);
    node.updatedAt = Date.now();
    
    // 重新索引（如果相关字段变化）
    if (updates.entities || updates.project || updates.topics) {
      this._reindexNode(memoryId);
    }
    
    return node;
  }

  // ─────────────────────────────────────────────────────────────
  // 边管理
  // ─────────────────────────────────────────────────────────────

  /**
   * 添加边（关联两个记忆）
   * 
   * @param {string} sourceId - 源节点 ID
   * @param {string} targetId - 目标节点 ID
   * @param {string} relationType - 关系类型
   * @param {number} [weight=1.0] - 权重
   * @returns {Object} 添加的边
   */
  addEdge(sourceId, targetId, relationType, weight = 1.0) {
    if (!this.nodes.has(sourceId) || !this.nodes.has(targetId)) {
      throw new Error('Source or target node not found');
    }
    
    if (sourceId === targetId) {
      throw new Error('Cannot add edge to self');
    }
    
    const edge = {
      sourceId,
      targetId,
      relation: relationType,
      weight: Math.max(0, Math.min(1, weight)),
      createdAt: Date.now(),
    };
    
    // 避免重复边
    const existing = this.getEdge(sourceId, targetId);
    if (existing) {
      existing.weight = Math.max(existing.weight, weight);
      return existing;
    }
    
    if (!this.edges.has(sourceId)) {
      this.edges.set(sourceId, []);
    }
    
    const edges = this.edges.get(sourceId);
    edges.push(edge);
    
    // 限制边的数量
    if (edges.length > this.config.maxRelationsPerNode) {
      // 移除权重最低的边
      edges.sort((a, b) => a.weight - b.weight);
      edges.shift();
    }
    
    return edge;
  }

  /**
   * 获取两点之间的边
   * 
   * @param {string} sourceId - 源节点 ID
   * @param {string} targetId - 目标节点 ID
   * @returns {Object|null} 边
   */
  getEdge(sourceId, targetId) {
    const edges = this.edges.get(sourceId);
    if (!edges) return null;
    return edges.find(e => e.targetId === targetId) || null;
  }

  /**
   * 获取节点的所有边
   * 
   * @param {string} memoryId - 记忆 ID
   * @param {string} [relationType] - 过滤特定关系类型
   * @returns {Array} 边数组
   */
  getEdges(memoryId, relationType = null) {
    const edges = this.edges.get(memoryId) || [];
    if (relationType) {
      return edges.filter(e => e.relation === relationType);
    }
    return [...edges];
  }

  /**
   * 获取节点的所有关系（包括反向）
   * 
   * @param {string} memoryId - 记忆 ID
   * @returns {Array} 所有相关节点和边
   */
  getRelated(memoryId) {
    const related = [];
    
    // 出边
    const outgoing = this.edges.get(memoryId) || [];
    for (const edge of outgoing) {
      const node = this.nodes.get(edge.targetId);
      if (node) {
        related.push({
          node,
          edge,
          direction: 'outgoing',
        });
      }
    }
    
    // 入边
    for (const [sourceId, edges] of this.edges) {
      if (sourceId === memoryId) continue;
      const incoming = edges.find(e => e.targetId === memoryId);
      if (incoming) {
        const node = this.nodes.get(sourceId);
        if (node) {
          related.push({
            node,
            edge: incoming,
            direction: 'incoming',
          });
        }
      }
    }
    
    return related;
  }

  // ─────────────────────────────────────────────────────────────
  // 查询
  // ─────────────────────────────────────────────────────────────

  /**
   * 查找相关记忆
   * 
   * @param {string} memoryId - 记忆 ID
   * @param {Object} [options] - 查询选项
   * @param {number} [options.limit=10] - 返回数量
   * @param {string} [options.relationType] - 过滤关系类型
   * @param {number} [options.minWeight] - 最小权重
   * @returns {Array} 相关记忆
   * 
   * @example
   * const related = graph.findRelated('mem_123', { limit: 5, minWeight: 0.7 });
   */
  findRelated(memoryId, options = {}) {
    const limit = options.limit || 10;
    const relationType = options.relationType;
    const minWeight = options.minWeight ?? 0;
    
    const related = this.getRelated(memoryId);
    
    // 过滤
    let filtered = related.filter(r => {
      if (relationType && r.edge.relation !== relationType) return false;
      if (r.edge.weight < minWeight) return false;
      return true;
    });
    
    // 按权重排序
    filtered.sort((a, b) => b.edge.weight - a.edge.weight);
    
    // 限制数量
    return filtered.slice(0, limit).map(r => ({
      id: r.node.id,
      text: r.node.text,
      category: r.node.category,
      relation: r.edge.relation,
      weight: r.edge.weight,
      direction: r.direction,
    }));
  }

  /**
   * 通过实体查找相关记忆
   * 
   * @param {string} entity - 实体名称
   * @param {Object} [options] - 查询选项
   * @param {string} [options.excludeId] - 排除的记忆 ID
   * @returns {Array} 相关记忆
   */
  findByEntity(entity, options = {}) {
    const memoryIds = this.entityIndex.get(entity) || [];
    const excludeId = options.excludeId;
    
    return memoryIds
      .filter(id => id !== excludeId)
      .map(id => this.nodes.get(id))
      .filter(Boolean)
      .map(node => ({
        id: node.id,
        text: node.text,
        category: node.category,
        matchEntity: entity,
      }));
  }

  /**
   * 通过项目查找记忆
   * 
   * @param {string} project - 项目名称
   * @returns {Array} 项目相关记忆
   */
  findByProject(project) {
    const memoryIds = this.projectIndex.get(project) || [];
    return memoryIds
      .map(id => this.nodes.get(id))
      .filter(Boolean)
      .map(node => ({
        id: node.id,
        text: node.text,
        category: node.category,
        project,
      }));
  }

  /**
   * 通过话题查找记忆
   * 
   * @param {string} topic - 话题
   * @returns {Array} 话题相关记忆
   */
  findByTopic(topic) {
    const memoryIds = this.topicIndex.get(topic) || [];
    return memoryIds
      .map(id => this.nodes.get(id))
      .filter(Boolean)
      .map(node => ({
        id: node.id,
        text: node.text,
        category: node.category,
        topic,
      }));
  }

  /**
   * 查找相似记忆
   * 
   * @param {string} memoryId - 记忆 ID
   * @param {Object} [options] - 查询选项
   * @param {number} [options.limit=5] - 返回数量
   * @param {number} [options.threshold] - 相似度阈值
   * @returns {Array} 相似记忆
   */
  findSimilar(memoryId, options = {}) {
    const limit = options.limit || 5;
    const threshold = options.threshold ?? this.config.similarityThreshold;
    
    const node = this.nodes.get(memoryId);
    if (!node) return [];
    
    // 优先通过边找相似
    const similarEdges = this.getEdges(memoryId, RelationType.SIMILAR);
    const similar = similarEdges
      .filter(e => e.weight >= threshold)
      .map(e => this.nodes.get(e.targetId))
      .filter(Boolean)
      .map(n => ({ id: n.id, text: n.text, similarity: this.getEdge(memoryId, n.id).weight }))
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, limit);
    
    return similar;
  }

  /**
   * 构建子图（获取记忆的局部网络）
   * 
   * @param {string} memoryId - 记忆 ID
   * @param {number} [depth=1] - 深度
   * @returns {Object} 子图数据
   */
  getSubgraph(memoryId, depth = 1) {
    const visited = new Set();
    const nodes = [];
    const edges = [];
    
    const traverse = (id, currentDepth) => {
      if (visited.has(id) || currentDepth > depth) return;
      visited.add(id);
      
      const node = this.nodes.get(id);
      if (!node) return;
      
      nodes.push({
        id: node.id,
        text: node.text.substring(0, 50),
        category: node.category,
      });
      
      const relatedEdges = this.getEdges(id);
      for (const edge of relatedEdges) {
        edges.push({
          source: edge.sourceId,
          target: edge.targetId,
          relation: edge.relation,
          weight: edge.weight,
        });
        
        traverse(edge.targetId, currentDepth + 1);
      }
    };
    
    traverse(memoryId, 0);
    
    return { nodes, edges };
  }

  // ─────────────────────────────────────────────────────────────
  // 分析
  // ─────────────────────────────────────────────────────────────

  /**
   * 获取图的统计信息
   * 
   * @returns {Object} 统计信息
   */
  getStats() {
    let totalEdges = 0;
    for (const edges of this.edges.values()) {
      totalEdges += edges.length;
    }
    
    const relationCounts = {};
    for (const edges of this.edges.values()) {
      for (const edge of edges) {
        relationCounts[edge.relation] = (relationCounts[edge.relation] || 0) + 1;
      }
    }
    
    return {
      nodeCount: this.nodes.size,
      edgeCount: totalEdges,
      entityCount: this.entityIndex.size,
      topicCount: this.topicIndex.size,
      projectCount: this.projectIndex.size,
      relationTypes: relationCounts,
      avgRelationsPerNode: this.nodes.size > 0 
        ? Math.round(totalEdges / this.nodes.size * 100) / 100 
        : 0,
    };
  }

  /**
   * 找出高重要性且高度关联的记忆
   * 
   * @param {number} [topN=10] - 返回数量
   * @returns {Array} 重要且高度关联的记忆
   */
  findCentralMemories(topN = 10) {
    const scores = new Map();
    
    for (const [id, node] of this.nodes) {
      const related = this.getRelated(id);
      const relationScore = Math.min(1, related.length / 10); // 归一化
      const importanceScore = node.importance || 0.5;
      
      // 综合分数 = 重要性 * 0.6 + 关联度 * 0.4
      scores.set(id, importanceScore * 0.6 + relationScore * 0.4);
    }
    
    return Array.from(scores.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, topN)
      .map(([id, score]) => {
        const node = this.nodes.get(id);
        return {
          id,
          text: node.text.substring(0, 50),
          importance: node.importance,
          relationCount: this.getRelated(id).length,
          centralityScore: Math.round(score * 1000) / 1000,
        };
      });
  }

  /**
   * 找出知识空洞（没有被关联的记忆）
   * 
   * @returns {Array} 孤立记忆
   */
  findOrphanMemories() {
    const orphans = [];
    
    for (const [id, node] of this.nodes) {
      const related = this.getRelated(id);
      if (related.length === 0) {
        orphans.push({
          id,
          text: node.text.substring(0, 50),
          category: node.category,
        });
      }
    }
    
    return orphans;
  }

  // ─────────────────────────────────────────────────────────────
  // 序列化
  // ─────────────────────────────────────────────────────────────

  /**
   * 导出图数据
   * 
   * @returns {Object} 图数据
   */
  export() {
    return {
      nodes: Array.from(this.nodes.values()),
      edges: Array.from(this.edges.entries()).flatMap(([sourceId, edges]) =>
        edges.map(e => ({ ...e, sourceId }))
      ),
      entityIndex: Array.from(this.entityIndex.entries()),
      topicIndex: Array.from(this.topicIndex.entries()),
      projectIndex: Array.from(this.projectIndex.entries()),
    };
  }

  /**
   * 导入图数据
   * 
   * @param {Object} data - 图数据
   */
  import(data) {
    this.clear();
    
    // 导入节点
    if (data.nodes) {
      for (const node of data.nodes) {
        this.nodes.set(node.id, node);
      }
    }
    
    // 导入边
    if (data.edges) {
      for (const edge of data.edges) {
        this.edges.set(edge.sourceId, this.edges.get(edge.sourceId) || []);
        this.edges.get(edge.sourceId).push({
          sourceId: edge.sourceId,
          targetId: edge.targetId,
          relation: edge.relation,
          weight: edge.weight,
          createdAt: edge.createdAt,
        });
      }
    }
    
    // 重建索引
    if (data.entityIndex) {
      this.entityIndex = new Map(data.entityIndex);
    }
    if (data.topicIndex) {
      this.topicIndex = new Map(data.topicIndex);
    }
    if (data.projectIndex) {
      this.projectIndex = new Map(data.projectIndex);
    }
  }

  /**
   * 清空图
   */
  clear() {
    this.nodes.clear();
    this.edges.clear();
    this.entityIndex.clear();
    this.topicIndex.clear();
    this.projectIndex.clear();
    this.similarityCache.clear();
  }

  // ─────────────────────────────────────────────────────────────
  // 私有方法
  // ─────────────────────────────────────────────────────────────

  /**
   * 自动关联新节点
   * @private
   */
  _autoLink(node) {
    // 通过实体关联
    for (const entity of node.entities || []) {
      const related = this.findByEntity(entity, { excludeId: node.id });
      for (const relatedNode of related) {
        this.addEdge(node.id, relatedNode.id, RelationType.SIMILAR, 0.7);
      }
    }
    
    // 通过项目关联
    if (node.project) {
      const related = this.findByProject(node.project).filter(r => r.id !== node.id);
      for (const relatedNode of related) {
        this.addEdge(node.id, relatedNode.id, RelationType.PART_OF, 0.8);
      }
    }
    
    // 通过话题关联
    for (const topic of node.topics || []) {
      const related = this.findByTopic(topic).filter(r => r.id !== node.id);
      for (const relatedNode of related) {
        this.addEdge(node.id, relatedNode.id, RelationType.TOPIC, 0.6);
      }
    }
  }

  /**
   * 索引实体
   * @private
   */
  _indexEntity(node) {
    for (const entity of node.entities || []) {
      if (!this.entityIndex.has(entity)) {
        this.entityIndex.set(entity, []);
      }
      const list = this.entityIndex.get(entity);
      if (!list.includes(node.id)) {
        list.push(node.id);
      }
    }
  }

  /**
   * 索引项目
   * @private
   */
  _indexProject(node) {
    if (node.project) {
      if (!this.projectIndex.has(node.project)) {
        this.projectIndex.set(node.project, []);
      }
      const list = this.projectIndex.get(node.project);
      if (!list.includes(node.id)) {
        list.push(node.id);
      }
    }
  }

  /**
   * 索引话题
   * @private
   */
  _indexTopics(node) {
    for (const topic of node.topics || []) {
      if (!this.topicIndex.has(topic)) {
        this.topicIndex.set(topic, []);
      }
      const list = this.topicIndex.get(topic);
      if (!list.includes(node.id)) {
        list.push(node.id);
      }
    }
  }

  /**
   * 重新索引节点
   * @private
   */
  _reindexNode(memoryId) {
    const node = this.nodes.get(memoryId);
    if (!node) return;
    
    // 清理旧索引（简化处理，实际需要存储原始实体）
    // 这里假设实体没有变化，只是更新了引用
  }

  /**
   * 从索引中移除节点
   * @private
   */
  _removeFromIndex(memoryId, node) {
    // 从实体索引移除
    for (const entity of node.entities || []) {
      const list = this.entityIndex.get(entity);
      if (list) {
        const idx = list.indexOf(memoryId);
        if (idx !== -1) list.splice(idx, 1);
        if (list.length === 0) this.entityIndex.delete(entity);
      }
    }
    
    // 从项目索引移除
    if (node.project) {
      const list = this.projectIndex.get(node.project);
      if (list) {
        const idx = list.indexOf(memoryId);
        if (idx !== -1) list.splice(idx, 1);
        if (list.length === 0) this.projectIndex.delete(node.project);
      }
    }
    
    // 从话题索引移除
    for (const topic of node.topics || []) {
      const list = this.topicIndex.get(topic);
      if (list) {
        const idx = list.indexOf(memoryId);
        if (idx !== -1) list.splice(idx, 1);
        if (list.length === 0) this.topicIndex.delete(topic);
      }
    }
  }
}

// ─────────────────────────────────────────────────────────────
// 工厂函数
// ─────────────────────────────────────────────────────────────

let _instance = null;

/**
 * 获取 MemoryGraph 单例
 * @returns {MemoryGraph}
 */
export function getMemoryGraph() {
  if (!_instance) {
    _instance = new MemoryGraph();
  }
  return _instance;
}

export default MemoryGraph;