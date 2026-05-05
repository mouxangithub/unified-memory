/**
 * IntentParser - 意图解析器
 * 
 * 将自然语言解析为结构化的意图和操作
 * 
 * @module intent_parser
 */

/**
 * 意图类型
 */
export const IntentType = {
  REMEMBER: 'remember',
  FORGET: 'forget',
  SEARCH: 'search',
  CONTEXT: 'context',
  ARCHIVE: 'archive',
  SUMMARIZE: 'summarize',
  STATS: 'stats',
  CLEANUP: 'cleanup',
  PREFERENCE: 'preference',
  SKILL: 'skill',
  UNKNOWN: 'unknown',
};

/**
 * IntentParser 类
 */
export class IntentParser {
  constructor() {
    this.cache = new Map();
    this.cacheEnabled = true;
  }

  /**
   * 解析自然语言为意图
   * 
   * @param {string} text - 输入文本
   * @returns {Object} 解析结果 { type, entities, rawText, confidence }
   */
  parse(text) {
    if (!text || typeof text !== 'string') {
      return { type: IntentType.UNKNOWN, entities: {}, rawText: text, confidence: 0 };
    }

    // 检查缓存
    const cacheKey = text;
    if (this.cacheEnabled && this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    const trimmed = text.trim();
    const result = {
      type: IntentType.UNKNOWN,
      entities: {},
      rawText: trimmed,
      confidence: 0,
    };

    // 优先检查特殊模式（更具体的模式优先）

    // 1. 归档
    if (/^(归档|这段对话可以归档了|保存当前对话|记录这次对话)/.test(trimmed)) {
      result.type = IntentType.ARCHIVE;
      result.confidence = 0.95;
    }
    // 2. 总结
    else if (/^(总结|概括|归纳)/.test(trimmed)) {
      result.type = IntentType.SUMMARIZE;
      result.confidence = 0.95;
    }
    // 3. 统计
    else if (/^(统计|状态|有多少)/.test(trimmed)) {
      result.type = IntentType.STATS;
      result.confidence = 0.9;
    }
    // 4. 清理
    else if (/^(清理|清除|重置)/.test(trimmed)) {
      result.type = IntentType.CLEANUP;
      result.confidence = 0.9;
    }
    // 5. 上下文
    else if (/^(当前上下文|工作记忆|会话记忆|上下文)/.test(trimmed)) {
      result.type = IntentType.CONTEXT;
      result.confidence = 0.9;
    }
    // 6. 搜索 (包括 "X有哪些" 和 "X是什么" 模式)
    else if (/^(搜索|查找|找一下|查一下)/.test(trimmed)) {
      result.type = IntentType.SEARCH;
      result.confidence = 0.95;
      result.extractedText = trimmed.replace(/^(搜索|查找|找一下|查一下)/, '');
    }
    else if (/(.+)有哪些/.test(trimmed)) {
      result.type = IntentType.SEARCH;
      result.confidence = 0.85;
      result.extractedText = trimmed.match(/(.+)有哪些/)[1];
    }
    else if (/(.+)是什么/.test(trimmed)) {
      result.type = IntentType.SEARCH;
      result.confidence = 0.85;
      result.extractedText = trimmed.match(/(.+)是什么/)[1];
    }
    // 7. 记住/记得
    else if (/^(记住|记得)/.test(trimmed)) {
      // 检查是否是偏好类
      if (/喜欢|偏好|想要|缩进|空格|单引号|双引号/.test(trimmed)) {
        result.type = IntentType.PREFERENCE;
        result.confidence = 0.9;
      } else {
        result.type = IntentType.REMEMBER;
        result.confidence = 0.9;
        result.extractedText = trimmed.replace(/^(记住|记得)/, '');
      }
    }
    // 8. 忘记
    else if (/^(忘记|不用记住|删掉|移除)/.test(trimmed)) {
      result.type = IntentType.FORGET;
      result.confidence = 0.9;
      result.extractedText = trimmed.replace(/^(忘记|不用记住|删掉|移除)/, '');
    }
    // 9. 偏好模式 (用户喜欢/偏好/想要)
    else if (/用户喜欢|用户偏好|用户想要/.test(trimmed)) {
      result.type = IntentType.PREFERENCE;
      result.confidence = 0.9;
    }
    // 10. 编码风格偏好
    else if (/缩进.*空格|单引号|双引号|编码风格/.test(trimmed)) {
      result.type = IntentType.PREFERENCE;
      result.confidence = 0.85;
    }
    // 11. 技能模式
    else if (/技能|如何|怎样|怎么做|编程|开发/.test(trimmed)) {
      result.type = IntentType.SKILL;
      result.confidence = 0.8;
    }
    // 12. "用户叫X" 模式 - 作为 REMEMBER
    else if (/^用户叫/.test(trimmed)) {
      result.type = IntentType.REMEMBER;
      result.confidence = 0.9;
      const match = trimmed.match(/用户叫(.+)/);
      if (match) {
        result.entities.personName = match[1].trim();
        result.extractedText = match[1].trim();
      }
    }
    // 13. 项目模式 - 作为 REMEMBER
    else if (/项目/.test(trimmed)) {
      result.type = IntentType.REMEMBER;
      result.confidence = 0.8;
    }

    // 提取实体
    if (result.type !== IntentType.UNKNOWN) {
      result.entities = { ...result.entities, ...this._extractEntities(trimmed, result.type) };
    }

    // 缓存结果
    if (this.cacheEnabled) {
      this.cache.set(cacheKey, result);
    }

    return result;
  }

  /**
   * 提取实体
   */
  _extractEntities(text, type) {
    const entities = {};

    // 偏好实体提取
    if (type === IntentType.PREFERENCE || text.includes('喜欢')) {
      if (text.includes('单引号')) {
        entities.quoteStyle = 'single';
      } else if (text.includes('双引号')) {
        entities.quoteStyle = 'double';
      }
      
      const indentMatch = text.match(/(\d+)\s*空格/);
      if (indentMatch) {
        entities.indentSize = parseInt(indentMatch[1]);
      }
      
      if (text.includes('Tab')) {
        entities.indentStyle = 'tab';
      } else if (text.includes('空格')) {
        entities.indentStyle = 'space';
      }
    }

    // 技能实体提取
    if (type === IntentType.SKILL) {
      const languages = ['JavaScript', 'TypeScript', 'Python', 'Java', 'Go', 'Rust', 'C++', 'C#'];
      for (const lang of languages) {
        if (text.includes(lang)) {
          entities.language = lang;
          break;
        }
      }
      
      const frameworks = ['React', 'Vue', 'Angular', 'Node.js', 'Django', 'Flask', 'Spring'];
      for (const fw of frameworks) {
        if (text.includes(fw)) {
          entities.framework = fw;
          break;
        }
      }
    }

    // 记忆实体提取
    if (type === IntentType.REMEMBER) {
      if (/用户叫(.+)/.test(text)) {
        const match = text.match(/用户叫(.+)/);
        if (match) entities.personName = match[1].trim();
      }
      if (/项目[是为]?(.+)/.test(text)) {
        const match = text.match(/项目[是为]?(.+)/);
        if (match) entities.project = match[1].trim();
      }
      if (/使用(.+)/.test(text)) {
        const match = text.match(/使用(.+)/);
        if (match) entities.technology = match[1].trim();
      }
    }

    return entities;
  }

  /**
   * 清除缓存
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * 启用/禁用缓存
   */
  setCacheEnabled(enabled) {
    this.cacheEnabled = enabled;
  }
}

// 导出单例
export const intentParser = new IntentParser();

export default IntentParser;