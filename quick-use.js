/**
 * Unified Memory 快速使用包装器
 * 直接使用现有核心功能，避免复杂依赖
 */

const fs = require('fs');
const path = require('path');

// 简单记忆存储（基于 JSON 文件）
class QuickMemory {
  constructor() {
    this.filePath = path.join(__dirname, 'quick-memories.json');
    this.memories = this.load();
  }
  
  load() {
    try {
      if (fs.existsSync(this.filePath)) {
        return JSON.parse(fs.readFileSync(this.filePath, 'utf8'));
      }
    } catch (e) {
      console.warn('加载记忆失败:', e.message);
    }
    return [];
  }
  
  save() {
    try {
      fs.writeFileSync(this.filePath, JSON.stringify(this.memories, null, 2));
      return true;
    } catch (e) {
      console.error('保存记忆失败:', e.message);
      return false;
    }
  }
  
  add(content, tags = [], metadata = {}) {
    const memory = {
      id: `qm_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      content,
      tags: Array.isArray(tags) ? tags : [tags],
      metadata,
      timestamp: Date.now(),
      createdAt: new Date().toISOString()
    };
    
    this.memories.push(memory);
    this.save();
    return memory;
  }
  
  search(query, options = {}) {
    const { limit = 5, tag } = options;
    const queryLower = query.toLowerCase();
    
    let results = this.memories.filter(m => 
      m.content.toLowerCase().includes(queryLower)
    );
    
    if (tag) {
      results = results.filter(m => m.tags.includes(tag));
    }
    
    return results
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit);
  }
  
  findByTag(tag) {
    return this.memories
      .filter(m => m.tags.includes(tag))
      .sort((a, b) => b.timestamp - a.timestamp);
  }
  
  getRecent(limit = 10) {
    return this.memories
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit);
  }
  
  stats() {
    const tags = new Set();
    this.memories.forEach(m => m.tags.forEach(t => tags.add(t)));
    
    return {
      total: this.memories.length,
      tags: tags.size,
      lastUpdated: this.memories.length > 0 ? 
        new Date(this.memories[this.memories.length - 1].timestamp).toLocaleString() : '从未'
    };
  }
}

// 创建单例并立即使用
const memory = new QuickMemory();

// 记录当前会话
memory.add(
  '刘选权询问 unified-memory 与 memory-core-plus 对比，决定并行进行',
  ['用户咨询', '系统对比', '刘选权', '并行执行'],
  { session: '2026-04-20', importance: 'high' }
);

memory.add(
  '发现 Python MCP 依赖问题，采用简化方案直接使用 Node.js 核心',
  ['技术问题', '简化方案', 'Node.js'],
  { session: '2026-04-20', issue: 'python-dependency' }
);

// 导出实例和方法
const quickMemory = memory;

// 导出方法
module.exports = {
  // 实例
  memory: quickMemory,
  
  // 快捷方法
  add: (content, tags, metadata) => quickMemory.add(content, tags, metadata),
  search: (query, options) => quickMemory.search(query, options),
  findByTag: (tag) => quickMemory.findByTag(tag),
  getRecent: (limit) => quickMemory.getRecent(limit),
  stats: () => quickMemory.stats()
};