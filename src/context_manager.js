/**
 * ContextManager - 智能上下文管理器
 * 
 * 动态管理上下文：
 * - 自动识别当前话题
 * - 智能加载相关记忆
 * - 上下文切换优化
 * 
 * @module context_manager
 */

import { MemoryGraph } from './memory_graph.js';

/**
 * 上下文级别
 */
export const ContextLevel = {
  TIGHT: 'tight',       // 紧凑 - 只包含最相关的
  STANDARD: 'standard', // 标准 - 平衡相关性和广度
  EXPANDED: 'expanded', // 扩展 - 包含更多相关内容
};

/**
 * 话题分类
 */
export const TopicCategory = {
  TECHNICAL: 'technical',
  PROJECT: 'project',
  PERSONAL: 'personal',
  MEETING: 'meeting',
  LEARNING: 'learning',
  GENERAL: 'general',
};

/**
 * 上下文项
 */
class ContextItem {
  constructor(content, metadata = {}) {
    this.id = metadata.id || `ctx_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.content = content;
    this.type = metadata.type || 'memory';
    this.relevance = metadata.relevance || 0.5;
    this.topic = metadata.topic || TopicCategory.GENERAL;
    this.timestamp = metadata.timestamp || Date.now();
    this.accessCount = metadata.accessCount || 0;
    this.source = metadata.source || 'unknown';
  }

  touch() {
    this.accessCount++;
    this.lastAccess = Date.now();
  }
}

/**
 * 智能上下文管理器
 */
export class ContextManager {
  constructor(options = {}) {
    this.maxItems = options.maxItems || 50;
    this.maxTokens = options.maxTokens || 4000;
    this.level = options.level || ContextLevel.STANDARD;
    
    // 上下文存储
    this._currentContext = [];
    this._contextHistory = [];
    this._topicHistory = [];
    
    // 话题追踪
    this._currentTopic = null;
    this._topicConfidence = 0;
    
    // 记忆图谱
    this._memoryGraph = options.memoryGraph || new MemoryGraph();
    
    // 话题关键词
    this._topicKeywords = {
      [TopicCategory.TECHNICAL]: [
        '代码', '编程', 'API', '接口', '数据库', '系统', '技术', '开发',
        'bug', 'debug', 'framework', 'library', 'algorithm'
      ],
      [TopicCategory.PROJECT]: [
        '项目', '需求', 'deadline', '任务', '迭代', '版本', '发布', '进度'
      ],
      [TopicCategory.PERSONAL]: [
        '喜欢', '习惯', '工作方式', '时间', '安排', '生活'
      ],
      [TopicCategory.MEETING]: [
        '会议', '讨论', '评审', '周会', '同步', '沟通'
      ],
      [TopicCategory.LEARNING]: [
        '学习', '了解', '研究', '探索', '教程', '文档'
      ],
    };
  }

  // ─────────────────────────────────────────────────────────────
  // 话题识别
  // ─────────────────────────────────────────────────────────────

  /**
   * 自动识别当前话题
   * @param {string} text - 输入文本
   * @returns {Object} 话题分析结果
   */
  identifyTopic(text) {
    const textLower = text.toLowerCase();
    const scores = {};
    
    for (const [topic, keywords] of Object.entries(this._topicKeywords)) {
      scores[topic] = 0;
      for (const keyword of keywords) {
        if (textLower.includes(keyword.toLowerCase())) {
          scores[topic]++;
        }
      }
    }
    
    // 找出最高分的话题
    let maxTopic = TopicCategory.GENERAL;
    let maxScore = 0;
    
    for (const [topic, score] of Object.entries(scores)) {
      if (score > maxScore) {
        maxScore = score;
        maxTopic = topic;
      }
    }
    
    const confidence = maxScore > 0 ? maxScore / 5 : 0;
    
    // 更新当前话题
    if (confidence > 0.3) {
      this._updateCurrentTopic(maxTopic, confidence, text);
    }
    
    return {
      topic: maxTopic,
      confidence,
      scores,
      allTopics: Object.entries(scores).map(([t, s]) => ({ topic: t, score: s })),
    };
  }

  /**
   * 更新当前话题
   * @private
   */
  _updateCurrentTopic(topic, confidence, text) {
    // 如果话题变化很大，记录历史
    if (this._currentTopic && this._currentTopic !== topic) {
      this._topicHistory.push({
        topic: this._currentTopic,
        confidence: this._topicConfidence,
        endedAt: Date.now(),
      });
    }
    
    this._currentTopic = topic;
    this._topicConfidence = confidence;
  }

  /**
   * 检测话题切换
   * @param {string} text - 新文本
   * @returns {Object} 切换检测结果
   */
  detectTopicSwitch(text) {
    const analysis = this.identifyTopic(text);
    
    if (!this._currentTopic) {
      return { switched: false, newTopic: analysis.topic };
    }
    
    const switched = analysis.topic !== this._currentTopic && analysis.confidence > 0.4;
    
    return {
      switched,
      from: this._currentTopic,
      to: analysis.topic,
      confidence: analysis.confidence,
    };
  }

  // ─────────────────────────────────────────────────────────────
  // 上下文管理
  // ─────────────────────────────────────────────────────────────

  /**
   * 添加到上下文
   * @param {string} content - 内容
   * @param {Object} metadata - 元数据
   * @returns {ContextItem} 添加的上下文项
   */
  addToContext(content, metadata = {}) {
    // 检测话题
    const topicAnalysis = this.identifyTopic(content);
    
    const item = new ContextItem(content, {
      ...metadata,
      topic: topicAnalysis.topic,
      relevance: metadata.relevance || topicAnalysis.confidence,
    });
    
    // 检查是否已存在相似内容
    const existing = this._findSimilar(item);
    if (existing) {
      existing.touch();
      existing.relevance = Math.max(existing.relevance, item.relevance);
      return existing;
    }
    
    // 添加到上下文
    this._currentContext.push(item);
    this._trimContext();
    
    return item;
  }

  /**
   * 智能加载相关记忆
   * @param {string} query - 查询
   * @param {Array} memories - 可用记忆
   * @param {Object} [options] - 选项
   * @returns {Array} 相关记忆
   */
  loadRelevantMemories(query, memories, options = {}) {
    const threshold = options.threshold || 0.3;
    const maxItems = options.maxItems || 10;
    
    // 识别查询的话题
    const queryTopic = this.identifyTopic(query);
    
    // 计算每个记忆的相关性
    const scored = memories.map(memory => {
      const relevance = this._calculateRelevance(query, memory, queryTopic);
      return { memory, relevance };
    });
    
    // 排序并过滤
    const relevant = scored
      .filter(s => s.relevance >= threshold)
      .sort((a, b) => b.relevance - a.relevance)
      .slice(0, maxItems)
      .map(s => s.memory);
    
    // 自动添加到上下文
    for (const mem of relevant) {
      this.addToContext(mem.text || mem.content, {
        type: 'memory',
        relevance: this._calculateRelevance(query, mem, queryTopic),
        source: 'auto_load',
      });
    }
    
    return relevant;
  }

  /**
   * 获取智能上下文
   * @param {Object} [options] - 选项
   * @returns {Array} 上下文项
   */
  getSmartContext(options = {}) {
    const level = options.level || this.level;
    const topic = options.topic || this._currentTopic;
    const maxItems = options.maxItems || this.maxItems;
    
    let context = [...this._currentContext];
    
    // 根据级别调整上下文
    switch (level) {
      case ContextLevel.TIGHT:
        context = context
          .filter(item => item.relevance >= 0.6)
          .sort((a, b) => b.relevance - a.relevance)
          .slice(0, Math.min(10, maxItems));
        break;
      
      case ContextLevel.EXPANDED:
        // 添加历史中的高相关性项
        const recentHistory = this._contextHistory
          .slice(-20)
          .filter(item => item.relevance >= 0.5);
        context = [...context, ...recentHistory];
        break;
      
      case ContextLevel.STANDARD:
      default:
        context = context
          .filter(item => item.relevance >= 0.4)
          .sort((a, b) => {
            // 主要按相关性排序
            if (b.relevance !== a.relevance) return b.relevance - a.relevance;
            // 相关性相同时按时间
            return b.timestamp - a.timestamp;
          })
          .slice(0, maxItems);
        break;
    }
    
    // 如果指定了话题，过滤不相关的
    if (topic) {
      context = context.filter(item => item.topic === topic);
    }
    
    return context;
  }

  /**
   * 获取上下文摘要
   * @returns {Object} 上下文摘要
   */
  getContextSummary() {
    const items = this.getSmartContext({ level: ContextLevel.EXPANDED });
    
    // 按话题分组
    const byTopic = {};
    for (const item of items) {
      if (!byTopic[item.topic]) {
        byTopic[item.topic] = [];
      }
      byTopic[item.topic].push(item);
    }
    
    // 按类型分组
    const byType = {};
    for (const item of items) {
      if (!byType[item.type]) {
        byType[item.type] = [];
      }
      byType[item.type].push(item);
    }
    
    return {
      totalItems: items.length,
      currentTopic: this._currentTopic,
      topicConfidence: this._topicConfidence,
      byTopic,
      byType,
      topItems: items.slice(0, 5).map(i => ({
        content: i.content.substring(0, 50),
        relevance: i.relevance,
        topic: i.topic,
      })),
    };
  }

  /**
   * 清除上下文
   * @param {string} [scope] - 范围: 'current', 'all'
   */
  clearContext(scope = 'current') {
    if (scope === 'all') {
      this._contextHistory = [...this._contextHistory, ...this._currentContext];
      this._currentContext = [];
      this._currentTopic = null;
    } else {
      this._contextHistory = [...this._contextHistory, ...this._currentContext];
      this._currentContext = [];
    }
  }

  // ─────────────────────────────────────────────────────────────
  // 上下文切换
  // ─────────────────────────────────────────────────────────────

  /**
   * 执行上下文切换
   * @param {string} newTopic - 新话题
   * @param {Object} [options] - 选项
   * @returns {Object} 切换结果
   */
  switchContext(newTopic, options = {}) {
    const preserveHighRelevance = options.preserveHighRelevance !== false;
    const saveToHistory = options.saveToHistory !== false;
    
    // 保存当前上下文
    if (saveToHistory && this._currentContext.length > 0) {
      this._contextHistory.push(...this._currentContext);
    }
    
    // 计算要保留的项目
    const toKeep = [];
    if (preserveHighRelevance) {
      const kept = this._currentContext.filter(item => item.relevance >= 0.8);
      toKeep.push(...kept);
    }
    
    // 切换话题
    this._currentTopic = newTopic;
    this._topicConfidence = 0.5;
    this._currentContext = toKeep;
    
    return {
      success: true,
      previousTopic: this._currentTopic,
      newTopic,
      keptItems: toKeep.length,
    };
  }

  /**
   * 获取上下文切换建议
   * @returns {Array} 切换建议
   */
  getSwitchSuggestions() {
    const suggestions = [];
    
    // 基于话题历史建议
    if (this._topicHistory.length > 0) {
      const recent = this._topicHistory.slice(-3);
      for (const h of recent) {
        if (h.topic !== this._currentTopic) {
          suggestions.push({
            type: 'topic_return',
            topic: h.topic,
            reason: '最近讨论过的话题',
          });
        }
      }
    }
    
    // 基于低相关性项目建议
    const lowRelevance = this._currentContext.filter(item => item.relevance < 0.3);
    if (lowRelevance.length > 5) {
      suggestions.push({
        type: 'context_cleanup',
        reason: '有太多低相关性项目',
        itemsToRemove: lowRelevance.length,
      });
    }
    
    return suggestions;
  }

  // ─────────────────────────────────────────────────────────────
  // 私有方法
  // ─────────────────────────────────────────────────────────────

  /**
   * 查找相似项
   * @private
   */
  _findSimilar(item) {
    return this._currentContext.find(existing => {
      const text1 = (existing.content || '').toLowerCase();
      const text2 = (item.content || '').toLowerCase();
      return this._simpleSimilarity(text1, text2) > 0.8;
    });
  }

  /**
   * 计算简单相似度
   * @private
   */
  _simpleSimilarity(text1, text2) {
    const words1 = new Set(text1.split(/\s+/));
    const words2 = new Set(text2.split(/\s+/));
    
    const intersection = [...words1].filter(w => words2.has(w)).length;
    const union = new Set([...words1, ...words2]).size;
    
    return union > 0 ? intersection / union : 0;
  }

  /**
   * 计算相关性
   * @private
   */
  _calculateRelevance(query, memory, queryTopic) {
    const queryText = query.toLowerCase();
    const memoryText = (memory.text || memory.content || '').toLowerCase();
    
    // 文本相似度
    const textSim = this._simpleSimilarity(queryText, memoryText);
    
    // 话题匹配度
    const topicMatch = memory.topic === queryTopic.topic ? 0.3 : 0;
    
    // 时间衰减因子
    const age = Date.now() - (memory.timestamp || Date.now());
    const ageFactor = Math.max(0.5, 1 - age / (7 * 24 * 60 * 60 * 1000)); // 7天衰减
    
    return Math.min(1, textSim * 0.5 + topicMatch + ageFactor * 0.2);
  }

  /**
   * 修剪上下文
   * @private
   */
  _trimContext() {
    if (this._currentContext.length > this.maxItems) {
      // 按相关性排序，保留高相关性的
      this._currentContext
        .sort((a, b) => b.relevance - a.relevance)
        .splice(this.maxItems);
    }
  }

  /**
   * 获取统计信息
   * @returns {Object} 统计信息
   */
  getStats() {
    return {
      currentItems: this._currentContext.length,
      historyItems: this._contextHistory.length,
      currentTopic: this._currentTopic,
      topicConfidence: this._topicConfidence,
      topicHistoryLength: this._topicHistory.length,
    };
  }
}

export default ContextManager;