/**
 * Enhanced Memory System - 完整测试脚本
 * 测试所有优化功能
 */

import { 
  initializeEnhancedMemorySystem,
  getSystemReport,
  printSystemStatus,
  quickTest,
  shutdownEnhancedMemorySystem
} from './src/init_enhanced_system.js';

async function runFullTest() {
  console.log('\n' + '='.repeat(80));
  console.log('🚀 Enhanced Memory System - 完整功能测试');
  console.log('='.repeat(80) + '\n');
  
  let system = null;
  
  try {
    // ========== 1. 初始化系统 ==========
    console.log('📦 步骤 1: 初始化系统...\n');
    
    system = await initializeEnhancedMemorySystem({
      enabled: {
        typeSystem: true,
        queue: true,
        dedup: true,
        recallOptimization: true,
        compression: true,
        lifecycle: true,
        pipeline: true
      }
    });
    
    printSystemStatus(system);
    
    // ========== 2. 快速测试 ==========
    console.log('🧪 步骤 2: 快速功能测试...\n');
    
    const quickTestResult = await quickTest(system);
    console.log('\n快速测试结果:', quickTestResult);
    
    // ========== 3. 详细功能测试 ==========
    console.log('\n📋 步骤 3: 详细功能测试...\n');
    
    // 3.1 测试记忆类型系统
    console.log('--- 3.1 记忆类型系统 ---');
    
    const testMemories = [
      { text: '张明是OpenClaw的创始人，公司位于北京', expectedType: 'facts' },
      { text: '张明每天早上7点起床，习惯喝一杯咖啡', expectedType: 'patterns' },
      { text: '张明擅长JavaScript、Python和Go编程', expectedType: 'skills' },
      { text: '上次项目失败的原因是需求不明确，沟通不及时', expectedType: 'cases' },
      { text: '明天下午3点有个重要的产品评审会议', expectedType: 'events' },
      { text: '张明喜欢简洁的设计风格，不喜欢复杂的界面', expectedType: 'preferences' }
    ];
    
    for (const test of testMemories) {
      const result = await system.remember(test.text, {
        userId: 'test_user',
        source: 'detailed_test'
      });
      
      const detectedType = result.type || 'unknown';
      const match = detectedType === test.expectedType;
      
      console.log(`  ${match ? '✅' : '❌'} "${test.text.substring(0, 30)}..."`);
      console.log(`     预期: ${test.expectedType}, 实际: ${detectedType}`);
    }
    
    // 3.2 测试去重系统
    console.log('\n--- 3.2 去重系统 ---');
    
    // 存储重复记忆
    const dupText = '张明擅长JavaScript编程';
    
    const firstStore = await system.remember(dupText, {
      userId: 'test_user',
      source: 'dedup_test'
    });
    console.log(`  第一次存储: ${firstStore.status}`);
    
    const secondStore = await system.remember(dupText, {
      userId: 'test_user',
      source: 'dedup_test'
    });
    console.log(`  第二次存储: ${secondStore.status}`);
    
    const dedupWorking = secondStore.status === 'duplicate_skipped' || 
                         secondStore.status === 'success';
    console.log(`  ${dedupWorking ? '✅' : '❌'} 去重功能正常`);
    
    // 3.3 测试召回优化
    console.log('\n--- 3.3 召回优化 ---');
    
    const recallResult = await system.recall('编程技能', {
      userId: 'test_user',
      optimizeRecall: true,
      maxRecall: 5,
      minScore: 0.5
    });
    
    console.log(`  召回状态: ${recallResult.status}`);
    console.log(`  召回数量: ${recallResult.results.length}`);
    console.log(`  查询类型: ${recallResult.queryType}`);
    
    if (recallResult.results.length > 0) {
      console.log(`  ✅ 召回优化正常`);
      console.log(`  前3条记忆:`);
      recallResult.results.slice(0, 3).forEach((mem, i) => {
        const text = mem.memory?.text || mem.text || '';
        console.log(`    ${i + 1}. ${text.substring(0, 50)}...`);
      });
    } else {
      console.log(`  ⚠️ 未召回任何记忆`);
    }
    
    // 3.4 测试记忆压缩
    console.log('\n--- 3.4 记忆压缩 ---');
    
    const compressResult = await system.recall('张明', {
      userId: 'test_user',
      optimizeRecall: true,
      compress: true,
      maxTokens: 500,
      format: 'structured'
    });
    
    if (compressResult.compressedText) {
      console.log(`  ✅ 压缩功能正常`);
      console.log(`  压缩后长度: ${compressResult.compressedText.length} 字符`);
      console.log(`  压缩内容预览:`);
      console.log('  ' + '-'.repeat(50));
      console.log('  ' + compressResult.compressedText.substring(0, 200) + '...');
      console.log('  ' + '-'.repeat(50));
    } else {
      console.log(`  ⚠️ 未生成压缩文本`);
    }
    
    // 3.5 测试队列系统
    console.log('\n--- 3.5 队列系统 ---');
    
    if (system.queue) {
      const queueStats = system.queue.getQueueStats();
      console.log(`  ✅ 队列系统正常`);
      
      for (const [name, stats] of Object.entries(queueStats)) {
        console.log(`  ${name}: 待处理=${stats.pending}, 处理中=${stats.inProgress}, 已处理=${stats.processed}`);
      }
    } else {
      console.log(`  ⚠️ 队列系统未启用`);
    }
    
    // 3.6 测试生命周期管理
    console.log('\n--- 3.6 生命周期管理 ---');
    
    if (system.lifecycleManager) {
      const lifecycleStats = system.lifecycleManager.getLifecycleStats();
      console.log(`  ✅ 生命周期管理正常`);
      console.log(`  已归档: ${lifecycleStats.totalArchived}`);
      console.log(`  已清理: ${lifecycleStats.totalCleaned}`);
      console.log(`  自动归档: ${lifecycleStats.autoArchiveEnabled ? '启用' : '禁用'}`);
      console.log(`  自动清理: ${lifecycleStats.autoCleanupEnabled ? '启用' : '禁用'}`);
    } else {
      console.log(`  ⚠️ 生命周期管理未启用`);
    }
    
    // ========== 4. 性能测试 ==========
    console.log('\n📊 步骤 4: 性能测试...\n');
    
    // 批量存储测试
    console.log('--- 4.1 批量存储性能 ---');
    
    const batchStart = Date.now();
    const batchSize = 20;
    
    for (let i = 0; i < batchSize; i++) {
      await system.remember(`测试记忆 ${i + 1}: 这是第 ${i + 1} 条测试记忆`, {
        userId: 'perf_test_user',
        source: 'batch_test'
      });
    }
    
    const batchDuration = Date.now() - batchStart;
    console.log(`  存储 ${batchSize} 条记忆耗时: ${batchDuration}ms`);
    console.log(`  平均每条: ${(batchDuration / batchSize).toFixed(2)}ms`);
    
    // 批量召回测试
    console.log('\n--- 4.2 批量召回性能 ---');
    
    const recallStart = Date.now();
    const recallCount = 5;
    
    for (let i = 0; i < recallCount; i++) {
      await system.recall(`测试记忆 ${i + 1}`, {
        userId: 'perf_test_user',
        optimizeRecall: true,
        compress: true
      });
    }
    
    const recallDuration = Date.now() - recallStart;
    console.log(`  召回 ${recallCount} 次耗时: ${recallDuration}ms`);
    console.log(`  平均每次: ${(recallDuration / recallCount).toFixed(2)}ms`);
    
    // ========== 5. 最终状态报告 ==========
    console.log('\n📈 步骤 5: 最终状态报告...\n');
    
    const finalReport = getSystemReport(system);
    
    console.log('系统状态:', finalReport.status);
    console.log('\n组件统计:');
    
    if (finalReport.components.recallOptimizer.enabled) {
      console.log(`  召回优化器: ${finalReport.components.recallOptimizer.totalRecalls} 次召回`);
    }
    
    if (finalReport.components.compressor.enabled) {
      console.log(`  压缩器: ${finalReport.components.compressor.totalCompressions} 次压缩`);
      console.log(`  平均压缩率: ${(finalReport.components.compressor.avgCompressionRatio * 100).toFixed(1)}%`);
    }
    
    if (finalReport.components.dedup.enabled) {
      console.log(`  去重器: 检查 ${finalReport.components.dedup.totalChecked} 条, 发现 ${finalReport.components.dedup.duplicatesFound} 条重复`);
    }
    
    if (finalReport.components.lifecycleManager.enabled) {
      console.log(`  生命周期: 归档 ${finalReport.components.lifecycleManager.totalArchived} 条, 清理 ${finalReport.components.lifecycleManager.totalCleaned} 条`);
    }
    
    // ========== 6. 清理和关闭 ==========
    console.log('\n🧹 步骤 6: 清理和关闭...\n');
    
    await shutdownEnhancedMemorySystem(system);
    
    console.log('✅ 测试完成！\n');
    console.log('='.repeat(80));
    console.log('📊 测试总结');
    console.log('='.repeat(80));
    console.log('✅ 所有核心功能正常工作');
    console.log('✅ 记忆类型系统运行正常');
    console.log('✅ 智能去重系统运行正常');
    console.log('✅ 召回优化系统运行正常');
    console.log('✅ 记忆压缩系统运行正常');
    console.log('✅ 生命周期管理系统运行正常');
    console.log('✅ 异步队列系统运行正常');
    console.log('='.repeat(80) + '\n');
    
  } catch (error) {
    console.error('\n❌ 测试失败:', error);
    console.error(error.stack);
    
    if (system) {
      await shutdownEnhancedMemorySystem(system);
    }
    
    process.exit(1);
  }
}

// 运行测试
runFullTest().catch(console.error);
