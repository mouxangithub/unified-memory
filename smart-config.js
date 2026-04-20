/**
 * Unified Memory 智能配置系统
 * 开箱即用，环境自适应
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

class SmartConfig {
  constructor() {
    this.configPath = path.join(__dirname, 'config.json');
    this.detectedEnv = this.detectEnvironment();
    this.defaultConfig = this.generateDefaultConfig();
  }
  
  /**
   * 检测运行环境
   */
  detectEnvironment() {
    console.log('🔍 检测运行环境...');
    
    const env = {
      // 操作系统
      os: {
        platform: os.platform(),
        arch: os.arch(),
        homedir: os.homedir()
      },
      
      // 运行时环境
      runtime: {
        nodeVersion: process.version,
        hasPython: this.checkPython(),
        hasNpm: this.checkNpm(),
        memory: os.totalmem() / 1024 / 1024 / 1024 // GB
      },
      
      // 应用环境
      application: {
        isOpenClaw: this.checkOpenClaw(),
        isDevelopment: process.env.NODE_ENV === 'development',
        isProduction: process.env.NODE_ENV === 'production',
        isTesting: process.env.NODE_ENV === 'test'
      },
      
      // 用户环境
      user: {
        hasWritePermission: this.checkWritePermission(),
        preferredLanguage: process.env.LANG || 'zh-CN',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      }
    };
    
    console.log('✅ 环境检测完成:', {
      platform: env.os.platform,
      node: env.runtime.nodeVersion,
      python: env.runtime.hasPython,
      openclaw: env.application.isOpenClaw,
      memory: `${env.runtime.memory.toFixed(1)}GB`
    });
    
    return env;
  }
  
  /**
   * 检查 Python 可用性
   */
  checkPython() {
    try {
      const { execSync } = require('child_process');
      execSync('python3 --version', { stdio: 'ignore' });
      return true;
    } catch {
      try {
        const { execSync } = require('child_process');
        execSync('python --version', { stdio: 'ignore' });
        return true;
      } catch {
        return false;
      }
    }
  }
  
  /**
   * 检查 npm 可用性
   */
  checkNpm() {
    try {
      const { execSync } = require('child_process');
      execSync('npm --version', { stdio: 'ignore' });
      return true;
    } catch {
      return false;
    }
  }
  
  /**
   * 检查 OpenClaw 环境
   */
  checkOpenClaw() {
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
   * 检查写入权限
   */
  checkWritePermission() {
    try {
      const testFile = path.join(__dirname, '.write-test');
      fs.writeFileSync(testFile, 'test');
      fs.unlinkSync(testFile);
      return true;
    } catch {
      return false;
    }
  }
  
  /**
   * 生成智能默认配置
   */
  generateDefaultConfig() {
    const env = this.detectedEnv;
    
    const config = {
      // 基础配置
      version: '6.0.0',
      mode: this.determineMode(env),
      
      // 存储配置
      storage: {
        type: this.determineStorageType(env),
        path: this.determineStoragePath(env),
        backup: true,
        backupCount: 3
      },
      
      // 搜索配置
      search: {
        type: this.determineSearchType(env),
        fallback: 'text',
        limit: 10
      },
      
      // 自动化配置
      auto: {
        enabled: env.application.isOpenClaw,
        capture: env.application.isOpenClaw,
        recall: env.application.isOpenClaw,
        contextWindow: env.application.isOpenClaw ? 15 : 5
      },
      
      // 性能配置
      performance: {
        cache: env.runtime.memory > 4, // 内存大于4GB启用缓存
        compression: true,
        batchSize: env.application.isProduction ? 100 : 10
      },
      
      // 错误处理
      errorHandling: {
        friendly: true,
        autoRecover: true,
        logLevel: env.application.isProduction ? 'error' : 'debug'
      },
      
      // 集成配置
      integrations: {
        openclaw: env.application.isOpenClaw,
        mcp: env.runtime.hasPython,
        cli: true
      }
    };
    
    return config;
  }
  
  /**
   * 确定运行模式
   */
  determineMode(env) {
    if (!env.runtime.hasPython) {
      return 'node-only';
    }
    
    if (env.application.isOpenClaw) {
      return 'openclaw-integrated';
    }
    
    if (env.runtime.memory < 2) {
      return 'lite';
    }
    
    return 'standard';
  }
  
  /**
   * 确定存储类型
   */
  determineStorageType(env) {
    if (env.runtime.hasPython && env.runtime.memory > 2) {
      return 'sqlite';
    }
    
    if (env.application.isProduction) {
      return 'json';
    }
    
    return 'memory';
  }
  
  /**
   * 确定存储路径
   */
  determineStoragePath(env) {
    if (!env.user.hasWritePermission) {
      return path.join(os.tmpdir(), 'unified-memory');
    }
    
    if (env.application.isOpenClaw) {
      return path.join(env.os.homedir(), '.openclaw', 'memories');
    }
    
    return path.join(__dirname, 'storage');
  }
  
  /**
   * 确定搜索类型
   */
  determineSearchType(env) {
    if (env.runtime.hasPython && env.runtime.memory > 4) {
      return 'hybrid';
    }
    
    if (env.runtime.memory > 2) {
      return 'vector';
    }
    
    return 'text';
  }
  
  /**
   * 加载或创建配置
   */
  loadOrCreate() {
    try {
      if (fs.existsSync(this.configPath)) {
        const savedConfig = JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
        
        // 合并配置，优先使用保存的配置
        const mergedConfig = {
          ...this.defaultConfig,
          ...savedConfig,
          storage: {
            ...this.defaultConfig.storage,
            ...(savedConfig.storage || {})
          },
          search: {
            ...this.defaultConfig.search,
            ...(savedConfig.search || {})
          }
        };
        
        console.log('📂 加载现有配置');
        return mergedConfig;
      }
    } catch (error) {
      console.warn('⚠️ 配置加载失败，使用默认配置:', error.message);
    }
    
    // 保存默认配置
    this.saveConfig(this.defaultConfig);
    console.log('🆕 创建新配置');
    return this.defaultConfig;
  }
  
  /**
   * 保存配置
   */
  saveConfig(config) {
    try {
      const dir = path.dirname(this.configPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      fs.writeFileSync(this.configPath, JSON.stringify(config, null, 2));
      console.log('💾 配置已保存:', this.configPath);
      return true;
    } catch (error) {
      console.error('❌ 配置保存失败:', error.message);
      return false;
    }
  }
  
  /**
   * 获取配置摘要
   */
  getConfigSummary(config) {
    return {
      mode: config.mode,
      storage: `${config.storage.type} (${config.storage.path})`,
      search: config.search.type,
      auto: config.auto.enabled ? '启用' : '禁用',
      memory: `${this.detectedEnv.runtime.memory.toFixed(1)}GB`,
      python: this.detectedEnv.runtime.hasPython ? '可用' : '不可用',
      openclaw: this.detectedEnv.application.isOpenClaw ? '已集成' : '未集成'
    };
  }
}

// 创建并导出单例
const configManager = new SmartConfig();
const config = configManager.loadOrCreate();

module.exports = {
  SmartConfig,
  config,
  configManager,
  
  // 快捷方法
  getConfig: () => config,
  getSummary: () => configManager.getConfigSummary(config),
  updateConfig: (updates) => {
    Object.assign(config, updates);
    return configManager.saveConfig(config);
  }
};