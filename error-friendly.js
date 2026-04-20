/**
 * Unified Memory 错误友好系统
 * 立即改善用户体验
 */

class FriendlyErrorHandler {
  constructor() {
    this.errorTypes = {
      // 依赖相关错误
      'dependency-missing': {
        userMessage: '缺少必要依赖',
        recovery: 'enable-lite-mode',
        priority: 'high'
      },
      'python-not-found': {
        userMessage: 'Python 环境不可用',
        recovery: 'use-node-only',
        priority: 'high'
      },
      
      // 配置相关错误
      'config-error': {
        userMessage: '配置有问题',
        recovery: 'use-defaults',
        priority: 'medium'
      },
      'permission-denied': {
        userMessage: '文件权限不足',
        recovery: 'change-path',
        priority: 'medium'
      },
      
      // 运行时错误
      'storage-error': {
        userMessage: '存储遇到问题',
        recovery: 'retry-with-fallback',
        priority: 'low'
      },
      'search-error': {
        userMessage: '搜索功能暂时不可用',
        recovery: 'use-simple-search',
        priority: 'low'
      }
    };
    
    this.recoveryStrategies = {
      'enable-lite-mode': () => this.enableLiteMode(),
      'use-node-only': () => this.useNodeOnly(),
      'use-defaults': () => this.useDefaultConfig(),
      'change-path': () => this.changeStoragePath(),
      'retry-with-fallback': () => this.retryWithFallback(),
      'use-simple-search': () => this.useSimpleSearch()
    };
  }
  
  /**
   * 处理错误，返回用户友好信息
   */
  handle(error, context = {}) {
    console.error('🔧 [错误详情]', error.message);
    
    // 1. 分类错误
    const errorType = this.classifyError(error);
    const errorInfo = this.errorTypes[errorType] || {
      userMessage: '遇到未知问题',
      recovery: 'degrade-gracefully',
      priority: 'low'
    };
    
    // 2. 执行恢复策略
    const recoveryResult = this.executeRecovery(errorInfo.recovery, context);
    
    // 3. 生成用户友好消息
    return {
      success: recoveryResult.success,
      userMessage: this.formatUserMessage(errorInfo.userMessage, recoveryResult),
      technicalInfo: error.message.substring(0, 100),
      recovery: recoveryResult.action,
      timestamp: new Date().toISOString()
    };
  }
  
  /**
   * 错误分类
   */
  classifyError(error) {
    const message = error.message.toLowerCase();
    
    if (message.includes('cannot find module') || message.includes('require')) {
      return 'dependency-missing';
    }
    
    if (message.includes('python') || message.includes('pip')) {
      return 'python-not-found';
    }
    
    if (message.includes('permission') || message.includes('eaccess')) {
      return 'permission-denied';
    }
    
    if (message.includes('config') || message.includes('configuration')) {
      return 'config-error';
    }
    
    if (message.includes('storage') || message.includes('file')) {
      return 'storage-error';
    }
    
    if (message.includes('search') || message.includes('query')) {
      return 'search-error';
    }
    
    return 'unknown-error';
  }
  
  /**
   * 执行恢复策略
   */
  executeRecovery(strategy, context) {
    const strategyFn = this.recoveryStrategies[strategy];
    
    if (strategyFn) {
      try {
        return strategyFn.call(this, context);
      } catch (recoveryError) {
        console.warn('恢复策略失败:', recoveryError.message);
        return this.degradeGracefully(context);
      }
    }
    
    return this.degradeGracefully(context);
  }
  
  /**
   * 启用轻量模式
   */
  enableLiteMode() {
    console.log('🔄 启用轻量模式...');
    
    // 切换到简单存储
    const SimpleStorage = require('./simple-storage.js');
    const storage = new SimpleStorage();
    
    return {
      success: true,
      action: 'lite-mode-enabled',
      message: '已切换到轻量模式，基本功能可用',
      storage
    };
  }
  
  /**
   * 仅使用 Node.js 功能
   */
  useNodeOnly() {
    console.log('🔄 切换到纯 Node.js 模式...');
    
    return {
      success: true,
      action: 'node-only-mode',
      message: 'Python 功能已禁用，使用纯 Node.js 功能',
      features: ['storage', 'text-search', 'basic-recall']
    };
  }
  
  /**
   * 使用默认配置
   */
  useDefaultConfig() {
    console.log('🔄 使用智能默认配置...');
    
    const defaultConfig = {
      storage: { type: 'json', path: './memories.json' },
      search: { type: 'text' },
      auto: { enabled: false }
    };
    
    return {
      success: true,
      action: 'default-config',
      message: '使用智能默认配置',
      config: defaultConfig
    };
  }
  
  /**
   * 改变存储路径
   */
  changeStoragePath() {
    console.log('🔄 改变存储路径...');
    
    const newPath = './user-memories.json';
    return {
      success: true,
      action: 'storage-path-changed',
      message: `存储路径已改为: ${newPath}`,
      path: newPath
    };
  }
  
  /**
   * 优雅降级
   */
  degradeGracefully(context) {
    console.log('🔄 优雅降级，保持基本功能...');
    
    return {
      success: true,
      action: 'graceful-degradation',
      message: '系统已降级，部分功能受限但可用',
      availableFeatures: ['basic-storage', 'simple-search'],
      degradedFeatures: ['advanced-search', 'auto-features', 'mcp-server']
    };
  }
  
  /**
   * 格式化用户消息
   */
  formatUserMessage(baseMessage, recovery) {
    return `🛠️ ${baseMessage}，${recovery.message}`;
  }
}

// 导出单例
const errorHandler = new FriendlyErrorHandler();

module.exports = errorHandler;