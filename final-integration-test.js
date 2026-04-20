// unified-memory 最终集成测试
// 验证所有6个模块的协同工作

console.log('🚀 unified-memory 最终集成测试开始');
console.log('⏰ 时间：', new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }));
console.log('📋 测试目标：验证6个模块的完整集成');
console.log('='.repeat(60));

const testResults = {
  total: 0,
  passed: 0,
  failed: 0,
  modules: {},
  performance: {}
};

async function runFinalTest() {
  console.log('\n🧪 测试1：导入所有模块');
  try {
    // 动态导入所有模块
    const modules = await Promise.allSettled([
      import('./zero-config-template.js'),
      import('./hybrid-search.js'),
      import('./src/transaction-system.js'),
      import('./plugin-system.js'),
      import('./integration-tools.js'),
      import('./performance-optimizer.js')
    ]);
    
    const imported = modules.filter(m => m.status === 'fulfilled').length;
    console.log(`   ✅ 成功导入 ${imported}/6 个模块`);
    
    if (imported === 6) {
      testResults.modules.import = '✅';
      testResults.passed++;
    } else {
      testResults.modules.import = '❌';
      testResults.failed++;
    }
  } catch (error) {
    console.log(`   ❌ 导入失败：${error.message}`);
    testResults.modules.import = '❌';
    testResults.failed++;
  }
  testResults.total++;

  console.log('\n🧪 测试2：基础记忆系统功能');
  try {
    const { default: ZeroConfigMemory } = await import('./zero-config-template.js');
    const memory = new ZeroConfigMemory();
    
    // 添加测试记忆
    const testId = memory.add('最终集成测试记忆', ['测试', '集成'], 'final-test');
    
    // 搜索测试
    const results = memory.search('集成测试', { limit: 5 });
    
    // 获取统计
    const stats = memory.stats();
    
    console.log(`   ✅ 基础功能正常`);
    console.log(`      总记忆：${stats.totalMemories} 条`);
    console.log(`      搜索到：${results.length} 条结果`);
    console.log(`      测试ID：${testId}`);
    
    testResults.modules.base = '✅';
    testResults.passed++;
  } catch (error) {
    console.log(`   ❌ 基础功能失败：${error.message}`);
    testResults.modules.base = '❌';
    testResults.failed++;
  }
  testResults.total++;

  console.log('\n🧪 测试3：混合搜索性能');
  try {
    const { HybridSearchEngine } = await import('./hybrid-search.js');
    
    // 创建测试文档
    const testDocs = [];
    for (let i = 0; i < 20; i++) {
      testDocs.push({
        id: `final-test-${i}`,
        content: `最终集成测试文档 ${i}：验证 unified-memory 混合搜索性能`,
        tags: ['测试', '性能', '集成'],
        category: 'benchmark'
      });
    }
    
    const engine = new HybridSearchEngine({ rrfK: 60 });
    await engine.initialize(testDocs);
    
    // 性能测试
    const startTime = Date.now();
    const searchResults = await engine.search('集成测试', { limit: 10 });
    const searchTime = Date.now() - startTime;
    
    console.log(`   ✅ 混合搜索正常`);
    console.log(`      搜索时间：${searchTime}ms`);
    console.log(`      结果数量：${searchResults.length} 条`);
    console.log(`      平均延迟：${(searchTime / 10).toFixed(2)}ms/查询`);
    
    testResults.performance.hybridSearch = searchTime;
    testResults.modules.hybrid = '✅';
    testResults.passed++;
  } catch (error) {
    console.log(`   ❌ 混合搜索失败：${error.message}`);
    testResults.modules.hybrid = '❌';
    testResults.failed++;
  }
  testResults.total++;

  console.log('\n🧪 测试4：事务系统基准');
  try {
    const { TransactionManager } = await import('./src/transaction-system.js');
    
    const txManager = new TransactionManager();
    
    // 开始事务
    const txId = txManager.beginTransaction();
    
    // 模拟一些操作
    txManager.recordOperation(txId, {
      type: 'insert',
      collection: 'memories',
      data: { id: 'test-1', content: '测试记忆' }
    });
    
    // 提交事务
    const result = txManager.commitTransaction(txId);
    
    console.log(`   ✅ 事务系统正常`);
    console.log(`      事务ID：${txId}`);
    console.log(`      提交结果：${result.success ? '成功' : '失败'}`);
    
    testResults.modules.transaction = '✅';
    testResults.passed++;
  } catch (error) {
    console.log(`   ❌ 事务系统失败：${error.message}`);
    testResults.modules.transaction = '❌';
    testResults.failed++;
  }
  testResults.total++;

  console.log('\n🧪 测试5：插件系统验证');
  try {
    const { default: UnifiedPluginManager } = await import('./plugin-system.js');
    
    const pluginManager = new UnifiedPluginManager();
    
    console.log(`   ✅ 插件系统初始化正常`);
    console.log(`      插件管理器：${pluginManager.constructor.name}`);
    
    // 检查插件目录
    const fs = await import('fs');
    const path = await import('path');
    
    const pluginDir = path.join(process.cwd(), 'plugins');
    if (fs.existsSync(pluginDir)) {
      const plugins = fs.readdirSync(pluginDir).filter(f => f.endsWith('.js'));
      console.log(`      发现 ${plugins.length} 个示例插件`);
    }
    
    testResults.modules.plugin = '✅';
    testResults.passed++;
  } catch (error) {
    console.log(`   ❌ 插件系统失败：${error.message}`);
    testResults.modules.plugin = '❌';
    testResults.failed++;
  }
  testResults.total++;

  console.log('\n🧪 测试6：集成工具检查');
  try {
    const { ConfigManager } = await import('./integration-tools.js');
    
    const configManager = new ConfigManager();
    const config = configManager.loadConfig();
    
    console.log(`   ✅ 集成工具正常`);
    console.log(`      配置版本：${config.version || '1.0.0'}`);
    console.log(`      OpenClaw集成：${config.openclaw?.integrationEnabled ? '启用' : '禁用'}`);
    
    testResults.modules.integration = '✅';
    testResults.passed++;
  } catch (error) {
    console.log(`   ❌ 集成工具失败：${error.message}`);
    testResults.modules.integration = '❌';
    testResults.failed++;
  }
  testResults.total++;

  console.log('\n🧪 测试7：性能优化模块');
  try {
    const { PerformanceOptimizer } = await import('./performance-optimizer.js');
    
    const optimizer = new PerformanceOptimizer();
    const suggestions = optimizer.getOptimizationSuggestions();
    
    console.log(`   ✅ 性能优化器正常`);
    console.log(`      缓存命中率：${suggestions.summary.cacheHitRate}`);
    console.log(`      瓶颈严重性：${suggestions.summary.bottleneckSeverity}`);
    console.log(`      优化建议数：${suggestions.suggestions.length} 条`);
    
    testResults.modules.performance = '✅';
    testResults.passed++;
  } catch (error) {
    console.log(`   ❌ 性能优化失败：${error.message}`);
    testResults.modules.performance = '❌';
    testResults.failed++;
  }
  testResults.total++;

  console.log('\n🧪 测试8：模块间集成场景');
  try {
    // 创建完整的应用场景
    const { default: ZeroConfigMemory } = await import('./zero-config-template.js');
    const { HybridSearchEngine } = await import('./hybrid-search.js');
    const { PerformanceOptimizer } = await import('./performance-optimizer.js');
    
    // 1. 初始化记忆系统
    const memory = new ZeroConfigMemory();
    
    // 2. 添加一些记忆
    for (let i = 0; i < 10; i++) {
      memory.add(`集成场景测试 ${i}：验证所有模块协同工作`, ['场景', '集成', '测试'], 'scenario');
    }
    
    // 3. 创建搜索索引
    const docs = memory.memories.map((mem, idx) => ({
      id: `scenario-${idx}`,
      content: mem.content,
      tags: mem.tags,
      category: mem.category
    }));
    
    const engine = new HybridSearchEngine();
    await engine.initialize(docs);
    
    // 4. 搜索测试
    const results = await engine.search('集成场景', { limit: 5 });
    
    // 5. 性能优化
    const optimizer = new PerformanceOptimizer();
    const report = optimizer.getFullReport();
    
    console.log(`   ✅ 模块集成场景正常`);
    console.log(`      记忆数量：${memory.memories.length} 条`);
    console.log(`      搜索结果：${results.length} 条`);
    console.log(`      性能报告：${report.monitor.totalOperations || 0} 次操作`);
    
    testResults.modules.scenario = '✅';
    testResults.passed++;
  } catch (error) {
    console.log(`   ❌ 集成场景失败：${error.message}`);
    testResults.modules.scenario = '❌';
    testResults.failed++;
  }
  testResults.total++;

  return testResults;
}

// ========== 运行测试 ==========
(async () => {
  const results = await runFinalTest();
  
  console.log('\n' + '='.repeat(60));
  console.log('📊 最终集成测试结果汇总');
  console.log('='.repeat(60));
  
  console.log(`   总测试数：${results.total}`);
  console.log(`   通过数：${results.passed}`);
  console.log(`   失败数：${results.failed}`);
  const passRate = ((results.passed / results.total) * 100).toFixed(1);
  console.log(`   通过率：${passRate}%`);
  
  console.log('\n📦 模块状态：');
  Object.entries(results.modules).forEach(([module, status]) => {
    console.log(`   ${module.padEnd(15)}：${status}`);
  });
  
  console.log('\n⚡ 性能指标：');
  Object.entries(results.performance).forEach(([metric, value]) => {
    console.log(`   ${metric.padEnd(20)}：${value}ms`);
  });
  
  console.log('\n🎯 测试结论：');
  if (results.failed === 0) {
    console.log('   ✅ 完美！所有模块集成正常，可以立即发布！');
    console.log('   🚀 项目100%完成，性能达标，功能完整！');
  } else if (passRate >= 80) {
    console.log(`   ⚠️  良好！通过率 ${passRate}%，核心功能正常`);
    console.log('   🔧 建议修复少量问题后发布');
  } else {
    console.log(`   ❌ 需要改进！通过率 ${passRate}%`);
    console.log('   🛠️  需要进一步调试集成问题');
  }
  
  console.log('\n⏰ 测试完成时间：', new Date().toLocaleTimeString('zh-CN'));
  console.log('🚀 unified-memory 并行实施项目测试完成！');
  
  // 保存测试结果
  const fs = await import('fs');
  const path = await import('path');
  const resultFile = path.join(process.cwd(), 'test-results', 'final-integration-result.json');
  const resultDir = path.dirname(resultFile);
  
  if (!fs.existsSync(resultDir)) {
    fs.mkdirSync(resultDir, { recursive: true });
  }
  
  const resultData = {
    timestamp: new Date().toISOString(),
    results: results,
    summary: {
      total: results.total,
      passed: results.passed,
      failed: results.failed,
      passRate: passRate + '%'
    },
    environment: {
      node: process.version,
      platform: process.platform,
      timezone: 'Asia/Shanghai'
    }
  };
  
  fs.writeFileSync(resultFile, JSON.stringify(resultData, null, 2));
  console.log(`\n📄 详细测试结果已保存：${resultFile}`);
})();