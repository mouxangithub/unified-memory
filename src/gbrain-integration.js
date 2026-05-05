/**
 * GBrain Integration Module - GBrain 集成模块
 * 
 * 将 GBrain 的核心功能集成到 Unified Memory v5
 * 
 * 功能：
 * - 两层页面格式支持
 * - Typed Links 集成
 * - Source Attribution 集成
 * - Entity Detection 集成
 * - Resolver 决策树集成
 * 
 * @module gbrain-integration
 */

import { Resolver, DirectoryType, DirectoryInfo } from './resolver.js';
import { TwoLayerFormat } from './memory_two_layer.js';
import { TypedLinks, TypedLinkType } from './typed_links.js';
import { Source, SourceManager, SourceType } from './source_attribution.js';
import { EntityDetector, EntityType } from './entity_detection.js';
import { MemoryGraph, RelationType, NodeType } from './memory_graph.js';

/**
 * GBrain 集成管理器
 */
export class GBrainIntegration {
  constructor(options = {}) {
    this.config = {
      enableTwoLayer: options.enableTwoLayer !== false,
      enableTypedLinks: options.enableTypedLinks !== false,
      enableSourceAttribution: options.enableSourceAttribution !== false,
      enableEntityDetection: options.enableEntityDetection !== false,
      enableResolver: options.enableResolver !== false,
    };
    
    // 初始化组件
    this.resolver = this.config.enableResolver ? new Resolver() : null;
    this.typedLinks = this.config.enableTypedLinks ? new TypedLinks() : null;
    this.sourceManager = this.config.enableSourceAttribution ? new SourceManager() : null;
    this.entityDetector = this.config.enableEntityDetection ? new EntityDetector() : null;
    
    // 内存图集成
    this.memoryGraph = options.memoryGraph || new MemoryGraph();
  }

  /**
   * 保存记忆（集成 GBrain 功能）
   */
  saveMemory(memory, context = {}) {
    const result = {
      memory,
      gbrain: {
        directory: null,
        twoLayer: null,
        typedLinks: [],
        source: null,
        entities: [],
      },
    };

    // 1. Resolver 决策树 - 确定目录
    if (this.config.enableResolver && this.resolver) {
      const decision = this.resolver.decide(memory.text, context);
      result.gbrain.directory = decision.directory;
      
      // 如果内存有目录字段，更新它
      if (memory.directory) {
        memory.directory = decision.directory;
      }
    }

    // 2. 两层页面格式
    if (this.config.enableTwoLayer) {
      const twoLayer = this.createTwoLayerPage(memory, context);
      result.gbrain.twoLayer = twoLayer;
      
      // 如果内存有 content 字段，更新为两层格式
      if (memory.content) {
        memory.content = twoLayer;
      }
    }

    // 3. Source Attribution
    if (this.config.enableSourceAttribution && this.sourceManager) {
      const source = this.createSourceFromContext(context);
      result.gbrain.source = source;
      
      this.sourceManager.add(memory.id, source);
    }

    // 4. Entity Detection
    if (this.config.enableEntityDetection && this.entityDetector) {
      const entities = this.entityDetector.detect(memory.text, context);
      result.gbrain.entities = entities;
      
      // 更新内存的 entities 字段
      if (memory.entities) {
        memory.entities = [...(memory.entities || []), ...entities.map(e => e.name)];
      }
      
      // 异步处理实体（创建/更新页面）
      this.processEntities(entities, memory.text, context);
    }

    // 5. Typed Links
    if (this.config.enableTypedLinks && this.typedLinks) {
      const relations = this.extractRelationsFromMemory(memory, context);
      result.gbrain.typedLinks = relations;
      
      // 添加关系
      for (const relation of relations) {
        this.typedLinks.add(relation.sourceId, relation.targetId, relation.type, relation.metadata);
      }
    }

    return result;
  }

  /**
   * 创建两层页面
   */
  createTwoLayerPage(memory, context = {}) {
    const entities = context.entities || [];
    const timeline = context.timeline || [];
    
    // 生成 Executive Summary
    const executiveSummary = this.generateExecutiveSummary(memory, context);
    
    // 生成 State
    const state = this.generateState(memory, context);
    
    // 生成 Assessment
    const assessment = this.generateAssessment(memory, context);
    
    // 生成 Open Threads
    const openThreads = this.generateOpenThreads(memory, context);
    
    // 构建 Timeline
    const timelineEntries = timeline.map(entry => ({
      date: entry.date || new Date().toISOString().split('T')[0],
      summary: entry.summary || '',
      detail: entry.detail || '',
      source: entry.source || '',
    }));
    
    return TwoLayerFormat.create({
      type: memory.type || 'default',
      slug: memory.slug || this.generateSlug(memory.text),
      tags: memory.tags || [],
      executiveSummary,
      state,
      assessment,
      openThreads,
      timeline: timelineEntries,
    });
  }

  /**
   * 生成 Executive Summary
   */
  generateExecutiveSummary(memory, context) {
    // 简单的摘要生成，后续可以用 LLM 增强
    const text = memory.text || '';
    
    // 如果文本很短，直接返回
    if (text.length <= 200) {
      return text;
    }
    
    // 提取前 200 个字符作为摘要
    return text.substring(0, 200) + '...';
  }

  /**
   * 生成 State
   */
  generateState(memory, context) {
    const state = {};
    
    // 从上下文中提取状态信息
    if (context.state) {
      Object.assign(state, context.state);
    }
    
    // 从内存中提取状态
    if (memory.state) {
      Object.assign(state, memory.state);
    }
    
    return state;
  }

  /**
   * 生成 Assessment
   */
  generateAssessment(memory, context) {
    // 简单的评估生成，后续可以用 LLM 增强
    if (context.assessment) {
      return context.assessment;
    }
    
    return '';
  }

  /**
   * 生成 Open Threads
   */
  generateOpenThreads(memory, context) {
    const threads = [];
    
    // 从上下文中提取开放线程
    if (context.openThreads) {
      for (const thread of context.openThreads) {
        threads.push({
          text: thread.text || thread,
          priority: thread.priority || 'medium',
          due: thread.due || 'pending',
        });
      }
    }
    
    return threads;
  }

  /**
   * 创建 Source
   */
  createSourceFromContext(context) {
    return new Source({
      type: context.sourceType || SourceType.USER,
      channel: context.channel || '',
      timestamp: context.timestamp || new Date(),
      author: context.author || '',
    });
  }

  /**
   * 处理实体
   */
  async processEntities(entities, text, context) {
    // 异步处理实体，不阻塞主流程
    setTimeout(() => {
      for (const entity of entities) {
        console.log(`[GBrainIntegration] Processing entity: ${entity.type} - ${entity.name}`);
        
        // 这里可以：
        // 1. 创建新页面
        // 2. 更新现有页面
        // 3. 添加关系
        // 4. 记录来源
        
        // 示例：创建页面
        // this.createEntityPage(entity, text, context);
      }
    }, 0);
  }

  /**
   * 从内存中提取关系
   */
  extractRelationsFromMemory(memory, context) {
    const relations = [];
    
    // 从上下文中提取关系
    if (context.relations) {
      for (const relation of context.relations) {
        relations.push({
          sourceId: relation.sourceId,
          targetId: relation.targetId,
          type: relation.type,
          metadata: relation.metadata || {},
        });
      }
    }
    
    return relations;
  }

  /**
   * 生成 Slug
   */
  generateSlug(text) {
    return text
      .toLowerCase()
      .replace(/[^a-z0-9\u4e00-\u9fff]+/g, '-')
      .replace(/^-|-$/g, '')
      .substring(0, 50);
  }

  /**
   * 获取内存的 GBrain 元数据
   */
  getGBrainMetadata(memoryId) {
    const metadata = {
      source: this.sourceManager ? this.sourceManager.format(memoryId) : null,
      typedLinks: this.typedLinks ? this.typedLinks.getOutgoing(memoryId) : [],
      entities: [],
    };
    
    return metadata;
  }

  /**
   * 查询内存（集成 GBrain 功能）
   */
  async search(query, options = {}) {
    const results = await this.memoryGraph.search(query, options);
    
    // 为每个结果添加 GBrain 元数据
    for (const result of results) {
      result.gbrain = this.getGBrainMetadata(result.id);
    }
    
    return results;
  }
}

/**
 * 工具函数：创建集成实例
 */
export function createGBrainIntegration(options = {}) {
  return new GBrainIntegration(options);
}

/**
 * 工具函数：保存记忆（带 GBrain 功能）
 */
export async function saveMemoryWithGBrain(memory, context = {}) {
  const integration = createGBrainIntegration();
  return integration.saveMemory(memory, context);
}
