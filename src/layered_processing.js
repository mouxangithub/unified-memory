/**
 * 分层内容处理引擎 - 实现OpenViking的L0/L1/L2分层
 * 
 * L0: 摘要层 (~100 tokens) - 快速筛选
 * L1: 概览层 (~2k tokens) - 决策参考  
 * L2: 详情层 (完整内容) - 深度阅读
 */

import { EmbeddingClient } from './embedding_providers.js';

export class LayeredProcessor {
  constructor(config = {}) {
    this.config = {
      // 默认配置
      enableL0: true,
      enableL1: true,
      l0MaxTokens: 100,
      l1MaxTokens: 2000,
      summaryModel: 'local', // local, ollama, openai
      ...config
    };
    
    this.embeddingClient = new EmbeddingClient();
  }

  /**
   * 处理记忆内容，生成分层表示
   */
  async processMemory(memory) {
    const { content, metadata = {} } = memory;
    
    const layers = {
      l0: null, // 摘要
      l1: null, // 概览
      l2: content, // 完整内容
      embeddings: {}
    };

    // 生成L0摘要
    if (this.config.enableL0) {
      layers.l0 = await this.generateL0Summary(content);
      // 为摘要生成向量
      layers.embeddings.l0 = await this.embeddingClient.embed(layers.l0);
    }

    // 生成L1概览
    if (this.config.enableL1) {
      layers.l1 = await this.generateL1Overview(content);
      layers.embeddings.l1 = await this.embeddingClient.embed(layers.l1);
    }

    // 为完整内容生成向量（如果还没有）
    if (!memory.embedding) {
      layers.embeddings.l2 = await this.embeddingClient.embed(content);
    } else {
      layers.embeddings.l2 = memory.embedding;
    }

    return {
      ...memory,
      layers,
      metadata: {
        ...metadata,
        processedAt: new Date().toISOString(),
        layerVersions: {
          l0: '1.0',
          l1: '1.0',
          l2: '1.0'
        }
      }
    };
  }

  /**
   * 生成L0摘要 (~100 tokens)
   */
  async generateL0Summary(content) {
    // 简单实现：提取前3句话或前100个字符
    if (content.length <= 100) {
      return content;
    }

    // 尝试按句子分割
    const sentences = content.split(/[.!?。！？]+/).filter(s => s.trim().length > 0);
    
    if (sentences.length >= 3) {
      return sentences.slice(0, 3).join('. ') + '.';
    }

    // 如果句子不够，取前100个字符
    return content.substring(0, 100) + (content.length > 100 ? '...' : '');
  }

  /**
   * 生成L1概览 (~2k tokens)
   */
  async generateL1Overview(content) {
    if (content.length <= 2000) {
      return content;
    }

    // 提取关键部分：开头、中间重要段落、结尾
    const parts = [];
    
    // 开头部分（前500字符）
    parts.push(content.substring(0, Math.min(500, content.length)));
    
    // 中间重要部分（尝试找关键段落）
    const middleStart = Math.floor(content.length * 0.3);
    const middleEnd = Math.floor(content.length * 0.7);
    const middleSection = content.substring(middleStart, Math.min(middleStart + 500, middleEnd));
    
    // 查找包含关键信息的段落
    const keyPhrases = ['重要', '关键', '注意', '建议', '解决', '配置', '设置'];
    let foundKeySection = middleSection;
    
    for (const phrase of keyPhrases) {
      const idx = content.indexOf(phrase);
      if (idx !== -1 && idx > middleStart && idx < middleEnd) {
        const start = Math.max(idx - 100, middleStart);
        const end = Math.min(idx + 400, middleEnd);
        foundKeySection = content.substring(start, end);
        break;
      }
    }
    
    parts.push(foundKeySection);
    
    // 结尾部分（最后500字符）
    const endStart = Math.max(0, content.length - 500);
    parts.push(content.substring(endStart));
    
    return parts.join('\n\n---\n\n');
  }

  /**
   * 按需加载内容层
   */
  async loadLayer(memory, layer = 'l2') {
    if (!memory.layers) {
      // 如果记忆还没有分层处理，先处理
      return this.processMemory(memory);
    }

    switch (layer) {
      case 'l0':
        return {
          content: memory.layers.l0,
          embedding: memory.layers.embeddings.l0,
          metadata: { ...memory.metadata, layerLoaded: 'l0' }
        };
      
      case 'l1':
        return {
          content: memory.layers.l1,
          embedding: memory.layers.embeddings.l1,
          metadata: { ...memory.metadata, layerLoaded: 'l1' }
        };
      
      case 'l2':
      default:
        return {
          content: memory.layers.l2,
          embedding: memory.layers.embeddings.l2,
          metadata: { ...memory.metadata, layerLoaded: 'l2' }
        };
    }
  }

  /**
   * 批量处理记忆
   */
  async batchProcessMemories(memories, concurrency = 3) {
    const results = [];
    
    // 简单实现：顺序处理
    for (let i = 0; i < memories.length; i++) {
      try {
        const processed = await this.processMemory(memories[i]);
        results.push(processed);
        
        // 进度日志
        if ((i + 1) % 10 === 0) {
          console.log(`已处理 ${i + 1}/${memories.length} 条记忆`);
        }
      } catch (error) {
        console.error(`处理记忆 ${i} 失败:`, error);
        results.push(memories[i]); // 保留原始记忆
      }
    }
    
    return results;
  }

  /**
   * 估算Token节省
   */
  estimateTokenSavings(memory) {
    if (!memory.layers) {
      return { l0: 0, l1: 0, total: 0 };
    }

    const l2Tokens = this.estimateTokens(memory.layers.l2);
    const l1Tokens = memory.layers.l1 ? this.estimateTokens(memory.layers.l1) : l2Tokens;
    const l0Tokens = memory.layers.l0 ? this.estimateTokens(memory.layers.l0) : l1Tokens;

    return {
      l0: l2Tokens - l0Tokens,
      l1: l2Tokens - l1Tokens,
      total: l2Tokens - l0Tokens, // 最大节省
      percentages: {
        l0: ((l2Tokens - l0Tokens) / l2Tokens * 100).toFixed(1),
        l1: ((l2Tokens - l1Tokens) / l2Tokens * 100).toFixed(1)
      }
    };
  }

  /**
   * 简单Token估算（中文按字，英文按词）
   */
  estimateTokens(text) {
    if (!text) return 0;
    
    // 简单估算：中文字符数 * 1.3 + 英文单词数 * 1.3
    const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
    const englishWords = (text.match(/\b[a-zA-Z]+\b/g) || []).length;
    
    return Math.ceil(chineseChars * 1.3 + englishWords * 1.3);
  }

  /**
   * 获取统计信息
   */
  getStats(memories) {
    const stats = {
      total: memories.length,
      processed: 0,
      tokenSavings: { l0: 0, l1: 0, total: 0 },
      layerDistribution: { l0: 0, l1: 0, l2: 0 }
    };

    for (const memory of memories) {
      if (memory.layers) {
        stats.processed++;
        
        if (memory.layers.l0) stats.layerDistribution.l0++;
        if (memory.layers.l1) stats.layerDistribution.l1++;
        if (memory.layers.l2) stats.layerDistribution.l2++;
        
        const savings = this.estimateTokenSavings(memory);
        stats.tokenSavings.l0 += savings.l0;
        stats.tokenSavings.l1 += savings.l1;
        stats.tokenSavings.total += savings.total;
      }
    }

    // 计算平均值
    if (stats.processed > 0) {
      stats.avgTokenSavings = {
        l0: Math.round(stats.tokenSavings.l0 / stats.processed),
        l1: Math.round(stats.tokenSavings.l1 / stats.processed),
        total: Math.round(stats.tokenSavings.total / stats.processed)
      };
      
      stats.avgPercentageSavings = {
        l0: ((stats.tokenSavings.l0 / (stats.tokenSavings.l0 + stats.tokenSavings.l1)) * 100).toFixed(1),
        l1: ((stats.tokenSavings.l1 / (stats.tokenSavings.l0 + stats.tokenSavings.l1)) * 100).toFixed(1)
      };
    }

    return stats;
  }
}

// 导出单例
export const layeredProcessor = new LayeredProcessor();

// 工具函数：快速处理单个记忆
export async function processMemoryWithLayers(memory, config = {}) {
  const processor = new LayeredProcessor(config);
  return processor.processMemory(memory);
}