/**
 * Unified Memory Plugin System
 * 完整的插件系统实现，支持热重载、依赖管理、生命周期管理
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const require = createRequire(import.meta.url);

// ========== 1. 插件接口定义 ==========
const PLUGIN_INTERFACE = {
  name: 'string',
  version: 'string',
  description: 'string',
  author: 'string (optional)',
  dependencies: 'array (optional)',
  hooks: 'object (optional)',
  initialize: 'function (optional)',
  destroy: 'function (optional)'
};

// ========== 2. 插件验证器 ==========
class PluginValidator {
  static validate(plugin, strict = false) {
    const errors = [];
    
    // 必须字段
    if (!plugin.name || typeof plugin.name !== 'string') {
      errors.push('Plugin must have a valid name (string)');
    }
    
    if (!plugin.version || typeof plugin.version !== 'string') {
      errors.push('Plugin must have a valid version (string)');
    }
    
    // 版本格式验证 (semver)
    if (plugin.version && !/^\d+\.\d+(\.\d+)?/.test(plugin.version)) {
      errors.push('Version must follow semver format (e.g., 1.0.0)');
    }
    
    // 钩子格式验证
    if (plugin.hooks && typeof plugin.hooks !== 'object') {
      errors.push('Hooks must be an object');
    } else if (plugin.hooks) {
      const validHooks = ['beforeSave', 'afterSave', 'beforeSearch', 'afterSearch', 'beforeLoad', 'afterLoad', 'beforeDelete', 'afterDelete'];
      Object.keys(plugin.hooks).forEach(hookName => {
        if (!validHooks.includes(hookName)) {
          errors.push(`Unknown hook: ${hookName}`);
        }
        if (typeof plugin.hooks[hookName] !== 'function') {
          errors.push(`Hook ${hookName} must be a function`);
        }
      });
    }
    
    // 依赖格式验证
    if (plugin.dependencies) {
      if (!Array.isArray(plugin.dependencies)) {
        errors.push('Dependencies must be an array');
      } else {
        plugin.dependencies.forEach(dep => {
          if (typeof dep !== 'string') {
            errors.push('Each dependency must be a string');
          }
        });
      }
    }
    
    // 严格模式额外检查
    if (strict) {
      if (!plugin.description) {
        errors.push('Plugin should have a description (strict mode)');
      }
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  static checkSecurity(plugin) {
    const warnings = [];
    
    // 检查危险操作
    if (plugin._raw && plugin._raw.includes('eval(')) {
      warnings.push('Plugin contains eval() - potential security risk');
    }
    
    if (plugin._raw && plugin._raw.includes('Function(')) {
      warnings.push('Plugin contains Function() constructor - potential security risk');
    }
    
    // 检查文件系统访问
    if (plugin._raw && (plugin._raw.includes('fs.writeFileSync') || plugin._raw.includes('fs.unlinkSync'))) {
      warnings.push('Plugin has write access to filesystem');
    }
    
    return {
      safe: warnings.length === 0,
      warnings
    };
  }
}

// ========== 3. 插件加载器 ==========
class PluginLoader {
  constructor(pluginDir, validator = new PluginValidator()) {
    this.pluginDir = pluginDir;
    this.validator = validator;
    this.loadedPlugins = new Map();
  }
  
  // 加载本地文件插件
  async loadFromFile(filePath) {
    try {
      const fullPath = path.resolve(filePath);
      
      if (!fs.existsSync(fullPath)) {
        throw new Error(`Plugin file not found: ${fullPath}`);
      }
      
      // 动态导入插件
      const plugin = await import(`file://${fullPath}?t=${Date.now()}`);
      const pluginModule = plugin.default || plugin;
      
      // 验证插件
      const validation = PluginValidator.validate(pluginModule);
      if (!validation.valid) {
        throw new Error(`Plugin validation failed: ${validation.errors.join(', ')}`);
      }
      
      // 安全检查
      const security = PluginValidator.checkSecurity(pluginModule);
      if (!security.safe) {
        console.warn(`⚠️  Security warnings for ${pluginModule.name}:`, security.warnings);
      }
      
      return {
        name: pluginModule.name,
        version: pluginModule.version,
        module: pluginModule,
        path: fullPath,
        loadedAt: Date.now()
      };
      
    } catch (error) {
      throw new Error(`Failed to load plugin from ${filePath}: ${error.message}`);
    }
  }
  
  // 加载目录中的所有插件
  async loadFromDirectory(dirPath = this.pluginDir) {
    const results = {
      loaded: [],
      failed: []
    };
    
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
      return results;
    }
    
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });
    
    for (const entry of entries) {
      if (entry.isDirectory()) {
        // 检查目录中是否有 index.js 或同名 .js 文件
        const indexPath = path.join(dirPath, entry.name, 'index.js');
        const mainPath = path.join(dirPath, entry.name, `${entry.name}.js`);
        
        let pluginPath = null;
        if (fs.existsSync(indexPath)) {
          pluginPath = indexPath;
        } else if (fs.existsSync(mainPath)) {
          pluginPath = mainPath;
        }
        
        if (pluginPath) {
          try {
            const loaded = await this.loadFromFile(pluginPath);
            results.loaded.push(loaded);
            this.loadedPlugins.set(loaded.name, loaded);
          } catch (error) {
            results.failed.push({ name: entry.name, error: error.message });
          }
        }
      } else if (entry.name.endsWith('.js') && entry.name !== 'plugin-system.js') {
        try {
          const fullPath = path.join(dirPath, entry.name);
          const loaded = await this.loadFromFile(fullPath);
          results.loaded.push(loaded);
          this.loadedPlugins.set(loaded.name, loaded);
        } catch (error) {
          results.failed.push({ name: entry.name, error: error.message });
        }
      }
    }
    
    return results;
  }
  
  // 远程插件加载（预留接口）
  async loadFromURL(url, options = {}) {
    console.warn('🔌 Remote plugin loading is not yet implemented');
    // TODO: 实现远程插件加载
    // 1. 下载插件代码
    // 2. 验证签名
    // 3. 沙箱执行
    // 4. 返回插件模块
    return null;
  }
  
  // 卸载插件
  unload(pluginName) {
    if (this.loadedPlugins.has(pluginName)) {
      this.loadedPlugins.delete(pluginName);
      return true;
    }
    return false;
  }
  
  // 获取已加载插件
  getLoaded() {
    return Array.from(this.loadedPlugins.values());
  }
}

// ========== 4. 插件依赖解析器 ==========
class DependencyResolver {
  constructor() {
    this.pluginRegistry = new Map();
  }
  
  register(plugin) {
    this.pluginRegistry.set(plugin.name, plugin);
  }
  
  unregister(pluginName) {
    this.pluginRegistry.delete(pluginName);
  }
  
  // 解析依赖并返回加载顺序
  resolveLoadOrder(plugins) {
    const visited = new Set();
    const order = [];
    const visiting = new Set();
    const errors = [];
    
    const visit = (pluginName) => {
      if (visited.has(pluginName)) return true;
      if (visiting.has(pluginName)) {
        errors.push(`Circular dependency detected: ${pluginName}`);
        return false;
      }
      
      visiting.add(pluginName);
      
      const plugin = this.pluginRegistry.get(pluginName);
      if (!plugin) {
        errors.push(`Plugin not found: ${pluginName}`);
        return false;
      }
      
      if (plugin.dependencies) {
        for (const dep of plugin.dependencies) {
          if (!visit(dep)) {
            return false;
          }
        }
      }
      
      visiting.delete(pluginName);
      visited.add(pluginName);
      order.push(pluginName);
      
      return true;
    };
    
    // 按依赖关系排序
    const sorted = this.topoSort(plugins);
    
    for (const plugin of sorted) {
      if (!visit(plugin.name)) {
        return { order: [], errors };
      }
    }
    
    return { order, errors: [] };
  }
  
  // 拓扑排序
  topoSort(plugins) {
    const inDegree = new Map();
    const adjList = new Map();
    
    // 初始化
    plugins.forEach(p => {
      inDegree.set(p.name, 0);
      adjList.set(p.name, []);
    });
    
    // 构建依赖图
    plugins.forEach(p => {
      if (p.dependencies) {
        p.dependencies.forEach(dep => {
          if (inDegree.has(dep)) {
            adjList.get(dep).push(p.name);
            inDegree.set(p.name, inDegree.get(p.name) + 1);
          }
        });
      }
    });
    
    // Kahn算法
    const queue = [];
    inDegree.forEach((degree, name) => {
      if (degree === 0) queue.push(name);
    });
    
    const result = [];
    while (queue.length > 0) {
      const node = queue.shift();
      result.push(this.pluginRegistry.get(node));
      
      adjList.get(node).forEach(neighbor => {
        inDegree.set(neighbor, inDegree.get(neighbor) - 1);
        if (inDegree.get(neighbor) === 0) {
          queue.push(neighbor);
        }
      });
    }
    
    return result;
  }
  
  // 检查依赖是否满足
  checkDependencies(plugin) {
    if (!plugin.dependencies || plugin.dependencies.length === 0) {
      return { satisfied: true, missing: [] };
    }
    
    const missing = [];
    plugin.dependencies.forEach(dep => {
      if (!this.pluginRegistry.has(dep)) {
        missing.push(dep);
      }
    });
    
    return {
      satisfied: missing.length === 0,
      missing
    };
  }
}

// ========== 5. 插件生命周期管理器 ==========
class PluginLifecycleManager {
  constructor() {
    this.states = new Map(); // pluginName -> state
    this.listeners = new Map();
  }
  
  // 初始化插件
  async initializePlugin(plugin) {
    try {
      if (typeof plugin.initialize === 'function') {
        const context = this.createContext(plugin);
        await plugin.initialize(context);
      }
      
      this.states.set(plugin.name, {
        status: 'active',
        activatedAt: Date.now(),
        error: null
      });
      
      this.emit('initialized', { plugin: plugin.name });
      return true;
    } catch (error) {
      this.states.set(plugin.name, {
        status: 'error',
        error: error.message,
        failedAt: Date.now()
      });
      throw error;
    }
  }
  
  // 销毁插件
  async destroyPlugin(plugin) {
    const state = this.states.get(plugin.name);
    if (!state || state.status !== 'active') {
      return false;
    }
    
    try {
      if (typeof plugin.destroy === 'function') {
        const context = this.createContext(plugin);
        await plugin.destroy(context);
      }
      
      this.states.set(plugin.name, {
        status: 'destroyed',
        destroyedAt: Date.now()
      });
      
      this.emit('destroyed', { plugin: plugin.name });
      return true;
    } catch (error) {
      this.states.set(plugin.name, {
        status: 'error',
        error: error.message,
        failedAt: Date.now()
      });
      throw error;
    }
  }
  
  // 创建插件上下文
  createContext(plugin) {
    return {
      name: plugin.name,
      version: plugin.version,
      config: plugin.config || {},
      setState: (key, value) => this.setPluginState(plugin.name, key, value),
      getState: (key) => this.getPluginState(plugin.name, key),
      emit: (event, data) => this.emitToPlugin(plugin.name, event, data),
      on: (event, handler) => this.addPluginListener(plugin.name, event, handler)
    };
  }
  
  // 设置插件状态
  setPluginState(pluginName, key, value) {
    if (!this.states.has(pluginName)) {
      this.states.set(pluginName, { status: 'unknown' });
    }
    if (!this.states.get(pluginName).data) {
      this.states.get(pluginName).data = {};
    }
    this.states.get(pluginName).data[key] = value;
  }
  
  // 获取插件状态
  getPluginState(pluginName, key) {
    const state = this.states.get(pluginName);
    if (state && state.data) {
      return state.data[key];
    }
    return null;
  }
  
  // 添加生命周期监听器
  on(event, handler) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(handler);
  }
  
  // 发送事件
  emit(event, data) {
    const handlers = this.listeners.get(event) || [];
    handlers.forEach(handler => handler(data));
  }
  
  // 向特定插件发送事件
  emitToPlugin(pluginName, event, data) {
    const handlers = this.listeners.get(`${pluginName}:${event}`) || [];
    handlers.forEach(handler => handler(data));
  }
  
  // 添加插件特定监听器
  addPluginListener(pluginName, event, handler) {
    const key = `${pluginName}:${event}`;
    if (!this.listeners.has(key)) {
      this.listeners.set(key, []);
    }
    this.listeners.get(key).push(handler);
  }
  
  // 获取插件状态
  getState(pluginName) {
    return this.states.get(pluginName) || { status: 'unknown' };
  }
  
  // 获取所有活跃插件
  getActivePlugins() {
    const active = [];
    this.states.forEach((state, name) => {
      if (state.status === 'active') {
        active.push(name);
      }
    });
    return active;
  }
}

// ========== 6. 配置管理器 ==========
class PluginConfigManager {
  constructor(configDir) {
    this.configDir = configDir || path.join(__dirname, 'config');
    this.configs = new Map();
    
    if (!fs.existsSync(this.configDir)) {
      fs.mkdirSync(this.configDir, { recursive: true });
    }
  }
  
  // 加载插件配置
  loadConfig(pluginName) {
    const configPath = path.join(this.configDir, `${pluginName}.json`);
    
    if (fs.existsSync(configPath)) {
      try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        this.configs.set(pluginName, config);
        return config;
      } catch (error) {
        throw new Error(`Failed to load config for ${pluginName}: ${error.message}`);
      }
    }
    
    return null;
  }
  
  // 保存插件配置
  saveConfig(pluginName, config) {
    const configPath = path.join(this.configDir, `${pluginName}.json`);
    
    try {
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf8');
      this.configs.set(pluginName, config);
      return true;
    } catch (error) {
      throw new Error(`Failed to save config for ${pluginName}: ${error.message}`);
    }
  }
  
  // 更新配置（热更新）
  updateConfig(pluginName, updates) {
    const current = this.loadConfig(pluginName) || {};
    const updated = { ...current, ...updates };
    return this.saveConfig(pluginName, updated);
  }
  
  // 删除配置
  deleteConfig(pluginName) {
    const configPath = path.join(this.configDir, `${pluginName}.json`);
    
    if (fs.existsSync(configPath)) {
      fs.unlinkSync(configPath);
    }
    
    this.configs.delete(pluginName);
    return true;
  }
  
  // 获取配置
  getConfig(pluginName) {
    if (this.configs.has(pluginName)) {
      return this.configs.get(pluginName);
    }
    return this.loadConfig(pluginName);
  }
  
  // 获取所有配置
  getAllConfigs() {
    return Object.fromEntries(this.configs);
  }
}

// ========== 7. 热重载管理器 ==========
class HotReloadManager {
  constructor(pluginManager, lifecycleManager) {
    this.pluginManager = pluginManager;
    this.lifecycleManager = lifecycleManager;
    this.watchers = new Map();
    this.rollbackState = new Map();
  }
  
  // 启用热重载
  enableHotReload(pluginName, filePath) {
    if (this.watchers.has(pluginName)) {
      this.watchers.get(pluginName).close();
    }
    
    const watcher = fs.watch(filePath, async (eventType) => {
      if (eventType === 'change') {
        console.log(`🔄 Hot reload triggered for ${pluginName}`);
        await this.reloadPlugin(pluginName, filePath);
      }
    });
    
    this.watchers.set(pluginName, watcher);
    console.log(`👁️  Watching ${pluginName} for changes`);
  }
  
  // 禁用热重载
  disableHotReload(pluginName) {
    if (this.watchers.has(pluginName)) {
      this.watchers.get(pluginName).close();
      this.watchers.delete(pluginName);
      console.log(`⏹️  Stopped watching ${pluginName}`);
    }
  }
  
  // 重载插件
  async reloadPlugin(pluginName, filePath) {
    const loader = this.pluginManager.loader;
    const oldPlugin = loader.loadedPlugins.get(pluginName);
    
    // 保存当前状态用于回滚
    if (oldPlugin) {
      this.rollbackState.set(pluginName, {
        plugin: oldPlugin,
        state: this.lifecycleManager.getState(pluginName)
      });
    }
    
    try {
      // 销毁旧插件
      if (oldPlugin && oldPlugin.module) {
        await this.lifecycleManager.destroyPlugin(oldPlugin.module);
      }
      
      // 卸载旧插件
      loader.unload(pluginName);
      
      // 加载新插件
      const newLoaded = await loader.loadFromFile(filePath);
      
      // 初始化新插件
      if (newLoaded.module) {
        await this.lifecycleManager.initializePlugin(newLoaded.module);
      }
      
      console.log(`✅ Plugin ${pluginName} reloaded successfully`);
      return true;
      
    } catch (error) {
      console.error(`❌ Failed to reload ${pluginName}: ${error.message}`);
      await this.rollback(pluginName);
      return false;
    }
  }
  
  // 回滚到旧版本
  async rollback(pluginName) {
    const saved = this.rollbackState.get(pluginName);
    
    if (!saved) {
      console.warn(`⚠️  No rollback state for ${pluginName}`);
      return false;
    }
    
    try {
      console.log(`↩️  Rolling back ${pluginName} to previous version`);
      
      // 重新注册旧插件
      this.pluginManager.registerPlugin(saved.plugin.name, saved.plugin);
      
      // 恢复状态
      if (saved.plugin.module) {
        await this.lifecycleManager.initializePlugin(saved.plugin.module);
      }
      
      this.rollbackState.delete(pluginName);
      return true;
      
    } catch (error) {
      console.error(`❌ Rollback failed for ${pluginName}: ${error.message}`);
      return false;
    }
  }
  
  // 关闭所有 watcher
  closeAll() {
    this.watchers.forEach((watcher, name) => {
      watcher.close();
      console.log(`⏹️  Closed watcher for ${name}`);
    });
    this.watchers.clear();
  }
}

// ========== 8. 完整插件管理器 ==========
class UnifiedPluginManager {
  constructor(options = {}) {
    this.options = {
      pluginDir: options.pluginDir || path.join(__dirname, 'plugins'),
      configDir: options.configDir || path.join(__dirname, 'config'),
      enableHotReload: options.enableHotReload !== false,
      strictValidation: options.strictValidation || false,
      ...options
    };
    
    // 初始化各子系统
    this.validator = new PluginValidator();
    this.loader = new PluginLoader(this.options.pluginDir, this.validator);
    this.depResolver = new DependencyResolver();
    this.lifecycle = new PluginLifecycleManager();
    this.config = new PluginConfigManager(this.options.configDir);
    this.hotReload = new HotReloadManager(this, this.lifecycle);
    
    // 注册的插件
    this.plugins = new Map();
    
    // 钩子
    this.hooks = {
      beforeSave: [],
      afterSave: [],
      beforeSearch: [],
      afterSearch: [],
      beforeLoad: [],
      afterLoad: [],
      beforeDelete: [],
      afterDelete: []
    };
  }
  
  // 注册插件
  async registerPlugin(pluginOrPath, options = {}) {
    let plugin, loaded;
    
    if (typeof pluginOrPath === 'string') {
      // 从文件加载
      loaded = await this.loader.loadFromFile(pluginOrPath);
      plugin = loaded.module;
      plugin._loadedFrom = loaded.path;
    } else {
      // 直接传入插件对象
      plugin = pluginOrPath;
      
      // 验证
      const validation = PluginValidator.validate(plugin, this.options.strictValidation);
      if (!validation.valid) {
        throw new Error(`Plugin validation failed: ${validation.errors.join(', ')}`);
      }
    }
    
    // 检查依赖
    const depCheck = this.depResolver.checkDependencies(plugin);
    if (!depCheck.satisfied) {
      throw new Error(`Missing dependencies: ${depCheck.missing.join(', ')}`);
    }
    
    // 注册到依赖解析器
    this.depResolver.register(plugin);
    
    // 注册到配置管理器
    const config = this.config.loadConfig(plugin.name) || {};
    plugin.config = { ...plugin.defaultConfig, ...config };
    
    // 注册钩子
    if (plugin.hooks) {
      Object.entries(plugin.hooks).forEach(([hookName, handler]) => {
        if (this.hooks[hookName]) {
          this.hooks[hookName].push(handler);
        }
      });
    }
    
    // 存储插件
    this.plugins.set(plugin.name, plugin);
    
    // 初始化插件
    await this.lifecycle.initializePlugin(plugin);
    
    // 启用热重载
    if (this.options.enableHotReload && loaded) {
      this.hotReload.enableHotReload(plugin.name, loaded.path);
    }
    
    console.log(`✅ Plugin registered: ${plugin.name} v${plugin.version}`);
    return plugin;
  }
  
  // 卸载插件
  async unregisterPlugin(pluginName) {
    const plugin = this.plugins.get(pluginName);
    if (!plugin) {
      return false;
    }
    
    // 销毁插件
    await this.lifecycle.destroyPlugin(plugin);
    
    // 移除钩子
    if (plugin.hooks) {
      Object.entries(plugin.hooks).forEach(([hookName, handler]) => {
        if (this.hooks[hookName]) {
          const index = this.hooks[hookName].indexOf(handler);
          if (index > -1) {
            this.hooks[hookName].splice(index, 1);
          }
        }
      });
    }
    
    // 禁用热重载
    this.hotReload.disableHotReload(pluginName);
    
    // 从各管理器移除
    this.plugins.delete(pluginName);
    this.depResolver.unregister(pluginName);
    this.loader.unload(pluginName);
    
    console.log(`🗑️  Plugin unregistered: ${pluginName}`);
    return true;
  }
  
  // 执行钩子
  async executeHook(hookName, ...args) {
    const handlers = this.hooks[hookName] || [];
    const results = [];
    
    for (const handler of handlers) {
      try {
        const result = await handler(...args);
        results.push({ success: true, result });
      } catch (error) {
        results.push({ success: false, error: error.message });
      }
    }
    
    return results;
  }
  
  // 热重载
  async hotReloadPlugin(pluginName) {
    const plugin = this.plugins.get(pluginName);
    if (!plugin || !plugin._loadedFrom) {
      throw new Error(`Plugin ${pluginName} cannot be hot reloaded (not loaded from file)`);
    }
    
    return this.hotReload.reloadPlugin(pluginName, plugin._loadedFrom);
  }
  
  // 列出所有插件
  listPlugins() {
    return Array.from(this.plugins.keys()).map(name => {
      const plugin = this.plugins.get(name);
      const state = this.lifecycle.getState(name);
      return {
        name,
        version: plugin.version,
        description: plugin.description,
        status: state.status,
        dependencies: plugin.dependencies || []
      };
    });
  }
  
  // 获取插件信息
  getPlugin(name) {
    return this.plugins.get(name);
  }
  
  // 加载所有本地插件
  async loadAllPlugins() {
    const results = await this.loader.loadFromDirectory();
    
    // 按依赖顺序加载
    const { order, errors } = this.depResolver.resolveLoadOrder(results.loaded);
    
    if (errors.length > 0) {
      console.warn('⚠️  Dependency errors:', errors);
    }
    
    for (const loaded of order) {
      try {
        await this.registerPlugin(loaded.path);
      } catch (error) {
        console.error(`❌ Failed to register ${loaded.name}: ${error.message}`);
      }
    }
    
    return {
      loaded: this.plugins.size,
      failed: results.failed.length
    };
  }
  
  // 获取状态报告
  getStatusReport() {
    return {
      totalPlugins: this.plugins.size,
      plugins: this.listPlugins(),
      hooks: Object.keys(this.hooks).map(name => ({
        name,
        handlerCount: this.hooks[name].length
      })),
      hotReloadEnabled: this.hotReload.watchers.size,
      lifecycle: {
        active: this.lifecycle.getActivePlugins()
      }
    };
  }
}

// ========== 导出 ==========
export {
  PluginValidator,
  PluginLoader,
  DependencyResolver,
  PluginLifecycleManager,
  PluginConfigManager,
  HotReloadManager,
  UnifiedPluginManager,
  PLUGIN_INTERFACE
};

// 方便直接使用
export default UnifiedPluginManager;
