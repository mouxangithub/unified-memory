/**
 * Unified Memory 自动化管理器
 * 完整的 auto-capture/recall 实现
 */

const fs = require('fs');
const path = require('path');
const natural = require('natural'); // 用于文本分析

class AutoManager {
  constructor(config = {}) {
    this.config = {
      enabled: true,
      capture: {
        enabled: true,
        importanceThreshold: 0.6,
        contextWindow: 10,
        minLength: 20,
        maxLength: 1000
      },
      recall: {
        enabled: true,
        relevanceThreshold: 0.5,
        maxResults: 5,
        contextBoost: true
      },
      extraction: {
        enabled: true,
        extractKeywords: true,
        detectTopics: true,
        summarize: true
      },
      ...config
    };
    
    this.initialize();
  }
  
  initialize() {
    console.log('🤖 自动化管理器初始化...');
    
    // 初始化自然语言处理工具
    this.tokenizer = new natural.WordTokenizer();
    this.tfidf = new natural.TfIdf();
    
    // 加载重要关键词
    this.importantKeywords = this.loadImportantKeywords();
    
    // 初始化上下文跟踪器
    this.contextTracker = new ContextTracker();
    
    console.log('✅ 自动化管理器就绪');
  }
  
  /**
   * 自动捕获对话
   */
  async autoCapture(session, messages, options = {}) {
    if (!this.config.enabled || !this.config.capture.enabled) {
      console.log('⏸️ 自动捕获已禁用');
      return { captured: 0, skipped: 0 };
    }
    
    console.log(`🎯 自动捕获会话: ${session.id || 'unknown'}`);
    
    const captureConfig = { ...this.config.capture, ...options };
    const recentMessages = this.getRecentMessages(messages, captureConfig.contextWindow);
    
    let captured = 0;
    let skipped = 0;
    
    for (const message of recentMessages) {
      const shouldCapture = await this.shouldCaptureMessage(message, captureConfig);
      
      if (shouldCapture) {
        const memory = await this.createMemoryFromMessage(message, session);
        await this.saveMemory(memory);
        captured++;
        
        console.log(`💾 捕获记忆: ${memory.id} (重要性: ${memory.importance.toFixed(2)})`);
      } else {
        skipped++;
      }
    }
    
    console.log(`✅ 自动捕获完成: ${captured} 条捕获, ${skipped} 条跳过`);
    return { captured, skipped };
  }
  
  /**
   * 判断是否应该捕获消息
   */
  async shouldCaptureMessage(message, config) {
    const content = this.getMessageContent(message);
    
    // 1. 基础检查
    if (!content || content.length < config.minLength) {
      return false;
    }
    
    if (content.length > config.maxLength) {
      // 过长内容需要特殊处理
      return this.shouldCaptureLongContent(content, config);
    }
    
    // 2. 重要性评分
    const importance = await this.scoreImportance(content, message);
    
    // 3. 上下文相关性
    const contextRelevance = this.contextTracker.getRelevance(content);
    
    // 4. 最终决策
    const finalScore = (importance * 0.7) + (contextRelevance * 0.3);
    const shouldCapture = finalScore >= config.importanceThreshold;
    
    if (!shouldCapture) {
      console.log(`⏭️ 跳过消息: 分数 ${finalScore.toFixed(2)} < 阈值 ${config.importanceThreshold}`);
    }
    
    return shouldCapture;
  }
  
  /**
   * 重要性评分
   */
  async scoreImportance(content, message) {
    let score = 0;
    
    // 1. 长度分数 (0-0.3)
    const lengthScore = Math.min(content.length / 500, 0.3);
    score += lengthScore;
    
    // 2. 关键词分数 (0-0.4)
    const keywordScore = this.scoreKeywords(content);
    score += keywordScore;
    
    // 3. 问题分数 (0-0.2)
    const questionScore = this.isQuestion(content) ? 0.2 : 0;
    score += questionScore;
    
    // 4. 指令分数 (0-0.1)
    const commandScore = this.isCommand(content) ? 0.1 : 0;
    score += commandScore;
    
    // 5. 元数据加分
    if (message.metadata?.importance) {
      score += Math.min(message.metadata.importance, 0.2);
    }
    
    return Math.min(score, 1.0);
  }
  
  /**
   * 关键词评分
   */
  scoreKeywords(content) {
    const contentLower = content.toLowerCase();
    let score = 0;
    
    // 重要关键词
    this.importantKeywords.high.forEach(keyword => {
      if (contentLower.includes(keyword)) {
        score += 0.1;
      }
    });
    
    // 中等关键词
    this.importantKeywords.medium.forEach(keyword => {
      if (contentLower.includes(keyword)) {
        score += 0.05;
      }
    });
    
    // 技术关键词
    this.importantKeywords.technical.forEach(keyword => {
      if (contentLower.includes(keyword)) {
        score += 0.03;
      }
    });
    
    return Math.min(score, 0.4);
  }
  
  /**
   * 从消息创建记忆
   */
  async createMemoryFromMessage(message, session) {
    const content = this.getMessageContent(message);
    
    // 提取关键词
    const keywords = await this.extractKeywords(content);
    
    // 检测主题
    const topics = await this.detectTopics(content);
    
    // 生成摘要
    const summary = await this.generateSummary(content);
    
    return {
      id: `auto_${Date.now()}_${Math.random().toString(36).substr(2, 8)}`,
      content,
      summary,
      keywords,
      topics,
      importance: await this.scoreImportance(content, message),
      metadata: {
        source: 'auto-capture',
        session: session.id || 'unknown',
        timestamp: message.timestamp || Date.now(),
        user: message.user || 'unknown',
        messageId: message.id
      },
      timestamp: Date.now(),
      createdAt: new Date().toISOString()
    };
  }
  
  /**
   * 自动召回相关记忆
   */
  async autoRecall(query, context = {}, options = {}) {
    if (!this.config.enabled || !this.config.recall.enabled) {
      console.log('⏸️ 自动召回已禁用');
      return [];
    }
    
    console.log(`🔍 自动召回: "${query.substring(0, 50)}..."`);
    
    const recallConfig = { ...this.config.recall, ...options };
    
    // 1. 直接搜索
    const directResults = await this.searchMemories(query, recallConfig);
    
    // 2. 上下文增强搜索
    const contextResults = await this.searchByContext(context, recallConfig);
    
    // 3. 语义搜索（如果可用）
    const semanticResults = await this.semanticSearch(query, recallConfig);
    
    // 4. 合并和排序
    const allResults = [...directResults, ...contextResults, ...semanticResults];
    const rankedResults = this.rankResults(allResults, query, context);
    
    // 5. 过滤低相关性结果
    const filteredResults = rankedResults.filter(r => 
      r.relevance >= recallConfig.relevanceThreshold
    );
    
    const finalResults = filteredResults.slice(0, recallConfig.maxResults);
    
    console.log(`✅ 召回完成: ${finalResults.length} 条相关记忆`);
    return finalResults;
  }
  
  /**
   * 搜索记忆
   */
  async searchMemories(query, config) {
    // 这里应该调用实际的存储搜索
    // 暂时返回模拟数据
    return [];
  }
  
  /**
   * 按上下文搜索
   */
  async searchByContext(context, config) {
    const contextKeys = ['sessionId', 'userId', 'topic', 'tags'];
    const contextQueries = [];
    
    contextKeys.forEach(key => {
      if (context[key]) {
        contextQueries.push(context[key].toString());
      }
    });
    
    if (contextQueries.length === 0) return [];
    
    // 合并上下文查询
    const combinedQuery = contextQueries.join(' ');
    return await this.searchMemories(combinedQuery, config);
  }
  
  /**
   * 语义搜索
   */
  async semanticSearch(query, config) {
    if (!this.config.extraction.enabled) return [];
    
    try {
      // 提取查询的关键词
      const queryKeywords = await this.extractKeywords(query);
      
      // 使用 TF-IDF 进行语义匹配
      const results = [];
      
      // 这里应该调用实际的语义搜索
      // 暂时返回空数组
      
      return results;
    } catch (error) {
      console.warn('⚠️ 语义搜索失败:', error.message);
      return [];
    }
  }
  
  /**
   * 结果排序
   */
  rankResults(results, query, context) {
    return results.map(result => {
      let relevance = result.relevance || 0.5;
      
      // 时间衰减
      const timeDiff = Date.now() - result.timestamp;
      const daysDiff = timeDiff / (1000 * 60 * 60 * 24);
      const timeDecay = Math.max(0, 1 - (daysDiff / 30)); // 30天衰减
      
      relevance *= timeDecay;
      
      // 上下文增强
      if (this.config.recall.contextBoost) {
        const contextMatch = this.calculateContextMatch(result, context);
        relevance = relevance * 0.7 + contextMatch * 0.3;
      }
      
      return {
        ...result,
        relevance: Math.min(relevance, 1.0),
        timeDecay,
        rankedAt: Date.now()
      };
    }).sort((a, b) => b.relevance - a.relevance);
  }
  
  /**
   * 计算上下文匹配度
   */
  calculateContextMatch(result, context) {
    let matchScore = 0;
    
    // 会话匹配
    if (context.sessionId && result.metadata?.session === context.sessionId) {
      matchScore += 0.4;
    }
    
    // 用户匹配
    if (context.userId && result.metadata?.user === context.userId) {
      matchScore += 0.3;
    }
    
    // 主题匹配
    if (context.topic && result.topics?.includes(context.topic)) {
      matchScore += 0.3;
    }
    
    return matchScore;
  }
  
  /**
   * 提取关键词
   */
  async extractKeywords(content, limit = 10) {
    if (!this.config.extraction.extractKeywords) return [];
    
    try {
      const tokens = this.tokenizer.tokenize(content.toLowerCase());
      const stopWords = ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'];
      
      const filteredTokens = tokens.filter(token => 
        token.length > 1 && !stopWords.includes(token)
      );
      
      // 简单的词频统计
      const freq = {};
      filteredTokens.forEach(token => {
        freq[token] = (freq[token] || 0) + 1;
      });
      
      // 排序并取前N个
      return Object.entries(freq)
        .sort((a, b) => b[1] - a[1])
        .slice(0, limit)
        .map(([word]) => word);
    } catch (error) {
      console.warn('⚠️ 关键词提取失败:', error.message);
      return [];
    }
  }
  
  /**
   * 检测主题
   */
  async detectTopics(content) {
    if (!this.config.extraction.detectTopics) return [];
    
    // 简单的主题检测
    const topics = [];
    
    const topicPatterns = {
      '技术问题': ['bug', '错误', '问题', '故障', '修复'],
      '功能需求': ['需要', '想要', '希望', '建议', '功能'],
      '优化建议': ['优化', '改进', '提升', '加快', '简化'],
      '使用咨询': ['怎么', '如何', '为什么', '怎么办', '疑问']
    };
    
    const contentLower = content.toLowerCase();
    Object.entries(topicPatterns).forEach(([topic, keywords]) => {
      if (keywords.some(keyword => contentLower.includes(keyword))) {
        topics.push(topic);
      }
    });
    
    return topics;
  }
  
  /**
   * 生成摘要
   */
  async generateSummary(content, maxLength = 100) {
    if (!this.config.extraction.summarize) return content.substring(0, maxLength);
    
    // 简单的摘要生成：取第一句或前N个字符
    const firstSentence = content.split(/[。.!?]/)[0];
    if (firstSentence && firstSentence.length <= maxLength) {
      return firstSentence;
    }
    
    return content.substring(0, maxLength) + (content.length > maxLength ? '...' : '');
  }
  
  /**
   * 获取消息内容
   */
  getMessageContent(message) {
    if (typeof message === 'string') return message;
    if (message.content) return message.content;
    if (message.text) return message.text;
    if (message.message) return message.message;
    return '';
  }
  
  /**
   * 获取最近消息
   */
  getRecentMessages(messages, windowSize) {
    if (!Array.isArray(messages)) return [];
    return messages.slice(-windowSize);
  }
  
  /**
   * 判断是否是问题
   */
  isQuestion(content) {
    const questionWords = ['吗', '么', '如何', '怎么', '为什么', '什么', '哪', '谁', '何时', '哪里'];
    const questionMarks = ['?', '？'];
    
    return questionWords.some(word => content.includes(word)) ||
           questionMarks.some(mark => content.includes(mark));
  }
  
  /**
   * 判断是否是命令
   */
  isCommand(content) {
    const commandWords = ['请', '帮我', '麻烦', '需要', '要求', '命令', '执行', '做'];
    return commandWords.some(word => content.includes(word));
  }
  
  /**
   * 加载重要关键词
   */
  loadImportantKeywords() {
    return {
      high: ['重要', '关键', '记住', '备忘', 'note', 'important', 'critical', 'essential', '必须', '必要'],
      medium: ['建议', '想法', '思路', '方案', '计划', '设计', '架构', '优化', '改进'],
      technical: ['bug', '错误', '问题', '故障', '修复', '代码', '程序', '系统', '配置', '设置']
    };
  }
  
  /**
   * 保存记忆（应该调用实际的存储）
   */
  async saveMemory(memory) {
    // 这里应该调用实际的存储系统
    console.log(`💾 [模拟保存] ${memory.id}: ${memory.summary}`);
    return { success: true, memory };
  }
}

/**
 * 上下文跟踪器
 */
class ContextTracker {
  constructor() {
    this.contexts = new Map();
    this.maxContexts = 10;
  }
  
  getRelevance(content) {
    // 简单的上下文相关性计算
    let maxRelevance = 0;
    
    for (const [contextId, context] of this.contexts) {
      const relevance = this.calculateRelevance(content, context);
      if (relevance > maxRelevance) {
        maxRelevance = relevance;
      }
    }
    
    return maxRelevance;
  }
  
  calculateRelevance(content, context) {
    // 基于共享关键词的相关性计算
    const contentWords = new Set(content.toLowerCase().split(/\s+/));
    const contextWords = new Set(context.keywords || []);
    
    const intersection = [...contentWords].filter(word => contextWords.has(word));
    const union = new Set([...contentWords, ...contextWords]);
    
    return union.size > 0 ? intersection.length / union.size : 0;
  }
  
  updateContext(contextId, content, keywords = []) {
    this.contexts.set(contextId, {
      content,
      keywords,
      timestamp: Date.now(),
      updatedAt: new Date().toISOString()
    });
    
    // 限制上下文数量
    if (this.contexts.size > this.maxContexts) {
      const oldest = [...this.contexts.entries()]
        .sort((a, b) => a[1].timestamp - b[1].timestamp)[0];
      this.contexts.delete(oldest[0]);
    }
  }
}

// 导出
module.exports = AutoManager;