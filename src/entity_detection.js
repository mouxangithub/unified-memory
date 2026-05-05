/**
 * Entity Detection - 实体检测
 * 
 * 从文本中检测实体（人物、公司、项目等）
 * 
 * 功能：
 * - 检测人物
 * - 检测公司
 * - 检测项目
 * - 检测概念
 * - 异步检测（不阻塞主流程）
 * 
 * @module entity_detection
 */

import { DirectoryType, Resolver } from './resolver.js';

/**
 * 实体类型
 */
export const EntityType = {
  PERSON: 'person',
  COMPANY: 'company',
  DEAL: 'deal',
  CONCEPT: 'concept',
  MEETING: 'meeting',
  PROJECT: 'project',
  IDEA: 'idea',
  ORIGINAL: 'original',
};

/**
 * 实体对象
 */
export class Entity {
  constructor(options = {}) {
    this.type = options.type;
    this.name = options.name;
    this.slug = options.slug || this.normalizeName(options.name);
    this.confidence = options.confidence || 0.5;
    this.context = options.context || '';
    this.metadata = options.metadata || {};
  }

  /**
   * 规范化名称
   */
  normalizeName(name) {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  }

  /**
   * 创建目录路径
   */
  getDirectoryPath() {
    const dirMap = {
      [EntityType.PERSON]: DirectoryType.PEOPLE,
      [EntityType.COMPANY]: DirectoryType.COMPANIES,
      [EntityType.DEAL]: DirectoryType.DEALS,
      [EntityType.CONCEPT]: DirectoryType.CONCEPTS,
      [EntityType.MEETING]: DirectoryType.MEETINGS,
      [EntityType.PROJECT]: DirectoryType.PROJECTS,
      [EntityType.IDEA]: DirectoryType.IDEAS,
      [EntityType.ORIGINAL]: DirectoryType.ORIGINALS,
    };
    
    return dirMap[this.type] || DirectoryType.INBOX;
  }
}

/**
 * 实体检测器
 */
export class EntityDetector {
  constructor(options = {}) {
    this.config = {
      confidenceThreshold: options.confidenceThreshold || 0.6,
      maxEntities: options.maxEntities || 20,
    };
    
    this.resolver = new Resolver();
  }

  /**
   * 检测文本中的实体
   */
  detect(text, context = {}) {
    const entities = [];
    
    // 检测人物
    entities.push(...this.detectPeople(text));
    
    // 检测公司
    entities.push(...this.detectCompanies(text));
    
    // 检测项目
    entities.push(...this.detectProjects(text));
    
    // 检测概念
    entities.push(...this.detectConcepts(text));
    
    // 检测会议
    entities.push(...this.detectMeetings(text));
    
    // 检测点子
    entities.push(...this.detectIdeas(text));
    
    // 检测原创
    entities.push(...this.detectOriginals(text));
    
    // 过滤低置信度
    const filtered = entities.filter(e => e.confidence >= this.config.confidenceThreshold);
    
    // 去重（按名称）
    const unique = [];
    const seen = new Set();
    for (const entity of filtered) {
      const key = `${entity.type}:${entity.slug}`;
      if (!seen.has(key)) {
        seen.add(key);
        unique.push(entity);
      }
    }
    
    // 限制数量
    return unique.slice(0, this.config.maxEntities);
  }

  /**
   * 检测人物
   */
  detectPeople(text) {
    const entities = [];
    
    // 简单实现：检测常见中文人名
    const commonNames = [
      '张三', '李四', '王五', '赵六', '刘选权',
      'Zhang San', 'Li Si', 'Wang Wu', 'Zhao Liu',
    ];
    
    for (const name of commonNames) {
      if (text.includes(name)) {
        entities.push(new Entity({
          type: EntityType.PERSON,
          name,
          confidence: 0.9,
          context: '人名',
        }));
      }
    }
    
    // 检测职位相关的上下文
    const positionKeywords = ['总监', '经理', 'CTO', 'CEO', '工程师', 'product manager'];
    for (const keyword of positionKeywords) {
      const match = text.match(/([a-zA-Z\u4e00-\u9fff]+)\s*(?:是|担任|作为)?\s*(?:\w+\s*)*(?:${keyword})/);
      if (match) {
        entities.push(new Entity({
          type: EntityType.PERSON,
          name: match[1],
          confidence: 0.7,
          context: `职位：${keyword}`,
        }));
      }
    }
    
    return entities;
  }

  /**
   * 检测公司
   */
  detectCompanies(text) {
    const entities = [];
    
    // 简单实现：检测常见公司名
    const commonCompanies = [
      'Acme', 'TechCorp', 'StartUp', 'Google', 'Microsoft', 'Amazon',
      'Acme Corp', 'Tech Corp', 'Start Up',
    ];
    
    for (const company of commonCompanies) {
      if (text.includes(company)) {
        entities.push(new Entity({
          type: EntityType.COMPANY,
          name: company,
          confidence: 0.85,
          context: '公司名',
        }));
      }
    }
    
    // 检测融资相关的上下文
    const fundingKeywords = ['融资', '投资', 'Series A', 'Series B', '融资轮次'];
    for (const keyword of fundingKeywords) {
      const match = text.match(/([a-zA-Z\u4e00-\u9fff]+(?:公司)?)(?:\s*[^${keyword}]+)*${keyword}/);
      if (match) {
        entities.push(new Entity({
          type: EntityType.COMPANY,
          name: match[1],
          confidence: 0.7,
          context: `融资：${keyword}`,
        }));
      }
    }
    
    return entities;
  }

  /**
   * 检测项目
   */
  detectProjects(text) {
    const entities = [];
    
    // 检测项目关键词
    const projectKeywords = ['项目', '计划', '开发', '迁移', '重构', 'API', 'GraphQL'];
    for (const keyword of projectKeywords) {
      const match = text.match(/([a-zA-Z\u4e00-\u9fff]+(?:项目)?)(?:\s*[^${keyword}]+)*${keyword}/);
      if (match) {
        entities.push(new Entity({
          type: EntityType.PROJECT,
          name: match[1],
          confidence: 0.7,
          context: `项目：${keyword}`,
        }));
      }
    }
    
    return entities;
  }

  /**
   * 检测概念
   */
  detectConcepts(text) {
    const entities = [];
    
    // 检测概念关键词
    const conceptKeywords = ['MECE', '框架', '原则', '方法论', '理论', '模型', 'pattern'];
    for (const keyword of conceptKeywords) {
      const match = text.match(/([a-zA-Z\u4e00-\u9fff]+(?:原则)?)(?:\s*[^${keyword}]+)*${keyword}/);
      if (match) {
        entities.push(new Entity({
          type: EntityType.CONCEPT,
          name: match[1],
          confidence: 0.7,
          context: `概念：${keyword}`,
        }));
      }
    }
    
    return entities;
  }

  /**
   * 检测会议
   */
  detectMeetings(text) {
    const entities = [];
    
    // 检测日期
    const dateRegex = /\d{4}-\d{2}-\d{2}/g;
    const dates = text.match(dateRegex);
    
    if (dates) {
      for (const date of dates) {
        if (text.includes('会议') || text.includes('同步') || text.includes('讨论')) {
          entities.push(new Entity({
            type: EntityType.MEETING,
            name: `Meeting ${date}`,
            confidence: 0.75,
            context: `日期：${date}`,
          }));
        }
      }
    }
    
    return entities;
  }

  /**
   * 检测点子
   */
  detectIdeas(text) {
    const entities = [];
    
    // 检测点子关键词
    const ideaKeywords = ['点子', '创意', '想法', '功能', '方案', 'feature'];
    for (const keyword of ideaKeywords) {
      const match = text.match(/([a-zA-Z\u4e00-\u9fff]+(?:功能)?)(?:\s*[^${keyword}]+)*${keyword}/);
      if (match) {
        entities.push(new Entity({
          type: EntityType.IDEA,
          name: match[1],
          confidence: 0.65,
          context: `点子：${keyword}`,
        }));
      }
    }
    
    return entities;
  }

  /**
   * 检测原创
   */
  detectOriginals(text) {
    const entities = [];
    
    // 检测原创关键词
    const originalKeywords = ['洞察', '原话', '观点', 'ambition', 'lifespan', 'ratio'];
    for (const keyword of originalKeywords) {
      if (text.includes(keyword)) {
        entities.push(new Entity({
          type: EntityType.ORIGINAL,
          name: keyword,
          confidence: 0.7,
          context: `原创：${keyword}`,
        }));
      }
    }
    
    return entities;
  }

  /**
   * 异步检测（不阻塞主流程）
   */
  async detectAsync(text, context = {}) {
    // 在后台运行，不阻塞主流程
    setTimeout(() => {
      const entities = this.detect(text, context);
      
      // 这里可以触发创建/更新实体的逻辑
      for (const entity of entities) {
        this.handleEntity(entity, text, context);
      }
    }, 0);
    
    return { status: 'queued' };
  }

  /**
   * 处理检测到的实体
   */
  handleEntity(entity, text, context) {
    // 这里可以：
    // 1. 创建新页面
    // 2. 更新现有页面
    // 3. 添加关系
    // 4. 记录来源
    
    console.log(`[EntityDetection] Found ${entity.type}: ${entity.name} (${entity.confidence})`);
    
    // 示例：创建页面
    // this.createPage(entity, text, context);
  }
}

/**
 * 工具函数：创建检测器
 */
export function createEntityDetector(options = {}) {
  return new EntityDetector(options);
}

/**
 * 工具函数：检测文本中的实体
 */
export function detectEntities(text, options = {}) {
  const detector = createEntityDetector(options);
  return detector.detect(text);
}
