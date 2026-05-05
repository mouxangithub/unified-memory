/**
 * AgentBrain OpenClaw 快速集成模块
 * 提供最简单的集成方案，让 AgentBrain 可以直接在 OpenClaw 中使用
 */

import { AgentBrain } from './agent_brain.js';

/**
 * OpenClaw 技能包装器
 * 将 AgentBrain 包装为 OpenClaw 可以直接调用的技能
 */
export class AgentBrainOpenClaw {
  constructor() {
    this.brain = new AgentBrain();
    this.name = 'agent_brain';
    this.description = 'AI Agent 记忆大脑 - 快速集成版';
    this.version = '1.0.0';
  }

  /**
   * 技能执行入口
   * @param {string} action - 操作类型
   * @param {object} params - 参数
   * @returns {Promise<any>} 执行结果
   */
  async execute(action, params = {}) {
    try {
      switch (action) {
        case 'remember':
          return await this.remember(params.text, params);
        
        case 'search':
          return await this.search(params.query, params);
        
        case 'get_context':
          return await this.getContext(params);
        
        case 'summarize':
          return await this.summarize(params);
        
        case 'stats':
          return this.getStats();
        
        case 'cleanup':
          return await this.cleanup(params);
        
        default:
          throw new Error(`未知操作: ${action}`);
      }
    } catch (error) {
      console.error(`AgentBrain 执行错误 (${action}):`, error.message);
      return {
        success: false,
        error: error.message,
        action
      };
    }
  }

  /**
   * 记住信息
   * @param {string} text - 要记住的内容
   * @param {object} options - 选项
   * @returns {Promise<object>} 结果
   */
  async remember(text, options = {}) {
    if (!text) {
      return { success: false, error: '需要提供要记住的内容' };
    }
    
    const result = await this.brain.remember(text, options);
    return {
      success: true,
      action: 'remember',
      text,
      result
    };
  }

  /**
   * 搜索记忆
   * @param {string} query - 搜索查询
   * @param {object} options - 选项
   * @returns {Promise<object>} 搜索结果
   */
  async search(query, options = {}) {
    if (!query) {
      return { success: false, error: '需要提供搜索查询' };
    }
    
    const results = await this.brain.search(query, options);
    return {
      success: true,
      action: 'search',
      query,
      count: results.length,
      results: results.slice(0, options.limit || 10)
    };
  }

  /**
   * 获取上下文
   * @param {object} options - 选项
   * @returns {Promise<object>} 上下文
   */
  async getContext(options = {}) {
    const context = await this.brain.getContext(options);
    return {
      success: true,
      action: 'get_context',
      context
    };
  }

  /**
   * 总结会话
   * @param {object} options - 选项
   * @returns {Promise<object>} 总结
   */
  async summarize(options = {}) {
    const summary = await this.brain.summarize(options);
    return {
      success: true,
      action: 'summarize',
      summary
    };
  }

  /**
   * 获取统计信息
   * @returns {object} 统计信息
   */
  getStats() {
    const stats = this.brain.getStats();
    return {
      success: true,
      action: 'stats',
      stats
    };
  }

  /**
   * 清理记忆
   * @param {object} options - 选项
   * @returns {Promise<object>} 清理结果
   */
  async cleanup(options = {}) {
    const result = await this.brain.cleanup(options);
    return {
      success: true,
      action: 'cleanup',
      result
    };
  }

  /**
   * 自然语言接口 - 直接解析和执行
   * @param {string} command - 自然语言命令
   * @returns {Promise<object>} 执行结果
   */
  async naturalLanguage(command) {
    if (!command) {
      return { success: false, error: '需要提供命令' };
    }

    // 简单的自然语言解析
    const lowerCommand = command.toLowerCase();
    
    if (lowerCommand.includes('记住') || lowerCommand.includes('记一下')) {
      const text = command.replace(/记住|记一下/g, '').trim();
      return await this.remember(text);
    }
    
    if (lowerCommand.includes('搜索') || lowerCommand.includes('查找')) {
      const query = command.replace(/搜索|查找/g, '').trim();
      return await this.search(query);
    }
    
    if (lowerCommand.includes('总结') || lowerCommand.includes('汇总')) {
      return await this.summarize();
    }
    
    if (lowerCommand.includes('统计') || lowerCommand.includes('状态')) {
      return this.getStats();
    }
    
    if (lowerCommand.includes('清理') || lowerCommand.includes('清除')) {
      return await this.cleanup();
    }
    
    // 默认尝试搜索
    return await this.search(command);
  }
}

/**
 * 创建 OpenClaw 技能实例
 */
export function createAgentBrainSkill() {
  const instance = new AgentBrainOpenClaw();
  
  return {
    name: instance.name,
    description: instance.description,
    version: instance.version,
    
    // OpenClaw 技能接口
    execute: instance.execute.bind(instance),
    
    // 快捷方法
    remember: instance.remember.bind(instance),
    search: instance.search.bind(instance),
    getContext: instance.getContext.bind(instance),
    summarize: instance.summarize.bind(instance),
    getStats: instance.getStats.bind(instance),
    cleanup: instance.cleanup.bind(instance),
    naturalLanguage: instance.naturalLanguage.bind(instance)
  };
}

// 默认导出
export default createAgentBrainSkill();