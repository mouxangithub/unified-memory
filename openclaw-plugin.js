/**
 * Unified Memory OpenClaw 集成插件
 * 深度生态融合，类似 memory-core-plus 体验
 */

const path = require('path');
const fs = require('fs');

class OpenClawPlugin {
  constructor(options = {}) {
    this.name = 'unified-memory-openclaw';
    this.version = '1.0.0';
    this.description = 'Unified Memory 深度集成插件';
    
    this.config = {
      // 集成配置
      integration: {
        enabled: true,
        autoRegister: true,
        hookPriority: 'normal',
        toolExposure: 'full'
      },
      
      // 自动化配置
      automation: {
        autoCapture: true,
        autoRecall: true,
        contextAware: true,
        importanceFilter: true
      },
      
      // 性能配置
      performance: {
        cacheHooks: true,
        batchProcessing: true,
        lazyLoading: true
      },
      
      // UI 配置
      ui: {
        showMemoryPanel: true,
        memorySuggestions: true,
        contextDisplay: true
      },
      
      ...options
    };
    
    this.initialize();
  }
  
  initialize() {
    console.log('🔌 OpenClaw 插件初始化...');
    
    // 检测 OpenClaw 环境
    this.openclawAvailable = this.detectOpenClaw();
    
    if (!this.openclawAvailable) {
      console.log('⚠️ OpenClaw 环境未检测到，插件将以独立模式运行');
      this.mode = 'standalone';
      return;
    }
    
    this.mode = 'integrated';
    this.registerHooks();
    this.registerTools();
    this.setupUI();
    
    console.log(`✅ OpenClaw 插件初始化完成 (模式: ${this.mode})`);
  }
  
  /**
   * 检测 OpenClaw 环境
   */
  detectOpenClaw() {
    try {
      // 检查全局变量
      if (typeof global !== 'undefined' && global.openclaw) {
        return true;
      }
      
      // 检查模块
      require.resolve('@qingchencloud/openclaw-zh');
      return true;
    } catch {
      return false;
    }
  }
  
  /**
   * 注册 OpenClaw hooks
   */
  registerHooks() {
    if (this.mode !== 'integrated') return;
    
    console.log('🪝 注册 OpenClaw hooks...');
    
    this.hooks = {
      // 对话开始 hook
      session_start: {
        handler: this.handleSessionStart.bind(this),
        priority: this.config.integration.hookPriority
      },
      
      // 消息接收 hook
      message_received: {
        handler: this.handleMessageReceived.bind(this),
        priority: this.config.integration.hookPriority
      },
      
      // 提示构建前 hook（自动召回）
      before_prompt_build: {
        handler: this.handleBeforePromptBuild.bind(this),
        priority: 'high' // 高优先级，确保记忆被包含
      },
      
      // 代理结束 hook（自动捕获）
      agent_end: {
        handler: this.handleAgentEnd.bind(this),
        priority: this.config.integration.hookPriority
      },
      
      // 错误处理 hook
      error_occurred: {
        handler: this.handleError.bind(this),
        priority: 'low'
      }
    };
    
    // 模拟注册到 OpenClaw
    console.log('✅ Hooks 注册完成:', Object.keys(this.hooks).join(', '));
  }
  
  /**
   * 注册工具
   */
  registerTools() {
    if (this.mode !== 'integrated') return;
    
    console.log('🛠️ 注册工具...');
    
    this.tools = [
      {
        name: 'memory_search',
        description: '搜索记忆库',
        parameters: {
          query: {
            type: 'string',
            required: true,
            description: '搜索关键词'
          },
          limit: {
            type: 'number',
            default: 5,
            description: '返回结果数量'
          },
          tags: {
            type: 'array',
            default: [],
            description: '按标签过滤'
          }
        },
        handler: this.handleMemorySearch.bind(this)
      },
      {
        name: 'memory_add',
        description: '添加记忆',
        parameters: {
          content: {
            type: 'string',
            required: true,
            description: '记忆内容'
          },
          tags: {
            type: 'array',
            default: [],
            description: '记忆标签'
          },
          importance: {
            type: 'number',
            default: 0.5,
            description: '重要性评分 (0-1)'
          }
        },
        handler: this.handleMemoryAdd.bind(this)
      },
      {
        name: 'memory_stats',
        description: '获取记忆统计',
        parameters: {},
        handler: this.handleMemoryStats.bind(this)
      },
      {
        name: 'memory_context',
        description: '获取当前对话上下文记忆',
        parameters: {
          recentOnly: {
            type: 'boolean',
            default: true,
            description: '仅获取最近记忆'
          }
        },
        handler: this.handleMemoryContext.bind(this)
      }
    ];
    
    console.log('✅ 工具注册完成:', this.tools.map(t => t.name).join(', '));
  }
  
  /**
   * 设置 UI 集成
   */
  setupUI() {
    if (this.mode !== 'integrated' || !this.config.ui.showMemoryPanel) return;
    
    console.log('🎨 设置 UI 集成...');
    
    this.uiComponents = {
      // 记忆面板
      memoryPanel: {
        type: 'sidebar',
        position: 'right',
        title: '记忆库',
        components: [
          {
            type: 'search',
            placeholder: '搜索记忆...',
            action: 'memory_search'
          },
          {
            type: 'list',
            source: 'recent_memories',
            itemTemplate: 'memory_item'
          },
          {
            type: 'button',
            text: '添加记忆',
            action: 'open_memory_editor'
          }
        ]
      },
      
      // 上下文提示
      contextHints: {
        enabled: this.config.ui.memorySuggestions,
        position: 'inline',
        trigger: 'auto',
        maxSuggestions: 3
      },
      
      // 记忆编辑器
      memoryEditor: {
        type: 'modal',
        fields: [
          { name: 'content', type: 'textarea', label: '内容', required: true },
          { name: 'tags', type: 'tags', label: '标签' },
          { name: 'importance', type: 'slider', label: '重要性', min: 0, max: 1, step: 0.1 }
        ]
      }
    };
    
    console.log('✅ UI 集成设置完成');
  }
  
  /**
   * Hook 处理函数
   */
  
  // 会话开始
  async handleSessionStart(event) {
    console.log(`🔄 会话开始: ${event.sessionId}`);
    
    if (!this.config.automation.contextAware) return;
    
    // 加载会话相关记忆
    const sessionMemories = await this.loadSessionMemories(event.sessionId);
    
    return {
      memories: sessionMemories,
      context: {
        sessionId: event.sessionId,
        userId: event.userId,
        timestamp: new Date().toISOString()
      }
    };
  }
  
  // 消息接收
  async handleMessageReceived(event) {
    if (!this.config.automation.autoCapture) return;
    
    const message = event.message;
    const session = event.session;
    
    // 简单的重要性过滤
    if (this.config.automation.importanceFilter) {
      const importance = this.scoreMessageImportance(message);
      if (importance < 0.3) {
        console.log(`⏭️ 跳过低重要性消息: ${importance.toFixed(2)}`);
        return;
      }
    }
    
    // 自动捕获重要消息
    await this.autoCaptureMessage(message, session);
    
    return { processed: true, timestamp: Date.now() };
  }
  
  // 提示构建前（自动召回）
  async handleBeforePromptBuild(event) {
    if (!this.config.automation.autoRecall) return;
    
    console.log(`🔍 自动召回相关记忆...`);
    
    const query = event.prompt || event.message?.text || '';
    const context = {
      sessionId: event.session?.id,
      userId: event.user?.id,
      topic: this.extractTopic(query)
    };
    
    // 召回相关记忆
    const relevantMemories = await this.recallRelevantMemories(query, context);
    
    // 格式化记忆为上下文
    const memoryContext = this.formatMemoriesForContext(relevantMemories);
    
    return {
      memories: relevantMemories,
      context: memoryContext,
      recallCount: relevantMemories.length
    };
  }
  
  // 代理结束
  async handleAgentEnd(event) {
    if (!this.config.automation.autoCapture) return;
    
    console.log(`💾 会话结束，自动捕获总结...`);
    
    const session = event.session;
    const messages = event.messages || [];
    
    // 捕获会话总结
    await this.captureSessionSummary(session, messages);
    
    return { captured: true, timestamp: Date.now() };
  }
  
  // 错误处理
  async handleError(event) {
    console.error(`❌ 错误发生: ${event.error.message}`);
    
    // 记录错误到记忆
    await this.captureError(event.error, event.context);
    
    return {
      handled: true,
      recovery: 'error_logged',
      suggestion: '检查记忆库了解类似错误解决方案'
    };
  }
  
  /**
   * 工具处理函数
   */
  
  // 记忆搜索
  async handleMemorySearch(params) {
    const { query, limit, tags } = params;
    
    console.log(`🔍 工具调用: memory_search "${query}"`);
    
    // 这里应该调用实际的记忆搜索
    const results = await this.searchMemories(query, { limit, tags });
    
    return {
      success: true,
      query,
      results,
      count: results.length,
      timestamp: new Date().toISOString()
    };
  }
  
  // 添加记忆
  async handleMemoryAdd(params) {
    const { content, tags, importance } = params;
    
    console.log(`➕ 工具调用: memory_add`);
    
    const memory = {
      id: `manual_${Date.now()}`,
      content,
      tags,
      importance,
      source: 'manual',
      timestamp: Date.now(),
      createdAt: new Date().toISOString()
    };
    
    // 保存记忆
    await this.saveMemory(memory);
    
    return {
      success: true,
      memory,
      message: '记忆添加成功'
    };
  }
  
  // 记忆统计
  async handleMemoryStats() {
    console.log(`📊 工具调用: memory_stats`);
    
    const stats = await this.getMemoryStats();
    
    return {
      success: true,
      stats,
      timestamp: new Date().toISOString()
    };
  }
  
  // 上下文记忆
  async handleMemoryContext(params) {
    const { recentOnly } = params;
    
    console.log(`🔄 工具调用: memory_context`);
    
    const contextMemories = await this.getContextMemories(recentOnly);
    
    return {
      success: true,
      memories: contextMemories,
      count: contextMemories.length,
      recentOnly
    };
  }
  
  /**
   * 辅助方法
   */
  
  // 评分消息重要性
  scoreMessageImportance(message) {
    const content = message.text || message.content || '';
    let score = 0;
    
    // 长度因素
    score += Math.min(content.length / 500, 0.3);
    
    // 问题因素
    if (content.includes('?') || content.includes('？')) score += 0.2;
    
    // 关键词因素
    const importantWords = ['重要', '关键', '记住', '备忘', 'note'];
    importantWords.forEach(word => {
      if (content.includes(word)) score += 0.1;
    });
    
    // 指令因素
    if (content.includes('请') || content.includes('帮我')) score += 0.1;
    
    return Math.min(score, 1.0);
  }
  
  // 提取主题
  extractTopic(content) {
    const topics = {
      '技术': ['代码', '程序', 'bug', '错误', '修复', '系统', '配置'],
      '需求': ['需要', '想要', '希望', '功能', '特性', '改进'],
      '咨询': ['怎么', '如何', '为什么', '什么', '哪', '谁'],
      '决策': ['决定', '选择', '方案', '计划', '建议']
    };
    
    for (const [topic, keywords] of Object.entries(topics)) {
      if (keywords.some(keyword => content.includes(keyword))) {
        return topic;
      }
    }
    
    return '其他';
  }
  
  // 格式化记忆为上下文
  formatMemoriesForContext(memories) {
    if (!memories || memories.length === 0) return '';
    
    const memoryTexts = memories.map((memory, index) => {
      return `记忆 ${index + 1}: ${memory.summary || memory.content.substring(0, 100)}`;
    });
    
    return `相关记忆 (${memories.length} 条):\n${memoryTexts.join('\n')}`;
  }
  
  /**
   * 存储相关方法（应该调用实际的存储系统）
   */
  
  async loadSessionMemories(sessionId) {
    // 模拟实现
    return [
      {
        id: 'session_memory_1',
        content: `会话 ${sessionId} 的相关记忆`,
        timestamp: Date.now() - 3600000 // 1小时前
      }
    ];
  }
  
  async autoCaptureMessage(message, session) {
    console.log(`💾 自动捕获消息: ${message.text?.substring(0, 50)}...`);
    // 实际实现应该调用 AutoManager
    return { success: true };
  }
  
  async recallRelevantMemories(query, context) {
    // 模拟实现
    return [
      {
        id: 'relevant_1',
        content: `与 "${query.substring(0, 30)}..." 相关的记忆`,
        relevance: 0.8,
        timestamp: Date.now() - 1800000 // 30分钟前
      }
    ];
  }
  
  async captureSessionSummary(session, messages) {
    console.log(`📝 捕获会话总结: ${session.id}, ${messages.length} 条消息`);
    // 实际实现应该调用 AutoManager
    return { success: true };
  }
  
  async captureError(error, context) {
    console.log(`📋 记录错误到记忆: ${error.message}`);
    // 实际实现应该保存错误信息
    return { success: true };
  }
  
  async searchMemories(query, options) {
    // 模拟实现
    return [
      {
        id: 'search_result_1',
        content: `搜索结果: ${query}`,
        relevance: 0.9,
        timestamp: Date.now()
      }
    ];
  }
  
  async saveMemory(memory) {
    console.log(`💾 保存记忆: ${memory.id}`);
    // 实际实现应该调用存储系统
    return { success: true, memory };
  }
  
  async getMemoryStats() {
    // 模拟实现
    return {
      total: 42,
      bySource: { auto: 30, manual: 12 },
      byTag: { '技术': 15, '需求': 10, '咨询': 12, '其他': 5 },
      storageSize: '15.3KB',
      lastUpdated: new Date().toISOString()
    };
  }
  
  async getContextMemories(recentOnly) {
    // 模拟实现
    return [
      {
        id: 'context_1',
        content: '当前对话上下文记忆',
        timestamp: Date.now() - 300000 // 5分钟前
      }
    ];
  }
  
  /**
   * 获取插件信息
   */
  getPluginInfo() {
    return {
      name: this.name,
      version: this.version,
      description: this.description,
      mode: this.mode,
      config: {
        integration: this.config.integration.enabled,
        automation: {
          autoCapture: this.config.automation.autoCapture,
          autoRecall: this.config.automation.autoRecall
        },
        tools: this.tools?.length || 0,
        hooks: Object.keys(this.hooks || {}).length
      }
    };
  }
}

// 导出
module.exports = OpenClawPlugin;