/**
 * AgentBrain 插件系统 (精简版)
 * 支持插件扩展和模块热加载
 */

/**
 * 插件接口
 */
export class AgentBrainPlugin {
  constructor(name, options = {}) {
    this.name = name;
    this.options = options;
    this.enabled = false;
  }

  // 插件安装时调用
  async install(brain) {
    this.brain = brain;
    this.enabled = true;
  }

  // 插件卸载时调用
  async uninstall() {
    this.enabled = false;
  }

  // 获取插件信息
  getInfo() {
    return { name: this.name, enabled: this.enabled };
  }
}

/**
 * 插件管理器
 */
export class PluginManager {
  constructor() {
    this.plugins = new Map();
  }

  // 注册插件
  register(plugin) {
    if (!(plugin instanceof AgentBrainPlugin)) {
      throw new Error('必须是 AgentBrainPlugin 实例');
    }
    this.plugins.set(plugin.name, plugin);
    console.log(`[PluginManager] 注册插件: ${plugin.name}`);
  }

  // 卸载插件
  async unregister(name) {
    const plugin = this.plugins.get(name);
    if (plugin) {
      await plugin.uninstall();
      this.plugins.delete(name);
    }
  }

  // 启用所有插件
  async enableAll(brain) {
    for (const plugin of this.plugins.values()) {
      await plugin.install(brain);
    }
  }

  // 获取插件列表
  list() {
    return Array.from(this.plugins.values()).map(p => p.getInfo());
  }
}

/**
 * 内置插件: 记忆统计插件
 */
export class StatsPlugin extends AgentBrainPlugin {
  constructor() {
    super('stats');
  }

  async install(brain) {
    await super.install(brain);
    // 挂钩 brain 的 remember 方法
    const originalRemember = brain.remember.bind(brain);
    brain.remember = async (text, options) => {
      const result = await originalRemember(text, options);
      brain._stats = brain._stats || { total: 0 };
      brain._stats.total++;
      return result;
    };
  }
}

/**
 * 内置插件: 自动摘要插件
 */
export class AutoSummaryPlugin extends AgentBrainPlugin {
  constructor(options = {}) {
    super('auto_summary', options);
    this.threshold = options.threshold || 100;
  }

  async install(brain) {
    await super.install(brain);
    brain.on('memory_added', async (entry) => {
      if (brain.entries.size >= this.threshold) {
        await brain.summarize();
      }
    });
  }
}

export default { AgentBrainPlugin, PluginManager, StatsPlugin, AutoSummaryPlugin };
