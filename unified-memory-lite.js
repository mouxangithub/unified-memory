/**
 * Unified Memory 轻量版
 * 类似 memory-core-plus 的开箱即用体验
 */

const fs = require('fs');
const path = require('path');

class UnifiedMemoryLite {
  constructor(options = {}) {
    // 零配置初始化
    this.config = this.initializeConfig(options);
    this.storage = this.initializeStorage();
    this.search = this.initializeSearch();
    this.auto = this.initializeAuto();
    
    console.log('🚀 Unified Memory Lite 初始化完成');
    console.log('📊 配置:', JSON.stringify(this.getSummary(), null, 2));
  }
  
  /**
   * 初始化配置（零配置设计）
   */
  initializeConfig(options) {
    const defaultConfig = {
      // 存储配置
      storage: {
        type: 'json',
        path: path.join(__dirname, 'memories-lite.json'),
        autoBackup: true
      },
      
      // 搜索配置
      search: {
        type: 'text',
        limit: 10,
        fuzzy: true
      },
      
      // 自动化配置（默认开启）
      auto: {
        enabled: true,
        capture: true,
        recall: true,
        importanceThreshold: 0.6,
        contextWindow: 10
      },
      
      // 性能配置
      performance: {
        cache: true,
        batchSize: 50,
        compression: false
      },
      
      // 错误处理
      errorHandling: {
        friendly: true,
        autoRecover: true,
        fallbackToSimple: true
      }
    };
    
    // 深度合并配置
    return this.deepMerge(defaultConfig, options);
  }
  
  /**
   * 初始化存储
   */
  initializeStorage() {
    const config = this.config.storage;
    
    // 确保存储目录存在
    const dir = path.dirname(config.path);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    // 初始化存储文件
    if (!fs.existsSync(config.path)) {
      fs.writeFileSync(config.path, JSON.stringify({
        version: '1.0.0',
        memories: [],
        metadata: {
          createdAt: new Date().toISOString(),
          totalMemories: 0,
          lastUpdated: null
        }
      }, null, 2));
    }
    
    return {
      // 保存记忆
      save: (memory) => this.saveMemory(memory),
      
      // 加载记忆
      load: () => this.loadMemories(),
      
      // 获取统计
      stats: () => this.getStorageStats(),
      
      // 备份
      backup: () => this.createBackup()
    };
  }
  
  /**
   * 初始化搜索
   */
  initializeSearch() {
    const config = this.config.search;
    
    return {
      // 文本搜索
      text: (query, options = {}) => this.textSearch(query, options),
      
      // 标签搜索
      byTag: (tag, options = {}) => this.searchByTag(tag, options),
      
      // 最近记忆
      recent: (limit) => this.getRecentMemories(limit),
      
      // 相关记忆
      related: (content, options = {}) => this.findRelated(content, options)
    };
  }
  
  /**
   * 初始化自动化
   */
  initializeAuto() {
    const config = this.config.auto;
    
    if (!config.enabled) {
      return {
        capture: () => Promise.resolve(),
        recall: () => Promise.resolve([])
      };
    }
    
    return {
      // 自动捕获
      capture: (session, messages) => this.autoCapture(session, messages),
      
      // 自动召回
      recall: (query, context) => this.autoRecall(query, context),
      
      // 智能提取
      extract: (content) => this.autoExtract(content),
      
      // 重要性评分
      score: (content) => this.scoreImportance(content)
    };
  }
  
  /**
   * 保存记忆
   */
  saveMemory(memoryData) {
    try {
      const data = this.loadStorageData();
      const memory = {
        id: `lite_${Date.now()}_${Math.random().toString(36).substr(2, 8)}`,
        content: memoryData.content,
        tags: memoryData.tags || [],
        metadata: memoryData.metadata || {},
        importance: memoryData.importance || this.auto.score(memoryData.content),
        timestamp: Date.now(),
        createdAt: new Date().toISOString()
      };
      
      data.memories.push(memory);
      data.metadata.totalMemories = data.memories.length;
      data.metadata.lastUpdated = new Date().toISOString();
      
      fs.writeFileSync(this.config.storage.path, JSON.stringify(data, null, 2));
      
      console.log('💾 记忆保存成功:', memory.id);
      return { success: true, memory };
    } catch (error) {
      console.error('❌ 记忆保存失败:', error.message);
      
      // 错误恢复：尝试简单存储
      if (this.config.errorHandling.fallbackToSimple) {
        return this.fallbackSave(memoryData);
      }
      
      return { success: false, error: error.message };
    }
  }
  
  /**
   * 降级保存
   */
  fallbackSave(memoryData) {
    const fallbackPath = path.join(__dirname, 'memories-fallback.json');
    const fallbackData = fs.existsSync(fallbackPath) 
      ? JSON.parse(fs.readFileSync(fallbackPath, 'utf8'))
      : { memories: [] };
    
    const memory = {
      id: `fb_${Date.now()}`,
      content: memoryData.content,
      timestamp: Date.now()
    };
    
    fallbackData.memories.push(memory);
    fs.writeFileSync(fallbackPath, JSON.stringify(fallbackData, null, 2));
    
    console.log('🔄 使用降级存储保存记忆');
    return { success: true, memory, fallback: true };
  }
  
  /**
   * 文本搜索
   */
  textSearch(query, options = {}) {
    const data = this.loadStorageData();
    const limit = options.limit || this.config.search.limit;
    const queryLower = query.toLowerCase();
    
    // 简单文本匹配
    const results = data.memories
      .filter(memory => {
        const contentMatch = memory.content.toLowerCase().includes(queryLower);
        const tagMatch = memory.tags.some(tag => 
          tag.toLowerCase().includes(queryLower)
        );
        
        return contentMatch || tagMatch;
      })
      .sort((a, b) => {
        // 按重要性排序
        if (a.importance !== b.importance) {
          return b.importance - a.importance;
        }
        // 按时间排序
        return b.timestamp - a.timestamp;
      })
      .slice(0, limit);
    
    console.log(`🔍 搜索 "${query}"，找到 ${results.length} 条结果`);
    return results;
  }
  
  /**
   * 自动捕获
   */
  async autoCapture(session, messages) {
    if (!this.config.auto.capture) return;
    
    console.log('🎯 自动捕获对话...');
    
    // 提取最后 N 条消息
    const recentMessages = messages.slice(-this.config.auto.contextWindow);
    
    for (const msg of recentMessages) {
      const importance = await this.auto.score(msg.content || msg.text || '');
      
      if (importance >= this.config.auto.importanceThreshold) {
        await this.saveMemory({
          content: msg.content || msg.text,
          tags: ['auto-captured', session.id || 'unknown'],
          metadata: { session, importance },
          importance
        });
      }
    }
    
    console.log('✅ 自动捕获完成');
  }
  
  /**
   * 自动召回
   */
  async autoRecall(query, context = {}) {
    if (!this.config.auto.recall) return [];
    
    console.log('🔍 自动召回相关记忆...');
    
    // 1. 直接搜索
    const directResults = this.textSearch(query, { limit: 5 });
    
    // 2. 上下文增强搜索
    const contextResults = this.searchByContext(context);
    
    // 3. 合并结果
    const allResults = [...directResults, ...contextResults];
    
    // 4. 去重和排序
    const uniqueResults = this.deduplicateResults(allResults);
    
    console.log(`✅ 召回 ${uniqueResults.length} 条相关记忆`);
    return uniqueResults.slice(0, this.config.search.limit);
  }
  
  /**
   * 按上下文搜索
   */
  searchByContext(context) {
    const data = this.loadStorageData();
    const contextKeys = Object.keys(context).filter(key => 
      typeof context[key] === 'string'
    );
    
    if (contextKeys.length === 0) return [];
    
    return data.memories.filter(memory => {
      // 检查记忆元数据中的上下文匹配
      if (memory.metadata.session && memory.metadata.session.id === context.sessionId) {
        return true;
      }
      
      // 检查标签匹配
      if (context.tags && Array.isArray(context.tags)) {
        return context.tags.some(tag => memory.tags.includes(tag));
      }
      
      return false;
    });
  }
  
  /**
   * 加载存储数据
   */
  loadStorageData() {
    try {
      const content = fs.readFileSync(this.config.storage.path, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      console.error('❌ 存储数据加载失败:', error.message);
      return { memories: [], metadata: { totalMemories: 0 } };
    }
  }
  
  /**
   * 获取存储统计
   */
  getStorageStats() {
    const data = this.loadStorageData();
    const tags = new Set();
    
    data.memories.forEach(memory => {
      memory.tags.forEach(tag => tags.add(tag));
    });
    
    return {
      total: data.metadata.totalMemories || data.memories.length,
      tags: tags.size,
      lastUpdated: data.metadata.lastUpdated,
      storageSize: fs.existsSync(this.config.storage.path) 
        ? (fs.statSync(this.config.storage.path).size / 1024).toFixed(2) + 'KB'
        : '0KB'
    };
  }
  
  /**
   * 深度合并对象
   */
  deepMerge(target, source) {
    const result = { ...target };
    
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = this.deepMerge(result[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }
    
    return result;
  }
  
  /**
   * 结果去重
   */
  deduplicateResults(results) {
    const seen = new Set();
    return results.filter(memory => {
      if (seen.has(memory.id)) return false;
      seen.add(memory.id);
      return true;
    });
  }
  
  /**
   * 重要性评分（简单实现）
   */
  scoreImportance(content) {
    // 简单规则：长度、关键词、标点等
    const lengthScore = Math.min(content.length / 100, 1.0);
    const keywordScore = this.hasImportantKeywords(content) ? 0.3 : 0;
    const punctuationScore = this.hasPunctuation(content) ? 0.2 : 0;
    
    return Math.min(lengthScore + keywordScore + punctuationScore, 1.0);
  }
  
  hasImportantKeywords(content) {
    const keywords = ['重要', '关键', '记住', '备忘', 'note', 'important', 'critical'];
    return keywords.some(keyword => content.includes(keyword));
  }
  
  hasPunctuation(content) {
    return /[。！？!?]/.test(content);
  }
  
  /**
   * 获取配置摘要
   */
  getSummary() {
    const stats = this.getStorageStats();
    
    return {
      version: 'Unified Memory Lite v1.0',
      mode: 'lite',
      storage: {
        type: this.config.storage.type,
        path: this.config.storage.path,
        size: stats.storageSize
      },
      memories: {
        total: stats.total,
        tags: stats.tags,
        lastUpdated: stats.lastUpdated
      },
      features: {
        autoCapture: this.config.auto.capture,
        autoRecall: this.config.auto.recall,
        textSearch: true,
        tagSearch: true,
        errorRecovery: this.config.errorHandling.autoRecover
      }
    };
  }
}

// 创建并导出单例
const memoryLite = new UnifiedMemoryLite();

// 立即测试
console.log('\n🧪 立即测试轻量版...');
memoryLite.saveMemory({
  content: 'Unified Memory Lite 测试 - 开箱即用，类似 memory-core-plus 体验',
  tags: ['测试', '轻量版', '用户体验'],
  metadata: { test: true, timestamp: new Date().toISOString() }
});

const searchResults = memoryLite.textSearch('memory-core-plus');
console.log(`搜索测试: 找到 ${searchResults.length} 条结果`);

const stats = memoryLite.getStorageStats();
console.log(`统计: ${stats.total} 条记忆，${stats.tags} 个标签`);

module.exports = memoryLite;