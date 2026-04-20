// unified-memory 集成测试
// 测试所有模块的集成和协同工作

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('🚀 开始 unified-memory 集成测试\n');

// ========== 导入所有模块 ==========

// 基础功能
import ZeroConfigMemory from './zero-config-template.js';

// 混合搜索
import { HybridSearchEngine } from './hybrid-search.js';

// 插件系统
import UnifiedPluginManager from './plugin-system.js';

// 集成工具
import { OpenClawIntegration, APIWrapper } from './integration-tools.js';

// ========== 测试配置 ==========
const testConfig = {
  memoryCount: 50,
  searchQueries: ['unified', 'memory', '搜索', '测试'],
  pluginCount: 3,
  apiTest: true
};

// ========== 测试用例 ==========

async function runIntegrationTests() {
  const results = {
    total: 0,
    passed: 0,
    failed: 0,
    modules: {}
  };

  console.log('🧪 测试1：基础记忆系统');
  try {
    const memory = new ZeroConfigMemory();
    const stats = memory.stats();
    console.log(`   ✅ 基础功能正常，记忆数：${stats.totalMemories}`);
    results.modules.base = '✅';
    results.passed++;
  } catch (error) {
    console.log(`   ❌ 基础功能失败：${error.message}`);
    results.modules.base = '❌';
    results.failed++;
  }
  results.total++;

  console.log('\n🧪 测试2：混合搜索系统');
  try {
    // 创建测试数据
    const testDocs = [];
    for (let i = 0; i < 10; i++) {
      testDocs.push({
        id: `test-${i}`,
        content: `测试文档 ${i}：unified-memory 集成测试 ${i}`,
        tags: ['测试', '集成'],
        category: 'test'
      });
    }

    const engine = new HybridSearchEngine({ rrfK: 60 });
    await engine.initialize(testDocs);
    
    const searchResults = await engine.search('测试', { limit: 5 });
    console.log(`   ✅ 混合搜索正常，结果数：${searchResults.length}`);
    results.modules.hybrid = '✅';
    results.passed++;
  } catch (error) {
    console.log(`   ❌ 混合搜索失败：${error.message}`);
    results.modules.hybrid = '❌';
    results.failed++;
  }
  results.total++;

  console.log('\n🧪 测试3：插件系统');
  try {
    const pluginManager = new UnifiedPluginManager();
    
    // 加载示例插件
    const loggerPlugin = await import('./plugins/logger-plugin.js');
    pluginManager.registerPlugin('logger', loggerPlugin.default);
    
    console.log(`   ✅ 插件系统正常，插件数：${pluginManager.listPlugins().length}`);
    results.modules.plugin = '✅';
    results.passed++;
  } catch (error) {
    console.log(`   ❌ 插件系统失败：${error.message}`);
    results.modules.plugin = '❌';
    results.failed++;
  }
  results.total++;

  console.log('\n🧪 测试4：集成工具');
  try {
    const integration = new OpenClawIntegration();
    const config = integration.checkExistingSystems();
    
    console.log(`   ✅ 集成工具正常，系统检查：${JSON.stringify(config)}`);
    results.modules.integration = '✅';
    results.passed++;
  } catch (error) {
    console.log(`   ❌ 集成工具失败：${error.message}`);
    results.modules.integration = '❌';
    results.failed++;
  }
  results.total++;

  console.log('\n🧪 测试5：模块间集成');
  try {
    // 创建完整的应用实例
    const memory = new ZeroConfigMemory();
    
    // 添加测试记忆
    for (let i = 0; i < 5; i++) {
      memory.add(
        `集成测试记忆 ${i}：测试 unified-memory 各模块协同工作`,
        ['集成测试', '模块协同'],
        'test',
        { priority: 'high' }
      );
    }
    
    // 创建搜索索引
    const docs = memory.memories.map((mem, idx) => ({
      id: `mem-${idx}`,
      content: mem.content,
      tags: mem.tags,
      category: mem.category
    }));
    
    const engine = new HybridSearchEngine();
    await engine.initialize(docs);
    
    // 搜索测试
    const results = await engine.search('集成测试', { limit: 3 });
    
    console.log(`   ✅ 模块集成正常，搜索到 ${results.length} 条结果`);
    results.modules.integration = '✅';
    results.passed++;
  } catch (error) {
    console.log(`   ❌ 模块集成失败：${error.message}`);
    results.modules.integration = '❌';
    results.failed++;
  }
  results.total++;

  console.log('\n🧪 测试6：性能基准');
  try {
    const memory = new ZeroConfigMemory();
    
    // 性能测试：批量添加
    const startTime = Date.now();
    for (let i = 0; i < 100; i++) {
      memory.add(`性能测试记忆 ${i}`, ['性能测试'], 'benchmark');
    }
    const addTime = Date.now() - startTime;
    
    // 搜索性能
    const searchStart = Date.now();
    const searchResults = memory.search('性能测试', { limit: 10 });
    const searchTime = Date.now() - searchStart;
    
    console.log(`   ✅ 性能测试正常`);
    console.log(`      添加100条：${addTime}ms (${(100/addTime*1000).toFixed(1)} ops/s)`);
    console.log(`      搜索10条：${searchTime}ms`);
    results.modules.performance = '✅';
    results.passed++;
  } catch (error) {
    console.log(`   ❌ 性能测试失败：${error.message}`);
    results.modules.performance = '❌';
    results.failed++;
  }
  results.total++;

  // ========== 测试结果汇总 ==========
  console.log('\n📊 集成测试结果汇总');
  console.log('=' .repeat(50));
  
  console.log(`   总测试数：${results.total}`);
  console.log(`   通过数：${results.passed}`);
  console.log(`   失败数：${results.failed}`);
  console.log(`   通过率：${((results.passed / results.total) * 100).toFixed(1)}%`);
  
  console.log('\n📦 模块状态：');
  Object.entries(results.modules).forEach(([module, status]) => {
    console.log(`   ${module}: ${status}`);
  });
  
  console.log('\n🎯 集成测试结论：');
  if (results.failed === 0) {
    console.log('   ✅ 所有模块集成正常，可以发布！');
    return true;
  } else if (results.passed / results.total >= 0.8) {
    console.log('   ⚠️  大部分模块正常，建议修复失败模块后发布');
    return 'partial';
  } else {
    console.log('   ❌ 集成问题较多，需要进一步调试');
    return false;
  }
}

// ========== 运行测试 ==========
(async () => {
  console.log('🚀 unified-memory 集成测试开始');
  console.log(`⏰ 时间：${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}`);
  console.log('📋 测试配置：', JSON.stringify(testConfig, null, 2));
  console.log('-'.repeat(60));
  
  const testResult = await runIntegrationTests();
  
  console.log('\n📈 测试完成时间：', new Date().toLocaleTimeString('zh-CN'));
  console.log('🚀 下一步：根据测试结果决定发布计划');
  
  // 保存测试结果
  const resultFile = path.join(__dirname, 'test-results', 'integration-test-result.json');
  const resultDir = path.dirname(resultFile);
  if (!fs.existsSync(resultDir)) {
    fs.mkdirSync(resultDir, { recursive: true });
  }
  
  const resultData = {
    timestamp: new Date().toISOString(),
    config: testConfig,
    result: testResult,
    summary: {
      total: results.total,
      passed: results.passed,
      failed: results.failed,
      passRate: ((results.passed / results.total) * 100).toFixed(1) + '%'
    }
  };
  
  fs.writeFileSync(resultFile, JSON.stringify(resultData, null, 2));
  console.log(`📄 测试结果已保存：${resultFile}`);
})();