#!/usr/bin/env node

/**
 * 统一检索API
 * 优先搜索Unified Memory，文件系统作为后备
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const __dirname = path.dirname(fileURLToPath(import.meta.url));

class UnifiedQueryAPI {
  constructor(options = {}) {
    this.workspacePath = options.workspacePath || '/root/.openclaw/workspace/memory';
    this.unifiedMemoryPath = options.unifiedMemoryPath || '/root/.openclaw/skills/unified-memory';
    this.cacheSize = options.cacheSize || 100;
    this.cache = new Map();
    this.stats = {
      unifiedHits: 0,
      filesystemFallbacks: 0,
      totalQueries: 0,
      responseTimes: []
    };
  }

  /**
   * 统一查询入口
   */
  async query(query, options = {}) {
    const startTime = Date.now();
    this.stats.totalQueries++;
    
    try {
      // 1. 先查缓存
      const cacheKey = this.generateCacheKey(query, options);
      if (this.cache.has(cacheKey)) {
        const cached = this.cache.get(cacheKey);
        this.stats.responseTimes.push(Date.now() - startTime);
        return {
          ...cached,
          source: 'cache',
          responseTime: Date.now() - startTime
        };
      }

      // 2. 优先搜索Unified Memory
      let results = [];
      let unifiedHit = false;
      
      try {
        const unifiedResults = await this.queryUnifiedMemory(query, options);
        if (unifiedResults && unifiedResults.length > 0) {
          results = unifiedResults;
          unifiedHit = true;
          this.stats.unifiedHits++;
        }
      } catch (error) {
        console.warn('Unified Memory查询失败，回退到文件系统:', error.message);
      }

      // 3. 如果Unified Memory未命中或命中率不足，搜索文件系统
      if (!unifiedHit || (options.requireFallback && results.length < options.minResults)) {
        const filesystemResults = await this.queryFilesystem(query, options);
        results = this.mergeAndDeduplicate(results, filesystemResults);
        this.stats.filesystemFallbacks++;
      }

      // 4. 排序和限制结果
      results = this.sortResults(results, options);
      if (options.limit && results.length > options.limit) {
        results = results.slice(0, options.limit);
      }

      // 5. 准备响应
      const response = {
        success: true,
        query,
        results,
        stats: {
          total: results.length,
          unifiedHit,
          unifiedResults: unifiedHit ? results.filter(r => r.source === 'unified').length : 0,
          filesystemResults: results.filter(r => r.source === 'filesystem').length,
          responseTime: Date.now() - startTime
        },
        metadata: {
          cacheKey,
          timestamp: new Date().toISOString()
        }
      };

      // 6. 缓存结果
      this.cache.set(cacheKey, response);
      this.manageCache();

      this.stats.responseTimes.push(response.stats.responseTime);
      
      return response;
    } catch (error) {
      const responseTime = Date.now() - startTime;
      this.stats.responseTimes.push(responseTime);
      
      return {
        success: false,
        query,
        error: error.message,
        stats: {
          responseTime,
          unifiedHit: false,
          filesystemFallback: false
        },
        results: []
      };
    }
  }

  /**
   * 查询Unified Memory
   */
  async queryUnifiedMemory(query, options = {}) {
    try {
      const cmd = `cd ${this.unifiedMemoryPath} && node -e "
        import('./src/core/enhanced_memory_system.js').then(async (module) => {
          const memorySystem = module.default || module;
          const results = await memorySystem.searchMemories({
            query: ${JSON.stringify(query)},
            limit: ${options.limit || 10},
            filters: ${JSON.stringify(options.filters || {})},
            searchMode: ${JSON.stringify(options.searchMode || 'hybrid')}
          });
          console.log(JSON.stringify(results));
        }).catch(err => {
          console.error(JSON.stringify({ error: err.message }));
        });
      "`;
      
      const { stdout, stderr } = await execAsync(cmd);
      
      if (stderr && !stderr.includes('ExperimentalWarning')) {
        throw new Error(`Unified Memory查询错误: ${stderr}`);
      }
      
      const parsed = JSON.parse(stdout.trim());
      
      if (parsed.error) {
        throw new Error(parsed.error);
      }
      
      // 转换结果为统一格式
      return parsed.map(result => ({
        ...result,
        source: 'unified',
        score: result.relevance || result.score || 0,
        content: result.content || result.text || '',
        metadata: {
          ...result.metadata,
          type: result.type,
          timestamp: result.timestamp || result.created_at
        }
      }));
    } catch (error) {
      console.error('Unified Memory查询失败:', error);
      return [];
    }
  }

  /**
   * 查询文件系统
   */
  async queryFilesystem(query, options = {}) {
    const results = [];
    
    try {
      // 获取所有.md文件
      const files = await fs.readdir(this.workspacePath);
      const mdFiles = files.filter(f => f.endsWith('.md'));
      
      // 对每个文件进行搜索
      for (const file of mdFiles) {
        const filePath = path.join(this.workspacePath, file);
        
        try {
          const content = await fs.readFile(filePath, 'utf8');
          const lines = content.split('\n');
          
          // 简单的文本搜索
          for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            if (this.matchesQuery(line, query)) {
              // 获取上下文（前后3行）
              const start = Math.max(0, i - 3);
              const end = Math.min(lines.length, i + 4);
              const context = lines.slice(start, end).join('\n');
              
              results.push({
                content: context,
                source: 'filesystem',
                score: this.calculateRelevance(line, query),
                metadata: {
                  file,
                  line: i + 1,
                  contextLines: `${start+1}-${end}`,
                  timestamp: await this.getFileTimestamp(filePath)
                }
              });
              
              // 如果达到限制，提前返回
              if (options.limit && results.length >= options.limit * 2) {
                break;
              }
            }
          }
        } catch (fileError) {
          console.warn(`读取文件 ${file} 失败:`, fileError.message);
        }
      }
    } catch (error) {
      console.error('文件系统查询失败:', error);
    }
    
    return results;
  }

  /**
   * 检查行是否匹配查询
   */
  matchesQuery(line, query) {
    const lineLower = line.toLowerCase();
    const queryLower = query.toLowerCase();
    
    // 简单包含检查
    if (lineLower.includes(queryLower)) {
      return true;
    }
    
    // 分词检查（简单版本）
    const queryWords = queryLower.split(/\s+/).filter(w => w.length > 2);
    if (queryWords.length === 0) return false;
    
    const matchCount = queryWords.filter(word => lineLower.includes(word)).length;
    return matchCount >= Math.ceil(queryWords.length / 2);
  }

  /**
   * 计算相关性分数
   */
  calculateRelevance(line, query) {
    let score = 0;
    const lineLower = line.toLowerCase();
    const queryLower = query.toLowerCase();
    
    // 完全匹配加分
    if (lineLower === queryLower) score += 1.0;
    
    // 包含所有查询词
    const queryWords = queryLower.split(/\s+/).filter(w => w.length > 0);
    const matchedWords = queryWords.filter(word => lineLower.includes(word));
    score += (matchedWords.length / queryWords.length) * 0.8;
    
    // 位置权重（标题行更重要）
    if (line.startsWith('#') || line.startsWith('##')) {
      score += 0.5;
    }
    
    // 长度权重（适中长度更好）
    const length = line.length;
    if (length > 20 && length < 200) {
      score += 0.3;
    }
    
    return Math.min(score, 1.0);
  }

  /**
   * 获取文件时间戳
   */
  async getFileTimestamp(filePath) {
    try {
      const stats = await fs.stat(filePath);
      return stats.mtime.toISOString();
    } catch (error) {
      return new Date().toISOString();
    }
  }

  /**
   * 合并和去重结果
   */
  mergeAndDeduplicate(unifiedResults, filesystemResults) {
    const allResults = [...unifiedResults, ...filesystemResults];
    const seen = new Set();
    const deduplicated = [];
    
    for (const result of allResults) {
      // 基于内容生成唯一标识
      const contentKey = result.content.substring(0, 200).toLowerCase().replace(/\s+/g, ' ');
      
      if (!seen.has(contentKey)) {
        seen.add(contentKey);
        deduplicated.push(result);
      }
    }
    
    return deduplicated;
  }

  /**
   * 排序结果
   */
  sortResults(results, options) {
    const sortBy = options.sortBy || 'score';
    const order = options.order || 'desc';
    
    return results.sort((a, b) => {
      let valueA, valueB;
      
      switch (sortBy) {
        case 'score':
          valueA = a.score || 0;
          valueB = b.score || 0;
          break;
        case 'timestamp':
          valueA = new Date(a.metadata?.timestamp || 0).getTime();
          valueB = new Date(b.metadata?.timestamp || 0).getTime();
          break;
        case 'relevance':
        default:
          valueA = a.score || 0;
          valueB = b.score || 0;
      }
      
      return order === 'desc' ? valueB - valueA : valueA - valueB;
    });
  }

  /**
   * 生成缓存键
   */
  generateCacheKey(query, options) {
    const keyParts = [
      query,
      options.limit,
      options.sortBy,
      options.order,
      JSON.stringify(options.filters || {})
    ];
    
    return keyParts.join('|').toLowerCase();
  }

  /**
   * 管理缓存大小
   */
  manageCache() {
    if (this.cache.size > this.cacheSize) {
      // 移除最旧的条目
      const keys = Array.from(this.cache.keys());
      const keysToRemove = keys.slice(0, this.cache.size - this.cacheSize);
      
      for (const key of keysToRemove) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * 获取统计信息
   */
  getStats() {
    const responseTimes = this.stats.responseTimes;
    const avgResponseTime = responseTimes.length > 0 
      ? responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length 
      : 0;
    
    const hitRate = this.stats.totalQueries > 0
      ? (this.stats.unifiedHits / this.stats.totalQueries) * 100
      : 0;
    
    const fallbackRate = this.stats.totalQueries > 0
      ? (this.stats.filesystemFallbacks / this.stats.totalQueries) * 100
      : 0;
    
    return {
      queries: {
        total: this.stats.totalQueries,
        unifiedHits: this.stats.unifiedHits,
        filesystemFallbacks: this.stats.filesystemFallbacks,
        hitRate: hitRate.toFixed(2) + '%',
        fallbackRate: fallbackRate.toFixed(2) + '%'
      },
      performance: {
        avgResponseTime: avgResponseTime.toFixed(2) + 'ms',
        minResponseTime: responseTimes.length > 0 ? Math.min(...responseTimes) + 'ms' : 'N/A',
        maxResponseTime: responseTimes.length > 0 ? Math.max(...responseTimes) + 'ms' : 'N/A',
        cacheSize: this.cache.size,
        cacheHitRate: 'N/A' // 需要跟踪缓存命中
      },
      timestamp: new Date().toISOString()
    };
  }

  /**
   * 清空缓存
   */
  clearCache() {
    this.cache.clear();
    return { success: true, message: '缓存已清空' };
  }
}

// REST API服务器（可选）
class QueryServer {
  constructor(port = 3851) {
    this.port = port;
    this.queryAPI = new UnifiedQueryAPI();
  }

  async start() {
    // 这里可以扩展为真正的HTTP服务器
    console.log(`🚀 统一检索API已启动`);
    console.log(`📊 统计信息:`, this.queryAPI.getStats());
    console.log(`💡 使用 queryAPI.query('关键词') 进行查询`);
  }
}

// CLI支持
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const queryAPI = new UnifiedQueryAPI();
  
  if (args[0] === '--server') {
    const port = parseInt(args[1]) || 3851;
    const server = new QueryServer(port);
    server.start().catch(console.error);
  } else if (args[0] === '--stats') {
    console.log(JSON.stringify(queryAPI.getStats(), null, 2));
  } else if (args[0] === '--clear-cache') {
    console.log(JSON.stringify(queryAPI.clearCache(), null, 2));
  } else if (args.length > 0) {
    // 执行查询
    const query = args.join(' ');
    queryAPI.query(query, { limit: 10 })
      .then(result => console.log(JSON.stringify(result, null, 2)))
      .catch(error => console.error('查询失败:', error));
  } else {
    console.log('使用方法:');
    console.log('  node unified_query_api.js <查询词>');
    console.log('  node unified_query_api.js --server [端口]');
    console.log('  node unified_query_api.js --stats');
    console.log('  node unified_query_api.js --clear-cache');
  }
}

export default UnifiedQueryAPI;