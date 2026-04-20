// unified-memory 零配置启动模板
// 基于务实方案：立即可用，无需复杂配置

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * 零配置记忆系统
 * 特点：
 * 1. 零依赖：纯 Node.js，无需 Python
 * 2. 零配置：默认值即可用
 * 3. 立即可用：无需复杂设置
 */
class ZeroConfigMemory {
  constructor(options = {}) {
    // 默认配置
    this.config = {
      storagePath: options.storagePath || path.join(__dirname, 'memory'),
      memoryFile: options.memoryFile || 'memories.json',
      cacheSize: options.cacheSize || 1000,
      searchWeights: options.searchWeights || { bm25: 0.4, vector: 0.4, rrf: 0.2 },
      autoSave: options.autoSave !== false,
      ...options
    };
    
    // 初始化
    this.memories = [];
    this.cache = new Map();
    this.init();
  }
  
  init() {
    // 创建存储目录
    if (!fs.existsSync(this.config.storagePath)) {
      fs.mkdirSync(this.config.storagePath, { recursive: true });
    }
    
    // 加载现有记忆
    const filePath = path.join(this.config.storagePath, this.config.memoryFile);
    if (fs.existsSync(filePath)) {
      try {
        const content = fs.readFileSync(filePath, 'utf8');
        this.memories = JSON.parse(content);
        console.log(`📁 加载 ${this.memories.length} 条记忆`);
      } catch (error) {
        console.warn('❌ 加载记忆失败，创建新文件:', error.message);
        this.memories = [];
      }
    }
  }
  
  /**
   * 添加记忆
   */
  add(content, tags = [], category = 'general', metadata = {}) {
    const memory = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      content,
      tags: Array.isArray(tags) ? tags : [tags],
      category,
      timestamp: new Date().toISOString(),
      priority: metadata.priority || 'normal',
      source: metadata.source || 'zero-config',
      ...metadata
    };
    
    this.memories.push(memory);
    
    // 自动保存
    if (this.config.autoSave) {
      this.save();
    }
    
    // 更新缓存
    this.updateCache(memory);
    
    return memory;
  }
  
  /**
   * 搜索记忆
   */
  search(query, options = {}) {
    const {
      limit = 10,
      category = null,
      tags = [],
      minDate = null,
      maxDate = null
    } = options;
    
    // 1. 检查缓存
    const cacheKey = `search:${query}:${limit}:${category}`;
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }
    
    // 2. 基础关键词搜索（简化版 BM25）
    let results = this.memories.filter(memory => {
      // 内容匹配
      const contentMatch = memory.content.toLowerCase().includes(query.toLowerCase());
      
      // 标签匹配
      const tagMatch = tags.length === 0 || 
        tags.some(tag => memory.tags.includes(tag));
      
      // 分类匹配
      const categoryMatch = !category || memory.category === category;
      
      // 时间范围匹配
      const timeMatch = (!minDate || new Date(memory.timestamp) >= new Date(minDate)) &&
                       (!maxDate || new Date(memory.timestamp) <= new Date(maxDate));
      
      return contentMatch && tagMatch && categoryMatch && timeMatch;
    });
    
    // 3. 简单相关性评分
    results = results.map(memory => {
      let score = 0;
      
      // 内容匹配度
      const contentLower = memory.content.toLowerCase();
      const queryLower = query.toLowerCase();
      
      if (contentLower.includes(queryLower)) {
        score += 10;
        
        // 完全匹配加分
        if (memory.content === query) {
          score += 20;
        }
        
        // 开头匹配加分
        if (contentLower.startsWith(queryLower)) {
          score += 15;
        }
      }
      
      // 标签匹配加分
      const matchingTags = memory.tags.filter(tag => 
        tag.toLowerCase().includes(queryLower)
      );
      score += matchingTags.length * 5;
      
      // 时间新鲜度（最近的内容加分）
      const ageDays = (Date.now() - new Date(memory.timestamp).getTime()) / (1000 * 60 * 60 * 24);
      score += Math.max(0, 10 - ageDays); // 10天内每天减1分
      
      // 优先级加分
      if (memory.priority === 'high') score += 10;
      if (memory.priority === 'critical') score += 20;
      
      return { ...memory, score };
    });
    
    // 4. 按分数排序
    results.sort((a, b) => b.score - a.score);
    
    // 5. 限制结果数量
    results = results.slice(0, limit);
    
    // 6. 缓存结果
    this.cache.set(cacheKey, results);
    
    return results;
  }
  
  /**
   * 获取记忆统计
   */
  stats() {
    const tagCount = new Set();
    const categoryCount = {};
    let totalSize = 0;
    
    this.memories.forEach(memory => {
      memory.tags.forEach(tag => tagCount.add(tag));
      categoryCount[memory.category] = (categoryCount[memory.category] || 0) + 1;
      
      // 估算大小
      totalSize += JSON.stringify(memory).length;
    });
    
    return {
      totalMemories: this.memories.length,
      totalTags: tagCount.size,
      categories: categoryCount,
      estimatedSize: totalSize,
      latest: this.memories.length > 0 ? this.memories[this.memories.length - 1].timestamp : null,
      cacheSize: this.cache.size
    };
  }
  
  /**
   * 按标签搜索
   */
  searchByTag(tag, limit = 20) {
    return this.memories
      .filter(memory => memory.tags.includes(tag))
      .slice(0, limit);
  }
  
  /**
   * 按分类搜索
   */
  searchByCategory(category, limit = 20) {
    return this.memories
      .filter(memory => memory.category === category)
      .slice(0, limit);
  }
  
  /**
   * 获取最近记忆
   */
  getRecent(limit = 10) {
    return [...this.memories]
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, limit);
  }
  
  /**
   * 更新缓存
   */
  updateCache(memory) {
    // 清除相关的搜索缓存
    const keysToDelete = [];
    this.cache.forEach((value, key) => {
      if (key.startsWith('search:')) {
        keysToDelete.push(key);
      }
    });
    
    keysToDelete.forEach(key => this.cache.delete(key));
  }
  
  /**
   * 保存到文件
   */
  save() {
    const filePath = path.join(this.config.storagePath, this.config.memoryFile);
    try {
      fs.writeFileSync(filePath, JSON.stringify(this.memories, null, 2));
      return true;
    } catch (error) {
      console.error('❌ 保存失败:', error.message);
      return false;
    }
  }
  
  /**
   * 导出记忆
   */
  export(format = 'json') {
    if (format === 'json') {
      return JSON.stringify(this.memories, null, 2);
    } else if (format === 'csv') {
      // 简化的 CSV 导出
      const headers = ['id', 'content', 'tags', 'category', 'timestamp', 'priority'];
      const rows = this.memories.map(memory => [
        memory.id,
        `"${memory.content.replace(/"/g, '""')}"`,
        `"${memory.tags.join(',')}"`,
        memory.category,
        memory.timestamp,
        memory.priority
      ]);
      
      return [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
    }
    
    return null;
  }
  
  /**
   * 清空缓存
   */
  clearCache() {
    this.cache.clear();
  }
  
  /**
   * 备份记忆
   */
  backup(backupPath = null) {
    const backupDir = backupPath || path.join(this.config.storagePath, 'backups');
    if (!fs.existsSync(backupDir)) {
      fs.mkdirSync(backupDir, { recursive: true });
    }
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupFile = path.join(backupDir, `memories-backup-${timestamp}.json`);
    
    fs.writeFileSync(backupFile, JSON.stringify(this.memories, null, 2));
    return backupFile;
  }
}

// 导出零配置记忆系统
export default ZeroConfigMemory;

// 如果直接运行，创建实例并测试
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('🚀 测试零配置记忆系统...\n');
  
  const memory = new ZeroConfigMemory();
  
  // 测试添加
  const testMemory = memory.add(
    '测试零配置记忆系统：立即可用，无需复杂配置',
    ['测试', '零配置', 'unified-memory'],
    '测试分类',
    { priority: 'high', source: 'zero-config-test' }
  );
  
  console.log('✅ 添加测试记忆:', testMemory.content);
  
  // 测试搜索
  const results = memory.search('零配置');
  console.log('🔍 搜索"零配置"结果:', results.length, '条');
  
  // 测试统计
  const stats = memory.stats();
  console.log('📊 系统统计:');
  console.log('   总记忆:', stats.totalMemories);
  console.log('   总标签:', stats.totalTags);
  console.log('   缓存大小:', stats.cacheSize);
  
  console.log('\n🎯 零配置记忆系统测试完成！');
  console.log('🚀 立即可用，无需复杂配置。');
}