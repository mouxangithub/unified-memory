# Unified Memory Plugin System

完整的插件系统实现，支持热重载、依赖管理、生命周期管理。

## 📁 文件结构

```
unified-memory/
├── plugin-system.js          # 核心插件系统
├── plugins/
│   ├── logger-plugin.js      # 日志插件
│   ├── cache-plugin.js       # 缓存插件
│   ├── monitor-plugin.js     # 监控插件
│   └── export-plugin.js      # 导出插件
├── config/                   # 插件配置目录
├── test-plugin-system.js     # 测试文件
└── README.md
```

## 🚀 快速开始

### 1. 创建插件管理器

```javascript
import { UnifiedPluginManager } from './plugin-system.js';

const manager = new UnifiedPluginManager({
  pluginDir: './plugins',
  configDir: './config',
  enableHotReload: true,
  strictValidation: false
});
```

### 2. 注册插件

**方式一：从文件加载**
```javascript
await manager.registerPlugin('./plugins/logger-plugin.js');
```

**方式二：动态注册**
```javascript
const myPlugin = {
  name: 'my-plugin',
  version: '1.0.0',
  description: 'My custom plugin',
  hooks: {
    beforeSave: async (memory) => {
      console.log('Saving memory:', memory.id);
      return memory;
    }
  }
};

await manager.registerPlugin(myPlugin);
```

### 3. 执行钩子

```javascript
// 在保存前执行
await manager.executeHook('beforeSave', memory);

// 在保存后执行
await manager.executeHook('afterSave', savedMemory);
```

### 4. 列出插件

```javascript
const plugins = manager.listPlugins();
console.log(plugins);
// [{ name: 'logger', version: '1.0.0', status: 'active', ... }]
```

## 🔌 插件接口

```javascript
export default {
  name: 'plugin-name',           // 必填，唯一标识
  version: '1.0.0',              // 必填，语义化版本
  description: '描述',            // 可选
  author: '作者',                // 可选
  dependencies: [],              // 可选，依赖插件
  
  defaultConfig: {},             // 可选，默认配置
  
  // 生命周期
  async initialize(context) {}, // 可选
  async destroy(context) {},     // 可选
  
  // 钩子
  hooks: {
    beforeSave: async (memory, context) => memory,
    afterSave: async (result, context) => result,
    beforeSearch: async (query, context) => query,
    afterSearch: async (results, context) => results,
    beforeLoad: async (context) => true,
    afterLoad: async (memories, context) => memories,
    beforeDelete: async (id, context) => id,
    afterDelete: async (id, context) => id
  }
};
```

## 🎣 支持的钩子

| 钩子 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `beforeSave` | memory, context | memory | 保存前 |
| `afterSave` | result, context | result | 保存后 |
| `beforeSearch` | query, context | query | 搜索前 |
| `afterSearch` | results, context | results | 搜索后 |
| `beforeLoad` | context | boolean | 加载前 |
| `afterLoad` | memories, context | memories | 加载后 |
| `beforeDelete` | id, context | id | 删除前 |
| `afterDelete` | id, context | id | 删除后 |

## 🔧 插件配置

```javascript
// 保存配置
manager.config.saveConfig('plugin-name', {
  option1: 'value1',
  option2: 100
});

// 热更新配置
manager.config.updateConfig('plugin-name', {
  option3: 'new-value'
});

// 加载配置
const config = manager.config.loadConfig('plugin-name');

// 删除配置
manager.config.deleteConfig('plugin-name');
```

## 🔄 热重载

```javascript
// 自动热重载已启用
// 修改插件文件后，系统自动重载

// 手动触发热重载
await manager.hotReloadPlugin('plugin-name');
```

## 📊 状态报告

```javascript
const status = manager.getStatusReport();
console.log(status);
// {
//   totalPlugins: 4,
//   plugins: [...],
//   hooks: [...],
//   hotReloadEnabled: 4,
//   lifecycle: { active: [...] }
// }
```

## 📦 示例插件

### Logger Plugin
记录所有 memory 操作日志。

```javascript
// 已实现钩子: beforeSave, afterSave, beforeSearch, afterSearch, 
//             beforeLoad, afterLoad, beforeDelete, afterDelete
```

### Cache Plugin
提供 LRU 缓存和查询结果缓存。

```javascript
// 配置项:
// - maxSize: 最大缓存条目数
// - ttl: 缓存过期时间（毫秒）
// - persistCache: 是否持久化缓存
```

### Monitor Plugin
监控 memory 操作性能和系统资源使用。

```javascript
// 导出函数:
// getMetrics() - 获取性能指标
// resetMetrics() - 重置指标
```

### Export Plugin
支持多种格式导出记忆数据。

```javascript
// 支持格式: json, csv, markdown, text

// 使用
import { exportMemories, exportToFile, getSupportedFormats } from './plugins/export-plugin.js';

await exportMemories(memories, 'json', { filePath: '/tmp/export.json' });
await exportToFile(memories, 'csv', 'memories.csv');
getSupportedFormats();
```

## 🧪 运行测试

```bash
node test-plugin-system.js
```

## 📝 创建新插件

1. 在 `plugins/` 目录创建 `.js` 文件
2. 导出默认插件对象
3. 实现 `name`, `version`, `hooks`
4. 可选实现 `initialize`, `destroy`

```javascript
// plugins/my-plugin.js
export default {
  name: 'my-plugin',
  version: '1.0.0',
  hooks: {
    beforeSave: async (memory) => memory,
    afterSave: async (result) => result
  }
};
```
