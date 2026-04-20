/**
 * Unified Memory 简化版
 * 专注于核心功能，避免复杂依赖
 */

const fs = require('fs');
const path = require('path');

class SimpleMemory {
  constructor(options = {}) {
    this.storagePath = options.storagePath || path.join(__dirname, 'storage', 'memories.json');
    this.ensureStorage();
    this.memories = this.loadMemories();
  }

  ensureStorage() {
    const dir = path.dirname(this.storagePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    if (!fs.existsSync(this.storagePath)) {
      fs.writeFileSync(this.storagePath, JSON.stringify([], null, 2));
    }
  }

  loadMemories() {
    try {
      const content = fs.readFileSync(this.storagePath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      console.warn('加载记忆失败，使用空数组:', error.message);
      return [];
    }
  }

  saveMemories() {
    try {
      fs.writeFileSync(this.storagePath, JSON.stringify(this.memories, null, 2));
      return true;
    } catch (error) {
      console.error('保存记忆失败:', error.message);
      return false;
    }
  }

  /**
   * 存储记忆
   */
  store(memory) {
    const memoryWithMeta = {
      id: `mem_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      content: memory.content,
      tags: memory.tags || [],
      context: memory.context || {},
      timestamp: Date.now(),
      ...memory
    };

    this.memories.push(memoryWithMeta);
    this.saveMemories();
    return memoryWithMeta;
  }

  /**
   * 搜索记忆
   */
  search(query, options = {}) {
    const { limit = 10, tags = [] } = options;
    
    return this.memories
      .filter(memory => {
        // 内容匹配
        const contentMatch = memory.content.toLowerCase().includes(query.toLowerCase());
        
        // 标签匹配
        const tagMatch = tags.length === 0 || 
          tags.some(tag => memory.tags.includes(tag));
        
        return contentMatch && tagMatch;
      })
      .sort((a, b) => b.timestamp - a.timestamp) // 最新优先
      .slice(0, limit);
  }

  /**
   * 按标签搜索
   */
  searchByTag(tag) {
    return this.memories
      .filter(memory => memory.tags.includes(tag))
      .sort((a, b) => b.timestamp - a.timestamp);
  }

  /**
   * 获取最近记忆
   */
  getRecent(limit = 5) {
    return this.memories
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit);
  }

  /**
   * 统计信息
   */
  getStats() {
    const tags = new Set();
    this.memories.forEach(memory => {
      memory.tags.forEach(tag => tags.add(tag));
    });

    return {
      total: this.memories.length,
      uniqueTags: tags.size,
      oldest: this.memories.length > 0 ? 
        new Date(Math.min(...this.memories.map(m => m.timestamp))).toISOString() : null,
      newest: this.memories.length > 0 ? 
        new Date(Math.max(...this.memories.map(m => m.timestamp))).toISOString() : null
    };
  }
}

// 创建并导出单例
const memoryInstance = new SimpleMemory();

// 快捷方法
const store = (content, tags = [], context = {}) => 
  memoryInstance.store({ content, tags, context });

const search = (query, options) => memoryInstance.search(query, options);

const searchByTag = (tag) => memoryInstance.searchByTag(tag);

const getRecent = (limit) => memoryInstance.getRecent(limit);

const getStats = () => memoryInstance.getStats();

// 导出
module.exports.SimpleMemory = SimpleMemory;
module.exports.memory = memoryInstance;
module.exports.store = store;
module.exports.search = search;
module.exports.searchByTag = searchByTag;
module.exports.getRecent = getRecent;
module.exports.getStats = getStats;