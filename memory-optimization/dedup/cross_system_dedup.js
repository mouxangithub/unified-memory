#!/usr/bin/env node

/**
 * 跨系统去重增强模块
 * 扩展Unified Memory的去重功能，支持跨系统去重检查
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const __dirname = path.dirname(fileURLToPath(import.meta.url));

class CrossSystemDeduplicator {
  constructor(options = {}) {
    this.workspacePath = options.workspacePath || '/root/.openclaw/workspace/memory';
    this.unifiedMemoryPath = options.unifiedMemoryPath || '/root/.openclaw/skills/unified-memory';
    this.similarityThreshold = options.similarityThreshold || 0.85; // 语义相似度阈值
    this.exactMatchThreshold = options.exactMatchThreshold || 0.95; // 精确匹配阈值
    this.cacheSize = options.cacheSize || 1000;
    this.cache = new Map();
    this.stats = {
      totalChecks: 0,
      duplicatesFound: 0,
      crossSystemDuplicates: 0,
      responseTimes: []
    };
  }

  /**
   * 检查记忆是否重复（跨系统）
   */
  async checkDuplicate(memory, options = {}) {
    const startTime = Date.now();
    this.stats.totalChecks++;
    
    try {
      const {
        sources = ['unified_memory', 'workspace_filesystem'],
        crossSystemDedup = true,
        similarityThreshold = this.similarityThreshold
      } = options;

      // 1. 生成记忆指纹
      const fingerprint = this.generateFingerprint(memory);
      
      // 2. 检查缓存
      const cacheKey = `${fingerprint}|${sources.join(',')}`;
      if (this.cache.has(cacheKey)) {
        const cached = this.cache.get(cacheKey);
        this.stats.responseTimes.push(Date.now() - startTime);
        return {
          ...cached,
          source: 'cache',
          responseTime: Date.now() - startTime
        };
      }

      // 3. 执行去重检查
      const results = {
        isDuplicate: false,
        duplicateOf: null,
        similarity: 0,
        sourcesChecked: [],
        details: []
      };

      // 4. 检查Unified Memory
      if (sources.includes('unified_memory')) {
        const unifiedResult = await this.checkUnifiedMemory(memory, similarityThreshold);
        results.sourcesChecked.push('unified_memory');
        
        if (unifiedResult.isDuplicate) {
          results.isDuplicate = true;
          results.duplicateOf = unifiedResult.duplicateOf;
          results.similarity = unifiedResult.similarity;
          results.details.push({
            source: 'unified_memory',
            duplicateId: unifiedResult.duplicateId,
            similarity: unifiedResult.similarity
          });
          this.stats.duplicatesFound++;
        }
      }

      // 5. 检查Workspace文件系统（跨系统去重）
      if (crossSystemDedup && sources.includes('workspace_filesystem')) {
        const filesystemResult = await this.checkWorkspaceFilesystem(memory, similarityThreshold);
        results.sourcesChecked.push('workspace_filesystem');
        
        if (filesystemResult.isDuplicate) {
          results.isDuplicate = true;
          if (!results.duplicateOf) {
            results.duplicateOf = filesystemResult.duplicateOf;
          }
          results.similarity = Math.max(results.similarity, filesystemResult.similarity);
          results.details.push({
            source: 'workspace_filesystem',
            duplicateFile: filesystemResult.duplicateFile,
            duplicateLine: filesystemResult.duplicateLine,
            similarity: filesystemResult.similarity
          });
          this.stats.duplicatesFound++;
          this.stats.crossSystemDuplicates++;
        }
      }

      // 6. 准备响应
      const response = {
        ...results,
        fingerprint,
        memoryType: memory.type,
        contentPreview: memory.content.substring(0, 100),
        responseTime: Date.now() - startTime,
        timestamp: new Date().toISOString()
      };

      // 7. 缓存结果
      this.cache.set(cacheKey, response);
      this.manageCache();

      this.stats.responseTimes.push(response.responseTime);
      
      return response;
    } catch (error) {
      const responseTime = Date.now() - startTime;
      this.stats.responseTimes.push(responseTime);
      
      return {
        isDuplicate: false,
        error: error.message,
        responseTime,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * 生成记忆指纹
   */
  generateFingerprint(memory) {
    const content = memory.content || '';
    
    // 1. 提取关键特征
    const features = {
      // 文本特征
      length: content.length,
      wordCount: content.split(/\s+/).length,
      lineCount: content.split('\n').length,
      
      // 语义特征（简化版）
      keywords: this.extractKeywords(content),
      
      // 结构特征
      hasDates: /\d{4}[-/]\d{1,2}[-/]\d{1,2}/.test(content),
      hasNumbers: /\d+/.test(content),
      hasUrls: /https?:\/\/\S+/.test(content),
      
      // 类型特征
      type: memory.type || 'unknown'
    };
    
    // 2. 生成指纹哈希
    const fingerprintStr = JSON.stringify(features);
    return this.simpleHash(fingerprintStr);
  }

  /**
   * 提取关键词
   */
  extractKeywords(text, maxKeywords = 10) {
    // 移除常见停用词
    const stopWords = new Set([
      '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'
    ]);
    
    // 分词（简化版）
    const words = text
      .toLowerCase()
      .replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 1 && !stopWords.has(word));
    
    // 统计词频
    const freq = {};
    words.forEach(word => {
      freq[word] = (freq[word] || 0) + 1;
    });
    
    // 按频率排序并取前N个
    return Object.entries(freq)
      .sort((a, b) => b[1] - a[1])
      .slice(0, maxKeywords)
      .map(([word]) => word);
  }

  /**
   * 简单哈希函数
   */
  simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // 转换为32位整数
    }
    return hash.toString(36);
  }

  /**
   * 检查Unified Memory中的重复
   */
  async checkUnifiedMemory(memory, similarityThreshold) {
    try {
      const cmd = `cd ${this.unifiedMemoryPath} && node -e "
        import('./src/core/smart_deduplicator.js').then(async (module) => {
          const deduplicator = module.default || module;
          const result = await deduplicator.checkDuplicate({
            content: ${JSON.stringify(memory.content)},
            source: ${JSON.stringify(memory.source)},
            type: ${JSON.stringify(memory.type)}
          }, {
            similarityThreshold: ${similarityThreshold},
            exactMatchThreshold: ${this.exactMatchThreshold}
          });
          console.log(JSON.stringify(result));
        }).catch(err => {
          console.error(JSON.stringify({ error: err.message }));
        });
      "`;
      
      const { stdout, stderr } = await execAsync(cmd);
      
      if (stderr && !stderr.includes('ExperimentalWarning')) {
        throw new Error(`Unified Memory去重检查错误: ${stderr}`);
      }
      
      const result = JSON.parse(stdout.trim());
      
      if (result.error) {
        throw new Error(result.error);
      }
      
      return {
        isDuplicate: result.isDuplicate || false,
        duplicateId: result.duplicateId,
        duplicateOf: result.duplicateOf,
        similarity: result.similarity || 0
      };
    } catch (error) {
      console.warn('Unified Memory去重检查失败:', error.message);
      return {
        isDuplicate: false,
        similarity: 0
      };
    }
  }

  /**
   * 检查Workspace文件系统中的重复
   */
  async checkWorkspaceFilesystem(memory, similarityThreshold) {
    const results = {
      isDuplicate: false,
      duplicateFile: null,
      duplicateLine: null,
      similarity: 0,
      content: null
    };
    
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
          
          // 检查每一行
          for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line.length < 10) continue; // 跳过过短的行
            
            const similarity = this.calculateSimilarity(memory.content, line);
            
            if (similarity >= similarityThreshold) {
              results.isDuplicate = true;
              results.duplicateFile = file;
              results.duplicateLine = i + 1;
              results.similarity = similarity;
              results.content = line;
              
              // 找到高度相似的重复，立即返回
              if (similarity >= this.exactMatchThreshold) {
                return results;
              }
            }
          }
        } catch (fileError) {
          console.warn(`检查文件 ${file} 时出错:`, fileError.message);
        }
      }
    } catch (error) {
      console.error('文件系统去重检查失败:', error);
    }
    
    return results;
  }

  /**
   * 计算文本相似度（简化版）
   */
  calculateSimilarity(text1, text2) {
    if (!text1 || !text2) return 0;
    
    // 1. 精确匹配检查
    if (text1 === text2) return 1.0;
    
    // 2. 包含关系检查
    const longer = text1.length > text2.length ? text1 : text2;
    const shorter = text1.length > text2.length ? text2 : text1;
    
    if (longer.includes(shorter) && shorter.length > 20) {
      return 0.9;
    }
    
    // 3. 基于词重叠的相似度
    const words1 = new Set(this.tokenize(text1));
    const words2 = new Set(this.tokenize(text2));
    
    if (words1.size === 0 || words2.size === 0) return 0;
    
    const intersection = new Set([...words1].filter(x => words2.has(x)));
    const union = new Set([...words1, ...words2]);
    
    const jaccard = intersection.size / union.size;
    
    // 4. 基于长度的相似度
    const lengthRatio = 1 - Math.abs(text1.length - text2.length) / Math.max(text1.length, text2.length);
    
    // 5. 综合评分
    return (jaccard * 0.6) + (lengthRatio * 0.4);
  }

  /**
   * 分词
   */
  tokenize(text) {
    return text
      .toLowerCase()
      .replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 1);
  }

  /**
   * 管理缓存
   */
  manageCache() {
    if (this.cache.size > this.cacheSize) {
      const keys = Array.from(this.cache.keys());
      const keysToRemove = keys.slice(0, this.cache.size - Math.floor(this.cacheSize * 0.8));
      
      for (const key of keysToRemove) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * 批量检查重复
   */
  async batchCheckDuplicates(memories, options = {}) {
    const results = [];
    const batchSize = options.batchSize || 10;
    
    for (let i = 0; i < memories.length; i += batchSize) {
      const batch = memories.slice(i, i + batchSize);
      const batchPromises = batch.map(memory => this.checkDuplicate(memory, options));
      
      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);
      
      // 进度显示
      if (options.progressCallback) {
        options.progressCallback(i + batch.length, memories.length);
      }
    }
    
    return results;
  }

  /**
   * 获取统计信息
   */
  getStats() {
    const responseTimes = this.stats.responseTimes;
    const avgResponseTime = responseTimes.length > 0 
      ? responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length 
      : 0;
    
    const duplicateRate = this.stats.totalChecks > 0
      ? (this.stats.duplicatesFound / this.stats.totalChecks) * 100
      : 0;
    
    const crossSystemRate = this.stats.duplicatesFound > 0
      ? (this.stats.crossSystemDuplicates / this.stats.duplicatesFound) * 100
      : 0;
    
    return {
      checks: {
        total: this.stats.totalChecks,
        duplicatesFound: this.stats.duplicatesFound,
        crossSystemDuplicates: this.stats.crossSystemDuplicates,
        duplicateRate: duplicateRate.toFixed(2) + '%',
        crossSystemRate: crossSystemRate.toFixed(2) + '%'
      },
      performance: {
        avgResponseTime: avgResponseTime.toFixed(2) + 'ms',
        cacheSize: this.cache.size,
        cacheHitRate: 'N/A'
      },
      thresholds: {
        similarity: this.similarityThreshold,
        exactMatch: this.exactMatchThreshold
      },
      timestamp: new Date().toISOString()
    };
  }

  /**
   * 清空缓存
   */
  clearCache() {
    this.cache.clear();
    return { success: true, message: '去重缓存已清空' };
  }

  /**
   * 导出重复分析报告
   */
  async exportDuplicateReport(outputPath) {
    const report = {
      summary: this.getStats(),
      duplicates: [],
      recommendations: []
    };
    
    // 这里可以扩展为导出详细的重复分析
    // 目前只导出统计信息
    
    if (outputPath) {
      await fs.writeFile(outputPath, JSON.stringify(report, null, 2), 'utf8');
      return { success: true, path: outputPath };
    }
    
    return report;
  }
}

// CLI支持
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const dedup = new CrossSystemDeduplicator();
  
  if (args[0] === '--stats') {
    console.log(JSON.stringify(dedup.getStats(), null, 2));
  } else if (args[0] === '--clear-cache') {
    console.log(JSON.stringify(dedup.clearCache(), null, 2));
  } else if (args[0] === '--test') {
    // 测试去重功能
    const testMemory = {
      content: '这是一个测试记忆，用于验证去重功能。',
      source: 'test',
      type: 'facts'
    };
    
    dedup.checkDuplicate(testMemory, {
      crossSystemDedup: true,
      similarityThreshold: 0.8
    }).then(result => {
      console.log(JSON.stringify(result, null, 2));
    }).catch(error => {
      console.error('测试失败:', error);
    });
  } else if (args[0] === '--export') {
    const outputPath = args[1] || './duplicate_report.json';
    dedup.exportDuplicateReport(outputPath).then(result => {
      console.log(JSON.stringify(result, null, 2));
    }).catch(console.error);
  } else {
    console.log('使用方法:');
    console.log('  node cross_system_dedup.js --stats');
    console.log('  node cross_system_dedup.js --clear-cache');
    console.log('  node cross_system_dedup.js --test');
    console.log('  node cross_system_dedup.js --export [输出路径]');
  }
}

export default CrossSystemDeduplicator;