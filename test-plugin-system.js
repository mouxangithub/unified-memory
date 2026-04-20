/**
 * Plugin System Test
 * 测试完整的插件系统
 */

import { UnifiedPluginManager, PluginValidator } from './plugin-system.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function runTests() {
  console.log('🧪 Plugin System Tests\n');
  console.log('='.repeat(50));
  
  // 测试1: PluginValidator
  console.log('\n📋 Test 1: PluginValidator');
  console.log('-'.repeat(30));
  
  const validPlugin = {
    name: 'test-plugin',
    version: '1.0.0',
    description: 'A test plugin',
    hooks: {
      beforeSave: async () => {}
    }
  };
  
  const validation = PluginValidator.validate(validPlugin);
  console.log(`Valid plugin: ${validation.valid ? '✅' : '❌'}`);
  if (!validation.valid) console.log(`   Errors: ${validation.errors}`);
  
  const invalidPlugin = { name: 123 };
  const invalidValidation = PluginValidator.validate(invalidPlugin);
  console.log(`Invalid plugin: ${!invalidValidation.valid ? '✅' : '❌'} (expected to fail)`);
  
  // 测试2: UnifiedPluginManager 初始化
  console.log('\n📋 Test 2: PluginManager Initialization');
  console.log('-'.repeat(30));
  
  const manager = new UnifiedPluginManager({
    pluginDir: path.join(__dirname, 'plugins'),
    configDir: path.join(__dirname, 'config'),
    enableHotReload: true,
    strictValidation: false
  });
  
  console.log(`✅ PluginManager created`);
  console.log(`   Plugin dir: ${manager.options.pluginDir}`);
  console.log(`   Config dir: ${manager.options.configDir}`);
  
  // 测试3: 动态注册插件
  console.log('\n📋 Test 3: Dynamic Plugin Registration');
  console.log('-'.repeat(30));
  
  const inlinePlugin = {
    name: 'inline-test',
    version: '1.0.0',
    description: 'An inline test plugin',
    hooks: {
      beforeSave: async (memory) => {
        console.log(`   [inline-test] beforeSave: ${memory.content?.substring(0, 20)}...`);
        return memory;
      },
      afterSave: async (result) => {
        console.log(`   [inline-test] afterSave: ${result?.id || 'unknown'}`);
        return result;
      }
    },
    initialize: async (context) => {
      console.log(`   [inline-test] initialized with config:`, context.config);
    },
    destroy: async () => {
      console.log(`   [inline-test] destroyed`);
    }
  };
  
  try {
    await manager.registerPlugin(inlinePlugin);
    console.log(`✅ Inline plugin registered`);
  } catch (error) {
    console.log(`❌ Failed to register inline plugin: ${error.message}`);
  }
  
  // 测试4: 加载文件插件
  console.log('\n📋 Test 4: Load File-based Plugins');
  console.log('-'.repeat(30));
  
  const pluginFiles = [
    'logger-plugin.js',
    'cache-plugin.js',
    'monitor-plugin.js',
    'export-plugin.js'
  ];
  
  for (const pluginFile of pluginFiles) {
    const pluginPath = path.join(__dirname, 'plugins', pluginFile);
    if (fs.existsSync(pluginPath)) {
      try {
        await manager.registerPlugin(pluginPath);
        console.log(`✅ Loaded: ${pluginFile}`);
      } catch (error) {
        console.log(`❌ Failed to load ${pluginFile}: ${error.message}`);
      }
    } else {
      console.log(`⚠️  File not found: ${pluginPath}`);
    }
  }
  
  // 测试5: 列出插件
  console.log('\n📋 Test 5: List Plugins');
  console.log('-'.repeat(30));
  
  const plugins = manager.listPlugins();
  console.log(`Total plugins: ${plugins.length}`);
  plugins.forEach(p => {
    console.log(`   - ${p.name} v${p.version} [${p.status}]`);
    if (p.dependencies && p.dependencies.length > 0) {
      console.log(`     Dependencies: ${p.dependencies.join(', ')}`);
    }
  });
  
  // 测试6: 执行钩子
  console.log('\n📋 Test 6: Execute Hooks');
  console.log('-'.repeat(30));
  
  const testMemory = {
    id: 'test-memory-1',
    content: 'This is a test memory for hook execution',
    timestamp: new Date().toISOString()
  };
  
  console.log('Executing beforeSave hook...');
  await manager.executeHook('beforeSave', testMemory);
  
  console.log('Executing afterSave hook...');
  await manager.executeHook('afterSave', testMemory);
  
  // 测试7: 状态报告
  console.log('\n📋 Test 7: Status Report');
  console.log('-'.repeat(30));
  
  const status = manager.getStatusReport();
  console.log(`Total plugins: ${status.totalPlugins}`);
  console.log(`Active plugins: ${status.lifecycle.active.join(', ') || 'none'}`);
  console.log(`Hot reload enabled: ${status.hotReloadEnabled}`);
  console.log(`Hooks registered:`);
  status.hooks.forEach(h => {
    console.log(`   - ${h.name}: ${h.handlerCount} handlers`);
  });
  
  // 测试8: 热重载钩子测试
  console.log('\n📋 Test 8: Hot Reload Hook');
  console.log('-'.repeat(30));
  
  const searchResults = [
    { id: 'mem-1', content: 'Test result 1' },
    { id: 'mem-2', content: 'Test result 2' }
  ];
  
  console.log('Executing beforeSearch hook...');
  await manager.executeHook('beforeSearch', 'test query');
  
  console.log('Executing afterSearch hook...');
  await manager.executeHook('afterSearch', searchResults);
  
  // 测试9: 卸载插件
  console.log('\n📋 Test 9: Unregister Plugin');
  console.log('-'.repeat(30));
  
  const pluginsBefore = manager.plugins.size;
  if (manager.plugins.has('inline-test')) {
    await manager.unregisterPlugin('inline-test');
    console.log(`✅ Unregistered inline-test`);
  }
  const pluginsAfter = manager.plugins.size;
  console.log(`Plugins before: ${pluginsBefore}, after: ${pluginsAfter}`);
  
  // 测试10: 配置管理
  console.log('\n📋 Test 10: Config Management');
  console.log('-'.repeat(30));
  
  // 保存配置
  try {
    manager.config.saveConfig('test-plugin', {
      enabled: true,
      option1: 'value1',
      option2: 100
    });
    console.log(`✅ Saved config for test-plugin`);
    
    const loaded = manager.config.loadConfig('test-plugin');
    console.log(`✅ Loaded config:`, loaded);
    
    // 热更新配置
    manager.config.updateConfig('test-plugin', { option3: 'new-value' });
    const updated = manager.config.getConfig('test-plugin');
    console.log(`✅ Updated config:`, updated);
    
    // 删除配置
    manager.config.deleteConfig('test-plugin');
    console.log(`✅ Deleted config`);
  } catch (error) {
    console.log(`❌ Config management error: ${error.message}`);
  }
  
  // 总结
  console.log('\n' + '='.repeat(50));
  console.log('📊 Test Summary');
  console.log('='.repeat(50));
  console.log(`Total plugins registered: ${manager.plugins.size}`);
  console.log(`Plugin list: ${manager.listPlugins().map(p => p.name).join(', ')}`);
  
  const finalStatus = manager.getStatusReport();
  console.log(`\nActive hooks:`);
  finalStatus.hooks.forEach(h => {
    if (h.handlerCount > 0) {
      console.log(`   - ${h.name}: ${h.handlerCount} handler(s)`);
    }
  });
  
  console.log('\n✅ All plugin system tests completed!');
  console.log('\n📝 Note: To test hot reload, modify a plugin file while the system is running.');
  console.log('   The system will automatically reload the modified plugin.');
}

// 运行测试
runTests().catch(error => {
  console.error('\n❌ Test failed with error:', error.message);
  console.error(error.stack);
  process.exit(1);
});
