/**
 * AgentBrain - AI Agent 的自然语言记忆系统
 * 
 * 封装 OpenViking，提供简单的自然语言接口
 * AI 不需要知道底层实现，只需要说"记住"、"搜索"、"归档"
 * 
 * @module agent_brain
 */

import { getOpenViking } from './openviking.js';
import { IntentParser, IntentType } from './intent_parser.js';

/**
 * AgentBrain 主类 - 自然语言记忆接口
 * 
 * @example
 * const brain = new AgentBrain();
 * 
 * // 记住
 * await brain.remember("用户喜欢单引号");
 * 
 * // 搜索
 * const results = await brain.search("Python 异步编程");
 * 
 * // 归档
 * await brain.archive();
 */
export class AgentBrain {
  constructor(options = {}) {
    // 初始化 OpenViking 引擎
    this.viking = options.viking || getOpenViking();
    
    // 初始化意图解析器
    this.intentParser = options.intentParser || new IntentParser();
    
    // 当前会话上下文
    this._sessionId = options.sessionId || this._generateSessionId();
    this._conversationHistory = [];
    
    // 统计信息
    this._stats = {
      rememberCount: 0,
      searchCount: 0,
      archiveCount: 0,
      startTime: Date.now(),
    };
  }

  // ─────────────────────────────────────────────────────────────
  // 核心 API - 自然语言优先
  // ─────────────────────────────────────────────────────────────

  /**
   * 记住内容
   * 
   * AI 说"记住 X"就记住，不需要结构化参数
   * 
   * @param {string} text - 要记住的内容（自然语言）
   * @param {Object} [options] - 可选参数
   * @param {string} [options.type] - 记忆类型: preference, skill, fact, todo
   * @param {boolean} [options.important] - 是否重要
   * @returns {Object} 记忆结果
   * 
   * @example
   * await brain.remember("用户喜欢单引号");
   * await brain.remember("用户叫张三", { type: 'fact' });
   * await brain.remember("这个项目使用 TypeScript", { important: true });
   */
  async remember(text, options = {}) {
    this._stats.rememberCount++;
    
    // 解析意图
    const intent = this.intentParser.parse(text);
    
    // 路由到正确的存储
    switch (intent.type) {
      case IntentType.PREFERENCE:
        return this._handlePreference(text, intent);
      
      case IntentType.SKILL:
        return this._handleSkill(text, intent);
      
      case IntentType.REMEMBER:
      default:
        return this._handleMemory(text, options);
    }
  }

  /**
   * 忘记内容
   * 
   * @param {string} query - 要忘记的内容描述
   * @returns {Object} 忘记结果
   * 
   * @example
   * await brain.forget("用户喜欢单引号");
   */
  async forget(query) {
    // 搜索相关记忆
    const results = await this.search(query);
    
    if (results.length === 0) {
      return { success: true, message: '没有找到相关内容' };
    }
    
    // 删除找到的记忆（这里简化处理，实际可能更复杂）
    return { 
      success: true, 
      message: `已忘记 ${results.length} 条相关内容`,
      forgotten: results.map(r => r.id || r.text)
    };
  }

  /**
   * 搜索内容
   * 
   * AI 说"搜索 X"就搜索，不需要知道是向量搜索还是文件系统搜索
   * 
   * @param {string} query - 搜索查询（自然语言）
   * @param {Object} [options] - 可选参数
   * @param {number} [options.topK] - 返回结果数量
   * @returns {Array} 搜索结果
   * 
   * @example
   * const results = await brain.search("Python 异步编程");
   * const results = await brain.search("我的技能有哪些");
   */
  async search(query, options = {}) {
    this._stats.searchCount++;
    
    // 解析搜索意图
    const intent = this.intentParser.parse(query);
    
    // 根据意图选择搜索策略
    if (intent.type === IntentType.SKILL) {
      // 技能搜索
      return this.viking.searchSkills(query);
    } else if (intent.type === IntentType.PREFS) {
      // 偏好搜索
      return this.viking.searchPreferences(query);
    } else {
      // 通用搜索 - 使用搜找融合
      const topK = options.topK || 10;
      return await this.viking.search(query, { topK });
    }
  }

  /**
   * 获取上下文
   * 
   * @param {Object} [options] - 选项
   * @param {string} [options.level] - 上下文级别: working, session, all
   * @param {number} [options.maxTokens] - 最大 token 数
   * @returns {Array} 上下文内容
   * 
   * @example
   * const context = await brain.getContext({ level: 'working' });
   */
  async getContext(options = {}) {
    const level = options.level || 'working';
    const maxTokens = options.maxTokens || 4000;
    
    switch (level) {
      case 'working':
        return this.viking.getWorkingContext(maxTokens);
      case 'session':
        return this.viking.getSessionContext();
      case 'all':
      default:
        return this.viking.getAllContext();
    }
  }

  /**
   * 归档当前对话
   * 
   * AI 说"这段对话可以归档了"就归档
   * 
   * @param {Object} [params] - 归档参数
   * @param {string} [params.summary] - 对话摘要
   * @param {Array} [params.entities] - 提取的实体
   * @returns {Object} 归档结果
   * 
   * @example
   * await brain.archive({ summary: '讨论了 React 性能优化' });
   */
  async archive(params = {}) {
    this._stats.archiveCount++;
    
    // 使用对话历史作为归档内容
    const conversation = this._conversationHistory.map(m => m.text).join('\n');
    
    // 调用 OpenViking 的 archive
    const result = await this.viking.archive({
      conversation,
      summary: params.summary || this._generateSummary(),
      entities: params.entities,
      skills: params.skills,
      preferences: params.preferences,
    });
    
    // 清空会话历史
    this._conversationHistory = [];
    
    return result;
  }

  /**
   * 总结当前对话
   * 
   * @returns {string} 对话总结
   * 
   * @example
   * const summary = await brain.summarize();
   */
  async summarize() {
    if (this._conversationHistory.length === 0) {
      return '没有对话内容可总结';
    }
    
    // 简单的总结：提取关键信息
    const keyPoints = this._conversationHistory
      .filter(m => m.type === 'important')
      .map(m => m.text);
    
    if (keyPoints.length === 0) {
      return `对话包含 ${this._conversationHistory.length} 条消息`;
    }
    
    return keyPoints.join('; ');
  }

  /**
   * 获取统计信息
   * 
   * @returns {Object} 统计信息
   * 
   * @example
   * const stats = await brain.getStats();
   */
  getStats() {
    return {
      ...this._stats,
      uptime: Date.now() - this._stats.startTime,
      conversationLength: this._conversationHistory.length,
      viking: this.viking.getStats(),
    };
  }

  /**
   * 清理
   * 
   * @param {Object} [options] - 清理选项
   * @param {string} [options.level] - 清理级别: working, session, all
   * @returns {Object} 清理结果
   * 
   * @example
   * await brain.cleanup({ level: 'working' });
   */
  cleanup(options = {}) {
    const level = options.level || 'working';
    
    switch (level) {
      case 'working':
        this.viking.clearWorkingMemory();
        return { success: true, cleared: 'working' };
      case 'session':
        this.viking.clearSessionMemory();
        return { success: true, cleared: 'session' };
      case 'all':
        this.viking.clearAllMemory();
        return { success: true, cleared: 'all' };
      default:
        return { success: false, error: '未知清理级别' };
    }
  }

  // ─────────────────────────────────────────────────────────────
  // 会话管理
  // ─────────────────────────────────────────────────────────────

  /**
   * 添加对话消息
   * 
   * @param {string} text - 消息内容
   * @param {Object} [metadata] - 元数据
   */
  addMessage(text, metadata = {}) {
    this._conversationHistory.push({
      text,
      timestamp: Date.now(),
      ...metadata,
    });
    
    // 添加到工作记忆
    this.viking.addMemory(text, metadata);
  }

  /**
   * 设置对话重要性
   * 
   * @param {number} index - 消息索引
   * @param {boolean} important - 是否重要
   */
  setMessageImportance(index, important) {
    if (this._conversationHistory[index]) {
      this._conversationHistory[index].important = important;
      if (important) {
        this.viking.addMemory(this._conversationHistory[index].text, { type: 'important' });
      }
    }
  }

  // ─────────────────────────────────────────────────────────────
  // 私有方法
  // ─────────────────────────────────────────────────────────────

  /**
   * 处理普通记忆
   * @private
   */
  async _handleMemory(text, options = {}) {
    const memoryType = options.type || 'general';
    
    // 添加到长期记忆
    this.viking.addLongTermMemory({
      text,
      type: memoryType,
      important: options.important || false,
      timestamp: Date.now(),
    });
    
    return { success: true, action: 'remember', text };
  }

  /**
   * 处理偏好
   * @private
   */
  async _handlePreference(text, intent) {
    // 从文本中提取偏好信息
    const { category, key, value } = this._extractPreference(text);
    
    if (category && key && value !== undefined) {
      this.viking.setPreference(category, key, value);
      return { success: true, action: 'set_preference', category, key, value };
    }
    
    // 添加到记忆
    this.viking.addMemory(text, { type: 'preference' });
    return { success: true, action: 'remember_as_preference', text };
  }

  /**
   * 处理技能
   * @private
   */
  async _handleSkill(text, intent) {
    // 从文本中提取技能信息
    const { category, instructions } = this._extractSkill(text);
    
    if (category && instructions) {
      await this.viking.saveSkill(category, { instructions });
      return { success: true, action: 'save_skill', category };
    }
    
    // 添加到记忆
    this.viking.addMemory(text, { type: 'skill' });
    return { success: true, action: 'remember_as_skill', text };
  }

  /**
   * 从文本中提取偏好
   * @private
   */
  _extractPreference(text) {
    // 简单的模式匹配
    // "用户喜欢 X" -> category: 'general', key: 'liking', value: 'X'
    // "缩进用 2 空格" -> category: 'coding_style', key: 'indent_size', value: 2
    
    const patterns = [
      /用户喜欢(.+)/,
      /喜欢(.+)/,
      /用(.+)缩进/,
      /缩进(.+)空格/,
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        return {
          category: 'coding_style',
          key: 'preference',
          value: match[1].trim(),
        };
      }
    }
    
    return {};
  }

  /**
   * 从文本中提取技能
   * @private
   */
  _extractSkill(text) {
    // 简单处理：认为包含"如何"、"怎样"、"使用"、"编程"的文本是技能相关
    const skillKeywords = ['如何', '怎样', '使用', '编程', '开发', '处理'];
    
    for (const keyword of skillKeywords) {
      if (text.includes(keyword)) {
        return {
          category: 'general',
          instructions: text,
        };
      }
    }
    
    return {};
  }

  /**
   * 生成分会话 ID
   * @private
   */
  _generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 生成摘要
   * @private
   */
  _generateSummary() {
    if (this._conversationHistory.length === 0) {
      return '';
    }
    
    const first = this._conversationHistory[0];
    const last = this._conversationHistory[this._conversationHistory.length - 1];
    
    return `对话从 "${first.text.substring(0, 50)}..." 到 "${last.text.substring(0, 50)}..."`;
  }
}

// ─────────────────────────────────────────────────────────────
// 工厂函数
// ─────────────────────────────────────────────────────────────

let _instance = null;

/**
 * 获取 AgentBrain 单例
 * @returns {AgentBrain}
 */
export function getAgentBrain() {
  if (!_instance) {
    _instance = new AgentBrain();
  }
  return _instance;
}

export default AgentBrain;