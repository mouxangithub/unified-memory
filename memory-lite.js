// Unified Memory 极简版 - 立即可用
const fs = require('fs');
const path = require('path');

// 单例实例
let instance = null;

class MemoryLite {
  constructor() {
    if (instance) return instance;
    
    this.storagePath = path.join(__dirname, 'storage', 'memories.json');
    this.ensureStorage();
    this.memories = this.loadMemories();
    
    instance = this;
  }
  
  ensureStorage() {
    const dir = path.dirname(this.storagePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    if (!fs.existsSync(this.storagePath)) {
      fs.writeFileSync(this.storagePath, '[]');
    }
  }
  
  loadMemories() {
    try {
      return JSON.parse(fs.readFileSync(this.storagePath, 'utf8'));
    } catch {
      return [];
    }
  }
  
  saveMemories() {
    fs.writeFileSync(this.storagePath, JSON.stringify(this.memories, null, 2));
  }
  
  store(content, tags = [], context = {}) {
    const memory = {
      id: `mem_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      content,
      tags: Array.isArray(tags) ? tags : [tags],
      context,
      timestamp: Date.now()
    };
    
    this.memories.push(memory);
    this.saveMemories();
    return memory;
  }
  
  search(query, options = {}) {
    const { limit = 10 } = options;
    const queryLower = query.toLowerCase();
    
    return this.memories
      .filter(m => m.content.toLowerCase().includes(queryLower))
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit);
  }
  
  searchByTag(tag) {
    return this.memories
      .filter(m => m.tags.includes(tag))
      .sort((a, b) => b.timestamp - a.timestamp);
  }
  
  getRecent(limit = 5) {
    return this.memories
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit);
  }
  
  getStats() {
    const tags = new Set();
    this.memories.forEach(m => m.tags.forEach(t => tags.add(t)));
    
    return {
      total: this.memories.length,
      uniqueTags: tags.size,
      oldest: this.memories[0] ? new Date(this.memories[0].timestamp).toISOString() : null,
      newest: this.memories.length > 0 ? 
        new Date(this.memories[this.memories.length - 1].timestamp).toISOString() : null
    };
  }
}

// 创建并导出单例
const memory = new MemoryLite();

// 导出快捷方法
module.exports = {
  MemoryLite,
  memory,
  
  // 快捷方法
  store: (content, tags, context) => memory.store(content, tags, context),
  search: (query, options) => memory.search(query, options),
  searchByTag: (tag) => memory.searchByTag(tag),
  getRecent: (limit) => memory.getRecent(limit),
  getStats: () => memory.getStats()
};